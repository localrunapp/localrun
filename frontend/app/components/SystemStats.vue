<script setup>
import { useServerStats } from "@/composables/useWsStats";
import * as icons from "@tabler/icons-vue";

// Props
const props = defineProps({
  serverId: {
    type: String,
    required: false,
    default: null
  }
});

const systemInfo = ref(null);
const systemStats = ref(null);
const agentConnected = ref(false);

const getOsIcon = () => {
  if (!systemInfo.value) return icons.IconDeviceDesktop;

  const os = systemInfo.value.os.toLowerCase();
  if (os.includes("mac") || os.includes("darwin")) {
    return icons.IconBrandApple;
  } else if (os.includes("windows")) {
    return icons.IconBrandWindows;
  } else if (os.includes("linux")) {
    return icons.IconBrandUbuntu;
  }
  return icons.IconDeviceDesktop;
};

// Only use stats composable if we have a serverId
let stats = ref(null);
let isConnected = ref(false);
let isStale = ref(true);
let startMonitoring = () => {};

if (props.serverId) {
  const statsComposable = useServerStats(props.serverId);
  stats = statsComposable.stats;
  isConnected = statsComposable.isConnected;
  isStale = statsComposable.isStale;
  startMonitoring = statsComposable.startMonitoring;
}

// Watch for stats updates
watch(stats, (newStats) => {
  if (!newStats) {
    systemStats.value = null;
    agentConnected.value = false;
    return;
  }
  
  // Update system stats
  systemStats.value = {
    cpu_percent: newStats.cpu_percent,
    memory_percent: newStats.memory_percent,
    disk_percent: newStats.disk_percent,
  };

  // Update system info
  systemInfo.value = {
    os: newStats.os_name || "Unknown",
    os_version: newStats.os_version || "",
    cpu_cores: newStats.cpu_cores || 0,
    memory_gb: newStats.memory_gb || 0,
    disk_gb: newStats.disk_gb || 0,
    local_ip: newStats.local_ip || "",
  };

  agentConnected.value = true;
}, { immediate: true });

watch(isConnected, (connected) => {
  if (!connected) {
    agentConnected.value = false;
  }
});

onMounted(() => {
  if (import.meta.client && props.serverId) {
    // Start WebSocket monitoring only if we have a serverId
    setTimeout(() => {
      startMonitoring();
    }, 500);
  }
});
</script>

<template>
  <!-- Show message when no serverId (CLI agent not installed) -->
  <div v-if="!serverId" class="bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800 shadow-sm p-4">
    <div class="flex items-start gap-3">
      <icons.IconAlertCircle class="size-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
      <div class="flex-1">
        <h3 class="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-1">
          CLI Agent Not Installed
        </h3>
        <p class="text-xs text-amber-700 dark:text-amber-300">
          Install the LocalRun CLI agent to monitor system stats.
        </p>
      </div>
    </div>
  </div>

  <!-- Show stats when serverId is available -->
  <div v-else-if="systemInfo" class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col overflow-hidden">
    <!-- Header: Icon + Name + Status -->
    <div class="p-3 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <component
          :is="getOsIcon()"
          class="size-5 text-slate-600 dark:text-slate-300"
        />
        <div class="flex flex-col">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate max-w-[150px]">
            {{ systemInfo.os }}
            </span>
            <span class="text-[10px] text-slate-400 dark:text-slate-500 font-mono" v-if="systemInfo.local_ip">
                {{ systemInfo.local_ip }}
            </span>
        </div>
      </div>
      
      <span
        class="shrink-0 px-1.5 py-0.5 text-[10px] uppercase tracking-wider rounded font-bold"
        :class="
          agentConnected
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
            : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
        "
      >
        {{ agentConnected ? "Online" : "Offline" }}
      </span>
    </div>

    <!-- Footer: Stats -->
    <div class="mt-auto border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
        <div class="grid grid-cols-3 divide-x divide-slate-200 dark:divide-slate-700">
            <!-- CPU -->
            <div class="p-2 flex flex-col items-center justify-center gap-1.5">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">CPU</div>
                <div class="w-full px-1">
                    <div class="flex justify-center items-end mb-1">
                        <span class="text-xs font-bold text-slate-700 dark:text-slate-200" v-if="systemStats">{{ systemStats.cpu_percent }}%</span>
                        <span class="text-xs font-bold text-slate-400" v-else>-</span>
                    </div>
                    <div class="h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden w-full">
                        <div
                            v-if="systemStats"
                            class="h-full bg-blue-500 rounded-full transition-all duration-500"
                            :style="{ width: `${systemStats.cpu_percent}%` }"
                        ></div>
                    </div>
                </div>
            </div>
            <!-- RAM -->
            <div class="p-2 flex flex-col items-center justify-center gap-1.5">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">RAM</div>
                <div class="w-full px-1">
                    <div class="flex justify-center items-end mb-1">
                        <span class="text-xs font-bold text-slate-700 dark:text-slate-200" v-if="systemStats">{{ systemStats.memory_percent }}%</span>
                        <span class="text-xs font-bold text-slate-400" v-else>-</span>
                    </div>
                    <div class="h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden w-full">
                        <div
                            v-if="systemStats"
                            class="h-full bg-purple-500 rounded-full transition-all duration-500"
                            :style="{ width: `${systemStats.memory_percent}%` }"
                        ></div>
                    </div>
                </div>
            </div>
            <!-- DISK -->
            <div class="p-2 flex flex-col items-center justify-center gap-1.5">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">HDD</div>
                <div class="w-full px-1">
                    <div class="flex justify-center items-end mb-1">
                        <span class="text-xs font-bold text-slate-700 dark:text-slate-200" v-if="systemStats">{{ systemStats.disk_percent }}%</span>
                        <span class="text-xs font-bold text-slate-400" v-else>-</span>
                    </div>
                    <div class="h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden w-full">
                        <div
                            v-if="systemStats"
                            class="h-full bg-amber-500 rounded-full transition-all duration-500"
                            :style="{ width: `${systemStats.disk_percent}%` }"
                        ></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </div>
</template>
