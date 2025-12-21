<script setup>
import { ref, computed } from 'vue';
import * as icons from "@tabler/icons-vue";
import { useToast } from '@/composables/useToast';

const props = defineProps({
  isOpen: Boolean,
  networkIp: {
    type: String,
    default: 'localhost'
  }
});

const emit = defineEmits(['close', 'register']);

const toast = useToast();
const activeTab = ref('manual'); // manual, cli
const cliOsTab = ref('linux'); // linux, macos, windows

// Manual Registration Form
const form = ref({
  name: '',
  host: '',
  description: ''
});

const loading = ref(false);

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

const handleRegister = async () => {
  if (!form.value.name || !form.value.host) {
    toast.error('Name and Host are required');
    return;
  }

  loading.value = true;
  try {
    emit('register', { ...form.value });
    form.value = { name: '', host: '', description: '' }; // Reset
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <BaseModal
    :isOpen="isOpen"
    title="Register Server"
    :icon="icons.IconServer"
    @close="$emit('close')"
  >
    <!-- Tabs -->
    <div class="border-b border-gray-200 dark:border-gray-700">
      <nav class="-mb-px flex space-x-8" aria-label="Tabs">
        <button
          @click="activeTab = 'manual'"
          :class="[
            activeTab === 'manual'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300',
            'whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium'
          ]"
        >
          Manual Registration
        </button>
        <button
          @click="activeTab = 'cli'"
          :class="[
            activeTab === 'cli'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300',
            'whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium'
          ]"
        >
          Register with CLI
        </button>
      </nav>
    </div>

    <!-- Content -->
    <div class="mt-6">
      <!-- Manual Form -->
      <div v-if="activeTab === 'manual'" class="space-y-4">
        <div>
          <label for="name" class="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">Name</label>
          <div class="mt-2">
            <input v-model="form.name" type="text" name="name" id="name" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 dark:bg-slate-700 dark:text-white dark:ring-gray-600" placeholder="My Server">
          </div>
        </div>
        <div>
          <label for="host" class="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">Host / IP</label>
          <div class="mt-2">
            <input v-model="form.host" type="text" name="host" id="host" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 dark:bg-slate-700 dark:text-white dark:ring-gray-600" placeholder="192.168.1.100">
          </div>
        </div>
        <div>
          <label for="description" class="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">Description (Optional)</label>
          <div class="mt-2">
            <textarea v-model="form.description" id="description" name="description" rows="3" class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 dark:bg-slate-700 dark:text-white dark:ring-gray-600"></textarea>
          </div>
        </div>
      </div>

      <!-- CLI Instructions -->
      <div v-else class="space-y-4">
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Install the LocalRun CLI on your server to automatically register it and enable advanced monitoring.
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
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <button
        v-if="activeTab === 'manual'"
        type="button"
        class="inline-flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 sm:ml-3 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="loading"
        @click="handleRegister"
      >
        <icons.IconLoader2 v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4" />
        Register
      </button>
      <button
        type="button"
        class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto dark:bg-slate-700 dark:text-white dark:ring-gray-600 dark:hover:bg-slate-600"
        @click="$emit('close')"
      >
        {{ activeTab === 'cli' ? 'Close' : 'Cancel' }}
      </button>
    </template>
  </BaseModal>
</template>
