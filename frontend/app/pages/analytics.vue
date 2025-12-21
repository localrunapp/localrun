<template>
  <Page>
    <template #header>
      <PageHeader :icon="IconActivity" title="Analytics" backPath="/">
        <template #actions>
          <!-- Server Selector -->
          <div v-if="servers.length > 0" class="relative">
            <select
              v-model="selectedServerId"
              @change="fetchAnalytics"
              class="py-2 px-3 pe-9 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 disabled:opacity-50 disabled:pointer-events-none dark:bg-slate-900 dark:border-gray-700 dark:text-gray-400 dark:focus:ring-gray-600"
            >
              <option
                v-for="server in servers"
                :key="server.id"
                :value="server.id"
              >
                {{ server.name }}
              </option>
            </select>
          </div>
        </template>
      </PageHeader>
    </template>

    <div class="p-4 space-y-6">
      <div v-if="loading" class="flex justify-center items-center py-20">
        <div
          class="animate-spin inline-block size-8 border-[3px] border-current border-t-transparent text-blue-600 rounded-full dark:text-blue-500"
          role="status"
          aria-label="loading"
        >
          <span class="sr-only">Loading...</span>
        </div>
      </div>

      <div
        v-else-if="error"
        class="bg-red-50 border border-red-200 text-sm text-red-800 rounded-lg p-4 dark:bg-red-800/10 dark:border-red-900 dark:text-red-500"
        role="alert"
      >
        {{ error }}
      </div>

      <div v-else class="space-y-6">
        <!-- Stats Grid -->
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <!-- Card -->
          <div
            class="flex flex-col bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
          >
            <div class="p-4 md:p-5">
              <div class="flex items-center gap-x-2">
                <p class="text-xs uppercase tracking-wide text-gray-500">
                  Total Requests
                </p>
              </div>
              <div class="mt-1 flex items-center gap-x-2">
                <h3
                  class="text-xl sm:text-2xl font-medium text-gray-800 dark:text-gray-200"
                >
                  {{ analytics?.total_requests?.toLocaleString() || 0 }}
                </h3>
              </div>
            </div>
          </div>
          <!-- End Card -->

          <!-- Card -->
          <div
            class="flex flex-col bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
          >
            <div class="p-4 md:p-5">
              <div class="flex items-center gap-x-2">
                <p class="text-xs uppercase tracking-wide text-gray-500">
                  Avg Response Time
                </p>
              </div>
              <div class="mt-1 flex items-center gap-x-2">
                <h3
                  class="text-xl sm:text-2xl font-medium text-gray-800 dark:text-gray-200"
                >
                  {{ analytics?.avg_response_time_ms }} ms
                </h3>
              </div>
            </div>
          </div>
          <!-- End Card -->

          <!-- Card -->
          <div
            class="flex flex-col bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
          >
            <div class="p-4 md:p-5">
              <div class="flex items-center gap-x-2">
                <p class="text-xs uppercase tracking-wide text-gray-500">
                  Bandwidth
                </p>
              </div>
              <div class="mt-1 flex items-center gap-x-2">
                <h3
                  class="text-xl sm:text-2xl font-medium text-gray-800 dark:text-gray-200"
                >
                  {{ analytics?.total_bandwidth_mb }} MB
                </h3>
              </div>
            </div>
          </div>
          <!-- End Card -->
        </div>
        <!-- End Stats Grid -->

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Devices Card -->
          <div
            class="bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
          >
            <div
              class="p-4 md:p-5 border-b border-gray-200 dark:border-gray-700"
            >
              <h2
                class="text-lg font-semibold text-gray-800 dark:text-gray-200"
              >
                Devices
              </h2>
            </div>
            <div class="p-4 md:p-5">
              <div class="min-h-[300px] flex items-center justify-center">
                <ClientOnly>
                  <apexchart
                    v-if="deviceSeries.length > 0"
                    type="donut"
                    height="300"
                    :options="deviceOptions"
                    :series="deviceSeries"
                  />
                  <div v-else class="text-gray-500 dark:text-gray-400">
                    No device data available
                  </div>
                </ClientOnly>
              </div>
            </div>
          </div>
          <!-- End Devices Card -->

          <!-- Countries Card -->
          <div
            class="bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
          >
            <div
              class="p-4 md:p-5 border-b border-gray-200 dark:border-gray-700"
            >
              <h2
                class="text-lg font-semibold text-gray-800 dark:text-gray-200"
              >
                Top Countries
              </h2>
            </div>
            <div class="p-4 md:p-5">
              <ul class="space-y-4">
                <li
                  v-for="(count, country) in topCountries"
                  :key="country"
                  class="flex justify-between items-center group"
                >
                  <div class="flex items-center gap-x-3">
                    <span
                      class="text-sm text-gray-800 dark:text-gray-200 font-medium"
                      >{{ country }}</span
                    >
                  </div>
                  <div class="flex items-center gap-x-3">
                    <span class="text-sm text-gray-500"
                      >{{ count }} visits</span
                    >
                    <div
                      class="w-20 h-1.5 bg-gray-100 rounded-full dark:bg-gray-700 overflow-hidden"
                    >
                      <div
                        class="h-full bg-blue-600 rounded-full"
                        :style="{
                          width:
                            getPercentage(count, analytics?.total_requests) +
                            '%',
                        }"
                      ></div>
                    </div>
                    <span class="text-xs text-gray-500 w-8 text-right"
                      >{{
                        getPercentage(count, analytics?.total_requests)
                      }}%</span
                    >
                  </div>
                </li>
                <li
                  v-if="
                    !analytics?.countries ||
                    Object.keys(analytics.countries).length === 0
                  "
                  class="text-gray-500 dark:text-gray-400 text-center py-4"
                >
                  No country data available
                </li>
              </ul>
            </div>
          </div>
          <!-- End Countries Card -->
        </div>

        <!-- Map Section -->
        <div
          class="bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
        >
          <div class="p-4 md:p-5 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">
              Real-time Users Map
            </h2>
          </div>
          <div class="p-4 md:p-5">
            <ClientOnly>
              <WorldMap :data="countryCodes" />
            </ClientOnly>
          </div>
        </div>
        <!-- End Map Section -->

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Top Paths -->
          <div
            class="bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
          >
            <div
              class="p-4 md:p-5 border-b border-gray-200 dark:border-gray-700"
            >
              <h2
                class="text-lg font-semibold text-gray-800 dark:text-gray-200"
              >
                Top Paths
              </h2>
            </div>
            <div class="p-4 md:p-5 overflow-hidden">
              <div class="space-y-4">
                <div
                  v-for="(count, path) in analytics?.top_paths"
                  :key="path"
                  class="flex flex-col gap-y-1"
                >
                  <div class="flex justify-between items-center">
                    <span
                      class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate max-w-[70%]"
                      >{{ path }}</span
                    >
                    <span class="text-xs text-gray-500">{{ count }} hits</span>
                  </div>
                  <div
                    class="w-full h-1.5 bg-gray-100 rounded-full dark:bg-gray-700 overflow-hidden"
                  >
                    <div
                      class="h-full bg-indigo-500 rounded-full"
                      :style="{
                        width:
                          getPercentage(count, analytics?.total_requests) + '%',
                      }"
                    ></div>
                  </div>
                </div>
                <div
                  v-if="
                    !analytics?.top_paths ||
                    Object.keys(analytics.top_paths).length === 0
                  "
                  class="text-gray-500 dark:text-gray-400 text-center py-4"
                >
                  No path data available
                </div>
              </div>
            </div>
          </div>
          <!-- End Top Paths -->

          <!-- Browsers -->
          <div
            class="bg-white border shadow-sm rounded-xl dark:bg-slate-900 dark:border-gray-700"
          >
            <div
              class="p-4 md:p-5 border-b border-gray-200 dark:border-gray-700"
            >
              <h2
                class="text-lg font-semibold text-gray-800 dark:text-gray-200"
              >
                Browsers
              </h2>
            </div>
            <div class="p-4 md:p-5">
              <div class="space-y-4">
                <div
                  v-for="(count, browser) in analytics?.browsers"
                  :key="browser"
                  class="flex items-center justify-between"
                >
                  <span class="text-sm text-gray-800 dark:text-gray-200">{{
                    browser
                  }}</span>
                  <span class="text-sm font-medium text-gray-500">{{
                    count
                  }}</span>
                </div>
                <div
                  v-if="
                    !analytics?.browsers ||
                    Object.keys(analytics.browsers).length === 0
                  "
                  class="text-gray-500 dark:text-gray-400 text-center py-4"
                >
                  No browser data available
                </div>
              </div>
            </div>
          </div>
          <!-- End Browsers -->
        </div>
      </div>
    </div>
  </Page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { IconActivity } from "@tabler/icons-vue";

useHead({
  title: "Analytics",
});

const config = useRuntimeConfig();
const servers = ref<any[]>([]);
const selectedServerId = ref<string>("");
const analytics = ref<any>(null);
const loading = ref(false);
const error = ref<string | null>(null);

// Charts
const deviceSeries = ref<number[]>([]);
const deviceOptions = ref({
  chart: {
    type: "donut",
    height: 300,
    fontFamily: "Inter, ui-sans-serif",
    toolbar: { show: false },
    background: "transparent",
  },
  labels: [] as string[],
  colors: ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#64748b"],
  plotOptions: {
    pie: {
      donut: {
        size: "65%",
        labels: {
          show: true,
          total: {
            show: true,
            label: "Total",
            color: "#9ca3af",
            formatter: function (w: any) {
              return w.globals.seriesTotals.reduce(
                (a: any, b: any) => a + b,
                0
              );
            },
          },
        },
      },
    },
  },
  dataLabels: { enabled: false },
  stroke: { show: false },
  legend: { position: "bottom" },
  theme: { mode: "light" },
});

const fetchServers = async () => {
  try {
    const { data } = await useFetch(`${config.public.apiBase}/servers`);
    if (data.value) {
      servers.value = data.value;
      if (servers.value.length > 0) {
        selectedServerId.value = servers.value[0].id;
      }
    }
  } catch (e) {
    console.error("Error fetching servers", e);
    error.value = "Failed to load servers.";
  }
};

const fetchAnalytics = async () => {
  if (!selectedServerId.value) return;
  loading.value = true;
  error.value = null;
  try {
    const { data } = await useFetch(
      `${config.public.apiBase}/metrics/servers/${selectedServerId.value}/analytics`
    );
    if (data.value) {
      analytics.value = data.value;
      updateCharts();
    }
  } catch (e) {
    console.error("Error fetching analytics", e);
    error.value = "Failed to load analytics data.";
    analytics.value = null;
  } finally {
    loading.value = false;
  }
};

const updateCharts = () => {
  if (!analytics.value) return;

  // Devices
  const devices = analytics.value.devices || {};
  deviceOptions.value = {
    ...deviceOptions.value,
    labels: Object.keys(devices).map(
      (k) => k.charAt(0).toUpperCase() + k.slice(1)
    ),
  };
  deviceSeries.value = Object.values(devices);
};

const topCountries = computed(() => {
  if (!analytics.value?.countries) return {};
  return analytics.value.countries;
});

const countryCodes = computed(() => {
  if (!analytics.value?.country_codes) return {};
  return analytics.value.country_codes;
});

const getPercentage = (value: number, total: number) => {
  if (!total || total === 0) return 0;
  return Math.round((value / total) * 100);
};

onMounted(async () => {
  await fetchServers();
  if (selectedServerId.value) {
    await fetchAnalytics();
  }
});
</script>
