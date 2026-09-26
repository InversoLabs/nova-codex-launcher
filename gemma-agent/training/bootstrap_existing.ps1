# Reuse the existing compatible Python 3.12 ML libraries read-only.
# Additional packages are installed only into the lab's private environment.
$ErrorActionPreference='Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$shared='C:\Users\justi\Documents\comfy\ComfyUI\venv\Lib\site-packages'
if(-not (Test-Path "$shared\torch")){throw 'Existing compatible runtime not found; use setup.ps1 for a standalone install'}
if(-not (Test-Path '.venv-training\Scripts\python.exe')){& py -3.12 -m venv .venv-training}
[IO.File]::WriteAllText((Join-Path (Get-Location) '.venv-training\Lib\site-packages\shared-ml-readonly.pth'),$shared+"`n")
$env:PYTHONDONTWRITEBYTECODE='1'
& .\.venv-training\Scripts\python.exe -m pip install 'peft>=0.18,<1' 'accelerate>=1.10,<2' 'bitsandbytes>=0.49,<1'
if($LASTEXITCODE){throw 'Private ML dependency install failed'}
# Override the borrowed older Transformers only inside this private environment.
& .\.venv-training\Scripts\python.exe -m pip install --ignore-installed --no-deps transformers==5.17.0 safetensors==0.8.0 tokenizers==0.23.1
if($LASTEXITCODE){throw 'Private Gemma runtime override failed'}
& .\.venv-training\Scripts\python.exe -m pip check
if($LASTEXITCODE){throw 'ML dependency check failed'}
& .\.venv-training\Scripts\python.exe -m pip freeze | Set-Content -Encoding utf8 training/resolved-requirements.txt
