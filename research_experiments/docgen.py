"""Helpers that fill the VESIT Research Methodology & IPR lab templates (python-docx)."""
import copy
import re
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

DL = Path(r"C:\Users\Aditya\Downloads")
TEMPLATES = {
    1: DL / "Experiment 1_Template_Research_Problem_and_Gap_Analysis.docx",
    2: DL / "Experiment 2_Template_Research_Planning_and_Methodology_Design.docx",
    3: DL / "Experiment_3_Template_Dataset_Experimental_Setup_Preparation.docx",
    4: DL / "Experiment_4_Implementation and Experimental Validation.docx",
    5: DL / "Experiment_5_Data Analysis and Visualization.docx",
}
CONTENT_DXA = 10224  # 7.1 in usable width in the templates
_BOLD = re.compile(r"(\*\*.+?\*\*|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))")


def _runs(par, text, size=None, bold=None, italic=None, color=None, font=None):
    """Add text with **bold** and *italic* inline markup."""
    for part in _BOLD.split(text):
        if not part:
            continue
        b = part.startswith("**") and part.endswith("**") and len(part) > 4
        it = not b and part.startswith("*") and part.endswith("*") and len(part) > 2
        r = par.add_run(part[2:-2] if b else part[1:-1] if it else part)
        r.bold = True if b else bold
        if italic or it:
            r.italic = True
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
        if font:
            r.font.name = font
            r._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    return par


class LabDoc:
    def __init__(self, exp_no: int, title: str, template_no: int = None, heading="h1", body_size=11):
        self.d = docx.Document(TEMPLATES[template_no or exp_no])
        self.heading_mode = heading
        self.body_size = body_size
        body = self.d.element.body
        kids = list(body.iterchildren())
        first_tbl = next(i for i, c in enumerate(kids) if c.tag == qn("w:tbl"))
        self._tblpr = copy.deepcopy(kids[first_tbl].find(qn("w:tblPr")))
        for c in kids[first_tbl + 1:]:
            if c.tag != qn("w:sectPr"):
                body.remove(c)
        # Title block: "EXPERIMENT n" + subtitle
        for p in self.d.paragraphs[:8]:
            t = p.text.strip()
            if t.upper().startswith("EXPERIMENT"):
                self._set_text(p, f"EXPERIMENT {exp_no}")
            elif p.runs and p.runs[0].font.size and p.runs[0].font.size.pt == 15:
                self._set_text(p, title)
        self.fig_no = 0
        self.tab_no = 0

    @staticmethod
    def _set_text(p, text):
        p.runs[0].text = text
        for r in p.runs[1:]:
            r.text = ""

    # ── text ──────────────────────────────────────────────────────────────────
    def h(self, text):
        if self.heading_mode == "bold14":
            p = self.d.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            _runs(p, text, size=14, bold=True)
            return p
        if self.heading_mode == "h2":
            p = self.d.add_paragraph(style="Heading 2")
            _runs(p, text, size=14)
            return p
        return self.d.add_paragraph(text, style="Heading 1")

    def h2(self, text):
        p = self.d.add_paragraph(style="Heading 2" if self.heading_mode != "h2" else "Heading 3")
        _runs(p, text, size=12)
        return p

    def p(self, text, size=None, bold=None, italic=None, align=None, space_after=4, color=None):
        par = self.d.add_paragraph()
        par.paragraph_format.space_after = Pt(space_after)
        _runs(par, text, size=size or self.body_size, bold=bold, italic=italic, color=color)
        if align == "center":
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == "justify":
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        return par

    def _bullet_num_id(self):
        if getattr(self, "_bullet_id", None):
            return self._bullet_id
        numbering = self.d.part.numbering_part.element
        abs_ids = [int(a.get(qn("w:abstractNumId"))) for a in numbering.findall(qn("w:abstractNum"))]
        num_ids = [int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num"))]
        aid, nid = max(abs_ids + [0]) + 1, max(num_ids + [0]) + 1
        absn = OxmlElement("w:abstractNum"); absn.set(qn("w:abstractNumId"), str(aid))
        lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
        for tag, val in (("w:start", "1"), ("w:numFmt", "bullet"), ("w:lvlText", "•"), ("w:lvlJc", "left")):
            e = OxmlElement(tag); e.set(qn("w:val"), val); lvl.append(e)
        ppr = OxmlElement("w:pPr"); ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "400"); ind.set(qn("w:hanging"), "260")
        ppr.append(ind); lvl.append(ppr)
        rpr = OxmlElement("w:rPr"); rf = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            rf.set(qn(a), "Symbol" if False else "Arial")
        rpr.append(rf); lvl.append(rpr)
        absn.append(lvl)
        first_num = numbering.find(qn("w:num"))
        if first_num is not None:
            first_num.addprevious(absn)
        else:
            numbering.append(absn)
        num = OxmlElement("w:num"); num.set(qn("w:numId"), str(nid))
        an = OxmlElement("w:abstractNumId"); an.set(qn("w:val"), str(aid)); num.append(an)
        numbering.append(num)
        self._bullet_id = nid
        return nid

    def bullets(self, items, size=None):
        nid = self._bullet_num_id()
        for it in items:
            par = self.d.add_paragraph()
            ppr = par._p.get_or_add_pPr()
            numpr = OxmlElement("w:numPr")
            il = OxmlElement("w:ilvl"); il.set(qn("w:val"), "0")
            ni = OxmlElement("w:numId"); ni.set(qn("w:val"), str(nid))
            numpr.append(il); numpr.append(ni); ppr.insert(0, numpr)  # numPr precedes spacing in CT_PPr
            par.paragraph_format.space_after = Pt(2)
            _runs(par, it, size=size or self.body_size)

    def numbered(self, items, size=None, start=1):
        for i, it in enumerate(items, start):
            par = self.d.add_paragraph()
            par.paragraph_format.left_indent = Inches(0.3)
            par.paragraph_format.first_line_indent = Inches(-0.3)
            par.paragraph_format.space_after = Pt(2)
            _runs(par, f"{i}.\t" if False else f"{i}. ", size=size or self.body_size)
            _runs(par, it, size=size or self.body_size)

    def kv(self, pairs, size=None):
        """Lines like 'Label: value' with bold label (template 4 style)."""
        for k, v in pairs:
            par = self.d.add_paragraph()
            par.paragraph_format.space_after = Pt(2)
            _runs(par, f"**{k}:** {v}", size=size or self.body_size)

    def caption(self, text, kind="Figure"):
        if kind == "Figure":
            self.fig_no += 1
            label = f"Figure {self.fig_no}: {text}"
        else:
            self.tab_no += 1
            label = f"Table {self.tab_no}: {text}"
        par = self.d.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_after = Pt(8)
        _runs(par, label, size=10, italic=(kind == "Figure"), bold=(kind == "Table"))
        return par

    def fig(self, path, caption, width=6.6):
        par = self.d.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(path), width=Inches(width))
        self.caption(caption, "Figure")

    def page_break(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ── tables ────────────────────────────────────────────────────────────────
    def table(self, rows, widths=None, header=True, size=9.5, caption=None, header_fill="F2F2F2", bold_first_col=False):
        if caption:
            self.caption(caption, "Table").paragraph_format.keep_with_next = True
        ncol = len(rows[0])
        widths = widths or [1] * ncol
        total = sum(widths)
        dxa = [int(CONTENT_DXA * w / total) for w in widths]
        dxa[-1] = CONTENT_DXA - sum(dxa[:-1])
        t = self.d.add_table(rows=len(rows), cols=ncol)
        tbl = t._tbl
        old = tbl.find(qn("w:tblPr"))
        new = copy.deepcopy(self._tblpr)
        new.find(qn("w:tblW")).set(qn("w:w"), str(CONTENT_DXA))
        new.find(qn("w:tblW")).set(qn("w:type"), "dxa")
        tbl.replace(old, new)
        grid = tbl.find(qn("w:tblGrid"))
        for gc, w in zip(grid.findall(qn("w:gridCol")), dxa):
            gc.set(qn("w:w"), str(w))
        for ri, row in enumerate(rows):
            if ri == 0 and header:
                trpr = t.rows[0]._tr.get_or_add_trPr()
                th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trpr.append(th)
            for ci, val in enumerate(row):
                cell = t.cell(ri, ci)
                cell.width = docx.shared.Twips(dxa[ci])
                tcpr = cell._tc.get_or_add_tcPr()
                tcw = tcpr.find(qn("w:tcW"))
                if tcw is None:
                    tcw = OxmlElement("w:tcW"); tcpr.append(tcw)
                tcw.set(qn("w:w"), str(dxa[ci])); tcw.set(qn("w:type"), "dxa")
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if ri == 0 and header and header_fill:
                    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), header_fill)
                    tcpr.append(shd)
                lines = str(val).split("\n")
                par = cell.paragraphs[0]
                for li, line in enumerate(lines):
                    if li:
                        par = cell.add_paragraph()
                    par.paragraph_format.space_after = Pt(1)
                    par.paragraph_format.space_before = Pt(1)
                    bold = (ri == 0 and header) or (bold_first_col and ci == 0)
                    _runs(par, line, size=size, bold=bold or None)
        self.d.add_paragraph().paragraph_format.space_after = Pt(2)
        return t

    # ── two-column section (IEEE paper) ───────────────────────────────────────
    def section(self, cols=1, space_in=0.25):
        sec = self.d.add_section(WD_SECTION.CONTINUOUS)
        sp = sec._sectPr
        c = sp.find(qn("w:cols"))
        if c is None:
            c = OxmlElement("w:cols"); sp.append(c)
        c.set(qn("w:num"), str(cols)); c.set(qn("w:space"), str(int(space_in * 1440)))
        return sec

    def save(self, path):
        self.d.core_properties.title = path.stem
        self.d.core_properties.author = "Court Vision AI project group"
        self.d.save(str(path))
