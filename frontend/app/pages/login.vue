<script setup>
definePageMeta({
  layout: false,
});

const authStore = useAuthStore();
const route = useRoute();
const isDark = useState("isDark", () => false);

const password = ref("");
const showPassword = ref(false);
const loading = ref(false);
const error = ref("");
const showSocialLogin = ref(false);

// Relay Server URL
const RELAY_URL = "";

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (import.meta.client) {
    document.documentElement.classList.toggle("dark", isDark.value);
  }
};

const handleLogin = async () => {
  if (!password.value || loading.value) return;

  loading.value = true;
  error.value = "";

  try {
    await authStore.login(password.value);

    // Redirect to dashboard
    await navigateTo("/");
  } catch (err) {
    error.value = err.message || "Invalid password. Please try again.";
    password.value = "";
  } finally {
    loading.value = false;
  }
};

const loginWith = (provider) => {
  const returnUrl = window.location.href;
  window.location.href = `${RELAY_URL}/login/${provider}?return_url=${encodeURIComponent(
    returnUrl
  )}`;
};

// Initialize theme on mount
onMounted(async () => {
  if (import.meta.client) {
    isDark.value = document.documentElement.classList.contains("dark");
  }

  // Check for OAuth callback
  const { provider, provider_id, email } = route.query;
  if (provider && provider_id) {
    try {
      loading.value = true;
      await authStore.loginWithProvider(provider, provider_id, email);
      await navigateTo("/");
    } catch (err) {
      error.value = err.message || "Login failed. Account might not be linked.";
    } finally {
      loading.value = false;
    }
  }
});
</script>

<template>
  <div
    class="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center p-4"
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

    <!-- Login Card -->
    <div class="w-full max-w-md">
      <div
        class="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <!-- Header -->
        <div class="p-8 text-center">
          <div class="flex items-center justify-center mb-6">
            <img
              :src="isDark ? '/white.png' : '/dark.png'"
              alt="LocalRun"
              class="h-16"
            />
          </div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Welcome Back
          </h1>
          <p class="text-gray-600 dark:text-gray-400">
            Enter your password to continue
          </p>
        </div>

        <!-- Form -->
        <div class="px-8 pb-8">
          <form @submit.prevent="handleLogin" class="space-y-6">
            <!-- Password Input -->
            <div>
              <div class="relative">
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autofocus
                  class="w-full px-4 py-3 pr-12 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="Enter your password"
                  @keydown.enter="handleLogin"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                >
                  <i
                    :class="showPassword ? 'ti ti-eye-off' : 'ti ti-eye'"
                    class="text-xl"
                  ></i>
                </button>
              </div>
            </div>

            <!-- Error Message -->
            <div
              v-if="error"
              class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"
            >
              <div class="flex items-center">
                <i
                  class="ti ti-alert-circle text-red-600 dark:text-red-400 text-xl mr-2"
                ></i>
                <span class="text-red-800 dark:text-red-300 text-sm">{{
                  error
                }}</span>
              </div>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              :disabled="loading || !password"
              class="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-all disabled:cursor-not-allowed shadow-lg flex items-center justify-center"
            >
              <span v-if="loading" class="flex items-center">
                <svg
                  class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                Signing in...
              </span>
              <span v-else class="flex items-center">
                <i class="ti ti-login mr-2"></i>
                Sign In
              </span>
            </button>

            <!-- Forgot Password Link -->
            <div class="text-center mt-4">
              <NuxtLink
                to="/reset-password"
                class="text-sm text-blue-600 dark:text-blue-400 hover:underline "
              >
                Forgot your password?
              </NuxtLink>
            </div>
          </form>

          <!-- Divider -->
          <div v-if="showSocialLogin" class="relative my-6">
            <div class="absolute inset-0 flex items-center">
              <div
                class="w-full border-t border-gray-200 dark:border-gray-700"
              ></div>
            </div>
            <div class="relative flex justify-center text-sm">
              <span class="px-2 bg-white dark:bg-gray-800 text-gray-500"
                >Or sign in with</span
              >
            </div>
          </div>

          <!-- Social Login -->
          <div v-if="showSocialLogin" class="grid grid-cols-3 gap-3">
            <button
              @click="loginWith('github')"
              class="flex items-center justify-center py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 "
              title="Sign in with GitHub"
            >
              <svg
                class="w-5 h-5 text-gray-900 dark:text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  fill-rule="evenodd"
                  clip-rule="evenodd"
                  d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"
                />
              </svg>
            </button>
            <button
              @click="loginWith('google')"
              class="flex items-center justify-center py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 "
              title="Sign in with Google"
            >
              <svg
                class="w-5 h-5"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
            </button>
            <button
              @click="loginWith('microsoft')"
              class="flex items-center justify-center py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 "
              title="Sign in with Microsoft"
            >
              <svg
                class="w-5 h-5"
                viewBox="0 0 23 23"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path fill="#f35325" d="M1 1h10v10H1z" />
                <path fill="#81bc06" d="M12 1h10v10H12z" />
                <path fill="#05a6f0" d="M1 12h10v10H1z" />
                <path fill="#ffba08" d="M12 12h10v10H12z" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Footer -->
        <div
          class="bg-gray-50 dark:bg-gray-900/50 px-8 py-4 text-center border-t border-gray-200 dark:border-gray-700"
        >
          <p class="text-xs text-gray-500 dark:text-gray-400">
            LocalRun - Secure Local Tunneling
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
