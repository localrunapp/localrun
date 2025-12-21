<script setup lang="ts">
import { ref, computed } from "vue";
import * as icons from "@tabler/icons-vue";

const props = defineProps<{
  visible: boolean;
  x: number;
  y: number;
  nodeType: "server" | "service" | "domain";
  nodeData: any;
}>();

const emit = defineEmits<{
  close: [];
  action: [action: string, data: any];
}>();

const menuItems = computed(() => {
  if (props.nodeType === "server") {
    return [
      { label: "Go to Server", action: "goto-server", icon: icons.IconServer },
      {
        label: "Expose Service",
        action: "expose-service",
        icon: icons.IconWorld,
      },
    ];
  } else if (props.nodeType === "service") {
    return [
      { label: "Start", action: "start", icon: icons.IconPlayerPlay },
      { label: "Stop", action: "stop", icon: icons.IconPlayerStop },
      { label: "Restart", action: "restart", icon: icons.IconRefresh },
      {
        label: "View Details",
        action: "view-details",
        icon: icons.IconFileText,
      },
    ];
  }
  return [];
});

const handleAction = (action: string) => {
  emit("action", action, props.nodeData);
  emit("close");
};
</script>

<template>
  <div
    v-if="visible"
    :style="{ left: `${x}px`, top: `${y}px` }"
    class="fixed z-50 min-w-[180px] bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1"
    @click.stop
  >
    <button
      v-for="item in menuItems"
      :key="item.action"
      @click="handleAction(item.action)"
      class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
    >
      <component :is="item.icon" class="w-4 h-4" />
      <span>{{ item.label }}</span>
    </button>
  </div>
</template>
