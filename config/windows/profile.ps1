# NEPTUNE v2. Dot-source from the existing PowerShell 7 profile.
# Prefer an existing matching portable runtime; do not download or replace it.
foreach ($runtime in @('codex','python-3.13.18')) {
    $bin = Join-Path $HOME ".local/share/neptune/runtimes/$runtime"
    if ((Test-Path -LiteralPath $bin -PathType Container) -and ($env:PATH -split ';') -notcontains $bin) { $env:PATH = $bin + ';' + $env:PATH }
}
if (-not $env:NEPTUNE_PROJECTS) { $env:NEPTUNE_PROJECTS = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Projects' }
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:HERDR_CONFIG_PATH = Join-Path $HOME '.config/herdr/config.toml'
function proj { Set-Location -LiteralPath $env:NEPTUNE_PROJECTS }
function neptune {
    if ($args.Count -eq 1 -and $args[0] -in @('--version','-V')) { Write-Output 'NEPTUNE v2'; return }
    if ($PWD.ProviderPath -eq $HOME) { Set-Location -LiteralPath $env:NEPTUNE_PROJECTS -ErrorAction Stop }
    if ($env:HERDR_ENV -eq '1') { return }
    $project = $PWD.ProviderPath
    $label = ((Split-Path $project -Leaf) -replace '[^a-zA-Z0-9_-]', '-').ToLowerInvariant()
    $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($project.ToLowerInvariant()))).Substring(0,8).ToLowerInvariant()
    $previousActive = $env:NEPTUNE_ACTIVE
    $previousPermission = $env:NEPTUNE_FULL_ACCESS
    try {
        $env:NEPTUNE_ACTIVE = '1'
        if (-not $env:NEPTUNE_FULL_ACCESS) { $env:NEPTUNE_FULL_ACCESS = '1' }
        & herdr --session "neptune-$label-$hash"
    } finally {
        if ($null -eq $previousActive) { Remove-Item Env:NEPTUNE_ACTIVE -ErrorAction SilentlyContinue }
        else { $env:NEPTUNE_ACTIVE = $previousActive }
        if ($null -eq $previousPermission) { Remove-Item Env:NEPTUNE_FULL_ACCESS -ErrorAction SilentlyContinue }
        else { $env:NEPTUNE_FULL_ACCESS = $previousPermission }
    }
}
function Set-NeptunePrelaunchName([string]$Agent) {
    if ($env:NEPTUNE_ACTIVE -eq '1' -and $env:HERDR_ENV -eq '1' -and $env:HERDR_PANE_ID) {
        & node -e "require(require('node:path').join(require('node:os').homedir(),'.local','share','neptune','hook-entry.cjs')).run('name','windows','$Agent')"
    }
}
function codex {
    Set-NeptunePrelaunchName codex
    $cli = Get-Command codex -CommandType Application -ErrorAction Stop | Select-Object -First 1
    if ($env:NEPTUNE_ACTIVE -eq '1' -and $env:HERDR_ENV -eq '1') {
        $previousPermission = $env:NEPTUNE_FULL_ACCESS
        try {
            if (-not $env:NEPTUNE_FULL_ACCESS) { $env:NEPTUNE_FULL_ACCESS = '1' }
            $launchArgs = @('--no-daemon')
            if ($env:NEPTUNE_FULL_ACCESS -eq '1') {
                if (-not ($args | Where-Object { $_ -match '^(--sandbox|-s)(=|$)|^--dangerously-bypass-approvals-and-sandbox$' })) { $launchArgs += @('--sandbox','danger-full-access') }
                if (-not ($args | Where-Object { $_ -match '^(--ask-for-approval|-a)(=|$)|^--dangerously-bypass-approvals-and-sandbox$' })) { $launchArgs += @('--ask-for-approval','never') }
            }
            & $cli.Source @launchArgs @args
        } finally {
            if ($null -eq $previousPermission) { Remove-Item Env:NEPTUNE_FULL_ACCESS -ErrorAction SilentlyContinue }
            else { $env:NEPTUNE_FULL_ACCESS = $previousPermission }
        }
    } else { & $cli.Source @args }
}
function claude {
    Set-NeptunePrelaunchName claude
    $cli = Get-Command claude -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $previousPermission = $env:NEPTUNE_FULL_ACCESS
    try {
        $launchArgs = @()
        if ($env:NEPTUNE_ACTIVE -eq '1' -and $env:HERDR_ENV -eq '1') {
            if (-not $env:NEPTUNE_FULL_ACCESS) { $env:NEPTUNE_FULL_ACCESS = '1' }
            if ($env:NEPTUNE_FULL_ACCESS -eq '1' -and -not ($args | Where-Object { $_ -match '^--permission-mode(=|$)|^--dangerously-skip-permissions$' })) { $launchArgs += @('--permission-mode','bypassPermissions') }
        }
        & $cli.Source @launchArgs @args
    } finally {
        if ($null -eq $previousPermission) { Remove-Item Env:NEPTUNE_FULL_ACCESS -ErrorAction SilentlyContinue }
        else { $env:NEPTUNE_FULL_ACCESS = $previousPermission }
    }
}
