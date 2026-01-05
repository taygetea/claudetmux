# Claude Code Extension Mechanisms (December 2025)

Research on the current idiomatic ways to extend and interface with Claude Code.

## Extension Mechanisms Overview

There are **six primary ways** to extend Claude Code:

| Mechanism | Invocation | Best For |
|-----------|-----------|----------|
| **MCP Servers** | Automatic (tools available) | External APIs, databases, services |
| **Skills** | Automatic (model discovers) | Complex workflows, team standards |
| **Custom Commands** | Manual (`/command`) | Quick prompts, manual triggers |
| **Hooks** | Automatic (event-driven) | Formatting, logging, validation |
| **Subagents** | Automatic + explicit | Task-specific expertise |
| **Plugins** | Distribution wrapper | Sharing bundles with teams |

---

## 1. MCP Servers (Model Context Protocol)

**What**: External tool integrations using the open-source MCP standard.

**Installation methods**:
1. Remote HTTP servers (recommended for cloud)
2. SSE servers (deprecated but supported)
3. Local stdio servers (for direct system access)

```bash
# Add an MCP server
claude mcp add --transport http my-server https://example.com/mcp

# Scopes: local (current project), project (team via .mcp.json), user (personal)
claude mcp add -s project my-server https://example.com/mcp
```

**Popular servers**: Sentry, GitHub, PostgreSQL, Playwright, Notion, Gmail

**MCP Registry**: 450+ servers at https://github.com/modelcontextprotocol/servers

**Best for**: Databases, external APIs, browser automation, monitoring tools.

---

## 2. Agent Skills (Model-Invoked)

**What**: Reusable capability modules Claude automatically discovers and uses.

**Locations**:
- Personal: `~/.claude/skills/my-skill/SKILL.md`
- Project: `.claude/skills/my-skill/SKILL.md`

**Format**: YAML-frontmatter Markdown files

```markdown
---
description: "Generate database migrations from schema changes"
allowed-tools:
  - Read
  - Edit
  - Bash
---

# Database Migration Skill

When asked to create migrations, follow these steps:
1. Read the current schema from `db/schema.sql`
2. Compare with requested changes
3. Generate migration file in `db/migrations/`
```

**Discovery**: Claude reads the `description` field to decide when to use it.

**Best for**: Complex workflows with multiple files, team-standardized procedures.

---

## 3. Custom Slash Commands (User-Invoked)

**What**: User-triggered commands stored as Markdown files.

**Locations**:
- Personal: `~/.claude/commands/my-command.md`
- Project: `.claude/commands/my-command.md`

**Format**:
```markdown
---
description: "Run tests with coverage"
allowed-tools:
  - Bash
  - Read
argument-hint: "[test-path]"
---

Run tests for $ARGUMENTS with coverage enabled.
If no path provided, run all tests.
```

**Features**:
- Arguments: `$ARGUMENTS` (all), `$1`, `$2` (individual)
- Bash execution: `!git status` prefix
- File references: `@src/main.py` prefix

**Best for**: Quick, frequently used prompts you trigger manually.

---

## 4. Hooks (Event Handlers)

**What**: Shell commands that run at specific lifecycle points.

**Events**:
- `PreToolUse` - Before tool calls (can block)
- `PostToolUse` - After tool calls
- `UserPromptSubmit` - Before processing user input
- `PermissionRequest` - When permission dialog shown
- `SessionStart` / `SessionEnd` - Session lifecycle

**Configuration** (`.claude/settings.json`):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": { "tool_name": "Edit" },
        "command": "prettier --write $CLAUDE_FILE_PATH"
      }
    ]
  }
}
```

**Best for**: Auto-formatting, compliance logging, file protection, notifications.

---

## 5. Subagents (Specialized AI Assistants)

**What**: Pre-configured AI agents with separate context windows.

**Locations**:
- Project: `.claude/agents/my-agent.md`
- User: `~/.claude/agents/my-agent.md`

**Format**:
```markdown
---
name: security-auditor
description: "Performs security audits on code changes"
tools:
  - Read
  - Grep
  - Glob
model: opus
---

You are a security expert. When analyzing code:
1. Check for OWASP Top 10 vulnerabilities
2. Review authentication/authorization logic
3. Identify potential injection points
```

**Built-in agents**: Plan, Explore, general-purpose

**Best for**: Complex multi-step tasks requiring specialized expertise.

---

## 6. Plugins (Distributable Collections)

**What**: Packaged bundles combining commands, agents, skills, hooks, and MCP servers.

**Structure**:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest
├── commands/                 # Slash commands
├── agents/                   # Subagents
├── skills/                   # Skills
├── hooks.json               # Hook definitions
├── .mcp.json                # MCP configurations
└── .lsp.json                # Language servers
```

**Best for**: Sharing reusable extensions with teams/community.

---

## Claude Agent SDK (Programmatic Interface)

For building autonomous agents programmatically (CI/CD, production apps):

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"])
    ):
        print(message)
```

**Features**:
- Same tools as Claude Code (Read, Write, Edit, Bash, Grep, etc.)
- Hooks via callback functions
- Subagent spawning
- MCP server connections
- Session management (resume later)

**Best for**: CI/CD pipelines, production automation, custom applications.

---

## Decision Matrix: Which Mechanism to Use?

| Need | Use |
|------|-----|
| External API/database integration | MCP Server |
| Claude should auto-discover capability | Skill |
| I want to trigger manually | Custom Command |
| Automatic on every edit/save | Hook |
| Specialized subtask with separate context | Subagent |
| Share with team/community | Plugin |
| Production/CI integration | Agent SDK |

---

## For TUI/tmux Integration: Recommendations

Based on this research, for building tmux interaction capabilities:

### Option A: MCP Server (Recommended for complex integrations)
- Claude would have tmux tools available automatically
- Could list sessions, read panes, send keys
- Follows the standard protocol
- BUT: More setup overhead, runs as separate process

### Option B: Custom Command + Bash (Simpler)
- Create `/tmux` command that runs libtmux scripts
- Claude already has Bash tool access
- Less ceremony, direct integration
- BUT: Less discoverable, manual invocation

### Option C: Skill with Bash Tools (Hybrid)
- Skill describes how to use tmux via Bash
- Claude auto-discovers when relevant
- Can include libtmux wrapper scripts
- Good balance of discoverability and simplicity

### Option D: Hook for TUI Monitoring
- PostToolUse hook to capture TUI state
- Automatic screenshots/state dumps after commands
- Passive observation rather than active control

**Recommendation**: Start with **Option C (Skill + Bash)** for simplicity, graduate to **MCP Server** if you need richer tool semantics or sharing.

---

## References

- Claude Code docs: https://code.claude.com/docs/
- MCP specification: https://modelcontextprotocol.io/
- Agent SDK: https://platform.claude.com/docs/en/agent-sdk/
- MCP Registry: https://github.com/modelcontextprotocol/servers
