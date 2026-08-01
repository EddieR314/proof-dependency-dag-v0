param(
    [string]$Version = "v0.1"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$releaseName = "algebra-dag-suitability-screening-$Version-frozen"
$zipPath = Join-Path $root "$releaseName.zip"
$checksumPath = "$zipPath.sha256"
$stage = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-" + [guid]::NewGuid().ToString("N"))
$packageRoot = Join-Path $stage $releaseName

$items = @(
    "skills\dag-suitability-screening",
    "data\dag_suitability_screening",
    "outputs\dag_suitability_screening",
    "scripts\build_algebra_screening_calibration.py",
    "scripts\make_stratified_audit.py",
    "scripts\prepare_screening_batch.py",
    "scripts\test_dag_suitability_screening.py",
    "scripts\validate_screening_results.py",
    "work\dag_suitability_screening\analyze_borderline.mjs",
    "work\dag_suitability_screening\finalize_borderline_second_pass.mjs",
    "work\dag_suitability_screening\clean_promotable_borderlines.mjs"
)

try {
    New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null
    foreach ($relative in $items) {
        $source = Join-Path $root $relative
        if (-not (Test-Path -LiteralPath $source)) {
            throw "Required release item missing: $relative"
        }
        $destination = Join-Path $packageRoot $relative
        $parent = Split-Path -Parent $destination
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
    }

    $manifestFiles = Get-ChildItem -LiteralPath $packageRoot -Recurse -File |
        Where-Object { $_.Name -ne "MANIFEST.json" } |
        Sort-Object FullName |
        ForEach-Object {
            [ordered]@{
                path = $_.FullName.Substring($packageRoot.Length + 1).Replace("\", "/")
                bytes = $_.Length
                sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
            }
        }

    $manifest = [ordered]@{
        release = $releaseName
        frozen_at = "2026-08-01"
        scope = "algebra DAG-suitability screening"
        counts = [ordered]@{ suitable = 186; borderline = 44; unsuitable = 20; total = 250 }
        human_review = [ordered]@{
            stratified_audit_records = 108
            stratified_audit_confirmed = 108
            cleaned_records_confirmed_complete_and_correct = 13
        }
        boundary = "Suitable means ready for later DAG construction; it does not mean DAG or Lean verification is complete."
        files = @($manifestFiles)
    }
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $packageRoot "MANIFEST.json") -Encoding utf8

    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    if (Test-Path -LiteralPath $checksumPath) { Remove-Item -LiteralPath $checksumPath -Force }
    Compress-Archive -LiteralPath $packageRoot -DestinationPath $zipPath -CompressionLevel Optimal
    $zipHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath).Hash.ToLowerInvariant()
    "$zipHash  $releaseName.zip" | Set-Content -LiteralPath $checksumPath -Encoding ascii

    [ordered]@{
        zip = $zipPath
        checksum_file = $checksumPath
        sha256 = $zipHash
        archived_files = $manifestFiles.Count + 1
        bytes = (Get-Item -LiteralPath $zipPath).Length
    } | ConvertTo-Json
}
finally {
    $resolvedTemp = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
    $resolvedStage = [System.IO.Path]::GetFullPath($stage)
    if ($resolvedStage.StartsWith($resolvedTemp, [System.StringComparison]::OrdinalIgnoreCase) -and
        (Test-Path -LiteralPath $stage)) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
