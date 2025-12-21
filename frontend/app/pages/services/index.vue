<script setup>
import * as icons from "@tabler/icons-vue";
import ServiceTableItem from "@/components/Service/TableItem.vue";
import ServiceGraphView from "@/components/Service/GraphView.vue";

const api = useApi();
const toast = useToast();

const services = ref([]);
const servers = ref([]);
const dnsRecords = ref([]);
const availableProviders = ref([]);
const loadingProviders = ref(false);
const refreshingServices = ref(false);
const refreshing = ref(false);
const showCreateModal = ref(false);
const preselectedServerId = ref("");
const viewMode = ref("table"); // 'table' or 'graph'

const openCreateModal = () => {
  preselectedServerId.value = "";
  showCreateModal.value = true;
};

const handleServiceCreated = () => {
  fetchServices();
};

const filters = reactive({
  search: "",
  status: "",
  protocol: "",
  provider: "",
});

useHead({ title: "Services" });

const filteredServices = computed(() => {
  return services.value.filter((service) => {
    // Search - filter by all columns
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      const server = servers.value.find((s) => s.id === service.server_id);
      const serverName = server?.name?.toLowerCase() || "";

      const matches =
        service.name.toLowerCase().includes(searchLower) ||
        service.host.toLowerCase().includes(searchLower) ||
        service.port.toString().includes(searchLower) ||
        service.protocol.toLowerCase().includes(searchLower) ||
        service.provider_key.toLowerCase().includes(searchLower) ||
        serverName.includes(searchLower) ||
        (service.public_url &&
          service.public_url.toLowerCase().includes(searchLower)) ||
        (service.domain &&
          service.domain.toLowerCase().includes(searchLower)) ||
        (service.subdomain &&
          service.subdomain.toLowerCase().includes(searchLower));

      if (!matches) return false;
    }

    // Status
    if (filters.status && service.status !== filters.status) return false;
    // Protocol
    if (filters.protocol && service.protocol !== filters.protocol) return false;
    // Provider
    if (filters.provider && service.provider_key !== filters.provider)
      return false;

    return true;
  });
});

const fetchServers = async () => {
  try {
    servers.value = await api.get("/servers");
  } catch (e) {
    console.error("Error loading servers:", e);
  }
};

const fetchDNSRecords = async () => {
  try {
    dnsRecords.value = await api.get("/dns");
  } catch (e) {
    console.error("Error loading DNS records:", e);
  }
};

const fetchProviders = async () => {
  loadingProviders.value = true;
  try {
    const response = await api.get("/services/providers/available");
    availableProviders.value = response?.providers || [];
  } catch (e) {
    console.error("Error loading providers:", e);
    availableProviders.value = [];
  } finally {
    loadingProviders.value = false;
  }
};

const fetchServices = async () => {
  refreshing.value = true;
  try {
    services.value = await api.get("/services");
  } catch (e) {
    console.error(e);
  } finally {
    refreshing.value = false;
  }
};

const refreshAll = () => {
  fetchServices();
};

const startService = async (service) => {
  try {
    await api.post(`/services/${service.id}/start`);
    toast.success("Service started");
    fetchServices();
  } catch (e) {
    toast.error("Error starting service: " + e.message);
  }
};

const stopService = async (service) => {
  try {
    await api.post(`/services/${service.id}/stop`);
    toast.success("Service stopped");
    fetchServices();
  } catch (e) {
    toast.error("Error stopping service: " + e.message);
  }
};

const deleteService = async (service) => {
  try {
    await api.delete(`/services/${service.id}`);
    toast.success("Service deleted");
    fetchServices();
  } catch (e) {
    toast.error("Error deleting service: " + e.message);
  }
};

const reconcileServices = async () => {
  try {
    const result = await api.post("/services/reconcile");
    toast.success(
      `Synced ${result.reconciled} service${result.reconciled !== 1 ? "s" : ""}`
    );
    if (result.reconciled > 0) {
      fetchServices();
    }
  } catch (e) {
    toast.error("Error syncing containers: " + e.message);
  }
};

const route = useRoute();
const router = useRouter();

// Watch for query parameter to open modal
watch(
  () => route.query,
  (query) => {
    if (query.new === 'true') {
      // Check if server parameter is provided
      if (query.server) {
        preselectedServerId.value = query.server;
      } else {
        preselectedServerId.value = "";
      }
      
      showCreateModal.value = true;
    }
  },
  { immediate: true, deep: true }
);

// Clean URL when modal closes
watch(showCreateModal, (isOpen) => {
  if (!isOpen && route.query.new === 'true') {
    // Remove the query parameters from URL without reloading
    router.replace({ query: {} });
  }
});

onMounted(() => {
  fetchServices();
  fetchServers();
  fetchDNSRecords();
  fetchProviders();
});
</script>

<template>
  <Page>
    <template #header>
      <PageHeader title="Services" :icon="icons.IconRocket" backPath="/">
        <template #actions>
          <!-- Sync Containers Button -->
          <button
            @click="reconcileServices"
            class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700"
            title="Sync with running containers"
          >
            <icons.IconRefresh class="w-4 h-4" />
            Sync Containers
          </button>

          <!-- View Toggle-->
          <div
            class="relative inline-flex rounded-lg border border-gray-200 dark:border-gray-700 p-1 bg-white dark:bg-gray-800"
          >
            <!-- Sliding background indicator -->
            <div
              class="absolute top-1 bottom-1 rounded-md bg-gray-200 dark:bg-gray-700 transition-all duration-300 ease-in-out"
              :style="{
                left: viewMode === 'table' ? '4px' : 'calc(50% + 2px)',
                width: 'calc(50% - 6px)',
              }"
            ></div>

            <button
              @click="viewMode = 'table'"
              :class="[
                'relative z-10 flex items-center gap-2 px-3 py-1.5 text-sm rounded-md',
                viewMode === 'table'
                  ? 'text-gray-900 dark:text-gray-100'
                  : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100',
              ]"
            >
              <icons.IconTable class="w-4 h-4" />
              Table
            </button>
            <button
              @click="viewMode = 'graph'"
              :class="[
                'relative z-10 flex items-center gap-2 px-3 py-1.5 text-sm rounded-md',
                viewMode === 'graph'
                  ? 'text-gray-900 dark:text-gray-100'
                  : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100',
              ]"
            >
              <icons.IconChartDots class="w-4 h-4" />
              Graph
            </button>
          </div>

          <button
            @click="openCreateModal"
            class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            <icons.IconPlus class="w-4 h-4" />
            New Service
          </button>
          <button
            @click="refreshAll"
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <icons.IconRefresh
              class="w-5 h-5"
              :class="{ 'animate-spin': refreshing }"
            />
          </button>
        </template>
      </PageHeader>
    </template>

    <!-- Main Layout -->
    <div class="grid lg:grid-cols-12 min-h-screen">
      <div class="col-span-12 border-r border-gray-200 dark:border-gray-700">
        <div class="flex flex-col">
          <!-- Filters Toolbar (only show in table view) -->
          <div
            v-if="viewMode === 'table'"
            class="p-4 border-b border-gray-200 dark:border-gray-700 flex flex-wrap gap-4 items-center"
          >
            <!-- Search -->
            <div class="relative flex-1 min-w-[200px]">
              <div
                class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none"
              >
                <icons.IconSearch class="size-4 text-gray-400" />
              </div>
              <input
                v-model="filters.search"
                type="text"
                placeholder="Search services..."
                class="py-2 pl-10 pr-4 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-900 dark:border-gray-700 dark:text-gray-400"
              />
            </div>

            <!-- Status Filter -->
            <select
              v-model="filters.status"
              class="py-2 px-3 block w-40 border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-900 dark:border-gray-700 dark:text-gray-400"
            >
              <option value="">All Status</option>
              <option value="running">Running</option>
              <option value="stopped">Stopped</option>
            </select>

            <!-- Protocol Filter -->
            <select
              v-model="filters.protocol"
              class="py-2 px-3 block w-40 border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-900 dark:border-gray-700 dark:text-gray-400"
            >
              <option value="">All Protocols</option>
              <option value="http">HTTP</option>
              <option value="tcp">TCP</option>
            </select>

            <!-- Provider Filter -->
            <select
              v-model="filters.provider"
              :disabled="loadingProviders"
              class="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="">
                {{
                  loadingProviders ? "Loading providers..." : "All Providers"
                }}
              </option>
              <option
                v-for="provider in availableProviders"
                :key="provider.key"
                :value="provider.key"
              >
                {{ provider.name }}
              </option>
            </select>
          </div>

          <!-- Table View -->
          <div v-if="viewMode === 'table'" class="overflow-x-auto">
            <div class="min-w-full inline-block align-middle">
              <table
                class="min-w-full divide-y divide-gray-200 dark:divide-gray-700"
              >
                <thead class="bg-white dark:bg-gray-800">
                  <tr>
                    <th
                      scope="col"
                      class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Service
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Server:Port
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Provider
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Status
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Metrics
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Password
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-end text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody
                  class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800"
                >
                  <tr v-if="filteredServices.length === 0">
                    <td
                      colspan="7"
                      class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400"
                    >
                      No services found.
                    </td>
                  </tr>
                  <ServiceTableItem
                    v-else
                    v-for="service in filteredServices"
                    :key="service.id"
                    :service="service"
                    :servers="servers"
                    @start="startService"
                    @stop="stopService"
                    @delete="deleteService"
                  />
                </tbody>
              </table>
            </div>
          </div>

          <!-- Graph View -->
          <div v-else-if="viewMode === 'graph'" class="h-full">
            <ServiceGraphView
              :services="services"
              :servers="servers"
              :dns-records="dnsRecords"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Create Service Modal -->
    <ServiceCreateModal
      :isOpen="showCreateModal"
      :preselectedServerId="preselectedServerId"
      @close="showCreateModal = false"
      @created="handleServiceCreated"
    />
  </Page>
</template>
