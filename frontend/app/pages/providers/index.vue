<script setup>
import { ref, onMounted, computed } from 'vue';
import { useAuthStore } from '@/stores/auth.js';
import { IconPlug } from '@tabler/icons-vue';

const config = useRuntimeConfig();
const authStore = useAuthStore();
const providers = ref([]);
const selectedFilter = ref('All');

const staticProviders = [
    {
        key: 'ngrok',
        name: 'Ngrok',
        description: 'Configurar tueneles anónimos y privados.',
        icon: 'simple-icons:ngrok',
        iconSize: 130,
        link: '/providers/ngrok',
        tags: ['Tunnel']
    },
    {
        key: 'cloudflare',
        name: 'Cloudflare',
        description: 'Configurar tueneles anónimos y privados, además de autoconfiguración de DNS.',
        icon: 'simple-icons:cloudflare',
        iconSize: 110,
        link: '/providers/cloudflare',
        tags: ['DNS', 'Tunnel']
    },
    {
        key: 'namecheap',
        name: 'Namecheap',
        description: 'Integra tu cuenta de Namecheap para autoconfiguración de DNS.',
        icon: 'simple-icons:namecheap',
        iconSize: 110,
        link: '/providers/namecheap', // Updated to logical link, though page might not exist yet
        tags: ['DNS']
    }
];

const fetchProviders = async () => {
    try {
        const response = await fetch('/api/providers', {
            headers: {
                'Authorization': `Bearer ${authStore.getToken()}`
            }
        });
        if (response.ok) {
            providers.value = await response.json();
        } else {
            console.error('Failed to fetch providers');
        }
    } catch (error) {
        console.error('Error fetching providers:', error);
    }
};

const isConfigured = (key) => {
    const provider = providers.value.find(p => p.key === key);
    return provider ? provider.has_credentials : false;
};

const filteredProviders = computed(() => {
    if (selectedFilter.value === 'All') {
        return staticProviders;
    }
    return staticProviders.filter(p => p.tags.includes(selectedFilter.value));
});

onMounted(() => {
    fetchProviders();
});
</script>

<template>
    <Page>
        <template #header>
            <PageHeader :icon="IconPlug" title="Providers" subtitle="Manage your tunnel providers and integrations."
                backPath="/" />
        </template>

        <div class="p-2 pt-4 mx-auto">
            <!-- Filters -->
            <div class="flex gap-x-2 mb-6">
                <button v-for="filter in ['All', 'Tunnel', 'DNS', 'Notification']" :key="filter"
                    @click="selectedFilter = filter" :class="[
                        'py-2 px-3 inline-flex items-center gap-x-2 text-sm font-medium rounded-lg border border-1.5',
                        selectedFilter === filter
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-white text-gray-800 hover:bg-gray-50 border-gray-200 dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:hover:bg-slate-800'
                    ]">
                    {{ filter }}
                </button>
            </div>

            <!-- Grid -->
            <div class="grid sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                <div v-for="provider in filteredProviders" :key="provider.key"
                    class="group flex flex-col h-full bg-white border border-slate-200 shadow-sm rounded-xl dark:bg-slate-900 dark:border-slate-700">
                    <div
                        class="h-40 flex flex-col justify-center items-center bg-slate-100 rounded-t-xl dark:bg-slate-800">
                        <Icon :name="provider.icon" :size="provider.iconSize"
                            class="text-slate-600 dark:text-slate-400" />
                    </div>
                    <div class="p-4 md:p-6">
                        <h3 class="text-xl font-semibold text-slate-800 dark:text-slate-300 dark:hover:text-white">
                            {{ provider.name }}
                        </h3>
                        <p class="mt-3 text-sm text-slate-500 dark:text-slate-500">
                            {{ provider.description }}
                        </p>
                        <div class="flex justify-between items-start mt-4">
                            <div class="flex gap-1">
                                <span v-for="tag in provider.tags" :key="tag"
                                    class="inline-flex items-center py-1.5 px-3 rounded-full text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200">
                                    {{ tag }}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div
                        class="mt-auto flex border-t border-slate-200 divide-x divide-slate-200 dark:border-slate-700 dark:divide-slate-700">
                        <NuxtLink :to="provider.link"
                            class="w-full py-3 px-4 inline-flex justify-center items-center gap-x-2 text-sm font-medium rounded-es-xl bg-white text-slate-800 shadow-sm hover:bg-slate-50 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:hover:bg-slate-800">
                            Configure
                        </NuxtLink>
                        <div
                            class="w-full py-3 px-4 inline-flex justify-center items-center gap-x-2 text-sm font-medium rounded-ee-xl bg-white text-slate-800 shadow-sm hover:bg-slate-50 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-slate-700 dark:text-white dark:hover:bg-slate-800">
                            <span v-if="isConfigured(provider.key)" class="flex items-center gap-x-1 text-teal-500">
                                <Icon name="tabler:check" size="18" />
                                <span class="text-xs">
                                    Configured
                                </span>
                            </span>
                            <span v-else class="text-slate-400">
                                <span class="text-xs">
                                    Not Configured
                                </span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            <!-- End Grid -->
        </div>
    </Page>
</template>
