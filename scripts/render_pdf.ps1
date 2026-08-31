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

  $tpl  = Get-Content -Raw -LiteralPath $TemplatePath
  $json = Get-Content -Raw -LiteralPath $DataPath
  $html = $tpl.Replace($Placeholder, $json)

  # Headless Chromium resolves relative url() against the rendered .rendered.html file,
  # which lives next to -OutPath, NOT next to the template. Rewrite the bundled-font
  # url("fonts/...") strings to absolute file:/// paths at the template's own fonts/ dir
  # so the woff2 faces load instead of silently falling back to Georgia. Both templates
  # carry a CSS comment guaranteeing these literal strings are present verbatim.
  $fontDirUrl = 'file:///' + (((Split-Path $TemplatePath -Parent) + '\fonts\') -replace '\\','/')
  $html = $html.Replace('url("fonts/', 'url("' + $fontDirUrl)

  $renderedHtml = [IO.Path]::ChangeExtension($OutPath, '.rendered.html')
  Set-Content -LiteralPath $renderedHtml -Value $html -Encoding utf8

  $cfg     = Get-JobAppConfig
  $browser = Resolve-Browser -Hint $cfg.BrowserPath
  $fileUrl = 'file:///' + ($renderedHtml -replace '\\','/')

  # msedge.exe / chrome.exe are GUI-subsystem binaries: the call operator (`&`) does not
  # block on them and leaves $LASTEXITCODE unset, so drive them through Start-Process -Wait
  # with redirected streams. A throwaway --user-data-dir keeps this run from colliding with
  # a browser the user already has open (which would make the new process hand off and exit
  # before printing).
  $tmpProfile = Join-Path ([IO.Path]::GetTempPath()) "render_pdf-profile-$(Get-Random)"
  $outLog = Join-Path $tmpProfile 'stdout.txt'
  $errLog = Join-Path $tmpProfile 'stderr.txt'
  New-Item -ItemType Directory $tmpProfile -Force | Out-Null
  $bArgs = @(
    '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
    '--no-first-run', '--no-default-browser-check',
    "--user-data-dir=$tmpProfile",
    '--run-all-compositor-stages-before-draw', '--virtual-time-budget=5000',
    "--print-to-pdf=$OutPath", $fileUrl
  )
  $exit = 1
  try {
    $proc = Start-Process -FilePath $browser -ArgumentList $bArgs -NoNewWindow -Wait -PassThru `
                          -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    $exit = $proc.ExitCode
  } catch { $exit = 1 }
  $out = @()
  foreach ($f in @($errLog, $outLog)) {
    if (Test-Path $f) { $out += (Get-Content -LiteralPath $f) }
  }
  Remove-Item $tmpProfile -Recurse -Force -ErrorAction SilentlyContinue

  $ok = ($exit -eq 0) -and (Test-Path $OutPath) -and ((Get-Item $OutPath).Length -gt 0)
  $pages = 0
  if ($ok) {
    $bytes = [IO.File]::ReadAllText($OutPath, [Text.Encoding]::Latin1)
    $pages = ([regex]::Matches($bytes, '/Type\s*/Page\b')).Count
  }
  if (-not $KeepHtml) { Remove-Item $renderedHtml -ErrorAction SilentlyContinue }

  [pscustomobject]@{
    Pdf   = $OutPath
    Pages = $pages
    Ok    = $ok
    Log   = if ($ok) { '' } else { (($out | Select-Object -Last 25) -join "`n") }
    Html  = if ($KeepHtml) { $renderedHtml } else { $null }
  }
}

if (-not $AsModule) {
  if (-not $TemplatePath -or -not $DataPath -or -not $OutPath) {
    Write-Error "render_pdf.ps1: -TemplatePath, -DataPath and -OutPath are required"; exit 2
  }
  $r = Invoke-RenderPdf -TemplatePath $TemplatePath -DataPath $DataPath -OutPath $OutPath -Placeholder $Placeholder -KeepHtml:$KeepHtml
  if ($r.Ok) { Write-Host "OK: $($r.Pdf) ($($r.Pages) page$(if($r.Pages -ne 1){'s'}))" }
  else { Write-Error "Render failed:`n$($r.Log)"; exit 1 }
}
