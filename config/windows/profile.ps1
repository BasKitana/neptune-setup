# Merge by dot-sourcing this file from the existing PowerShell 7 profile.
if (-not $env:NEPTUNE_PROJECTS) { $env:NEPTUNE_PROJECTS = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Projects' }
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:HERDR_CONFIG_PATH = Join-Path $HOME '.config/herdr/config.toml'
function proj { Set-Location -LiteralPath $env:NEPTUNE_PROJECTS }
function neptune {
    Set-Location -LiteralPath $env:NEPTUNE_PROJECTS -ErrorAction Stop
    if ($env:HERDR_ENV -eq '1') { return }
    $project = $PWD.ProviderPath
    $label = ((Split-Path $project -Leaf) -replace '[^a-zA-Z0-9_-]', '-').ToLowerInvariant()
    $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($project.ToLowerInvariant()))).Substring(0,8).ToLowerInvariant()
    $previousActive = $env:NEPTUNE_ACTIVE
    try {
        $env:NEPTUNE_ACTIVE = '1'
        & herdr --session "neptune-$label-$hash"
    } finally {
        if ($null -eq $previousActive) { Remove-Item Env:NEPTUNE_ACTIVE -ErrorAction SilentlyContinue }
        else { $env:NEPTUNE_ACTIVE = $previousActive }
    }
}
function Set-NeptunePrelaunchName {
    if ($env:NEPTUNE_ACTIVE -eq '1' -and $env:HERDR_ENV -eq '1' -and $env:HERDR_PANE_ID) { python "$HOME/.local/share/neptune/herdr_agents.py" hook }
}
function codex {
    Set-NeptunePrelaunchName
    $cli = Get-Command codex -CommandType Application -ErrorAction Stop | Select-Object -First 1
    if ($env:NEPTUNE_ACTIVE -eq '1' -and $env:HERDR_ENV -eq '1') {
        & $cli.Source --no-daemon -c features.multi_agent=false @args
    } else { & $cli.Source @args }
}
function claude {
    Set-NeptunePrelaunchName
    $cli = Get-Command claude -CommandType Application -ErrorAction Stop | Select-Object -First 1
    & $cli.Source @args
}
# The setup AI may add project-title prompt integration, preserving the existing prompt.
