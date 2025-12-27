<script setup>
definePageMeta({
  layout: false,
});

const setupStore = useSetupStore();
const isDark = useState("isDark", () => false);

const loading = ref(false);
const error = ref("");
const setupCompleted = ref(false);
const resetToken = ref("");
const copied = ref(false);
const downloadedToken = ref(false);
const systemInfo = ref(null);
const agentConnected = ref(false);
const hostInfo = ref(null);
const apiConnected = ref(true);
const checkingConnection = ref(false);
const agentInstallCommand = ref("");
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
  return isPasswordValid.value && formData.value.serverName;
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
    const response = await fetch("/api/health", {
      signal: AbortSignal.timeout(5000),
      headers: {
        Accept: "application/json",
      },
    });

    if (response.ok) {
      apiConnected.value = true;
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

const loadSystemInfo = async () => {
  try {
    const info = await setupStore.getSystemInfo();
    if (info) {
      systemInfo.value = info;

      const script = await setupStore.getAgentInstallScript();
      if (script) {
        agentInstallCommand.value = script;
      }

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

    const wasConnected = agentConnected.value;
    agentConnected.value = data.agent_installed;

    if (data.agent_installed && !wasConnected) {
      await getHostInfo();
    }

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

  checkAgentStatus();

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

const copyToken = async () => {
  if (import.meta.client && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(resetToken.value);
      copied.value = true;
      setTimeout(() => {
        copied.value = false;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  }
};

const downloadToken = () => {
  const tokenData = {
    reset_token: resetToken.value,
    installation_name: formData.value.serverName,
    created_at: new Date().toISOString(),
    note: "Keep this token safe! You'll need it to reset your password if you forget it.",
  };

  const blob = new Blob([JSON.stringify(tokenData, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `localrun-reset-token-${formData.value.serverName}.json`;
  a.click();
  URL.revokeObjectURL(url);
  downloadedToken.value = true;
};

const handleSubmit = async () => {
  if (!canSubmit.value) return;

  loading.value = true;
  error.value = "";

  try {
    const setupData = {
      new_password: formData.value.newPassword,
      new_password_confirmation: formData.value.confirmPassword,
      installation_name: formData.value.serverName,
    };

    const result = await setupStore.completeSetup(setupData);
    
    resetToken.value = result.reset_token;
    setupCompleted.value = true;
  } catch (err) {
    console.error("Setup error:", err);
    error.value = err.message || "Setup failed. Please try again.";
  } finally {
    loading.value = false;
  }
};

const continueToDashboard = async () => {
  await setupStore.checkSetupStatus();
  
  if (import.meta.client) {
    window.location.href = "/login";
  } else {
    await navigateTo("/login", { replace: true });
  }
};

onMounted(async () => {
  if (import.meta.client) {
    isDark.value = document.documentElement.classList.contains("dark");

    try {
      const response = await fetch("/api/setup/status");
      if (response.ok) {
        const data = await response.json();
        if (data.setup_completed) {
          window.location.href = "/login";
          return;
        }
      }
    } catch (err) {
      console.error("Error checking setup status:", err);
    }

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
              class="inline-flex items-center gap-1 px-2 py-1 bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white text-xs font-medium rounded disabled:cursor-not-allowed"
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

      <!-- Setup Form (shown before completion) -->
      <div
        v-if="!setupCompleted"
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <form
          @submit.prevent="handleSubmit"
          class="divide-y divide-gray-200 dark:divide-gray-700"
        >
          <!-- Section 1: Set Password -->
          <div class="p-6">
            <h2
              class="text-sm font-semibold text-gray-900 dark:text-white mb-4"
            >
              1. Set Your Password
            </h2>
            <p class="text-xs text-gray-600 dark:text-gray-400 mb-4">
              Create a secure password for your admin account
            </p>

            <!-- Password inputs -->
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label
                  class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2"
                  >Password</label
                >
                <input
                  v-model="formData.newPassword"
                  type="password"
                  required
                  :disabled="!apiConnected"
                  class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:cursor-not-allowed"
                  placeholder="Enter password"
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
                  :disabled="!apiConnected"
                  class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:cursor-not-allowed"
                  placeholder="Confirm password"
                />
              </div>
            </div>

            <!-- Password Requirements -->
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

          <!-- Section 2: Server Configuration -->
          <div class="p-6">
            <h2
              class="text-sm font-semibold text-gray-900 dark:text-white mb-4"
            >
              2. Server Configuration
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
                :disabled="!apiConnected"
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
                  :disabled="!apiConnected"
                  class="absolute top-2 right-2 p-1.5 rounded bg-gray-800 hover:bg-gray-700 disabled:bg-gray-700 text-gray-400 hover:text-white disabled:text-gray-600 disabled:cursor-not-allowed opacity-0 group-hover:opacity-100"
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

      <!-- Setup Completed - Show Reset Token -->
      <div
        v-else
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <div class="p-8">
          <!-- Success Icon -->
          <div class="text-center mb-6">
            <div
              class="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4"
            >
              <i
                class="ti ti-circle-check text-4xl text-green-600 dark:text-green-400"
              ></i>
            </div>
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Setup Complete!
            </h2>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Your password has been configured successfully
            </p>
          </div>

          <!-- Reset Token Warning -->
          <div
            class="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg"
          >
            <div class="flex items-start gap-3">
              <i
                class="ti ti-alert-triangle text-amber-600 dark:text-amber-400 text-xl flex-shrink-0 mt-0.5"
              ></i>
              <div>
                <h3
                  class="text-sm font-semibold text-amber-800 dark:text-amber-300 mb-1"
                >
                  Important: Save Your Reset Token
                </h3>
                <p class="text-xs text-amber-700 dark:text-amber-400">
                  This token will allow you to reset your password if you forget
                  it. Save it securely - you won't be able to see it again!
                </p>
              </div>
            </div>
          </div>

          <!-- Reset Token Display -->
          <div class="mb-6">
            <label
              class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2"
              >Reset Token</label
            >
            <div class="relative">
              <input
                :value="resetToken"
                type="text"
                readonly
                class="w-full px-4 py-3 pr-24 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white font-mono text-sm"
              />
              <button
                @click="copyToken"
                class="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-all"
              >
                <i
                  v-if="copied"
                  class="ti ti-check text-sm mr-1"
                ></i>
                <i v-else class="ti ti-copy text-sm mr-1"></i>
                {{ copied ? "Copied!" : "Copy" }}
              </button>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex gap-3 mb-6">
            <button
              @click="downloadToken"
              class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-medium rounded-lg transition-all"
            >
              <i
                v-if="downloadedToken"
                class="ti ti-check text-lg"
              ></i>
              <i v-else class="ti ti-download text-lg"></i>
              {{ downloadedToken ? "Downloaded" : "Download as JSON" }}
            </button>
          </div>

          <!-- Continue Button -->
          <button
            @click="continueToDashboard"
            class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
          >
            <span>Continue to Dashboard</span>
            <i class="ti ti-arrow-right text-lg"></i>
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="mt-6 flex items-center justify-center gap-4 text-sm">
        <a
          href="http://localhost:3001"
          target="_blank"
          class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-1"
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
            class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-1"
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
