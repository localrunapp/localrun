<script setup>
import * as icons from "@tabler/icons-vue";
import BaseModal from "@/components/BaseModal.vue";

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  serviceName: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["close", "confirm"]);
</script>

<template>
  <BaseModal
    :isOpen="show"
    title="Delete Service"
    :icon="icons.IconAlertTriangle"
    maxWidth="sm:max-w-md"
    @close="emit('close')"
  >
    <!-- Content -->
    <p class="text-sm text-gray-600 dark:text-gray-400">
      Are you sure you want to delete
      <span class="font-semibold text-gray-900 dark:text-white">{{ serviceName }}</span>?
      This action cannot be undone.
    </p>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-end gap-3 w-full">
        <button
          type="button"
          :disabled="loading"
          @click="emit('close')"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="loading"
          @click="emit('confirm')"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            v-if="loading"
            class="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          {{ loading ? "Deleting..." : "Delete" }}
        </button>
      </div>
    </template>
  </BaseModal>
</template>
