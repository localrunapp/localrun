"""
Server routes - API endpoints for server management.
"""

from fastapi import APIRouter
from app.controllers.servers import ServersController

router = APIRouter(prefix="/servers", tags=["Servers"])
servers_controller = ServersController()

# Create server
router.add_api_route("", servers_controller.create_server, methods=["POST"])

# Get all servers
router.add_api_route("", servers_controller.get_all_servers, methods=["GET"])

# Get server by ID
router.add_api_route(
    "/{server_id}", servers_controller.get_server_by_id, methods=["GET"]
)

# Get server detail (with agent status)
router.add_api_route(
    "/{server_id}/detail", servers_controller.get_server_detail, methods=["GET"]
)

# Update server
router.add_api_route("/{server_id}", servers_controller.update_server, methods=["PUT"])

# Delete server
router.add_api_route(
    "/{server_id}", servers_controller.delete_server, methods=["DELETE"]
)

# Check connectivity
router.add_api_route(
    "/{server_id}/connectivity", servers_controller.check_connectivity, methods=["POST"]
)

# Scan server
router.add_api_route("/{server_id}/scan", servers_controller.scan, methods=["POST"])

# Test port
router.add_api_route(
    "/{server_id}/test-port", servers_controller.test_port, methods=["POST"]
)


# Stats WebSocket
router.add_api_websocket_route(
    "/{server_id}/stats", servers_controller.handle_stats_websocket
)

# Terminal WebSocket
router.add_api_websocket_route(
    "/{server_id}/terminal", servers_controller.handle_terminal_websocket
)
