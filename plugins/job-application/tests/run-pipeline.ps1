#requires -Version 7
$ErrorActionPreference = 'Stop'

# Single entry point for every mechanical test in this repo:
#   - renders the bundled HTML templates with the tests/fixtures/*.data.json
#     (browser -> PDF), asserting the resume is one page,
#   - exercises cover_letter_to_txt.ps1 and Get-JobAppConfig,
#   - then runs each tests/scripts/*.Tests.ps1 and folds its exit code in.
# Plain PowerShell assertions only — no Pester. Run: pwsh tests/run-pipeline.ps1

$root = Split-Path $PSScriptRoot -Parent

# Brings in Invoke-RenderPdf (returns @{ Pdf; Pages; Ok; Log; Html }) and,
# transitively (via lib/config.ps1), Get-JobAppConfig + Resolve-Browser —
# without the CLI wrapper's `exit`.
. (Join-Path $root 'scripts/render_pdf.ps1') -AsModule

$work = Join-Path ([IO.Path]::GetTempPath()) "jobapp-pipeline-$(Get-Random)"

$script:fail = 0
function Check($name, $cond) {
    if ($cond) { Write-Host "PASS  $name" -ForegroundColor Green }
    else { Write-Host "FAIL  $name" -ForegroundColor Red; $script:fail++ }
}
function Skip($name, $why) {
    Write-Host "SKIP  $name ($why)" -ForegroundColor Yellow
}

$resumeTpl = Join-Path $root 'templates/resume.html'
$coverTpl  = Join-Path $root 'templates/cover_letter.html'
$resumeEn  = Join-Path $root 'tests/fixtures/resume.data.json'
$resumeZh  = Join-Path $root 'tests/fixtures/resume.zh.data.json'
$coverJson = Join-Path $root 'tests/fixtures/cover_letter.data.json'

# A Chromium browser is the only hard dependency. If none resolves, the render
# checks skip (not fail) — mirrors tests/scripts/render_pdf.Tests.ps1.
$hasBrowser = $true
try { $null = Resolve-Browser } catch { $hasBrowser = $false }

# pdftotext is optional: PATH first, then the TinyTeX / Git-for-Windows bundles.
# Missing -> the text-extraction sub-asserts skip; the render asserts still run.
$pdftotext = (Get-Command pdftotext -ErrorAction SilentlyContinue).Source
if (-not $pdftotext) {
    foreach ($p in @("$env:APPDATA\TinyTeX\bin\windows\pdftotext.exe",
                     "$env:ProgramFiles\Git\mingw64\bin\pdftotext.exe")) {
        if (Test-Path $p) { $pdftotext = $p; break }
    }
}

# Everything that touches $work runs inside this try so the finally can always
# clean the temp dir up — even when $ErrorActionPreference = 'Stop' turns a
# missing file into a thrown exception mid-run. The pass/fail verdict is decided
# after the finally, so a thrown exception still cleans up *and* still surfaces.
try {
    New-Item -ItemType Directory -Path $work | Out-Null

    # -----------------------------------------------------------------------
    # (a) resume.html + tests/fixtures/resume.data.json -> 1-page PDF, text round-trips
    # -----------------------------------------------------------------------
    if ($hasBrowser) {
        $rEn = Invoke-RenderPdf -TemplatePath $resumeTpl -DataPath $resumeEn -OutPath (Join-Path $work 'r.pdf')
        Check "resume.data.json : renders (Ok)" $rEn.Ok
        Check "resume.data.json : is 1 page"    ($rEn.Pages -eq 1)
        if ($pdftotext -and $rEn.Ok) {
            $txtEn = & $pdftotext -enc UTF-8 $rEn.Pdf - 2>$null
            Check "resume.pdf : text contains 'Sample Dev'" ("$txtEn" -match 'Sample Dev')
            Check "resume.pdf : text contains 'Acme Corp'"  ("$txtEn" -match 'Acme Corp')
        } else {
            Skip "resume.pdf : text extraction" 'pdftotext not found'
        }

        # ---------------------------------------------------------------------
        # (b) resume.html + tests/fixtures/resume.zh.data.json -> Chinese section title
        # ---------------------------------------------------------------------
        $rZh = Invoke-RenderPdf -TemplatePath $resumeTpl -DataPath $resumeZh -OutPath (Join-Path $work 'rz.pdf')
        Check "resume.zh.data.json : renders (Ok)" $rZh.Ok
        Check "resume.zh.data.json : is 1 page"    ($rZh.Pages -eq 1)
        if ($pdftotext -and $rZh.Ok) {
            $txtZh = & $pdftotext -enc UTF-8 $rZh.Pdf - 2>$null
            Check "resume.zh.pdf : text contains '工作经验'" ("$txtZh" -match '工作经验')
        } else {
            Skip "resume.zh.pdf : text extraction" 'pdftotext not found'
        }

        # ---------------------------------------------------------------------
        # (c) cover_letter.html + tests/fixtures/cover_letter.data.json -> 1-page PDF
        # ---------------------------------------------------------------------
        $rCl = Invoke-RenderPdf -TemplatePath $coverTpl -DataPath $coverJson `
            -OutPath (Join-Path $work 'cl.pdf') -Placeholder '{{COVER_LETTER_JSON}}'
        Check "cover_letter.data.json : renders (Ok)" $rCl.Ok
        Check "cover_letter.data.json : is 1 page"    ($rCl.Pages -eq 1)
    } else {
        Skip "template render checks" 'no Chromium browser'
    }

    # -----------------------------------------------------------------------
    # (d) cover_letter_to_txt.ps1 -> .txt whose first non-blank line starts "Subject:"
    # -----------------------------------------------------------------------
    $txt = Join-Path $work 'cl.txt'
    & (Join-Path $root 'scripts/cover_letter_to_txt.ps1') -DataPath $coverJson -OutPath $txt *> $null
    $txtExists = Test-Path -LiteralPath $txt
    Check "cover_letter.txt : produced" $txtExists
    $firstLine = if ($txtExists) {
        Get-Content -LiteralPath $txt | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1
    } else { '' }
    Check "cover_letter.txt : first non-blank line 'Subject:'" ($firstLine -like 'Subject:*')

    # -----------------------------------------------------------------------
    # (e) Get-JobAppConfig with no jobapp.config.yml up-tree -> plugin defaults
    # -----------------------------------------------------------------------
    Push-Location $work
    try { $cfg = Get-JobAppConfig } finally { Pop-Location }
    Check "Get-JobAppConfig : BrowserPath key present"                 ($cfg.ContainsKey('BrowserPath'))
    Check "Get-JobAppConfig : SourceOfTruthDir == 'resume_sections'"   ($cfg.SourceOfTruthDir -eq 'resume_sections')
    Check "Get-JobAppConfig : OutputDir == 'applications/{Company}'"    ($cfg.OutputDir -eq 'applications/{Company}')

    # -----------------------------------------------------------------------
    # (f) each tests/scripts/*.Tests.ps1 exits 0
    # -----------------------------------------------------------------------
    foreach ($t in (Get-ChildItem (Join-Path $root 'tests/scripts') -Filter '*.Tests.ps1' | Sort-Object Name)) {
        $out = & pwsh -NoProfile -File $t.FullName 2>&1
        $ok = $LASTEXITCODE -eq 0
        if (-not $ok) { $out | ForEach-Object { Write-Host "      $_" -ForegroundColor DarkGray } }
        Check "tests/scripts/$($t.Name) : exits 0" $ok
    }
}
finally {
    if (Test-Path $work) { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------------------
if ($fail) { Write-Error "$fail check(s) failed"; exit 1 }
Write-Host "`nall checks passed" -ForegroundColor Green
