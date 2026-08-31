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
    Assert "no config: BrowserPath null"         ($null -eq $c1.BrowserPath)
    Assert "no config: GhostscriptPath null"     ($null -eq $c1.GhostscriptPath)
    Assert "no config: no PdflatexPath key"      (-not $c1.ContainsKey('PdflatexPath'))

    Set-Location $override
    $c2 = Get-JobAppConfig
    Assert "override: OutputDir wins"            ($c2.OutputDir -eq 'custom/{Company}')
    Assert "override: SourceOfTruthDir default"  ($c2.SourceOfTruthDir -eq 'resume_sections')
    Assert "override: Root is the config dir"    ($c2.Root -eq (Get-Location).Path)

    # (c) browser_path override is read into BrowserPath.
    $bcfg = Join-Path ([IO.Path]::GetTempPath()) "config-test-browser-$(Get-Random)"
    New-Item -ItemType Directory $bcfg | Out-Null
    Set-Content (Join-Path $bcfg "jobapp.config.yml") @(
        'browser_path: "C:/does/not/exist/msedge.exe"'
        'ghostscript_path: "C:/does/not/exist/gswin64c.exe"'
    )
    try {
        Set-Location $bcfg
        $c3 = Get-JobAppConfig
        Assert "browser override: BrowserPath read"     ($c3.BrowserPath -eq 'C:/does/not/exist/msedge.exe')
        Assert "gs override: GhostscriptPath read"       ($c3.GhostscriptPath -eq 'C:/does/not/exist/gswin64c.exe')
    } finally {
        Set-Location $origLocation
        Remove-Item $bcfg -Recurse -Force -ErrorAction SilentlyContinue
    }

    # (d) Resolve-Browser: returns an existing path, or throws mentioning browser_path.
    try {
        $b = Resolve-Browser
        Assert "Resolve-Browser: returns an existing path" (Test-Path $b)
    } catch {
        Assert "Resolve-Browser: throw mentions browser_path" ($_.Exception.Message -match 'browser_path')
    }

    # Resolve-Browser honours a valid -Hint over auto-detection.
    Assert "Resolve-Browser: -Hint wins when it exists" `
        ((Resolve-Browser -Hint $PSCommandPath) -eq $PSCommandPath)
}
finally {
    Set-Location $origLocation
    Remove-Item $plain -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $override -Recurse -Force -ErrorAction SilentlyContinue
}
if ($fail) { Write-Error "$fail assertion(s) failed"; exit 1 }
Write-Host "all assertions passed" -ForegroundColor Green
