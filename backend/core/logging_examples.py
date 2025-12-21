"""
Ejemplos de uso del sistema de logging flexible de LocalRun.

El nuevo sistema permite controlar el destino de los logs mediante flags:
- store: Guardar en base de datos (default: False)
- console: Mostrar en consola (default: True)
"""

from core.logger import log

# =============================================================================
# CASO 1: Debug/Desarrollo (Solo Consola)
# =============================================================================
# Útil para logs de debugging que no quieres guardar en BD

log("debug", "auth", "Procesando login para usuario X")
log("info", "api", "Request recibido en /api/servers")

# Resultado:
# ✅ Se muestra en consola
# ❌ NO se guarda en BD
# ❌ NO se transmite por WebSocket


# =============================================================================
# CASO 2: Métricas Silenciosas (Solo BD)
# =============================================================================
# Útil para métricas y analytics sin ruido en consola

log(
    "info",
    "metrics",
    "API request procesado",
    metadata={
        "tags": ["api", "performance"],
        "endpoint": "/api/servers",
        "method": "GET",
        "duration_ms": 45,
        "status_code": 200,
    },
    store=True,
    console=False,
)

# Resultado:
# ❌ NO se muestra en consola
# ✅ Se guarda en BD
# ✅ Se transmite por WebSocket al frontend
# ✅ Filtrable por tags en frontend


# =============================================================================
# CASO 3: Eventos Importantes (Ambos)
# =============================================================================
# Útil para eventos que necesitas ver Y guardar

log(
    "error",
    "services",
    "Tunnel connection failed",
    metadata={
        "tags": ["tunnel", "error"],
        "trace": "req_xyz_789",
        "server_id": "srv_123",
        "server_name": "my-server",
        "error_code": "CONN_TIMEOUT",
        "retry_count": 3,
    },
    store=True,
    console=True,
)

# Resultado:
# ✅ Se muestra en consola con formato: "Tunnel connection failed [tags: tunnel, error] [trace: req_xyz_789]"
# ✅ Se guarda en BD con metadata completo
# ✅ Se transmite por WebSocket
# ✅ Correlacionable por trace ID


# =============================================================================
# CASO 4: Logs con Trace para Debugging
# =============================================================================
# Útil para seguir el flujo de una request a través de múltiples módulos

trace_id = "req_abc_123"

# Inicio de request (solo consola)
log("info", "api", "Request iniciado", metadata={"trace": trace_id})

# Operaciones intermedias (solo consola)
log(
    "debug",
    "database",
    "Query ejecutado",
    metadata={"trace": trace_id, "query_time_ms": 23, "rows": 5},
)

log(
    "debug",
    "cache",
    "Cache miss",
    metadata={"trace": trace_id, "key": "servers_list"},
)

# Resultado final (guardar en BD)
log(
    "info",
    "api",
    "Response enviado",
    metadata={"trace": trace_id, "status": 200, "total_time_ms": 150},
    store=True,
    console=True,
)


# =============================================================================
# CASO 5: Uso con Controller (WebSocket broadcast)
# =============================================================================
# Para logs que necesitan broadcast a clientes WebSocket

from app.controllers.system_logs import system_logs_controller


async def example_with_controller():
    # Nuevo estilo (recomendado)
    await system_logs_controller.log_and_broadcast(
        severity="warning",
        module="websocket",
        message="Connection lost, retrying...",
        metadata={"tags": ["websocket", "connection"], "reconnect_attempts": 2},
        store=True,
        console=True,
    )

    # Estilo legacy (actualizado para funcionar con nueva firma)
    await system_logs_controller.log_and_broadcast(
        module="backend",
        severity="info",
        message="Server started",
        metadata={"server_id": "srv_123", "server_name": "my-server"}
    )


# =============================================================================
# CASO 6: Logs de Diferentes Severidades
# =============================================================================

# Debug (desarrollo)
log("debug", "module", "Variable X = 123")

# Info (operaciones normales)
log("info", "services", "Tunnel started successfully", store=True, console=True)

# Warning (situaciones anormales pero no críticas)
log(
    "warning",
    "agents",
    "Agent response slow",
    metadata={"response_time_ms": 5000},
    store=True,
)

# Error (errores que requieren atención)
log(
    "error",
    "backend",
    "Failed to start service",
    metadata={"tags": ["critical"], "error": "Port already in use"},
    store=True,
    console=True,
)


# =============================================================================
# CASO 7: Metadata Flexible
# =============================================================================

# Puedes agregar cualquier campo en metadata
log(
    "info",
    "custom",
    "Custom event",
    metadata={
        "tags": ["custom", "event"],
        "trace": "trace_123",
        "user_id": "user_456",
        "action": "file_upload",
        "file_size_mb": 15.3,
        "file_type": "image/png",
        "ip_address": "192.168.1.100",
        "custom_field_1": "value1",
        "custom_field_2": {"nested": "object"},
    },
    store=True,
)
