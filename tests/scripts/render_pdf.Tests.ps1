# tests/scripts/render_pdf.Tests.ps1 — plain PowerShell assertions (no Pester)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/render_pdf.ps1" -AsModule

$fail = 0
function Assert($n, [bool]$c) {
    if ($c) { Write-Host "PASS  $n" -ForegroundColor Green }
    else { Write-Host "FAIL  $n" -ForegroundColor Red; $script:fail++ }
}

# A Chromium browser is a documented global constraint. If none resolves, skip the file.
try { $null = Resolve-Browser } catch {
    Write-Host "SKIP: no Chromium browser ($($_.Exception.Message))" -ForegroundColor Yellow
    exit 0
}

# Resolve pdftotext for the bad-json text assertion; skip that one check if unavailable.
$pdftotext = (Get-Command pdftotext -ErrorAction SilentlyContinue).Source
if (-not $pdftotext) {
    foreach ($p in @("$env:APPDATA\TinyTeX\bin\windows\pdftotext.exe",
                     "$env:ProgramFiles\Git\mingw64\bin\pdftotext.exe")) {
        if (Test-Path $p) { $pdftotext = $p; break }
    }
}

$repo = (Resolve-Path "$PSScriptRoot/../..").Path
$work = Join-Path ([IO.Path]::GetTempPath()) "render_pdf-test-$(Get-Random)"
New-Item -ItemType Directory $work | Out-Null
try {
    $tpl = Join-Path $repo "templates/resume.html"

    # ---- small JSON -> 1 page ----
    $small = Join-Path $work "s.json"
    Set-Content $small '{"name":"Testy McTest","contact":["x@example.com"],"sections":[{"title":"Skills","type":"skills","groups":[{"label":"Languages","value":"Python"}]}]}'
    $r = Invoke-RenderPdf -TemplatePath $tpl -DataPath $small -OutPath (Join-Path $work "s.pdf")
    Assert "small: Ok"          $r.Ok
    Assert "small: 1 page"      ($r.Pages -eq 1)
    Assert "small: pdf exists"  (Test-Path $r.Pdf)

    # ---- large JSON (5 roles, many bullets) -> >= 3 pages ----
    $roles = 1..5 | ForEach-Object {
        $i = $_
        $bullets = (1..8 | ForEach-Object {
            '"Delivered a substantial body of work item ' + $_ + ' for role ' + $i +
            ', spanning design, implementation, rollout and measurement across several teams and quarters."'
        }) -join ','
        '{"primary":"Senior Engineer ' + $i + '","secondary":"Company ' + $i +
        '","dates":"20' + (10 + $i) + '-20' + (11 + $i) +
        '","stack":"TypeScript, Go, PostgreSQL, Kubernetes","bullets":[' + $bullets + ']}'
    }
    $bigObj = '{"name":"Big Resume","contact":["big@example.com","555-0100"],' +
              '"intro":["A senior engineer with a long and detailed track record across many organisations."],' +
              '"sections":[{"title":"Experience","type":"entries","items":[' + ($roles -join ',') + ']}]}'
    $big = Join-Path $work "b.json"
    Set-Content $big $bigObj
    $rbig = Invoke-RenderPdf -TemplatePath $tpl -DataPath $big -OutPath (Join-Path $work "b.pdf")
    Assert "big: Ok"            $rbig.Ok
    Assert "big: >= 3 pages"    ($rbig.Pages -ge 3)

    # ---- malformed JSON -> still renders a pdf whose page shows the error ----
    $bad = Join-Path $work "bad.json"
    Set-Content $bad '{ this is not json'
    $rb = Invoke-RenderPdf -TemplatePath $tpl -DataPath $bad -OutPath (Join-Path $work "bad.pdf")
    Assert "bad json: still renders a pdf" $rb.Ok
    if ($pdftotext) {
        $txt = & $pdftotext -enc UTF-8 $rb.Pdf - 2>$null
        Assert "bad json: page shows the error" ("$txt" -match "Invalid resume JSON")
    } else {
        Write-Host "SKIP  bad json: page shows the error (pdftotext not found)" -ForegroundColor Yellow
    }

    # ---- font-URL rewrite: -KeepHtml leaves a rendered file with absolute file:/// font URLs ----
    $kh = Invoke-RenderPdf -TemplatePath $tpl -DataPath $small -OutPath (Join-Path $work "k.pdf") -KeepHtml
    $rendered = Get-Content -Raw -LiteralPath $kh.Html
    Assert "rewrite: no relative url(""fonts/ remains" (-not ($rendered -match 'url\("fonts/'))
    Assert "rewrite: both @font-face src now file:///" (([regex]::Matches($rendered, 'src:\s*url\("file:///[^"]*\.woff2"')).Count -eq 2)
}
finally { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }

if ($fail) { Write-Error "$fail assertion(s) failed"; exit 1 }
Write-Host "all assertions passed" -ForegroundColor Green
