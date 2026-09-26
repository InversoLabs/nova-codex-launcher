$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv-training\Scripts\python.exe')) { & py -3.12 -m venv .venv-training; if($LASTEXITCODE){throw 'venv failed'} }
$python=Join-Path (Get-Location) '.venv-training\Scripts\python.exe'
& $python -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cu118
if($LASTEXITCODE){throw 'Torch installation failed'}
& $python -m pip install -r training/requirements.txt
if($LASTEXITCODE){throw 'Training dependency installation failed'}
& $python -m pip check
if($LASTEXITCODE){throw 'Dependency check failed'}
& $python -m pip freeze | Set-Content -Encoding utf8 training/resolved-requirements.txt
