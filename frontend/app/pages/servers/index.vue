<script setup>
import { ref, onMounted, computed, onUnmounted } from "vue";
import { useToast } from "@/composables/useToast";
import { useServersList } from "@/composables/useServers";
import { useMetrics } from "@/composables/useMetrics";
import * as icons from "@tabler/icons-vue";
import { IconServer } from "@tabler/icons-vue";
import ServerRegistrationModal from "@/components/ServerRegistrationModal.vue";
import CliInstallModal from "@/components/CliInstallModal.vue";
import ScanServicesModal from "@/components/Server/ScanServicesModal.vue"; // NEW import
import MultiServerChart from "@/components/MultiServerChart.vue";
import ServerTableItem from "@/components/Server/TableItem.vue";

const toast = useToast();
const isModalOpen = ref(false);
const isCliModalOpen = ref(false);

// Use the enhanced server list composable
const {
  servers,
  loading,
  allStats,
  networkIp,
  fetchServers,
  createServer,
  formatHost,
} = useServersList();

// Use metrics composable
const { getServerHistory } = useMetrics();

// Historical data for charts - array of server histories
const serversHistoricalData = ref([]);
const loadingHistory = ref(false);

// Time range filter (in hours)
const selectedTimeRange = ref(0.25); // Default 15 minutes

// Aggregated metrics
const aggregatedMetrics = computed(() => {
  const connected = servers.value.filter((s) => s.agent_status === "connected");
  const hasStats = connected.filter((s) => allStats.value[s.id]);

  // Calculate averages
  const totalCpu = hasStats.reduce(
    (sum, s) => sum + (allStats.value[s.id]?.cpu_percent || 0),
    0
  );
  const totalRam = hasStats.reduce(
    (sum, s) => sum + (allStats.value[s.id]?.memory_percent || 0),
    0
  );
  const totalDisk = hasStats.reduce(
    (sum, s) => sum + (allStats.value[s.id]?.disk_percent || 0),
    0
  );

  const avgCpu = hasStats.length > 0 ? totalCpu / hasStats.length : 0;
  const avgRam = hasStats.length > 0 ? totalRam / hasStats.length : 0;
  const avgDisk = hasStats.length > 0 ? totalDisk / hasStats.length : 0;

  // Calculate totals
  const totalCores = hasStats.reduce(
    (sum, s) => sum + (allStats.value[s.id]?.cpu_cores || 0),
    0
  );
  const totalMemory = hasStats.reduce(
    (sum, s) => sum + (allStats.value[s.id]?.memory_gb || 0),
    0
  );

  return {
    totalServers: servers.value.length,
    connectedServers: connected.length,
    disconnectedServers: servers.value.length - connected.length,
    activeAgents: hasStats.length,
    avgCpu: Math.round(avgCpu),
    avgRam: Math.round(avgRam),
    avgDisk: Math.round(avgDisk),
    totalCores,
    totalMemory: Math.round(totalMemory),
  };
});

// Fetch historical metrics for all connected servers
const fetchHistoricalMetrics = async () => {
  const connectedServers = servers.value.filter(
    (s) => s.agent_status === "connected"
  );

  console.log(
    "Fetching historical metrics for",
    connectedServers.length,
    "connected servers",
    "Range:",
    selectedTimeRange.value,
    "hours"
  );

  if (connectedServers.length === 0) {
    console.log("No connected servers, skipping historical metrics");
    serversHistoricalData.value = [];
    return;
  }

  loadingHistory.value = true;

  try {
    // Fetch history for each connected server with selected time range
    const promises = connectedServers.map((s) =>
      getServerHistory(s.id, selectedTimeRange.value)
    );
    const results = await Promise.all(promises);

    console.log("Historical metrics results:", results);

    // Filter out null results
    const validResults = results.filter(
      (r) => r !== null && r.entries && r.entries.length > 0
    );
    console.log("Valid historical results:", validResults.length);

    serversHistoricalData.value = validResults;
  } catch (e) {
    console.error("Error fetching historical metrics:", e);
    serversHistoricalData.value = [];
  } finally {
    loadingHistory.value = false;
  }
};

onMounted(async () => {
  await fetchServers();

  // Wait a bit for servers to be populated
  setTimeout(() => {
    fetchHistoricalMetrics();
  }, 500);

  // Refresh historical data every 5 minutes
  const interval = setInterval(fetchHistoricalMetrics, 5 * 60 * 1000);

  onUnmounted(() => {
    clearInterval(interval);
  });
});

const handleRegister = async (data) => {
  try {
    await createServer(data);
    toast.success("Server registered successfully");
    isModalOpen.value = false;
  } catch (e) {
    toast.error("Failed to register server");
    console.error(e);
  }
};

const openCliModal = () => {
  isCliModalOpen.value = true;
};

const refreshAll = async () => {
  await fetchServers();
  await fetchHistoricalMetrics();
};

const isScanModalOpen = ref(false);
const selectedServerForScan = ref(null);

const openScanModal = (server) => {
  selectedServerForScan.value = server;
  isScanModalOpen.value = true;
};
</script>

<template>
  <Page>
    <template #header>
      <PageHeader
        :icon="IconServer"
        :title="`Servers (${servers.length})`"
        backPath="/"
      >
        <template #actions>
          <button
            @click="isModalOpen = true"
            class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 "
          >
            <icons.IconPlus class="w-4 h-4" />
            New
          </button>
          <button
            @click="refreshAll"
            class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 "
          >
            <icons.IconRefresh
              class="w-5 h-5"
              :class="{ 'animate-spin': loading }"
            />
          </button>
        </template>
      </PageHeader>
    </template>

    <!-- Two Column Layout -->
    <div class="grid lg:grid-cols-12 min-h-screen">
      <!-- Main Table (Left) -->
      <div class="col-span-12 2xl:col-span-8 border-r border-gray-200 dark:border-gray-700">
        <div class="flex flex-col">
          <div class="overflow-x-auto">
            <div class="min-w-full inline-block align-middle">
              <!-- Table -->
              <table
                class="min-w-full divide-y divide-gray-200 dark:divide-gray-700"
              >
                <thead class="bg-white dark:bg-gray-800">
                  <tr>
                    <th
                      scope="col"
                      class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Name
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      Hardware Stats
                    </th>
                    <th
                      scope="col"
                      class="px-6 py-3 text-start text-xs font-medium text-gray-500 uppercase dark:text-gray-400"
                    >
                      CLI Agent
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
                  <tr v-if="loading && servers.length === 0">
                    <td
                      colspan="4"
                      class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400"
                    >
                      Loading servers...
                    </td>
                  </tr>
                  <tr v-else-if="servers.length === 0">
                    <td
                      colspan="4"
                      class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400"
                    >
                      No servers found.
                    </td>
                  </tr>
                  <ServerTableItem
                    v-else
                    v-for="server in servers"
                    :key="server.id"
                    :server="server"
                    :formatted-host="formatHost(server)"
                    @install="openCliModal"
                    @scan="openScanModal(server)"
                    @review="
                      () => {
                        /* Implement review logic later */
                      }
                    "
                  />
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Metrics Sidebar (Right) -->
      <div class="hidden 2xl:block 2xl:col-span-4 space-y-4">
        <!-- Historical Metrics Charts -->
        <div
          v-if="loadingHistory"
          class="bg-white border border-gray-200 rounded-lg p-4 dark:bg-gray-800 dark:border-gray-700"
        >
          <div class="flex items-center justify-center h-[200px]">
            <div class="text-sm text-gray-500 dark:text-gray-400">
              Loading charts...
            </div>
          </div>
        </div>

        <div
          v-else-if="serversHistoricalData.length === 0"
          class="bg-white border-b border-gray-200 p-4 dark:bg-gray-800 dark:border-gray-700"
        >
          <div class="flex items-center justify-center h-[200px]">
            <div class="text-center">
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-2">
                No historical data available
              </div>
              <div class="text-xs text-gray-400 dark:text-gray-500 mb-2">
                Connected servers: {{ aggregatedMetrics.connectedServers }} |
                Total servers: {{ aggregatedMetrics.totalServers }}
              </div>
              <div class="text-xs text-gray-400 dark:text-gray-500">
                {{
                  loadingHistory
                    ? "Loading..."
                    : "Connect servers with CLI-agent to see metrics"
                }}
              </div>
            </div>
          </div>
        </div>

        <template v-else>
          <!-- All Charts in One Card -->
          <div class="h-full">
            <!-- Time Range Filter -->
            <div class="p-2 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-center gap-3">
                <label
                  for="time-range"
                  class="text-sm text-gray-700 dark:text-gray-300"
                >
                  Time Range:
                </label>
                <div class="relative">
                  <select
                    id="time-range"
                    v-model="selectedTimeRange"
                    @change="fetchHistoricalMetrics"
                    :disabled="loadingHistory"
                    class="py-0.5 px-2 pe-12 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-gray-900 dark:border-gray-700 dark:text-gray-400 dark:placeholder-gray-500 dark:focus:ring-gray-600"
                  >
                    <option :value="0.25">15 minutos</option>
                    <option :value="1">1 hora</option>
                    <option :value="6">6 horas</option>
                    <option :value="24">1 día</option>
                    <option :value="168">7 días</option>
                    <option :value="336">2 semanas</option>
                  </select>
                  <!-- Loading Spinner -->
                  <div
                    v-if="loadingHistory"
                    class="absolute inset-y-0 end-0 flex items-center pe-3 pointer-events-none"
                  >
                    <svg
                      class="animate-spin h-4 w-4 text-blue-600"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        class="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        stroke-width="4"
                      ></circle>
                      <path
                        class="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- CPU Chart -->
            <div class="p-4">
              <h3
                class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-4"
              >
                CPU Usage
              </h3>
              <MultiServerChart
                :servers-data="serversHistoricalData"
                metric="cpu"
                :show-card="false"
                :height="160"
              />
            </div>

            <!-- Divider -->
            <div class="border-t border-gray-200 dark:border-gray-700"></div>

            <!-- Memory Chart -->
            <div class="p-4">
              <h3
                class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-4"
              >
                Memory Usage
              </h3>
              <MultiServerChart
                :servers-data="serversHistoricalData"
                metric="memory"
                :show-card="false"
                :height="160"
              />
            </div>



            <!-- Divider -->
            <div class="border-t border-gray-200 dark:border-gray-700"></div>

            <!-- IOPS Chart -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3
                class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-4"
              >
                High Performance I/O
              </h3>
              <MultiServerChart
                :servers-data="serversHistoricalData"
                metric="iops"
                :show-card="false"
                :height="160"
              />
            </div>
          </div>
        </template>
      </div>
    </div>

    <ServerRegistrationModal
      :isOpen="isModalOpen"
      :networkIp="networkIp"
      @close="isModalOpen = false"
      @register="handleRegister"
    />

    <CliInstallModal
      :isOpen="isCliModalOpen"
      :networkIp="networkIp"
      @close="isCliModalOpen = false"
    />

    <ScanServicesModal
      v-if="selectedServerForScan"
      :isOpen="isScanModalOpen"
      :server="selectedServerForScan"
      @close="isScanModalOpen = false"
    />
  </Page>
</template>
