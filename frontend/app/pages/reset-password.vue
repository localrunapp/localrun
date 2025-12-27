<script setup>
definePageMeta({
  layout: false,
});

const isDark = useState("isDark", () => false);
const resetToken = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const success = ref(false);
const error = ref("");

const passwordChecks = computed(() => {
  return {
    minLength: newPassword.value.length >= 8,
    passwordsMatch:
      newPassword.value &&
      confirmPassword.value &&
      newPassword.value === confirmPassword.value,
  };
});

const isFormValid = computed(() => {
  return (
    resetToken.value &&
    passwordChecks.value.minLength &&
    passwordChecks.value.passwordsMatch
  );
});

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (import.meta.client) {
    document.documentElement.classList.toggle("dark", isDark.value);
  }
};

const handleReset = async () => {
  if (!isFormValid.value) return;

  loading.value = true;
  error.value = "";
  success.value = false;

  try {
    const response = await fetch("/api/auth/reset-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Reset-Token": resetToken.value,
      },
      body: JSON.stringify({
        new_password: newPassword.value,
      }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || "Reset failed");
    }

    success.value = true;
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      if (import.meta.client) {
        window.location.href = "/login";
      } else {
        navigateTo("/login", { replace: true });
      }
    }, 2000);
  } catch (err) {
    console.error("Reset error:", err);
    error.value = err.message || "Failed to reset password. Please check your reset token and try again.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (import.meta.client) {
    isDark.value = document.documentElement.classList.contains("dark");
  }
});
</script>

<template>
  <div
    class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4"
  >
    <!-- Reset Password Container -->
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <NuxtLink to="/login" class="inline-block mb-6">
          <ClientOnly>
            <template #fallback>
              <img src="/dark.png" alt="LocalRun" class="h-12 mx-auto" />
            </template>
            <img
              :src="isDark ? '/white.png' : '/dark.png'"
              alt="LocalRun"
              class="h-12 mx-auto"
            />
          </ClientOnly>
        </NuxtLink>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Reset Password
        </h1>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Use your reset token to set a new password
        </p>
      </div>

      <!-- Success Message -->
      <div
        v-if="success"
        class="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
      >
        <div class="flex items-start gap-3">
          <i
            class="ti ti-circle-check text-green-600 dark:text-green-400 text-xl flex-shrink-0 mt-0.5"
          ></i>
          <div>
            <h3
              class="text-sm font-semibold text-green-800 dark:text-green-300 mb-1"
            >
              Password Reset Successfully
            </h3>
            <p class="text-xs text-green-700 dark:text-green-400">
              Redirecting to login...
            </p>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="error"
        class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
      >
        <div class="flex items-start gap-3">
          <i
            class="ti ti-alert-triangle text-red-600 dark:text-red-400 text-xl flex-shrink-0 mt-0.5"
          ></i>
          <div>
            <h3
              class="text-sm font-semibold text-red-800 dark:text-red-300 mb-1"
            >
              Reset Failed
            </h3>
            <p class="text-xs text-red-700 dark:text-red-400">
              {{ error }}
            </p>
          </div>
        </div>
      </div>

      <!-- Reset Form -->
      <div
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
      >
        <form @submit.prevent="handleReset" class="p-6 space-y-6">
          <!-- Reset Token -->
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >Reset Token</label
            >
            <input
              v-model="resetToken"
              type="text"
              required
              :disabled="success"
              class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Enter your reset token"
            />
            <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Use the token you received during setup or from the previous reset
            </p>
          </div>

          <!-- New Password -->
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >New Password</label
            >
            <input
              v-model="newPassword"
              type="password"
              required
              :disabled="success"
              class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Enter new password"
            />
          </div>

          <!-- Confirm Password -->
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
              >Confirm Password</label
            >
            <input
              v-model="confirmPassword"
              type="password"
              required
              :disabled="success"
              class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              placeholder="Confirm new password"
            />
          </div>

          <!-- Password Requirements -->
          <div v-if="newPassword" class="space-y-2">
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
              <div v-if="confirmPassword" class="flex items-center gap-2">
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

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading || !isFormValid || success"
            class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-all disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <i v-if="loading" class="ti ti-loader-2 animate-spin"></i>
            <i v-else-if="success" class="ti ti-check"></i>
            <span>{{
              loading
                ? "Resetting..."
                : success
                ? "Password Reset!"
                : "Reset Password"
            }}</span>
          </button>
        </form>

        <!-- Footer -->
        <div
          class="px-6 py-4 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700"
        >
          <div class="flex items-center justify-between text-xs">
            <NuxtLink
              to="/login"
              class="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
            >
              <i class="ti ti-arrow-left"></i>
              <span>Back to Login</span>
            </NuxtLink>
            <ClientOnly>
              <button
                @click="toggleTheme"
                class="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-1"
              >
                <i v-if="isDark" class="ti ti-sun"></i>
                <i v-else class="ti ti-moon"></i>
                <span>{{ isDark ? "Light" : "Dark" }}</span>
              </button>
            </ClientOnly>
          </div>
        </div>
      </div>

      <!-- Help Section -->
      <div class="mt-6 text-center">
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">
          Don't have your reset token?
        </p>
        <p class="text-xs text-gray-600 dark:text-gray-500">
          The reset token was provided during initial setup. If you've lost it,
          you'll need access to the server to retrieve it from
          <code
            class="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs"
            >/app/storage/reset_token.json</code
          >
        </p>
      </div>
    </div>
  </div>
</template>
