param(
    [string]$DocumentPath = "$PSScriptRoot/../output/report/Bao_cao_ECC_Chu_ky_so.docx",
    [string]$PdfPath = "$PSScriptRoot/../output/report/Bao_cao_ECC_Chu_ky_so.pdf"
)
$ErrorActionPreference = 'Stop'
$resolvedDoc = (Resolve-Path -LiteralPath $DocumentPath).Path
$resolvedPdf = [System.IO.Path]::GetFullPath($PdfPath)
$wordInstance = $null
$document = $null
try {
    $wordInstance = New-Object -ComObject Word.Application
    $wordInstance.Visible = $false
    $wordInstance.DisplayAlerts = 0
    $document = $wordInstance.Documents.Open($resolvedDoc, $false, $false)
    $document.Fields.Update() | Out-Null
    foreach ($toc in $document.TablesOfContents) { $toc.Update() }
    $document.Repaginate()
    $document.Save()
    $document.ExportAsFixedFormat($resolvedPdf, 17)
    Write-Output ('Exported PDF; pages: ' + $document.ComputeStatistics(2))
} finally {
    if ($null -ne $document) { $document.Close(0) }
    if ($null -ne $wordInstance) { $wordInstance.Quit() }
}
