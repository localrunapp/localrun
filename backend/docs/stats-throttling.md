# Stats Throttling Implementation

## Problema
Los CLI agents envían estadísticas (CPU, memoria, disco, etc.) al backend con alta frecuencia. Anteriormente, **cada stat** se guardaba en la base de datos TinyDB, lo que podía saturar el almacenamiento con datos redundantes.

## Solución Implementada

### Comportamiento Actual
✅ **WebSocket (Tiempo Real)**: Todos los stats se reenvían al frontend inmediatamente por WebSocket  
✅ **Base de Datos (Throttled)**: Solo se guarda 1 stat por minuto en TinyDB

### Cambios Realizados

#### 1. `ServersController.__init__()` (líneas 68-70)
```python
# Throttling: Track last DB save per server (server_id -> timestamp)
self.last_db_save: Dict[str, datetime] = {}
self.db_save_interval_seconds = 60  # Save to DB once per minute
```

Se agregó un diccionario para rastrear el último timestamp de guardado en BD por cada servidor.

#### 2. `ServersController.add_server_stats()` (líneas 384-418)
```python
async def add_server_stats(self, server_id: str, stats: Dict[str, Any]):
    """
    Add stats for a server (called by agent).
    
    - Always broadcasts to WebSocket subscribers in real-time
    - Only saves to DB once per minute to prevent saturation
    """
    # Verify server exists
    await self.get_server(server_id)
    
    # Check if we should save to DB (throttling)
    now = datetime.utcnow()
    should_save_to_db = False
    
    if server_id not in self.last_db_save:
        # First time for this server - save
        should_save_to_db = True
    else:
        # Check if enough time has passed
        time_since_last_save = (now - self.last_db_save[server_id]).total_seconds()
        if time_since_last_save >= self.db_save_interval_seconds:
            should_save_to_db = True
    
    # Save to DB only if throttle allows
    if should_save_to_db:
        self.stats_storage.add_stats(server_id, stats)
        self.last_db_save[server_id] = now
        logger.debug(f"Stats saved to DB for server {server_id}")
    else:
        logger.debug(f"Stats skipped DB save for server {server_id} (throttled)")

    # ALWAYS broadcast to WebSocket subscribers (real-time)
    await self.stats_manager.broadcast(
        server_id, {"type": "stats_update", "server_id": server_id, "data": stats}
    )
```

### Flujo de Datos

```
CLI Agent (cada 5s) 
    ↓
WebSocket: /agent/servers/{server_id}/stats
    ↓
agent.py: websocket_agent_stats() [línea 533]
    ↓
servers_controller.add_server_stats()
    ↓
    ├─→ [SIEMPRE] WebSocket broadcast → Frontend (tiempo real)
    └─→ [CADA 60s] TinyDB save → Persistencia
```

### Beneficios

1. **Tiempo Real**: El frontend recibe todas las actualizaciones sin delay
2. **Eficiencia**: La BD solo guarda 1 stat/minuto (60x menos escrituras)
3. **Histórico**: Se mantiene suficiente granularidad para gráficos históricos
4. **Escalabilidad**: Reduce I/O en disco significativamente

### Configuración

Para cambiar el intervalo de guardado, modificar en `servers.py`:
```python
self.db_save_interval_seconds = 60  # Cambiar a 120 para 2 minutos, etc.
```

## Archivos Modificados

- `/Users/guillermofarias/Sites/localrun/localrun/backend/app/controllers/servers.py`
  - Líneas 68-70: Inicialización del throttling
  - Líneas 384-418: Lógica de throttling en `add_server_stats()`
