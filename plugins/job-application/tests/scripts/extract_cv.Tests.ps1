# tests/scripts/extract_cv.Tests.ps1 — plain PowerShell assertions (no Pester)
$ErrorActionPreference = 'Stop'
$script = "$PSScriptRoot/../../scripts/extract_cv.ps1"
$fail = 0
function Assert($name, [bool]$cond) {
    if ($cond) { Write-Host "PASS  $name" -ForegroundColor Green }
    else { Write-Host "FAIL  $name" -ForegroundColor Red; $script:fail++ }
}
$work = Join-Path ([IO.Path]::GetTempPath()) "extract_cv-test-$(Get-Random)"
New-Item -ItemType Directory $work | Out-Null
try {
    $md = Join-Path $work "a.md"; Set-Content $md "# Sample Dev`nC++ engineer"
    Assert "reads .md verbatim" ((& $script -Path $md) -join "`n" -match "C\+\+ engineer")

    $tex = Join-Path $work "a.tex"; Set-Content $tex "\section{Experience} Globex"
    Assert "reads .tex verbatim" ((& $script -Path $tex) -join "`n" -match "Globex")

    $rtf = Join-Path $work "a.rtf"; Set-Content $rtf "x"
    $threw = $false; $msg = ""
    try { & $script -Path $rtf } catch { $threw = $true; $msg = $_.Exception.Message }
    Assert "unsupported ext throws with 'Unsupported'" ($threw -and $msg -match "Unsupported")
}
finally { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
if ($fail) { Write-Error "$fail assertion(s) failed"; exit 1 }
Write-Host "all assertions passed" -ForegroundColor Green
