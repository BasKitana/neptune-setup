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
    & herdr --session "neptune-$label-$hash"
}
function Set-NeptunePrelaunchName {
    if ($env:HERDR_ENV -eq '1' -and $env:HERDR_PANE_ID) { python "$HOME/.local/share/neptune/herdr_agents.py" hook }
}
function codex {
    Set-NeptunePrelaunchName
    $cli = Get-Command codex -CommandType Application -ErrorAction Stop | Select-Object -First 1
    if ($args.Count -eq 0 -and -not $env:NEPTUNE_SUPERVISOR_PANE) {
        & $cli.Source resume --last
    } else {
        & $cli.Source @args
    }
}
function claude {
    Set-NeptunePrelaunchName
    $cli = Get-Command claude -CommandType Application -ErrorAction Stop | Select-Object -First 1
    & $cli.Source @args
}
# The setup AI may add project-title prompt integration, preserving the existing prompt.
