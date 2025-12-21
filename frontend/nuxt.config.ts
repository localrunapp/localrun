// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  ssr: true,
  runtimeConfig: {
    // Server-only config (not exposed to client)
    // Development: localhost:8000 (frontend runs locally, not in Docker)
    // Production: localrun-backend:8000 (both in Docker network)
    backendInternalUrl: process.env.BACKEND_INTERNAL_URL || 'http://localhost:8000',
    public: {
      appName: 'LocalRun',
      apiBaseUrl: '',
      wsBaseUrl: ''
    }
  },
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  app: {
    head: {
      title: 'LocalRun',
      script: [
        { innerHTML: `console.log('LocalRun - Secure Local Tunneling');` },
        {
          src: '/init-theme.js',
          tagPosition: 'head',
        },
        // Lodash (required by Preline helper)
        {
          src: 'https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js',
          tagPosition: 'bodyClose'
        },
        // ApexCharts
        {
          src: 'https://cdn.jsdelivr.net/npm/apexcharts@3.45.1/dist/apexcharts.min.js',
          tagPosition: 'bodyClose'
        },
        // Preline ApexCharts Helper
        {
          src: '/preline/helper-apexcharts.js',
          tagPosition: 'bodyClose'
        }
      ],
      link: [
        { rel: 'icon', href: '/favicon.png' },
        {
          rel: 'stylesheet',
          href: 'https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css',
        },
        // ApexCharts CSS
        {
          rel: 'stylesheet',
          href: 'https://cdn.jsdelivr.net/npm/apexcharts@3.45.1/dist/apexcharts.css'
        }
      ],
      bodyAttrs: {
        class: 'bg-gray-50'
      }
    },
    pageTransition: {
      name: 'page',
      mode: 'out-in',
      duration: 200
    }
  },
  css: ['~/assets/css/main.css'],
  modules: ['@pinia/nuxt', '@nuxt/image', '@nuxtjs/seo', '@nuxtjs/i18n', '@nuxt/icon'],
  nitro: {
    devServer: {
      host: '127.0.0.1',
      port: 3000
    },
    // Proxy de API en desarrollo
    // Backend NO usa /api/, pero frontend sí por convención
    // pathRewrite elimina /api antes de enviar al backend
    devProxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        prependPath: true,
        pathRewrite: { '^/api': '' }
      }
    }
  },
  vite: {
    plugins: [
      tailwindcss(),
    ],
    server: {
      host: '127.0.0.1', // Solo localhost
      port: 3000
    }
  },
  i18n: {
    locales: ['en', 'es'],
    defaultLocale: 'en',
  },
})