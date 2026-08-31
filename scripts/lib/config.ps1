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

function Resolve-Ghostscript {
    # Locate a PDF-compression engine. Returns
    #   @{ Path = <exe>; Direct = <bool> }
    # Direct=$false -> a ps2pdf wrapper, invoked as: & $Path <in.pdf> <out.pdf>
    # Direct=$true  -> a raw Ghostscript engine (gs / gswin64c), invoked with the
    #                  explicit pdfwrite argument list.
    # Resolution order: config hint dir, bundled TinyTeX ps2pdf, then PATH
    # (ps2pdf wrapper first, then the gswin64c / gs engine).
    param([string]$Hint)
    $candidates = @()
    if ($Hint) {
        $hintDir = if (Test-Path $Hint -PathType Container) { $Hint } else { Split-Path $Hint -Parent }
        if ($hintDir) { $candidates += @{ Path = (Join-Path $hintDir 'ps2pdf.exe'); Direct = $false } }
    }
    $candidates += @{ Path = (Join-Path $env:APPDATA 'TinyTeX/bin/windows/ps2pdf.exe'); Direct = $false }
    foreach ($name in 'ps2pdf', 'gswin64c', 'gs') {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { $candidates += @{ Path = $cmd.Source; Direct = ($name -ne 'ps2pdf') } }
    }
    foreach ($c in $candidates) { if ($c.Path -and (Test-Path $c.Path)) { return $c } }
    throw "compress_pdf: no PDF compressor found. Install Ghostscript (gs / gswin64c on PATH) or TinyTeX (bundles ps2pdf), or set pdflatex_path in jobapp.config.yml."
}
