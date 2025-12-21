<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  name: string;
  protocol: string;
  port: number;
  status: string;
  publicUrl?: string;
}>();

const isRunning = computed(() => props.status === "running");
</script>

<template>
  <g>
    <!-- Shadow (right and bottom only) -->
    <rect
      x="3"
      y="3"
      width="200"
      height="120"
      rx="8"
      class="fill-gray-400/20 dark:fill-black/40"
    />
    
    <!-- Card background -->
    <rect
      width="200"
      height="120"
      rx="8"
      class="fill-white dark:fill-gray-800 stroke-gray-300 dark:stroke-gray-600 cursor-move"
      stroke-width="1"
    />
    
    <!-- Header -->
    <rect
      width="200"
      height="35"
      rx="8"
      :class="
        isRunning
          ? 'fill-green-500 dark:fill-green-600'
          : 'fill-gray-500 dark:fill-gray-600'
      "
    />
    <rect
      y="8"
      width="200"
      height="27"
      :class="
        isRunning
          ? 'fill-green-500 dark:fill-green-600'
          : 'fill-gray-500 dark:fill-gray-600'
      "
    />
    
    <!-- Type badge in header -->
    <text
      x="10"
      y="22"
      class="fill-white text-xs font-bold"
      style="font-size: 10px"
    >
      SERVICE
    </text>
    
    <!-- Status indicator -->
    <circle
      cx="175"
      cy="18"
      r="6"
      :class="isRunning ? 'fill-green-300' : 'fill-gray-300'"
    />
    
    <!-- Body -->
    <!-- Service name -->
    <text
      x="10"
      y="55"
      class="fill-gray-800 dark:fill-gray-200 font-semibold"
      style="font-size: 13px"
    >
      {{ name.length > 20 ? name.substring(0, 17) + "..." : name }}
    </text>
    
    <!-- Protocol badge -->
    <rect
      x="10"
      y="63"
      width="85"
      height="20"
      rx="4"
      :class="
        isRunning
          ? 'fill-green-100 dark:fill-green-900/30'
          : 'fill-gray-100 dark:fill-gray-700'
      "
    />
    <text
      x="52"
      y="77"
      text-anchor="middle"
      :class="
        isRunning
          ? 'fill-green-700 dark:fill-green-300'
          : 'fill-gray-700 dark:fill-gray-300'
      "
      class="text-xs font-medium"
      style="font-size: 11px"
    >
      {{ protocol.toUpperCase() }} : {{ port }}
    </text>
    
    <!-- Status text -->
    <text
      x="10"
      y="100"
      :class="
        isRunning
          ? 'fill-green-600 dark:fill-green-400'
          : 'fill-gray-600 dark:fill-gray-400'
      "
      class="text-xs font-medium"
      style="font-size: 10px"
    >
      {{ status }}
    </text>
    
    <!-- Public URL if exists -->
    <text
      v-if="publicUrl"
      x="10"
      y="113"
      class="fill-gray-500 dark:fill-gray-400 text-xs"
      style="font-size: 9px"
    >
      {{
        publicUrl.length > 26 ? publicUrl.substring(0, 23) + "..." : publicUrl
      }}
    </text>
  </g>
</template>
