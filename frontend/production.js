#!/usr/bin/env node

import express from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'
import { existsSync } from 'fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const app = express()
const PORT = process.env.PORT || 3001
const API_URL = process.env.API_URL || 'http://localhost:8000'

// Verificar si existe el build de Nuxt
const nuxtServer = path.join(__dirname, '.output/server/index.mjs')
if (!existsSync(nuxtServer)) {
  console.error('❌ Build de Nuxt no encontrado. Ejecuta: pnpm build')
  process.exit(1)
}

console.log('🏗️  Iniciando servidor Nuxt...')

// Iniciar Nuxt en puerto 3000
const nuxtProcess = spawn('node', [nuxtServer], {
  cwd: __dirname,
  stdio: 'pipe',
  env: { ...process.env, PORT: '3000', NITRO_PORT: '3000' }
})

nuxtProcess.stdout.on('data', (data) => {
  const output = data.toString().trim()
  if (output) console.log(`[Nuxt] ${output}`)
})

nuxtProcess.stderr.on('data', (data) => {
  const output = data.toString().trim()
  // Filtrar warnings conocidos de Vue Router
  if (output && !output.includes('No match found for location with path "/_nuxt/')) {
    console.error(`[Nuxt] ${output}`)
  }
})

nuxtProcess.on('close', (code) => {
  console.log(`[Nuxt] Proceso cerrado con código ${code}`)
  process.exit(code)
})

// Esperar a que Nuxt inicie
await new Promise(resolve => setTimeout(resolve, 3000))

// Proxy para API (excluir rutas internas de Nuxt)
app.use('/api', createProxyMiddleware({
  target: API_URL,
  changeOrigin: true,
  pathRewrite: { '^/api': '' },
  skip: (req) => {
    // No hacer proxy de las rutas internas de Nuxt
    return req.path.includes('/_nuxt_icon/') || req.path.includes('/_nuxt/')
  },
  onError: (err, req, res) => {
    console.error('❌ API Error:', err.message)
    res.status(500).json({ error: 'Backend no disponible' })
  }
}))

// Proxy para WebSocket
const wsProxy = createProxyMiddleware({
  target: API_URL, // Mantener protocolo http://
  changeOrigin: true,
  ws: true,
  pathFilter: '/ws',
  onError: (err, req, res) => {
    console.error('❌ WS Error:', err.message)
  }
})

app.use('/ws', wsProxy)

// Proxy para frontend
app.use('/', createProxyMiddleware({
  target: 'http://localhost:3000',
  changeOrigin: true,
  onError: (err, req, res) => {
    console.error('❌ Frontend Error:', err.message)
    res.status(500).send('Frontend no disponible')
  }
}))

// Iniciar proxy
const server = app.listen(PORT, '0.0.0.0', () => {
  console.log('🚀 LocalRun Producción')
  console.log(`🌐 Acceso: http://localhost:${PORT}`)
  console.log(`🔧 Backend: ${API_URL}`)
})

// Manejar upgrade de WebSocket
server.on('upgrade', wsProxy.upgrade)

// Shutdown limpio
const shutdown = () => {
  console.log('🛑 Cerrando servidores...')
  nuxtProcess.kill('SIGTERM')
  server.close(() => {
    console.log('✅ Servidores cerrados')
    process.exit(0)
  })
}

process.on('SIGTERM', shutdown)
process.on('SIGINT', shutdown)