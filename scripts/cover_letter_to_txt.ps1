<#
.SYNOPSIS
    Convert cover_letter.data.json into an email-ready plain-text cover letter.

.DESCRIPTION
    Reads the cover-letter data schema (the same JSON that templates/cover_letter.html
    renders) and emits a plain-text version suitable for pasting into an email body. The
    "Subject:" line is hoisted to the very first line so it can be copied straight into the
    email subject field. Chinese letters (lang: "zh") use the 主题： / 日期： labels so the
    text matches the rendered PDF.

.PARAMETER DataPath
    Path to the cover_letter.data.json file.

.PARAMETER OutPath
    Optional output path. Defaults to cover_letter.txt beside -DataPath.

.PARAMETER AsModule
    Dot-source without running; exposes the ConvertTo-CoverLetterText function.

.EXAMPLE
    pwsh "$env:CLAUDE_PLUGIN_ROOT/scripts/cover_letter_to_txt.ps1" -DataPath cover_letter.data.json
#>
param([string]$DataPath, [string]$OutPath, [switch]$AsModule)
$ErrorActionPreference = 'Stop'

function ConvertTo-CoverLetterText {
    param(
        [Parameter(Mandatory)][string]$DataPath,
        [string]$OutPath
    )
    $d = Get-Content -Raw -LiteralPath $DataPath | ConvertFrom-Json
    # Reject valid-but-non-object JSON (null / "x" / 123 / [ ]) — mirrors the
    # `if (!data || typeof data !== "object")` guard in templates/cover_letter.html.
    # NB: the [pscustomobject] accelerator is [psobject], which -is matches for scalars
    # too; the fully-qualified PSCustomObject type is the one that means "JSON object".
    if ($d -isnot [System.Management.Automation.PSCustomObject]) {
        throw "cover_letter.data.json is not a JSON object"
    }
    if (-not $OutPath) {
        $OutPath = Join-Path (Split-Path -Parent (Resolve-Path -LiteralPath $DataPath).Path) 'cover_letter.txt'
    }
    $isZh = ($d.lang -eq 'zh')

    $lines = [System.Collections.Generic.List[string]]::new()

    # Subject — hoisted to the first line so it can be pasted into the email subject field.
    $lines.Add($(if ($isZh) { "主题：$($d.subject)" } else { "Subject: $($d.subject)" }))
    $lines.Add('')

    # Header: name + contact line ("  |  " separated; objects contribute their .text).
    $lines.Add([string]$d.name)
    if ($d.contact) {
        $contact = @($d.contact | ForEach-Object { if ($_ -is [string]) { $_ } else { $_.text } })
        if ($contact.Count) { $lines.Add(($contact -join '  |  ')) }
    }
    $lines.Add('')

    # Date (labelled, matching the rendered letter).
    if ($d.date) {
        $lines.Add($(if ($isZh) { "日期：$($d.date)" } else { "Date: $($d.date)" }))
        $lines.Add('')
    }

    # Recipient block.
    if ($d.recipient) {
        foreach ($r in @($d.recipient)) { $lines.Add([string]$r) }
        $lines.Add('')
    }

    if ($d.salutation) { $lines.Add([string]$d.salutation); $lines.Add('') }

    # Body paragraphs, separated by a blank line.
    if ($d.paragraphs) {
        $paras = @($d.paragraphs)
        for ($i = 0; $i -lt $paras.Count; $i++) {
            $lines.Add([string]$paras[$i])
            if ($i -lt $paras.Count - 1) { $lines.Add('') }
        }
        $lines.Add('')
    }

    if ($d.closing)   { $lines.Add([string]$d.closing);   $lines.Add('') }
    if ($d.signature) { $lines.Add([string]$d.signature) }

    # Join, strip trailing whitespace per line, one trailing newline.
    $text = (($lines -join "`n") -replace '[ \t]+(\r?\n)', '$1').TrimEnd() + "`n"
    Set-Content -LiteralPath $OutPath -Value $text -Encoding utf8 -NoNewline
    $text
}

if (-not $AsModule) {
    if (-not $DataPath) {
        [Console]::Error.WriteLine("cover_letter_to_txt.ps1: -DataPath is required")
        exit 2
    }
    try {
        if (-not $OutPath) {
            $OutPath = Join-Path (Split-Path -Parent (Resolve-Path -LiteralPath $DataPath).Path) 'cover_letter.txt'
        }
        ConvertTo-CoverLetterText -DataPath $DataPath -OutPath $OutPath | Out-Null
    }
    catch {
        [Console]::Error.WriteLine($_.Exception.Message)
        exit 1
    }
    Write-Host "Wrote $OutPath"
}
