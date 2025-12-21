<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';

interface ServerHistory {
  server_id: string;
  server_name: string;
  entries: Array<{
    timestamp: string;
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
    disk_read_ops?: number;
    disk_write_ops?: number;
  }>;
}

const props = defineProps<{
  serversData: ServerHistory[];
  metric: 'cpu' | 'memory' | 'disk' | 'iops';
  title?: string;
  showCard?: boolean;
  height?: number;
}>();

// Default showCard to true if not provided
const showCard = props.showCard !== false;

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: any = null;

// Color palette for different servers
const colors = [
  '#3b82f6', // blue
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#f59e0b', // amber
  '#10b981', // green
  '#06b6d4', // cyan
  '#f97316', // orange
  '#6366f1', // indigo
];

const initChart = async () => {
  if (!chartRef.value || !props.serversData || props.serversData.length === 0) return;
  
  await nextTick();
  
  if (typeof window === 'undefined' || !(window as any).ApexCharts) {
    console.warn('ApexCharts not loaded yet');
    return;
  }
  
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  const ApexCharts = (window as any).ApexCharts;
  
  // Format timestamps
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  };
  
  // Get all unique timestamps (use first server as reference)
  const timestamps = props.serversData[0]?.entries.map(e => formatTime(e.timestamp)) || [];
  
  // Create series for each server
  const series = props.serversData.map((serverData, index) => {
    // Special handling for IOPS: sum of read and write ops
    if (props.metric === 'iops') {
      return {
        name: serverData.server_name,
        data: serverData.entries.map(e => (e.disk_read_ops || 0) + (e.disk_write_ops || 0))
      };
    }
    
    // Default handling for other metrics (percentages)
    const metricKey = `${props.metric}_percent`;
    return {
      name: serverData.server_name,
      data: serverData.entries.map(e => e[metricKey as keyof typeof e] || 0)
    };
  });
  
  const options = {
    chart: {
      type: 'area',
      height: props.height || 280,
      toolbar: {
        show: false
      },
      zoom: {
        enabled: false
      }
    },
    dataLabels: {
      enabled: false
    },
    stroke: {
      curve: 'smooth',
      width: 2
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.3,
        opacityTo: 0.05,
        stops: [0, 90, 100]
      }
    },
    colors: colors.slice(0, props.serversData.length),
    series: series,
    xaxis: {
      categories: timestamps,
      labels: {
        show: true,
        rotate: 0,
        style: {
          colors: '#9ca3af',
          fontSize: '11px'
        }
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      },
      tickAmount: 6
    },
    yaxis: {
      min: 0,
      max: props.metric === 'iops' ? undefined : 100,
      tickAmount: 2,
      labels: {
        show: true,
        style: {
          colors: '#9ca3af',
          fontSize: '11px'
        },
        formatter: function(value: number) {
          if (props.metric === 'iops') {
            return value.toFixed(0);
          }
          return value.toFixed(0) + '%';
        }
      }
    },
    grid: {
      show: true,
      borderColor: '#374151', 
      strokeDashArray: 4,
      padding: {
        top: 0,
        right: 0,
        bottom: 0,
        left: 0
      }
    },
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'left',
      fontSize: '12px',
      fontFamily: 'Inter, sans-serif',
      markers: {
        width: 8,
        height: 8,
        radius: 2
      },
      itemMargin: {
        horizontal: 12,
        vertical: 4
      },
      labels: {
        colors: '#9ca3af',
        useSeriesColors: false
      }
    },
    tooltip: {
      enabled: true,
      shared: true,
      intersect: false,
      x: {
        show: true
      },
      y: {
        formatter: function(value: number) {
          if (props.metric === 'iops') {
            return value.toFixed(0) + ' ops';
          }
          return value.toFixed(1) + '%';
        }
      }
    }
  };
  
  chartInstance = new ApexCharts(chartRef.value, options);
  chartInstance.render();
};

onMounted(() => {
  setTimeout(() => {
    initChart();
  }, 100);
});

watch(() => props.serversData, () => {
  setTimeout(() => {
    initChart();
  }, 50);
}, { deep: true });

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy();
  }
});
</script>

<template>
  <div v-if="showCard" class="bg-white border border-gray-200 rounded-lg dark:bg-gray-800 dark:border-gray-700">
    <h3 v-if="title" class="text-sm font-medium text-gray-800 dark:text-gray-200 mb-4">
      {{ title }}
    </h3>
    <div ref="chartRef" class="w-full"></div>
  </div>
  <div v-else ref="chartRef" class="w-full"></div>
</template>
