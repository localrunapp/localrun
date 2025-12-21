<script setup lang="ts">
const props = defineProps<{
  name: string;
  recordType?: string;
}>();
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
      class="fill-purple-500 dark:fill-purple-600"
    />
    <rect
      y="8"
      width="200"
      height="27"
      class="fill-purple-500 dark:fill-purple-600"
    />
    
    <!-- Type badge in header -->
    <text
      x="10"
      y="22"
      class="fill-white text-xs font-bold"
      style="font-size: 10px"
    >
      DOMAIN
    </text>
    
    <!-- Record type badge -->
    <text
      v-if="recordType"
      x="190"
      y="22"
      text-anchor="end"
      class="fill-purple-200 dark:fill-purple-300 text-xs font-medium"
      style="font-size: 9px"
    >
      {{ recordType }}
    </text>
    
    <!-- Body -->
    <!-- Globe icon -->
    <circle
      cx="100"
      cy="65"
      r="18"
      class="fill-purple-100 dark:fill-purple-900/30 stroke-purple-400 dark:stroke-purple-500"
      stroke-width="1.5"
    />
    <circle
      cx="100"
      cy="65"
      r="12"
      class="stroke-purple-500 dark:stroke-purple-400 fill-none"
      stroke-width="1.5"
    />
    <ellipse
      cx="100"
      cy="65"
      rx="6"
      ry="12"
      class="stroke-purple-500 dark:stroke-purple-400 fill-none"
      stroke-width="1"
    />
    <line
      x1="88"
      y1="65"
      x2="112"
      y2="65"
      class="stroke-purple-500 dark:stroke-purple-400"
      stroke-width="1"
    />
    
    <!-- Domain name -->
    <text
      x="100"
      y="100"
      text-anchor="middle"
      class="fill-gray-800 dark:fill-gray-200 font-semibold"
      style="font-size: 11px"
    >
      {{ name.length > 24 ? name.substring(0, 21) + "..." : name }}
    </text>
    
    <!-- DNS label -->
    <text
      x="100"
      y="113"
      text-anchor="middle"
      class="fill-gray-600 dark:fill-gray-400 text-xs"
      style="font-size: 9px"
    >
      DNS Domain
    </text>
  </g>
</template>
