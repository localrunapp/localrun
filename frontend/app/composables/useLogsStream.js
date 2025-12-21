/**
 * Composable for system logs streaming
 * Connects to /system/logs/stream WebSocket for real-time logs
 */
export function useLogsStream() {
    const logs = ref([])
    const isConnected = ref(false)
    const error = ref(null)

    // Filters
    const categoryFilter = ref('all')
    const levelFilter = ref('all')
    const serverFilter = ref('all')

    // WebSocket connection
    let ws = null
    let reconnectTimeout = null

    // Filtered logs
    const filteredLogs = computed(() => {
        return logs.value.filter(log => {
            if (categoryFilter.value !== 'all' && log.category !== categoryFilter.value) {
                return false
            }
            if (levelFilter.value !== 'all' && log.level !== levelFilter.value) {
                return false
            }
            if (serverFilter.value !== 'all' && log.server_id !== serverFilter.value) {
                return false
            }
            return true
        })
    })

    function connect() {
        if (ws) return

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.hostname}:8000/system/logs/stream`

        ws = new WebSocket(wsUrl)

        ws.onopen = () => {
            isConnected.value = true
            error.value = null
            console.log('[Logs] WebSocket connected')
        }

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)

                if (message.type === 'initial_logs') {
                    // Replace logs with initial batch
                    logs.value = message.data
                } else if (message.type === 'log_entry') {
                    // Prepend new log (newest first)
                    logs.value.unshift(message.data)

                    // Keep only last 500 logs in memory
                    if (logs.value.length > 500) {
                        logs.value = logs.value.slice(0, 500)
                    }
                }
            } catch (err) {
                console.error('[Logs] Error parsing message:', err)
            }
        }

        ws.onerror = (err) => {
            error.value = 'WebSocket error'
            console.error('[Logs] WebSocket error:', err)
        }

        ws.onclose = () => {
            isConnected.value = false
            ws = null
            console.log('[Logs] WebSocket closed, reconnecting in 5s...')

            // Auto-reconnect
            reconnectTimeout = setTimeout(() => {
                connect()
            }, 5000)
        }
    }

    function disconnect() {
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout)
            reconnectTimeout = null
        }

        if (ws) {
            ws.close()
            ws = null
        }

        isConnected.value = false
    }

    function clearLogs() {
        logs.value = []
    }

    // Auto-connect on mount
    onMounted(() => {
        if (import.meta.client) {
            connect()
        }
    })

    // Auto-disconnect on unmount
    onUnmounted(() => {
        disconnect()
    })

    return {
        logs,
        filteredLogs,
        isConnected,
        error,

        // Filters
        categoryFilter,
        levelFilter,
        serverFilter,

        // Actions
        connect,
        disconnect,
        clearLogs
    }
}
