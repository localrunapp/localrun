<template>
    <Page>
        <template #header>
            <PageHeader :title="service?.name || 'Service Details'" :subtitle="service?.full_domain || 'Loading...'"
                backPath="/services">
                <template #actions>
                    <div class="flex items-center gap-2">
                        <span v-if="service" :class="{
                            'bg-green-100 text-green-800 dark:bg-green-800/30 dark:text-green-500': service.status === 'running',
                            'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400': service.status !== 'running'
                        }" class="inline-flex items-center gap-1.5 py-1.5 px-3 rounded-md text-sm font-medium">
                            <span :class="service.status === 'running' ? 'bg-green-400' : 'bg-gray-400'"
                                class="w-1.5 h-1.5 rounded-full"></span>
                            {{ service.status }}
                        </span>

                        <div class="h-6 w-px bg-gray-300 dark:bg-gray-600 mx-2"></div>

                        <button v-if="service?.status !== 'running'" @click="startService"
                            class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700 ">
                            <icons.IconPlayerPlay class="w-4 h-4" />
                            Start
                        </button>
                        <button v-else @click="stopService"
                            class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700 ">
                            <icons.IconPlayerStop class="w-4 h-4" />
                            Stop
                        </button>
                        <button @click="toggleRestart"
                            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 ">
                            <icons.IconRefresh class="w-5 h-5" />
                        </button>
                    </div>
                </template>
            </PageHeader>
        </template>

        <div v-if="loading" class="flex items-center justify-center min-h-[400px]">
            <icons.IconLoader2 class="w-8 h-8 animate-spin text-blue-600" />
        </div>

        <div v-else-if="service" class="max-w-[85rem] px-4 py-6 sm:px-6 lg:px-8 mx-auto">
            <!-- Stats Cards -->
            <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div class="bg-white border border-gray-200 rounded-xl p-4 dark:bg-slate-900 dark:border-gray-700">
                    <div class="flex items-center gap-x-2">
                        <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Total Requests</p>
                    </div>
                    <div class="mt-1 flex items-center gap-x-2">
                        <h3 class="text-xl sm:text-2xl font-medium text-gray-800 dark:text-gray-200">
                            {{ analytics.total_requests || 0 }}
                        </h3>
                    </div>
                </div>
                <div class="bg-white border border-gray-200 rounded-xl p-4 dark:bg-slate-900 dark:border-gray-700">
                    <div class="flex items-center gap-x-2">
                        <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Avg Response Time</p>
                    </div>
                    <div class="mt-1 flex items-center gap-x-2">
                        <h3 class="text-xl sm:text-2xl font-medium text-gray-800 dark:text-gray-200">
                            {{ analytics.avg_response_time_ms || 0 }}ms
                        </h3>
                    </div>
                </div>
                <div class="bg-white border border-gray-200 rounded-xl p-4 dark:bg-slate-900 dark:border-gray-700">
                    <div class="flex items-center gap-x-2">
                        <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Bandwidth</p>
                    </div>
                    <div class="mt-1 flex items-center gap-x-2">
                        <h3 class="text-xl sm:text-2xl font-medium text-gray-800 dark:text-gray-200">
                            {{ formatBytes(analytics.total_bandwidth_bytes || 0) }}
                        </h3>
                    </div>
                </div>
                <div class="bg-white border border-gray-200 rounded-xl p-4 dark:bg-slate-900 dark:border-gray-700">
                    <div class="flex items-center gap-x-2">
                        <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Error Rate</p>
                    </div>
                    <div class="mt-1 flex items-center gap-x-2">
                        <h3 class="text-xl sm:text-2xl font-medium text-gray-800 dark:text-gray-200">
                            {{ errorRate }}%
                        </h3>
                    </div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
                <nav class="-mb-px flex space-x-8" aria-label="Tabs">
                    <button v-for="tab in tabs" :key="tab.id" @click="currentTab = tab.id" :class="[
                        currentTab === tab.id
                            ? 'border-blue-500 text-blue-600 dark:text-blue-500'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300',
                        'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
                    ]">
                        <component :is="tab.icon" class="size-4" />
                        {{ tab.name }}
                    </button>
                </nav>
            </div>

            <!-- Analytics Tab -->
            <div v-if="currentTab === 'analytics'" class="space-y-6">
                <!-- Visits Map Placeholder -->
                <div class="bg-white border border-gray-200 rounded-xl p-6 dark:bg-slate-900 dark:border-gray-700">
                    <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">Visits Map</h3>
                    <div class="h-[400px] flex items-center justify-center bg-gray-50 dark:bg-slate-800 rounded-lg">
                        <p class="text-gray-500 dark:text-gray-400">Map Visualization Coming Soon</p>
                    </div>
                </div>

                <!-- Top Paths & Status Codes -->
                <div class="grid lg:grid-cols-2 gap-6">
                    <div class="bg-white border border-gray-200 rounded-xl p-6 dark:bg-slate-900 dark:border-gray-700">
                        <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">Top Paths</h3>
                        <div class="space-y-2">
                            <div v-for="(count, path) in analytics.top_paths" :key="path"
                                class="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-slate-800 rounded">
                                <span class="text-sm font-mono text-gray-600 dark:text-gray-300 truncate max-w-[80%]">{{ path
                                    }}</span>
                                <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ count }}</span>
                            </div>
                        </div>
                    </div>
                    <div class="bg-white border border-gray-200 rounded-xl p-6 dark:bg-slate-900 dark:border-gray-700">
                        <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">Status Codes</h3>
                        <div class="space-y-2">
                            <div v-for="(count, code) in analytics.status_codes" :key="code"
                                class="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-slate-800 rounded">
                                <span class="inline-flex items-center gap-1.5 py-1 px-2 rounded-md text-xs font-medium" :class="{
                                    'bg-green-100 text-green-800': code.startsWith('2'),
                                    'bg-blue-100 text-blue-800': code.startsWith('3'),
                                    'bg-yellow-100 text-yellow-800': code.startsWith('4'),
                                    'bg-red-100 text-red-800': code.startsWith('5')
                                }">
                                    {{ code }}
                                </span>
                                <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ count }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Settings Tab -->
            <div v-else-if="currentTab === 'settings'" class="max-w-2xl space-y-6">
                <div class="bg-white border border-gray-200 rounded-xl p-6 dark:bg-slate-900 dark:border-gray-700">
                    <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">Security</h3>
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Tunnel Password</label>
                                <p class="text-xs text-gray-500 dark:text-gray-400">Protect your tunnel with a password</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <input v-model="settings.tunnel_password" type="password" placeholder="No password set"
                                    class="py-2 px-3 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-800 dark:border-gray-700 dark:text-gray-400">
                                <button @click="savePassword"
                                    class="py-2 px-3 inline-flex items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none">
                                    Save
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

             <!-- Logs Tab -->
             <div v-else-if="currentTab === 'logs'" class="space-y-6">
                <!-- Live Logs -->
                <div class="bg-slate-900 rounded-xl p-4 font-mono text-xs text-white h-[500px] overflow-y-auto">
                    <div v-for="(log, i) in logs" :key="i" class="mb-1">
                        <span class="text-gray-500">[{{ log.timestamp }}]</span>
                        <span :class="{
                            'text-green-400': log.level === 'info',
                            'text-yellow-400': log.level === 'warn',
                            'text-red-400': log.level === 'error'
                        }"> {{ log.message }}</span>
                    </div>
                     <div v-if="logs.length === 0" class="text-gray-500 italic">No logs available</div>
                </div>
            </div>

             <!-- Debug/Container Tab -->
             <div v-else-if="currentTab === 'container'" class="space-y-6">
                <!-- Container Stats -->
                <div class="bg-white border border-gray-200 rounded-xl p-6 dark:bg-slate-900 dark:border-gray-700">
                    <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">Container Statistics</h3>
                     <div class="grid sm:grid-cols-2 gap-6">
                        <div>
                             <h4 class="text-sm font-medium text-gray-500 uppercase">CPU Usage</h4>
                             <div class="mt-2 text-2xl font-semibold text-gray-800 dark:text-gray-200">
                                {{ containerStats.cpu_percent || 0 }}%
                             </div>
                        </div>
                         <div>
                             <h4 class="text-sm font-medium text-gray-500 uppercase">Memory Usage</h4>
                             <div class="mt-2 text-2xl font-semibold text-gray-800 dark:text-gray-200">
                                {{ containerStats.memory_percent || 0 }}%
                             </div>
                              <p class="text-xs text-gray-500">{{ formatBytes(containerStats.memory_usage_bytes || 0) }}</p>
                        </div>
                     </div>
                </div>
            </div>

        </div>
    </Page>
</template>

<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRoute } from "vue-router";
import * as icons from "@tabler/icons-vue";

const route = useRoute();
const api = useApi();
const toast = useToast();

const service = ref(null);
const loading = ref(true);
const currentTab = ref('analytics');
const analytics = ref({});
const logs = ref([]);
const containerStats = ref({});
const settings = ref({ tunnel_password: '' });

const tabs = [
    { id: 'analytics', name: 'Analytics', icon: icons.IconChartBar },
    { id: 'settings', name: 'Settings', icon: icons.IconSettings },
    { id: 'logs', name: 'Logs', icon: icons.IconTerminal2 },
    { id: 'container', name: 'Container', icon: icons.IconBox },
];

const errorRate = computed(() => {
    if (!analytics.value.total_requests) return 0;
    const errors = Object.entries(analytics.value.status_codes || {})
        .filter(([code]) => code.startsWith('4') || code.startsWith('5'))
        .reduce((acc, [, count]) => acc + count, 0);
    return Math.round((errors / analytics.value.total_requests) * 100);
});

const loadService = async () => {
    loading.value = true;
    try {
        service.value = await api.get(`/services/${route.params.id}`);
        // Check if ID is int but accessible via UUID-like string if backend supported it, 
        // but here we rely on standard API.
        
        settings.value.tunnel_password = service.value.tunnel_password || '';
        await loadAnalytics();
    } catch (e) {
        toast.error('Error loading service');
    } finally {
        loading.value = false;
    }
};

const loadAnalytics = async () => {
    if (!service.value) return;
    try {
        // Mock analytics for now until backend endpoint linked
        // In real impl: analytics.value = await api.get(`/services/${service.value.id}/analytics`);
        analytics.value = {
            total_requests: 1250,
            avg_response_time_ms: 45,
            total_bandwidth_bytes: 52428800, // 50MB
            top_paths: { '/': 500, '/api/users': 200, '/login': 150 },
            status_codes: { '200': 1100, '404': 100, '500': 50 }
        };
    } catch (e) {
        console.error(e);
    }
};

const loadLogs = async () => {
     // Mock logs
     logs.value = [
         { timestamp: new Date().toISOString(), level: 'info', message: 'Tunnel started' },
         { timestamp: new Date().toISOString(), level: 'info', message: 'Incoming request GET /' },
     ];
};

const loadContainerStats = async () => {
    // Mock container stats
    containerStats.value = {
        cpu_percent: 1.5,
        memory_percent: 12.4,
        memory_usage_bytes: 256000000
    };
};

const startService = async () => {
    // Implement start logic
    toast.success('Service started');
};

const stopService = async () => {
    // Implement stop logic
    toast.success('Service stopped');
};

const toggleRestart = async () => {
    // Implement restart
    toast.success('Service restarted');
};

const savePassword = async () => {
    try {
        await api.put(`/services/${service.value.id}`, {
            tunnel_password: settings.value.tunnel_password
        });
        toast.success('Password updated');
    } catch (e) {
        toast.error('Failed to update password');
    }
};

const formatBytes = (bytes, decimals = 2) => {
    if (!+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

watch(currentTab, (newTab) => {
    if (newTab === 'logs') loadLogs();
    if (newTab === 'container') loadContainerStats();
});

onMounted(() => {
    loadService();
});
</script>
