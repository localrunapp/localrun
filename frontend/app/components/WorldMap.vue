<template>
  <div id="map" ref="mapRef" class="w-full h-96"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';

const props = defineProps<{
  data: Record<string, number>;
}>();

const mapRef = ref<HTMLElement | null>(null);
let map: any = null;

const loadScript = (src: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script ${src}`));
    document.head.appendChild(script);
  });
};

const loadStyle = (href: string) => {
  if (document.querySelector(`link[href="${href}"]`)) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = href;
  document.head.appendChild(link);
};

const initMap = () => {
  if (!mapRef.value || !(window as any).jsVectorMap) return;

  // Cleanup
  if (map) {
      // jsvectormap doesn't have a clear destroy that removes DOM elements perfectly in all versions, 
      // but let's try or standard DOM clear.
      try { map.destroy(); } catch (e) {}
      map = null;
  }
  mapRef.value.innerHTML = '';

  const data = props.data || {};
  
  map = new (window as any).jsVectorMap({
    selector: mapRef.value,
    map: 'world',
    zoomButtons: true,
    zoomOnScroll: false,
    regionsSelectable: false,
    markersSelectable: false,
    // Visualizing data requires specific config in jsVectorMap
    visualizeData: {
        scale: ['#DBEAFE', '#1E40AF'],
        values: data
    },
    regionStyle: {
      initial: {
        fill: '#e5e7eb',
        "fill-opacity": 1,
        stroke: '#fff',
        "stroke-width": 0.5,
        "stroke-opacity": 1
      },
      hover: {
        fill: '#93c5fd'
      },
      selected: {
        fill: '#3b82f6'
      }
    },
    onRegionTooltipShow(event: any, tooltip: any, code: string) {
        const count = data[code] || 0;
        tooltip.text(
            `<h5>${tooltip.text()}</h5>` +
            `<p class="text-xs">Visits: ${count}</p>`
        , true); // true enables HTML
    }
  });
};

onMounted(async () => {
  try {
    loadStyle('https://cdn.jsdelivr.net/npm/jsvectormap/dist/css/jsvectormap.min.css');
    await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap');
    await loadScript('https://cdn.jsdelivr.net/npm/jsvectormap/dist/maps/world.js');
    initMap();
  } catch (e) {
    console.error("Failed to load map libraries", e);
  }
});

watch(() => props.data, () => {
    if ((window as any).jsVectorMap) {
        initMap();
    }
}, { deep: true });

onBeforeUnmount(() => {
  if (map) {
      // map.destroy(); 
  }
});
</script>

<style>
.jvm-tooltip {
  background-color: #1f2937;
  color: white;
  font-family: inherit;
  border-radius: 0.375rem;
  padding: 0.5rem;
  font-size: 0.75rem;
  z-index: 100;
}
</style>
