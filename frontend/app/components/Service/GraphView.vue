<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import ServerNode from './Graph/ServerNode.vue';
import ServiceNode from './Graph/ServiceNode.vue';
import DomainNode from './Graph/DomainNode.vue';
import ContextMenu from './Graph/ContextMenu.vue';

interface Service {
  id: string;
  name: string;
  host: string;
  port: number;
  protocol: string;
  public_url?: string;
  server_id?: string;
  status: string;
}

interface Server {
  id: string;
  name: string;
  os_name?: string;
  is_local?: boolean;
  stats?: {
    cpu_percent?: number;
    memory_percent?: number;
    disk_read_ops?: number;
    disk_write_ops?: number;
    os_name?: string;
  };
}

interface DNSRecord {
  id: number;
  name: string;
  service_id: number;
  record_type: string;
  content: string;
}

interface Node {
  id: string;
  type: 'server' | 'service' | 'domain';
  label: string;
  sublabel?: string;
  x: number;
  y: number;
  status?: string;
  protocol?: string;
  port?: number;
  publicUrl?: string;
}

const props = defineProps<{
  services: Service[];
  servers: Server[];
  dnsRecords?: DNSRecord[];
}>();

// Graph state
const nodes = ref<Node[]>([]);
const edges = ref<Array<{ from: string; to: string }>>([]);
const draggingNode = ref<string | null>(null);
const dragOffset = ref({ x: 0, y: 0 });
const viewBox = ref({ x: 0, y: 0, width: 1200, height: 800 });
const zoom = ref(1);
const isPanning = ref(false);
const panStart = ref({ x: 0, y: 0 });

// Context menu state
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  nodeType: 'server' as 'server' | 'service' | 'domain',
  nodeData: null as any,
});

// Initialize graph
const initializeGraph = () => {
  const newNodes: Node[] = [];
  const newEdges: Array<{ from: string; to: string }> = [];
  
  // Extract unique servers
  const serverIds = new Set<string>();
  props.services.forEach(service => {
    if (service.server_id) serverIds.add(service.server_id);
  });
  
  // Extract DNS domains from DNS records
  const domainRecords = new Map<number, DNSRecord>();
  if (props.dnsRecords) {
    props.dnsRecords.forEach(record => {
      domainRecords.set(record.service_id, record);
    });
  }
  
  // Create server nodes (left column) - show ALL servers
  let yOffset = 100;
  const serverPositions = new Map<string, { x: number; y: number }>();
  props.servers.forEach((server, index) => {
    const nodeId = `server-${server.id}`;
    newNodes.push({
      id: nodeId,
      type: 'server',
      label: server.name,
      x: 80,
      y: yOffset,
    });
    serverPositions.set(server.id, { x: 80, y: yOffset });
    yOffset += 160;
  });
  
  // Create service nodes (middle column)
  yOffset = 100;
  const servicePositions = new Map<string, { x: number; y: number }>();
  props.services.forEach((service, index) => {
    const nodeId = `service-${service.id}`;
    newNodes.push({
      id: nodeId,
      type: 'service',
      label: service.name,
      x: 480,
      y: yOffset,
      status: service.status,
      protocol: service.protocol,
      port: service.port,
      publicUrl: service.public_url,
    });
    servicePositions.set(service.id, { x: 480, y: yOffset });
    
    // Create edge from server to service
    if (service.server_id) {
      const edgeFrom = `server-${service.server_id}`;
      const edgeTo = nodeId;
      console.log('Creating edge:', edgeFrom, '->', edgeTo, 'service:', service.name);
      newEdges.push({
        from: edgeFrom,
        to: edgeTo,
      });
    } else {
      console.log('Service has no server_id:', service.name);
    }
    
    yOffset += 140;
  });
  
  // Create domain nodes (right column) - only for services with DNS records
  yOffset = 100;
  const domainPositions = new Map<number, { x: number; y: number }>();
  const createdDomains = new Set<number>();
  
  props.services.forEach(service => {
    const dnsRecord = domainRecords.get(parseInt(service.id));
    if (dnsRecord && !createdDomains.has(dnsRecord.id)) {
      const nodeId = `domain-${dnsRecord.id}`;
      newNodes.push({
        id: nodeId,
        type: 'domain',
        label: dnsRecord.name,
        x: 880,
        y: yOffset,
      });
      domainPositions.set(dnsRecord.id, { x: 880, y: yOffset });
      createdDomains.add(dnsRecord.id);
      yOffset += 160;
      
      // Create edge from service to domain
      newEdges.push({
        from: `service-${service.id}`,
        to: nodeId,
      });
    }
  });
  
  console.log('Total nodes:', newNodes.length);
  console.log('Total edges:', newEdges.length);
  console.log('Edges:', newEdges);
  
  nodes.value = newNodes;
  edges.value = newEdges;
};

// Get service count for each server
const getServerServiceCount = (serverId: string) => {
  return props.services.filter(s => s.server_id === serverId).length;
};

// Get DNS record for a service
const getDNSRecordForService = (serviceId: string) => {
  if (!props.dnsRecords) return null;
  return props.dnsRecords.find(r => r.service_id === parseInt(serviceId));
};

// Context menu handlers
const showContextMenu = (event: MouseEvent, node: Node) => {
  event.preventDefault();
  event.stopPropagation();
  
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    nodeType: node.type,
    nodeData: node,
  };
};

const hideContextMenu = () => {
  contextMenu.value.visible = false;
};

const handleContextAction = (action: string, data: any) => {
  console.log('Context action:', action, data);
  // TODO: Implement actions
  // emit('node-action', { action, node: data });
};

// Drag handlers
const startDrag = (event: MouseEvent, nodeId: string) => {
  // Don't allow dragging if context menu is open
  if (contextMenu.value.visible) return;
  
  const node = nodes.value.find(n => n.id === nodeId);
  if (!node) return;
  
  draggingNode.value = nodeId;
  const svgPoint = getSVGPoint(event);
  dragOffset.value = {
    x: svgPoint.x - node.x,
    y: svgPoint.y - node.y,
  };
};

const onDrag = (event: MouseEvent) => {
  if (draggingNode.value) {
    const node = nodes.value.find(n => n.id === draggingNode.value);
    if (!node) return;
    
    const svgPoint = getSVGPoint(event);
    node.x = svgPoint.x - dragOffset.value.x;
    node.y = svgPoint.y - dragOffset.value.y;
  } else if (isPanning.value) {
    const dx = event.clientX - panStart.value.x;
    const dy = event.clientY - panStart.value.y;
    viewBox.value.x -= dx / zoom.value;
    viewBox.value.y -= dy / zoom.value;
    panStart.value = { x: event.clientX, y: event.clientY };
  }
};

const endDrag = () => {
  draggingNode.value = null;
  isPanning.value = false;
};

const startPan = (event: MouseEvent) => {
  // Don't allow panning if context menu is open
  if (contextMenu.value.visible) return;
  
  // Allow panning when clicking on the SVG itself or the background rect
  const target = event.target as SVGElement;
  if (target.tagName === 'svg' || target.tagName === 'rect') {
    isPanning.value = true;
    panStart.value = { x: event.clientX, y: event.clientY };
  }
};

// Zoom handlers
const handleZoom = (delta: number, centerX?: number, centerY?: number) => {
  const newZoom = Math.max(0.1, Math.min(3, zoom.value + delta));
  const factor = newZoom / zoom.value;
  
  // If center point provided, zoom towards that point
  if (centerX !== undefined && centerY !== undefined) {
    const svgX = viewBox.value.x + centerX;
    const svgY = viewBox.value.y + centerY;
    
    viewBox.value.x = svgX - (svgX - viewBox.value.x) / factor;
    viewBox.value.y = svgY - (svgY - viewBox.value.y) / factor;
  }
  
  viewBox.value.width /= factor;
  viewBox.value.height /= factor;
  zoom.value = newZoom;
};

const handleWheel = (event: WheelEvent) => {
  event.preventDefault();
  const delta = event.deltaY > 0 ? -0.1 : 0.1;
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  const centerX = (event.clientX - rect.left) / zoom.value;
  const centerY = (event.clientY - rect.top) / zoom.value;
  handleZoom(delta, centerX, centerY);
};

const zoomIn = () => handleZoom(0.1);
const zoomOut = () => handleZoom(-0.1);
const resetView = () => {
  viewBox.value = { x: 0, y: 0, width: 1200, height: 800 };
  zoom.value = 1;
};

// Helper to convert mouse coordinates to SVG coordinates
const getSVGPoint = (event: MouseEvent) => {
  return {
    x: viewBox.value.x + (event.offsetX / zoom.value),
    y: viewBox.value.y + (event.offsetY / zoom.value),
  };
};

// Get node style classes (opaque cards)
const getNodeClass = (node: Node) => {
  const baseClasses = 'transition-all duration-200 cursor-move';
  if (node.type === 'server') {
    return `${baseClasses} fill-blue-100 stroke-blue-500 dark:fill-blue-900 dark:stroke-blue-500`;
  } else if (node.type === 'service') {
    if (node.status === 'running') {
      return `${baseClasses} fill-green-100 stroke-green-500 dark:fill-green-900 dark:stroke-green-500`;
    }
    return `${baseClasses} fill-gray-100 stroke-gray-500 dark:fill-gray-800 dark:stroke-gray-500`;
  } else {
    return `${baseClasses} fill-purple-100 stroke-purple-500 dark:fill-purple-900 dark:stroke-purple-500`;
  }
};

const getTextClass = (node: Node) => {
  if (node.type === 'server') {
    return 'fill-blue-900 dark:fill-blue-200';
  } else if (node.type === 'service') {
    if (node.status === 'running') {
      return 'fill-green-900 dark:fill-green-200';
    }
    return 'fill-gray-900 dark:fill-gray-200';
  } else {
    return 'fill-purple-900 dark:fill-purple-200';
  }
};

onMounted(() => {
  initializeGraph();
});
</script>

<template>
  <div class="relative w-full h-full bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700" @click="hideContextMenu">
    <!-- Controls -->
    <div class="absolute top-4 right-4 z-10 flex flex-col gap-2">
      <button
        @click="zoomIn"
        class="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
        title="Zoom In"
      >
        <svg class="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
      </button>
      <button
        @click="zoomOut"
        class="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
        title="Zoom Out"
      >
        <svg class="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
        </svg>
      </button>
      <button
        @click="resetView"
        class="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
        title="Reset View"
      >
        <svg class="w-5 h-5 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <!-- SVG Canvas -->
    <svg
      class="w-full h-full cursor-grab active:cursor-grabbing"
      :viewBox="`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`"
      @mousedown="startPan"
      @mousemove="onDrag"
      @mouseup="endDrag"
      @mouseleave="endDrag"
      @wheel="handleWheel"
    >
      <!-- Background pattern -->
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r="1" class="fill-gray-300 dark:fill-gray-700" />
        </pattern>
      </defs>
      <!-- Extended background to cover entire viewBox -->
      <rect 
        :x="viewBox.x - 500" 
        :y="viewBox.y - 500" 
        :width="viewBox.width + 1000" 
        :height="viewBox.height + 1000" 
        fill="url(#grid)" 
      />
      
      <!-- Edges -->
      <g class="edges">
        <path
          v-for="(edge, index) in edges"
          :key="`edge-${index}`"
          :d="(() => {
            const fromNode = nodes.find(n => n.id === edge.from);
            const toNode = nodes.find(n => n.id === edge.to);
            if (!fromNode || !toNode) return '';
            const startX = fromNode.x + 200;
            const startY = fromNode.y + 60;
            const endX = toNode.x;
            const endY = toNode.y + 60;
            const midX = (startX + endX) / 2;
            return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
          })()"
          class="stroke-blue-400 dark:stroke-blue-500 fill-none opacity-60"
          stroke-width="2.5"
          stroke-dasharray="5,5"
        />
      </g>
      
      <!-- Nodes -->
      <g class="nodes">
        <g
          v-for="node in nodes"
          :key="node.id"
          :transform="`translate(${node.x}, ${node.y})`"
          @mousedown.stop="startDrag($event, node.id)"
          @contextmenu="showContextMenu($event, node)"
        >
          <!-- Shadow filter -->
          <filter :id="`shadow-${node.id}`">
            <feDropShadow dx="0" dy="2" stdDeviation="4" flood-opacity="0.1" />
          </filter>
          
          <g :filter="`url(#shadow-${node.id})`">
            <!-- Server Node -->
            <ServerNode
              v-if="node.type === 'server'"
              :name="node.label"
              :service-count="getServerServiceCount(node.id.replace('server-', ''))"
              :os-name="props.servers.find(s => s.id === node.id.replace('server-', ''))?.os_name"
              :is-local="props.servers.find(s => s.id === node.id.replace('server-', ''))?.is_local"
              :stats="props.servers.find(s => s.id === node.id.replace('server-', ''))?.stats"
            />
            
            <!-- Service Node -->
            <ServiceNode
              v-else-if="node.type === 'service'"
              :name="node.label"
              :protocol="node.protocol || 'tcp'"
              :port="node.port || 0"
              :status="node.status || 'stopped'"
              :public-url="node.publicUrl"
            />
            
            <!-- Domain Node -->
            <DomainNode
              v-else-if="node.type === 'domain'"
              :name="node.label"
              :record-type="getDNSRecordForService(node.id.replace('domain-', ''))?.record_type"
            />
          </g>
        </g>
      </g>
    </svg>
    
    <!-- Instructions -->
    <div class="absolute bottom-4 left-4 text-xs text-gray-500 dark:text-gray-400 bg-white/80 dark:bg-gray-800/80 px-3 py-2 rounded-lg backdrop-blur-sm">
      <p>🖱️ Drag nodes • Right-click for actions • Scroll to zoom</p>
    </div>
    
    <!-- Context Menu -->
    <ContextMenu
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :node-type="contextMenu.nodeType"
      :node-data="contextMenu.nodeData"
      @close="hideContextMenu"
      @action="handleContextAction"
    />
  </div>
</template>
