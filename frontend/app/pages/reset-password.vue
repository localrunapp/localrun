<script setup>
definePageMeta({
  layout: false,
});

const isDark = useState("isDark", () => false);
const copied = ref(false);
const userOS = ref("linux"); // Default to linux

// Detect user's operating system
const detectOS = () => {
  if (!import.meta.client) return "linux";
  
  const platform = navigator.platform.toLowerCase();
  const userAgent = navigator.userAgent.toLowerCase();
  
  if (platform.includes("win") || userAgent.includes("windows")) {
    return "windows";
  } else if (platform.includes("mac") || userAgent.includes("mac")) {
    return "macos";
  } else {
    return "linux";
  }
};

// Platform-specific commands
const getTokenCommand = computed(() => {
  if (userOS.value === "windows") {
    return 'docker logs (docker ps -q -f label=localrun-app) 2>&1 | Select-String "Token:" | Select-Object -Last 1';
  }
  return 'docker logs $(docker ps -q -f label=localrun-app) 2>&1 | grep "Token:" | tail -1';
});

const getResetCommand = computed(() => {
  const baseUrl = "http://localhost:8000/auth/reset-password";
  
  if (userOS.value === "windows") {
    // PowerShell command
    return `$headers = @{
    "Content-Type" = "application/json"
    "X-Reset-Token" = "YOUR_TOKEN_HERE"
}
$body = '{"new_password": "your_new_password"}'
Invoke-RestMethod -Uri "${baseUrl}" -Method Post -Headers $headers -Body $body`;
  } else {
    // Unix/Linux curl command
    return `curl -X POST ${baseUrl} \\
  -H "Content-Type: application/json" \\
  -H "X-Reset-Token: YOUR_TOKEN_HERE" \\
  -d '{"new_password": "your_new_password"}'`;
  }
});

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (import.meta.client) {
    document.documentElement.classList.toggle("dark", isDark.value);
  }
};

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    console.error("Failed to copy:", err);
  }
};

// Initialize theme and detect OS on mount
onMounted(() => {
  if (import.meta.client) {
    isDark.value = document.documentElement.classList.contains("dark");
    userOS.value = detectOS();
  }
});
</script>

<template>
  <div
    class="min-h-screen bg-gray-100 dark:bg-gray-900 p-4"
  >
    <!-- Theme Toggle -->
    <div class="absolute top-4 right-4">
      <button
        @click="toggleTheme"
        class="p-2 rounded-lg bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200 dark:border-gray-700 hover:bg-white dark:hover:bg-gray-800 transition-all"
      >
        <i v-if="isDark" class="ti ti-sun text-xl text-yellow-500"></i>
        <i v-else class="ti ti-moon text-xl text-blue-600"></i>
      </button>
    </div>

    <!-- Content -->
    <div class="max-w-4xl mx-auto py-12">
      <!-- Header -->
      <div class="text-center mb-12">
        <NuxtLink to="/login" class="inline-block mb-6">
          <img
            :src="isDark ? '/white.png' : '/dark.png'"
            alt="LocalRun"
            class="h-16 mx-auto"
          />
        </NuxtLink>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Reset Password
        </h1>
        <p class="text-gray-600 dark:text-gray-400">
          Follow these steps to reset your admin password
        </p>
        
        <!-- OS Selector -->
        <div class="flex justify-center gap-2 mt-6">
          <button
            @click="userOS = 'windows'"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              userOS === 'windows'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            ]"
          >
            <i class="ti ti-brand-windows mr-1"></i>
            Windows
          </button>
          <button
            @click="userOS = 'macos'"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              userOS === 'macos'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            ]"
          >
            <i class="ti ti-brand-apple mr-1"></i>
            macOS
          </button>
          <button
            @click="userOS = 'linux'"
            :class="[
              'px-4 py-2 rounded-lg font-medium transition-all',
              userOS === 'linux'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
            ]"
          >
            <i class="ti ti-brand-ubuntu mr-1"></i>
            Linux
          </button>
        </div>
      </div>

      <!-- Instructions Card -->
      <div
        class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <div class="p-8 space-y-8">
          <!-- Step 1 -->
          <div>
            <div class="flex items-center mb-4">
              <div
                class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold mr-3"
              >
                1
              </div>
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                Get Your Reset Token
              </h2>
            </div>
            <p class="text-gray-600 dark:text-gray-400 mb-4 ml-13">
              The reset token is stored in your Docker container logs. Run this
              command to find it:
            </p>
            <div class="ml-13 relative group">
              <div
                class="bg-gray-900 dark:bg-black rounded-lg p-4 overflow-x-auto"
              >
                <code class="text-sm text-green-400 whitespace-pre-wrap block">{{ getTokenCommand }}</code>
              </div>
              <button
                @click="copyToClipboard(getTokenCommand)"
                class="absolute top-2 right-2 p-2 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white  opacity-0 group-hover:opacity-100"
                :title="copied ? 'Copied!' : 'Copy command'"
              >
                <i v-if="copied" class="ti ti-check text-sm"></i>
                <i v-else class="ti ti-copy text-sm"></i>
              </button>
            </div>
            <div
              class="ml-13 mt-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4"
            >
              <div class="flex items-start">
                <i
                  class="ti ti-info-circle text-blue-600 dark:text-blue-400 text-xl mr-2 mt-0.5"
                ></i>
                <div class="text-sm text-blue-800 dark:text-blue-300">
                  <p class="font-medium mb-1">Note:</p>
                  <p>
                    The reset token is generated when LocalRun starts for the
                    first time and is stored in
                    <code
                      class="bg-blue-100 dark:bg-blue-900/40 px-1 py-0.5 rounded"
                      >/app/storage/reset_token.json</code
                    >
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 2 -->
          <div>
            <div class="flex items-center mb-4">
              <div
                class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold mr-3"
              >
                2
              </div>
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                Reset Your Password
              </h2>
            </div>
            <p class="text-gray-600 dark:text-gray-400 mb-4 ml-13">
              <span v-if="userOS === 'windows'">
                Use this PowerShell command to reset your password. Replace
              </span>
              <span v-else>
                Use this curl command to reset your password. Replace
              </span>
              <code
                class="bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded text-sm"
                >YOUR_TOKEN_HERE</code
              >
              with your reset token and
              <code
                class="bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded text-sm"
                >your_new_password</code
              >
              with your desired password (minimum 8 characters):
            </p>
            <div class="ml-13 relative group">
              <div
                class="bg-gray-900 dark:bg-black rounded-lg p-4 overflow-x-auto"
              >
                <code class="text-sm text-green-400 whitespace-pre-wrap block">{{ getResetCommand }}</code>
              </div>
              <button
                @click="copyToClipboard(getResetCommand)"
                class="absolute top-2 right-2 p-2 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white  opacity-0 group-hover:opacity-100"
                :title="copied ? 'Copied!' : 'Copy command'"
              >
                <i v-if="copied" class="ti ti-check text-sm"></i>
                <i v-else class="ti ti-copy text-sm"></i>
              </button>
            </div>
            <div
              class="ml-13 mt-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4"
            >
              <div class="flex items-start">
                <i
                  class="ti ti-alert-triangle text-yellow-600 dark:text-yellow-400 text-xl mr-2 mt-0.5"
                ></i>
                <div class="text-sm text-yellow-800 dark:text-yellow-300">
                  <p class="font-medium mb-1">Important:</p>
                  <p>
                    Your new password must be at least 8 characters long. Make
                    sure to save it securely!
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Step 3 -->
          <div>
            <div class="flex items-center mb-4">
              <div
                class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold mr-3"
              >
                3
              </div>
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                Login with New Password
              </h2>
            </div>
            <p class="text-gray-600 dark:text-gray-400 mb-4 ml-13">
              After successfully resetting your password, you can log in with
              your new credentials.
            </p>
            <div class="ml-13">
              <NuxtLink
                to="/login"
                class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium rounded-lg transition-all shadow-lg"
              >
                <i class="ti ti-login mr-2"></i>
                Go to Login
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div
          class="bg-gray-50 dark:bg-gray-900/50 px-8 py-4 border-t border-gray-200 dark:border-gray-700"
        >
          <div class="flex items-center justify-between">
            <p class="text-xs text-gray-500 dark:text-gray-400">
              LocalRun - Secure Local Tunneling
            </p>
            <NuxtLink
              to="/login"
              class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
            >
              Back to Login
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
