# Config export — macOS ➜ Windows / PowerShell

Exported on 2026-06-22. Contains your Claude Code chat config, VS Code settings,
and terminal appearance, all converted to work on Windows with PowerShell.

## ⚠️ SECURITY — read first

Your original `~/.claude/settings.json` on the Mac stores a **GitHub Personal
Access Token in plaintext**. That token was **deliberately NOT copied** into this
export — it's replaced with the placeholder `<PUT-YOUR-GITHUB-PAT-HERE>`.

Recommended:
- **Rotate** that token (GitHub → Settings → Developer settings → Tokens) since it
  has been sitting unencrypted in a config file.
- On Windows, set it as an environment variable rather than in the file:
  `setx GITHUB_PERSONAL_ACCESS_TOKEN "your_new_token"`.

## What's in here

```
export/
├─ README.md                     ← you are here
├─ INSTALL-WINDOWS.md            ← step-by-step install instructions
├─ claude/                       ← Claude Code "chat" config  → %USERPROFILE%\.claude\
│  ├─ settings.json              (token redacted; hooks → Windows; statusline → PowerShell)
│  ├─ settings.local.json
│  ├─ keybindings.json
│  ├─ CLAUDE.md
│  ├─ .mcp.json                  (npx/uvx paths de-macOS-ified)
│  └─ statusline-command.ps1     (PowerShell port of your bash statusline)
├─ vscode/                       → %APPDATA%\Code\User\
│  ├─ settings.json              (mac font/python paths fixed; beige terminal kept)
│  └─ keybindings.json
├─ windows-terminal/
│  └─ settings.fragment.json     (your beige Terminal.app look as a WT color scheme)
└─ powershell/
   └─ Microsoft.PowerShell_profile.ps1   (git-branch prompt + aliases)
```

## The two things you specifically asked for

1. **Convert configs for Windows/PowerShell** — done. macOS-only bits were
   translated: `osascript` notification → Windows sound, bash statusline →
   `statusline-command.ps1`, absolute `/usr/local/bin` & `/opt/homebrew` paths →
   PATH-resolved commands, Terminal.app beige profile → Windows Terminal scheme.

2. **Show the git branch in the PowerShell prompt** — `powershell/Microsoft.PowerShell_profile.ps1`
   gives you an oh-my-zsh-style prompt:
   ```
   ~\code\myrepo on main ✓
   ❯
   ```
   branch after `on`, green ✓ when clean / red ✗ when you have changes. No extra
   modules required.

See **INSTALL-WINDOWS.md** for exactly where each file goes.
