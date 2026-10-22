$ErrorActionPreference = 'Stop'
$plan = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'deployment_plan.json') -Raw | ConvertFrom-Json
$sourceRoot = [IO.Path]::GetFullPath($plan.source)
$targetRoot = [IO.Path]::GetFullPath($plan.target)
if ($targetRoot -ne 'D:\Kazaluka_slots\polska_gurom_phase2_v0.1') {
    throw 'Unexpected deployment target'
}

function Get-ContainedPath([string]$root, [string]$relative) {
    $resolved = [IO.Path]::GetFullPath((Join-Path $root $relative))
    if (-not $resolved.StartsWith($root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Path escapes its intended project directory'
    }
    return $resolved
}

# Preflight every source and destination file before changing the target.
foreach ($entry in $plan.source_files.PSObject.Properties) {
    $path = Get-ContainedPath $sourceRoot $entry.Name
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Source changed: $($entry.Name)"
    }
}
$existing = @(Get-ChildItem -LiteralPath $targetRoot -File -Recurse -Force)
if ($existing.Count -ne @($plan.original_files.PSObject.Properties).Count) {
    throw 'Target changed since backup; prepare a new backup'
}
foreach ($entry in $plan.original_files.PSObject.Properties) {
    $path = Get-ContainedPath $targetRoot $entry.Name
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Target changed since backup: $($entry.Name)"
    }
}
if ((Get-FileHash -LiteralPath $plan.backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $plan.backup_sha256) {
    throw 'Backup changed'
}

$backupFolder = 'D:\Kazaluka_slots\backups'
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
$targetBackup = Join-Path $backupFolder $plan.backup_name
if (Test-Path -LiteralPath $targetBackup) { throw 'Backup already exists' }
Copy-Item -LiteralPath $plan.backup -Destination $targetBackup
if ((Get-FileHash -LiteralPath $targetBackup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $plan.backup_sha256) {
    throw 'Copied backup failed verification'
}

# Retain obsolete reports separately so the active project has one set of results.
$legacyRoot = Get-ContainedPath $targetRoot 'legacy_v0_1'
if (Test-Path -LiteralPath $legacyRoot) { throw 'Legacy directory already exists' }
New-Item -ItemType Directory -Path $legacyRoot | Out-Null
foreach ($name in @('PHASE2_REPORT.md','simulation_10000.json','simulation_100000.json','simulation_1m.json','theory.json')) {
    $oldFile = Get-ContainedPath $targetRoot $name
    if (Test-Path -LiteralPath $oldFile -PathType Leaf) {
        Move-Item -LiteralPath $oldFile -Destination (Get-ContainedPath $legacyRoot $name)
    }
}
foreach ($entry in $plan.source_files.PSObject.Properties) {
    $from = Get-ContainedPath $sourceRoot $entry.Name
    $to = Get-ContainedPath $targetRoot $entry.Name
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($to)) -Force | Out-Null
    Copy-Item -LiteralPath $from -Destination $to -Force
}
foreach ($entry in $plan.source_files.PSObject.Properties) {
    $path = Get-ContainedPath $targetRoot $entry.Name
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Deployed file differs: $($entry.Name)"
    }
}
@{
    status = 'copied_and_hash_verified'
    target = $targetRoot
    version = '0.2.0'
    files_verified = @($plan.source_files.PSObject.Properties).Count
    backup = $targetBackup
    legacy = $legacyRoot
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'deployment_result.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'deployment_result.json') -Raw
