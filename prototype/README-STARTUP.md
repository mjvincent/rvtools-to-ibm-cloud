# Carbon UI Quick Start Scripts

## Overview

These scripts provide one-click startup for the entire Carbon UI environment, including:
- Carbon UI (Next.js + React + IBM Carbon Design)
- FastAPI backend
- Streamlit production app
- PostgreSQL database

## Usage

### macOS / Linux

**Double-click:** `start-carbon-ui.command`

Or from terminal:
```bash
cd prototype
./start-carbon-ui.command
```

### Windows

**Double-click:** `start-carbon-ui.bat`

Or from Command Prompt:
```cmd
cd prototype
start-carbon-ui.bat
```

## What the Scripts Do

1. 🔍 **Detect Docker runtime** (OrbStack, Docker Desktop, or Colima)
2. 🚀 **Auto-start Docker** if not running (waits up to 30 seconds)
3. ✅ **Verify docker-compose** is available
4. 🛑 **Stop any existing containers** (clean slate)
5. 🏗️ **Build and start all containers** (may take a few minutes first time)
6. ⏳ **Wait for services to be ready** (health checks for API, UI, Streamlit)
7. 🌐 **Open Carbon UI in your browser** automatically
8. 📋 **Show live logs** (Ctrl+C to stop viewing, services keep running)

## Services Started

| Service | URL | Description |
|---------|-----|-------------|
| **Carbon UI** | http://localhost:3000 | Modern React UI for network planning |
| **API** | http://localhost:8000 | FastAPI backend for Carbon UI |
| **Streamlit** | http://localhost:8501 | Production Streamlit workbench |
| **Postgres** | localhost:5432 | Database for project persistence |

## Requirements

### Docker Runtime (Auto-Detected & Auto-Started!)

The script automatically detects and starts your Docker runtime. Supported:

- **OrbStack** (recommended for macOS): https://orbstack.dev
  - Faster, lighter, more efficient than Docker Desktop
  - Auto-detected via `orbctl` command

- **Docker Desktop**: https://www.docker.com/products/docker-desktop
  - Auto-detected via application path
  - Works on macOS and Windows

- **Colima** (macOS alternative): `brew install colima`
  - Auto-detected via `colima` command

**You don't need to manually start Docker!** The script will:
1. Detect which Docker runtime you have installed
2. Start it automatically if it's not running
3. Wait for it to be ready before proceeding

### System Resources

- **8GB RAM** minimum (16GB recommended)
- **10GB disk space** for Docker images

## Troubleshooting

### "Docker is not running" / Auto-start fails

**If you have OrbStack:**
- The script will automatically open OrbStack
- Wait a few seconds for it to start
- Script will proceed once ready

**If you have Docker Desktop:**
- The script will automatically open Docker Desktop
- Wait for the whale icon to appear in system tray
- Script will proceed once ready

**If auto-start fails:**
- Manually start your Docker runtime
- Run the script again
- It will detect Docker is running and proceed

### "No Docker runtime found"

Install one of the supported Docker runtimes:
- **OrbStack** (recommended): https://orbstack.dev
- **Docker Desktop**: https://www.docker.com/products/docker-desktop
- **Colima**: `brew install colima` (macOS only)

### "Port already in use"
- Stop any services using ports 3000, 8000, 8501, or 5432
- Or run: `docker-compose down` to stop existing containers

### Services won't start
- Check Docker Desktop has enough resources allocated
- View logs: `docker-compose logs -f`
- Rebuild: `docker-compose up -d --build --force-recreate`

### Browser doesn't open automatically
- Manually navigate to: http://localhost:3000

## Stopping Services

### Option 1: Keep services running
- Close the terminal window
- Services continue running in background

### Option 2: Stop services
- Press `Ctrl+C` in the terminal
- Or run: `docker-compose down`

## Manual Control

If you prefer manual control:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# View specific service logs
docker-compose logs -f api
docker-compose logs -f app
```

## First Time Setup

The first run will take longer because Docker needs to:
1. Download base images (Python, Node.js, Postgres)
2. Build application images
3. Install dependencies
4. Initialize database

**Estimated first run time:** 5-10 minutes

Subsequent runs are much faster (30-60 seconds).

## Development Workflow

1. **Start environment:** Double-click startup script
2. **Make code changes:** Edit files in your IDE
3. **See changes:**
   - Carbon UI: Auto-reloads (Hot Module Replacement)
   - API: Auto-reloads (uvicorn --reload)
   - Streamlit: Refresh browser
4. **Stop environment:** `docker-compose down`

## Accessing Services

### Carbon UI
- **URL:** http://localhost:3000
- **Features:** Network planning, VM assignment, Terraform generation

### API
- **URL:** http://localhost:8000
- **Docs:** http://localhost:8000/docs (Swagger UI)
- **Health:** http://localhost:8000/health

### Streamlit
- **URL:** http://localhost:8501
- **Features:** RVTools upload, readiness assessment, Terraform export

### Database
- **Host:** localhost
- **Port:** 5432
- **Database:** rvtools
- **User:** rvtools
- **Password:** rvtools_password

## Next Steps

After starting the environment:

1. **Upload RVTools workbook** in Streamlit (http://localhost:8501)
2. **Create project** in Carbon UI (http://localhost:3000)
3. **Plan network** using visual tools
4. **Assign VMs** to subnets and security groups
5. **Generate Terraform** and download ZIP

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- View documentation: `docs/` directory
- Check Docker Desktop resources (CPU, Memory, Disk)

---

**Made with ❤️ for IBM Cloud migrations**
