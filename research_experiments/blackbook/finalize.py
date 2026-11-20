"""Open the draft in Microsoft Word, update all fields (contents, lists, page numbers), save .docx and .pdf, render check sheets."""
from pathlib import Path

import fitz
import win32com.client
from PIL import Image

HERE = Path(__file__).resolve().parent
DRAFT, DOCX, PDF = HERE / "CourtVisionAI_Blackbook_draft.docx", HERE / "CourtVisionAI_Blackbook.docx", HERE / "CourtVisionAI_Blackbook.pdf"

word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
try:
    doc = word.Documents.Open(str(DRAFT), False, False)
    doc.Repaginate()
    for _ in range(2):                      # second pass: page numbers settle after the lists are filled
        for t in doc.TablesOfContents:
            t.Update()
        doc.Fields.Update()
    for s in doc.Sections:
        for f in s.Footers:
            f.Range.Fields.Update()
    doc.SaveAs2(str(DOCX), 16)
    doc.ExportAsFixedFormat(str(PDF), 17)
    print("pages:", doc.ComputeStatistics(2))
    doc.Close(0)
finally:
    try:
        word.Quit()
    except Exception:
        pass

pdf = fitz.open(str(PDF))
ims = []
for p in pdf:
    pix = p.get_pixmap(dpi=55)
    ims.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
w, h = ims[0].size
(HERE / "check").mkdir(exist_ok=True)
for s in range(0, len(ims), 8):
    sheet = Image.new("RGB", (w * 4, h * 2), "white")
    for i, im in enumerate(ims[s:s + 8]):
        sheet.paste(im, ((i % 4) * w, (i // 4) * h))
    sheet.save(HERE / "check" / f"sheet_{s // 8:02d}.png")
print("check sheets:", (len(ims) + 7) // 8)
