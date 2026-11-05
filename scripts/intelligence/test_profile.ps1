$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'config/windows/profile.ps1'), [ref]$null, [ref]$parseErrors) | Out-Null
if ($parseErrors.Count) { throw ($parseErrors | Out-String) }
$temp = Join-Path ([IO.Path]::GetTempPath()) ('neptune-profile-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
$fixture = Join-Path $temp 'cli.ps1'
@'
@{argv=@($args); permission=$env:NEPTUNE_FULL_ACCESS} | ConvertTo-Json -Compress -Depth 4
'@ | Set-Content -LiteralPath $fixture
try {
    . (Join-Path $root 'config/windows/profile.ps1')
    # All external calls are intercepted; fixture pane IDs never reach Herdr.
    function Get-Command { param($Name, $CommandType, $ErrorAction) [pscustomobject]@{Source=$fixture} }
    function node { }
    function Assert-Equal($Actual, $Expected) {
        if (($Actual | ConvertTo-Json -Compress) -ne ($Expected | ConvertTo-Json -Compress)) {
            throw "Expected $($Expected | ConvertTo-Json -Compress); got $($Actual | ConvertTo-Json -Compress)"
        }
    }
    Assert-Equal (neptune --version) 'NEPTUNE v2'
    $env:NEPTUNE_ACTIVE='0'; $env:HERDR_ENV='0'
    Assert-Equal ((codex resume --last | ConvertFrom-Json).argv) @('resume','--last')
    Assert-Equal ((claude --continue | ConvertFrom-Json).argv) @('--continue')
    $env:NEPTUNE_ACTIVE='1'; $env:HERDR_ENV='1'; $env:HERDR_PANE_ID='fixture-only'
    Remove-Item Env:NEPTUNE_FULL_ACCESS -ErrorAction SilentlyContinue
    $result = codex resume --last | ConvertFrom-Json
    Assert-Equal $result.argv @('--no-daemon','--sandbox','danger-full-access','--ask-for-approval','never','resume','--last')
    Assert-Equal $result.permission '1'
    if (Test-Path Env:NEPTUNE_FULL_ACCESS) { throw 'Permission environment leaked out of launch' }
    Assert-Equal ((claude --continue | ConvertFrom-Json).argv) @('--permission-mode','bypassPermissions','--continue')
    Assert-Equal ((codex --sandbox workspace-write --ask-for-approval on-request | ConvertFrom-Json).argv) @('--no-daemon','--sandbox','workspace-write','--ask-for-approval','on-request')
    Assert-Equal ((claude --permission-mode manual | ConvertFrom-Json).argv) @('--permission-mode','manual')
    $env:NEPTUNE_FULL_ACCESS='0'
    Assert-Equal ((codex --help | ConvertFrom-Json).argv) @('--no-daemon','--help')
    Assert-Equal ((claude --help | ConvertFrom-Json).argv) @('--help')
    Assert-Equal $env:NEPTUNE_FULL_ACCESS '0'
    Write-Output 'PASS: PowerShell parse, scoped full-access defaults, explicit overrides, environment restoration, native resume arguments.'
} finally {
    # Delete only the known fixture file and empty directory; no recursive cleanup.
    Remove-Item -LiteralPath $fixture -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $temp -ErrorAction SilentlyContinue
}
