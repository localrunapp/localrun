"""
System Information Controller.
Provides detailed information about the host system.
"""

import datetime
import json
import os
import platform
import socket
import ipaddress
from typing import Any, Dict, Optional, List
from pathlib import Path

import docker
import httpx
import psutil
from fastapi import HTTPException, Request, WebSocket
import asyncio
import uuid
from sqlmodel import Session
from core.database import engine
from app.repositories.server_repository import server_repository
from app.models.server import Server


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_connection: Optional[WebSocket] = None
        self.active_agents: Dict[str, WebSocket] = {}  # server_id -> websocket
        self.pending_requests: Dict[str, asyncio.Future] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from active agents if present
        for server_id, ws in list(self.active_agents.items()):
            if ws == websocket:
                print(f"Agent for server {server_id} disconnected")
                del self.active_agents[server_id]
                break

        if websocket == self.agent_connection:
            print("Agent disconnected")
            self.agent_connection = None

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def register_agent(self, websocket: WebSocket, server_id: Optional[str] = None):
        """Register a websocket connection as the agent."""
        client_host = websocket.client.host
        print(f"Agent registered via WebSocket. Server ID: {server_id}. Host: {client_host}")

        # Check for Local Agent Auto-Discovery
        if client_host in ["127.0.0.1", "::1", "localhost"]:
            try:
                with Session(engine) as session:
                    local_server = server_repository.get_localhost(session)
                    if local_server:
                        # If agent has no ID or ID mismatch, send correct ID
                        if not server_id or server_id != local_server.id:
                            print(
                                f"Local agent detected with wrong ID ({server_id}). Sending correct ID: {local_server.id}"
                            )
                            await websocket.send_json({"type": "config_update", "data": {"server_id": local_server.id}})
                            return  # Stop registration, agent should reconnect

                        # If ID matches, ensure we use the canonical ID
                        server_id = local_server.id
            except Exception as e:
                print(f"Error in local agent discovery: {e}")

        self.agent_connection = websocket

        if server_id:
            try:
                with Session(engine) as session:
                    # Check if server exists
                    server = server_repository.get_by_id(session, server_id)

                    if server:
                        print(f"Agent re-connected for server: {server.name} ({server.id})")
                        # Update status
                        server.is_reachable = True
                        server.last_check = datetime.datetime.utcnow()
                        session.add(server)
                        session.commit()
                    else:
                        print(f"New agent detected. Registering server: {server_id}")
                        # Auto-register new server
                        new_server = Server(
                            id=server_id,
                            name=f"Agent {server_id[:8]}",
                            host=client_host,  # Use actual client IP
                            description="Auto-registered via CLI Agent",
                            is_local=False,
                            is_reachable=True,
                            last_check=datetime.datetime.utcnow(),
                        )
                        session.add(new_server)
                        session.commit()
                        print(f"Server registered: {new_server.name}")

                    self.active_agents[server_id] = websocket
            except Exception as e:
                print(f"Error registering agent server: {e}")
        else:
            # Fallback should not happen for local agent due to auto-discovery above
            # But keep for safety
            pass

    async def handle_message(self, websocket: WebSocket, data: str):
        """Handle incoming WebSocket message."""
        try:
            message = json.loads(data)

            # Handle registration
            if message.get("type") == "register" and message.get("role") == "agent":
                server_id = message.get("server_id")
                await self.register_agent(websocket, server_id)
                return

            # Handle scan results
            if message.get("type") == "scan_result":
                request_id = message.get("requestId")
                if request_id and request_id in self.pending_requests:
                    future = self.pending_requests.pop(request_id)
                    if not future.done():
                        future.set_result(message.get("data"))
                return

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error handling message: {e}")

    async def request_scan(self) -> List[Dict[str, Any]]:
        """Send scan request to agent and wait for result."""
        if not self.agent_connection:
            raise Exception("Agent not connected")

        request_id = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        self.pending_requests[request_id] = future

        try:
            await self.agent_connection.send_json({"type": "scan_request", "requestId": request_id})

            # Wait for result with timeout
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            raise Exception("Scan timed out")
        except Exception as e:
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            raise e


manager = ConnectionManager()


class SystemController:
    """Controller for system information endpoints."""

    def __init__(self):
        """Initialize controller and Docker client if available."""
        self.docker_client = None
        try:
            # Try to connect to Docker socket
            self.docker_client = docker.from_env()
        except Exception:
            pass

        # Define stats file path
        try:
            self.stats_file = Path("/app/database/agent_stats.json")
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error initializing stats file: {e}")
            self.stats_file = Path("/tmp/agent_stats.json")


        self.broadcasting = False

    # Legacy broadcaster and heartbeat receiver removed
    # Now using per-server WebSocket stats in ServersController and AgentController


    async def get_agent_stats(self) -> Dict[str, Any]:
        """
        Get latest agent stats from JSON file.

        Returns cached data with freshness indicator.
        Data is considered stale if > 30 seconds old.
        """
        try:
            if not self.stats_file.exists():
                return {"available": False, "fresh": False, "message": "No agent data available"}

            # Read from JSON file
            try:
                with open(self.stats_file, "r") as f:
                    latest = json.load(f)
            except json.JSONDecodeError:
                return {"available": False, "fresh": False, "message": "Corrupted agent data"}

            # Check freshness (30 second threshold)
            server_time = datetime.datetime.fromisoformat(latest.get("server_timestamp"))
            age_seconds = (datetime.datetime.now() - server_time).total_seconds()
            is_fresh = age_seconds < 30

            return {
                "available": True,
                "fresh": is_fresh,
                "age_seconds": age_seconds,
                "last_update": latest.get("server_timestamp"),
                "data": {
                    "os_name": latest.get("os_name"),
                    "os_version": latest.get("os_version"),
                    "cpu_cores": latest.get("cpu_cores"),
                    "cpu_percent": latest.get("cpu_percent"),
                    "memory_gb": latest.get("memory_gb"),
                    "memory_percent": latest.get("memory_percent"),
                    "disk_gb": latest.get("disk_gb"),
                    "disk_percent": latest.get("disk_percent"),
                    "local_ip": latest.get("local_ip"),
                },
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading agent stats: {str(e)}")

    async def get_agent_connection_status(self) -> Dict[str, Any]:
        """Get real-time agent connection status."""
        return {"connected": manager.agent_connection is not None, "timestamp": datetime.datetime.now().isoformat()}

    async def get_system_info(self, request: Request) -> Dict[str, Any]:
        """
        Get comprehensive system information.
        Attempts to get host information when running in Docker.
        """
        try:
            is_in_docker = self._is_in_docker()

            # Try to get IP from request (better than container IP)
            request_ip = request.url.hostname
            detected_ip = None

            try:
                if request_ip and request_ip != "localhost" and request_ip != "127.0.0.1":
                    # Check if it's a valid private IP
                    import ipaddress

                    ip_obj = ipaddress.ip_address(request_ip)
                    if ip_obj.is_private:
                        detected_ip = request_ip
            except ValueError:
                pass

            network_info = await self._get_network_info()
            if detected_ip:
                network_info["private_ip"] = detected_ip
                network_info["interfaces"] = {"eth0": [{"address": detected_ip, "family": "AF_INET"}]}

            result = {
                "container": {
                    "os": self._get_os_info(),
                    "cpu": self._get_cpu_info(),
                    "memory": self._get_memory_info(),
                    "disks": self._get_disk_info(),
                    "network": network_info,
                    "uptime": self._get_uptime_info(),
                }
                if is_in_docker
                else {},
                "host": await self._get_host_info() if is_in_docker and self.docker_client else {},
                "is_docker": is_in_docker,
            }

            # If not in Docker, move container info to top level
            if not is_in_docker:
                result.update(
                    {
                        "os": self._get_os_info(),
                        "cpu": self._get_cpu_info(),
                        "memory": self._get_memory_info(),
                        "disks": self._get_disk_info(),
                        "network": network_info,
                        "uptime": self._get_uptime_info(),
                    }
                )
                del result["container"]

            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting system info: {str(e)}")

    def _is_in_docker(self) -> bool:
        """Check if running inside Docker container."""
        return os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")

    async def _get_host_info(self) -> Dict[str, Any]:
        """Get host system information via Docker API."""
        if not self.docker_client:
            return {"error": "Docker client not available"}

        try:
            # Get Docker system info
            info = self.docker_client.info()

            # Get Docker version
            version = self.docker_client.version()

            # Detect if running on macOS based on architecture and Docker Desktop
            is_mac = info.get("Architecture") == "aarch64" or "Docker Desktop" in info.get("OperatingSystem", "")

            host_info = {
                "os": {
                    "system": "macOS (Docker Desktop)" if is_mac else info.get("OperatingSystem", "Unknown"),
                    "kernel_version": info.get("KernelVersion", "Unknown"),
                    "architecture": info.get("Architecture", "Unknown"),
                    "os_type": info.get("OSType", "Unknown"),
                    "os_version": "Unknown (cannot detect from Docker)",
                    "is_mac": is_mac,
                    "is_arm": info.get("Architecture") in ["aarch64", "arm64"],
                    "note": "macOS version cannot be detected from inside Docker Desktop VM",
                },
                "cpu": {
                    "cores": info.get("NCPU"),
                    "architecture": info.get("Architecture"),
                    "model": self._detect_cpu_model(info, version),
                },
                "memory": {
                    "total_gb": round(info.get("MemTotal", 0) / (1024**3), 2) if info.get("MemTotal") else None,
                },
                "docker": {
                    "version": version.get("Version"),
                    "api_version": version.get("ApiVersion"),
                    "platform": version.get("Platform"),
                    "server_version": info.get("ServerVersion"),
                    "storage_driver": info.get("Driver"),
                    "containers": {
                        "total": info.get("Containers", 0),
                        "running": info.get("ContainersRunning", 0),
                        "paused": info.get("ContainersPaused", 0),
                        "stopped": info.get("ContainersStopped", 0),
                    },
                    "images": info.get("Images", 0),
                },
                "system": {
                    "name": info.get("Name"),
                    "id": info.get("ID"),
                    "server_version": info.get("ServerVersion"),
                },
            }

            # Try to get more detailed host info by reading /proc from host if mounted
            if os.path.exists("/host/proc/cpuinfo"):
                cpu_details = self._read_host_cpuinfo()
                if cpu_details:
                    host_info["cpu"]["details"] = cpu_details

            if os.path.exists("/host/etc/os-release"):
                os_details = self._read_host_os_release()
                if os_details:
                    host_info["os"]["details"] = os_details

            # Get host disks if available
            if os.path.exists("/host/proc/mounts"):
                host_info["disks"] = self._get_host_disks()

            # Try to get macOS specific info
            if is_mac:
                mac_info = await self._get_macos_info()
                if mac_info:
                    host_info["macos"] = mac_info

            return host_info
        except Exception as e:
            return {"error": str(e)}

    def _detect_cpu_model(self, info: Dict, version: Dict) -> str:
        """Detect CPU model based on architecture and available info."""
        arch = info.get("Architecture", "")
        cores = info.get("NCPU", 0)

        # For Apple Silicon
        if arch in ["aarch64", "arm64"]:
            # Check for Apple Silicon chips
            if "Docker Desktop" in info.get("OperatingSystem", ""):
                # Cannot reliably determine M1/M2/M3/M4 from Docker
                return f"Apple Silicon (ARM64) - {cores} cores allocated to Docker"
            return f"ARM64 - {cores} cores" if cores else "ARM64"

        # For x86_64
        platform = version.get("Platform", {})
        if isinstance(platform, dict):
            platform_name = platform.get("Name", "")
            if platform_name:
                return platform_name

        return "Unknown"

    async def _get_macos_info(self) -> Optional[Dict[str, Any]]:
        """Try to get macOS specific information."""
        try:
            mac_info = {
                "note": "Running in Docker Desktop on macOS",
                "virtualization": "Docker Desktop VM",
            }

            # Try to get additional macOS info via docker exec to host
            # This requires special setup but provides better info
            try:
                # Check if we can access host commands through docker
                if self.docker_client:
                    # Try to inspect the host through Docker API labels or environment
                    info = self.docker_client.info()

                    # Add helpful detection info
                    labels = info.get("Labels", [])
                    if labels:
                        mac_info["host_labels"] = labels

                    # Try to get real macOS info using nsenter to host
                    real_host_info = await self._get_real_host_info_via_nsenter()
                    if real_host_info:
                        mac_info["host_real_info"] = real_host_info

            except Exception:
                pass

            return mac_info
        except Exception:
            return None

    async def _get_real_host_info_via_nsenter(self) -> Optional[Dict[str, Any]]:
        """
        Try to execute commands on the actual host using nsenter.
        This only works if the container is running with privileged: true
        """
        try:
            # Check if we're privileged and can use nsenter
            if not os.path.exists("/proc/1/ns"):
                return None

            host_info = self._execute_host_commands()
            return host_info if host_info else None

        except Exception:
            return None

    def _execute_host_commands(self) -> Dict[str, Any]:
        """Execute commands on host via nsenter."""
        commands = {
            "kernel": "uname -r",
            "hostname": "hostname",
            "cpu_from_proc": "cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d':' -f2",
            "meminfo": "cat /proc/meminfo | grep MemTotal | awk '{print $2}'",
            "uptime": "uptime -p",
            "os_info": "cat /etc/os-release 2>/dev/null || sw_vers 2>/dev/null",
        }

        host_info = {}

        for key, command in commands.items():
            result = self._run_on_host(command)
            if result:
                if key == "meminfo":
                    try:
                        mem_kb = int(result)
                        host_info["memory_total_gb"] = round(mem_kb / (1024**2), 2)
                    except Exception:
                        pass
                elif key == "cpu_from_proc":
                    host_info[key] = result.strip()
                else:
                    host_info[key] = result

        return host_info

    def _run_on_host(self, command: str) -> Optional[str]:
        """Run a single command on the host."""
        import subprocess

        try:
            result = subprocess.run(
                ["nsenter", "-t", "1", "-m", "-u", "-n", "-i", "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    async def get_host_details_via_script(self) -> Dict[str, Any]:
        """
        Get detailed host information by executing a script.
        This endpoint provides instructions to run a script on the host.
        """
        try:
            return {
                "status": "instructions",
                "message": "Para obtener información detallada del Mac host, ejecuta uno de estos comandos:",
                "commands": {
                    "cpu_info": "sysctl -n machdep.cpu.brand_string",
                    "cpu_cores": "sysctl -n hw.physicalcpu hw.logicalcpu",
                    "total_memory": "sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 \" GB\"}'",
                    "macos_version": "sw_vers",
                    "architecture": "uname -m",
                    "hostname": "hostname",
                    "all_info": "system_profiler SPHardwareDataType SPSoftwareDataType",
                },
                "docker_method": {
                    "description": "Ejecutar comando en el host desde Docker",
                    "example": (
                        "docker run --rm --privileged --pid=host alpine "
                        "nsenter -t 1 -m -u -n -i sh -c 'cat /etc/os-release'"
                    ),
                    "note": "Requiere privilegios especiales",
                },
                "current_detection": {
                    "architecture": "aarch64 (ARM64) - Apple Silicon detectado",
                    "cores_allocated": "10 cores asignados a Docker Desktop",
                    "os": "macOS (detectado via Docker Desktop)",
                    "docker_memory_limit": "4.8 GB (configuración de Docker Desktop)",
                    "limitations": [
                        "No se puede determinar el chip exacto (M1/M2/M3/M4)",
                        "No se puede obtener la versión de macOS",
                        "No se puede acceder a la RAM total del Mac",
                        "Los cores mostrados son los asignados a Docker, no los del Mac",
                    ],
                },
                "note": (
                    "Desde Docker Desktop no podemos acceder directamente al macOS host. "
                    "Para información exacta, ejecuta los comandos listados arriba directamente en tu Mac."
                ),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def _read_host_cpuinfo(self) -> Dict[str, Any]:
        """Read CPU info from host /proc/cpuinfo."""
        try:
            cpu_info = {}
            with open("/host/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        cpu_info["model_name"] = line.split(":")[1].strip()
                        break
            return cpu_info
        except Exception:
            return {}

    def _read_host_os_release(self) -> Dict[str, Any]:
        """Read OS release info from host."""
        try:
            os_info = {}
            with open("/host/etc/os-release", "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        os_info[key.lower()] = value.strip('"')
            return os_info
        except Exception:
            return {}

    def _get_host_disks(self) -> Dict[str, Any]:
        """Get host disk information."""
        try:
            # This would require mounting host /proc or using Docker API
            return {"note": "Host disk info requires additional volume mounts"}
        except Exception:
            return {}

    def _get_network_ip(self) -> str:
        """Get local network IP address."""
        import socket

        try:
            # Create a dummy socket to connect to a public IP
            # This doesn't actually connect but helps find the correct interface
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                # connect to an IP that is reachable (Google DNS)
                s.connect(("8.8.8.8", 1))
                ip = s.getsockname()[0]
            except Exception:
                ip = "127.0.0.1"
            finally:
                s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def _get_host_ip_from_docker(self) -> Optional[str]:
        """
        Get host machine IP from Docker container.
        
        Uses multiple methods to detect the host IP:
        1. Docker gateway IP (usually the host on Docker Desktop for Mac)
        2. host.docker.internal resolution
        
        Returns None if not in Docker or cannot detect.
        """
        if not self._is_in_docker():
            return None
        
        try:
            # Method 1: Get default gateway (usually the host IP)
            import subprocess
            import ipaddress
            result = subprocess.run(
                ['sh', '-c', 'ip route | grep default | awk \'{print $3}\''],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout.strip():
                gateway_ip = result.stdout.strip()
                # Verify it's a private IP
                try:
                    ip_obj = ipaddress.ip_address(gateway_ip)
                    if ip_obj.is_private:
                        print(f"Detected host IP from gateway: {gateway_ip}")
                        return gateway_ip
                except ValueError:
                    pass
        except Exception as e:
            print(f"Error getting gateway IP: {e}")
        
        # Method 2: Try resolving host.docker.internal
        try:
            host_ip = socket.gethostbyname('host.docker.internal')
            print(f"Detected host IP from host.docker.internal: {host_ip}")
            return host_ip
        except socket.gaierror:
            pass
        
        return None

    def _get_os_info(self) -> Dict[str, Any]:
        """Get operating system information."""
        try:
            uname = platform.uname()
            return {
                "system": uname.system,
                "node_name": uname.node,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "processor": uname.processor,
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "in_docker": os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"),
                "network_ip": self._get_network_ip(),
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information."""
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)

            return {
                "physical_cores": psutil.cpu_count(logical=False),
                "total_cores": psutil.cpu_count(logical=True),
                "current_frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
                "min_frequency_mhz": round(cpu_freq.min, 2) if cpu_freq else None,
                "max_frequency_mhz": round(cpu_freq.max, 2) if cpu_freq else None,
                "usage_per_core": [round(p, 2) for p in cpu_percent],
                "average_usage": round(sum(cpu_percent) / len(cpu_percent), 2),
                "load_average": [round(x, 2) for x in psutil.getloadavg()] if hasattr(psutil, "getloadavg") else None,
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()

            return {
                "total_gb": round(virtual_mem.total / (1024**3), 2),
                "available_gb": round(virtual_mem.available / (1024**3), 2),
                "used_gb": round(virtual_mem.used / (1024**3), 2),
                "percent_used": round(virtual_mem.percent, 2),
                "swap": {
                    "total_gb": round(swap_mem.total / (1024**3), 2),
                    "used_gb": round(swap_mem.used / (1024**3), 2),
                    "free_gb": round(swap_mem.free / (1024**3), 2),
                    "percent_used": round(swap_mem.percent, 2),
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk information."""
        try:
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total_gb": round(usage.total / (1024**3), 2),
                            "used_gb": round(usage.used / (1024**3), 2),
                            "free_gb": round(usage.free / (1024**3), 2),
                            "percent_used": round(usage.percent, 2),
                        }
                    )
                except PermissionError:
                    continue

            # Disk I/O statistics
            disk_io = psutil.disk_io_counters()
            io_stats = (
                {
                    "read_count": disk_io.read_count,
                    "write_count": disk_io.write_count,
                    "read_bytes_gb": round(disk_io.read_bytes / (1024**3), 2),
                    "write_bytes_gb": round(disk_io.write_bytes / (1024**3), 2),
                    "read_time_ms": disk_io.read_time,
                    "write_time_ms": disk_io.write_time,
                }
                if disk_io
                else None
            )

            return {
                "partitions": partitions,
                "io_statistics": io_stats,
            }
        except Exception as e:
            return {"error": str(e)}

    async def _get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        try:
            # Private IP
            hostname = socket.gethostname()
            try:
                private_ip = socket.gethostbyname(hostname)
            except Exception:
                private_ip = None

            # Public IP
            public_ip = await self._get_public_ip()

            # Network interfaces
            interfaces = []
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            for interface_name, addresses in net_if_addrs.items():
                interface_info = {
                    "name": interface_name,
                    "addresses": [],
                }

                # Get stats if available
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    interface_info.update(
                        {
                            "is_up": stats.isup,
                            "speed_mbps": stats.speed,
                            "mtu": stats.mtu,
                        }
                    )

                # Add addresses
                for addr in addresses:
                    addr_info = {
                        "family": str(addr.family),
                        "address": addr.address,
                    }
                    if addr.netmask:
                        addr_info["netmask"] = addr.netmask
                    if addr.broadcast:
                        addr_info["broadcast"] = addr.broadcast
                    interface_info["addresses"].append(addr_info)

                interfaces.append(interface_info)

            # Network I/O statistics
            net_io = psutil.net_io_counters()
            io_stats = (
                {
                    "bytes_sent_gb": round(net_io.bytes_sent / (1024**3), 2),
                    "bytes_recv_gb": round(net_io.bytes_recv / (1024**3), 2),
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errors_in": net_io.errin,
                    "errors_out": net_io.errout,
                    "drops_in": net_io.dropin,
                    "drops_out": net_io.dropout,
                }
                if net_io
                else None
            )

            return {
                "hostname": hostname,
                "private_ip": private_ip,
                "public_ip": public_ip,
                "interfaces": interfaces,
                "io_statistics": io_stats,
            }
        except Exception as e:
            return {"error": str(e)}

    async def _get_public_ip(self) -> Optional[str]:
        """Get public IP address using external service."""
        services = [
            "https://api.ipify.org?format=json",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
        ]

        for service in services:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(service)
                    if response.status_code == 200:
                        # Handle JSON response
                        if "ipify" in service:
                            return response.json().get("ip")
                        # Handle plain text response
                        return response.text.strip()
            except Exception:
                continue

        return None

    def _get_uptime_info(self) -> Dict[str, Any]:
        """Get system uptime information."""
        try:
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time

            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            return {
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": int(uptime.total_seconds()),
                "uptime_formatted": f"{days}d {hours}h {minutes}m {seconds}s",
                "uptime_days": days,
                "uptime_hours": hours,
                "uptime_minutes": minutes,
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_docker_info(self) -> Dict[str, Any]:
        """Get Docker-specific information if running in container."""
        try:
            is_docker = os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv")

            info = {
                "running_in_docker": is_docker,
            }

            if is_docker:
                # Try to read container ID
                try:
                    with open("/proc/self/cgroup", "r") as f:
                        for line in f:
                            if "docker" in line or "containerd" in line:
                                parts = line.strip().split("/")
                                if len(parts) > 0:
                                    container_id = parts[-1]
                                    if container_id and len(container_id) >= 12:
                                        info["container_id"] = container_id[:12]
                                        break
                except Exception:
                    pass

                # Check for Docker environment variables
                info["environment"] = {
                    "hostname": os.environ.get("HOSTNAME"),
                    "path": os.environ.get("PATH"),
                }

                # Try to get capabilities
                try:
                    # Check if we can reboot (capability check)
                    info["capabilities"] = {
                        "can_reboot": os.access("/sbin/reboot", os.X_OK) or os.access("/usr/sbin/reboot", os.X_OK),
                    }
                except Exception:
                    pass

            return info
        except Exception as e:
            return {"error": str(e)}

    async def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick system statistics (lightweight)."""
        try:
            # Try to read from stats file (latest heartbeat)
            try:
                if os.path.exists(self.stats_file):
                    with open(self.stats_file, "r") as f:
                        stats = json.load(f)
                        # Check freshness (e.g. 15 seconds to be safe)
                        if stats.get("server_timestamp"):
                            last_update = datetime.datetime.fromisoformat(stats["server_timestamp"])
                            if (datetime.datetime.now() - last_update).total_seconds() < 15:
                                return {
                                    "cpu_percent": stats.get("cpu_percent", 0),
                                    "memory_percent": stats.get("memory_percent", 0),
                                    "memory_available_gb": 0, 
                                    "disk_percent": stats.get("disk_percent", 0),
                                    "network_ip": stats.get("local_ip", ""),
                                    "agent_connected": True,
                                    "timestamp": stats.get("timestamp"),
                                }
            except Exception:
                pass

            # If no agent stats, return empty/zero stats
            # We do NOT want to show Docker container stats
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_available_gb": 0,
                "disk_percent": 0,
                "network_ip": "Waiting for Agent...",
                "agent_connected": False,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting quick stats: {str(e)}")

    async def get_agent_config(self) -> Dict[str, Any]:
        """
        Leer configuración del LocalRun Agent (macOS).

        El agente guarda su puerto en ~/.localrun/agent.json
        Esto permite al frontend descubrir el puerto automáticamente.
        """
        from pathlib import Path
        import json

        try:
            config_path = Path.home() / ".localrun" / "agent.json"

            if not config_path.exists():
                raise HTTPException(status_code=404, detail="LocalRun Agent config not found. Install the agent first.")

            with open(config_path) as f:
                config = json.load(f)

            return {
                "port": config.get("port", 47777),
                "version": config.get("version", "unknown"),
                "pid": config.get("pid"),
                "started_at": config.get("started_at"),
                "url": f"http://localhost:{config.get('port', 47777)}",
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def check_agent_status(self) -> Dict[str, Any]:
        """
        Verificar si el agente está corriendo.

        Intenta leer la config y luego hace ping al puerto.
        """
        try:
            # Intentar leer config
            try:
                config = await self.get_agent_config()
                port = config["port"]
            except HTTPException:
                return {
                    "installed": False,
                    "running": False,
                    "message": "Agent not installed",
                }

            # Intentar hacer ping al agente
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    response = await client.get(f"http://localhost:{port}/api/ping")

                    if response.status_code == 200:
                        return {
                            "installed": True,
                            "running": True,
                            "port": port,
                            "url": f"http://localhost:{port}",
                            "message": "Agent running",
                        }
            except Exception:
                pass

            return {
                "installed": True,
                "running": False,
                "port": port,
                "message": "Agent installed but not running. Run: localrun-agent start",
            }

        except Exception as e:
            return {
                "installed": False,
                "running": False,
                "message": str(e),
            }

    async def get_agent_info(self) -> Dict[str, Any]:
        """
        Get detailed system information from LocalRun Agent.

        Returns macOS-specific information like version, CPU model, etc.
        """
        try:
            # Check if agent is running
            status = await self.check_agent_status()

            if not status.get("running"):
                raise HTTPException(status_code=503, detail="Agent not running. Start it with: localrun-agent start")

            port = status.get("port", 47777)

            # Fetch system info from agent
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"http://localhost:{port}/api/system/info")

                if response.status_code == 200:
                    return response.json()
                else:
                    raise HTTPException(status_code=response.status_code, detail="Failed to get info from agent")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with agent: {str(e)}")


# Singleton instance
system_controller = SystemController()
