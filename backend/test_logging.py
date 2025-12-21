#!/usr/bin/env python3
"""
Test script para verificar el sistema de logging flexible.
Este script prueba todas las combinaciones de store/console.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import log

print("=" * 80)
print("TEST 1: Solo Consola (store=False, console=True - DEFAULT)")
print("=" * 80)
print("Llamando: log('info', 'test', 'MENSAJE_CONSOLA_SOLO')")
log("info", "test", "MENSAJE_CONSOLA_SOLO")
print("✅ Debería aparecer arriba en consola")
print("❌ NO debería estar en database/logs.json")
print()

print("=" * 80)
print("TEST 2: Solo BD (store=True, console=False)")
print("=" * 80)
print("Llamando: log('info', 'test', 'MENSAJE_BD_SOLO', store=True, console=False)")
log_id = log("info", "test", "MENSAJE_BD_SOLO", store=True, console=False)
print(f"✅ Log guardado con ID: {log_id}")
print("❌ NO debería aparecer en consola (arriba)")
print("✅ Debería estar en database/logs.json")
print()

print("=" * 80)
print("TEST 3: Ambos (store=True, console=True)")
print("=" * 80)
print("Llamando: log('warning', 'test', 'MENSAJE_AMBOS', metadata={'tags': ['test']}, store=True, console=True)")
log_id = log(
    "warning",
    "test",
    "MENSAJE_AMBOS",
    metadata={"tags": ["test", "verification"]},
    store=True,
    console=True,
)
print(f"✅ Log guardado con ID: {log_id}")
print("✅ Debería aparecer arriba en consola con [tags: test, verification]")
print("✅ Debería estar en database/logs.json")
print()

print("=" * 80)
print("TEST 4: Con Tags y Trace")
print("=" * 80)
print("Llamando: log con tags y trace")
log(
    "error",
    "test",
    "MENSAJE_CON_TRACE",
    metadata={
        "tags": ["websocket", "connection"],
        "trace": "test_trace_123",
        "error_code": "TIMEOUT",
    },
    store=True,
    console=True,
)
print("✅ Debería aparecer arriba con [tags: websocket, connection] [trace: test_trace_123]")
print()

print("=" * 80)
print("TEST 5: Diferentes Severidades")
print("=" * 80)
log("debug", "test", "Debug message")
log("info", "test", "Info message")
log("warning", "test", "Warning message")
log("error", "test", "Error message")
print("✅ Deberían aparecer 4 mensajes arriba con diferentes niveles")
print()

print("=" * 80)
print("TEST 6: Metadata Completo")
print("=" * 80)
log(
    "info",
    "test",
    "MENSAJE_METADATA_COMPLETO",
    metadata={
        "tags": ["api", "performance"],
        "trace": "req_456",
        "server_id": "srv_test",
        "server_name": "test-server",
        "duration_ms": 150,
        "endpoint": "/api/test",
        "custom_field": "custom_value",
    },
    store=True,
    console=True,
)
print("✅ Debería aparecer con tags y trace en consola")
print("✅ Metadata completo debería estar en BD")
print()

print("=" * 80)
print("VERIFICACIÓN MANUAL")
print("=" * 80)
print("Para verificar los resultados:")
print()
print("1. Ver logs en consola:")
print("   docker logs localrun-backend | grep 'MENSAJE_'")
print()
print("2. Ver logs en BD:")
print("   docker exec localrun-backend cat /app/database/logs.json | jq '.[] | select(.message | contains(\"MENSAJE_\"))'")
print()
print("3. Verificar tags:")
print("   docker exec localrun-backend cat /app/database/logs.json | jq '.[] | select(.metadata.tags // [] | contains([\"test\"]))'")
print()
print("4. Verificar trace:")
print("   docker exec localrun-backend cat /app/database/logs.json | jq '.[] | select(.metadata.trace == \"test_trace_123\")'")
print()

print("=" * 80)
print("TESTS COMPLETADOS")
print("=" * 80)
