# tests/scripts/config.Tests.ps1 — plain PowerShell assertions (no Pester)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/lib/config.ps1"
$fail = 0
function Assert($name, [bool]$cond) {
    if ($cond) { Write-Host "PASS  $name" -ForegroundColor Green }
    else { Write-Host "FAIL  $name" -ForegroundColor Red; $script:fail++ }
}

$origLocation = (Get-Location).Path

# (a) No jobapp.config.yml anywhere up-tree -> built-in defaults.
$plain = Join-Path ([IO.Path]::GetTempPath()) "config-test-plain-$(Get-Random)"
New-Item -ItemType Directory $plain | Out-Null

# (b) A dir containing jobapp.config.yml with an output_dir override.
$override = Join-Path ([IO.Path]::GetTempPath()) "config-test-override-$(Get-Random)"
New-Item -ItemType Directory $override | Out-Null
Set-Content (Join-Path $override "jobapp.config.yml") @(
    '# test config'
    'output_dir: "custom/{Company}"'
)

try {
    Set-Location $plain
    $c1 = Get-JobAppConfig
    Assert "no config: SourceOfTruthDir default" ($c1.SourceOfTruthDir -eq 'resume_sections')
    Assert "no config: OutputDir default"        ($c1.OutputDir -eq 'applications/{Company}')
    Assert "no config: Root is cwd"              ($c1.Root -eq (Get-Location).Path)

    Set-Location $override
    $c2 = Get-JobAppConfig
    Assert "override: OutputDir wins"            ($c2.OutputDir -eq 'custom/{Company}')
    Assert "override: SourceOfTruthDir default"  ($c2.SourceOfTruthDir -eq 'resume_sections')
    Assert "override: Root is the config dir"    ($c2.Root -eq (Get-Location).Path)
}
finally {
    Set-Location $origLocation
    Remove-Item $plain -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $override -Recurse -Force -ErrorAction SilentlyContinue
}
if ($fail) { Write-Error "$fail assertion(s) failed"; exit 1 }
Write-Host "all assertions passed" -ForegroundColor Green
