#!/usr/bin/env bash
set -euo pipefail

echo "==> Uninstalling ctmux..."

# Remove the wrapper script
if [ -f "$HOME/bin/ctmux" ]; then
    rm "$HOME/bin/ctmux"
    echo "Removed ~/bin/ctmux"
fi

# Remove the skill symlink
if [ -L "$HOME/.claude/skills/tmux/SKILL.md" ]; then
    rm "$HOME/.claude/skills/tmux/SKILL.md"
    rmdir "$HOME/.claude/skills/tmux" 2>/dev/null || true
    echo "Removed ~/.claude/skills/tmux/"
fi

echo ""
echo "==> Uninstall complete!"
echo "Note: The project directory and venv were not removed."
