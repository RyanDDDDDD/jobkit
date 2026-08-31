param (
    [Parameter(Mandatory=$true)]
    [string]$PdfPath
)

. "$PSScriptRoot/lib/config.ps1"

if (-not (Test-Path $PdfPath)) {
    Write-Error "File not found: $PdfPath"
    exit 1
}

$cfg = Get-JobAppConfig
$gs = Resolve-Ghostscript -Hint $cfg.PdflatexPath   # throws a clear error if none resolve

$pdfAbsPath = (Resolve-Path $PdfPath).Path
$tempPath = [System.IO.Path]::ChangeExtension($pdfAbsPath, "temp.pdf")
$origSize = (Get-Item $pdfAbsPath).Length

Remove-Item $tempPath -ErrorAction SilentlyContinue

# Run compression into a temp file; never touch the original until it succeeds.
if ($gs.Direct) {
    & $gs.Path -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook `
        -dNOPAUSE -dBATCH "-sOutputFile=$tempPath" $pdfAbsPath
} else {
    & $gs.Path $pdfAbsPath $tempPath
}

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tempPath) -or (Get-Item $tempPath).Length -eq 0) {
    Remove-Item $tempPath -ErrorAction SilentlyContinue
    Write-Error "compress_pdf: compression failed, original left intact"
    exit 1
}

$newSize = (Get-Item $tempPath).Length
if ($newSize -ge $origSize) {
    Remove-Item $tempPath -ErrorAction SilentlyContinue
    Write-Output "compress_pdf: compressed output ($newSize bytes) is not smaller than the original ($origSize bytes); keeping the original."
    exit 0
}

Move-Item -Path $tempPath -Destination $pdfAbsPath -Force
Write-Output "Successfully compressed $pdfAbsPath ($origSize -> $newSize bytes)"
