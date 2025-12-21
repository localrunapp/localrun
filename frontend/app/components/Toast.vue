<template>
  <Teleport to="body">
    <div v-for="(toasts, position) in toastStore.toasts" :key="position"
      :class="['fixed z-[10000] space-y-2', positionClass(position)]">
      <TransitionGroup name="toast" tag="div" class="space-y-2" appear>
        <div v-for="toast in toasts" :key="toast.id" :class="[
          'max-w-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg p-4',
          toast.type === 'error' ? 'border-l-4 border-l-red-500' : '',
          toast.type === 'success' ? 'border-l-4 border-l-green-500' : '',
          toast.type === 'warning' ? 'border-l-4 border-l-yellow-500' : '',
          toast.type === 'info' ? 'border-l-4 border-l-blue-500' : '',
        ]">
          <div class="flex items-start">
            <div class="flex-1">
              <h3 v-if="toast.title" class="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                {{ toast.title }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-300">
                {{ toast.message }}
              </p>
            </div>
            <button @click="toastStore.remove(toast.id)"
              class="ml-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
              <i class="ti ti-x text-lg"></i>
            </button>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToastStore } from "@/stores/toast";

const toastStore = useToastStore();

function positionClass(position) {
  return (
    {
      "top-right": "top-5 right-5",
      "top-left": "top-5 left-5",
      "top-center": "top-5 left-1/2 -translate-x-1/2",
      "bottom-right": "bottom-5 right-5",
      "bottom-left": "bottom-5 left-5",
      "bottom-center": "bottom-5 left-1/2 -translate-x-1/2",
    }[position] || "top-5 right-5"
  );
}
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease-out;
}

.toast-leave-active {
  transition: all 0.3s ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
