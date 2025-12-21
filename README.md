# Localrun

Self-hosted tunnel management platform with DNS integration.

## Quick Start

### Using Docker (Recommended)

Pull and run the latest image from GitHub Container Registry:

```bash
docker run -d \
  --name localrun \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume ~/.localrun:/app/storage \
  --publish 8000:8000 \
  --publish 3006:3006 \
  ghcr.io/localrun-tech/portal:latest
```

Access the application:
- **Frontend**: http://localhost:3006
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Environment Variables

```bash
docker run -d \
  --name localrun \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume ~/.localrun:/app/storage \
  --publish 8000:8000 \
  --publish 3006:3006 \
  --env DATABASE_URL="sqlite:////app/storage/localrun.db" \
  --env SECRET_KEY="your-secret-key-here" \
  ghcr.io/localrun-tech/portal:latest
```

### Building from Source

```bash
# Build the image
docker build -t localrun-portal .

# Run locally built image
docker run -d \
  --name localrun \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume ~/.localrun:/app/storage \
  --publish 8000:8000 \
  --publish 3006:3006 \
  localrun-portal
```

## GitHub Container Registry

Yes, GitHub provides a free public container registry (ghcr.io). 

**Note:** Docker requires token authentication for GitHub Container Registry (web login is not supported).

### Quick Setup

1. **Create Personal Access Token** (one-time setup):
   - Visit: https://github.com/settings/tokens/new?scopes=write:packages
   - Or go to: GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scope: `write:packages` (and optionally `read:packages`, `delete:packages`)
   - Generate and copy the token

2. **Set token as environment variable:**
   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   ```

3. **Login and publish:**
   ```bash
   make docker-login
   make publish
   ```

### Publishing Multi-Architecture Images

For both ARM64 (Apple Silicon) and AMD64 (Intel) support:

```bash
# One-time setup
make buildx-setup

# Publish for both architectures
make publish-multiarch
```

## Makefile Commands

```bash
make help              # Show all available commands
make build             # Build Docker image locally
make test              # Build and run test container
make logs              # View logs from test container
make stop              # Stop and remove test container
make publish           # Build and publish to GitHub
make publish-multiarch # Publish multi-architecture image
make run               # Run published image from GitHub
make clean             # Clean up local images and containers
```

## Docker Compose

For development or production with custom configuration:

```yaml
version: '3.8'

services:
  portal:
    image: ghcr.io/localrun-tech/portal:latest
    ports:
      - "8000:8000"
      - "3006:3006"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ~/.localrun:/app/storage
    environment:
      - DATABASE_URL=sqlite:////app/storage/localrun.db
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
```

## Development

See `backend/README.md` and `frontend/README.md` for development setup.
