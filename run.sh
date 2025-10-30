#!/bin/bash
# Quick start script for JamUpTaskMaster

set -e

echo "🚀 Starting JamUpTaskMaster..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Error: Ollama is not running on port 11434"
    echo "   Start Ollama first: systemctl --user start ollama"
    exit 1
fi

# Check if model exists
if ! OLLAMA_HOST=127.0.0.1:11434 ollama list | grep -q "gpt-oss-20b-assistant"; then
    echo "⚠️  Warning: gpt-oss-20b-assistant model not found"
    echo "   Make sure your model is available or update TASK_MODEL in config/config.env"
fi

# Detect if we're in distrobox
if [ -f /run/.containerenv ] || [ -f /.dockerenv ] || [ -n "$CONTAINER_ID" ]; then
    echo "📦 Running in container, using host podman..."
    HOST_EXEC="distrobox-host-exec"
else
    HOST_EXEC=""
fi

# Determine which container runtime to use
if $HOST_EXEC command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="$HOST_EXEC podman-compose"
elif $HOST_EXEC command -v podman &> /dev/null; then
    COMPOSE_CMD="$HOST_EXEC podman compose"
elif $HOST_EXEC command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="$HOST_EXEC docker-compose"
elif $HOST_EXEC command -v docker &> /dev/null; then
    COMPOSE_CMD="$HOST_EXEC docker compose"
else
    echo "❌ Error: No container runtime found (podman or docker)"
    echo "   Install podman: sudo dnf install podman podman-compose"
    exit 1
fi

echo "📦 Using: $COMPOSE_CMD"

# Create data directory
mkdir -p data

# Build and start
echo "🔨 Building containers..."
$COMPOSE_CMD build

echo "▶️  Starting services..."
$COMPOSE_CMD up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 3

# Check health
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✅ API is running!"
else
    echo "❌ API failed to start. Check logs:"
    echo "   $COMPOSE_CMD logs api"
    exit 1
fi

echo ""
echo "🎉 JamUpTaskMaster is running!"
echo ""
echo "📊 Dashboard: http://localhost:8000"
echo "📝 API docs:  http://localhost:8000/docs"
echo ""
echo "🔥 Test capture:"
echo "   ./scripts/capture-task.sh"
echo ""
echo "📋 View logs:"
echo "   $COMPOSE_CMD logs -f api"
echo "   $COMPOSE_CMD logs -f worker"
echo ""
echo "🛑 Stop services:"
echo "   $COMPOSE_CMD down"
