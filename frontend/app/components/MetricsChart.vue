<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';

interface DataPoint {
  timestamp: string;
  cpu_percent?: number;
  memory_percent?: number;
  disk_percent?: number;
}

const props = defineProps<{
  data: DataPoint[];
  metric: 'cpu' | 'memory' | 'disk';
  color: string;
}>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: any = null;

const initChart = async () => {
  if (!chartRef.value || !props.data || props.data.length === 0) return;
  
  // Wait for ApexCharts to be available
  await nextTick();
  
  if (typeof window === 'undefined' || !(window as any).ApexCharts) {
    console.warn('ApexCharts not loaded yet');
    return;
  }
  
  // Destroy existing instance
  if (chartInstance) {
    chartInstance.destroy();
  }
  
  const ApexCharts = (window as any).ApexCharts;
  
  // Format timestamps for display (HH:MM)
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  };
  
  // Extract data
  const categories = props.data.map(d => formatTime(d.timestamp));
  const seriesData = props.data.map(d => {
    const key = `${props.metric}_percent` as keyof DataPoint;
    return d[key] || 0;
  });
  
  const options = {
    chart: {
      type: 'area',
      height: 100,
      sparkline: {
        enabled: true
      },
      toolbar: {
        show: false
      },
      zoom: {
        enabled: false
      }
    },
    stroke: {
      curve: 'smooth',
      width: 2
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.1,
        stops: [0, 90, 100]
      }
    },
    colors: [props.color],
    series: [{
      name: props.metric.toUpperCase(),
      data: seriesData
    }],
    xaxis: {
      categories: categories,
      labels: {
        show: false
      },
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      }
    },
    yaxis: {
      min: 0,
      max: 100,
      labels: {
        show: false
      }
    },
    grid: {
      show: false,
      padding: {
        top: 0,
        right: 0,
        bottom: 0,
        left: 0
      }
    },
    tooltip: {
      enabled: true,
      x: {
        show: true
      },
      y: {
        formatter: function(value: number) {
          return value.toFixed(1) + '%';
        }
      }
    }
  };
  
  chartInstance = new ApexCharts(chartRef.value, options);
  chartInstance.render();
};

onMounted(() => {
  // Wait a bit for ApexCharts to load from CDN
  setTimeout(() => {
    initChart();
  }, 100);
});

watch(() => props.data, () => {
  setTimeout(() => {
    initChart();
  }, 50);
}, { deep: true });

watch(() => props.color, () => {
  initChart();
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy();
  }
});
</script>

<template>
  <div ref="chartRef" class="w-full h-[100px]"></div>
</template>
