<script setup>
import { useAuthStore } from '~/stores/auth';

const authStore = useAuthStore();
const router = useRouter();
const isDark = useState('isDark', () => false);

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (import.meta.client) {
    document.documentElement.classList.toggle('dark', isDark.value);
    localStorage.setItem('hs_theme', isDark.value ? 'dark' : 'light');
  }
};

const logout = async () => {
  authStore.logout();
  await navigateTo('/login');
};

onMounted(() => {
  if (import.meta.client) {
    const savedTheme = localStorage.getItem('hs_theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
      isDark.value = true;
      document.documentElement.classList.add('dark');
    } else {
      isDark.value = false;
      document.documentElement.classList.remove('dark');
    }
  }
});
</script>
<template>
  <header
    class="lg:ms-55 fixed top-0 inset-x-0 flex flex-wrap md:justify-start md:flex-nowrap z-50 bg-zinc-100 dark:bg-gray-900">
    <div class="flex justify-between basis-full items-center w-full py-1 mt-1 px-4 sm:px-5.5">
      <div class="flex items-center gap-x-3">
        <div class="lg:hidden">
          <!-- Sidebar Toggle -->
          <button type="button"
            class="w-7 h-9.5 inline-flex justify-center items-center gap-x-2 text-sm font-medium rounded-lg border border-gray-200 bg-white text-gray-800 shadow-2xs hover:bg-gray-50 focus:outline-hidden focus:bg-gray-100 disabled:opacity-50 disabled:pointer-events-none dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700 dark:focus:bg-gray-700"
            aria-haspopup="dialog" aria-expanded="false" aria-controls="hs-pro-sidebar" aria-label="Toggle navigation"
            data-hs-overlay="#hs-pro-sidebar">
            <svg class="shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 8L21 12L17 16M3 12H13M3 6H13M3 18H13" />
            </svg>
          </button>
          <!-- End Sidebar Toggle -->
        </div>
        
        <!-- Logo on mobile -->
        <div class="lg:hidden">
          <Logo />
        </div>
      </div>

      <div class="flex justify-end items-center gap-x-2">
        <div class="flex items-center gap-x-2">
          <!-- Version -->
          <span class="text-xs text-gray-500 dark:text-gray-500 hidden sm:block">
            v1.0.0
          </span>
          
          <!-- Docs Link -->
          <a href="http://localhost:3006" target="_blank"
            class="flex items-center gap-x-1.5 py-1.5 px-2 text-sm text-gray-800 rounded-lg hover:bg-gray-200 focus:outline-hidden focus:bg-gray-200 dark:hover:bg-gray-800 dark:focus:bg-gray-800 dark:text-gray-200">
            Docs
          </a>
          
          <!-- Theme Toggle -->
          <ClientOnly>
            <button
              @click="toggleTheme"
              type="button"
              class="size-9.5 inline-flex justify-center items-center gap-x-2 rounded-full border border-transparent text-gray-500 hover:bg-gray-200 disabled:opacity-50 disabled:pointer-events-none focus:outline-hidden focus:bg-gray-200 dark:text-gray-400 dark:hover:bg-gray-800 dark:focus:bg-gray-800"
            >
              <svg v-if="!isDark" class="shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
              </svg>
              <svg v-else class="shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5" />
                <path d="M12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
              </svg>
            </button>
          </ClientOnly>
          <!-- End Theme Toggle -->

          <!-- Logout Button -->
          <button
            @click="logout"
            type="button"
            class="size-9.5 inline-flex justify-center items-center gap-x-2 rounded-full border border-transparent text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 disabled:opacity-50 disabled:pointer-events-none focus:outline-hidden"
          >
            <svg class="shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24"
              viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
              stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" x2="9" y1="12" y2="12" />
            </svg>
          </button>
          <!-- End Logout Button -->
        </div>
      </div>
    </div>
  </header>
</template>
