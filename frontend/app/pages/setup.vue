<script setup>
definePageMeta({
  layout: false,
});

const setupStore = useSetupStore();
const isDark = useState("isDark", () => false);

const initialPassword = ref("");
const passwordVerified = ref(false);
const loading = ref(false);
const error = ref("");
const copied = ref(false);
const logsCopied = ref(false);
const agentInstallCommand = ref("");
const systemInfo = ref(null);
const agentConnected = ref(false);
const hostInfo = ref(null);
const apiConnected = ref(true); // Assume connected initially
const checkingConnection = ref(false);
let pollingInterval = null;

const formData = ref({
  newPassword: "",
  confirmPassword: "",
  serverName: "HomeServerPrincipal",
});

const passwordChecks = computed(() => {
  const password = formData.value.newPassword;
  return {
    minLength: password.length >= 8,
    passwordsMatch:
      password &&
      formData.value.confirmPassword &&
      password === formData.value.confirmPassword,
  };
});

const isPasswordValid = computed(() => {
  const checks = passwordChecks.value;
  return checks.minLength && checks.passwordsMatch;
});

const canSubmit = computed(() => {
  return (
    passwordVerified.value && isPasswordValid.value && formData.value.serverName
  );
});

const formatBytes = (bytes) => {
  if (!bytes) return "N/A";
  const gb = bytes / 1024 ** 3;
  return `${gb.toFixed(1)} GB`;
};

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (import.meta.client) {
    document.documentElement.classList.toggle("dark", isDark.value);
  }
};

const checkApiConnection = async () => {
  checkingConnection.value = true;
  error.value = "";

  try {
    const config = useRuntimeConfig();
    const response = await fetch("/api/health", {
      signal: AbortSignal.timeout(5000), // 5 second timeout
      headers: {
        Accept: "application/json",
      },
    });

    if (response.ok) {
      apiConnected.value = true;
      // Try to load system info if connection is successful
      if (!systemInfo.value) {
        await loadSystemInfo();
      }
    } else {
      throw new Error(`API server returned status: ${response.status}`);
    }
  } catch (err) {
    console.error("API connection check failed:", err);
    apiConnected.value = false;
    error.value = `Cannot connect to API server: ${err.message}`;
  } finally {
    checkingConnection.value = false;
  }
};

const verifyPassword = async () => {
  loading.value = true;
  error.value = "";

  try {
    const result = await setupStore.verifyInitialPassword(
      initialPassword.value
    );

    if (result.valid) {
      passwordVerified.value = true;
      apiConnected.value = true; // Mark API as connected on successful verification
      await loadSystemInfo();
    } else {
      error.value = result.message || "Invalid password";
    }
  } catch (err) {
    // Check if it's a network error
    if (
      err.message.includes("fetch") ||
      err.message.includes("Failed to fetch")
    ) {
      apiConnected.value = false;
      error.value =
        "Cannot connect to API server. Please check if the server is running.";
    } else {
      error.value = "Failed to verify password. Please try again.";
    }
  } finally {
    loading.value = false;
  }
};

const loadSystemInfo = async () => {
  try {
    const info = await setupStore.getSystemInfo();
    if (info) {
      systemInfo.value = info;

      // Get install command for detected OS
      const script = await setupStore.getAgentInstallScript();
      if (script) {
        agentInstallCommand.value = script;
      }

      // Always start polling for agent status (regardless of OS)
      startAgentPolling();
    }
  } catch (err) {
    console.error("Error loading system info:", err);
  }
};

const checkAgentStatus = async () => {
  try {
    const response = await fetch("/api/setup/agent-status");
    const data = await response.json();

    // Update connection state
    const wasConnected = agentConnected.value;
    agentConnected.value = data.agent_installed;

    // If just connected, fetch host info
    if (data.agent_installed && !wasConnected) {
      await getHostInfo();
    }

    // If disconnected, clear host info
    if (!data.agent_installed && wasConnected) {
      hostInfo.value = null;
    }
  } catch (err) {
    console.error("Error checking agent status:", err);
    agentConnected.value = false;
    hostInfo.value = null;
  }
};

const getHostInfo = async () => {
  try {
    const config = useRuntimeConfig();
    const response = await fetch("/api/setup/agent-host-info");
    const data = await response.json();

    if (!data.error) {
      hostInfo.value = data;
    }
  } catch (err) {
    console.error("Error getting host info:", err);
  }
};

const startAgentPolling = () => {
  if (pollingInterval) return;

  // Check immediately
  checkAgentStatus();

  // Then check every 2 seconds (continuous polling)
  pollingInterval = setInterval(() => {
    checkAgentStatus();
  }, 2000);
};

const stopAgentPolling = () => {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
};

const copyInstallCommand = async () => {
  if (import.meta.client && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(agentInstallCommand.value);
      copied.value = true;
      setTimeout(() => {
        copied.value = false;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }
};

// Computed command based on detected OS
const logsCommand = computed(() => {
  const platform = systemInfo.value?.platform?.toLowerCase() || "";
  const isWindows = platform.includes("win") || platform === "windows";

  if (isWindows) {
    // PowerShell command - show full log line with password (last occurrence)
    return '(docker logs (docker ps -q -f label=localrun-app) 2>&1 | Select-String "Initial Setup Password:" | Select-Object -Last 1).Line';
  } else {
    // Unix/Linux/macOS - show full log line with password (last occurrence)
    return 'docker logs $(docker ps -q -f label=localrun-app) 2>&1 | grep "Initial Setup Password:" | tail -1';
  }
});

const copyLogsCommand = async () => {
  if (import.meta.client && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(logsCommand.value);
      logsCopied.value = true;
      setTimeout(() => {
        logsCopied.value = false;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }
};

const handleSubmit = async () => {
  console.log("handleSubmit called");
  console.log("canSubmit:", canSubmit.value);

  if (!canSubmit.value) {
    console.log("Submit blocked - canSubmit is false");
    return;
  }

  loading.value = true;
  error.value = "";
  console.log("Starting setup submission...");

  try {
    const setupData = {
      initial_password: initialPassword.value,
      new_password: formData.value.newPassword,
      new_password_confirmation: formData.value.confirmPassword,
      installation_name: formData.value.serverName,
    };

    console.log("Setup data:", {
      ...setupData,
      initial_password: "***",
      new_password: "***",
      new_password_confirmation: "***",
    });

    const result = await setupStore.completeSetup(setupData);
    console.log("Setup completed successfully:", result);

    // Update setup status in store
    console.log("Updating setup status...");
    await setupStore.checkSetupStatus();
    console.log("Setup status updated");

    // Force navigation to login
    console.log("Navigating to login...");
    if (import.meta.client) {
      console.log("Using window.location.href");
      window.location.href = "/login";
    } else {
      console.log("Using navigateTo");
      await navigateTo("/login", { replace: true });
    }
  } catch (err) {
    console.error("Setup error:", err);
    error.value = err.message || "Setup failed. Please try again.";
  } finally {
    loading.value = false;
    console.log("handleSubmit finished");
  }
};

onMounted(async () => {
  if (import.meta.client) {
    isDark.value = document.documentElement.classList.contains("dark");

    // Check if setup is already completed
    try {
      const response = await fetch("/api/setup/status");
      if (response.ok) {
        const data = await response.json();
        if (data.setup_completed) {
          // Setup already completed, redirect to login
          console.log("Setup already completed, redirecting to login...");
          window.location.href = "/login";
          return;
        }
      }
    } catch (err) {
      console.error("Error checking setup status:", err);
    }

    // Check API connection
    checkApiConnection();
  }
});

onBeforeUnmount(() => {
  stopAgentPolling();
});
</script>
<template>
  <div
    class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4"
  >
    <!-- Setup Container -->
    <div class="w-full max-w-2xl">
      <!-- Logo -->
      <div class="text-center mb-8">
        <ClientOnly>
          <template #fallback>
            <img src="/dark.png" alt="LocalRun" class="h-12 mx-auto mb-4" />
          </template>
          <img
            :src="isDark ? '/white.png' : '/dark.png'"
            alt="LocalRun"
            class="h-12 mx-auto mb-4"
          />
        </ClientOnly>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Initial Setup
        </h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">
          Configure your LocalRun server
        </p>

        <!-- System Info -->
        <div
          v-if="systemInfo"
          class="mt-4 inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-700 dark:text-gray-300"
        >
          <i class="ti ti-device-desktop text-sm"></i>
          <span>{{ systemInfo.os_name || systemInfo.platform }}</span>
          <span
            v-if="systemInfo.architecture"
            class="text-gray-400 dark:text-gray-600"
            >•</span
          >
          <span v-if="systemInfo.architecture">{{
            systemInfo.architecture
          }}</span>
          <span
            v-if="systemInfo.in_docker"
            class="text-gray-400 dark:text-gray-600"
            >•</span
          >
          <span
            v-if="systemInfo.in_docker"
            class="text-blue-600 dark:text-blue-400"
            >Docker</span
          >
        </div>
      </div>

      <!-- API Connection Status -->
      <div
        v-if="!apiConnected && !loading"
        class="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
      >
        <div class="flex items-start gap-3">
          <i
            class="ti ti-exclamation-triangle text-yellow-600 dark:text-yellow-400 text-lg flex-shrink-0 mt-0.5"
          ></i>
          <div>
            <h3
              class="text-sm font-semibold text-yellow-800 dark:text-yellow-300 mb-1"
            >
              Cannot Connect to API Server
            </h3>
            <p class="text-xs text-yellow-700 dark:text-yellow-400 mb-2">
              The LocalRun API server is not accessible. Please ensure the
              server is running.
            </p>
            <button
              @click="checkApiConnection"
              :disabled="checkingConnection"
              class="inline-flex items-center gap-1 px-2 py-1 bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white text-xs font-medium rounded  disabled:cursor-not-allowed"
            >
              <i
                v-if="checkingConnection"
                class="ti ti-loader-2 animate-spin"
              ></i>
              <i v-else class="ti ti-refresh"></i>
              {{ checkingConnection ? "Checking..." : "Retry Connection" }}
            </button>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="error"
        class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
      >
        <p class="text-sm text-red-800 dark:text-red-300">{{ error }}</p>
      </div>

      <!-- Unified Form Card -->
      <div
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <form
          @submit.prevent="handleSubmit"
          class="divide-y divide-gray-200 dark:divide-gray-700"
        >
          <!-- Section 1: Initial Password -->
          <div class="p-6">
            <h2
              class="text-sm font-semibold text-gray-900 dark:text-white mb-4"
            >
              1. Initial Password
            </h2>
            <p class="text-xs text-gray-600 dark:text-gray-400 mb-3">
              Enter the password from your Docker logs
            </p>

            <!-- Docker logs command -->
            <div class="relative group mb-4">
              <div
                class="bg-gray-900 dark:bg-black rounded-lg p-4 overflow-x-auto"
              >
                <code
                  class="text-sm text-green-400 whitespace-pre-wrap block"
                  >{{ logsCommand }}</code
                >
              </div>
              <button
                @click="copyLogsCommand"
                class="absolute top-2 right-2 p-2 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white  opacity-0 group-hover:opacity-100"
                :title="logsCopied ? 'Copied!' : 'Copy command'"
              >
                <i v-if="logsCopied" class="ti ti-check text-sm"></i>
                <i v-else class="ti ti-copy text-sm"></i>
              </button>
            </div>

            <div class="flex gap-2">
              <input
                v-model="initialPassword"
                type="password"
                required
                :disabled="passwordVerified || !apiConnected"
                class="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                placeholder="Initial password"
              />
              <button
                v-if="!passwordVerified"
                type="button"
                @click="verifyPassword"
                :disabled="loading || !initialPassword || !apiConnected"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-all disabled:cursor-not-allowed text-sm"
              >
                {{ loading ? "..." : "Verify" }}
              </button>
              <div v-else class="flex items-center px-3">
                <i
                  class="ti ti-check text-green-600 dark:text-green-400 text-xl"
                ></i>
              </div>
            </div>
          </div>

          <!-- Section 2: New Password -->
          <div class="p-6" :class="{ 'opacity-50': !passwordVerified }">
            <h2
              class="text-sm font-semibold text-gray-900 dark:text-white mb-4"
            >
              2. New Password
            </h2>

            <!-- Password inputs in horizontal layout -->
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label
                  class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2"
                  >New Password</label
                >
                <input
                  v-model="formData.newPassword"
                  type="password"
                  required
                  :disabled="!passwordVerified"
                  class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:cursor-not-allowed"
                  placeholder="Enter new password"
                />
              </div>
              <div>
                <label
                  class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2"
                  >Confirm Password</label
                >
                <input
                  v-model="formData.confirmPassword"
                  type="password"
                  required
                  :disabled="!passwordVerified"
                  class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:cursor-not-allowed"
                  placeholder="Confirm password"
                />
              </div>
            </div>

            <!-- Security Requirements -->
            <div v-if="formData.newPassword" class="space-y-2">
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-2">
                  <i
                    v-if="passwordChecks.minLength"
                    class="ti ti-circle-check text-green-600 dark:text-green-400 text-sm"
                  ></i>
                  <i
                    v-else
                    class="ti ti-circle-x text-gray-400 dark:text-gray-600 text-sm"
                  ></i>
                  <span
                    class="text-xs"
                    :class="
                      passwordChecks.minLength
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-gray-600 dark:text-gray-400'
                    "
                  >
                    At least 8 characters
                  </span>
                </div>
                <div
                  v-if="formData.confirmPassword"
                  class="flex items-center gap-2"
                >
                  <i
                    v-if="passwordChecks.passwordsMatch"
                    class="ti ti-circle-check text-green-600 dark:text-green-400 text-sm"
                  ></i>
                  <i
                    v-else
                    class="ti ti-circle-x text-red-600 dark:text-red-400 text-sm"
                  ></i>
                  <span
                    class="text-xs"
                    :class="
                      passwordChecks.passwordsMatch
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    "
                  >
                    Passwords match
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Section 3: Server Configuration -->
          <div class="p-6" :class="{ 'opacity-50': !passwordVerified }">
            <h2
              class="text-sm font-semibold text-gray-900 dark:text-white mb-4"
            >
              3. Server Configuration
            </h2>

            <!-- Server Name Input -->
            <div class="mb-4">
              <label
                class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2"
                >Server Name</label
              >
              <input
                v-model="formData.serverName"
                type="text"
                required
                :disabled="!passwordVerified"
                class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:cursor-not-allowed"
                placeholder="HomeServerPrincipal"
              />
            </div>

            <!-- CLI Agent Install/Status -->
            <div
              v-if="agentInstallCommand"
              class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <i
                    class="ti ti-terminal-2 text-blue-600 dark:text-blue-400 text-lg"
                  ></i>
                  <h3
                    class="text-xs font-semibold text-gray-900 dark:text-white"
                  >
                    CLI Agent
                  </h3>
                </div>
                <!-- Connection Status -->
                <div class="flex items-center gap-2">
                  <div
                    v-if="agentConnected"
                    class="flex items-center gap-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 rounded-full"
                  >
                    <i
                      class="ti ti-circle-check-filled text-green-600 dark:text-green-400 text-sm"
                    ></i>
                    <span
                      class="text-xs font-medium text-green-700 dark:text-green-300"
                      >Connected</span
                    >
                  </div>
                  <div
                    v-else-if="checkingAgent"
                    class="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full"
                  >
                    <i
                      class="ti ti-loader-2 text-gray-600 dark:text-gray-400 text-sm animate-spin"
                    ></i>
                    <span
                      class="text-xs font-medium text-gray-600 dark:text-gray-400"
                      >Checking...</span
                    >
                  </div>
                  <div
                    v-else
                    class="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full"
                  >
                    <i
                      class="ti ti-circle-x text-gray-600 dark:text-gray-400 text-sm"
                    ></i>
                    <span
                      class="text-xs font-medium text-gray-600 dark:text-gray-400"
                      >Not connected</span
                    >
                  </div>
                </div>
              </div>

              <!-- Host Info (when connected) -->
              <div
                v-if="agentConnected && hostInfo"
                class="mb-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <p
                  class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Host Information:
                </p>
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span class="text-gray-600 dark:text-gray-400"
                      >Hostname:</span
                    >
                    <span
                      class="ml-1 font-medium text-gray-900 dark:text-white"
                      >{{ hostInfo.hostname }}</span
                    >
                  </div>
                  <div>
                    <span class="text-gray-600 dark:text-gray-400"
                      >Platform:</span
                    >
                    <span class="ml-1 font-medium text-gray-900 dark:text-white"
                      >{{ hostInfo.platform }} ({{ hostInfo.arch }})</span
                    >
                  </div>
                  <div>
                    <span class="text-gray-600 dark:text-gray-400">CPUs:</span>
                    <span class="ml-1 font-medium text-gray-900 dark:text-white"
                      >{{ hostInfo.cpus }} cores</span
                    >
                  </div>
                  <div>
                    <span class="text-gray-600 dark:text-gray-400"
                      >Memory:</span
                    >
                    <span
                      class="ml-1 font-medium text-gray-900 dark:text-white"
                      >{{ formatBytes(hostInfo.totalMemory) }}</span
                    >
                  </div>
                </div>
              </div>

              <p class="text-xs text-gray-600 dark:text-gray-400 mb-3">
                <template v-if="agentConnected"
                  >Agent is running and connected</template
                >
                <template v-else
                  >Install the agent for enhanced local system access</template
                >
              </p>

              <div
                v-if="!agentConnected"
                class="bg-gray-900 dark:bg-black rounded-lg p-3 mb-2 relative group overflow-x-auto"
              >
                <code
                  class="text-xs text-green-400 whitespace-pre-wrap pr-8 block"
                  >{{ agentInstallCommand }}</code
                >
                <button
                  type="button"
                  @click="copyInstallCommand"
                  :disabled="!passwordVerified"
                  class="absolute top-2 right-2 p-1.5 rounded bg-gray-800 hover:bg-gray-700 disabled:bg-gray-700 text-gray-400 hover:text-white disabled:text-gray-600  disabled:cursor-not-allowed opacity-0 group-hover:opacity-100"
                  :title="copied ? 'Copied!' : 'Copy command'"
                >
                  <i v-if="copied" class="ti ti-check text-sm"></i>
                  <i v-else class="ti ti-copy text-sm"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="p-6 bg-gray-50 dark:bg-gray-900/50">
            <button
              type="submit"
              :disabled="loading || !canSubmit"
              class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-all disabled:cursor-not-allowed"
            >
              {{ loading ? "Setting up..." : "Complete Setup" }}
            </button>
          </div>
        </form>
      </div>

      <!-- Footer -->
      <div class="mt-6 flex items-center justify-center gap-4 text-sm">
        <a
          href="http://localhost:3001"
          target="_blank"
          class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400  flex items-center gap-1"
        >
          <i class="ti ti-book text-lg"></i>
          <span>Documentation</span>
        </a>
        <ClientOnly>
          <template #fallback>
            <span class="text-gray-300 dark:text-gray-700">•</span>
            <div
              class="text-gray-600 dark:text-gray-400 flex items-center gap-1"
            >
              <i class="ti ti-moon text-lg"></i>
              <span>Theme</span>
            </div>
          </template>
          <span class="text-gray-300 dark:text-gray-700">•</span>
          <button
            @click="toggleTheme"
            class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400  flex items-center gap-1"
          >
            <i v-if="isDark" class="ti ti-sun text-lg"></i>
            <i v-else class="ti ti-moon text-lg"></i>
            <span>{{ isDark ? "Light" : "Dark" }} Mode</span>
          </button>
        </ClientOnly>
      </div>
    </div>
  </div>
</template>
