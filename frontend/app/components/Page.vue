<script setup></script>
<template>
  <div class="flex flex-col h-full">
    <!-- Page Header (inside white container) -->
    <div
      v-if="$slots.header"
      class="py-2 px-4 flex-shrink-0 border-b border-gray-200 dark:border-gray-700"
    >
      <slot name="header" />
    </div>

    <!-- Scrollable Content Area -->
    <div
      class="flex-1 overflow-y-auto [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-gray-100 [&::-webkit-scrollbar-thumb]:bg-gray-300 dark:[&::-webkit-scrollbar-track]:bg-gray-700 dark:[&::-webkit-scrollbar-thumb]:bg-gray-500"
    >
      <slot />
    </div>

    <slot name="modals" />
  </div>
</template>
