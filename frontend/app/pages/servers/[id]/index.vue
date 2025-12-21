<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from '@/composables/useToast';

import { useServers } from '@/composables/useServers';

const route = useRoute();
const toast = useToast();
const serverId = route.params.id;

const { getServer, scanServer: apiScanServer, getAgentStatus } = useServers();

const server = ref(null);
const loading = ref(true);
const scanning = ref(false);
const agentStatus = ref({ connected: false });

const fetchServer = async () => {
    loading.value = true;
    try {
        const [serverData, statusData] = await Promise.all([
            getServer(serverId),
            getAgentStatus()
        ]);
        server.value = serverData;
        agentStatus.value = statusData;
    } catch (e) {
        toast.error('Failed to load server details');
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const scanServer = async () => {
    if (!agentStatus.value.connected) {
        toast.error('CLI Agent is not connected. Cannot perform scan.');
        return;
    }
    
    scanning.value = true;
    try {
        const data = await apiScanServer(serverId);
        
        // Update server data with new scan results
        if (server.value) {
            server.value.services = data;
        }
        toast.success('Scan completed successfully');
        
        // Refresh full server data to get updated status/OS
        await fetchServer();
    } catch (e) {
        toast.error('Scan failed');
        console.error(e);
    } finally {
        scanning.value = false;
    }
};

onMounted(fetchServer);
</script>

<template>
    <Page>
        <template #header>
            <PageHeader icon="lucide:server" :title="server?.name || 'Server Details'" :subtitle="server?.host || 'Loading...'" backPath="/servers">
                <template #actions>
                    <div class="flex items-center gap-3">
                        <!-- Agent Status Indicator -->
                        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                            <div class="relative flex h-2.5 w-2.5">
                                <span v-if="agentStatus.connected" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span class="relative inline-flex rounded-full h-2.5 w-2.5" :class="agentStatus.connected ? 'bg-green-500' : 'bg-gray-400'"></span>
                            </div>
                            <span class="text-xs font-medium text-gray-600 dark:text-gray-300">
                                {{ agentStatus.connected ? 'Agent Connected' : 'Agent Disconnected' }}
                            </span>
                        </div>

                        <button @click="scanServer" :disabled="scanning || !agentStatus.connected" 
                            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium  flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            :title="!agentStatus.connected ? 'CLI Agent required for scanning' : ''">
                            <Icon name="lucide:radar" class="w-4 h-4" :class="{ 'animate-spin': scanning }" />
                            {{ scanning ? 'Scanning...' : 'Scan Ports' }}
                        </button>
                    </div>
                </template>
            </PageHeader>
        </template>

        <div v-if="loading" class="flex justify-center py-10">
            <Icon name="lucide:loader-2" class="w-8 h-8 text-blue-500 animate-spin" />
        </div>

        <div v-else-if="server" class="space-y-6">
            <!-- Server Info Card -->
            <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-sm">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Icon name="lucide:info" class="w-5 h-5 text-gray-500" />
                    System Information
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Host / IP</p>
                        <p class="font-mono text-gray-900 dark:text-gray-200">{{ server.host }}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Operating System</p>
                        <div class="flex items-center gap-2">
                            <Icon :name="server.os_type?.toLowerCase().includes('windows') ? 'lucide:monitor' : (server.os_type?.toLowerCase().includes('linux') ? 'lucide:terminal' : 'lucide:laptop')" class="w-4 h-4 text-gray-400" />
                            <p class="text-gray-900 dark:text-gray-200">{{ server.os_type || 'Unknown' }}</p>
                        </div>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Status</p>
                        <span v-if="server.is_reachable" class="inline-flex items-center gap-1.5 py-0.5 px-2 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                            <span class="w-1.5 h-1.5 inline-block bg-green-400 rounded-full"></span>
                            Reachable
                        </span>
                        <span v-else class="inline-flex items-center gap-1.5 py-0.5 px-2 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                            <span class="w-1.5 h-1.5 inline-block bg-red-400 rounded-full"></span>
                            Unreachable
                        </span>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Last Check</p>
                        <p class="text-gray-900 dark:text-gray-200">{{ server.last_check ? new Date(server.last_check).toLocaleString() : 'Never' }}</p>
                    </div>
                    <div class="md:col-span-2" v-if="server.description">
                        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Description</p>
                        <p class="text-gray-900 dark:text-gray-200">{{ server.description }}</p>
                    </div>
                </div>
            </div>

            <!-- Detected Services -->
            <div class="bg-white dark:bg-slate-900 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden shadow-sm">
                <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                        <Icon name="lucide:network" class="w-5 h-5 text-gray-500" />
                        Detected Services
                        <span class="text-xs font-normal text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded-full">
                            {{ server.services?.length || 0 }} ports open
                        </span>
                    </h3>
                </div>

                <div v-if="!server.services || server.services.length === 0" class="text-center py-12 text-gray-500 dark:text-gray-400">
                    <Icon name="lucide:search-x" class="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p class="text-lg font-medium">No services detected yet</p>
                    <p class="text-sm mt-1">Click "Scan Ports" to analyze this server.</p>
                </div>

                <div v-else class="overflow-x-auto">
                    <table class="w-full text-left text-sm">
                        <thead class="bg-gray-50 dark:bg-gray-800/50 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-200 dark:border-gray-700">
                            <tr>
                                <th class="px-6 py-3 w-24">Port</th>
                                <th class="px-6 py-3 w-32">Service</th>
                                <th class="px-6 py-3">Version / Banner</th>
                                <th class="px-6 py-3">Process</th>
                                <th class="px-6 py-3">Docker</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                            <tr v-for="service in server.services" :key="service.port" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 ">
                                <td class="px-6 py-4 font-mono text-blue-600 dark:text-blue-400 font-semibold">
                                    {{ service.port }}
                                </td>
                                <td class="px-6 py-4">
                                    <div class="flex items-center gap-2">
                                        <span class="font-medium text-gray-900 dark:text-white">{{ service.service_name }}</span>
                                        <span class="text-xs font-mono bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-gray-500 uppercase">
                                            {{ service.protocol }}
                                        </span>
                                    </div>
                                </td>
                                <td class="px-6 py-4">
                                    <div v-if="service.version" class="text-gray-900 dark:text-gray-200 font-medium">
                                        {{ service.version }}
                                    </div>
                                    <div v-if="service.banner" class="text-xs text-gray-500 dark:text-gray-400 font-mono mt-0.5 truncate max-w-xs" :title="service.banner">
                                        {{ service.banner }}
                                    </div>
                                    <div v-if="!service.version && !service.banner" class="text-gray-400 italic">
                                        Unknown
                                    </div>
                                </td>
                                <td class="px-6 py-4">
                                    <div v-if="service.process" class="flex items-center gap-2">
                                        <Icon name="lucide:cpu" class="w-4 h-4 text-yellow-500" />
                                        <span class="text-gray-700 dark:text-gray-300">{{ service.process.name }}</span>
                                        <span class="text-xs text-gray-400">({{ service.process.pid }})</span>
                                    </div>
                                    <div v-else class="text-gray-400 text-xs">-</div>
                                </td>
                                <td class="px-6 py-4">
                                    <div v-if="service.docker" class="flex flex-col">
                                        <div class="flex items-center gap-2 text-gray-900 dark:text-white font-medium">
                                            <Icon name="lucide:container" class="w-4 h-4 text-blue-500" />
                                            {{ service.docker.image }}
                                        </div>
                                        <span class="text-xs text-gray-500 ml-6">{{ service.docker.name }}</span>
                                    </div>
                                    <div v-else class="text-gray-400 text-xs">-</div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </Page>
</template>
