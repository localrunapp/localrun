<template>
  <div
    class="min-h-screen bg-gray-50 dark:bg-slate-900 flex flex-col justify-center items-center px-4"
  >
    <div class="text-center max-w-lg mx-auto">
      <!-- Ilustración 404 -->
      <div class="mb-8">
        <div class="relative">
          <h1
            class="text-9xl font-bold text-blue-600 dark:text-blue-400 relative z-10"
          >
            404
          </h1>
          <div
            class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-blue-100 dark:bg-blue-900/20 rounded-full -z-0"
          ></div>
        </div>
        <div
          class="w-24 h-1 bg-gradient-to-r from-blue-600 to-blue-400 dark:from-blue-400 dark:to-blue-300 mx-auto mb-6 rounded-full"
        ></div>
        <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          ¡Oops! Página no encontrada
        </h2>
        <p
          class="text-lg text-gray-600 dark:text-gray-300 mb-8 leading-relaxed"
        >
          La página que estás buscando parece haber tomado unas vacaciones.
          <br class="hidden sm:block" />
          Mientras la encontramos, ¿qué tal si exploras otras secciones?
        </p>
      </div>

      <!-- Acciones -->
      <div class="space-y-4 mb-12">
        <NuxtLink
          to="/"
          class="inline-flex items-center justify-center w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-xl transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-xl"
        >
          <svg
            class="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
            ></path>
          </svg>
          Volver al inicio
        </NuxtLink>

        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            @click="goBack"
            class="inline-flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800 font-medium rounded-lg  duration-200"
          >
            <svg
              class="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              ></path>
            </svg>
            Página anterior
          </button>

          <button
            @click="refresh"
            class="inline-flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800 font-medium rounded-lg  duration-200"
          >
            <svg
              class="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              ></path>
            </svg>
            Intentar de nuevo
          </button>
        </div>
      </div>

      <!-- Enlaces útiles -->
      <div class="border-t border-gray-200 dark:border-gray-700 pt-8">
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Enlaces útiles:
        </p>
        <div class="flex flex-wrap justify-center gap-4 text-sm">
          <NuxtLink
            to="/"
            class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 "
          >
            Inicio
          </NuxtLink>
          <span class="text-gray-300 dark:text-gray-600">•</span>
          <a
            href="mailto:soporte@backlogapp.cl"
            class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 "
          >
            Soporte
          </a>
          <span class="text-gray-300 dark:text-gray-600">•</span>
          <a
            href="/help"
            class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 "
          >
            Ayuda
          </a>
        </div>
      </div>
    </div>

    <!-- Decoración de fondo -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div
        class="absolute -top-40 -right-40 w-80 h-80 bg-blue-400/10 dark:bg-blue-400/5 rounded-full"
      ></div>
      <div
        class="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-400/10 dark:bg-blue-400/5 rounded-full"
      ></div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Función para ir a la página anterior
const goBack = () => {
  if (typeof window !== "undefined") {
    window.history.back();
  }
};

// Función para refrescar la página
const refresh = () => {
  if (typeof window !== "undefined") {
    window.location.reload();
  }
};

// Meta tags optimizados para SEO
definePageMeta({
  title: "Página no encontrada - 404",
  layout: false,
});
</script>

<style scoped>
/* Animación sutil para el número 404 */
@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

h1 {
  animation: float 3s ease-in-out infinite;
}
</style>
