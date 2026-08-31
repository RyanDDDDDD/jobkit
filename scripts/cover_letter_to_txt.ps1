<#
.SYNOPSIS
    Convert a LaTeX cover letter (built from templates/cover_letter.tex)
    into a plain-text version suitable for pasting into an email body.

.DESCRIPTION
    Strips the LaTeX preamble and markup, unescapes LaTeX special characters,
    flattens the date/recipient block, and hoists the "Subject:" line to the top
    so it can be copied straight into the email subject field.

.PARAMETER TexPath
    Path to the cover_letter.tex file to convert.

.PARAMETER OutPath
    Optional output path. Defaults to the .tex path with a .txt extension
    (e.g. cover_letter.tex -> cover_letter.txt in the same folder).

.EXAMPLE
    & "C:\Users\user\Desktop\Resume\scripts\cover_letter_to_txt.ps1" -TexPath cover_letter.tex
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$TexPath,

    [string]$OutPath
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $TexPath)) {
    throw "TeX file not found: $TexPath"
}
$TexPath = (Resolve-Path -LiteralPath $TexPath).Path
if (-not $OutPath) {
    $OutPath = [System.IO.Path]::ChangeExtension($TexPath, '.txt')
}

$raw = Get-Content -Raw -LiteralPath $TexPath

# Keep only the document body.
if ($raw -match '(?s)\\begin\{document\}(.*?)\\end\{document\}') {
    $raw = $Matches[1]
}

$result = New-Object System.Collections.Generic.List[string]

foreach ($line in ($raw -split "`r?`n")) {
    $l = $line

    # Drop full-line LaTeX comments and trailing comments.
    $l = [regex]::Replace($l, '(?<!\\)%.*$', '')
    $l = $l.Trim()
    if ($l -eq '') { $result.Add(''); continue }

    # Drop structural / preamble-style commands.
    if ($l -match '^\\(begin|end)\{(center|tabular\*|itemize|document)\}') { continue }
    if ($l -match '^\\(pagestyle|fancyhf|fancyfoot|renewcommand|addtolength|urlstyle|raggedbottom|raggedright|setlength|input|usepackage|documentclass|newcommand)\b') { continue }

    # Inline markup -> text.
    $l = [regex]::Replace($l, '\\href\{[^{}]*\}\{\\underline\{([^{}]*)\}\}', '$1')
    $l = [regex]::Replace($l, '\\href\{([^{}]*)\}\{([^{}]*)\}', '$2 ($1)')
    $l = [regex]::Replace($l, '\\underline\{([^{}]*)\}', '$1')
    $l = [regex]::Replace($l, '\\textbf\{([^{}]*)\}', '$1')
    $l = [regex]::Replace($l, '\\textit\{([^{}]*)\}', '$1')
    $l = [regex]::Replace($l, '\\(Huge|LARGE|Large|large|normalsize|small|footnotesize|scshape)\b', '')
    $l = [regex]::Replace($l, '\\vspace\{[^{}]*\}', '')
    $l = $l -replace '\\\\', ''          # LaTeX line break -> already line-split
    $l = $l -replace '[{}]', ''
    $l = $l -replace '\$\|\$', '|'       # heading separator
    $l = $l -replace '\\&', '&' -replace '\\%', '%' -replace '\\#', '#' -replace '\\_', '_' -replace '\\\$', '$'
    $l = $l -replace '---', "$([char]0x2014)" -replace '(?<!-)--(?!-)', "$([char]0x2013)"
    $l = $l -replace '``', '"' -replace "''", '"'
    $l = $l -replace '~', ' '
    $l = $l -replace '\\ ', ' '
    $l = ($l -replace '\s+$', '') -replace '  +', ' '

    # Skip any residual pure-command lines.
    if ($l -match '^\\[A-Za-z]') { continue }

    $result.Add($l.Trim())
}

$text = ($result -join "`n")

# Join contact fragments that were split across physical lines (line ends with "|").
$text = [regex]::Replace($text, '\|\s*\n\s*', '| ')

# Collapse excess blank lines.
$text = [regex]::Replace($text, "`n{3,}", "`n`n").Trim()

# Hoist the Subject line to the very top.
$lines = [System.Collections.Generic.List[string]]($text -split "`n")
$subject = $lines | Where-Object { $_ -match '^Subject:' } | Select-Object -First 1
if ($subject) {
    $lines = $lines | Where-Object { $_ -ne $subject }
    $text = $subject + "`n`n" + (($lines -join "`n").Trim())
}

# Final pass: collapse any blank runs created by the removals above.
$text = [regex]::Replace($text, "`n{3,}", "`n`n").Trim() + "`n"

Set-Content -LiteralPath $OutPath -Value $text -Encoding utf8
Write-Host "Wrote plain-text cover letter: $OutPath"
