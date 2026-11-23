# Social Research Reader — by The Ask Why Company

Read and compare public social content with clear evidence layers, source links, coverage limits, privacy safeguards, and no unauthorized access or unapproved spending.

Read the skill: [skills/social-research-reader/SKILL.md](skills/social-research-reader/SKILL.md)

Works with Claude (Claude Code, Claude.ai) and any tool that reads the open [Agent Skills](https://agentskills.io) `SKILL.md` format.

## Install in Claude

**Claude Code:**
```
/plugin marketplace add theaskwhy/social-research-reader
/plugin install social-research-reader@social-research-reader
```

Or from the full catalogue: `/plugin marketplace add theaskwhy/skills` then `/plugin install social-research-reader@theaskwhy`.

**Manual:** copy `skills/social-research-reader/` into `~/.claude/skills/` (personal) or `.claude/skills/` (project).

**Claude.ai:** zip the `skills/social-research-reader` folder and upload it under Settings → Capabilities → Skills.

## Use with other AI agents

This skill uses the open **Agent Skills** standard. The same `SKILL.md` works with compatible tools including OpenAI Codex, Cursor, Gemini CLI, GitHub Copilot, Windsurf, Antigravity, OpenCode, and Goose.

**Quick install:** the open-source `skills` installer detects supported tools:
```
npx skills add theaskwhy/social-research-reader
```

**Manual:** copy `skills/social-research-reader/` into your tool's skills folder:

| Tool | Personal (all projects) | One project |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| OpenAI Codex | `~/.codex/skills/` | `.agents/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| Gemini CLI / Antigravity | `~/.gemini/skills/` | `.gemini/skills/` |
| GitHub Copilot | `~/.copilot/skills/` | `.github/skills/` |
| Windsurf | — | `.windsurf/skills/` |
| Any spec-compliant agent | — | `.agents/skills/` |

For tools without skills support, paste `SKILL.md` into the tool's rules or instructions file.

## Licence

MIT. See [LICENSE](LICENSE).
