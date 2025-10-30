# CLI Usage Guide

The CLI (`jt`) is the primary interface for JamUpTaskMaster. Dashboard is passive eye candy.

## Installation

```bash
# From project root
./scripts/install-cli.sh

# Or manually
ln -s $(pwd)/scripts/jt ~/.local/bin/jt
```

## Quick Reference

```bash
jt ls              # List active tasks (default command)
jt add "text"      # Capture a task
jt md 0            # Mark task 0 done
jt po 1 3          # Put off task 1 for 3 days
jt li 2            # Lost interest in task 2
jt fo 3            # Fuck off task 3 (archive)
jt next            # Ask AI what to do
jt stats           # See overview
```

## Commands

### List Tasks
```bash
jt ls              # Active tasks (default)
jt                 # Same as 'jt ls'
jt ls done         # Completed tasks
jt ls put_off      # Put off tasks
```

### Add Tasks
```bash
jt add "order pillows walmart"
jt add "pick up screws"
jt a "shorthand works too"
```

### Manage Tasks
```bash
jt show 0          # Show details for task 0
jt md 0            # Mark done
jt po 0 7          # Put off for 7 days (default 3)
jt li 0            # Lost interest (comes back in 2 weeks)
jt fo 0            # Fuck off (archived)
jt del 0           # Delete (asks confirmation)
```

### AI Interaction
```bash
jt next            # AI suggests what to do based on current state
jt process         # Manually trigger processing (usually auto every 2min)
```

### Status Overview
```bash
jt stats           # See counts, critical items, quick wins
```

## Status Types

**active**: Current tasks you're working with
**captured**: Just added, not yet processed by AI
**done**: Completed
**put_off**: Not now, remind me in N days
**lost_interest**: Maybe later, check back in 2 weeks
**fuck_off**: Archived, out of sight (not deleted, can unarchive)

## Typical Workflow

```bash
# Throughout the day, capture stuff
# (or use hotkey → fuzzel → enter)
jt add "home depot boards"
jt add "take out trash"
jt add "check lima vm"

# When ready to work, see options
jt ls

# Output:
# [0] [shopping] Order boards from Home Depot [HIGH]
# [1] [health] Take out trash
# [2] [tech] Check lima VM setup

# Pick one that fits current energy
jt md 1            # Did the trash

# Ask AI for suggestion
jt next

# Output: "Take out trash first - it's blocking other
# tasks and only takes 5 minutes. Then you can tackle
# the board order."

# See overview
jt stats

# Output:
# Total: 15
#   active: 10
#   done: 3
#   put_off: 2
# Life critical: 1
# Quick wins: 3
```

## Advanced

### Change API endpoint
```bash
export JAMUP_API_BASE=http://192.168.1.100:8000
jt ls
```

### Integration with other tools
```bash
# Add from pipe
echo "buy milk" | xargs -I {} jt add {}

# Get list for processing
jt ls | grep CRITICAL

# Quick capture alias
alias t='jt add'
t "thing I need to do"
```

## Color Output

- **Red**: Critical priority / fuck off action
- **Orange**: High priority
- **Yellow**: Medium priority / put off action
- **Green**: Quick win / done action
- **Cyan**: Categories and labels
- **Gray**: Low priority / context

Colors work in any terminal with ANSI support.

## Tips

1. **Don't overthink capture** - Type whatever comes to mind, AI processes it later
2. **Use 'li' liberally** - Lost interest != failure, it's permission to move on
3. **'fo' is not delete** - Fuck off means "stop showing me this" not "erase forever"
4. **Check 'jt next' when stuck** - AI sees patterns you don't
5. **Stats show reality** - If 10 things are critical, none are critical

## Philosophy

The CLI is immediate and non-judgmental. It doesn't ask questions. It doesn't force decisions. It captures what's in your head and lets you interact when YOU'RE ready, not when IT demands attention.

Dashboard = passive awareness
CLI = active control
