function Get-JobAppConfig {
    $defaults = @{
        Root             = (Get-Location).Path
        PdflatexPath     = $null
        SourceOfTruthDir = "resume_sections"
        OutputDir        = "applications/{Company}"
    }
    $dir = (Get-Location).Path
    while ($dir) {
        $cfg = Join-Path $dir "jobapp.config.yml"
        if (Test-Path $cfg) {
            $defaults.Root = $dir
            foreach ($line in Get-Content $cfg) {
                if ($line -match '^\s*#' -or $line -notmatch ':') { continue }
                $k, $v = $line -split ':', 2
                $v = $v.Trim().Trim('"').Trim("'")
                switch ($k.Trim()) {
                    'pdflatex_path'       { $defaults.PdflatexPath = [Environment]::ExpandEnvironmentVariables($v) }
                    'source_of_truth_dir' { $defaults.SourceOfTruthDir = $v }
                    'output_dir'          { $defaults.OutputDir = $v }
                }
            }
            break
        }
        $parent = Split-Path $dir -Parent
        if ($parent -eq $dir) { break }
        $dir = $parent
    }
    return $defaults
}

function Resolve-Pdflatex {
    param([string]$Hint)
    $candidates = @()
    if ($Hint) { $candidates += $Hint }
    $candidates += (Join-Path $env:APPDATA "TinyTeX/bin/windows/pdflatex.exe")
    $cmd = Get-Command pdflatex -ErrorAction SilentlyContinue
    if ($cmd) { $candidates += $cmd.Source }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    throw "pdflatex not found. Set pdflatex_path in jobapp.config.yml."
}
