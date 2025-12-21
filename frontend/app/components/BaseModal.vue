<script setup>
import * as icons from "@tabler/icons-vue";

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  icon: {
    type: Object,
    default: null
  },
  maxWidth: {
    type: String,
    default: 'sm:max-w-2xl'
  }
});

const emit = defineEmits(['close']);
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-[60] overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <!-- Backdrop with blur and transparency -->
      <div class="fixed inset-0 bg-gray-900/50 dark:bg-black/60 backdrop-blur-sm transition-opacity" @click="$emit('close')"></div>

      <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        <div class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full dark:bg-slate-800" :class="maxWidth">
          
          <!-- Header -->
          <div class="bg-white px-4 py-5 sm:p-6 dark:bg-slate-800">
            <!-- Title & Icon -->
            <div class="flex items-center gap-3 mb-6">
              <component v-if="icon" :is="icon" class="h-7 w-7 text-blue-600 dark:text-blue-400" stroke-width="2" />
              <h3 class="text-xl font-semibold leading-6 text-gray-900 dark:text-white" id="modal-title">
                {{ title }}
              </h3>
            </div>
                
            <!-- Content Slot -->
            <div>
              <slot></slot>
            </div>
          </div>

          <!-- Footer Slot -->
          <div v-if="$slots.footer" class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6 dark:bg-slate-800/50">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
