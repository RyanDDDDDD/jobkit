param([Parameter(Mandatory)][string]$Path)
$ErrorActionPreference = 'Stop'
$Path = (Resolve-Path $Path).Path
$ext = [IO.Path]::GetExtension($Path).ToLower()
switch ($ext) {
    { $_ -in '.md', '.tex', '.txt' } { Get-Content -Raw -LiteralPath $Path }
    '.pdf' {
        if (-not (Get-Command pdftotext -ErrorAction SilentlyContinue)) { throw "pdftotext not found; install poppler to ingest PDFs." }
        & pdftotext -layout $Path -
    }
    '.docx' {
        if (-not (Get-Command pandoc -ErrorAction SilentlyContinue)) { throw "pandoc not found; install pandoc to ingest .docx." }
        & pandoc -t plain $Path
    }
    default { throw "Unsupported file type: $ext" }
}
