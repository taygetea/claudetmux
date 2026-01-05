#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing ctmux from $SCRIPT_DIR"

# Check for required tools
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is required but not installed"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create venv and install package with entry points
echo "==> Setting up Python environment..."
uv venv --quiet
uv pip install -e . --reinstall --quiet

# Create ~/bin if it doesn't exist
mkdir -p "$HOME/bin"

# Create wrapper script that uses the venv
echo "==> Installing ctmux to ~/bin..."
rm -f "$HOME/bin/ctmux"  # Remove any existing file/symlink
cat > "$HOME/bin/ctmux" << EOF
#!/usr/bin/env bash
exec "$SCRIPT_DIR/.venv/bin/ctmux" "\$@"
EOF
chmod +x "$HOME/bin/ctmux"

# Install the skill for Claude Code
echo "==> Installing Claude Code skill..."
mkdir -p "$HOME/.claude/skills/tmux"
ln -sf "$SCRIPT_DIR/.claude/skills/tmux/SKILL.md" "$HOME/.claude/skills/tmux/SKILL.md"

echo ""
echo "==> Installation complete!"
echo ""
echo "Make sure ~/bin is in your PATH. Add this to your ~/.bashrc if needed:"
echo '  export PATH="$HOME/bin:$PATH"'
echo ""
echo "Test with: ctmux --help"
