# tests/scripts/cover_letter_to_txt.Tests.ps1 — plain PowerShell assertions (no Pester)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../scripts/cover_letter_to_txt.ps1" -AsModule

$fail = 0
function Assert($n, [bool]$c) {
    if ($c) { Write-Host "PASS  $n" -ForegroundColor Green }
    else { Write-Host "FAIL  $n" -ForegroundColor Red; $script:fail++ }
}

$work = Join-Path ([IO.Path]::GetTempPath()) "cl2txt-$(Get-Random)"
New-Item -ItemType Directory $work | Out-Null
try {
    # ---- 1. English letter, full schema ----
    $j = Join-Path $work "cl.json"
    Set-Content -LiteralPath $j -Encoding utf8 '{"name":"Sample Dev","contact":["x@example.com","github.com/s"],"date":"September 1, 2026","recipient":["Hiring Manager","Acme Corp"],"subject":"Application for the Position of X","salutation":"Dear Hiring Manager,","paragraphs":["Para one.","Para two."],"closing":"Sincerely,","signature":"Sample Dev"}'
    $out = Join-Path $work "cl.txt"
    $t = ConvertTo-CoverLetterText -DataPath $j -OutPath $out
    Assert "file written"           (Test-Path $out)
    Assert "first line is Subject"  (($t -split "`n")[0] -eq 'Subject: Application for the Position of X')
    Assert "has date label"         ($t -match '(?m)^Date: September 1, 2026$')
    Assert "has salutation"         ($t -match 'Dear Hiring Manager,')
    Assert "paragraphs separated"   ($t -match 'Para one\.\r?\n\r?\nPara two\.')
    Assert "ends with signature"    ($t.TrimEnd() -match 'Sample Dev$')
    Assert "single trailing newline" ($t.EndsWith("`n") -and -not $t.EndsWith("`n`n"))

    # ---- 2. Chinese letter (lang: zh) — localized Subject/Date labels ----
    $jz = Join-Path $work "cl-zh.json"
    Set-Content -LiteralPath $jz -Encoding utf8 '{"lang":"zh","name":"王开发","contact":["x@example.com"],"date":"2026年9月1日","recipient":["招聘经理"],"subject":"应聘软件工程师职位","salutation":"尊敬的招聘经理：","paragraphs":["第一段。"],"closing":"此致","signature":"王开发"}'
    $tz = ConvertTo-CoverLetterText -DataPath $jz -OutPath (Join-Path $work "cl-zh.txt")
    Assert "zh: first line is 主题："  (($tz -split "`n")[0] -eq '主题：应聘软件工程师职位')
    Assert "zh: date line is 日期："   ($tz -match '(?m)^日期：2026年9月1日$')

    # ---- 3. contact[] with {text,href} objects ----
    $jc = Join-Path $work "cl-contact.json"
    Set-Content -LiteralPath $jc -Encoding utf8 '{"name":"Obj Dev","contact":[{"text":"a@b.com","href":"mailto:a@b.com"},"github.com/x"],"subject":"S","paragraphs":["p"]}'
    $tc = ConvertTo-CoverLetterText -DataPath $jc -OutPath (Join-Path $work "cl-contact.txt")
    Assert "contact objects flattened to text, joined by '  |  '" ($tc -match [regex]::Escape('a@b.com  |  github.com/x'))

    # ---- 4. minimal fixture — only required-ish fields, no spurious blank runs ----
    $jm = Join-Path $work "cl-min.json"
    Set-Content -LiteralPath $jm -Encoding utf8 '{"name":"X","subject":"Y","paragraphs":["p"]}'
    $tm = $null
    $threw = $false
    try { $tm = ConvertTo-CoverLetterText -DataPath $jm -OutPath (Join-Path $work "cl-min.txt") }
    catch { $threw = $true }
    Assert "minimal: does not throw"          (-not $threw)
    Assert "minimal: first line is Subject"   (($tm -split "`n")[0] -eq 'Subject: Y')
    Assert "minimal: no run of 3+ newlines"   ($tm -notmatch "`n`n`n")

    # ---- 5. valid JSON that is not an object -> throws (mirrors cover_letter.html guard) ----
    $jn = Join-Path $work "cl-null.json"
    Set-Content -LiteralPath $jn -Encoding utf8 'null'
    try { ConvertTo-CoverLetterText -DataPath $jn -OutPath (Join-Path $work "cl-null.txt") | Out-Null; $threwNull = $false }
    catch { $threwNull = $true }
    Assert "non-object (null): throws" $threwNull

    $js = Join-Path $work "cl-str.json"
    Set-Content -LiteralPath $js -Encoding utf8 '"hello"'
    try { ConvertTo-CoverLetterText -DataPath $js -OutPath (Join-Path $work "cl-str.txt") | Out-Null; $threwStr = $false }
    catch { $threwStr = $true }
    Assert "non-object (bare string): throws" $threwStr
}
finally { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }

if ($fail) { [Console]::Error.WriteLine("$fail assertion(s) failed"); exit 1 }
Write-Host "all assertions passed" -ForegroundColor Green
