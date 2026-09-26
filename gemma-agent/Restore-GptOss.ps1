$ErrorActionPreference='Stop'
$body=@{model='gpt-oss:20b';prompt='';stream=$false;keep_alive=-1;options=@{num_ctx=8192;num_predict=1}} | ConvertTo-Json -Depth 4 -Compress
Invoke-RestMethod http://127.0.0.1:11434/api/generate -Method Post -ContentType application/json -Body $body -TimeoutSec 300 | Select-Object model,done
Invoke-RestMethod http://127.0.0.1:11434/api/ps -TimeoutSec 10 | ConvertTo-Json -Depth 4
