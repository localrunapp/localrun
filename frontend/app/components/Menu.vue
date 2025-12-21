<script setup>
import * as icons from "@tabler/icons-vue";

const route = useRoute();
const authStore = useAuthStore();
const serverStore = useServerStore();
const isDark = useState("isDark", () => false);

const sizeTextMenu = ref("text-sm");
const sizeIconMenu = ref("size-4");
const isUpdating = ref(false);
const isRestarting = ref(false);

const waitForRestart = async () => {
  isRestarting.value = true;
  // Give it some time to shut down
  await new Promise((resolve) => setTimeout(resolve, 5000));

  const checkHealth = async () => {
    try {
      // Try to fetch a simple endpoint
      const res = await fetch("/api/health");
      if (res.ok) {
        window.location.reload();
        return;
      }
    } catch (e) {
      // Ignore errors (server down)
    }
    // Retry after 2 seconds
    // setTimeout(checkHealth, 2000);
  };

  checkHealth();
};

const handleUpdate = async () => {
  if (
    !confirm(
      "Are you sure you want to update LocalRun? This will restart the application."
    )
  )
    return;

  isUpdating.value = true;
  try {
    let method = "";
    // Try Agent Update first
    try {
      const response = await fetch("http://localhost:47777/api/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (response.ok) {
        method = "Agent";
      }
    } catch (e) {
      console.log("Agent update failed, trying backend fallback...");
    }

    if (!method) {
      // Fallback to Backend Watchtower Update
      const response = await fetch("/api/v1/update/docker", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (!response.ok) throw new Error("Update failed");
      method = "Watchtower";
    }

    // Start waiting for restart
    waitForRestart();
  } catch (e) {
    console.error(e);
    alert(
      "Failed to initiate update. Neither Agent nor Backend could handle the request."
    );
    isUpdating.value = false;
  }
};

const menuItems = [
  {
    label: "Dashboard",
    icon: "IconDashboard",
    route: "/",
    pattern: "/",
  },
  {
    label: "Services",
    icon: "IconRocket",
    route: "/services",
    pattern: "/services",
  },
  {
    label: "Analytics",
    icon: "IconActivity",
    route: "/analytics",
    pattern: "/analytics",
  },

  {
    label: "Servers",
    icon: "IconServer",
    route: "/servers",
    pattern: "/servers",
  },
  {
    label: "Toolkit",
    icon: "IconTools",
    route: "/toolkit",
    pattern: "/toolkit",
  },
];

const settingsItems = [
  {
    label: "Domains",
    icon: "IconWorld",
    route: "/domains",
    pattern: "/domains",
  },
  {
    label: "Providers",
    icon: "IconPlugConnected",
    route: "/providers",
    pattern: "/providers",
  },
  {
    label: "Backups",
    icon: "IconDatabaseExport",
    route: "/backup",
    pattern: "/backup",
  },
  {
    label: "Logs",
    icon: "IconFileText",
    route: "/logs",
    pattern: "/logs",
  },
];

const isActive = (path) => {
  if (path === "/") {
    return route.path === "/";
  }
  return route.path.startsWith(path);
};

onMounted(() => {
  if (import.meta.client) {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      isDark.value = true;
    } else if (savedTheme === "light") {
      isDark.value = false;
    } else {
      isDark.value = window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    // Fetch servers to cache localhost server ID
    serverStore.fetchServers();
  }
});
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Navigation -->
    <nav
      class="hs-accordion-group pb-3 w-full flex flex-col flex-1 overflow-y-auto"
      data-hs-accordion-always-open
    >
      <ul class="flex flex-col gap-y-1">
        <!-- Main Menu Items -->
        <li v-for="(item, index) in menuItems" :key="'menu-' + index" class="">
          <NuxtLink
            :to="item.route"
            class="flex gap-x-3 py-2 px-3 text-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 dark:text-gray-200"
            :class="[
              sizeTextMenu,
              {
                'bg-gray-200 dark:bg-gray-700': isActive(item.pattern),
              },
            ]"
          >
            <component
              :is="icons[item.icon]"
              class="shrink-0 mt-0.5"
              :class="sizeIconMenu"
            />
            {{ item.label }}
          </NuxtLink>
        </li>

        <li
          class="pt-5 px-3 lg:px-3 mt-5 border-t border-gray-200 dark:border-gray-700"
        >
          <span
            class="block text-xs uppercase text-gray-500 dark:text-gray-500"
            >Settings</span
          >
        </li>

        <!-- Settings Items -->
        <li v-for="(item, index) in settingsItems" :key="'settings-' + index">
          <NuxtLink
            :to="item.route"
            class="flex gap-x-3 py-2 px-3 text-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 dark:text-gray-200"
            :class="[
              sizeTextMenu,
              {
                'bg-gray-200 dark:bg-gray-700': isActive(item.pattern),
              },
            ]"
          >
            <component
              :is="icons[item.icon]"
              class="shrink-0 mt-0.5"
              :class="sizeIconMenu"
            />
            {{ item.label }}
          </NuxtLink>
        </li>
      </ul>
    </nav>

    <!-- Footer - Stuck at bottom -->
    <div class="mt-auto pt-3 border-t border-gray-200 dark:border-gray-700">
      <div class="space-y-1">
        <!-- System Stats Component -->
        <!-- <SystemStats :serverId="serverStore.localServerId" /> -->

        <!-- Update Button -->
        <button
          @click="handleUpdate"
          type="button"
          class="w-full flex items-center gap-x-3 py-2.5 px-3 text-sm font-medium rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800 hover:text-gray-800 dark:hover:text-gray-200"
        >
          <icons.IconRefresh
            class="size-5 shrink-0"
            :class="{ 'animate-spin': isUpdating }"
          />
          <span>{{ isUpdating ? "Updating..." : "Update LocalRun" }}</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Restarting Modal -->
  <div
    v-if="isRestarting"
    class="fixed inset-0 z-50 bg-slate-900/90 backdrop-blur-sm flex items-center justify-center"
  >
    <div class="text-center">
      <icons.IconLoader2
        class="w-16 h-16 text-blue-500 animate-spin mx-auto mb-6"
      />
      <h2 class="text-2xl font-bold text-white mb-2">Updating LocalRun...</h2>
      <p class="text-slate-400">Please wait while the application restarts.</p>
      <p class="text-slate-500 text-sm mt-4">
        This page will reload automatically.
      </p>
    </div>
  </div>
</template>
