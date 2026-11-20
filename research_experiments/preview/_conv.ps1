
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  foreach ($f in $args) {
    $doc = $word.Documents.Open($f, $false, $true)
    $pdf = Join-Path "C:\Users\Aditya\OneDrive\Desktop\New folder\court-vision-ai\research_experiments\preview" ([IO.Path]::GetFileNameWithoutExtension($f) + ".pdf")
    $doc.ExportAsFixedFormat($pdf, 17)
    $doc.Close([ref]0)
    Write-Output "pdf $pdf"
  }
} finally { $word.Quit() }
