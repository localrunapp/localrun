<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';
import * as icons from "@tabler/icons-vue";
import { useServers } from '@/composables/useServers';
import BaseModal from '@/components/BaseModal.vue';

const props = defineProps({
  isOpen: Boolean,
  server: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['close']);

const { scanServer, getServer } = useServers();
const loading = ref(false);
const scanning = ref(false);
const services = ref([]);
const lastScan = ref(null);
let pollInterval = null;

// Fetch latest server details (including discovered_services)
const fetchDetails = async () => {
  if (!props.server?.id) return;
  loading.value = true;
  try {
    const data = await getServer(props.server.id);
    if (data && data.services) {
      services.value = data.services;
    }
    // Check if currently scanning (if API provided status)
    if (data.scanning_status === 'scanning') {
      scanning.value = true;
      startPolling();
    } else {
      scanning.value = false;
      stopPolling();
    }
  } catch (e) {
    console.error("Failed to fetch server details", e);
  } finally {
    loading.value = false;
  }
};

const handleScan = async () => {
  scanning.value = true;
  try {
    await scanServer(props.server.id);
    startPolling();
  } catch (e) {
    console.error("Failed to trigger scan", e);
    scanning.value = false;
  }
};

const startPolling = () => {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const data = await getServer(props.server.id);
      if (data && data.services) {
        services.value = data.services;
      }
      if (data.scanning_status !== 'scanning') {
        scanning.value = false;
        stopPolling();
      }
    } catch (e) {
      console.error("Polling error", e);
    }
  }, 2000); // Poll every 2 seconds
};

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
};

const effectiveHost = computed(() => {
  if (!props.server) return 'localhost';
  
  if (props.server.is_local) {
      // For local servers, use the host (usually 127.0.0.1 or localhost)
      return props.server.host || 'localhost';
  } else {
      // For remote servers, prefer network_ip (LAN IP) over host (likely Docker/Proxy IP)
      return props.server.network_ip || props.server.host;
  }
});

// Start fetching when modal opens
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchDetails();
  } else {
    stopPolling();
  }
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <BaseModal
    :isOpen="isOpen"
    :title="`Discovered Services - ${server?.name}`"
    :icon="icons.IconScan"
    maxWidth="sm:max-w-5xl"
    @close="$emit('close')"
  >
    <div class="space-y-4">
      <!-- Status Bar -->
      <div v-if="scanning" class="flex items-center gap-3 p-3 bg-blue-50 text-blue-700 rounded-lg dark:bg-blue-900/20 dark:text-blue-200">
        <icons.IconLoader2 class="w-5 h-5 animate-spin" />
        <span class="text-sm font-medium">Scanning server for open ports and services...</span>
      </div>

      <!-- Services Table -->
      <div class="border rounded-lg overflow-hidden border-gray-200 dark:border-gray-700 overflow-y-auto max-h-[60vh]">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700 relative">
          <thead class="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400">Service</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400">Port</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400">Protocol</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400">State</th>
              <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200 dark:bg-gray-900 dark:divide-gray-700">
            <template v-if="services.length > 0">
              <tr v-for="(svc, index) in services" :key="index" class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                  <div class="flex flex-col gap-0.5">
                    <div class="flex items-center gap-2">
                        <span>{{ svc.service !== 'Unknown' ? svc.service : (svc.name || 'Unknown') }}</span>
                        <span v-if="svc.version" class="text-xs font-normal text-gray-500 dark:text-gray-400 border-l border-gray-300 dark:border-gray-600 pl-2">
                            {{ svc.version.length > 25 ? svc.version.substring(0, 25) + '...' : svc.version }}
                        </span>
                    </div>
                    <!-- Details Row -->
                    <div class="flex items-center gap-3 text-xs font-normal text-gray-500 dark:text-gray-400">
                        <!-- Process Info -->
                        <span v-if="svc.process" class="flex items-center gap-1" title="Process">
                            <icons.IconCpu class="size-3" />
                            {{ svc.process.name }} ({{ svc.process.pid }})
                        </span>
                        <!-- Docker Info -->
                        <span v-if="svc.docker" class="flex items-center gap-1 text-blue-600 dark:text-blue-400" title="Docker Container">
                            <icons.IconBrandDocker class="size-3" />
                            {{ svc.docker.name }}
                        </span>
                        <!-- Banner (Tooltip) -->
                        <span v-if="svc.banner" class="flex items-center gap-1" :title="svc.banner">
                            <icons.IconInfoCircle class="size-3" />
                            Banner
                        </span>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 font-mono">
                  <a 
                    :href="`http://${effectiveHost}:${svc.port}`" 
                    target="_blank" 
                    :title="`http://${effectiveHost}:${svc.port}`"
                    class="text-blue-600 hover:underline dark:text-blue-400 flex items-center gap-1"
                  >
                    {{ svc.port }}
                    <icons.IconExternalLink class="size-3" />
                  </a>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 uppercase">
                  {{ svc.protocol || 'tcp' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                    {{ svc.state || 'Open' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <NuxtLink
                    :to="{
                      path: '/services',
                      query: {
                        create: 'true',
                        server_id: server.id,
                        port: svc.port,
                        protocol: svc.protocol || 'tcp',
                        name: (svc.service && svc.service !== 'Unknown') ? svc.service : (svc.docker?.name || svc.process?.name || svc.name || `Service ${svc.port}`)
                      }
                    }"
                    class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                    @click="$emit('close')"
                  >
                    Expose Service
                  </NuxtLink>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="5" class="px-6 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                No services found. Click "Scan Now" to discover running services.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Action Footer -->
      <div class="flex justify-end gap-3 pt-2">
        <button
          @click="$emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
        >
          Close
        </button>
        <button
          @click="handleScan"
          :disabled="scanning"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <icons.IconRefresh v-if="!scanning" class="w-4 h-4" />
          <icons.IconLoader2 v-else class="w-4 h-4 animate-spin" />
          {{ scanning ? 'Scanning...' : 'Scan Now' }}
        </button>
      </div>
    </div>
  </BaseModal>
</template>
