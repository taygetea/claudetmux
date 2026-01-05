---
description: "Interact with tmux sessions to view and control TUI applications"
allowed-tools:
  - Bash
  - Read
---

# tmux Interaction Skill

Use the `ctmux` CLI tool to interact with tmux sessions. This enables viewing pane contents, sending keystrokes/mouse input, and running multi-step TUI testing macros.

## CLI Location

After running the install script, `ctmux` is available globally:

```bash
ctmux --help
```

## Commands

### Session Management

```bash
# List all sessions
ctmux list [--json]

# List windows in a session
ctmux windows SESSION [--json]

# List panes in a session/window
ctmux panes SESSION [--window NAME] [--json]

# Create a new session
ctmux new SESSION_NAME [--window NAME] [--cmd "initial command"] [--width 120] [--height 40]

# Kill a session
ctmux kill SESSION [--force]
```

### Screen Capture

```bash
# Capture current pane contents
ctmux capture SESSION [--pane ID] [--lines N] [--history]

# Capture only if changed (avoids redundant output)
ctmux capture SESSION --if-changed

# Watch for changes with timeout
ctmux watch SESSION [--interval 0.5] [--timeout 30] [--until "text to wait for"]
```

### Input

```bash
# Send tmux key sequences (e.g., Enter, C-c, Escape)
ctmux send SESSION KEY1 KEY2 ... [--pane ID] [--literal] [--enter]

# Type literal text (for user input)
ctmux type SESSION "text to type" [--pane ID] [--enter] [--delay MS]

# Mouse click at coordinates
ctmux mouse SESSION X Y [--pane ID] [--click left|right|middle] [--double]
```

## Best Practices

### Change Detection

Always use `--if-changed` when polling to avoid sending duplicate screen content:

```bash
# Good: Only outputs when content changes
ctmux capture my-session --if-changed

# Bad: Outputs same content repeatedly
ctmux capture my-session
```

### Waiting for Output

Use `watch --until` to wait for specific text to appear:

```bash
# Wait for prompt to return after a command
ctmux type my-session "make build" --enter
ctmux watch my-session --until "$ " --timeout 60
```

### Multi-step Macros

For testing TUI applications, chain commands with change detection:

```bash
# 1. Start the TUI app
ctmux type my-session "vim test.txt" --enter
sleep 0.5
ctmux capture my-session --if-changed

# 2. Enter insert mode
ctmux send my-session i
ctmux capture my-session --if-changed

# 3. Type some text
ctmux type my-session "Hello, world!"
ctmux capture my-session --if-changed

# 4. Save and quit
ctmux send my-session Escape
ctmux type my-session ":wq" --enter
ctmux capture my-session --if-changed
```

### Error Detection

If a command produces unexpected output, the screen capture will show the error. Compare expected vs actual output to diagnose issues.

### Key Sequences

Common tmux key sequences for `ctmux send`:
- `Enter` - Enter/Return key
- `Escape` - Escape key
- `Space` - Space bar
- `Tab` - Tab key
- `BSpace` - Backspace
- `C-c` - Ctrl+C
- `C-d` - Ctrl+D
- `C-z` - Ctrl+Z
- `Up`, `Down`, `Left`, `Right` - Arrow keys
- `PgUp`, `PgDn` - Page up/down
- `Home`, `End` - Home/End keys
- `F1` through `F12` - Function keys

## Example: Testing a REPL

```bash
# Create session for testing
ctmux new test-repl --cmd "python3"

# Wait for Python prompt
ctmux watch test-repl --until ">>>" --timeout 10

# Run some code
ctmux type test-repl "print('hello')" --enter
sleep 0.2
ctmux capture test-repl --if-changed

# Exit
ctmux send test-repl C-d
ctmux kill test-repl --force
```
