# ctmux Testing Observations

Notes from a testing session using ctmux to interact with various TUI applications (htop, vim, mc, python REPL).

## Summary

The tool works and is usable for TUI automation, but there are several pain points around timing, feedback, and visual ambiguity that could be improved.

---

## Pain Points

### 1. Timing is Guesswork

**Problem:** After sending input, I had to guess how long to `sleep` before capturing. Different TUIs need different wait times.

**Examples:**
- htop needed ~0.5s to fully render
- vim mode changes were near-instant (~0.2s)
- mc took ~0.5s to load initially
- Python REPL needed variable time depending on command complexity

**Current workaround:** Manual `sleep` calls between send/type and capture:
```bash
ctmux send htop-test F2 && sleep 0.3 && ctmux capture htop-test
```

**Suggestions:**
- The `watch --until "text"` command exists but I didn't use it because I didn't always know what text to wait for
- A `capture --wait-for-idle` that detects when screen stops changing would be helpful
- Or `capture --min-delay 300` that ensures at least 300ms since last screen change

### 2. No Visual Cursor/Selection Indicator

**Problem:** In the captured output, I couldn't see where the cursor was or which item was selected. This made it hard to know if navigation succeeded.

**Examples:**
- In htop's Setup menu, after pressing Down twice, I couldn't tell which option was highlighted
- In mc, the selected file/directory wasn't visually distinct in the capture
- In vim, cursor position wasn't visible in the text capture

**Why this matters:** When automating, I need to verify "did my Down keypress actually move selection?" Without seeing the highlight, I'm flying blind.

**Suggestions:**
- Capture ANSI escape codes and parse them to indicate cursor position
- Add a `--show-cursor` flag that marks cursor position in output
- Or provide cursor coordinates as metadata in the output

### 3. Unclear if Input Was Received vs Buffered

**Problem:** Some keys seemed to get buffered and execute after the TUI exited, rather than being processed by the TUI.

**Example:** After quitting mc with F10, the shell showed:
```
$ Down Down Down
zsh:1: command not found: Down
```

This suggests the Down keypresses I sent earlier were buffered somewhere and executed as shell commands after mc exited.

**Possible causes:**
- Sent keys before TUI was fully ready to receive them
- Race condition between key sending and TUI's input processing
- tmux buffering behavior

**Suggestions:**
- Add a `--wait-ready` option that waits for the pane to be ready before sending
- Provide feedback about whether the target application actually consumed the input
- Document best practices for avoiding this (e.g., always capture first to ensure TUI is ready)

### 4. F-key Behavior Was Inconsistent

**Problem:** Some F-keys worked (F2, F5, F10) but others didn't seem to work as expected (F3 in htop didn't open search prompt).

**Example:**
```bash
ctmux send htop-test F3  # Expected: search prompt appears
# Actual: no visible change, search prompt not shown
```

**Possible causes:**
- F-key sequences might vary by terminal type
- htop might need a different key sequence
- The search prompt might have appeared but wasn't captured properly

**Suggestions:**
- Document which key names are supported and their exact sequences
- Provide a debug mode that shows what bytes were actually sent
- Test with different TERM settings

### 5. Special Character Escaping

**Problem:** Some characters got escaped unexpectedly.

**Example:**
```bash
ctmux type vim-test "print('Hello from Python via ctmux!')"
# Result in Python: print('Hello from Python via ctmux\!')
```

The `!` was escaped with a backslash, which appeared in the actual output.

**Suggestions:**
- Document which characters need escaping and which don't
- Provide a `--raw` mode that sends exact bytes without shell interpretation
- Or handle escaping internally so users don't need to think about it

### 6. No Feedback on What Was Actually Rendered

**Problem:** The capture shows text but not styling (colors, bold, inverse video). This means I can't distinguish:
- Selected items (usually inverse video)
- Error messages (usually red)
- Prompts vs output
- Insert mode indicators

**Example:** htop uses colors extensively. The capture showed CPU percentages but not the colored bars that indicate load.

**Suggestions:**
- Option to capture with ANSI codes intact
- Option to render a simplified version showing [SELECTED], [HIGHLIGHTED], etc.
- Metadata output showing color regions

### 7. Session History Pollution

**Problem:** The capture includes scrollback history, so I see old commands mixed with current state.

**Example:** After exiting vim and starting mc, my captures showed:
```
❯ vim /tmp/test_ctmux.txt
❯ git status -u .
...
```

This history made it harder to find the actual current screen content.

**Suggestions:**
- A `--current-only` flag that shows only the visible viewport
- Clear screen detection to know where current content starts
- Or create sessions with limited/no scrollback for cleaner captures

### 8. Hard to Know When TUI Has Fully Loaded

**Problem:** No signal that a TUI has finished its initial render and is ready for input.

**Example workflow:**
```bash
ctmux new test --cmd "htop"
sleep 1  # Hope this is enough?
ctmux capture test
```

If htop is slow to start (first run, system busy), 1 second might not be enough. If it's fast, I'm wasting time.

**Suggestions:**
- `ctmux wait SESSION --ready` that blocks until pane has stable content
- Heuristic: wait for function key bar at bottom (common in TUIs)
- Return session state (loading/ready/exited) in output

---

## What Worked Well

1. **Session management** - `new`, `kill`, `list` all worked smoothly
2. **Basic key sequences** - Enter, Escape, arrow keys, Ctrl+key all worked
3. **Text typing** - `ctmux type` reliably entered text
4. **Screen capture** - Content was readable and correctly formatted
5. **Multiple commands** - Chaining with `&&` worked for sequential operations

---

## Suggested Testing Protocol

Based on my experience, here's a more robust testing pattern:

```bash
# 1. Create session
ctmux new test --cmd "htop"

# 2. Wait and verify TUI loaded
sleep 1
ctmux capture test | grep -q "F1Help" || echo "Not ready yet"

# 3. Send input
ctmux send test F2

# 4. Wait for change and capture
sleep 0.3
ctmux capture test --if-changed

# 5. Verify expected state before next action
# ... check output contains expected content ...

# 6. Clean up
ctmux kill test --force
```

---

## Feature Requests (Priority Order)

1. **Cursor position indication** - Most impactful for automation
2. **Wait-for-stable-screen** - Eliminates timing guesswork
3. **Current viewport only** - Cleaner captures without history
4. **Debug mode** - See exactly what bytes are sent/received
5. **Character escaping documentation** - Avoid surprises with special chars

---

## Environment Notes

- OS: Ubuntu 22.04 on WSL2
- tmux version: (not checked)
- Terminal: Windows Terminal
- Shell: zsh with oh-my-zsh

These observations are from a single test session and may not cover all edge cases.
