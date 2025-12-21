# Localrun Backend

Backend del sistema de gestión de túneles Localrun, construido con FastAPI siguiendo una arquitectura estilo Laravel.

## 🚀 Características

- **Autenticación JWT**: Login con usuario/password (sin OAuth)
- **SQLite Database**: Base de datos ligera con migraciones automáticas
- **Logging con Trace ID**: Logs estructurados para debugging
- **Gestión de Túneles**: Soporte para Cloudflare y Ngrok
- **DNS Management**: API para gestión de registros DNS

## 🔐 Autenticación

El sistema usa autenticación simple con usuario y contraseña:

- **Usuario por defecto**: `demo`
- **Contraseña por defecto**: `demo`

El usuario demo se crea automáticamente en el primer inicio.

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'
```

Respuesta:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 10080
}
```

### Usar el token

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

## 📁 Estructura del Proyecto

```
backend/
├── main.py                    # Entry point
├── core/                      # Infraestructura (Laravel: app/Support)
│   ├── auth.py               # JWT authentication
│   ├── context.py            # Request context (trace_id)
│   ├── database.py           # Database connection
│   ├── hash.py               # Password hashing (Laravel: Hash facade)
│   ├── logger.py             # Custom logger con trace_id
│   ├── settings.py           # Configuración (Laravel: config/)
│   ├── storage.py            # File storage (deprecated)
│   ├── supervisor.py         # Process supervision
│   ├── trace_id_middleware.py # Trace ID middleware
│   └── tunnel_manager.py     # Tunnel orchestration
├── app/                       # Lógica de negocio (Laravel: app/)
│   ├── controllers/          # Controllers (Laravel: Controllers)
│   ├── models/               # SQLAlchemy models (Laravel: Models)
│   ├── schemas/              # Pydantic DTOs (Laravel: FormRequests)
│   ├── drivers/              # External services drivers
│   ├── handler.py            # Exception handlers
│   └── router.py             # Routes definition
├── database/                  # Database (Laravel: database/)
│   ├── __init__.py
│   └── seeders.py            # Database seeders
└── storage/                   # Runtime data
```

## 🛠️ Desarrollo

### Requisitos

- Python 3.11+
- Pipenv

### Setup

```bash
# Instalar dependencias
pipenv install --dev

# Copiar variables de entorno
cp ../.env.example ../.env

# Editar .env y configurar JWT_SECRET_KEY
nano ../.env

# Ejecutar
pipenv run python main.py
```

La base de datos se inicializa automáticamente en el primer inicio.

### Docker

```bash
# Desarrollo
docker compose up backend

# Producción
docker build -f ../Dockerfile -t localrun .
docker run -p 8000:8000 localrun
```

## 🗄️ Base de Datos

### Migración

Las tablas se crean automáticamente en el primer inicio usando SQLAlchemy:

```python
from database.seeders import seed_database
seed_database()  # Laravel: php artisan migrate:fresh --seed
```

### Seeders

El seeder crea el usuario `demo/demo` automáticamente si no existe.

Para re-ejecutar seeders manualmente:

```python
from database.seeders import DatabaseSeeder
DatabaseSeeder.run()
```

## 📝 API Endpoints

### Authentication

- `POST /api/auth/login` - Login con username/password
- `GET /api/auth/me` - Obtener usuario actual
- `POST /api/auth/logout` - Logout (client-side)

### Providers

- `GET /api/providers/tunnels` - Listar tunnel providers
- `POST /api/providers/tunnels` - Crear tunnel provider
- `DELETE /api/providers/tunnels/{id}` - Eliminar tunnel provider

### Tunnels

- `GET /api/tunnels` - Listar túneles
- `POST /api/tunnels` - Crear túnel
- `POST /api/tunnels/{id}/start` - Iniciar túnel
- `POST /api/tunnels/{id}/stop` - Detener túnel
- `GET /api/tunnels/{id}/status` - Estado del túnel

### DNS

- `GET /api/dns/records` - Listar registros DNS
- `POST /api/dns/records` - Crear registro DNS
- `DELETE /api/dns/records/{id}` - Eliminar registro DNS

## 🔧 Configuración

Ver `.env.example` para todas las variables de entorno disponibles.

Variables importantes:

- `JWT_SECRET_KEY`: Clave secreta para firmar tokens (⚠️ cambiar en producción)
- `DATABASE_URL`: URL de conexión a SQLite
- `DATA_DIR`: Directorio para archivos del sistema
- `FRONTEND_URL`: URL del frontend para CORS

## 🧪 Testing

```bash
pipenv run pytest
```

## 📚 Inspiración

Este proyecto sigue principios de arquitectura de Laravel:

- **Facades** → `core/hash.py` (Hash::make, Hash::check)
- **Eloquent Models** → `app/models/user.py`
- **Controllers** → `app/controllers/`
- **Form Requests** → `app/schemas/`
- **Seeders** → `database/seeders.py`
- **Migrations** → SQLAlchemy Base.metadata.create_all()
