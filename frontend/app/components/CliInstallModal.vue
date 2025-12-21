<script setup>
import * as icons from "@tabler/icons-vue";
import { useToast } from '@/composables/useToast';

const props = defineProps({
  isOpen: Boolean,
  networkIp: {
    type: String,
    default: 'localhost'
  }
});

const emit = defineEmits(['close']);

const toast = useToast();
const cliOsTab = ref('linux'); // linux, macos, windows

const cliCommand = computed(() => {
  const host = props.networkIp !== 'localhost' ? props.networkIp : 'localhost';
  const backendBase = `http://${host}:8000`;
  
  if (cliOsTab.value === 'macos') {
    return `curl -fsSL ${backendBase}/setup/install/macos | bash`;
  } else if (cliOsTab.value === 'linux') {
    return `curl -fsSL ${backendBase}/setup/install/linux | bash`;
  } else { // windows
    return `irm ${backendBase}/setup/install/windows | iex`;
  }
});

const copyCommand = () => {
  navigator.clipboard.writeText(cliCommand.value);
  toast.success('Command copied to clipboard');
};
</script>

<template>
  <BaseModal
    :isOpen="isOpen"
    title="Install LocalRun CLI"
    :icon="icons.IconDownload"
    @close="$emit('close')"
  >
    <!-- Content -->
    <div class="space-y-4">
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Install the LocalRun CLI agent to enable system monitoring and automatic server registration.
      </p>
      
      <!-- OS Tabs -->
      <div class="flex space-x-2 rounded-lg bg-gray-100 p-1 dark:bg-slate-700">
        <button
          v-for="os in ['linux', 'macos', 'windows']"
          :key="os"
          @click="cliOsTab = os"
          :class="[
            cliOsTab === os
              ? 'bg-white text-gray-900 shadow dark:bg-slate-600 dark:text-white'
              : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200',
            'flex-1 rounded-md py-1.5 text-sm font-medium capitalize'
          ]"
        >
          {{ os === 'macos' ? 'macOS' : os }}
        </button>
      </div>

      <!-- Command Box -->
      <div class="relative mt-2 rounded-md bg-slate-900 p-4">
        <code class="block whitespace-pre-wrap text-sm text-green-400 font-mono break-all">
          {{ cliCommand }}
        </code>
        <button
          @click="copyCommand"
          class="absolute right-2 top-2 rounded p-1 text-gray-400 hover:bg-white/10 hover:text-white"
          title="Copy to clipboard"
        >
          <icons.IconCopy class="h-4 w-4" />
        </button>
      </div>

      <!-- Additional Info -->
      <div class="mt-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 p-4">
        <div class="flex items-start gap-3">
          <icons.IconInfoCircle class="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
          <div class="text-sm text-blue-700 dark:text-blue-300">
            <p class="font-medium mb-1">What does the CLI agent provide?</p>
            <ul class="list-disc list-inside space-y-1 text-xs">
              <li>Real-time system monitoring (CPU, RAM, Disk)</li>
              <li>Automatic server registration</li>
              <li>Local network IP detection</li>
              <li>OS and hardware information</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <button
        type="button"
        class="inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:w-auto dark:bg-slate-700 dark:text-white dark:ring-gray-600 dark:hover:bg-slate-600"
        @click="$emit('close')"
      >
        Close
      </button>
    </template>
  </BaseModal>
</template>
