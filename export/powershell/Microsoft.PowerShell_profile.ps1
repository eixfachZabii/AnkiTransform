# ─────────────────────────────────────────────────────────────────────────
#  PowerShell profile  —  ported from macOS / zsh setup
#  Main feature: shows the current git branch in the prompt (like oh-my-zsh).
#
#  Install: copy this file to the path printed by  $PROFILE  in PowerShell,
#  then run  . $PROFILE  (or open a new window). See INSTALL-WINDOWS.md.
# ─────────────────────────────────────────────────────────────────────────

# Optional: GitHub PAT used by `gh` and the GitHub MCP. Prefer setting this as a
# real Windows environment variable instead of hard-coding a secret here:
#   setx GITHUB_PERSONAL_ACCESS_TOKEN "ghp_xxx"
# (then restart the terminal). Uncomment the next line only if you must:
# $env:GITHUB_PERSONAL_ACCESS_TOKEN = '<PUT-YOUR-GITHUB-PAT-HERE>'

# Better defaults
$PSDefaultParameterValues['Out-Default:OutVariable'] = $null
Set-PSReadLineOption -PredictionSource History -ErrorAction SilentlyContinue
Set-PSReadLineOption -HistorySearchCursorMovesToEnd -ErrorAction SilentlyContinue

# Cache whether git exists so we don't probe PATH on every prompt
$script:HasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)

function prompt {
    $e     = [char]27
    $reset = "$e[0m"

    # Current directory, with ~ for the home folder
    $path = $PWD.Path
    if ($HOME -and $path.StartsWith($HOME)) {
        $path = '~' + $path.Substring($HOME.Length)
    }

    # Git segment: "on <branch> ✓/✗"
    $git = ''
    if ($script:HasGit -and (git rev-parse --is-inside-work-tree 2>$null) -eq 'true') {
        $branch = (git symbolic-ref --short HEAD 2>$null)
        if (-not $branch) { $branch = (git describe --tags --exact-match 2>$null) }
        if (-not $branch) { $branch = "$(git rev-parse --short HEAD 2>$null)" }

        if (git status --porcelain 2>$null) {
            $mark = "$e[31m ✗$reset"     # red  ✗  = uncommitted changes
        } else {
            $mark = "$e[32m ✓$reset"     # green ✓ = clean working tree
        }
        $git = " $e[90mon$reset $e[35m$branch$reset$mark"
    }

    # cyan path · git segment · newline · yellow ❯
    "$e[36m$path$reset$git`n$e[33m❯$reset "
}

# ── Handy aliases ported from a typical zsh setup ───────────────────────────
function gs  { git status @args }
function gl  { git log --oneline --graph --decorate @args }
function gd  { git diff @args }
function gco { git checkout @args }
function gp  { git pull @args }
function la  { Get-ChildItem -Force @args }
function ..  { Set-Location .. }
function ... { Set-Location ../.. }

# ── Want a fancier prompt later? ────────────────────────────────────────────
# Option A — posh-git (adds branch + ahead/behind counts to the prompt):
#   Install-Module posh-git -Scope CurrentUser ; then add:  Import-Module posh-git
# Option B — oh-my-posh (themeable powerline prompt, needs a Nerd Font):
#   winget install JanDeDobbeleer.OhMyPosh
#   oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\jandedobbeleer.omp.json" | Invoke-Expression
# If you enable either, delete the custom `prompt` function above.
