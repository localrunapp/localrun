<script setup lang="ts">
import { computed } from 'vue';
import * as icons from '@tabler/icons-vue';

interface ServerStats {
  cpu_percent?: number;
  memory_percent?: number;
  disk_read_ops?: number;
  disk_write_ops?: number;
  os_name?: string;
}

const props = defineProps<{
  name: string;
  serviceCount?: number;
  osName?: string;
  isLocal?: boolean;
  stats?: ServerStats;
}>();

// Get OS-specific icon
const osIcon = computed(() => {
  const osName = props.stats?.os_name?.toLowerCase() || props.osName?.toLowerCase() || '';
  
  // macOS/Darwin
  if (osName.includes('darwin') || osName.includes('macos') || osName.includes('mac os')) {
    return icons.IconBrandApple;
  }
  
  // Windows
  if (osName.includes('windows')) {
    return icons.IconBrandWindows;
  }
  
  // Linux
  if (osName.includes('linux') || osName.includes('ubuntu') || osName.includes('debian') || 
      osName.includes('centos') || osName.includes('fedora') || osName.includes('arch')) {
    return icons.IconBrandUbuntu;
  }
  
  // Fallback
  return props.isLocal ? icons.IconDeviceLaptop : icons.IconServer;
});
</script>

<template>
  <g>
    <!-- Shadow (right and bottom only) -->
    <rect
      x="3"
      y="3"
      width="220"
      height="140"
      rx="8"
      class="fill-gray-400/20 dark:fill-black/40"
    />
    
    <!-- Card background -->
    <rect
      width="220"
      height="140"
      rx="8"
      class="fill-white dark:fill-gray-800 stroke-gray-300 dark:stroke-gray-600 transition-all duration-200 cursor-move"
      stroke-width="1"
    />
    
    <!-- Header -->
    <rect
      width="220"
      height="35"
      rx="8"
      class="fill-blue-500 dark:fill-blue-600"
    />
    <rect
      y="8"
      width="220"
      height="27"
      class="fill-blue-500 dark:fill-blue-600"
    />
    
    <!-- Type badge in header -->
    <text
      x="10"
      y="22"
      class="fill-white text-xs font-bold"
      style="font-size: 10px"
    >
      SERVER
    </text>
    
    <!-- Service count badge -->
    <circle
      v-if="serviceCount !== undefined"
      cx="195"
      cy="18"
      r="12"
      class="fill-blue-400 dark:fill-blue-700"
    />
    <text
      v-if="serviceCount !== undefined"
      x="195"
      y="22"
      text-anchor="middle"
      class="fill-white text-xs font-bold"
      style="font-size: 11px"
    >
      {{ serviceCount }}
    </text>
    
    <!-- Body -->
    <!-- OS Icon -->
    <foreignObject x="85" y="45" width="50" height="50">
      <div xmlns="http://www.w3.org/1999/xhtml" class="flex items-center justify-center w-full h-full">
        <component :is="osIcon" class="w-10 h-10 text-blue-400 dark:text-blue-500" />
      </div>
    </foreignObject>
    
    <!-- Server name -->
    <text
      x="110"
      y="110"
      text-anchor="middle"
      class="fill-gray-800 dark:fill-gray-200 font-semibold"
      style="font-size: 13px"
    >
      {{ name.length > 20 ? name.substring(0, 17) + "..." : name }}
    </text>
    
    <!-- Stats (if available) -->
    <g v-if="stats">
      <!-- CPU -->
      <text x="10" y="130" class="fill-gray-600 dark:fill-gray-400" style="font-size: 9px">CPU</text>
      <rect x="30" y="123" width="50" height="4" rx="2" class="fill-gray-200 dark:fill-gray-700" />
      <rect x="30" y="123" :width="(stats.cpu_percent || 0) * 0.5" height="4" rx="2" class="fill-blue-500" />
      <text x="85" y="130" class="fill-gray-600 dark:fill-gray-400" style="font-size: 9px">{{ stats.cpu_percent || 0 }}%</text>
      
      <!-- RAM -->
      <text x="110" y="130" class="fill-gray-600 dark:fill-gray-400" style="font-size: 9px">RAM</text>
      <rect x="135" y="123" width="50" height="4" rx="2" class="fill-gray-200 dark:fill-gray-700" />
      <rect x="135" y="123" :width="(stats.memory_percent || 0) * 0.5" height="4" rx="2" class="fill-purple-500" />
      <text x="190" y="130" class="fill-gray-600 dark:fill-gray-400" style="font-size: 9px">{{ stats.memory_percent || 0 }}%</text>
    </g>
    <text
      v-else
      x="110"
      y="130"
      text-anchor="middle"
      class="fill-gray-600 dark:fill-gray-400 text-xs"
      style="font-size: 10px"
    >
      {{ serviceCount !== undefined ? `${serviceCount} service${serviceCount !== 1 ? 's' : ''}` : 'No stats' }}
    </text>
  </g>
</template>
