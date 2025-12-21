export function useWebSocket(endpoint, options = {}) {
  const socket = ref(null)
  const isConnected = ref(false)
  const lastMessage = ref(null)
  const error = ref(null)
  const reconnectAttempts = ref(0)
  const reconnectTimer = ref(null)

  const defaultOptions = {
    maxReconnectionDelay: 10000,
    minReconnectionDelay: 1000,
    reconnectionDelayGrowFactor: 1.3,
    maxRetries: 5,
    connectionTimeout: 4000,
    debug: false,
    autoReconnect: true,
    ...options
  }

  function getWebSocketUrl(endpoint) {
    if (!process.client) return null

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const currentHost = window.location.host

    // En desarrollo (puerto 3000), conectar directamente al backend
    // En producción, usar la URL completa con el host actual
    if (currentHost.includes(':3000')) {
      // Desarrollo: conexión directa al backend
      return `${protocol}//localhost:8000${endpoint}`
    } else if (currentHost.includes(':3001')) {
      // Puerto 3001 - producción con proxy
      return `${protocol}//${currentHost}${endpoint}`
    } else {
      // Producción: usar host actual
      return `${protocol}//${currentHost}${endpoint}`
    }
  }

  function scheduleReconnect() {
    if (!defaultOptions.autoReconnect || reconnectAttempts.value >= defaultOptions.maxRetries) {
      if (defaultOptions.debug) {
        console.log('[WS] Max reconnection attempts reached or auto-reconnect disabled')
      }
      return
    }

    const delay = Math.min(
      defaultOptions.minReconnectionDelay * Math.pow(defaultOptions.reconnectionDelayGrowFactor, reconnectAttempts.value),
      defaultOptions.maxReconnectionDelay
    )

    if (defaultOptions.debug) {
      console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.value + 1}/${defaultOptions.maxRetries})`)
    }

    reconnectTimer.value = setTimeout(() => {
      connect()
    }, delay)
  }

  function connect() {
    // Limpiar timer existente
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }

    if (socket.value) return
    if (!process.client) return

    try {
      const wsUrl = getWebSocketUrl(endpoint)
      if (!wsUrl) return

      if (defaultOptions.debug) {
        console.log(`[WS] Connecting to: ${wsUrl}`)
      }

      // WebSocket nativo
      socket.value = new WebSocket(wsUrl)

      socket.value.onopen = () => {
        isConnected.value = true
        error.value = null
        reconnectAttempts.value = 0

        if (defaultOptions.debug) {
          console.log('[WS] Connected successfully')
        }
      }

      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (defaultOptions.debug && data?.type !== 'stats_update') {
            console.log('[WS] Received:', data)
          }
          lastMessage.value = data
        } catch (e) {
          if (defaultOptions.debug) {
            console.warn('[WS] Invalid JSON received:', event.data)
          }
          lastMessage.value = { error: 'Invalid JSON data', raw: event.data }
        }
      }

      socket.value.onclose = (event) => {
        isConnected.value = false

        if (defaultOptions.debug) {
          console.log(`[WS] Connection closed: ${event.code} - ${event.reason}`)
        }

        // Auto-reconectar si no fue cierre manual
        if (event.code !== 1000 && defaultOptions.autoReconnect) {
          reconnectAttempts.value++
          scheduleReconnect()
        }
      }

      socket.value.onerror = (event) => {
        error.value = event
        isConnected.value = false

        if (defaultOptions.debug) {
          console.error('[WS] Connection error:', event)
        }
      }

    } catch (err) {
      error.value = err
      isConnected.value = false

      if (defaultOptions.debug) {
        console.error('[WS] Failed to create WebSocket connection:', err)
      }
    }
  }

  function send(data) {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      if (defaultOptions.debug) {
        console.warn('[WS] Cannot send: WebSocket not connected')
      }
      return false
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      socket.value.send(message)
      return true
    } catch (err) {
      if (defaultOptions.debug) {
        console.error('[WS] Send error:', err)
      }
      return false
    }
  }

  function disconnect() {
    // Limpiar timer de reconexión
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }

    if (socket.value) {
      socket.value.close(1000, 'Manual disconnect')
      socket.value = null
    }
    isConnected.value = false
    error.value = null
    reconnectAttempts.value = 0
  }

  function retry() {
    disconnect()
    setTimeout(() => connect(), 1000)
  }

  // Auto cleanup
  onBeforeUnmount(() => {
    disconnect()
  })

  return {
    // Estado reactivo
    isConnected: readonly(isConnected),
    lastMessage: readonly(lastMessage),
    error: readonly(error),
    reconnectAttempts: readonly(reconnectAttempts),

    // Métodos
    connect,
    disconnect,
    send,
    retry,

    // Estado interno (solo lectura)
    socket: readonly(socket)
  }
}