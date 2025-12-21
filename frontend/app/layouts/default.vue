<script setup>
// import { useChatWebSocket } from "@/composables/useChatWebSocket";

// const { startListening } = useChatWebSocket();
const year = new Date().getFullYear();

onMounted(() => {
  // startListening();
});
</script>
<template>
  <div class="min-h-screen">
    <Header />

    <aside
      id="hs-pro-sidebar"
      class="hs-overlay [--auto-close:lg] hs-overlay-open:translate-x-0 -translate-x-full transition-transform duration-300 ease-in-out w-55 h-full hidden fixed inset-y-0 start-0 z-55 bg-zinc-100 lg:block lg:translate-x-0 lg:end-auto lg:bottom-0 dark:bg-gray-900"
      tabindex="-1"
      aria-label="Sidebar"
    >
      <div class="relative flex flex-col h-full max-h-full">
        <!-- Logo Section (Desktop) -->
        <div
          class="hidden lg:flex pt-2 ps-5 pe-2 pb-3 mt-2 items-center gap-x-1"
        >
          <Logo size="sm" />
        </div>

        <!-- Mobile Header with Logo and Close Button -->
        <div
          class="lg:hidden pt-3 pb-2 ps-5 pe-2 h-11.5 flex items-center gap-x-1"
        >
          <Logo size="sm" />
          <div class="ms-auto">
            <!-- Sidebar Close -->
            <button
              type="button"
              class="w-7 h-9 inline-flex justify-center items-center gap-x-2 text-sm font-medium rounded-md border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 focus:outline-hidden focus:bg-gray-100 disabled:opacity-50 disabled:pointer-events-none dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700 dark:focus:bg-gray-700"
              data-hs-overlay="#hs-pro-sidebar"
            >
              <svg
                class="shrink-0 size-4"
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
            <!-- End Sidebar Close -->
          </div>
        </div>

        <!-- Scrollable Menu Area -->
        <div
          class="p-3 pt-0 size-full flex flex-col overflow-y-auto [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-gray-200 [&::-webkit-scrollbar-thumb]:bg-gray-300 dark:[&::-webkit-scrollbar-track]:bg-gray-700 dark:[&::-webkit-scrollbar-thumb]:bg-gray-500"
        >
          <Menu />
        </div>
      </div>
    </aside>

    <main
      class="lg:ms-55 bg-zinc-100 lg:fixed lg:inset-0 pt-[52px] pr-3 pb-3 pl-0 dark:bg-gray-900"
    >
      <!-- Content Container -->
      <div
        class="h-[calc(100vh-68px)] lg:h-full overflow-hidden flex flex-col bg-white border border-gray-200 shadow-xs rounded-lg dark:bg-gray-800 dark:border-gray-700"
      >
        <slot />
      </div>
    </main>
  </div>
</template>
