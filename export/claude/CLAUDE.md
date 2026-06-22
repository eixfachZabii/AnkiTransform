# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, invoke the Skill tool with `skill: "graphify"` before doing anything else.

# Playwright MCP screenshots
When taking screenshots with the Playwright MCP (`mcp__playwright__browser_take_screenshot`), always save them to `.playwright/screenshots/<name>.png` relative to the project root. Never save screenshots directly to the repo root — this leaves PNG files in the working tree and pollutes `git status`.

Example: `filename: ".playwright/screenshots/fix1-sidebar-collapsed.png"`

# "We are done" → push workflow
When the user says "we are done", "push", "we're done", or any equivalent signal that a session is complete, ALWAYS do the following before committing and pushing:

1. **Update docs** — update any architecture docs (`docs/*/ARCHITECTURE.md`) that describe APIs, services, or components that changed this session
2. **Check finished boxes** — find all relevant ROADMAP files and mark completed items `[x]` (change `[ ]` to `[x]` and update section status from `🔲` to `✅ COMPLETE`)
3. **Update CLAUDE.md** — if new API endpoints, service methods, or architectural decisions were made, update the project `CLAUDE.md` to reflect them
4. **Then commit and push** — only after steps 1–3 are complete
