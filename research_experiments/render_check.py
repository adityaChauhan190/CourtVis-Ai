"""Convert built .docx files to PDF with MS Word (COM) and rasterise pages for visual QA."""
import subprocess
import sys
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
PREVIEW = HERE / "preview"
PREVIEW.mkdir(exist_ok=True)

PS = r'''
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  foreach ($f in $args) {
    $doc = $word.Documents.Open($f, $false, $true)
    $pdf = Join-Path "%s" ([IO.Path]::GetFileNameWithoutExtension($f) + ".pdf")
    $doc.ExportAsFixedFormat($pdf, 17)
    $doc.Close([ref]0)
    Write-Output "pdf $pdf"
  }
} finally { $word.Quit() }
''' % PREVIEW


def main(files):
    script = PREVIEW / "_conv.ps1"
    script.write_text(PS, encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *map(str, files)], check=True)
    for f in files:
        pdf = PREVIEW / (Path(f).stem + ".pdf")
        doc = fitz.open(pdf)
        print(f"{Path(f).name}: {len(doc)} pages")
        for i, page in enumerate(doc, 1):
            page.get_pixmap(dpi=70).save(PREVIEW / f"{Path(f).stem[:13]}_p{i:02d}.png")


if __name__ == "__main__":
    main([Path(a).resolve() for a in sys.argv[1:]])
