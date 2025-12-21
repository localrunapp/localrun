<script setup>
import { computed, onMounted, onUnmounted } from "vue";
import * as icons from "@tabler/icons-vue";
import { useServerStats } from "@/composables/useWsStats";

const props = defineProps({
  server: {
    type: Object,
    required: true,
  },
  formattedHost: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["install", "scan", "review"]);

// Initialize per-server socket connection
const { stats, agentStatus, startMonitoring, stopMonitoring } = useServerStats(
  props.server.id
);

// Start monitoring when component mounts
onMounted(() => {
  startMonitoring();
});

// Clean up when component unmounts
onUnmounted(() => {
  stopMonitoring();
});

// Computed agent status (fallback to prop if not yet available from socket)
const currentStatus = computed(() => {
  return agentStatus.value || props.server.agent_status;
});

// Get OS-specific icon based on server stats or OS type
const osIcon = computed(() => {
  const osName =
    stats.value?.os_name?.toLowerCase() ||
    props.server.os_name?.toLowerCase() ||
    "";

  // Check for macOS/Darwin
  if (
    osName.includes("darwin") ||
    osName.includes("macos") ||
    osName.includes("mac os")
  ) {
    return icons.IconBrandApple;
  }

  // Check for Windows
  if (osName.includes("windows")) {
    return icons.IconBrandWindows;
  }

  // Check for Linux
  if (
    osName.includes("linux") ||
    osName.includes("ubuntu") ||
    osName.includes("debian") ||
    osName.includes("centos") ||
    osName.includes("fedora") ||
    osName.includes("arch")
  ) {
    return icons.IconBrandUbuntu;
  }

  // Fallback to generic server/laptop icon
  return props.server.is_local ? icons.IconDeviceLaptop : icons.IconServer;
});

const openTerminal = () => {
  const url = `/servers/${props.server.id}/terminal?minimal=true`;
  window.open(
    url,
    `Terminal-${props.server.id}`,
    "width=900,height=600,menubar=no,toolbar=no,location=no,status=no"
  );
};
</script>

<template>
  <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
    <!-- Name Column: OS Icon + Name + IP -->
    <td class="px-6 py-4">
      <div class="flex items-center gap-3">
        <!-- Large OS Icon -->
        <div class="flex-shrink-0">
          <component
            :is="osIcon"
            class="w-8 h-8 text-gray-400 dark:text-gray-500"
          />
        </div>
        <!-- Name + IP -->
        <div class="flex flex-col">
          <span class="text-sm font-medium text-gray-800 dark:text-gray-200">
            {{ server.name }}
          </span>
          <span class="text-xs text-gray-500 dark:text-gray-400 font-mono">
            <template v-if="server.is_local">
              {{ formattedHost }}
              <span
                v-if="
                  server.network_ip &&
                  !formattedHost.includes(server.network_ip)
                "
                class="text-gray-400 dark:text-gray-500"
              >
                / {{ server.network_ip }}
              </span>
            </template>
            <template v-else>
              {{ server.network_ip || formattedHost }}
            </template>
          </span>
        </div>
      </div>
    </td>

    <!-- Hardware Stats Column: CPU, RAM, HDD, IOPS -->
    <td class="px-6 py-4">
      <!-- Loading State: Connected but no stats yet -->
      <div
        v-if="currentStatus === 'connected' && !stats"
        class="flex items-center gap-2 text-gray-400"
      >
        <icons.IconLoader2 class="w-4 h-4 animate-spin" />
        <span class="text-xs">Loading stats...</span>
      </div>

      <!-- Stats Available -->
      <div
        v-else-if="stats"
        class="grid grid-cols-2 xl:grid-cols-4 gap-3 max-w-[480px]"
      >
        <!-- CPU -->
        <div class="flex flex-col gap-1">
          <div
            class="flex justify-between text-[10px] text-gray-500 dark:text-gray-400"
          >
            <span>CPU</span>
            <span>{{ stats.cpu_percent }}%</span>
          </div>
          <div
            class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
          >
            <div
              class="h-full bg-blue-500 rounded-full transition-all duration-500"
              :style="{ width: `${stats.cpu_percent}%` }"
            ></div>
          </div>
        </div>
        <!-- RAM -->
        <div class="flex flex-col gap-1">
          <div
            class="flex justify-between text-[10px] text-gray-500 dark:text-gray-400"
          >
            <span>RAM</span>
            <span>{{ stats.memory_percent }}%</span>
          </div>
          <div
            class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
          >
            <div
              class="h-full bg-purple-500 rounded-full transition-all duration-500"
              :style="{ width: `${stats.memory_percent}%` }"
            ></div>
          </div>
        </div>

        <!-- IOPS -->
        <div
          class="flex flex-col gap-1"
          v-if="stats.disk_read_ops !== undefined"
        >
          <div
            class="flex justify-between text-[10px] text-gray-500 dark:text-gray-400"
          >
            <span>I/O</span>
            <span>{{
              (stats.disk_read_ops || 0) + (stats.disk_write_ops || 0)
            }}</span>
          </div>
          <div
            class="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
          >
            <div
              class="h-full bg-green-500 rounded-full transition-all duration-500"
              :style="{
                width: `${Math.min(
                  ((stats.disk_read_ops || 0) + (stats.disk_write_ops || 0)) /
                    10,
                  100
                )}%`,
              }"
            ></div>
          </div>
        </div>
      </div>

      <!-- No Stats Available (Disconnected or Error) -->
      <span
        v-else
        class="inline-flex items-center gap-1.5 py-1 px-2 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
      >
        No stats available
      </span>
    </td>

    <!-- CLI Agent Status Column -->
    <td class="px-6 py-4 whitespace-nowrap text-sm">
      <!-- Connected -->
      <span
        v-if="currentStatus === 'connected'"
        class="inline-flex items-center gap-1.5 py-0.5 px-2 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
      >
        <span class="w-1.5 h-1.5 inline-block bg-green-400 rounded-full"></span>
        Connected
      </span>
      <!-- Disconnected -->
      <span
        v-else-if="currentStatus === 'disconnected'"
        class="inline-flex items-center gap-1.5 py-0.5 px-2 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
      >
        <span
          class="w-1.5 h-1.5 inline-block bg-yellow-400 rounded-full"
        ></span>
        Disconnected
      </span>
      <!-- Not Installed -->
      <button
        v-else
        @click="$emit('install')"
        class="inline-flex items-center gap-1.5 py-0.5 px-2 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
      >
        <icons.IconDownload class="w-3 h-3" />
        Install
      </button>
    </td>

    <!-- Actions Column -->
    <td class="px-6 py-4 whitespace-nowrap text-end text-sm font-medium">
      <div class="flex items-center justify-end gap-2">
        <!-- Terminal Button (Teleport/Popup) -->
        <button
          v-if="currentStatus === 'connected'"
          @click="openTerminal"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700"
          title="Open Terminal"
        >
          <icons.IconTerminal2 class="w-3.5 h-3.5" />
          Terminal
        </button>

        <!-- Scan Services Button -->
        <button
          @click="$emit('scan')"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <icons.IconScan class="w-3.5 h-3.5" />
          Scan Services
        </button>
        <!-- Review Button -->
        <button
          @click="$emit('review')"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          <icons.IconEye class="w-3.5 h-3.5" />
          Review
        </button>
      </div>
    </td>
  </tr>
</template>
