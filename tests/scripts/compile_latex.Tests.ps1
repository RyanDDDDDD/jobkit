# tests/scripts/compile_latex.Tests.ps1 — plain PowerShell assertions (no Pester)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/compile_latex.ps1" -AsModule
$fail = 0
function Assert($name, [bool]$cond) {
    if ($cond) { Write-Host "PASS  $name" -ForegroundColor Green }
    else { Write-Host "FAIL  $name" -ForegroundColor Red; $script:fail++ }
}
$work = Join-Path ([IO.Path]::GetTempPath()) "compile_latex-test-$(Get-Random)"
New-Item -ItemType Directory $work | Out-Null
try {
    $tex = Join-Path $work "min.tex"
    Set-Content $tex "\documentclass{article}\begin{document}hello\end{document}"
    $r = Invoke-LatexCompile -TexPath $tex
    Assert "minimal doc: Ok"        $r.Ok
    Assert "minimal doc: 1 page"    ($r.Pages -eq 1)
    Assert "minimal doc: pdf exists" (Test-Path $r.Pdf)

    $bad = Join-Path $work "bad.tex"
    Set-Content $bad "\documentclass{article}\begin{document}\undefinedmacro"
    $r2 = Invoke-LatexCompile -TexPath $bad
    Assert "broken doc: not Ok"            (-not $r2.Ok)
    Assert "broken doc: LogTail has error" ($r2.LogTail -match "Undefined control sequence|Emergency stop")
    Assert "broken doc: .tex kept"         (Test-Path $bad)
}
finally { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
if ($fail) { Write-Error "$fail assertion(s) failed"; exit 1 }
Write-Host "all assertions passed" -ForegroundColor Green
