<template>
    <Page>
        <template #header>
            <PageHeader icon="tabler:terminal-2" title="Localhost.run"
                subtitle="Manage your Localhost.run integration." />
        </template>

        <div class="mx-auto">
            <div v-if="loading" class="flex justify-center items-center h-64">
                <div class="animate-spin inline-block w-6 h-6 border-[3px] border-current border-t-transparent text-blue-600 rounded-full dark:text-blue-500"
                    role="status" aria-label="loading">
                    <span class="sr-only">Loading...</span>
                </div>
            </div>

            <div v-else class="max-w-2xl mx-auto space-y-6">
                <!-- Info Card -->
                <div
                    class="bg-white border border-slate-200 shadow-sm rounded-xl p-4 md:p-5 dark:bg-slate-900 dark:border-slate-700">
                    <div class="mb-4">
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white">Configuration</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Localhost.run is client-less and requires
                            no
                            credentials.</p>
                    </div>
                    <p class="text-slate-600 dark:text-slate-400">
                        This provider uses SSH to create tunnels. It works out of the box without any API keys or
                        tokens.
                    </p>
                </div>

                <!-- Capabilities Card -->
                <div
                    class="bg-white border border-slate-200 shadow-sm rounded-xl p-4 md:p-5 dark:bg-slate-900 dark:border-slate-700">
                    <div class="mb-4">
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white">Capabilities</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Enable or disable specific features.</p>
                    </div>

                    <div class="space-y-4">
                        <!-- Tunnel Toggle -->
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 dark:text-white">Tunnels</label>
                                <p class="text-xs text-slate-500 dark:text-slate-400">Enable Localhost.run Tunnels.</p>
                            </div>
                            <div class="relative inline-block">
                                <input type="checkbox" id="tunnel-toggle" v-model="form.http"
                                    class="peer relative w-11 h-6 p-px bg-gray-100 border-transparent text-transparent rounded-full cursor-pointer  ease-in-out duration-200 focus:ring-blue-600 disabled:opacity-50 disabled:pointer-events-none checked:bg-none checked:text-blue-600 checked:border-blue-600 focus:checked:border-blue-600 dark:bg-slate-800 dark:border-slate-700 dark:checked:bg-blue-500 dark:checked:border-blue-500 dark:focus:ring-offset-gray-600 before:inline-block before:w-5 before:h-5 before:bg-white checked:before:bg-blue-200 before:translate-x-0 checked:before:translate-x-full before:shadow before:rounded-full before:transform before:ring-0 before:transition before:ease-in-out before:duration-200 dark:before:bg-slate-400 dark:checked:before:bg-blue-200">
                                <label for="tunnel-toggle" class="sr-only">switch</label>
                            </div>
                        </div>
                    </div>

                    <div class="mt-6 flex justify-end">
                        <button @click="saveCapabilities"
                            class="py-2 px-3 inline-flex justify-center items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-slate-100 text-slate-800 hover:bg-slate-200 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700">
                            Update Capabilities
                        </button>
                    </div>
                </div>

            </div>
        </div>
    </Page>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useAuthStore } from '@/stores/auth.js';

const config = useRuntimeConfig();
const authStore = useAuthStore();

const loading = ref(true);
const provider = ref<any>(null);

const form = reactive({
    http: false
});

const fetchProvider = async () => {
    loading.value = true;
    try {
        const response = await fetch('/api/providers/localhost.run', {
            headers: {
                'Authorization': `Bearer ${authStore.getToken()}`
            }
        });
        if (response.ok) {
            provider.value = await response.json();
            // Initialize form
            form.http = provider.value.http;
        } else {
            console.error('Failed to fetch provider');
        }
    } catch (error) {
        console.error('Error fetching provider:', error);
    } finally {
        loading.value = false;
    }
};

const saveCapabilities = async () => {
    try {
        const payload = {
            http: form.http
        };

        const response = await fetch('/api/providers/localhost.run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authStore.getToken()}`
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            fetchProvider();
        } else {
            console.error('Failed to update capabilities');
        }
    } catch (error) {
        console.error('Error updating capabilities:', error);
    }
};

onMounted(() => {
    fetchProvider();
});
</script>
