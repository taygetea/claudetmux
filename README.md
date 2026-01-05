# ctmux

A CLI tool that enables Claude Code to interact with tmux sessions for TUI testing and automation.

## Requirements

- Python 3.12+
- tmux
- [uv](https://github.com/astral-sh/uv) (Python package manager)

## Installation

```bash
git clone <this-repo> ~/code/ctmux
cd ~/code/ctmux
./install.sh
```

This will:
1. Create a Python venv and install dependencies
2. Install `ctmux` to `~/bin/`
3. Install the Claude Code skill to `~/.claude/skills/tmux/`

Make sure `~/bin` is in your PATH:
```bash
export PATH="$HOME/bin:$PATH"
```

## Usage

### From the command line

```bash
# List tmux sessions
ctmux list

# Create a new session
ctmux new my-session --cmd "python3"

# Capture pane contents
ctmux capture my-session

# Send keys
ctmux send my-session C-c
ctmux type my-session "hello world" --enter

# Kill session
ctmux kill my-session --force
```

### From Claude Code

The skill is automatically discovered by Claude Code. Just ask Claude to interact with a TUI:

> "Start htop in a tmux session and show me the process tree"

> "Run the Python REPL and test this function for me"

## Commands Reference

| Command | Description |
|---------|-------------|
| `ctmux list` | List all tmux sessions |
| `ctmux new NAME` | Create a new session |
| `ctmux kill NAME` | Kill a session |
| `ctmux windows SESSION` | List windows in a session |
| `ctmux panes SESSION` | List panes in a session |
| `ctmux capture SESSION` | Capture pane contents |
| `ctmux watch SESSION` | Watch for pane changes |
| `ctmux send SESSION KEYS...` | Send key sequences |
| `ctmux type SESSION TEXT` | Type literal text |
| `ctmux mouse SESSION X Y` | Send mouse click |

## Uninstall

```bash
./uninstall.sh
```

## Development

```bash
# Activate the venv
source .venv/bin/activate

# Run directly
python -m claudetmux.cli --help

# Or use uv
uv run ctmux --help
```
