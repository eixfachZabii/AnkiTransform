# Claude Code status line (PowerShell port of statusline-command.sh)
# Reads the session JSON from stdin and prints a rich one-line status.
# Referenced from settings.json -> statusLine.command

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }
try { $j = $raw | ConvertFrom-Json } catch { exit 0 }

# --- ANSI color helpers (dark theme) ---
$e = [char]27
$RESET  = "$e[0m"
$BOLD   = "$e[1m"
$DIM    = "$e[2m"
$LABEL  = "$e[38;5;67m"    # muted blue-grey for labels
$VALUE  = "$e[38;5;80m"    # cyan for values
$WARN   = "$e[38;5;220m"   # yellow for warnings
$DANGER = "$e[38;5;203m"   # red for danger
$GOOD   = "$e[38;5;114m"   # green for good state
$PURPLE = "$e[38;5;141m"   # model name
$ORANGE = "$e[38;5;215m"   # effort
$SEP    = "$DIM|$RESET"

$parts = @()

# Model
$model = $j.model.display_name
if ($model) { $parts += "$PURPLE$BOLD$model$RESET" }

# Effort level
$effort = $j.effort.level
if ($effort) { $parts += "${LABEL}effort:$RESET$ORANGE$($effort.ToUpper())$RESET" }

# Thinking
if ($j.thinking.enabled -eq $true) { $parts += "${LABEL}thinking:${RESET}${GOOD}on$RESET" }

# Context usage
$used = $j.context_window.used_percentage
if ($null -ne $used) {
    $u = [math]::Round($used)
    $c = if ($u -ge 80) { $DANGER } elseif ($u -ge 60) { $WARN } else { $GOOD }
    $parts += "${LABEL}ctx:$RESET$c$u%$RESET"
}

# Rate limits
$rate = ''
$fh = $j.rate_limits.five_hour.used_percentage
if ($null -ne $fh) {
    $v = [math]::Round($fh)
    $c = if ($v -ge 80) { $DANGER } elseif ($v -ge 50) { $WARN } else { $VALUE }
    $rate = "${c}5h:$v%$RESET"
}
$sd = $j.rate_limits.seven_day.used_percentage
if ($null -ne $sd) {
    $v = [math]::Round($sd)
    $c = if ($v -ge 80) { $DANGER } elseif ($v -ge 50) { $WARN } else { $VALUE }
    $seg = "${c}7d:$v%$RESET"
    $rate = if ($rate) { "$rate $seg" } else { $seg }
}
if ($rate) { $parts += "${LABEL}limits:$RESET$rate" }

# Repo
$repo = if ($j.workspace.repo) { "$($j.workspace.repo.owner)/$($j.workspace.repo.name)" } else { $null }
if ($repo) { $parts += "${LABEL}repo:$RESET$VALUE$repo$RESET" }

# Worktree
$wt = $j.workspace.git_worktree
if ($wt) { $parts += "${LABEL}wt:$RESET$VALUE$wt$RESET" }

# PR
$pr = $j.pr.number
if ($pr) {
    $lbl = "PR #$pr"
    if ($j.pr.review_state) { $lbl = "$lbl ($($j.pr.review_state))" }
    $parts += "$LABEL$lbl$RESET"
}

# Output style (only show if non-default)
$os = $j.output_style.name
if ($os -and $os -ne 'default' -and $os -ne 'Default') {
    $parts += "${LABEL}style:$RESET$VALUE$os$RESET"
}

if ($parts.Count -eq 0) { exit 0 }

$parts -join " $SEP "
