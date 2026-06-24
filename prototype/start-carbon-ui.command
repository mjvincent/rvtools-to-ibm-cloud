#!/bin/bash
# Carbon UI Startup Script for macOS
# Double-click this file to start the entire Carbon UI environment

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  Carbon UI Environment Startup"
echo "=========================================="
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Function to detect Docker runtime
detect_docker_runtime() {
    if command -v orbctl &> /dev/null; then
        echo "orbstack"
    elif [ -d "/Applications/Docker.app" ]; then
        echo "docker-desktop"
    elif command -v colima &> /dev/null; then
        echo "colima"
    else
        echo "unknown"
    fi
}

# Function to start Docker runtime
start_docker_runtime() {
    local runtime=$1

    case $runtime in
        orbstack)
            echo "🚀 Starting OrbStack..."
            open -a OrbStack
            sleep 3
            ;;
        docker-desktop)
            echo "🚀 Starting Docker Desktop..."
            open -a Docker
            sleep 5
            ;;
        colima)
            echo "🚀 Starting Colima..."
            colima start
            ;;
        *)
            echo "❌ Error: No Docker runtime found!"
            echo ""
            echo "Please install one of the following:"
            echo "  • OrbStack (recommended): https://orbstack.dev"
            echo "  • Docker Desktop: https://www.docker.com/products/docker-desktop"
            echo "  • Colima: brew install colima"
            echo ""
            read -p "Press Enter to exit..."
            exit 1
            ;;
    esac
}

# Function to wait for Docker to be ready
wait_for_docker() {
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for Docker to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if docker info > /dev/null 2>&1; then
            echo "✅ Docker is ready!"
            echo ""
            return 0
        fi

        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    echo ""
    echo "❌ Error: Docker failed to start after 30 seconds"
    echo "Please check your Docker installation and try again."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️  Docker is not running"

    # Detect which Docker runtime is available
    DOCKER_RUNTIME=$(detect_docker_runtime)
    echo "ℹ️  Detected runtime: $DOCKER_RUNTIME"
    echo ""

    # Try to start it
    start_docker_runtime "$DOCKER_RUNTIME"

    # Wait for Docker to be ready
    wait_for_docker
else
    echo "✅ Docker is already running"
    echo ""
fi

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed!"
    echo "Please install Docker Desktop which includes docker-compose."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ docker-compose is available"
echo ""

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down 2>/dev/null || true
echo ""

# Build and start containers
echo "🏗️  Building and starting containers..."
echo "This may take a few minutes on first run..."
echo ""
docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
echo ""

# Wait for API to be healthy
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Waiting for API... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ API failed to start. Check logs with: docker-compose logs api"
    read -p "Press Enter to exit..."
    exit 1
fi

# Wait for Carbon UI to be ready
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Carbon UI is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Waiting for Carbon UI... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "❌ Carbon UI failed to start. Check logs with: docker-compose logs carbon-ui"
    read -p "Press Enter to exit..."
    exit 1
fi

# Wait for Streamlit to be ready
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo "✅ Streamlit is ready"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "   Waiting for Streamlit... ($ATTEMPT/$MAX_ATTEMPTS)"
    sleep 2
done

echo ""
echo "=========================================="
echo "  🎉 Carbon UI Environment is Ready!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  • Carbon UI:  http://localhost:3000"
echo "  • API:        http://localhost:8000"
echo "  • Streamlit:  http://localhost:8501"
echo "  • Postgres:   localhost:5432"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop all services:"
echo "  docker-compose down"
echo ""
echo "Opening Carbon UI in your browser..."
sleep 2

# Open Carbon UI in default browser
if command -v open &> /dev/null; then
    open http://localhost:3000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
fi

echo ""
echo "Press Ctrl+C to view this window, or close to keep services running."
echo ""

# Keep terminal open and show logs
docker-compose logs -f

# Made with Bob
