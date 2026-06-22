# Install on Windows (PowerShell)

Everything here was exported from a macOS setup and converted for Windows.
Paths use `%USERPROFILE%` (cmd) / `$HOME` / `$env:USERPROFILE` (PowerShell),
which is your `C:\Users\<you>` folder.

> Run all PowerShell commands in a normal (non-admin) **PowerShell** window
> unless noted. `pwsh` = PowerShell 7, `powershell` = built-in Windows PowerShell 5.1.

---

## 0. Prerequisites

```powershell
# Git (gives you git + Git Bash, which Claude Code's Bash tool uses on Windows)
winget install Git.Git

# PowerShell 7 (recommended; the statusline uses `pwsh`)
winget install Microsoft.PowerShell

# Node (npx) and uv (uvx) for the MCP servers
winget install OpenJS.NodeJS
winget install astral-sh.uv
```

---

## 1. Claude Code config  →  `%USERPROFILE%\.claude\`

```powershell
$dst = "$env:USERPROFILE\.claude"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item .\claude\settings.json        $dst -Force
Copy-Item .\claude\settings.local.json  $dst -Force
Copy-Item .\claude\keybindings.json     $dst -Force
Copy-Item .\claude\CLAUDE.md            $dst -Force
Copy-Item .\claude\.mcp.json            $dst -Force
Copy-Item .\claude\statusline-command.ps1 $dst -Force
```

Then edit `%USERPROFILE%\.claude\settings.json`:

1. **GitHub token** — replace `<PUT-YOUR-GITHUB-PAT-HERE>` with your PAT, OR
   delete the whole `"env"` block and set the token as a Windows env var instead
   (`setx GITHUB_PERSONAL_ACCESS_TOKEN "ghp_xxx"`). **The original token was NOT
   exported for security — see SECURITY note in README.md.**
2. **statusLine path** — change `C:\Users\YOURNAME\.claude\statusline-command.ps1`
   to your actual username.

What changed vs. macOS:
- `Stop` hook: the macOS `osascript` desktop notification → a Windows system
  sound (`SystemSounds::Asterisk`).
- The `PreToolUse` "tool-banner" bash hook was **removed** (it's a bash script).
  To re-enable it you'd need Git Bash and a ported script.
- `.mcp.json`: absolute macOS binary paths → plain `npx` / `uvx` (resolved from
  PATH). If Claude can't find them, use `npx.cmd` / `uvx.exe` or full paths.

---

## 2. VS Code settings  →  `%APPDATA%\Code\User\`

```powershell
$dst = "$env:APPDATA\Code\User"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item .\vscode\settings.json    $dst -Force
Copy-Item .\vscode\keybindings.json $dst -Force
```

Then edit `settings.json`:
- `python.defaultInterpreterPath` is set to `"python"` (was `/opt/homebrew/bin/python3`).
  Point it at your Windows Python if you want a specific one.
- The beige terminal palette and JetBrains Mono font carry over unchanged
  (Windows fallbacks Consolas / Cascadia Mono are included).

---

## 3. Windows Terminal (the beige look)  →  merge a fragment

`windows-terminal\settings.fragment.json` is a **fragment**, not a full file.
Open Windows Terminal → `Ctrl+,` → **Open JSON file**, then:

1. Copy the object inside `"schemes": [ ... ]` into your existing top-level
   `"schemes"` array.
2. Merge the `"profiles": { "defaults": { ... } }` block into your existing
   `profiles.defaults` (this applies the beige scheme + Cascadia Mono to all profiles).
3. Optionally set `"initialCols": 120` and `"initialRows": 30` at the top level
   (matches your macOS 120×30 window).

Save — Windows Terminal applies it live. Set PowerShell as your default profile
in Settings → Startup.

---

## 4. PowerShell prompt with git branch  →  your `$PROFILE`

```powershell
# See where your profile lives:
$PROFILE
# Create the folder + copy the profile in:
New-Item -ItemType File -Force -Path $PROFILE | Out-Null
Copy-Item .\powershell\Microsoft.PowerShell_profile.ps1 $PROFILE -Force
# Allow local scripts to run (one-time), then reload:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
. $PROFILE
```

`cd` into any git repo and the prompt becomes:

```
~\code\myrepo on main ✓
❯
```

- **branch name** shows after `on` (magenta)
- **✓ green** = clean working tree, **✗ red** = uncommitted changes
- Works with no extra modules. To upgrade to posh-git / oh-my-posh, see the
  comments at the bottom of the profile.

> Do step 4 for **both** `pwsh` and `powershell` if you use both — each has its
> own `$PROFILE` path.
