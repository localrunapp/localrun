<script setup>
import { useLogsStream } from "@/composables/useLogsStream";
import * as icons from "@tabler/icons-vue";

const { 
  filteredLogs, 
  isConnected, 
  categoryFilter, 
  levelFilter, 
  serverFilter,
  clearLogs 
} = useLogsStream();

const autoScroll = ref(true);
const expandedLog = ref(null);

// Level badge colors
const levelColors = {
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
};

// Category badge colors
const categoryColors = {
  metrics: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  websocket: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  services: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
  backend: 'bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-400',
  agents: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400'
};

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

function toggleExpand(logId) {
  expandedLog.value = expandedLog.value === logId ? null : logId;
}

// Auto-scroll to bottom when new logs arrive
watch(filteredLogs, () => {
  if (autoScroll.value) {
    nextTick(() => {
      const container = document.getElementById('logs-container');
      if (container) {
        container.scrollTop = 0; // Scroll to top since newest is first
      }
    });
  }
});
</script>

<template>
  <Page>
    <template #header>
      <PageHeader
        :icon="icons.IconFileText"
        title="System Logs"
        subtitle="Real-time system logs with filtering"
        backPath="/"
      >
        <template #actions>
          <!-- Connection status -->
          <div class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg bg-slate-100 dark:bg-slate-800">
            <div 
              class="w-2 h-2 rounded-full"
              :class="isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'"
            ></div>
            <span class="text-slate-600 dark:text-slate-300">
              {{ isConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>

          <!-- Clear logs -->
          <button
            @click="clearLogs"
            class="p-2 text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 "
            title="Clear logs"
          >
            <icons.IconTrash class="w-5 h-5" />
          </button>
        </template>
      </PageHeader>
    </template>

    <!-- Filters -->
    <div class="mb-4 flex flex-wrap gap-3 items-center">
      <!-- Category filter -->
      <div class="flex items-center gap-2">
        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Category:</label>
        <select 
          v-model="categoryFilter"
          class="px-3 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300"
        >
          <option value="all">All</option>
          <option value="agents">Agents</option>
          <option value="metrics">Metrics</option>
          <option value="websocket">WebSocket</option>
          <option value="services">Services</option>
          <option value="backend">Backend</option>
        </select>
      </div>

      <!-- Level filter -->
      <div class="flex items-center gap-2">
        <label class="text-sm font-medium text-slate-700 dark:text-slate-300">Level:</label>
        <select 
          v-model="levelFilter"
          class="px-3 py-1.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300"
        >
          <option value="all">All</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
        </select>
      </div>

      <!-- Auto-scroll toggle -->
      <label class="flex items-center gap-2 cursor-pointer">
        <input 
          type="checkbox" 
          v-model="autoScroll"
          class="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
        >
        <span class="text-sm text-slate-700 dark:text-slate-300">Auto-scroll</span>
      </label>

      <!-- Log count -->
      <div class="ml-auto text-sm text-slate-500 dark:text-slate-400">
        {{ filteredLogs.length }} logs
      </div>
    </div>

    <!-- Logs table -->
    <div 
      id="logs-container"
      class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden"
    >
      <div class="overflow-x-auto max-h-[calc(100vh-300px)] overflow-y-auto">
        <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
          <thead class="bg-slate-50 dark:bg-slate-800 sticky top-0 z-10">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Timestamp
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Category
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Level
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Server
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Message
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-700">
            <template v-if="filteredLogs.length === 0">
              <tr>
                <td colspan="6" class="px-4 py-8 text-center text-sm text-slate-500 dark:text-slate-400">
                  No logs to display
                </td>
              </tr>
            </template>
            <template v-else>
              <template v-for="log in filteredLogs" :key="log.id">
                <!-- Main row -->
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50 ">
                  <td class="px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400 whitespace-nowrap">
                    {{ formatTimestamp(log.timestamp) }}
                  </td>
                  <td class="px-4 py-3">
                    <span 
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                      :class="categoryColors[log.category] || categoryColors.backend"
                    >
                      {{ log.category }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <span 
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase"
                      :class="levelColors[log.level] || levelColors.info"
                    >
                      {{ log.level }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                    {{ log.server_name || log.server_id || '-' }}
                  </td>
                  <td class="px-4 py-3 text-sm text-slate-700 dark:text-slate-300">
                    {{ log.message }}
                  </td>
                  <td class="px-4 py-3">
                    <button
                      v-if="log.metadata && Object.keys(log.metadata).length > 0"
                      @click="toggleExpand(log.id)"
                      class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    >
                      <icons.IconChevronDown 
                        class="w-4 h-4 transition-transform"
                        :class="{ 'rotate-180': expandedLog === log.id }"
                      />
                    </button>
                  </td>
                </tr>
                
                <!-- Expanded metadata row -->
                <tr v-if="expandedLog === log.id" class="bg-slate-50 dark:bg-slate-800/30">
                  <td colspan="6" class="px-4 py-3">
                    <div class="text-xs font-mono text-slate-600 dark:text-slate-400">
                      <pre class="whitespace-pre-wrap">{{ JSON.stringify(log.metadata, null, 2) }}</pre>
                    </div>
                  </td>
                </tr>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </Page>
</template>
