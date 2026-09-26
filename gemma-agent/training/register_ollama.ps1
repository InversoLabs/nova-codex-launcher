param([string]$GGUF=(Join-Path $PSScriptRoot '..\runs\convert-pilot-v5\gemma-pilot-q4_0.gguf'))
$ErrorActionPreference='Stop'
$model='gemma4-codex:pilot-v1'
$resolved=(Resolve-Path -LiteralPath $GGUF).Path
$result=Get-Content (Join-Path (Split-Path $resolved) 'result.json') -Raw | ConvertFrom-Json
if (-not $result.success) { throw 'Conversion and quantization must succeed before registration.' }
$installed=(Invoke-RestMethod http://127.0.0.1:11434/api/tags -TimeoutSec 15).models
if ($installed.name -contains $model) { throw 'Pilot model already exists; refusing to replace it.' }
$source=$resolved.Replace('\','/')
$modelfile=@"
FROM "$source"
TEMPLATE """{{- range .Messages }}<|turn>{{ if eq .Role "assistant" }}model{{ else }}{{ .Role }}{{ end }}
{{ .Content }}<turn|>
{{ end }}<|turn>model
"""
PARAMETER num_ctx 8192
PARAMETER num_thread 4
PARAMETER temperature 0
PARAMETER stop "<turn|>"
PARAMETER stop "<|endoftext|>"
"@
$path=Join-Path (Split-Path $resolved) 'Modelfile'
[IO.File]::WriteAllText($path,$modelfile,[Text.UTF8Encoding]::new($false))
& ollama create $model -f $path
if ($LASTEXITCODE -ne 0) { throw 'Ollama registration failed' }
$manifest=[ordered]@{model=$model;gguf_sha256=(Get-FileHash -LiteralPath $resolved).Hash.ToLower();bytes=(Get-Item -LiteralPath $resolved).Length;scope='Two-step trained pilot; no quality improvement claimed'}
$manifest | ConvertTo-Json | Set-Content (Join-Path (Split-Path $resolved) 'ollama-manifest.json')
$manifest | ConvertTo-Json -Compress
