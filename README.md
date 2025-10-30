# JamUpTaskMaster

**Task management for people whose brains work differently.**

Built for ADHD, autism, CPTSD, TBI survivors, former addicts, and anyone who can't use traditional task managers because they were designed for neurotypical corporate workers.

## The Problem

You get ideas constantly. You start 20 things, finish none. Traditional task managers:
- Ask too many questions (anxiety trigger)
- Demand rigid time schedules (you work in bursts)
- Force you to categorize (executive dysfunction says no)
- Make you pick "most important" (everything feels urgent or nothing does)

You need to order pillows. You've tried for 3 days. You keep seeing shiny things. You give up and eat granola bars for dinner again.

## The Solution

1. **Hit hotkey** → type "pillows walmart" → **done** (< 1 second)
2. AI processes it in background (you don't wait, don't answer questions)
3. Dashboard shows **5-10 options** based on priority
4. You pick what fits your current energy/focus
5. **You order the fucking pillows**

## Features

- ⚡ **Instant capture**: No friction, no questions, < 100ms response
- 🤖 **AI understanding**: gpt-oss-20b-assistant interprets your cryptic notes
- 🎯 **Smart priority**: Understands "heart pills" > "cool VM project"
- 🔄 **Pattern recognition**: Notices when you're stuck on something
- 🚀 **Quick wins**: Flags fast tasks for momentum
- 🆘 **Life critical**: Auto-detects health/food/meds priorities
- 📊 **Options not orders**: Shows 5-10 tasks, you choose
- 🔧 **Modular**: Built to extend with desktop integration, RAG, whatever

## Quick Start

```bash
# 1. Start it
./run.sh

# 2. Open dashboard (second monitor)
firefox http://localhost:8000

# 3. Bind hotkey (Niri example)
# Add to ~/.config/niri/config.kdl:
# Mod+T { spawn "bash" "/path/to/scripts/capture-task.sh"; }

# 4. Use it
# Hit hotkey → type task → enter → forget about it
# Check dashboard when you want options
```

See [SETUP.md](SETUP.md) for detailed setup and configuration.

## Architecture

- **Input**: Hotkey → fuzzel/rofi/wofi → instant API capture
- **Backend**: FastAPI + SQLite + async processing
- **AI**: Single gpt-oss-20b-assistant with full context awareness
- **Dashboard**: Vanilla HTML/JS with Tailwind (no build step)
- **Container**: Podman/Docker for easy deployment

Built modular for future expansion:
- Desktop integration (compositor IPC, window tracking)
- AUR package hooks → auto-RAG documentation
- MCP integration for tools/services
- Multi-model orchestration
- Vector memory for long-term context

## Components

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── models/       # SQLAlchemy models
│   │   ├── llm/          # AI processing
│   │   ├── services/     # Background workers
│   │   └── static/       # Dashboard HTML
│   └── requirements.txt
├── scripts/
│   └── capture-task.sh   # Input capture
├── config/
│   └── config.env        # Configuration
├── Containerfile         # Container build
├── compose.yaml          # Multi-container setup
└── run.sh               # One-command start
```

## Philosophy

Traditional task management assumes:
- Consistent executive function
- Time-based scheduling
- Linear priorities
- Question tolerance
- Neurotypical cognition

This assumes:
- **Burst-based work** (hyperfocus then nothing)
- **Pattern-based priorities** (context matters)
- **Anxiety-free input** (no interrogation)
- **Cognitive flexibility** (options > orders)
- **Neurodivergent workflows** (different, not broken)

## Who This Is For

- ADHD folks who start 20 things and finish none
- Autistic people who hate arbitrary time constraints
- TBI survivors with memory issues
- Former addicts dealing with neurotoxicity
- Anyone whose brain works in bursts not schedules
- People who need adaptive tech for cognitive differences

## License

MIT - Use it, fork it, adapt it. If it helps you order pillows and eat actual food, that's enough.

## Contributing

This is built for expansion. See [SETUP.md](SETUP.md) for architecture notes. PRs welcome, especially:
- Desktop environment integrations
- Additional model support
- Mobile/notification systems
- Accessibility features
