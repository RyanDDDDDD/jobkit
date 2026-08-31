function Get-JobAppConfig {
    $defaults = @{
        Root             = (Get-Location).Path
        BrowserPath      = $null
        GhostscriptPath  = $null
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
                    'browser_path'        { $defaults.BrowserPath = [Environment]::ExpandEnvironmentVariables($v) }
                    'ghostscript_path'    { $defaults.GhostscriptPath = [Environment]::ExpandEnvironmentVariables($v) }
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

function Resolve-Browser {
    # Locate a headless-capable Chromium binary for render_pdf.ps1.
    # Order: config hint; Edge (per-machine, both Program Files roots); Chrome
    # (both roots); then PATH (msedge / chrome / chromium / chromium-browser).
    param([string]$Hint)
    $candidates = @()
    if ($Hint) { $candidates += $Hint }
    $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe')
    $candidates += (Join-Path $env:ProgramFiles       'Microsoft\Edge\Application\msedge.exe')
    $candidates += (Join-Path $env:ProgramFiles       'Google\Chrome\Application\chrome.exe')
    $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe')
    foreach ($name in 'msedge', 'chrome', 'chromium', 'chromium-browser') {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { $candidates += $cmd.Source }
    }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    throw "No Chromium browser found. Set browser_path in jobapp.config.yml."
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
    throw "compress_pdf: no PDF compressor found. Install Ghostscript (gs / gswin64c on PATH) or TinyTeX (bundles ps2pdf), or set ghostscript_path in jobapp.config.yml."
}
