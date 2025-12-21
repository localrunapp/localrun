import { defineStore } from 'pinia';

export const useServerStore = defineStore('serverStore', {
    state: () => ({
        localServerId: null,
        servers: [],
    }),

    actions: {
        async fetchServers() {
            try {
                const api = useApi();
                this.servers = await api.get('/servers');

                // Find and cache localhost server ID
                const localServer = this.servers.find(s => s.is_local);
                if (localServer) {
                    this.localServerId = localServer.id;
                    console.log(`Localhost server ID cached: ${this.localServerId}`);
                }

                return this.servers;
            } catch (error) {
                console.error('Error fetching servers:', error);
                return [];
            }
        },

        getServerById(serverId) {
            return this.servers.find(s => s.id === serverId);
        },

        getLocalhostServer() {
            return this.servers.find(s => s.is_local);
        },
    },

    persist: {
        paths: ['localServerId']
    }
});
