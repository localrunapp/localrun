<script setup>
import { IconDashboard } from "@tabler/icons-vue";
definePageMeta({
  layout: "default",
});
</script>

<template>
  <Page>
    <template #header>
      <PageHeader :icon="IconDashboard" title="Dashboard" />
    </template>

    <div class="p-4">
      <!-- Stats Grid -->
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8">
        <!-- Active Services Card -->
        <div
          class="bg-white border border-gray-200 rounded-xl hover:border-gray-300  dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600"
        >
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Icon
                  name="tabler:server"
                  class="size-6 text-gray-700 dark:text-gray-300"
                />
              </div>
              <span
                class="text-xs font-medium text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-full"
                >Active</span
              >
            </div>
            <h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">
              0
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Active Services
            </p>
          </div>
        </div>

        <!-- Providers Card -->
        <div
          class="bg-white border border-gray-200 rounded-xl hover:border-gray-300  dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600"
        >
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Icon
                  name="tabler:plug-connected"
                  class="size-6 text-gray-700 dark:text-gray-300"
                />
              </div>
            </div>
            <h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">
              0
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">Providers</p>
          </div>
        </div>

        <!-- Domains Card -->
        <div
          class="bg-white border border-gray-200 rounded-xl hover:border-gray-300  dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600"
        >
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Icon
                  name="tabler:world"
                  class="size-6 text-gray-700 dark:text-gray-300"
                />
              </div>
            </div>
            <h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">
              0
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">Domains</p>
          </div>
        </div>

        <!-- Requests Card -->
        <div
          class="bg-white border border-gray-200 rounded-xl hover:border-gray-300  dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600"
        >
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Icon
                  name="tabler:chart-line"
                  class="size-6 text-gray-700 dark:text-gray-300"
                />
              </div>
            </div>
            <h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">
              0
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Total Requests
            </p>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div
        class="bg-white border border-gray-200 rounded-xl dark:bg-gray-800 dark:border-gray-700"
      >
        <div class="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2
            class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2"
          >
            <Icon
              name="tabler:bolt"
              class="size-5 text-gray-700 dark:text-gray-300"
            />
            Quick Actions
          </h2>
          <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Get started with these common tasks
          </p>
        </div>
        <div class="p-6">
          <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <NuxtLink
              to="/services"
              class="group flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-gray-400  dark:border-gray-700 dark:hover:border-gray-500"
            >
              <div class="shrink-0 p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Icon
                  name="tabler:plus"
                  class="size-5 text-gray-700 dark:text-gray-300"
                />
              </div>
              <div class="flex-1 min-w-0">
                <h3
                  class="text-sm font-semibold text-gray-900 dark:text-white mb-1"
                >
                  New Service
                </h3>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  Create a new tunnel service
                </p>
              </div>
            </NuxtLink>

            <NuxtLink
              to="/providers"
              class="group flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-gray-400  dark:border-gray-700 dark:hover:border-gray-500"
            >
              <div class="shrink-0 p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Icon
                  name="tabler:plug-connected"
                  class="size-5 text-gray-700 dark:text-gray-300"
                />
              </div>
              <div class="flex-1 min-w-0">
                <h3
                  class="text-sm font-semibold text-gray-900 dark:text-white mb-1"
                >
                  Configure Provider
                </h3>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  Setup tunnel providers
                </p>
              </div>
            </NuxtLink>

            <NuxtLink
              to="/domains"
              class="group flex items-start gap-4 p-4 rounded-xl border-2 border-gray-200 hover:border-gray-400  dark:border-gray-700 dark:hover:border-gray-500"
            >
              <div class="shrink-0 p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Icon
                  name="tabler:world"
                  class="size-5 text-gray-700 dark:text-gray-300"
                />
              </div>
              <div class="flex-1 min-w-0">
                <h3
                  class="text-sm font-semibold text-gray-900 dark:text-white mb-1"
                >
                  Add Domain
                </h3>
                <p class="text-xs text-gray-600 dark:text-gray-400">
                  Register a custom domain
                </p>
              </div>
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </Page>
</template>
