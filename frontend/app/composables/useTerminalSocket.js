import { useWebSocket } from './useWebSocket'

export function useTerminalSocket(serverId = null) {
  // Construct URL with optional server_id
  const url = serverId
    ? `/ws/terminal/client?server_id=${serverId}`
    : '/ws/terminal/client'

  // Usar el composable genérico de WebSocket
  const ws = useWebSocket(url, {
    debug: true,
    maxRetries: 5,
    connectionTimeout: 10000,
    autoReconnect: true
  })

  // Estado específico de la terminal
  const status = computed(() => {
    if (!ws.isConnected.value && ws.reconnectAttempts.value === 0) return 'connecting'
    if (ws.isConnected.value) return 'online'
    return 'offline'
  })

  // Métodos específicos de terminal
  const sendInput = (data) => ws.send({ type: 'input', data })
  const sendResize = (cols, rows) => ws.send({ type: 'resize', cols, rows })

  return {
    // Estado
    status,
    isConnected: ws.isConnected,
    lastMessage: ws.lastMessage,
    error: ws.error,
    reconnectAttempts: ws.reconnectAttempts,

    // Métodos
    connect: ws.connect,
    disconnect: ws.disconnect,
    retry: ws.retry,
    sendInput,
    sendResize
  }
}