param(
    [string]$Workspace = (Get-Location).Path,
    [ValidateSet('https://nova.inversolabs.us','http://192.168.86.51:8787','http://127.0.0.1:8788')][string]$BaseUrl='http://127.0.0.1:8788',
    [ValidateSet('read-only','workspace-write')][string]$Sandbox = 'workspace-write',
    [ValidateSet(4096,8192,16384,32768)][int]$ContextTokens = 8192,
    [string]$PromptFile,
    [string]$TestCommand = '',
    [string]$Out
)
$ErrorActionPreference='Stop'
$python=$env:NOVA_GEMMA_PYTHON
if (-not $python) {
    $candidate=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $candidate) { $python=$candidate }
    else { throw 'Set NOVA_GEMMA_PYTHON to a Python 3.11 or newer executable.' }
}
$mutex=[Threading.Mutex]::new($false,'Local\NOVA.Codex.Remote.Session')
$owns=$false
try {
    try { $owns=$mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $owns=$true }
    if (-not $owns) { throw 'A NOVA Codex session is already running. Close it first.' }
    $arguments=@((Join-Path $PSScriptRoot 'gemma-agent\launch_local.py'),'--workspace',$Workspace,'--base-url',$BaseUrl,'--context',"$ContextTokens",'--sandbox',$Sandbox)
    if ($TestCommand) { $arguments+=@('--test-command',$TestCommand) }
    if ($PromptFile) { $arguments+=@('--prompt-file',$PromptFile) }
    if ($Out) { $arguments+=@('--out',$Out) }
    & $python @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Gemma session failed. See the session logs printed above.' }
} finally {
    if ($owns) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
