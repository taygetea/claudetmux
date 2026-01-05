"""Main CLI for claudetmux."""

import hashlib
import json
import sys
from pathlib import Path

import click
import libtmux


# Store last screen hash to detect changes (persisted to temp file)
import tempfile

HASH_FILE = Path(tempfile.gettempdir()) / "ctmux_screen_hashes.json"


def load_screen_hashes() -> dict[str, str]:
    """Load screen hashes from temp file."""
    if HASH_FILE.exists():
        try:
            return json.loads(HASH_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_screen_hash(key: str, hash_val: str):
    """Save a screen hash to temp file."""
    hashes = load_screen_hashes()
    hashes[key] = hash_val
    HASH_FILE.write_text(json.dumps(hashes))


def get_server() -> libtmux.Server:
    """Get the tmux server connection."""
    try:
        return libtmux.Server()
    except Exception as e:
        click.echo(f"Error connecting to tmux server: {e}", err=True)
        sys.exit(1)


def find_session(server: libtmux.Server, name: str) -> libtmux.Session:
    """Find a session by name."""
    sessions = server.sessions.filter(session_name=name)
    if not sessions:
        click.echo(f"Session '{name}' not found", err=True)
        sys.exit(1)
    return sessions[0]


def find_pane(session: libtmux.Session, pane_id: str | None = None) -> libtmux.Pane:
    """Find a pane in session. Returns active pane if no ID specified."""
    if pane_id:
        for window in session.windows:
            for pane in window.panes:
                if pane.pane_id == pane_id or str(pane.pane_index) == pane_id:
                    return pane
        click.echo(f"Pane '{pane_id}' not found", err=True)
        sys.exit(1)
    # Return active pane
    window = session.active_window
    if window:
        pane = window.active_pane
        if pane:
            return pane
    click.echo("No active pane found", err=True)
    sys.exit(1)


@click.group()
def main():
    """Claude tmux interface - interact with tmux sessions."""
    pass


# --- Session Management ---


@main.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_sessions(as_json: bool):
    """List all tmux sessions."""
    server = get_server()
    sessions = []
    for s in server.sessions:
        info = {
            "name": s.session_name,
            "id": s.session_id,
            "windows": len(s.windows),
            "attached": s.session_attached == "1",
        }
        sessions.append(info)

    if as_json:
        click.echo(json.dumps(sessions, indent=2))
    else:
        if not sessions:
            click.echo("No tmux sessions found")
        else:
            for s in sessions:
                attached = "*" if s["attached"] else ""
                click.echo(f"{s['name']}{attached} ({s['windows']} windows)")


@main.command("windows")
@click.argument("session")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_windows(session: str, as_json: bool):
    """List windows in a session."""
    server = get_server()
    sess = find_session(server, session)
    windows = []
    for w in sess.windows:
        info = {
            "name": w.window_name,
            "id": w.window_id,
            "index": w.window_index,
            "panes": len(w.panes),
            "active": w == sess.active_window,
        }
        windows.append(info)

    if as_json:
        click.echo(json.dumps(windows, indent=2))
    else:
        for w in windows:
            active = "*" if w["active"] else ""
            click.echo(f"{w['index']}: {w['name']}{active} ({w['panes']} panes)")


@main.command("panes")
@click.argument("session")
@click.option("--window", "-w", help="Window name or index")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_panes(session: str, window: str | None, as_json: bool):
    """List panes in a session/window."""
    server = get_server()
    sess = find_session(server, session)

    target_windows = sess.windows
    if window:
        target_windows = [
            w for w in sess.windows if w.window_name == window or str(w.window_index) == window
        ]

    panes = []
    for w in target_windows:
        for p in w.panes:
            info = {
                "id": p.pane_id,
                "index": p.pane_index,
                "window": w.window_name,
                "window_index": w.window_index,
                "width": p.pane_width,
                "height": p.pane_height,
                "active": p == w.active_pane,
            }
            panes.append(info)

    if as_json:
        click.echo(json.dumps(panes, indent=2))
    else:
        for p in panes:
            active = "*" if p["active"] else ""
            click.echo(f"{p['id']}{active} [{p['window']}:{p['index']}] {p['width']}x{p['height']}")


# --- Screen Capture ---


@main.command("capture")
@click.argument("session")
@click.option("--pane", "-p", help="Pane ID or index")
@click.option("--lines", "-n", default=50, help="Number of history lines (with --history)")
@click.option("--if-changed", is_flag=True, help="Only output if screen changed")
@click.option("--history", "-H", is_flag=True, help="Include scrollback history")
@click.option("--raw", "-r", is_flag=True, help="Raw output without cursor metadata")
def capture_pane(session: str, pane: str | None, lines: int, if_changed: bool, history: bool, raw: bool):
    """Capture pane contents.

    By default, captures only the visible viewport and appends cursor position.
    Use --history to include scrollback, --raw for plain output.
    """
    server = get_server()
    sess = find_session(server, session)
    p = find_pane(sess, pane)

    # Capture visible viewport only (default) or with history
    if history:
        content = p.capture_pane(start=f"-{lines}", end="-0")
    else:
        # Visible viewport only - no scrollback
        content = p.capture_pane(start=0, end="-")

    if isinstance(content, list):
        content = "\n".join(content)

    # Check if changed
    if if_changed:
        content_hash = hashlib.md5(content.encode()).hexdigest()
        pane_key = f"{session}:{p.pane_id}"
        hashes = load_screen_hashes()
        if hashes.get(pane_key) == content_hash:
            click.echo("[no change]")
            return
        save_screen_hash(pane_key, content_hash)

    click.echo(content)

    # Append cursor metadata unless --raw
    if not raw:
        click.echo(f"[cursor: {p.cursor_x},{p.cursor_y}]")


@main.command("watch")
@click.argument("session")
@click.option("--pane", "-p", help="Pane ID or index")
@click.option("--interval", "-i", default=0.5, help="Poll interval in seconds")
@click.option("--timeout", "-t", default=30.0, help="Max time to watch")
@click.option("--until", "-u", help="Stop when this text appears")
def watch_pane(session: str, pane: str | None, interval: float, timeout: float, until: str | None):
    """Watch pane for changes, outputting only when content changes."""
    import time

    server = get_server()
    sess = find_session(server, session)
    p = find_pane(sess, pane)

    last_hash = ""
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed >= timeout:
            click.echo(f"[timeout after {timeout}s]", err=True)
            break

        content = p.capture_pane(start=0, end="-")  # Visible viewport only
        if isinstance(content, list):
            content = "\n".join(content)

        content_hash = hashlib.md5(content.encode()).hexdigest()

        if content_hash != last_hash:
            click.echo(f"--- [{elapsed:.1f}s] ---")
            click.echo(content)
            click.echo(f"[cursor: {p.cursor_x},{p.cursor_y}]")
            last_hash = content_hash

            if until and until in content:
                click.echo(f"[found '{until}']", err=True)
                break

        time.sleep(interval)


# --- Input ---


@main.command("send")
@click.argument("session")
@click.argument("keys", nargs=-1)
@click.option("--pane", "-p", help="Pane ID or index")
@click.option("--literal", "-l", is_flag=True, help="Send keys literally (no parsing)")
@click.option("--enter", "-e", is_flag=True, help="Append Enter key")
def send_keys(session: str, keys: tuple[str, ...], pane: str | None, literal: bool, enter: bool):
    """Send keys to a pane.

    Keys can include special sequences like Enter, Escape, C-c, etc.
    """
    server = get_server()
    sess = find_session(server, session)
    p = find_pane(sess, pane)

    key_string = " ".join(keys)
    if enter:
        key_string += " Enter"

    p.send_keys(key_string, literal=literal, enter=False)
    click.echo(f"Sent: {key_string}")


@main.command("type")
@click.argument("session")
@click.argument("text")
@click.option("--pane", "-p", help="Pane ID or index")
@click.option("--enter", "-e", is_flag=True, help="Press Enter after typing")
@click.option("--delay", "-d", default=0, help="Delay between chars (ms)")
def type_text(session: str, text: str, pane: str | None, enter: bool, delay: int):
    """Type text into a pane (literal characters)."""
    import time

    server = get_server()
    sess = find_session(server, session)
    p = find_pane(sess, pane)

    if delay > 0:
        for char in text:
            p.send_keys(char, literal=True)
            time.sleep(delay / 1000)
    else:
        p.send_keys(text, literal=True)

    if enter:
        p.send_keys("Enter")

    click.echo(f"Typed: {text!r}" + (" + Enter" if enter else ""))


@main.command("mouse")
@click.argument("session")
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.option("--pane", "-p", help="Pane ID or index")
@click.option("--click", "click_type", default="left", type=click.Choice(["left", "right", "middle"]))
@click.option("--double", is_flag=True, help="Double click")
def mouse_click(session: str, x: int, y: int, pane: str | None, click_type: str, double: bool):
    """Send mouse click to pane at x,y coordinates."""
    server = get_server()
    sess = find_session(server, session)
    p = find_pane(sess, pane)

    # tmux mouse escape sequences
    # Button encoding: 0=left, 1=middle, 2=right, add 32 for position encoding
    button_map = {"left": 0, "middle": 1, "right": 2}
    button = button_map[click_type]

    # Send mouse down then up (basic click)
    # Format: ESC [ M Cb Cx Cy (where Cb = button+32, Cx/Cy = position+33)
    cb = chr(button + 32)
    cx = chr(x + 33)
    cy = chr(y + 33)

    # Mouse press
    p.send_keys(f"\x1b[M{cb}{cx}{cy}", literal=True)
    # Mouse release (button 3 = release)
    p.send_keys(f"\x1b[M{chr(3 + 32)}{cx}{cy}", literal=True)

    if double:
        import time
        time.sleep(0.05)
        p.send_keys(f"\x1b[M{cb}{cx}{cy}", literal=True)
        p.send_keys(f"\x1b[M{chr(3 + 32)}{cx}{cy}", literal=True)

    click.echo(f"Clicked {click_type} at ({x}, {y})" + (" x2" if double else ""))


# --- Session Control ---


@main.command("new")
@click.argument("name")
@click.option("--window", "-w", default="main", help="Initial window name")
@click.option("--cmd", "-c", help="Initial command to run")
@click.option("--width", default=120, help="Window width")
@click.option("--height", default=40, help="Window height")
def new_session(name: str, window: str, cmd: str | None, width: int, height: int):
    """Create a new tmux session."""
    server = get_server()

    # Check if exists
    existing = server.sessions.filter(session_name=name)
    if existing:
        click.echo(f"Session '{name}' already exists", err=True)
        sys.exit(1)

    sess = server.new_session(
        session_name=name,
        window_name=window,
        start_directory=str(Path.cwd()),
        x=width,
        y=height,
    )

    if cmd:
        pane = sess.active_window.active_pane
        if pane:
            pane.send_keys(cmd)

    click.echo(f"Created session '{name}'")


@main.command("kill")
@click.argument("session")
@click.option("--force", "-f", is_flag=True, help="Kill without confirmation")
def kill_session(session: str, force: bool):
    """Kill a tmux session."""
    server = get_server()
    sess = find_session(server, session)

    if not force:
        click.confirm(f"Kill session '{session}'?", abort=True)

    sess.kill()
    click.echo(f"Killed session '{session}'")


if __name__ == "__main__":
    main()
