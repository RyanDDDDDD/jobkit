param (
    [Parameter(Mandatory=$true)]
    [string]$PdfPath
)

$ps2pdf = "$env:APPDATA\TinyTeX\bin\windows\ps2pdf.exe"

if (-not (Test-Path $PdfPath)) {
    Write-Error "File not found: $PdfPath"
    exit 1
}

if (-not (Test-Path $ps2pdf)) {
    Write-Error "ps2pdf.exe not found at: $ps2pdf"
    exit 1
}

$pdfAbsPath = Resolve-Path $PdfPath
$tempPath = [System.IO.Path]::ChangeExtension($pdfAbsPath, "temp.pdf")

# Run compression
& $ps2pdf $pdfAbsPath $tempPath

if (Test-Path $tempPath) {
    Move-Item -Path $tempPath -Destination $pdfAbsPath -Force
    Write-Output "Successfully compressed $pdfAbsPath"
} else {
    Write-Error "Compression failed to generate temp file."
    exit 1
}
