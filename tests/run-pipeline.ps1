#requires -Version 7
$ErrorActionPreference = 'Stop'

# Single entry point for every mechanical test in this repo:
#   - smoke-fills and compiles all three shipped LaTeX templates,
#   - exercises cover_letter_to_txt.ps1 and Get-JobAppConfig,
#   - then runs each tests/scripts/*.Tests.ps1 and folds its exit code in.
# Plain PowerShell assertions only — no Pester. Run: pwsh tests/run-pipeline.ps1

$root = Split-Path $PSScriptRoot -Parent

# Brings in Invoke-LatexCompile (returns @{ Pdf; Pages; Ok; LogTail }) and,
# transitively, Get-JobAppConfig — without the CLI wrapper's `exit`.
. (Join-Path $root 'scripts/compile_latex.ps1') -AsModule

$work = Join-Path ([IO.Path]::GetTempPath()) "jobapp-pipeline-$(Get-Random)"

$script:fail = 0
function Check($name, $cond) {
    if ($cond) { Write-Host "PASS  $name" -ForegroundColor Green }
    else { Write-Host "FAIL  $name" -ForegroundColor Red; $script:fail++ }
}

# Everything that touches $work runs inside this try so the finally can always
# clean the temp dir up — even when $ErrorActionPreference = 'Stop' turns a
# missing file into a thrown exception mid-run. The pass/fail verdict is decided
# after the finally, so a thrown exception still cleans up *and* still surfaces.
try {
    New-Item -ItemType Directory -Path $work | Out-Null

    # -----------------------------------------------------------------------
    # Placeholder value sets — one entry per {{...}} token the shipped
    # templates actually contain (enumerate with:
    #   Select-String -Path templates/*.tex -Pattern '\{\{[^}]+\}\}' ).
    # Every token is filled explicitly; nothing is left to "minimal" hand-waving.
    # -----------------------------------------------------------------------
    $resumeFill = [ordered]@{
        '{{NAME}}'                      = 'Sample Dev'
        '{{PHONE}}'                     = '(+00) 000-000-000'
        '{{EMAIL}}'                     = 'sample.dev@example.com'
        '{{GITHUB_USERNAME}}'           = 'sample-dev'
        '{{INTRODUCTION_BULLETS}}'      = 'Backend engineer with 4+ years across supply chain and logistics systems.'
        '{{JOB_TITLE}}'                 = 'Software Engineer'
        '{{EMPLOYMENT_DATES}}'          = 'Jan. 2024 -- Present'
        '{{COMPANY_NAME}}'              = 'Acme Corp'
        '{{LOCATION}}'                  = 'Sydney, Australia'
        '{{TECH_STACK}}'                = 'Python, Django, PostgreSQL'
        '{{BULLET_POINT_1}}'            = 'Built and shipped an internal service used across the org.'
        '{{BULLET_POINT_2}}'            = 'Migrated a legacy component with no customer-facing downtime.'
        '{{BULLET_POINT_3}}'            = 'Diagnosed and fixed a recurring production fault.'
        '{{EDUCATION_ENTRIES}}'         = '\resumeSubheading{Example University}{2018 -- 2021}{Bachelor of Computer Science}{Sydney, Australia}'
        '{{LANGUAGES_LIST}}'            = 'Python, Java'
        '{{FRAMEWORKS_AND_TOOLS_LIST}}' = 'Django, Docker, PostgreSQL'
        # resume_2page.tex only — Personal Projects block
        '{{PROJECT_GITHUB_URL}}'        = 'https://github.com/sample-dev/demo'
        '{{PROJECT_NAME}}'              = 'Demo Project'
        '{{PROJECT_TECH_STACK}}'        = 'Kafka, Python'
        '{{PROJECT_ROLE}}'              = 'Personal project'
        '{{PROJECT_BULLET_1}}'          = 'Designed an event-driven ingestion pipeline.'
        '{{PROJECT_BULLET_2}}'          = 'Documented the architecture and its trade-offs.'
    }

    # cover_letter.tex has no {{SUBJECT}} token — the subject line is assembled by
    # the template from {{JOB_TITLE}} + {{REQ_ID}}. Fill both.
    $coverFill = [ordered]@{
        '{{NAME}}'             = 'Sample Dev'
        '{{PHONE}}'            = '(+00) 000-000-000'
        '{{EMAIL}}'            = 'sample.dev@example.com'
        '{{GITHUB_USERNAME}}'  = 'sample-dev'
        '{{DATE}}'             = 'September 1, 2026'
        '{{RECIPIENT_NAME}}'   = 'Hiring Manager'
        '{{RECIPIENT_TITLE}}'  = 'Hiring Manager'
        '{{COMPANY_NAME}}'     = 'Testco'
        '{{COMPANY_ADDRESS}}'  = 'Sydney, NSW, Australia'
        '{{JOB_TITLE}}'        = 'Integration Developer'
        '{{REQ_ID}}'           = 'REQ-123'
        '{{INTRO_PARAGRAPH}}'  = 'I am applying for the Integration Developer position at Testco, bringing over four years of professional software engineering experience.'
        '{{BODY_PARAGRAPH_1}}' = 'At Acme Corp I built supply chain services in Python and Django; at Globex Pty Ltd I built logistics tooling in Java.'
        '{{BODY_PARAGRAPH_2}}' = 'Across both roles I delivered REST APIs and relational-database integrations on PostgreSQL.'
        '{{OUTRO_PARAGRAPH}}'  = 'I would welcome the chance to discuss how this background fits the role. Thank you for your consideration.'
    }

    function Set-Placeholders([string]$text, $map) {
        foreach ($k in $map.Keys) { $text = $text.Replace($k, [string]$map[$k]) }
        return $text
    }

    function Test-NoPlaceholderLeft([string]$path) {
        -not (Select-String -Path $path -Pattern '\{\{[A-Za-z0-9_]+\}\}' -AllMatches -Quiet)
    }

    # -----------------------------------------------------------------------
    # (a) resume_1page.tex : smoke-fills, compiles (Ok), and is exactly 1 page
    # -----------------------------------------------------------------------
    $r1 = Join-Path $work 'resume_1page.tex'
    Set-Placeholders ((Get-Content (Join-Path $root 'templates/resume_1page.tex') -Raw)) $resumeFill |
        Set-Content -LiteralPath $r1 -Encoding utf8
    Check "resume_1page.tex : every placeholder filled" (Test-NoPlaceholderLeft $r1)
    $c1 = Invoke-LatexCompile -TexPath $r1
    Check "resume_1page.tex : compiles (exit 0)" $c1.Ok
    Check "resume_1page.tex : is 1 page"         ($c1.Pages -eq 1)

    # -----------------------------------------------------------------------
    # (b) resume_2page.tex : smoke-fills and compiles
    # -----------------------------------------------------------------------
    $r2 = Join-Path $work 'resume_2page.tex'
    Set-Placeholders ((Get-Content (Join-Path $root 'templates/resume_2page.tex') -Raw)) $resumeFill |
        Set-Content -LiteralPath $r2 -Encoding utf8
    Check "resume_2page.tex : every placeholder filled" (Test-NoPlaceholderLeft $r2)
    $c2 = Invoke-LatexCompile -TexPath $r2
    Check "resume_2page.tex : compiles (exit 0)" $c2.Ok

    # -----------------------------------------------------------------------
    # (c) cover_letter.tex : smoke-fills and compiles
    # -----------------------------------------------------------------------
    $cl = Join-Path $work 'cover_letter.tex'
    Set-Placeholders ((Get-Content (Join-Path $root 'templates/cover_letter.tex') -Raw)) $coverFill |
        Set-Content -LiteralPath $cl -Encoding utf8
    Check "cover_letter.tex : every placeholder filled" (Test-NoPlaceholderLeft $cl)
    $c3 = Invoke-LatexCompile -TexPath $cl
    Check "cover_letter.tex : compiles (exit 0)" $c3.Ok

    # -----------------------------------------------------------------------
    # (d) cover_letter_to_txt.ps1 -> .txt whose first non-blank line starts "Subject:"
    # -----------------------------------------------------------------------
    & (Join-Path $root 'scripts/cover_letter_to_txt.ps1') -TexPath $cl | Out-Null
    $txt = [IO.Path]::ChangeExtension($cl, '.txt')
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
