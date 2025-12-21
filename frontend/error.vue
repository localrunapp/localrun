<template>
  <div
    class="min-h-screen bg-gray-50 dark:bg-slate-900 flex flex-col justify-center items-center px-4"
  >
    <!-- Error 404 -->
    <div v-if="safeError.statusCode === 404" class="text-center max-w-lg mx-auto">
      <div class="mb-8">
        <h1 class="text-9xl font-bold text-blue-600 dark:text-blue-400">404</h1>
        <div class="w-24 h-1 bg-blue-600 dark:bg-blue-400 mx-auto mb-4"></div>
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          Página no encontrada
        </h2>
        <p class="text-gray-600 dark:text-gray-300 mb-8">
          Lo sentimos, la página que estás buscando no existe o ha sido movida.
        </p>
      </div>

      <div class="space-y-4">
        <button
          @click="handleError"
          class="w-full sm:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg  duration-200"
        >
          Volver al inicio
        </button>
        <button
          @click="goBack"
          class="w-full sm:w-auto ml-0 sm:ml-3 px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800 font-medium rounded-lg  duration-200"
        >
          Página anterior
        </button>
      </div>
    </div>

    <!-- Error 500 -->
    <div v-else class="text-center max-w-2xl mx-auto">
      <div class="mb-8">
        <h1 class="text-9xl font-bold text-red-600 dark:text-red-400">500</h1>
        <div class="w-24 h-1 bg-red-600 dark:bg-red-400 mx-auto mb-4"></div>
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          Error interno del servidor
        </h2>
        <p class="text-gray-600 dark:text-gray-300 mb-8">
          {{
            safeError.statusMessage ||
            "Ha ocurrido un error inesperado. Nuestro equipo ha sido notificado."
          }}
        </p>
      </div>

      <!-- Error details (solo en desarrollo) -->
      <div v-if="isDevelopment && safeError" class="mb-8 text-left">
        <div
          class="bg-gray-100 dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700"
        >
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Detalles del error (solo en desarrollo)
          </h3>

          <!-- Error message -->
          <div class="mb-4">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">
              Mensaje:
            </h4>
            <pre
              class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded border overflow-x-auto"
              >{{ safeError.message || "Error desconocido" }}</pre
            >
          </div>

          <!-- Stack trace -->
          <div v-if="safeError.stack" class="mb-4">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">
              Stack trace:
            </h4>
            <pre
              class="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-slate-700 p-3 rounded border overflow-x-auto max-h-64 overflow-y-auto"
              >{{ safeError.stack }}</pre
            >
          </div>

          <!-- Additional error data -->
          <div v-if="safeError.data" class="mb-4">
            <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">
              Datos adicionales:
            </h4>
            <pre
              class="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-slate-700 p-3 rounded border overflow-x-auto"
              >{{ JSON.stringify(safeError.data, null, 2) }}</pre
            >
          </div>
        </div>
      </div>

      <div class="space-y-4">
        <button
          @click="handleError"
          class="w-full sm:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg  duration-200"
        >
          Volver al inicio
        </button>
        <button
          @click="refresh"
          class="w-full sm:w-auto ml-0 sm:ml-3 px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800 font-medium rounded-lg  duration-200"
        >
          Intentar de nuevo
        </button>
      </div>
    </div>

    <!-- Footer -->
    <div class="mt-16 text-center">
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Si el problema persiste, por favor contacta a nuestro equipo de soporte.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface NuxtError {
  statusCode: number;
  statusMessage?: string;
  message?: string;
  stack?: string;
  data?: any;
}

const props = defineProps<{
  error: NuxtError;
}>();

// Detectar si estamos en desarrollo
const isDevelopment = process.env.NODE_ENV === "development";

// Asegurar que el error tenga propiedades válidas
const safeError = computed(() => ({
  statusCode: props.error?.statusCode || 500,
  statusMessage: props.error?.statusMessage || '',
  message: props.error?.message || '',
  stack: props.error?.stack || '',
  data: props.error?.data || null
}));

// Función para manejar el error y redirigir al inicio
const handleError = () => {
  clearError({ redirect: '/' });
};

// Función para refrescar la página
const refresh = () => {
  clearError();
};

// Función para ir a la página anterior
const goBack = () => {
  if (typeof window !== "undefined") {
    window.history.back();
  }
};
</script>

<style scoped>
/* Estilos adicionales si son necesarios */
</style>
