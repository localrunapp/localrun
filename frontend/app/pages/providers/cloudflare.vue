<template>
    <Page>
        <template #header>
            <PageHeader icon="devicon-plain:cloudflare" title="Cloudflare" iconClass="!size-10 pt-0 !mt-2"
                subtitle="Manage your Cloudflare integration, DNS, and Tunnels." backPath="/providers" />
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
                    class="bg-white border border-slate-200 shadow-sm rounded-xl p-4 md:p-5 dark:bg-slate-900 dark:border-slate-700">
                    <div class="mb-4">
                        <h3 class="text-lg font-bold text-slate-800 dark:text-white">Authentication</h3>
                        <p class="text-sm text-slate-500 dark:text-slate-400">Configure your Cloudflare API Token.</p>
                    </div>

                    <div class="bg-blue-50 border border-blue-200 text-sm text-blue-600 rounded-lg p-4 mb-4 dark:bg-blue-800/10 dark:border-blue-900 dark:text-blue-500"
                        role="alert">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <Icon name="tabler:info-circle" class="h-4 w-4 mt-0.5" />
                            </div>
                            <div class="ms-4">
                                <h3 class="text-sm font-semibold">
                                    Required Permissions
                                </h3>
                                <div class="mt-1 text-sm text-blue-700 dark:text-blue-400">
                                    Your API Token needs the following permissions:
                                    <ul class="list-disc list-inside mt-1">
                                        <li>Zone: Read</li>
                                        <li>DNS: Edit</li>
                                        <li>Cloudflare Tunnel: Read</li>
                                        <li>Cloudflare Tunnel: Edit</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    <form @submit.prevent="saveToken">
                        <div class="space-y-4">
                            <div>
                                <label for="cf-token" class="block text-sm font-medium mb-2 dark:text-white">Cloudflare
                                    API
                                    Token</label>
                                <div class="relative">
                                    <input type="text" id="cf-token" v-model="form.credentials.token"
                                        class="py-3 px-4 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-slate-700 dark:text-slate-400 dark:focus:ring-slate-600"
                                        placeholder="Enter your token">
                                </div>
                                <p class="mt-2 text-xs text-slate-500">
                                    You can create a token in the <a
                                        href="https://dash.cloudflare.com/profile/api-tokens" target="_blank"
                                        class="text-blue-600 hover:underline">Cloudflare Dashboard</a>.
                                </p>
                            </div>
                        </div>

                        <div class="mt-6 flex justify-between items-center">
                            <div v-if="testResult"
                                :class="['text-sm font-medium', testResult.success ? 'text-teal-500' : 'text-red-500']">
                                {{ testResult.message }}
                            </div>
                            <div v-else></div>

                            <div class="flex gap-x-2">
                                <button type="button" @click="testToken" :disabled="!form.credentials.token || testing"
                                    class="py-2 px-3 inline-flex justify-center items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-slate-100 text-slate-800 hover:bg-slate-200 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700">
                                    <span v-if="testing"
                                        class="animate-spin inline-block w-4 h-4 border-[2px] border-current border-t-transparent rounded-full"
                                        role="status" aria-label="loading"></span>
                                    Test Token
                                </button>
                                <button type="submit" :disabled="!isTokenValid"
                                    class="py-2 px-3 inline-flex justify-center items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                                    Save Credentials
                                </button>
                            </div>
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
                        <!-- DNS Toggle -->
                        <div class="flex items-center justify-between"
                            :class="{ 'opacity-50 pointer-events-none': !hasSavedCredentials }">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 dark:text-white">DNS
                                    Management</label>
                                <p class="text-xs text-slate-500 dark:text-slate-400">Allow LocalRun to manage DNS
                                    records.</p>
                            </div>
                            <div class="relative inline-block">
                                <input type="checkbox" id="dns-toggle" v-model="form.dns"
                                    :disabled="!hasSavedCredentials"
                                    class="peer relative w-11 h-6 p-px bg-gray-200 border-transparent text-transparent rounded-full cursor-pointer  ease-in-out duration-200 focus:ring-blue-600 disabled:opacity-50 disabled:pointer-events-none checked:bg-blue-600 checked:bg-none checked:text-white checked:border-blue-600 focus:checked:border-blue-600 dark:bg-slate-700 dark:border-slate-600 dark:checked:bg-blue-500 dark:checked:border-blue-500 dark:focus:ring-offset-gray-600 before:inline-block before:w-5 before:h-5 before:bg-white checked:before:bg-white before:translate-x-0 checked:before:translate-x-full before:shadow before:rounded-full before:transform before:ring-0 before:transition before:ease-in-out before:duration-200">
                                <label for="dns-toggle" class="sr-only">switch</label>
                            </div>
                        </div>

                        <!-- Tunnel Toggle -->
                        <div class="flex items-center justify-between"
                            :class="{ 'opacity-50 pointer-events-none': !hasSavedCredentials }">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 dark:text-white">Tunnels</label>
                                <p class="text-xs text-slate-500 dark:text-slate-400">Enable Cloudflare Tunnels for
                                    exposing
                                    services.</p>
                            </div>
                            <div class="relative inline-block">
                                <input type="checkbox" id="tunnel-toggle" v-model="form.http"
                                    :disabled="!hasSavedCredentials"
                                    class="peer relative w-11 h-6 p-px bg-gray-200 border-transparent text-transparent rounded-full cursor-pointer  ease-in-out duration-200 focus:ring-blue-600 disabled:opacity-50 disabled:pointer-events-none checked:bg-blue-600 checked:bg-none checked:text-white checked:border-blue-600 focus:checked:border-blue-600 dark:bg-slate-700 dark:border-slate-600 dark:checked:bg-blue-500 dark:checked:border-blue-500 dark:focus:ring-offset-gray-600 before:inline-block before:w-5 before:h-5 before:bg-white checked:before:bg-white before:translate-x-0 checked:before:translate-x-full before:shadow before:rounded-full before:transform before:ring-0 before:transition before:ease-in-out before:duration-200">
                                <label for="tunnel-toggle" class="sr-only">switch</label>
                            </div>
                        </div>

                        <!-- Anonymous Tunnels Toggle -->
                        <div class="flex items-center justify-between">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 dark:text-white">Anonymous
                                    Tunnels</label>
                                <p class="text-xs text-slate-500 dark:text-slate-400">Allow creating tunnels without
                                    authentication.</p>
                            </div>
                            <div class="relative inline-block">
                                <input type="checkbox" id="anonymous-toggle" v-model="form.anonymous_tunnels"
                                    class="peer relative w-11 h-6 p-px bg-gray-200 border-transparent text-transparent rounded-full cursor-pointer  ease-in-out duration-200 focus:ring-blue-600 disabled:opacity-50 disabled:pointer-events-none checked:bg-blue-600 checked:bg-none checked:text-white checked:border-blue-600 focus:checked:border-blue-600 dark:bg-slate-700 dark:border-slate-600 dark:checked:bg-blue-500 dark:checked:border-blue-500 dark:focus:ring-offset-gray-600 before:inline-block before:w-5 before:h-5 before:bg-white checked:before:bg-white before:translate-x-0 checked:before:translate-x-full before:shadow before:rounded-full before:transform before:ring-0 before:transition before:ease-in-out before:duration-200">
                                <label for="anonymous-toggle" class="sr-only">switch</label>
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
import { useCloudflare } from '@/composables/useCloudflare';
import { useToast } from '@/composables/useToast';

const { getConfig, saveConfig, testToken: apiTestToken } = useCloudflare();
const toast = useToast();

const loading = ref(true);
const testing = ref(false);
const testResult = ref<any>(null);
const hasSavedCredentials = ref(false);

const form = reactive({
    credentials: {
        token: ''
    },
    dns: false,
    http: false,
    anonymous_tunnels: true
});

const isTokenValid = computed(() => {
    return form.credentials.token && form.credentials.token.length > 0;
});

const fetchProvider = async () => {
    loading.value = true;
    try {
        const provider = await getConfig();
        if (provider) {
            form.dns = provider.dns;
            form.http = provider.http;
            // Check if credentials exist (backend returns masked or empty)
            if (provider.credentials && provider.credentials.token) {
                hasSavedCredentials.value = true;
                // We don't pre-fill the token input for security reasons, 
                // or we could show a placeholder if needed.
                form.credentials.token = provider.credentials.token; // Masked
            }

            // Load anonymous tunnels config (default true)
            if (provider.configs && provider.configs.anonymous_tunnels !== undefined) {
                form.anonymous_tunnels = provider.configs.anonymous_tunnels;
            } else {
                form.anonymous_tunnels = true;
            }
        }
    } catch (error) {
        console.error('Error fetching provider:', error);
    } finally {
        loading.value = false;
    }
};

const testToken = async () => {
    testing.value = true;
    testResult.value = null;
    try {
        const result = await apiTestToken(form.credentials.token);
        testResult.value = result;
    } catch (error: any) {
        testResult.value = { success: false, message: error.message || 'Test failed' };
    } finally {
        testing.value = false;
    }
};

const saveToken = async () => {
    try {
        const payload = { credentials: { token: form.credentials.token } };
        await saveConfig(payload);
        hasSavedCredentials.value = true;
        testResult.value = { success: true, message: 'Credentials saved successfully' };
        toast.alert.success('Credentials saved successfully');
        // Refresh to get updated state
        fetchProvider();
    } catch (error: any) {
        console.error('Error saving config:', error);
        testResult.value = { success: false, message: 'Failed to save credentials' };
        toast.alert.error('Failed to save credentials');
    }
};

const saveCapabilities = async () => {
    try {
        const payload = {
            dns: form.dns,
            http: form.http,
            anonymous_tunnels: form.anonymous_tunnels
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
