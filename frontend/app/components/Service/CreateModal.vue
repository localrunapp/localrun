<script setup>
import * as icons from "@tabler/icons-vue";

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  preselectedServerId: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["close", "created"]);

const api = useApi();
const toast = useToast();

const loading = ref(false);
const servers = ref([]);
const providers = ref([]);
const domains = ref([]);
const loadingDomains = ref(false);

// Form state
const enablePassword = ref(false);
const enableAnalytics = ref(false);
const showDNSConfig = ref(false);
const inputMethod = ref("manual");
const showProviderDropdown = ref(false);
const showServerDropdown = ref(false);
const showMethodDropdown = ref(false);
const showServiceModal = ref(false);
const refreshingServices = ref(false);
const selectedServiceInfo = ref(null); // Store selected service details

const form = reactive({
  name: "",
  port: 8080,
  protocol: "http",
  host: "localhost",
  server_id: "",
  provider_key: "cloudflare_quick",
  tunnel_password: "",
  // DNS fields
  dns_provider_key: "",
  domain: "",
  subdomain: "",
  // Healthcheck fields
  healthcheck_enabled: true,
  healthcheck_path: "/",
  healthcheck_timeout: 5,
  healthcheck_expected_status: 200,
});

// Options
const providerOptions = computed(() => {
  const options = [];
  providers.value.forEach((provider) => {
    if (provider.key === "cloudflare") {
      options.push({
        value: "cloudflare_quick",
        label: "Cloudflare Quick Tunnel",
        description: "(Temporal - No requiere configuración)",
        is_managed: false,
      });

      if (provider.has_credentials) {
        options.push({
          value: "cloudflare",
          label: "Cloudflare Tunnel",
          description: "(Permanente - Requiere configuración)",
          is_managed: true, // Supports DNS
        });
      }
    } else if (provider.key === "pinggy") {
      options.push({
        value: "pinggy",
        label: "Pinggy",
        description: "(SSH Tunnel)",
        is_managed: false,
      });
    }
  });
  return options;
});

const selectedServer = computed(() => {
  return servers.value.find((s) => s.id === form.server_id);
});

const discoveredServices = computed(() => {
  if (!selectedServer.value || !selectedServer.value.detected_services)
    return [];

  try {
    const services = JSON.parse(selectedServer.value.detected_services);
    return services || [];
  } catch (e) {
    console.error("Error parsing detected services:", e);
    return [];
  }
});

// Watchers
watch(
  () => props.isOpen,
  (val) => {
    if (val) {
      fetchServers();
      fetchProviders();
      // Reset form or handle preselection
      if (props.preselectedServerId) {
        form.server_id = props.preselectedServerId;
      }
    }
  }
);

watch(
  () => form.server_id,
  (newServerId, oldServerId) => {
    if (newServerId) {
      const server = selectedServer.value;
      if (server) {
        // Reset input method and selected service when server changes
        if (oldServerId && oldServerId !== newServerId) {
          inputMethod.value = "manual";
          selectedServiceInfo.value = null;
        }

        // Auto-configure usage of Analytics if agent is installed
        if (server.agent_status === "connected") {
          enableAnalytics.value = true;
          // Default to manual, user can switch
        } else {
          enableAnalytics.value = false;
          // Force manual if agent not connected
          inputMethod.value = "manual";
        }
      }
    }
  }
);

watch(
  () => form.provider_key,
  async (newKey) => {
    if (newKey === "cloudflare") {
      showDNSConfig.value = true;
      form.dns_provider_key = "cloudflare";
      await fetchDomains();
    } else {
      showDNSConfig.value = false;
      form.dns_provider_key = "";
      form.domain = "";
      form.subdomain = "";
    }
  }
);

// Actions
const fetchServers = async () => {
  try {
    servers.value = await api.get("/servers");
    // Auto-select first server if none selected
    if (!form.server_id && servers.value.length > 0) {
      form.server_id = servers.value[0].id;
    }
  } catch (e) {
    console.error("Error loading servers:", e);
  }
};

const fetchProviders = async () => {
  try {
    const response = await api.get("/providers");
    providers.value = response || [];
  } catch (e) {
    console.error("Error loading providers:", e);
  }
};

const fetchDomains = async () => {
  loadingDomains.value = true;
  try {
    const response = await api.get("/domains");
    domains.value = response.filter(
      (d) => d.provider_name === form.provider_key
    );
  } catch (e) {
    console.error("Error loading domains:", e);
    toast.error("Failed to load domains");
  } finally {
    loadingDomains.value = false;
  }
};

const refreshServices = async () => {
  if (!selectedServer.value || !selectedServer.value.is_reachable) {
    toast.error("Server is not connected");
    return;
  }

  refreshingServices.value = true;
  try {
    await api.post(`/servers/${selectedServer.value.id}/scan`);

    setTimeout(async () => {
      await fetchServers();
      refreshingServices.value = false;
    }, 3000);
  } catch (e) {
    toast.error("Error refreshing services: " + e.message);
    refreshingServices.value = false;
  }
};

const selectDiscoveredService = (service) => {
  form.port = service.port;
  form.protocol = service.protocol || "http";

  let name = "";
  if (service.service && service.service !== "Unknown") {
    name = service.service;
  } else if (service.docker && service.docker.name) {
    name = service.docker.name;
  } else if (service.process && service.process.name) {
    name = service.process.name;
  } else {
    name =
      service.name || `${(service.protocol || "TCP").toUpperCase()} Service`;
  }

  form.name = `${name} (${service.port})`;

  // Store selected service info for display
  selectedServiceInfo.value = {
    ...service,
    displayName: name,
  };

  showServiceModal.value = false;
};

const testingPort = ref(false);
const portTestResult = ref(null);

const testPort = async () => {
  if (!selectedServer.value || !selectedServer.value.is_reachable) {
    toast.error("Server is not connected");
    return;
  }

  if (!form.port) {
    toast.error("Please enter a port number");
    return;
  }

  testingPort.value = true;
  portTestResult.value = null;

  try {
    const result = await api.post(
      `/servers/${selectedServer.value.id}/test-port`,
      {
        port: form.port,
        protocol: form.protocol,
      }
    );

    portTestResult.value = {
      success: result.success,
      message:
        result.message ||
        (result.success ? "Port is accessible" : "Port is not accessible"),
    };

    if (result.success) {
      toast.success("Port test successful");
    } else {
      toast.warning("Port test failed");
    }
  } catch (e) {
    portTestResult.value = {
      success: false,
      message: e.message || "Error testing port",
    };
    toast.error("Error testing port: " + e.message);
  } finally {
    testingPort.value = false;
  }
};

const createService = async () => {
  loading.value = true;
  try {
    // Validate server_id is required
    if (!form.server_id) {
      throw new Error("Please select a server");
    }

    if (!enablePassword.value) {
      form.tunnel_password = null;
    }

    const serviceData = { ...form };

    if (serviceData.provider_key === "cloudflare_quick") {
      serviceData.provider_key = "cloudflare";
      serviceData.is_quick_service = true;
      serviceData.domain = null;
      serviceData.subdomain = null;
      serviceData.dns_provider_key = null;
    }

    if (showDNSConfig.value) {
      if (!serviceData.domain || !serviceData.subdomain) {
        throw new Error("Domain and Subdomain are required for Named Tunnels");
      }
    }

    await api.post("/services", serviceData);
    toast.success("Service created successfully");
    emit("created");
    emit("close");

    // Reset minimal state
    form.name = "";
    form.port = 8080;
    inputMethod.value = "manual";
  } catch (e) {
    toast.error("Error creating service: " + e.message);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <BaseModal
    :isOpen="isOpen"
    :title="showServiceModal ? 'Select Service' : 'Create Service'"
    :icon="showServiceModal ? icons.IconList : icons.IconPlus"
    maxWidth="sm:max-w-3xl"
    @close="$emit('close')"
  >
    <!-- Service Selection View -->
    <div v-if="showServiceModal" class="space-y-4">
      <div
        class="border rounded-lg overflow-hidden border-gray-200 dark:border-gray-700 overflow-y-auto max-h-[60vh]"
      >
        <table
          class="min-w-full divide-y divide-gray-200 dark:divide-gray-700 relative"
        >
          <thead class="bg-gray-50 dark:bg-gray-800 sticky top-0 z-10">
            <tr>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400"
              >
                Service
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400"
              >
                Port
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400"
              >
                Protocol
              </th>
              <th
                scope="col"
                class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400"
              >
                Action
              </th>
            </tr>
          </thead>
          <tbody
            class="bg-white divide-y divide-gray-200 dark:bg-gray-900 dark:divide-gray-700"
          >
            <template v-if="discoveredServices.length > 0">
              <tr
                v-for="(service, index) in discoveredServices"
                :key="`${service.port}-${service.protocol}`"
                @click="selectDiscoveredService(service)"
                class="hover:bg-gray-50 dark:hover:bg-gray-800/50  cursor-pointer"
              >
                <td
                  class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100"
                >
                  <div class="flex flex-col gap-0.5">
                    <div class="flex items-center gap-2">
                      <span>{{
                        service.service !== "Unknown"
                          ? service.service
                          : service.name || "Unknown"
                      }}</span>
                    </div>
                    <div
                      class="flex items-center gap-3 text-xs font-normal text-gray-500 dark:text-gray-400"
                    >
                      <span
                        v-if="service.process"
                        class="flex items-center gap-1"
                        title="Process"
                      >
                        <icons.IconCpu class="size-3" />
                        {{ service.process.name }} ({{ service.process.pid }})
                      </span>
                      <span
                        v-if="service.docker"
                        class="flex items-center gap-1 text-blue-600 dark:text-blue-400"
                        title="Docker Container"
                      >
                        <icons.IconBrandDocker class="size-3" />
                        {{ service.docker.name }}
                      </span>
                    </div>
                  </div>
                </td>
                <td
                  class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 font-mono"
                >
                  {{ service.port }}
                </td>
                <td
                  class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 uppercase"
                >
                  {{ service.protocol || "tcp" }}
                </td>
                <td
                  class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium"
                >
                  <button
                    type="button"
                    @click="selectDiscoveredService(service)"
                    class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                  >
                    Select
                  </button>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td
                colspan="4"
                class="px-6 py-8 text-center text-sm text-gray-500 dark:text-gray-400"
              >
                <div class="flex flex-col items-center justify-center gap-2">
                  <icons.IconSearch class="size-8 opacity-50" />
                  <p>No services discovered.</p>
                  <p class="text-xs">
                    Click "Scan Now" to discover running services.
                  </p>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Form View -->
    <form v-else @submit.prevent="createService" class="space-y-6">
      <!-- Service Name (Top, Half Width) -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label
            class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
            >Service Name</label
          >
          <input
            v-model="form.name"
            type="text"
            required
            placeholder="e.g., My Web App"
            class="py-2 px-3 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-800 dark:border-gray-700 dark:text-gray-400"
          />
        </div>
      </div>

      <!-- Section: Origin -->
      <div class="space-y-4">
        <h3
          class="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-2 border-b border-gray-200 dark:border-gray-700 pb-2"
        >
          Origin Configuration
        </h3>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Server Selection (Rich Dropdown) -->
          <div class="relative">
            <label
              class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
              >Server</label
            >
            <button
              type="button"
              class="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left border border-gray-200 shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-slate-800 dark:border-gray-700"
              @click="showServerDropdown = !showServerDropdown"
            >
              <span class="block truncate">
                <span v-if="!form.server_id" class="text-gray-500"
                  >Select a server...</span
                >
                <span v-else class="flex flex-col text-left">
                  <span class="font-medium text-gray-900 dark:text-gray-100">
                    {{ selectedServer?.name }}
                    {{ selectedServer?.is_local ? "(Local)" : "" }}
                  </span>
                  <span
                    class="text-xs text-gray-500 truncate dark:text-gray-400"
                  >
                    {{
                      selectedServer?.is_local
                        ? selectedServer?.host
                        : selectedServer?.network_ip || "No IP"
                    }}
                  </span>
                </span>
              </span>
              <span
                class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2"
              >
                <icons.IconChevronDown
                  class="h-5 w-5 text-gray-400"
                  aria-hidden="true"
                />
              </span>
            </button>

            <ul
              v-if="showServerDropdown"
              class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-gray-200 dark:ring-gray-700 focus:outline-none sm:text-sm dark:bg-slate-800"
            >
              <li
                v-for="server in servers"
                :key="server.id"
                class="relative cursor-default select-none py-2 pl-3 pr-9 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                :class="
                  form.server_id === server.id
                    ? 'bg-blue-50 dark:bg-blue-900/20'
                    : 'text-gray-900 dark:text-gray-100'
                "
                @click="
                  form.server_id = server.id;
                  showServerDropdown = false;
                "
              >
                <div class="flex flex-col">
                  <span
                    class="font-medium block truncate"
                    :class="
                      form.server_id === server.id
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-900 dark:text-white'
                    "
                  >
                    {{ server.name }} {{ server.is_local ? "(Local)" : "" }}
                  </span>
                  <span
                    class="text-xs text-gray-500 truncate dark:text-gray-400"
                  >
                    {{
                      server.is_local
                        ? server.host
                        : server.network_ip || "No IP"
                    }}
                  </span>
                </div>

                <span
                  v-if="form.server_id === server.id"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600 dark:text-blue-400"
                >
                  <icons.IconCheck class="h-5 w-5" aria-hidden="true" />
                </span>
              </li>
            </ul>
          </div>

          <!-- Service Method Selection (Rich Dropdown) -->
          <div class="relative">
            <label
              class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
              >Input Method</label
            >
            <button
              type="button"
              class="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left border border-gray-200 shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-slate-800 dark:border-gray-700"
              :disabled="
                !selectedServer || selectedServer.agent_status !== 'connected'
              "
              @click="showMethodDropdown = !showMethodDropdown"
            >
              <span class="block text-left">
                <template v-if="!selectedServer">
                  <div class="flex items-center gap-2 text-gray-400">
                    <icons.IconEdit class="size-4" />
                    <span class="font-medium">Select a server first</span>
                  </div>
                </template>
                <template
                  v-else-if="selectedServer.agent_status !== 'connected'"
                >
                  <div class="flex items-center gap-2 text-gray-400">
                    <icons.IconEdit class="size-4" />
                    <span class="font-medium">Manual Entry</span>
                  </div>
                </template>
                <template v-else-if="inputMethod === 'manual'">
                  <div class="flex items-center gap-2">
                    <icons.IconEdit class="size-4 text-blue-500" />
                    <div class="flex flex-col">
                      <span class="font-medium text-gray-900 dark:text-gray-100"
                        >Manual Entry</span
                      >
                      <span class="text-xs text-gray-500"
                        >Enter details manually</span
                      >
                    </div>
                  </div>
                </template>
                <template v-else>
                  <div class="flex items-center gap-2">
                    <icons.IconList class="size-4 text-blue-500" />
                    <div class="flex flex-col">
                      <span class="font-medium text-gray-900 dark:text-gray-100"
                        >Select Service</span
                      >
                      <span class="text-xs text-gray-500"
                        >Pick from running services</span
                      >
                    </div>
                  </div>
                </template>
              </span>
              <span
                class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2"
              >
                <icons.IconChevronDown
                  class="h-5 w-5 text-gray-400"
                  aria-hidden="true"
                />
              </span>
            </button>

            <!-- Dropdown Menu -->
            <ul
              v-if="
                showMethodDropdown &&
                selectedServer &&
                selectedServer.agent_status === 'connected'
              "
              class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-gray-200 dark:ring-gray-700 focus:outline-none sm:text-sm dark:bg-slate-800"
            >
              <!-- Option: Manual Entry -->
              <li
                class="relative cursor-default select-none py-2 pl-3 pr-9 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                :class="
                  inputMethod === 'manual'
                    ? 'bg-blue-50 dark:bg-blue-900/20'
                    : 'text-gray-900 dark:text-gray-100'
                "
                @click="
                  inputMethod = 'manual';
                  showMethodDropdown = false;
                "
              >
                <div class="flex items-center gap-2">
                  <icons.IconEdit
                    class="size-4"
                    :class="
                      inputMethod === 'manual'
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-500'
                    "
                  />
                  <div class="flex flex-col">
                    <span
                      class="font-medium block"
                      :class="
                        inputMethod === 'manual'
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-gray-900 dark:text-white'
                      "
                    >
                      Manual Entry
                    </span>
                    <span class="text-xs text-gray-500 dark:text-gray-400">
                      Enter details manually
                    </span>
                  </div>
                </div>
                <span
                  v-if="inputMethod === 'manual'"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600 dark:text-blue-400"
                >
                  <icons.IconCheck class="h-5 w-5" aria-hidden="true" />
                </span>
              </li>

              <!-- Option: Select Service -->
              <li
                class="relative cursor-default select-none py-2 pl-3 pr-9 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                :class="
                  inputMethod === 'select'
                    ? 'bg-blue-50 dark:bg-blue-900/20'
                    : 'text-gray-900 dark:text-gray-100'
                "
                @click="
                  inputMethod = 'select';
                  showMethodDropdown = false;
                "
              >
                <div class="flex items-center gap-2">
                  <icons.IconList
                    class="size-4"
                    :class="
                      inputMethod === 'select'
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-500'
                    "
                  />
                  <div class="flex flex-col">
                    <span
                      class="font-medium block"
                      :class="
                        inputMethod === 'select'
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-gray-900 dark:text-white'
                      "
                    >
                      Select Service
                    </span>
                    <span class="text-xs text-gray-500 dark:text-gray-400">
                      Pick from running services
                    </span>
                  </div>
                </div>
                <span
                  v-if="inputMethod === 'select'"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600 dark:text-blue-400"
                >
                  <icons.IconCheck class="h-5 w-5" aria-hidden="true" />
                </span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Service Details -->
        <div class="space-y-4">
          <!-- Select Service Card (when inputMethod is 'select') -->
          <div
            v-if="
              selectedServer &&
              selectedServer.agent_status === 'connected' &&
              inputMethod === 'select'
            "
          >
            <!-- Search Card (if no service selected) -->
            <div v-if="!selectedServiceInfo">
              <button
                type="button"
                @click="
                  () => {
                    showServiceModal = true;
                    refreshServices();
                  }
                "
                class="w-full py-4 px-4 flex justify-center items-center gap-2 rounded-lg border-2 border-dashed border-gray-300 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-all text-gray-500 font-medium dark:border-gray-600 dark:hover:border-blue-400 dark:hover:text-blue-400 dark:hover:bg-blue-900/10"
              >
                <icons.IconSearch class="size-5" />
                Select a Service from {{ selectedServer.name }}
              </button>
            </div>

            <!-- Selected Service Card -->
            <div
              v-else
              class="border rounded-lg p-4 bg-white dark:bg-slate-800 border-gray-200 dark:border-gray-700"
            >
              <div class="flex items-center justify-between">
                <div class="flex flex-col gap-2 flex-1">
                  <div class="flex items-center gap-3">
                    <span
                      class="font-mono font-bold text-xl text-gray-900 dark:text-white"
                      >{{ selectedServiceInfo.port }}</span
                    >
                    <span
                      class="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 uppercase tracking-wider font-semibold"
                    >
                      {{ selectedServiceInfo.protocol }}
                    </span>
                  </div>
                  <div
                    class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400"
                  >
                    <span
                      v-if="selectedServiceInfo.process"
                      class="flex items-center gap-1"
                    >
                      <icons.IconCpu class="size-3" />
                      {{ selectedServiceInfo.process.name }} ({{
                        selectedServiceInfo.process.pid
                      }})
                    </span>
                    <span
                      v-if="selectedServiceInfo.docker"
                      class="flex items-center gap-1 text-blue-600 dark:text-blue-400"
                    >
                      <icons.IconBrandDocker class="size-3" />
                      {{ selectedServiceInfo.docker.name }}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  @click="
                    selectedServiceInfo = null;
                    showServiceModal = true;
                    refreshServices();
                  "
                  class="px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 "
                >
                  Replace
                </button>
              </div>
            </div>
          </div>

          <!-- Manual Inputs (only shown when inputMethod is 'manual') -->
          <div
            v-if="
              !selectedServer ||
              selectedServer.agent_status !== 'connected' ||
              inputMethod === 'manual'
            "
            class="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            <div>
              <div class="flex items-center justify-between mb-1">
                <label
                  class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >Port</label
                >
                <button
                  v-if="
                    selectedServer && selectedServer.is_reachable && form.port
                  "
                  type="button"
                  @click="testPort"
                  :disabled="testingPort"
                  class="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50"
                >
                  <icons.IconPlugConnected v-if="!testingPort" class="size-3" />
                  <icons.IconLoader2 v-else class="animate-spin size-3" />
                  Test
                </button>
              </div>
              <input
                v-model.number="form.port"
                type="number"
                required
                placeholder="8080"
                class="py-2 px-3 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-800 dark:border-gray-700 dark:text-gray-400"
              />
              <p
                v-if="portTestResult"
                :class="[
                  portTestResult.success
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400',
                  'text-xs mt-1',
                ]"
              >
                <icons.IconCheck
                  v-if="portTestResult.success"
                  class="inline size-3"
                />
                <icons.IconX v-else class="inline size-3" />
                {{ portTestResult.message }}
              </p>
            </div>
            <div>
              <label
                class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
                >Protocol</label
              >
              <select
                v-model="form.protocol"
                class="py-2 px-3 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-800 dark:border-gray-700 dark:text-gray-400"
              >
                <option value="http">HTTP</option>
                <option value="tcp">TCP</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Section: Tunnel -->
      <div class="space-y-4">
        <h3
          class="text-sm uppercase tracking-wider text-gray-500 font-semibold mb-2 border-b border-gray-200 dark:border-gray-700 pb-2"
        >
          Tunnel Configuration
        </h3>

        <!-- Provider Selection (Rich Select) -->
        <div>
          <label
            class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
            >Provider</label
          >
          <div class="relative">
            <button
              type="button"
              class="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left border border-gray-200 shadow-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm dark:bg-slate-800 dark:border-gray-700"
              @click="showProviderDropdown = !showProviderDropdown"
            >
              <span class="block truncate">
                <span v-if="!form.provider_key" class="text-gray-500"
                  >Select a provider...</span
                >
                <span
                  v-else
                  class="font-medium text-gray-900 dark:text-gray-100"
                >
                  {{
                    providerOptions.find((o) => o.value === form.provider_key)
                      ?.label
                  }}
                  <span class="font-normal text-gray-500"
                    >-
                    {{
                      providerOptions.find((o) => o.value === form.provider_key)
                        ?.description
                    }}</span
                  >
                </span>
              </span>
              <span
                class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2"
              >
                <icons.IconChevronDown
                  class="h-5 w-5 text-gray-400"
                  aria-hidden="true"
                />
              </span>
            </button>

            <ul
              v-if="showProviderDropdown"
              class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-gray-200 dark:ring-gray-700 focus:outline-none sm:text-sm dark:bg-slate-800"
            >
              <li
                v-for="option in providerOptions"
                :key="option.value"
                class="relative cursor-default select-none py-2 pl-3 pr-9 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                :class="
                  form.provider_key === option.value
                    ? 'bg-blue-50 dark:bg-blue-900/20'
                    : 'text-gray-900 dark:text-gray-100'
                "
                @click="
                  form.provider_key = option.value;
                  showProviderDropdown = false;
                "
              >
                <div class="flex flex-col">
                  <span
                    class="font-medium block truncate"
                    :class="
                      form.provider_key === option.value
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-900 dark:text-white'
                    "
                  >
                    {{ option.label }}
                  </span>
                  <span
                    class="text-xs text-gray-500 truncate dark:text-gray-400"
                  >
                    {{ option.description }}
                  </span>
                </div>

                <span
                  v-if="form.provider_key === option.value"
                  class="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600 dark:text-blue-400"
                >
                  <icons.IconCheck class="h-5 w-5" aria-hidden="true" />
                </span>
              </li>
            </ul>
          </div>
        </div>

        <!-- DNS Configuration (Conditional) -->
        <div
          v-if="showDNSConfig"
          class="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-gray-700 space-y-4"
        >
          <div class="flex items-center gap-2 mb-2">
            <icons.IconWorld class="size-4 text-blue-500" />
            <h4 class="font-medium text-sm text-gray-900 dark:text-white">
              Custom Domain Configuration
            </h4>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Domain Select -->
            <div>
              <label
                class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
                >Domain Zone</label
              >
              <select
                v-model="form.domain"
                :disabled="loadingDomains"
                class="py-2 px-3 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-900 dark:border-gray-700 dark:text-gray-400 disabled:opacity-50"
              >
                <option value="">Select a domain...</option>
                <option v-for="d in domains" :key="d.id" :value="d.domain">
                  {{ d.domain }}
                </option>
              </select>
              <p v-if="loadingDomains" class="text-xs text-gray-500 mt-1">
                Loading domains...
              </p>
              <p
                v-else-if="domains.length === 0"
                class="text-xs text-amber-600 mt-1"
              >
                No domains found for this provider.
              </p>
            </div>

            <!-- Subdomain Input -->
            <div>
              <label
                class="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
                >Subdomain</label
              >
              <div class="flex rounded-md shadow-sm">
                <input
                  v-model="form.subdomain"
                  type="text"
                  placeholder="app"
                  class="py-2 px-3 block w-full min-w-0 flex-1 border-gray-200 rounded-l-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-900 dark:border-gray-700 dark:text-gray-400"
                />
                <span
                  class="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-200 bg-gray-50 text-gray-500 text-sm dark:bg-slate-800 dark:border-gray-700 dark:text-gray-400"
                >
                  .{{ form.domain || "example.com" }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Analytics Configuration -->
        <div
          v-if="selectedServer"
          class="pt-4 mt-4 border-t border-gray-200 dark:border-gray-700"
        >
          <div class="flex items-center justify-between">
            <div>
              <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >Traffic Analytics</label
              >
              <p class="text-xs text-gray-500">
                Monitor traffic through your tunnel
              </p>
            </div>
            <div class="flex items-center gap-2">
              <span
                v-if="selectedServer.agent_status === 'connected'"
                class="text-xs text-green-600 bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded-full"
              >
                Agent Connected
              </span>
              <span
                v-else
                class="text-xs text-amber-600 bg-amber-50 dark:bg-amber-900/20 px-2 py-0.5 rounded-full"
              >
                Agent Disconnected
              </span>
              <label class="inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  v-model="enableAnalytics"
                  class="sr-only peer"
                />
                <div
                  class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"
                ></div>
              </label>
            </div>
          </div>
        </div>

        <!-- Password Protection -->
        <div class="pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="flex items-center justify-between">
            <div>
              <label
                class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >Password Protection</label
              >
              <p class="text-xs text-gray-500">
                Restrict access to your tunnel
              </p>
            </div>
            <button
              type="button"
              @click="enablePassword = !enablePassword"
              :class="[
                enablePassword ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700',
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent  duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 dark:focus:ring-offset-slate-900',
              ]"
            >
              <span
                :class="[
                  enablePassword ? 'translate-x-5' : 'translate-x-0',
                  'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
                ]"
              ></span>
            </button>
          </div>
          <div v-if="enablePassword" class="mt-3">
            <input
              v-model="form.tunnel_password"
              type="text"
              placeholder="Enter tunnel password"
              class="py-2 px-3 block w-full border-gray-200 rounded-lg text-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-slate-800 dark:border-gray-700 dark:text-gray-400"
            />
          </div>
        </div>
      </div>

      <!-- Form Actions -->
      <div
        class="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700"
      >
        <button
          type="button"
          @click="$emit('close')"
          class="py-2 px-4 inline-flex justify-center items-center gap-2 rounded-lg border border-gray-200 font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white focus:ring-blue-600 transition-all text-sm dark:border-gray-700 dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="loading"
          class="py-2 px-4 inline-flex justify-center items-center gap-2 rounded-lg border border-transparent font-semibold bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all text-sm disabled:opacity-50 disabled:pointer-events-none"
        >
          <icons.IconLoader2 v-if="loading" class="animate-spin size-4" />
          {{ loading ? "Creating..." : "Create Service" }}
        </button>
      </div>
    </form>

    <!-- Footer for Service Selection View -->
    <template v-if="showServiceModal" #footer>
      <div class="flex gap-3 justify-end w-full">
        <button
          @click="showServiceModal = false"
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700"
        >
          Back
        </button>
        <button
          type="button"
          @click="refreshServices"
          :disabled="refreshingServices"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <icons.IconRefresh v-if="!refreshingServices" class="w-4 h-4" />
          <icons.IconLoader2 v-else class="w-4 h-4 animate-spin" />
          {{ refreshingServices ? "Scanning..." : "Scan Now" }}
        </button>
      </div>
    </template>
  </BaseModal>
</template>
