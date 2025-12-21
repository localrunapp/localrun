"""
Docker Service - Operaciones de bajo nivel con Docker

Maneja todas las operaciones con contenedores Docker:
- Crear/detener/eliminar contenedores
- Listar contenedores
- Verificar estado de contenedores
- Operaciones genéricas de Docker
"""

import logging
from typing import Dict, List, Optional, Any

import docker
from docker.errors import APIError, NotFound

logger = logging.getLogger(__name__)


class DockerService:
    """Servicio para operaciones Docker de bajo nivel"""

    def __init__(self):
        """Inicializar cliente Docker"""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Cliente Docker inicializado correctamente")
        except Exception as e:
            logger.error(f"Error conectando a Docker: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Verificar si Docker está disponible"""
        return self.client is not None

    # ========== Operaciones con Contenedores ==========

    def create_container(
        self,
        image: str,
        name: str,
        command: Optional[List[str]] = None,
        network: str = "bridge",
        extra_hosts: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        detach: bool = True,
        restart_policy: Optional[Dict[str, str]] = None,
        mem_limit: Optional[str] = None,
        cpu_quota: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """
        Crear y ejecutar un contenedor Docker

        Args:
            image: Imagen Docker
            name: Nombre del contenedor
            command: Comando a ejecutar
            network: Red Docker
            extra_hosts: Hosts adicionales
            labels: Labels del contenedor
            detach: Ejecutar en background
            restart_policy: Política de reinicio
            mem_limit: Límite de memoria
            cpu_quota: Límite de CPU
            **kwargs: Argumentos adicionales

        Returns:
            Contenedor creado
        """
        if not self.is_available():
            raise RuntimeError("Docker no está disponible")

        try:
            # Pull de la imagen si no existe
            try:
                self.client.images.pull(image)
                logger.info(f"Imagen pulled: {image}")
            except Exception as e:
                logger.warning(f"No se pudo hacer pull de la imagen {image}: {e}")

            # Configuración del contenedor
            config = {
                "image": image,
                "name": name,
                "detach": detach,
                "network": network,
            }

            if command:
                config["command"] = command

            if extra_hosts:
                config["extra_hosts"] = extra_hosts

            if labels:
                config["labels"] = labels

            if restart_policy:
                config["restart_policy"] = restart_policy

            if mem_limit:
                config["mem_limit"] = mem_limit

            if cpu_quota:
                config["cpu_quota"] = cpu_quota
                config["cpu_period"] = 100000

            # Agregar kwargs adicionales
            config.update(kwargs)

            # Crear contenedor
            container = self.client.containers.run(**config)

            logger.info(f"Contenedor creado: {name} (ID: {container.id[:12]})")
            return container

        except Exception as e:
            logger.error(f"Error creando contenedor {name}: {e}")
            raise

    def get_container(self, name_or_id: str) -> Optional[Any]:
        """
        Obtener contenedor por nombre o ID

        Args:
            name_or_id: Nombre o ID del contenedor

        Returns:
            Contenedor si existe, None si no
        """
        if not self.is_available():
            return None

        try:
            container = self.client.containers.get(name_or_id)
            container.reload()
            return container
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo contenedor {name_or_id}: {e}")
            return None

    def list_containers(self, all: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Listar contenedores

        Args:
            all: Incluir contenedores detenidos
            filters: Filtros de búsqueda

        Returns:
            Lista de contenedores
        """
        if not self.is_available():
            return []

        try:
            return self.client.containers.list(all=all, filters=filters)
        except Exception as e:
            logger.error(f"Error listando contenedores: {e}")
            return []

    def start_container(self, name_or_id: str) -> bool:
        """
        Iniciar contenedor

        Args:
            name_or_id: Nombre o ID del contenedor

        Returns:
            True si se inició correctamente
        """
        container = self.get_container(name_or_id)
        if not container:
            logger.error(f"Contenedor no encontrado: {name_or_id}")
            return False

        try:
            if container.status == "running":
                logger.info(f"Contenedor ya está corriendo: {name_or_id}")
                return True

            container.start()
            logger.info(f"Contenedor iniciado: {name_or_id}")
            return True
        except Exception as e:
            logger.error(f"Error iniciando contenedor {name_or_id}: {e}")
            return False

    def stop_container(self, name_or_id: str, timeout: int = 10) -> bool:
        """
        Detener contenedor

        Args:
            name_or_id: Nombre o ID del contenedor
            timeout: Timeout en segundos

        Returns:
            True si se detuvo correctamente
        """
        container = self.get_container(name_or_id)
        if not container:
            logger.error(f"Contenedor no encontrado: {name_or_id}")
            return False

        try:
            if container.status != "running":
                logger.info(f"Contenedor ya está detenido: {name_or_id}")
                return True

            container.stop(timeout=timeout)
            logger.info(f"Contenedor detenido: {name_or_id}")
            return True
        except Exception as e:
            logger.error(f"Error deteniendo contenedor {name_or_id}: {e}")
            return False

    def remove_container(self, name_or_id: str, force: bool = False) -> bool:
        """
        Eliminar contenedor

        Args:
            name_or_id: Nombre o ID del contenedor
            force: Forzar eliminación

        Returns:
            True si se eliminó correctamente
        """
        container = self.get_container(name_or_id)
        if not container:
            logger.warning(f"Contenedor no encontrado: {name_or_id}")
            return True  # Ya no existe

        try:
            container.remove(force=force)
            logger.info(f"Contenedor eliminado: {name_or_id}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando contenedor {name_or_id}: {e}")
            return False

    def get_container_status(self, name_or_id: str) -> Optional[str]:
        """
        Obtener estado del contenedor

        Args:
            name_or_id: Nombre o ID del contenedor

        Returns:
            Estado del contenedor (running, stopped, etc.) o None
        """
        container = self.get_container(name_or_id)
        if not container:
            return None

        return container.status

    def get_container_logs(self, name_or_id: str, tail: int = 100, follow: bool = False) -> Optional[str]:
        """
        Obtener logs del contenedor

        Args:
            name_or_id: Nombre o ID del contenedor
            tail: Número de líneas
            follow: Seguir logs

        Returns:
            Logs del contenedor
        """
        container = self.get_container(name_or_id)
        if not container:
            return None

        try:
            logs = container.logs(tail=tail, follow=follow)
            return logs.decode("utf-8") if isinstance(logs, bytes) else logs
        except Exception as e:
            logger.error(f"Error obteniendo logs de {name_or_id}: {e}")
            return None

    # ========== Operaciones Avanzadas ==========

    def get_container_details(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener detalles completos del contenedor

        Args:
            name_or_id: Nombre o ID del contenedor

        Returns:
            Dict con detalles del contenedor
        """
        container = self.get_container(name_or_id)
        if not container:
            return None

        try:
            return {
                "id": container.id[:12],
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs.get("Created", "unknown"),
                "labels": container.labels,
                "ports": container.attrs.get("NetworkSettings", {}).get("Ports", {}),
                "networks": list(container.attrs.get("NetworkSettings", {}).get("Networks", {}).keys()),
            }
        except Exception as e:
            logger.error(f"Error obteniendo detalles de {name_or_id}: {e}")
            return None

    def list_containers_by_label(self, label: str, value: Optional[str] = None, all: bool = True) -> List[Any]:
        """
        Listar contenedores por label

        Args:
            label: Label a buscar
            value: Valor del label (opcional)
            all: Incluir contenedores detenidos

        Returns:
            Lista de contenedores
        """
        filters = {}
        if value:
            filters["label"] = f"{label}={value}"
        else:
            filters["label"] = label

        return self.list_containers(all=all, filters=filters)

    def cleanup_stopped_containers(self, label: Optional[str] = None) -> int:
        """
        Limpiar contenedores detenidos

        Args:
            label: Label para filtrar (opcional)

        Returns:
            Número de contenedores eliminados
        """
        if not self.is_available():
            return 0

        filters = {"status": "exited"}
        if label:
            filters["label"] = label

        containers = self.list_containers(all=True, filters=filters)
        count = 0

        for container in containers:
            try:
                container.remove()
                count += 1
                logger.info(f"Contenedor eliminado: {container.name}")
            except Exception as e:
                logger.error(f"Error eliminando contenedor {container.name}: {e}")

        logger.info(f"Limpieza completada: {count} contenedores eliminados")
        return count

    # ========== Operaciones con Imágenes ==========

    def pull_image(self, image: str) -> bool:
        """
        Hacer pull de una imagen Docker

        Args:
            image: Nombre de la imagen

        Returns:
            True si se descargó correctamente
        """
        if not self.is_available():
            return False

        try:
            self.client.images.pull(image)
            logger.info(f"Imagen pulled: {image}")
            return True
        except Exception as e:
            logger.error(f"Error haciendo pull de {image}: {e}")
            return False

    def image_exists(self, image: str) -> bool:
        """
        Verificar si una imagen existe localmente

        Args:
            image: Nombre de la imagen

        Returns:
            True si existe
        """
        if not self.is_available():
            return False

        try:
            self.client.images.get(image)
            return True
        except NotFound:
            return False
        except Exception as e:
            logger.error(f"Error verificando imagen {image}: {e}")
            return False


# Instancia singleton
docker_service = DockerService()
