$ErrorActionPreference='Stop'
# Interactive windows must not inherit the automation host's plain-text mode.
Remove-Item Env:NO_COLOR -ErrorAction SilentlyContinue
$env:TERM='xterm-256color'
$env:COLORTERM='truecolor'
# Reuse the current user's existing Conductor credential without writing cleartext.
if (-not $env:NOVA_DESKTOP_API_KEY) {
    $provider=Join-Path $env:LOCALAPPDATA 'NovaConductor\provider.json'
    if (Test-Path -LiteralPath $provider) {
        $config=Get-Content -LiteralPath $provider -Raw | ConvertFrom-Json
        if ($config.kind -eq 'nova' -and $config.keyEnv -match '^[A-Za-z_][A-Za-z0-9_]*$') {
            $file=Join-Path $env:LOCALAPPDATA ('NovaConductor\credentials\'+$config.keyEnv+'.dpapi')
            if (Test-Path -LiteralPath $file) {
                Add-Type -AssemblyName System.Security
                $cipher=[Convert]::FromBase64String([IO.File]::ReadAllText($file))
                $clear=[Security.Cryptography.ProtectedData]::Unprotect($cipher,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
                $env:NOVA_DESKTOP_API_KEY=[Text.Encoding]::UTF8.GetString($clear)
                [Array]::Clear($clear,0,$clear.Length)
            }
        }
    }
}
# The visible launcher is explicitly requested; its helper processes stay hidden.
Start-Process -FilePath (Join-Path $PSScriptRoot 'gui\NOVA.Codex.Launcher.exe') -WorkingDirectory $PSScriptRoot
