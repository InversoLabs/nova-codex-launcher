$ErrorActionPreference='Stop'
# Run administratively on NOVA, once. Profiles reuse existing model blobs.
$base='gemma4-codex:pilot-v1'
$installed=(Invoke-RestMethod http://127.0.0.1:11434/api/tags).models.name
if ($installed -notcontains $base) { throw 'Install the trained base pilot first.' }
foreach ($context in @(4096,16384,32768)) {
    $name=$base+'-'+($context/1024)+'k'
    if ($installed -contains $name) {
        $shown=Invoke-RestMethod http://127.0.0.1:11434/api/show -Method Post -ContentType application/json -Body (@{model=$name}|ConvertTo-Json)
        if ($shown.parameters -notmatch ('num_ctx\s+'+$context+'\b')) { throw "Existing profile has a different context: $name" }
        continue
    }
    $body=@{model=$name;from=$base;parameters=@{num_ctx=$context};stream=$false}|ConvertTo-Json -Depth 4
    Invoke-RestMethod http://127.0.0.1:11434/api/create -Method Post -ContentType application/json -Body $body -TimeoutSec 120 | Out-Null
    Write-Output "Created $name with $context tokens"
}
