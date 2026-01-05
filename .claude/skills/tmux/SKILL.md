---
description: "Interact with tmux sessions to view and control TUI applications"
allowed-tools:
  - Bash
  - Read
---

# tmux Interaction Skill

Use `ctmux` to interact with tmux sessions for TUI automation and testing.

## Important: Use Subagents for Multi-Step TUI Tasks

**Each ctmux call produces significant output (full screen captures).** For tasks involving more than 2-3 ctmux calls, spawn a subagent to manage context:

```
Use Task tool with subagent_type="general-purpose" for TUI automation tasks.
The subagent can make many ctmux calls without bloating the main conversation.
```

This keeps the parent conversation lean while the subagent handles the verbose screen captures.

## Quick Reference

```bash
ctmux new SESSION [--cmd "command"]     # Create session
ctmux capture SESSION                    # Get screen + cursor position
ctmux capture SESSION --if-changed       # Only if screen changed
ctmux send SESSION KEY1 KEY2 ...         # Send key sequences
ctmux type SESSION "text" [--enter]      # Type literal text
ctmux kill SESSION --force               # Clean up
```

## Capture Output Format

Default capture shows visible viewport + cursor metadata:
```
<screen content>
[cursor: 5,10]
```

Flags:
- `--if-changed` - suppress output if screen unchanged (use when polling)
- `--history` - include scrollback history
- `--raw` - omit cursor metadata

## Key Sequences

For `ctmux send`:
- `Enter`, `Escape`, `Space`, `Tab`, `BSpace`
- `C-c`, `C-d`, `C-z` (Ctrl+key)
- `Up`, `Down`, `Left`, `Right`
- `F1` through `F12`
- `PgUp`, `PgDn`, `Home`, `End`

## Known Limitations

### Character Escaping (Shell History Expansion)

The `!` character has special meaning in bash/zsh (history expansion). When typing text containing `!`, the receiving shell may escape it:

```bash
ctmux type session "print('hello!')"
# May appear as: print('hello\!')
```

**This is shell behavior, not a ctmux bug.** Workarounds:
- Use single quotes in the target shell: `ctmux type session "echo 'hello!'"`
- Avoid `!` in automation scripts where possible
- The target application still receives the text (escaping is visual)

### Colors and Selection Indicators

Screen captures are plain text - ANSI color codes are stripped. This means:
- You cannot see which item is "selected" (usually inverse video)
- Error messages (red) look like normal text
- Syntax highlighting is not visible

**Current workarounds:**
- Use cursor position `[cursor: X,Y]` to track navigation
- Check for text changes to infer state (e.g., menu text changes when selection moves)
- Look for text indicators (e.g., `>` prefix, `[x]` checkboxes)

**Future:** May add `--ansi` flag to preserve escape codes, or transform to token-efficient markers like `[SEL]` for selected lines.

### Timing

TUI apps need time to render. Use:
- `sleep 0.3` after sending input before capture
- `watch --until "text"` to wait for specific output
- `--if-changed` to avoid capturing stale content

## Example: Testing htop

```bash
# Create session and launch htop
ctmux new htop-test --cmd "htop"
sleep 1

# Open setup menu
ctmux send htop-test F2
sleep 0.3
ctmux capture htop-test

# Navigate and exit
ctmux send htop-test Escape
ctmux send htop-test q
ctmux kill htop-test --force
```

## Example: Python REPL

```bash
ctmux new py --cmd "python3"
ctmux watch py --until ">>>" --timeout 10

ctmux type py "2 + 2" --enter
sleep 0.2
ctmux capture py --if-changed

ctmux send py C-d
ctmux kill py --force
```
