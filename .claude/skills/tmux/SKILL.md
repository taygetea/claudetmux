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

**Style detection flags:**

```bash
ctmux capture SESSION --style=lines   # Line prefixes: > for selected, ! for error
ctmux capture SESSION --style=tags    # Inline tags: [i]selected[/i], [r]error[/r]
ctmux capture SESSION --style=ansi    # Raw ANSI escape codes
```

See "Style Encoding Reference" section below for details.

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

## Style Encoding Reference

Screen captures strip ANSI codes by default. The `--style` flag re-encodes style information in token-efficient formats that models can reliably parse.

### Why Not Raw ANSI?

Raw codes like `\x1b[7mtext\x1b[0m` are verbose and hard to parse. More importantly, models can't reliably count characters, so approaches like "next 16 chars are blue" fail. **Wrapping/tagging works** because the styled text is literally between markers.

### Style Levels

#### `--style=lines` (Recommended for most TUI work)

Prefixes entire lines based on dominant style:

```
  PID USER     COMMAND
> 123 root     htop           ← inverse video (selected)
  456 nobody   sshd
! Connection failed            ← red foreground (error)
* IMPORTANT                    ← bold
[cursor: 5,10]
```

Markers:
- `> ` = inverse/reverse video (selection highlight)
- `! ` = red foreground (errors, warnings)
- `* ` = bold text

**Token cost:** 2 chars per marked line. Handles 80%+ of TUI cases.

**Limitation:** Doesn't capture mid-line style changes.

#### `--style=tags` (For precise styling)

Inline semantic tags wrapped around styled regions:

```
Press [i]Enter[/i] to continue
Status: [r]FAILED[/r] - check [b]logs[/b]
Normal text here
[cursor: 5,10]
```

Tags:
- `[i]...[/i]` = inverse video
- `[r]...[/r]` = red foreground
- `[g]...[/g]` = green foreground
- `[y]...[/y]` = yellow foreground
- `[b]...[/b]` = bold
- `[u]...[/u]` = underline

**Token cost:** ~6 chars per styled region. Handles mid-line styling.

**Use when:** Selection spans partial lines, or you need to distinguish multiple colors.

#### `--style=ansi` (For debugging)

Preserves raw ANSI escape codes:

```
\x1b[7mSelected\x1b[0m normal \x1b[31merror\x1b[0m
```

**Use when:** Debugging style detection issues or need exact codes.

### Alternative Approaches Considered

#### Unicode Brackets
```
「selected」⟨error⟩
```
Compact but may not render consistently; models may not know convention.

#### Summary Block
```
<screen>
...content...
</screen>
[inverse: lines 3,7]
[red: line 5 cols 8-24]
```
Good for complex screens but requires cross-referencing.

#### Run-Length Encoding
```
[16 blue chars]Some text here
```
**Doesn't work** - models can't reliably count characters to tokens.

### Common ANSI Codes Detected

| Code | Meaning | Line Prefix | Tag |
|------|---------|-------------|-----|
| `\x1b[7m` | Inverse/reverse | `> ` | `[i]` |
| `\x1b[4Xm` | Background color (selection) | `> ` | `[i]` |
| `\x1b[1m` | Bold | `* ` | `[b]` |
| `\x1b[4m` | Underline | - | `[u]` |
| `\x1b[31m` | Red FG | `! ` | `[r]` |
| `\x1b[32m` | Green FG | - | `[g]` |
| `\x1b[33m` | Yellow FG | - | `[y]` |
| `\x1b[0m` | Reset | - | closing tag |

### Implementation Notes

Style detection requires capturing with ANSI codes enabled, then parsing and transforming. The transformation:

1. Capture screen with `escape_sequences=True`
2. Parse ANSI codes to build style map (which chars have which styles)
3. For `--style=lines`: find dominant style per line, add prefix
4. For `--style=tags`: insert open/close tags at style boundaries
5. Strip remaining ANSI codes from output
