param([long]$Rounds=100000,[ulong]$Seed=20261019,[int]$Trace=0,[string]$Config="config.json",[string]$Out="benchmark.json")
$ErrorActionPreference="Stop"
Add-Type -TypeDefinition (Get-Content -LiteralPath (Join-Path $PSScriptRoot "CascadeFast.cs") -Raw)
$cfg=Get-Content -LiteralPath (Join-Path $PSScriptRoot $Config) -Raw
$result=[CascadeFast]::Run($cfg,$Rounds,$Seed,$Trace)
Set-Content -LiteralPath (Join-Path $PSScriptRoot $Out) -Value $result -Encoding utf8
$summary=$result | ConvertFrom-Json
$summary | Select-Object rounds,rtp,baseRtp,bonusRtp,elapsedSeconds,hitFrequency,bonusFrequency,baseCascadeFrequency,maximumUnits,guardHits | Format-List
