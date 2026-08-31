param(
    [string]$TexPath,
    [int]$Runs = 2,
    [switch]$AsModule
)
. "$PSScriptRoot/lib/config.ps1"

function Invoke-LatexCompile {
    param([Parameter(Mandatory)][string]$TexPath, [int]$Runs = 2)
    $TexPath = (Resolve-Path $TexPath).Path
    $dir = Split-Path $TexPath -Parent
    $cfg = Get-JobAppConfig
    $engine = Resolve-Pdflatex -Hint $cfg.PdflatexPath
    $ok = $true; $logTail = ""
    for ($i = 1; $i -le $Runs; $i++) {
        $out = & $engine -interaction=nonstopmode -halt-on-error -output-directory $dir $TexPath 2>&1
        if ($LASTEXITCODE -ne 0) { $ok = $false; $logTail = ($out | Select-Object -Last 25) -join "`n"; break }
    }
    $pdf = [IO.Path]::ChangeExtension($TexPath, ".pdf")
    $pages = 0
    if ($ok -and (Test-Path $pdf)) {
        $log = [IO.Path]::ChangeExtension($TexPath, ".log")
        if (Test-Path $log) {
            $m = Select-String -Path $log -Pattern 'Output written on .*\((\d+) page' | Select-Object -Last 1
            if ($m) { $pages = [int]$m.Matches[0].Groups[1].Value }
        }
    }
    foreach ($ext in '.aux', '.out') {
        $f = [IO.Path]::ChangeExtension($TexPath, $ext); if (Test-Path $f) { Remove-Item $f }
    }
    return [pscustomobject]@{ Pdf = $pdf; Pages = $pages; Ok = $ok; LogTail = $logTail }
}

if (-not $AsModule) {
    if (-not $TexPath) { Write-Error "compile_latex.ps1: -TexPath is required"; exit 2 }
    $r = Invoke-LatexCompile -TexPath $TexPath -Runs $Runs
    if ($r.Ok) { Write-Host "OK: $($r.Pdf) ($($r.Pages) page$(if($r.Pages -ne 1){'s'}))" }
    else { Write-Error "LaTeX failed:`n$($r.LogTail)"; exit 1 }
}
