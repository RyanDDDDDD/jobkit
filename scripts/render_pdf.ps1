param(
  [string]$TemplatePath,
  [string]$DataPath,
  [string]$OutPath,
  [string]$Placeholder = '{{RESUME_JSON}}',
  [switch]$KeepHtml,
  [switch]$AsModule
)
$PSNativeCommandUseErrorActionPreference = $false
. "$PSScriptRoot/lib/config.ps1"

function Invoke-RenderPdf {
  param(
    [Parameter(Mandatory)][string]$TemplatePath,
    [Parameter(Mandatory)][string]$DataPath,
    [Parameter(Mandatory)][string]$OutPath,
    [string]$Placeholder = '{{RESUME_JSON}}',
    [switch]$KeepHtml
  )
  $TemplatePath = (Resolve-Path $TemplatePath).Path
  $DataPath     = (Resolve-Path $DataPath).Path
  $outDir = Split-Path $OutPath -Parent
  if (-not $outDir) { $outDir = (Get-Location).Path; $OutPath = Join-Path $outDir $OutPath }
  if (-not (Test-Path $outDir)) { New-Item -ItemType Directory $outDir -Force | Out-Null }
  $OutPath = [IO.Path]::GetFullPath((Join-Path $outDir (Split-Path $OutPath -Leaf)))

  # Resolve the browser BEFORE writing anything, so a missing-Chromium throw leaves no
  # stray <name>.rendered.html in the output dir.
  $cfg     = Get-JobAppConfig
  $browser = Resolve-Browser -Hint $cfg.BrowserPath

  $tpl  = Get-Content -Raw -LiteralPath $TemplatePath
  $json = Get-Content -Raw -LiteralPath $DataPath
  # The JSON is spliced verbatim into <script type="application/json">. ConvertTo-Json does
  # NOT escape '<', so a data string containing "</script>" (or any "</") would close that
  # script element early and break JSON.parse. '<\/' is a legal JSON escape, invisible after
  # JSON.parse, and can never terminate the element.
  $json = $json -replace '</', '<\/'
  $html = $tpl.Replace($Placeholder, $json)

  # Headless Chromium resolves relative url() against the rendered .rendered.html file,
  # which lives next to -OutPath, NOT next to the template. Rewrite the bundled-font
  # url("fonts/...") strings to absolute file:/// paths at the template's own fonts/ dir
  # so the woff2 faces load instead of silently falling back to Georgia. Both templates
  # carry a CSS comment guaranteeing these literal strings are present verbatim. (The
  # identical strings inside that comment get rewritten too — harmless, it is a comment,
  # and it keeps "zero remaining url(\"fonts/\"" true per the task's Ruling 4.)
  $fontDirUrl = 'file:///' + (((Split-Path $TemplatePath -Parent) + '\fonts\') -replace '\\','/')
  $html = $html.Replace('url("fonts/', 'url("' + $fontDirUrl)

  $renderedHtml = [IO.Path]::ChangeExtension($OutPath, '.rendered.html')
  $tmpProfile   = Join-Path ([IO.Path]::GetTempPath()) "render_pdf-profile-$(Get-Random)"

  try {
    Set-Content -LiteralPath $renderedHtml -Value $html -Encoding utf8
    $fileUrl = 'file:///' + ($renderedHtml -replace '\\','/')

    # msedge.exe / chrome.exe are GUI-subsystem binaries: the call operator (`&`) does not
    # block on them and leaves $LASTEXITCODE unset. Start-Process -ArgumentList does NOT
    # quote array elements, so any path with a space (e.g. applications/Jane Street/…, or
    # %TEMP% under C:\Users\John Doe\…) would be split at the space and reach the child
    # mangled. .NET ProcessStartInfo.ArgumentList quotes each element correctly on Windows.
    # A throwaway --user-data-dir keeps this run from handing off to a browser the user
    # already has open (which would exit before printing).
    New-Item -ItemType Directory $tmpProfile -Force | Out-Null
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName               = $browser
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    foreach ($a in @(
      '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
      '--no-first-run', '--no-default-browser-check',
      '--run-all-compositor-stages-before-draw', '--virtual-time-budget=5000',
      "--user-data-dir=$tmpProfile",
      "--print-to-pdf=$OutPath",
      $fileUrl
    )) { $psi.ArgumentList.Add($a) }

    $exit = 1
    $stdout = ''; $stderr = ''
    try {
      $proc = [System.Diagnostics.Process]::Start($psi)
      # Drain both pipes async so neither a full stdout nor a full stderr buffer can
      # deadlock the child before it exits.
      $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
      $stderrTask = $proc.StandardError.ReadToEndAsync()
      # Bound the wall-clock life of the process: --virtual-time-budget caps page time,
      # not process life, so a wedged headless Edge would otherwise hang /generate forever.
      if ($proc.WaitForExit(60000)) {
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        $exit = $proc.ExitCode
      } else {
        try { $proc.Kill() } catch {}
        try { $stdout = $stdoutTask.GetAwaiter().GetResult() } catch { $stdout = '' }
        try { $stderr = $stderrTask.GetAwaiter().GetResult() } catch { $stderr = '' }
        $stderr = ("render_pdf: headless browser did not exit within 60s; killed.`n" + $stderr).Trim()
        $exit = 1
      }
    } catch {
      $stderr = $_.Exception.Message
      $exit = 1
    }
    if ($null -eq $exit) { $exit = 1 }
    $out = ("$stdout`n$stderr").Trim() -split "`r?`n"

    $ok = ($exit -eq 0) -and (Test-Path $OutPath) -and ((Get-Item $OutPath).Length -gt 0)
    $pages = 0
    if ($ok) {
      $bytes = [IO.File]::ReadAllText($OutPath, [Text.Encoding]::Latin1)
      $pages = ([regex]::Matches($bytes, '/Type\s*/Page\b')).Count
    }

    [pscustomobject]@{
      Pdf   = $OutPath
      Pages = $pages
      Ok    = $ok
      Log   = if ($ok) { '' } else { (($out | Select-Object -Last 25) -join "`n") }
      Html  = if ($KeepHtml) { $renderedHtml } else { $null }
    }
  }
  finally {
    Remove-Item $tmpProfile -Recurse -Force -ErrorAction SilentlyContinue
    if (-not $KeepHtml -and (Test-Path $renderedHtml)) {
      Remove-Item $renderedHtml -ErrorAction SilentlyContinue
    }
  }
}

if (-not $AsModule) {
  if (-not $TemplatePath -or -not $DataPath -or -not $OutPath) {
    Write-Error "render_pdf.ps1: -TemplatePath, -DataPath and -OutPath are required"; exit 2
  }
  try {
    $r = Invoke-RenderPdf -TemplatePath $TemplatePath -DataPath $DataPath -OutPath $OutPath -Placeholder $Placeholder -KeepHtml:$KeepHtml
  } catch {
    Write-Error $_.Exception.Message; exit 1
  }
  if ($r.Ok) { Write-Host "OK: $($r.Pdf) ($($r.Pages) page$(if($r.Pages -ne 1){'s'}))" }
  else { Write-Error "Render failed:`n$($r.Log)"; exit 1 }
}
