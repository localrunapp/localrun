<template>
    <Page>
        <template #header>
            <PageHeader icon="logos:ngrok" title="Ngrok" subtitle="Manage your Ngrok integration and Tunnels."
                backPath="/providers" />
        </template>

        <div class="mx-auto">
            <div v-if="loading" class="flex justify-center items-center h-64">
                <div class="animate-spin inline-block w-6 h-6 border-[3px] border-current border-t-transparent text-blue-600 rounded-full dark:text-blue-500"
                    role="status" aria-label="loading">
                    <span class="sr-only">Loading...</span>
                </div>
            </div>

            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Credentials Card -->
                <div
                    class="bg-white border border-slate-200 shadow-sm rounded-xl p-4 md:p-5 dark:bg-slate-900 dark:border-slate-700 h-fit">
                    <div class="mb-4">
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white">Authentication</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Configure your Ngrok Authtoken.</p>
                    </div>

                    <form @submit.prevent="saveToken">
                        <div class="space-y-4">
                            <div>
                                <label for="ngrok-token" class="block text-sm font-medium mb-2 dark:text-white">Ngrok
                                    Authtoken</label>
                                <div class="relative">
                                    <input type="text" id="ngrok-token" v-model="form.credentials.authtoken"
                                        class="py-3 px-4 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-slate-700 dark:text-slate-400 dark:focus:ring-slate-600"
                                        placeholder="Enter your authtoken">
                                </div>
                                <p class="mt-2 text-xs text-slate-500">
                                    You can find your authtoken in the <a
                                        href="https://dashboard.ngrok.com/get-started/your-authtoken" target="_blank"
                                        class="text-blue-600 hover:underline">Ngrok Dashboard</a>.
                                </p>
                            </div>
                        </div>

                        <div class="mt-6 flex justify-end">
                            <button type="submit" :disabled="!isTokenValid"
                                class="py-2 px-3 inline-flex justify-center items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                                Save Credentials
                            </button>
                        </div>
                    </form>
                </div>

                <!-- Capabilities Card -->
                <div
                    class="bg-white border border-slate-200 shadow-sm rounded-xl p-4 md:p-5 dark:bg-slate-900 dark:border-slate-700 h-fit">
                    <div class="mb-4">
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white">Capabilities</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Enable or disable specific features.</p>
                    </div>

                    <div class="space-y-4">
                        <!-- HTTP Tunnel Toggle -->
                        <div class="flex items-center justify-between"
                            :class="{ 'opacity-50 pointer-events-none': !hasSavedCredentials }">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 dark:text-white">HTTP
                                    Tunnels</label>
                                <p class="text-xs text-slate-500 dark:text-slate-400">Enable HTTP/HTTPS tunnels.</p>
                            </div>
                            <div class="relative inline-block">
                                <input type="checkbox" id="http-toggle" v-model="form.http"
                                    :disabled="!hasSavedCredentials"
                                    class="peer relative w-11 h-6 p-px bg-gray-200 border-transparent text-transparent rounded-full cursor-pointer  ease-in-out duration-200 focus:ring-blue-600 disabled:opacity-50 disabled:pointer-events-none checked:bg-blue-600 checked:bg-none checked:text-white checked:border-blue-600 focus:checked:border-blue-600 dark:bg-slate-700 dark:border-slate-600 dark:checked:bg-blue-500 dark:checked:border-blue-500 dark:focus:ring-offset-gray-600 before:inline-block before:w-5 before:h-5 before:bg-white checked:before:bg-white before:translate-x-0 checked:before:translate-x-full before:shadow before:rounded-full before:transform before:ring-0 before:transition before:ease-in-out before:duration-200">
                                <label for="http-toggle" class="sr-only">switch</label>
                            </div>
                        </div>

                        <!-- TCP Tunnel Toggle -->
                        <div class="flex items-center justify-between"
                            :class="{ 'opacity-50 pointer-events-none': !hasSavedCredentials }">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 dark:text-white">TCP
                                    Tunnels</label>
                                <p class="text-xs text-slate-500 dark:text-slate-400">Enable TCP tunnels.</p>
                            </div>
                            <div class="relative inline-block">
                                <input type="checkbox" id="tcp-toggle" v-model="form.tcp"
                                    :disabled="!hasSavedCredentials"
                                    class="peer relative w-11 h-6 p-px bg-gray-200 border-transparent text-transparent rounded-full cursor-pointer  ease-in-out duration-200 focus:ring-blue-600 disabled:opacity-50 disabled:pointer-events-none checked:bg-blue-600 checked:bg-none checked:text-white checked:border-blue-600 focus:checked:border-blue-600 dark:bg-slate-700 dark:border-slate-600 dark:checked:bg-blue-500 dark:checked:border-blue-500 dark:focus:ring-offset-gray-600 before:inline-block before:w-5 before:h-5 before:bg-white checked:before:bg-white before:translate-x-0 checked:before:translate-x-full before:shadow before:rounded-full before:transform before:ring-0 before:transition before:ease-in-out before:duration-200">
                                <label for="tcp-toggle" class="sr-only">switch</label>
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
import { ref, onMounted, reactive, computed } from 'vue';
import { useNgrok } from '@/composables/useNgrok';
import { useToast } from '@/composables/useToast';

const { getConfig, saveConfig } = useNgrok();
const toast = useToast();

const loading = ref(true);
const hasSavedCredentials = ref(false);

const form = reactive({
    credentials: {
        authtoken: ''
    },
    http: false,
    tcp: false
});

const isTokenValid = computed(() => {
    return form.credentials.authtoken && form.credentials.authtoken.length > 0;
});

const fetchProvider = async () => {
    loading.value = true;
    try {
        const provider = await getConfig();
        if (provider) {
            form.http = provider.http;
            form.tcp = provider.tcp;

            if (provider.credentials && provider.credentials.authtoken) {
                hasSavedCredentials.value = true;
                form.credentials.authtoken = provider.credentials.authtoken; // Masked
            }
        }
    } catch (error) {
        console.error('Error fetching provider:', error);
    } finally {
        loading.value = false;
    }
};

const saveToken = async () => {
    try {
        const payload = { credentials: { authtoken: form.credentials.authtoken } };
        await saveConfig(payload);
        hasSavedCredentials.value = true;
        toast.alert.success('Credentials saved successfully');
        fetchProvider();
    } catch (error: any) {
        console.error('Error saving config:', error);
        toast.alert.error('Failed to save credentials');
    }
};

const saveCapabilities = async () => {
    try {
        const payload = {
            http: form.http,
            tcp: form.tcp
        };
        await saveConfig(payload);
        toast.alert.success('Capabilities updated successfully');
    } catch (error) {
        console.error('Error updating capabilities:', error);
        toast.alert.error('Failed to update capabilities');
    }
};

onMounted(() => {
    fetchProvider();
});
</script>
