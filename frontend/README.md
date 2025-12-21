# LocalRun Frontend

## 🏃 Desarrollo

```bash
pnpm install
pnpm dev
```

**Acceso:** `http://localhost:3001`

## 🚀 Producción

```bash
pnpm build
pnpm start
```

**Acceso:** `http://localhost:3001`

## 🐳 Docker

```bash
docker build -t localrun-frontend .
docker run -p 3001:3001 -e API_URL=http://backend:8000 localrun-frontend
```

## 📝 Scripts Disponibles

### Desarrollo
- `pnpm dev` - Proxy automático (puerto 3001)
- `pnpm dev:direct` - Sin proxy (puerto 3000)

### Producción  
- `pnpm start` - Proxy + build optimizado (puerto 3001)
- `pnpm start:direct` - Solo build Nuxt (puerto 3000)

## 🔧 Configuración

- **Frontend interno:** localhost:3000
- **Backend:** localhost:8000 (configurable con `API_URL`)
- **Proxy público:** localhost:3001

**Solo expón puerto 3001 con túneles** - oculta automáticamente el backend.
