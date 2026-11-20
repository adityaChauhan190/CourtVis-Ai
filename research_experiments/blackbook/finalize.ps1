param([string]$In, [string]$OutDocx, [string]$OutPdf)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open($In, $false, $false)
  $doc.Repaginate()
  foreach ($t in $doc.TablesOfContents) { $t.Update() }
  $doc.Fields.Update() | Out-Null
  foreach ($t in $doc.TablesOfContents) { $t.Update() }   # second pass: page numbers settle after the lists grow
  foreach ($s in $doc.Sections) { foreach ($f in $s.Footers) { $f.Range.Fields.Update() | Out-Null } }
  $doc.SaveAs2($OutDocx, 16)
  $doc.ExportAsFixedFormat($OutPdf, 17)
  Write-Output ("pages: " + $doc.ComputeStatistics(2))
  $doc.Close(0)
} finally { $word.Quit() }
