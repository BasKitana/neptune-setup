# Mouse movement types into PowerShell in WezTerm

On native Windows, WezTerm 20240203-110809-5046fc22 can corrupt mouse reports in its bundled ConPTY runtime. Moving the pointer then inserts coordinates or garbage into a Herdr shell pane. Updating the matched Microsoft `conpty.dll` and `OpenConsole.exe` pair resolved this on the tested Neptune host.

Keep `mouse_capture = true` under `[ui]` in Herdr's configuration. Use the normal Herdr mouse handler and WezTerm's default Win32 input encoding. Remove experimental mouse filters, `HERDR_WINDOWS_INPUT_PROBE` overrides, and automatic resize workarounds introduced while diagnosing this issue.

## Install the verified runtime beside a copy of WezTerm

Run these commands in PowerShell 7. Set `$weztermSource` to the existing installation directory if its location differs. The destination is a new per-user installation. An existing destination stops the copy so an active installation cannot be overwritten.

```powershell
$ErrorActionPreference = 'Stop'
$weztermSource = Join-Path $env:ProgramFiles 'WezTerm'
$destination = Join-Path $env:LOCALAPPDATA 'Programs/Neptune-WezTerm-ConPTY-1.24.260710001'
$download = Join-Path $env:TEMP ('neptune-conpty-' + [guid]::NewGuid())
$archive = Join-Path $download 'conpty.zip'
$unpacked = Join-Path $download 'package'

if (-not (Test-Path (Join-Path $weztermSource 'wezterm-gui.exe'))) {
    throw 'Set $weztermSource to the installed WezTerm directory.'
}
if (Test-Path $destination) {
    throw "Destination already exists: $destination"
}
New-Item -ItemType Directory -Path $download | Out-Null
Invoke-WebRequest -Uri 'https://github.com/microsoft/terminal/releases/download/v1.24.11911.0/Microsoft.Windows.Console.ConPTY.1.24.260710001.nupkg' -OutFile $archive
if ((Get-FileHash $archive -Algorithm SHA256).Hash -ine '9382ad7becb7e4d84e300578d8e4f4df28f43d979d9055d978c42913c47e0e9d') {
    throw 'ConPTY package hash mismatch.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $unpacked
$files = @(
    @{ Source = 'runtimes/win-x64/native/conpty.dll'; Name = 'conpty.dll'; Hash = '39fba2713e2495117b1591ae8c32a3b904bea7aa66069cf7815e2844c76d75d8' },
    @{ Source = 'build/native/runtimes/x64/OpenConsole.exe'; Name = 'OpenConsole.exe'; Hash = 'b7fd936c2668b87b9ecf7b3366dc6568afc1c6f981874cba3e955a1c35cf8160' }
)
foreach ($file in $files) {
    $path = Join-Path $unpacked $file.Source
    $signature = Get-AuthenticodeSignature -LiteralPath $path
    if ((Get-FileHash $path -Algorithm SHA256).Hash -ine $file.Hash -or
        $signature.Status -ne 'Valid' -or
        $signature.SignerCertificate.Subject -notlike '*Microsoft Corporation*') {
        throw "ConPTY verification failed: $path"
    }
}
New-Item -ItemType Directory -Path $destination | Out-Null
Copy-Item -Path (Join-Path $weztermSource '*') -Destination $destination -Recurse
foreach ($file in $files) {
    $installed = Join-Path $destination $file.Name
    Copy-Item -LiteralPath (Join-Path $unpacked $file.Source) -Destination $installed -Force
    if ((Get-FileHash $installed -Algorithm SHA256).Hash -ine $file.Hash) {
        throw "Installed file verification failed: $installed"
    }
}
& (Join-Path $destination 'wezterm.exe') --version
if ($LASTEXITCODE -ne 0) { throw 'WezTerm executable check failed.' }
Write-Output (Join-Path $destination 'wezterm-gui.exe')
```

Keep the downloaded package for its license, notices, and recovery reference. If a copy fails partway, inspect the destination before retrying with a fresh destination directory.

## Point Neptune's WezTerm shortcuts at the repaired copy

Update the user's Start menu and pinned taskbar shortcuts to the printed `wezterm-gui.exe` path. Set shortcut arguments to `start --always-new-process` so a launch uses the repaired installation. Back up existing shortcuts first. The current `~/.wezterm.lua` still controls Neptune's PowerShell launch, appearance, and mouse bindings.

Close and reopen WezTerm through the updated shortcut to load the replacement runtime. Existing windows retain their loaded runtime. Preserve active work and Herdr sessions while switching clients.

Verify that moving the pointer across a plain PowerShell pane leaves the prompt clean, clicking the tab-bar plus creates a tab, and scrolling and dragging work. Shift + left-drag uses WezTerm's text selection when Herdr captures the mouse.

## Verification on the repaired Windows host

An isolated console-input test reproduced corruption with the original WezTerm ConPTY pair in three runs. The replacement pair preserved the input in all three runs. A real Herdr session using the replacement accepted 380 movement reports plus click, drag, and wheel reports with a clean PowerShell prompt. Clicking the tab-bar plus created a second terminal. The same Herdr test with the old pair inserted mouse-report fragments into the prompt. The user then confirmed that the repaired WezTerm installation worked.

Related upstream reports describe mouse input corruption in Herdr on Windows and replacement of WezTerm's bundled ConPTY pair. [Herdr issue #4907](https://github.com/herdrdev/herdr/issues/4907), [WezTerm issue #7774](https://github.com/wezterm/wezterm/issues/7774).
