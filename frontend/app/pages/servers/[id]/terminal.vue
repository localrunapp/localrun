<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useToast } from '@/composables/useToast';
import { useTerminalSocket } from '@/composables/useTerminalSocket';
import { IconServerOff } from '@tabler/icons-vue';
import '@xterm/xterm/css/xterm.css';

const terminalContainer = ref(null);
const toast = useToast();
const route = useRoute();
let term = null;
let fitAddon = null;

const serverId = computed(() => route.params.id || null);
const isMinimal = computed(() => route.query.minimal === 'true');
const { getServer } = useServers();
const server = ref(null);

if (isMinimal.value) {
    setPageLayout('minimal');
}

// Fetch server details for title
onMounted(async () => {
    if (serverId.value) {
        try {
            server.value = await getServer(serverId.value);
            if (server.value) {
                useHead({
                    title: `Localrun - ${server.value.name}`
                });
            }
        } catch (e) {
            console.error('Failed to fetch server details', e);
        }
    }
});

// Usar el composable de WebSocket para terminal
const { status, lastMessage, sendInput, sendResize, connect, retry } = useTerminalSocket(serverId.value);

const copyCommand = () => {
    navigator.clipboard.writeText('curl -fsSL https://raw.githubusercontent.com/localrun-tech/cli-agent/main/install-macos.sh | bash');
    toast.success('Command copied to clipboard');
};

const initTerminal = async () => {
    // Dynamic import for client-side only
    const { Terminal } = await import('@xterm/xterm');
    const { FitAddon } = await import('@xterm/addon-fit');
    const { WebLinksAddon } = await import('@xterm/addon-web-links');

    const isMobile = window.innerWidth < 768;

    term = new Terminal({
        cursorBlink: true,
        fontSize: isMobile ? 9 : 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
            background: '#1e1e1e',
            foreground: '#f8f8f2',
            cursor: '#f8f8f2',
            selectionBackground: '#44475a',
            black: '#21222c',
            red: '#ff5555',
            green: '#50fa7b',
            yellow: '#f1fa8c',
            blue: '#bd93f9',
            magenta: '#ff79c6',
            cyan: '#8be9fd',
            white: '#f8f8f2',
            brightBlack: '#6272a4',
            brightRed: '#ff6e6e',
            brightGreen: '#69ff94',
            brightYellow: '#ffffa5',
            brightBlue: '#d6acff',
            brightMagenta: '#ff92df',
            brightCyan: '#a4ffff',
            brightWhite: '#ffffff',
        },
        allowProposedApi: true
    });

    fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(new WebLinksAddon());

    term.open(terminalContainer.value);
    fitAddon.fit();

    term.onData(data => {
        sendInput(data);
    });

    term.onResize(size => {
        sendResize(size.cols, size.rows);
    });

    window.addEventListener('resize', () => fitAddon.fit());
};

// Manejar mensajes del WebSocket
watch(lastMessage, (msg) => {
    if (!msg || !term) return;
    
    try {
        if (msg.type === 'output' || msg.type === 'terminal_output') {
            term.write(msg.data);
        } else if (msg.type === 'status') {
            if (msg.status === 'online') {
                term.clear();
                term.focus();
                fitAddon.fit();
                // Send Ctrl+L to clear screen and force prompt refresh
                sendInput('\u000C');
            }
        }
    } catch (error) {
        console.error('Error handling terminal message:', error);
    }
});

// Limpiar terminal cuando se conecta
watch(status, (newStatus) => {
    if (newStatus === 'online' && term) {
        term.clear();
        fitAddon.fit();
    }
});

onMounted(async () => {
    await initTerminal();
    connect();
});

onBeforeUnmount(() => {
    if (term) term.dispose();
    window.removeEventListener('resize', () => fitAddon?.fit());
});
</script>

<style scoped>
:deep(.xterm-viewport) {
    overflow-y: auto;
}
</style>
<template>
    <div :class="{'min-h-screen bg-white dark:bg-gray-950': isMinimal}">
        <!-- Header (only shown if not minimal) -->
        <PageHeader 
            v-if="!isMinimal"
            icon="lucide:terminal" 
            title="Web Terminal" 
            iconClass="!size-10 pt-0 !mt-2"
            subtitle="Direct access to your host shell." 
            backPath="/" 
        />

        <div :class="{'h-screen w-screen': isMinimal, 'container mx-auto px-4 py-6': !isMinimal}">

        <!-- Loading State -->
        <div v-if="status === 'connecting'" class="flex flex-col items-center justify-center bg-zinc-900" :class="isMinimal ? 'h-full' : 'h-[calc(100vh-14rem)]'">
            <Icon name="lucide:loader-2" class="w-10 h-10 text-blue-500 animate-spin mb-4" />
            <p class="text-slate-500 font-medium">Connecting to LocalRun Agent...</p>
        </div>

        <!-- Offline State -->
        <div v-else-if="status === 'offline'" class="flex flex-col items-center justify-center bg-zinc-900" :class="isMinimal ? 'h-full' : 'h-[calc(100vh-14rem)]'">
            <div class="max-w-2xl w-full flex flex-col items-center">
                <div class="mb-6">
                    <IconServerOff class="w-12 h-12 text-red-500 dark:text-red-400" />
                </div>

                <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-3">Agent Disconnected</h3>
                <p class="text-gray-500 dark:text-gray-400 text-center max-w-md mb-8">
                    The LocalRun Agent is not connected. Install and run the agent on your host machine to access the
                    terminal.
                </p>

                <!-- Install Command -->
                <div class="bg-gray-900 rounded-xl p-5 border border-gray-800 w-full mb-8 relative group shadow-lg">
                    <p class="text-xs text-gray-500 mb-3 uppercase font-bold tracking-wider flex items-center gap-2">
                        <Icon name="lucide:terminal" class="w-3 h-3" />
                        Install & Start Agent
                    </p>
                    <div class="flex items-center justify-between gap-4">
                        <code class="text-green-400 font-mono text-sm break-all">curl -fsSL
                    https://raw.githubusercontent.com/localrun-tech/cli-agent/main/install-macos.sh | bash</code>
                        <button @click="copyCommand"
                            class="text-gray-400 hover:text-white  shrink-0 p-2 hover:bg-gray-800 rounded-lg">
                            <Icon name="lucide:copy" class="w-4 h-4" />
                        </button>
                    </div>
                </div>

                <div class="flex items-center gap-4">
                    <button @click="retry"
                        class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium  flex items-center gap-2 shadow-sm hover:shadow-md">
                        <Icon name="lucide:refresh-cw" class="w-4 h-4" />
                        Retry Connection
                    </button>

                    <a href="https://localrun.app/v1/web-terminal" target="_blank"
                        class="px-6 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg font-medium  flex items-center gap-2">
                        <Icon name="lucide:book-open" class="w-4 h-4" />
                        Documentation
                    </a>
                </div>
            </div>
        </div>

        <!-- Terminal State -->
        <div v-show="status === 'online'"
            :class="isMinimal ? 'h-full w-full' : 'h-[calc(100vh-14rem)] rounded-xl border border-slate-800 shadow-2xl'"
            class="bg-[#1e1e1e] overflow-hidden relative group">
            <!-- Terminal Scroll Wrapper -->
            <div class="flex-1 w-full h-full overflow-hidden relative">
                <div class="absolute inset-0 overflow-hidden">
                    <div ref="terminalContainer" class="h-full w-full bg-[#1e1e1e]" :class="{'p-4': !isMinimal}"></div>
                </div>
            </div>
        </div>
    </div>
    </div>
</template>
