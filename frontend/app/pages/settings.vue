<template>
    <Page>
        <template #title>Settings</template>
        <template #subtitle>Manage your account and application preferences.</template>

        <div class="max-w-[85rem] px-4 py-10 sm:px-6 lg:px-8 lg:py-14 mx-auto">
            <!-- Authentication Section -->
            <div
                class="bg-white border border-slate-200 shadow-sm rounded-xl p-4 md:p-5 dark:bg-slate-900 dark:border-slate-700">
                <div class="mb-4">
                    <h3 class="text-lg font-bold text-gray-800 dark:text-white">
                        Linked Accounts
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        Link your external accounts to sign in with one click.
                    </p>
                </div>

                <div class="space-y-4">
                    <!-- GitHub -->
                    <div
                        class="flex items-center justify-between p-4 border border-gray-200 rounded-lg dark:border-gray-700">
                        <div class="flex items-center gap-3">
                            <div class="flex-shrink-0">
                                <svg class="w-6 h-6 text-gray-800 dark:text-white" fill="currentColor"
                                    viewBox="0 0 24 24">
                                    <path fill-rule="evenodd" clip-rule="evenodd"
                                        d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z" />
                                </svg>
                            </div>
                            <div>
                                <h4 class="font-medium text-gray-800 dark:text-white">GitHub</h4>
                                <p class="text-sm text-gray-500" v-if="user?.github_id">Linked</p>
                                <p class="text-sm text-gray-500" v-else>Not linked</p>
                            </div>
                        </div>
                        <button v-if="user?.github_id" @click="unlink('github')"
                            class="py-2 px-3 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-gray-200 bg-white text-red-500 shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-gray-700 dark:hover:bg-gray-800 dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                            Unlink
                        </button>
                        <button v-else @click="link('github')"
                            class="py-2 px-3 inline-flex items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                            Link
                        </button>
                    </div>

                    <!-- Google -->
                    <div
                        class="flex items-center justify-between p-4 border border-gray-200 rounded-lg dark:border-gray-700">
                        <div class="flex items-center gap-3">
                            <div class="flex-shrink-0">
                                <svg class="w-6 h-6" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path
                                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                        fill="#4285F4" />
                                    <path
                                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                        fill="#34A853" />
                                    <path
                                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                        fill="#FBBC05" />
                                    <path
                                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                        fill="#EA4335" />
                                </svg>
                            </div>
                            <div>
                                <h4 class="font-medium text-gray-800 dark:text-white">Google</h4>
                                <p class="text-sm text-gray-500" v-if="user?.google_id">Linked</p>
                                <p class="text-sm text-gray-500" v-else>Not linked</p>
                            </div>
                        </div>
                        <button v-if="user?.google_id" @click="unlink('google')"
                            class="py-2 px-3 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-gray-200 bg-white text-red-500 shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-gray-700 dark:hover:bg-gray-800 dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                            Unlink
                        </button>
                        <button v-else @click="link('google')"
                            class="py-2 px-3 inline-flex items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                            Link
                        </button>
                    </div>

                    <!-- Microsoft -->
                    <div
                        class="flex items-center justify-between p-4 border border-gray-200 rounded-lg dark:border-gray-700">
                        <div class="flex items-center gap-3">
                            <div class="flex-shrink-0">
                                <svg class="w-6 h-6" viewBox="0 0 23 23" xmlns="http://www.w3.org/2000/svg">
                                    <path fill="#f35325" d="M1 1h10v10H1z" />
                                    <path fill="#81bc06" d="M12 1h10v10H12z" />
                                    <path fill="#05a6f0" d="M1 12h10v10H1z" />
                                    <path fill="#ffba08" d="M12 12h10v10H12z" />
                                </svg>
                            </div>
                            <div>
                                <h4 class="font-medium text-gray-800 dark:text-white">Microsoft</h4>
                                <p class="text-sm text-gray-500" v-if="user?.microsoft_id">Linked</p>
                                <p class="text-sm text-gray-500" v-else>Not linked</p>
                            </div>
                        </div>
                        <button v-if="user?.microsoft_id" @click="unlink('microsoft')"
                            class="py-2 px-3 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-gray-200 bg-white text-red-500 shadow-sm hover:bg-gray-50 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-gray-700 dark:hover:bg-gray-800 dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                            Unlink
                        </button>
                        <button v-else @click="link('microsoft')"
                            class="py-2 px-3 inline-flex items-center gap-x-2 text-sm font-semibold rounded-lg border border-transparent bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none dark:focus:outline-none dark:focus:ring-1 dark:focus:ring-gray-600">
                            Link
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </Page>
</template>

<script setup>
import { useAuthStore } from '~/stores/auth';
import { useToastStore } from '~/stores/toast';

useHead({ title: 'Settings' });

const authStore = useAuthStore();
const toast = useToastStore();
const route = useRoute();
const router = useRouter();

const user = computed(() => authStore.user);

// Relay Server URL - In production this should be configurable
// For now we assume the user will deploy it and we can perhaps ask for it or default to a known one
// Since the user asked for a repo, they will likely self-host.
// We'll use a placeholder or environment variable.
const RELAY_URL = ''; // Relative path for proxy usage

const link = (provider) => {
    // Current URL to return to
    const returnUrl = window.location.href;

    // Redirect to Relay
    window.location.href = `${RELAY_URL}/login/${provider}?return_url=${encodeURIComponent(returnUrl)}`;
};

const unlink = async (provider) => {
    try {
        await authStore.unlinkAccount(provider);
        toast.success(`${provider} unlinked successfully`);
    } catch (error) {
        toast.error(error.message);
    }
};

// Check for callback params
onMounted(async () => {
    const { provider, provider_id, email, name, username } = route.query;

    if (provider && provider_id) {
        try {
            await authStore.linkAccount(provider, provider_id, email, name, username);
            toast.success(`${provider} linked successfully`);

            // Clear query params
            router.replace({ query: {} });
        } catch (error) {
            toast.error(error.message);
        }
    }
});
</script>
