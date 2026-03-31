# bump-version.ps1 — Bump HD-DHL Dashboard version in index.html
# Usage: .\bump-version.ps1           (patch bump: V.0.7.0 -> V.0.7.1)
#        .\bump-version.ps1 -Minor    (minor bump: V.0.7.0 -> V.0.8.0)
#        .\bump-version.ps1 -Major    (major bump: V.0.7.0 -> V.1.0.0)

param(
    [switch]$Minor,
    [switch]$Major
)

$file = "$PSScriptRoot\index.html"
$content = Get-Content $file -Raw

# Find current version
if ($content -match 'V\.(\d+)\.(\d+)\.(\d+)') {
    $curMajor = [int]$Matches[1]
    $curMinor = [int]$Matches[2]
    $curPatch = [int]$Matches[3]
} else {
    Write-Host "ERROR: Could not find version string (V.x.x.x) in index.html" -ForegroundColor Red
    exit 1
}

# Bump
if ($Major) {
    $newMajor = $curMajor + 1
    $newMinor = 0
    $newPatch = 0
} elseif ($Minor) {
    $newMajor = $curMajor
    $newMinor = $curMinor + 1
    $newPatch = 0
} else {
    $newMajor = $curMajor
    $newMinor = $curMinor
    $newPatch = $curPatch + 1
}

$oldVer = "V.$curMajor.$curMinor.$curPatch"
$newVer = "V.$newMajor.$newMinor.$newPatch"

$newContent = $content -replace [regex]::Escape($oldVer), $newVer
Set-Content $file $newContent -NoNewline

Write-Host "Bumped: $oldVer -> $newVer" -ForegroundColor Green
