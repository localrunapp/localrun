/**
 * Composable for managing per-server WebSocket stats connections
 * Connects to /servers/{id}/stats for each server
 */
export function useServerStats(serverId) {
  if (!serverId) {
    throw new Error('useServerStats requires a serverId')
  }

  // Connect to per-server stats endpoint
  const ws = useWebSocket(`/servers/${serverId}/stats`, {
    debug: true,
    maxRetries: 10,
    connectionTimeout: 5000,
    autoReconnect: true
  })

  // Server stats state
  const stats = ref(null)
  const lastUpdate = ref(null)
  const agentStatus = ref(null)

  // Watch for incoming stats
  watch(() => ws.lastMessage.value, (msg) => {
    if (msg && msg.type === 'stats_update') {
      stats.value = msg.data
      lastUpdate.value = Date.now()
    } else if (msg && msg.type === 'agent_status_change') {
      // Handle agent status changes (connect/disconnect)
      agentStatus.value = msg.agent_status
      console.log(`[useWsStats] Agent status changed for ${serverId}:`, msg.agent_status, msg)
    } else if (msg) {
      console.log(`[useWsStats] Unknown message type for ${serverId}:`, msg.type, msg)
    }
  })

  // Computed properties for easy access
  const cpu = computed(() => stats.value?.cpu_percent ?? null)
  const memory = computed(() => ({
    percent: stats.value?.memory_percent ?? null,
    gb: stats.value?.memory_gb ?? null
  }))
  const disk = computed(() => ({
    percent: stats.value?.disk_percent ?? null,
    gb: stats.value?.disk_gb ?? null
  }))
  const network = computed(() => stats.value?.local_ip ?? null)
  const osInfo = computed(() => ({
    name: stats.value?.os_name ?? null,
    version: stats.value?.os_version ?? null,
    cores: stats.value?.cpu_cores ?? null
  }))

  // Check if stats are stale (> 15 seconds old)
  const isStale = computed(() => {
    if (!lastUpdate.value) return true
    return (Date.now() - lastUpdate.value) > 15000
  })

  // Control functions
  function startMonitoring() {
    ws.connect()
  }

  function stopMonitoring() {
    ws.disconnect()
  }

  function retryConnection() {
    ws.retry()
  }

  return {
    // Connection state
    isConnected: ws.isConnected,
    error: ws.error,
    reconnectAttempts: ws.reconnectAttempts,
    isStale,

    // Stats data
    stats,
    cpu,
    memory,
    disk,
    network,
    osInfo,
    lastUpdate,
    agentStatus,

    // Control
    startMonitoring,
    stopMonitoring,
    retryConnection,

    // Raw WebSocket access
    ws
  }
}

/**
 * Composable for managing multiple server stats connections
 * Use this when you need to monitor multiple servers simultaneously
 */
export function useMultiServerStats(serverIds) {
  const connections = ref({})
  const allStats = ref({})
  const allAgentStatuses = ref({})  // NEW: Flat object for agent statuses
  const scopes = {}

  // Watch for changes in server IDs
  watch(() => unref(serverIds), (ids) => {
    if (!Array.isArray(ids)) return

    // Remove connections for servers no longer in the list
    for (const id in connections.value) {
      if (!ids.includes(id)) {
        connections.value[id].stopMonitoring()
        delete connections.value[id]
        delete allStats.value[id]
        delete allAgentStatuses.value[id]  // Clean up agent status

        // Dispose of the effect scope
        if (scopes[id]) {
          scopes[id].stop()
          delete scopes[id]
        }
      }
    }

    // Add connections for new servers
    for (const id of ids) {
      if (!connections.value[id]) {
        // Create an effect scope for this server's composable
        const scope = effectScope()
        scopes[id] = scope

        scope.run(() => {
          const serverStats = useServerStats(id)
          connections.value[id] = serverStats

          // Watch for stats updates
          watch(() => serverStats.stats.value, (stats) => {
            if (stats) {
              allStats.value[id] = stats
            }
          })

          // Watch for agent status updates - NEW
          watch(() => serverStats.agentStatus.value, (status) => {
            if (status) {
              console.log(`[useMultiServerStats] Agent status for ${id}: ${status}`)
              allAgentStatuses.value[id] = status
            }
          })

          // Auto-start monitoring
          serverStats.startMonitoring()
        })
      }
    }
  }, { immediate: true })

  // Cleanup on unmount
  onUnmounted(() => {
    for (const id in connections.value) {
      connections.value[id].stopMonitoring()
    }

    // Dispose all scopes
    for (const id in scopes) {
      scopes[id].stop()
    }
  })

  return {
    allStats,
    allAgentStatuses,  // NEW: Export agent statuses
    connections,

    // Get stats for specific server
    getServerStats: (serverId) => allStats.value[serverId] || null,

    // Get connection for specific server
    getServerConnection: (serverId) => connections.value[serverId] || null
  }
}
