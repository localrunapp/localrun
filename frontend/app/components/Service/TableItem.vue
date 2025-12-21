<script setup>
import { ref, watch } from "vue";
import * as icons from "@tabler/icons-vue";
import DeleteModal from "@/components/Service/DeleteModal.vue";

const props = defineProps({
  service: {
    type: Object,
    required: true,
  },
  servers: {
    type: Array,
    default: () => [],
  },
});


const emit = defineEmits(["start", "stop", "delete"]);

// Loading states
const isStarting = ref(false);
const isStopping = ref(false);
const isDeleting = ref(false);

// Delete modal
const showDeleteModal = ref(false);

// Watch for service status changes to reset loading states
watch(() => props.service.status, (newStatus, oldStatus) => {
  if (oldStatus !== newStatus) {
    // Reset loading states when status changes
    isStarting.value = false;
    isStopping.value = false;
  }
});

// Handle actions with loading states
const handleStart = async () => {
  isStarting.value = true;
  emit("start", props.service);
};

const handleStop = async () => {
  isStopping.value = true;
  emit("stop", props.service);
};

const handleDeleteClick = () => {
  showDeleteModal.value = true;
};

const handleDeleteConfirm = () => {
  isDeleting.value = true;
  emit("delete", props.service);
  showDeleteModal.value = false;
  setTimeout(() => {
    isDeleting.value = false;
  }, 2000);
};


// Find server for this service
const server = computed(() => {
  return props.servers.find(s => s.id === props.service.server_id);
});

// Provider display name
const providerName = computed(() => {
  const key = props.service.provider_key;
  if (key === 'cloudflare') return 'Cloudflare';
  if (key === 'pinggy') return 'Pinggy';
  return key;
});

// Status color
const statusColor = computed(() => {
  if (props.service.status === 'running') return 'green';
  if (props.service.status === 'stopped') return 'gray';
  return 'yellow';
});
</script>

<template>
  <tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50">
    <!-- Service Column -->
    <td class="px-6 py-4">
      <div class="flex flex-col gap-1">
        <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
          {{ service.name }}
        </span>
        <a
          v-if="service.public_url"
          :href="service.public_url"
          target="_blank"
          class="text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
        >
          {{ service.public_url }}
          <icons.IconExternalLink class="w-3 h-3" />
        </a>
        <span v-else class="text-xs text-gray-500 dark:text-gray-400">
          No public URL
        </span>
      </div>
    </td>

    <!-- Server:Port Column -->
    <td class="px-6 py-4">
      <div class="flex flex-col gap-1.5">
        <span
          v-if="server"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 w-fit"
        >
          <icons.IconServer class="w-3 h-3" />
          {{ server.name }}
        </span>
        <span
          v-else
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 w-fit"
        >
          <icons.IconAlertCircle class="w-3 h-3" />
          No server
        </span>
        <span class="text-xs text-gray-600 dark:text-gray-400 font-mono">
          {{ service.protocol.toUpperCase() }} : {{ service.host }}:{{ service.port }}
        </span>
      </div>
    </td>

    <!-- Provider Column -->
    <td class="px-6 py-4">
      <span
        class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
      >
        {{ providerName }}
      </span>
    </td>

    <!-- Status Column -->
    <td class="px-6 py-4">
      <span
        :class="[
          'inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium',
          statusColor === 'green'
            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
            : statusColor === 'gray'
            ? 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        ]"
      >
        <span
          :class="[
            'w-1.5 h-1.5 rounded-full',
            statusColor === 'green'
              ? 'bg-green-500'
              : statusColor === 'gray'
              ? 'bg-gray-400'
              : 'bg-yellow-500',
          ]"
        ></span>
        {{ service.status }}
      </span>
    </td>

    <!-- Metrics Column -->
    <td class="px-6 py-4 text-center">
      <icons.IconCheck
        v-if="service.enable_analytics"
        class="w-5 h-5 text-green-500 mx-auto"
        title="Analytics Enabled"
      />
      <icons.IconX v-else class="w-5 h-5 text-gray-400 mx-auto" title="Analytics Disabled" />
    </td>

    <!-- Password Column -->
    <td class="px-6 py-4 text-center">
      <icons.IconLock
        v-if="service.tunnel_password"
        class="w-5 h-5 text-blue-500 mx-auto"
        title="Password Protected"
      />
      <icons.IconLockOpen v-else class="w-5 h-5 text-gray-400 mx-auto" title="No Password" />
    </td>

    <!-- Actions Column -->
    <td class="px-6 py-4">
      <div class="flex items-center gap-2">
        <!-- Action Group -->
        <div class="inline-flex items-center rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <!-- Start/Stop Button -->
          <button
            v-if="service.status === 'stopped' || service.status === 'error'"
            @click="handleStart"
            :disabled="isStarting"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-green-800 bg-green-100 hover:bg-green-200 dark:bg-green-800 dark:text-green-300 dark:hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed border-r border-gray-200 dark:border-gray-700"
            title="Start"
          >
            <icons.IconLoader2 v-if="isStarting" class="w-4 h-4 animate-spin" />
            <icons.IconPlayerPlay v-else class="w-4 h-4" />
          </button>
          <button
            v-else-if="service.status === 'running'"
            @click="handleStop"
            :disabled="isStopping"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-red-800 bg-red-100 hover:bg-red-200 dark:bg-red-800 dark:text-red-300 dark:hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed border-r border-gray-200 dark:border-gray-700"
            title="Stop"
          >
            <icons.IconLoader2 v-if="isStopping" class="w-4 h-4 animate-spin" />
            <icons.IconPlayerStop v-else class="w-4 h-4" />
          </button>

          <!-- Delete Button -->
          <button
            @click="handleDeleteClick"
            :disabled="isDeleting"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Delete"
          >
            <icons.IconLoader2 v-if="isDeleting" class="w-4 h-4 animate-spin" />
            <icons.IconTrash v-else class="w-4 h-4" />
          </button>
        </div>

        <!-- View Details Button -->
        <NuxtLink
          :to="`/services/${service.id}`"
          class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800 rounded-lg border border-blue-200 dark:border-blue-700 transition-colors"
          title="View Details"
        >
          <icons.IconEye class="w-4 h-4" />
        </NuxtLink>
      </div>
    </td>
  </tr>

  <!-- Delete Confirmation Modal -->
  <DeleteModal
    :show="showDeleteModal"
    :service-name="service.name"
    :loading="isDeleting"
    @close="showDeleteModal = false"
    @confirm="handleDeleteConfirm"
  />
</template>
```
