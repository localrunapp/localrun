<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
    <!-- Offline Container -->
    <div class="w-full max-w-2xl">
      <!-- Logo -->
      <div class="text-center mb-8">
        <ClientOnly>
          <template #fallback>
            <img src="/dark.png" alt="LocalRun" class="h-12 mx-auto mb-4" />
          </template>
          <img :src="isDark ? '/white.png' : '/dark.png'" alt="LocalRun" class="h-12 mx-auto mb-4" />
        </ClientOnly>
        <div class="flex items-center justify-center gap-2 mb-2">
          <i class="ti ti-cloud-off text-red-600 dark:text-red-400 text-3xl"></i>
        </div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Backend Offline</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">Cannot connect to LocalRun API server</p>
      </div>

      <!-- Main Message Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
        <div class="p-6">
          <div class="flex items-start gap-3 mb-4">
            <i class="ti ti-exclamation-triangle text-red-600 dark:text-red-400 text-xl flex-shrink-0 mt-0.5"></i>
            <div>
              <h2 class="text-sm font-semibold text-gray-900 dark:text-white mb-2">Backend API Server is Unreachable</h2>
              <p class="text-xs text-gray-600 dark:text-gray-400 mb-2">
                The LocalRun backend API is not responding. This usually means the Docker container is not running or has crashed.
              </p>
              <p class="text-xs text-gray-600 dark:text-gray-400">
                Try the following steps to resolve this issue:
              </p>
            </div>
          </div>

          <!-- Troubleshooting Steps -->
          <div class="space-y-3">
            <!-- Step 1: Check Container Status -->
            <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div class="flex items-start gap-2 mb-2">
                <span class="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold flex items-center justify-center">1</span>
                <p class="text-xs font-medium text-gray-700 dark:text-gray-300">Check if the Docker container is running:</p>
              </div>
              <div class="bg-gray-900 dark:bg-black rounded-lg p-3 relative group">
                <code class="text-xs text-green-400 break-all pr-8">docker ps -f label=localrun-app</code>
                <button type="button" @click="copyCommand('docker ps -f label=localrun-app', 'check')"
                  class="absolute top-2 right-2 p-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white  opacity-0 group-hover:opacity-100"
                  :title="copiedCheck ? 'Copied!' : 'Copy command'">
                  <i v-if="copiedCheck" class="ti ti-check text-sm"></i>
                  <i v-else class="ti ti-copy text-sm"></i>
                </button>
              </div>
            </div>

            <!-- Step 2: Restart Container -->
            <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div class="flex items-start gap-2 mb-2">
                <span class="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold flex items-center justify-center">2</span>
                <p class="text-xs font-medium text-gray-700 dark:text-gray-300">Restart the Docker container:</p>
              </div>
              <div class="bg-gray-900 dark:bg-black rounded-lg p-3 relative group">
                <code class="text-xs text-green-400 break-all pr-8">docker restart $(docker ps -aq -f label=localrun-app)</code>
                <button type="button" @click="copyCommand('docker restart $(docker ps -aq -f label=localrun-app)', 'restart')"
                  class="absolute top-2 right-2 p-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white  opacity-0 group-hover:opacity-100"
                  :title="copiedRestart ? 'Copied!' : 'Copy command'">
                  <i v-if="copiedRestart" class="ti ti-check text-sm"></i>
                  <i v-else class="ti ti-copy text-sm"></i>
                </button>
              </div>
            </div>

            <!-- Step 3: View Logs -->
            <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div class="flex items-start gap-2 mb-2">
                <span class="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold flex items-center justify-center">3</span>
                <p class="text-xs font-medium text-gray-700 dark:text-gray-300">Check container logs for errors:</p>
              </div>
              <div class="bg-gray-900 dark:bg-black rounded-lg p-3 relative group">
                <code class="text-xs text-green-400 break-all pr-8">docker logs $(docker ps -q -f label=localrun-app) --tail 50</code>
                <button type="button" @click="copyCommand('docker logs $(docker ps -q -f label=localrun-app) --tail 50', 'logs')"
                  class="absolute top-2 right-2 p-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white  opacity-0 group-hover:opacity-100"
                  :title="copiedLogs ? 'Copied!' : 'Copy command'">
                  <i v-if="copiedLogs" class="ti ti-check text-sm"></i>
                  <i v-else class="ti ti-copy text-sm"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Retry Button -->
        <div class="p-6 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
          <button @click="retryConnection" :disabled="checking"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-all disabled:cursor-not-allowed flex items-center justify-center gap-2">
            <i v-if="checking" class="ti ti-loader-2 animate-spin"></i>
            <i v-else class="ti ti-refresh"></i>
            {{ checking ? 'Checking Connection...' : 'Retry Connection' }}
          </button>
          <p v-if="lastChecked" class="text-xs text-center text-gray-500 dark:text-gray-500 mt-2">
            Last checked: {{ lastChecked }}
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div class="mt-6 flex items-center justify-center gap-4 text-sm">
        <a href="http://localhost:3001" target="_blank"
          class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400  flex items-center gap-1">
          <i class="ti ti-book text-lg"></i>
          <span>Documentation</span>
        </a>
        <ClientOnly>
          <template #fallback>
            <span class="text-gray-300 dark:text-gray-700">•</span>
            <div class="text-gray-600 dark:text-gray-400 flex items-center gap-1">
              <i class="ti ti-moon text-lg"></i>
              <span>Theme</span>
            </div>
          </template>
          <span class="text-gray-300 dark:text-gray-700">•</span>
          <button @click="toggleTheme"
            class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400  flex items-center gap-1">
            <i v-if="isDark" class="ti ti-sun text-lg"></i>
            <i v-else class="ti ti-moon text-lg"></i>
            <span>{{ isDark ? 'Light' : 'Dark' }} Mode</span>
          </button>
        </ClientOnly>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
});

const isDark = useState('isDark', () => false);
const checking = ref(false);
const lastChecked = ref('');
const copiedCheck = ref(false);
const copiedRestart = ref(false);
const copiedLogs = ref(false);

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (import.meta.client) {
    document.documentElement.classList.toggle('dark', isDark.value);
  }
};

const copyCommand = async (command, type) => {
  if (import.meta.client && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(command);
      
      // Set the appropriate copied state
      if (type === 'check') copiedCheck.value = true;
      else if (type === 'restart') copiedRestart.value = true;
      else if (type === 'logs') copiedLogs.value = true;
      
      setTimeout(() => {
        if (type === 'check') copiedCheck.value = false;
        else if (type === 'restart') copiedRestart.value = false;
        else if (type === 'logs') copiedLogs.value = false;
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }
};

const retryConnection = async () => {
  checking.value = true;
  
  try {
    // Try to check API health
    const response = await fetch('/api/health', {
      signal: AbortSignal.timeout(5000),
      headers: {
        'Accept': 'application/json',
      }
    });

    if (response.ok) {
      // API is back online, check if setup is complete
      const setupResponse = await fetch('/api/setup/status', {
        signal: AbortSignal.timeout(5000),
        headers: {
          'Accept': 'application/json',
        }
      });

      if (setupResponse.ok) {
        const data = await setupResponse.json();
        
        if (data.setup_completed) {
          // Setup is complete, redirect to home/login
          navigateTo('/login');
        } else {
          // Setup is not complete, redirect to setup
          navigateTo('/setup');
        }
      } else {
        // Can't determine setup status, redirect to setup
        navigateTo('/setup');
      }
    } else {
      throw new Error('API still offline');
    }
  } catch (error) {
    console.error('Retry connection failed:', error);
    // Update last checked time
    const now = new Date();
    lastChecked.value = now.toLocaleTimeString();
  } finally {
    checking.value = false;
  }
};

onMounted(() => {
  if (import.meta.client) {
    isDark.value = document.documentElement.classList.contains('dark');
  }
});
</script>
