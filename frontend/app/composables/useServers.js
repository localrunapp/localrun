/**
 * Enhanced Server Management Composable
 * Encapsulates all server logic: CRUD, metrics, agent status, WebSocket communication
 */
import { ref, computed, watch, watchEffect } from 'vue';
import { useMultiServerStats } from './useWsStats';

export const useServers = () => {
    const api = useApi();

    // ========== Basic CRUD Operations ==========

    const getServers = async (onlyReachable = false) => {
        const query = onlyReachable ? '?only_reachable=true' : '';
        return await api.get(`/servers${query}`);
    };

    const getServer = async (id) => {
        return await api.get(`/servers/${id}`);
    };

    const createServer = async (data) => {
        return await api.post('/servers', data);
    };

    const updateServer = async (id, data) => {
        return await api.put(`/servers/${id}`, data);
    };

    const deleteServer = async (id) => {
        return await api.delete(`/servers/${id}`);
    };

    const scanServer = async (id) => {
        return await api.post(`/servers/${id}/scan`);
    };

    const checkConnectivity = async (id, port = null) => {
        const query = port ? `?port=${port}` : '';
        return await api.post(`/servers/${id}/check${query}`);
    };

    const scanNetwork = async (network = null) => {
        const query = network ? `?network=${network}` : '';
        return await api.post(`/servers/scan-network${query}`);
    };

    const getAgentStatus = async () => {
        return await api.get('/system/agent/status');
    };

    return {
        getServers,
        getServer,
        createServer,
        updateServer,
        deleteServer,
        scanServer,
        checkConnectivity,
        scanNetwork,
        getAgentStatus
    };
};

/**
 * Server List Management with Real-time Updates
 * Manages a list of servers with automatic metrics and agent status updates
 */
export const useServersList = () => {
    const api = useApi();
    const servers = ref([]);
    const loading = ref(false);
    const error = ref(null);

    // Get server IDs for WebSocket monitoring
    const serverIds = computed(() => servers.value.map(s => s.id));

    // Set up WebSocket connections for all servers
    const { allStats, allAgentStatuses, connections } = useMultiServerStats(serverIds);

    // ========== Auto-update Agent Status ==========

    // When we receive stats, agent is connected
    watch(
        allStats,
        (newStats) => {
            servers.value.forEach((server) => {
                if (newStats[server.id]) {
                    // Receiving stats = agent connected
                    if (server.agent_status !== 'connected') {
                        server.agent_status = 'connected';
                    }
                }
            });
        },
        { deep: true }
    );

    // When we receive agent_status_change notification
    watch(
        allAgentStatuses,
        (newStatuses) => {
            console.log('[useServersList] Agent statuses changed:', newStatuses);
            servers.value.forEach((server) => {
                const newStatus = newStatuses[server.id];
                if (newStatus && server.agent_status !== newStatus) {
                    console.log(`[useServersList] Updating ${server.name}: ${server.agent_status} -> ${newStatus}`);
                    server.agent_status = newStatus;

                    // Clear stats when agent disconnects
                    if (newStatus === 'disconnected') {
                        console.log(`[useServersList] Clearing stats for ${server.name}`);
                        delete allStats.value[server.id];
                    }
                }
            });
        },
        { deep: true }
    );

    // ========== Server Operations ==========

    const fetchServers = async (onlyReachable = false) => {
        loading.value = true;
        error.value = null;
        try {
            const query = onlyReachable ? '?only_reachable=true' : '';
            const response = await api.get(`/servers${query}`);
            servers.value = response || [];
            return servers.value;
        } catch (e) {
            error.value = e.message || 'Failed to load servers';
            console.error('Error fetching servers:', e);
            throw e;
        } finally {
            loading.value = false;
        }
    };

    const createServer = async (data) => {
        try {
            const newServer = await api.post('/servers', data);
            // Refresh list to include new server
            await fetchServers();
            return newServer;
        } catch (e) {
            error.value = e.message || 'Failed to create server';
            throw e;
        }
    };

    const updateServer = async (id, data) => {
        try {
            const updated = await api.put(`/servers/${id}`, data);
            // Update in local list
            const index = servers.value.findIndex(s => s.id === id);
            if (index !== -1) {
                servers.value[index] = { ...servers.value[index], ...updated };
            }
            return updated;
        } catch (e) {
            error.value = e.message || 'Failed to update server';
            throw e;
        }
    };

    const deleteServer = async (id) => {
        try {
            await api.delete(`/servers/${id}`);
            // Remove from local list
            servers.value = servers.value.filter(s => s.id !== id);
        } catch (e) {
            error.value = e.message || 'Failed to delete server';
            throw e;
        }
    };

    // ========== Helper Functions ==========

    const getServerById = (id) => {
        return servers.value.find(s => s.id === id);
    };

    const getServerStats = (id) => {
        return allStats.value[id] || null;
    };

    const getServerConnection = (id) => {
        return connections.value[id] || null;
    };

    // Format host with network IP for local servers
    const formatHost = (server) => {
        if (server.is_local) {
            const localIp = allStats.value[server.id]?.local_ip || server.network_ip;
            if (localIp && localIp !== "...") {
                return `${server.host} / ${localIp}`;
            }
            return server.host;
        }
        return server.host;
    };

    // Get network IP (for modals, etc)
    const networkIp = computed(() => {
        const localServer = servers.value.find(s => s.is_local);
        if (localServer) {
            return (
                allStats.value[localServer.id]?.local_ip ||
                localServer.network_ip ||
                'localhost'
            );
        }
        return 'localhost';
    });

    return {
        // State
        servers,
        loading,
        error,

        // Real-time data
        allStats,
        connections,
        networkIp,

        // Operations
        fetchServers,
        createServer,
        updateServer,
        deleteServer,

        // Helpers
        getServerById,
        getServerStats,
        getServerConnection,
        formatHost
    };
};
