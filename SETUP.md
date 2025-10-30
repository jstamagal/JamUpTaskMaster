# JamUpTaskMaster - Setup Guide

## What This Is

A task management system for neurodivergent workflows. No questions, no anxiety, just capture and flow.

- **Instant capture**: Hotkey → type → done (< 1 second)
- **AI processing**: gpt-oss-assistant understands your cryptic notes
- **Options, not orders**: Dashboard shows 5-10 tasks, you pick what fits
- **Modular**: Built to expand with desktop integration, RAG, whatever you need

## Prerequisites

1. **Ollama running** on port 11434 (or configure different port)
2. **gpt-oss-20b-assistant** model available (or change in config)
3. **Python 3.11+** (for non-container setup)
4. **Podman or Docker** (for container setup)
5. **fuzzel/rofi/wofi/bemenu** (for input capture)

## Quick Start (Container - Recommended)

```bash
# 1. Make sure Ollama is running with gpt-oss-assistant
OLLAMA_HOST=127.0.0.1:11434 ollama list | grep gpt-oss

# 2. Build and start services
podman-compose up -d --build
# OR
docker-compose up -d --build

# 3. Check it's running
curl http://localhost:8000/health

# 4. Open dashboard on second screen
firefox http://localhost:8000

# 5. Test capture script
./scripts/capture-task.sh

# 6. Bind to hotkey (see below)
```

## Alternative: Local Python Setup

```bash
# 1. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # or `venv/bin/activate.fish` for fish shell

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start API server (terminal 1)
cd ..
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# 4. Start background worker (terminal 2)
python -m backend.app.services.background_worker

# 5. Open dashboard
firefox http://localhost:8000
```

## Niri Compositor Hotkey Setup

Add to your `~/.config/niri/config.kdl`:

```kdl
binds {
    // ... your existing binds ...

    // JamUp task capture - Super+T
    Mod+T { spawn "bash" "/path/to/JamUpTaskMaster/scripts/capture-task.sh"; }
}
```

Reload Niri config:
```bash
niri msg action reload-config
```

## Configuration

Edit `config/config.env`:

```bash
# Use different model
TASK_MODEL=qwen2.5:14b

# Use different Ollama instance
OLLAMA_API_BASE=http://192.168.1.100:11434

# Process tasks more frequently (60 seconds instead of 120)
WORKER_INTERVAL=60

# Different port for API
PORT=9000
```

## Testing the Workflow

1. **Hit your hotkey** (e.g., Super+T)
2. **Type something cryptic**: "pillows walmart"
3. **Hit Enter** - should return instantly
4. **Check dashboard** after ~2 minutes
5. **See processed task** with priority, category, flags

## Troubleshooting

### Tasks not processing?

```bash
# Check worker logs
podman logs jamup-worker
# OR
docker logs jamup-worker

# Manually trigger processing
curl -X POST http://localhost:8000/api/tasks/process
```

### Can't reach Ollama from container?

Make sure `extra_hosts` in compose.yaml is correct:
```yaml
extra_hosts:
  - "host.containers.internal:host-gateway"
```

Test from container:
```bash
podman exec -it jamup-api curl http://host.containers.internal:11434/api/tags
```

### Dashboard not updating?

- Check browser console for errors
- Verify API is reachable: `curl http://localhost:8000/api/tasks`
- Dashboard auto-refreshes every 30 seconds

## Architecture for Future Expansion

### Adding Desktop Integration

Create plugins in `backend/app/plugins/`:
```python
# Example: Niri IPC integration
from app.events import EventBus

class NiriPlugin:
    async def on_task_created(self, task):
        # Hook into Niri IPC
        pass
```

### Adding RAG for Documentation

```python
# Example: AUR package hook
class AURPlugin:
    async def on_package_installed(self, pkg_name):
        # Fetch docs, ingest to vector DB
        pass
```

### Adding More Models

```python
# config/models.py
MODELS = {
    "secretary": "qwen2.5:14b",
    "analyzer": "granite:13b",
    "creativity": "mistral:7b"
}
```

System is built modular - just extend without rewriting core.

## Next Steps

1. Use it for a few days - see if it helps you order those pillows
2. Note what works, what doesn't
3. Extend based on your actual workflow
4. Share with others who need it

## License

MIT - See LICENSE file
