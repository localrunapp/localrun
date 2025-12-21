import { ref } from 'vue';

export const useMetrics = () => {
    const config = useRuntimeConfig();
    const authStore = useAuthStore();

    const loading = ref(false);
    const error = ref(null);

    const getServerHistory = async (serverId: string, hours: number = 24) => {
        try {
            loading.value = true;
            error.value = null;

            const response = await $fetch(`/api/metrics/servers/${serverId}/history`, {
                params: { hours },
                headers: {
                    Authorization: `Bearer ${authStore.token}`
                }
            });

            return response;
        } catch (e) {
            console.error(`Error fetching history for server ${serverId}:`, e);
            error.value = e;
            return null;
        } finally {
            loading.value = false;
        }
    };

    const getAggregateMetrics = async () => {
        try {
            loading.value = true;
            error.value = null;

            const response = await $fetch(`/api/metrics/aggregate`, {
                headers: {
                    Authorization: `Bearer ${authStore.token}`
                }
            });

            return response;
        } catch (e) {
            console.error('Error fetching aggregate metrics:', e);
            error.value = e;
            return null;
        } finally {
            loading.value = false;
        }
    };

    /**
     * Aggregate historical data from multiple servers by timestamp
     */
    const aggregateHistoricalData = (serverHistories: any[]) => {
        const timestampMap = new Map();

        serverHistories.forEach(history => {
            if (!history || !history.entries) return;

            history.entries.forEach((entry: any) => {
                if (!timestampMap.has(entry.timestamp)) {
                    timestampMap.set(entry.timestamp, {
                        timestamp: entry.timestamp,
                        cpu_values: [],
                        memory_values: [],
                        disk_values: []
                    });
                }

                const data = timestampMap.get(entry.timestamp);
                data.cpu_values.push(entry.cpu_percent);
                data.memory_values.push(entry.memory_percent);
                data.disk_values.push(entry.disk_percent);
            });
        });

        // Calculate averages and sort by timestamp
        return Array.from(timestampMap.values())
            .map(data => ({
                timestamp: data.timestamp,
                cpu_percent: data.cpu_values.reduce((a: number, b: number) => a + b, 0) / data.cpu_values.length,
                memory_percent: data.memory_values.reduce((a: number, b: number) => a + b, 0) / data.memory_values.length,
                disk_percent: data.disk_values.reduce((a: number, b: number) => a + b, 0) / data.disk_values.length
            }))
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    };

    return {
        loading,
        error,
        getServerHistory,
        getAggregateMetrics,
        aggregateHistoricalData
    };
};
