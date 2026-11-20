"""Helpers that fill the VESIT capstone blackbook template in place (python-docx + raw OOXML)."""
import copy
import re

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Twips

BODY_FONT = "Times New Roman"
HEAD_FONT = "Georgia"
TEXT_DXA = 9359  # A4 11910 − 1417 − 1134
_INLINE = re.compile(r"(\*\*.+?\*\*|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*])|`[^`]+`)")


def _font(run, name=BODY_FONT, size=12, bold=None, italic=None, color=None):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


# ── IEEE citations: write [@key] or [@a,@b] in text; numbered in order of first appearance ──
CITE_ORDER: list[str] = []
_CITE = re.compile(r"\[(@[\w-]+(?:\s*,\s*@[\w-]+)*)\]")


def cite_number(key):
    if key not in CITE_ORDER:
        CITE_ORDER.append(key)
    return CITE_ORDER.index(key) + 1


def resolve_cites(text):
    def rep(m):
        keys = [k.strip()[1:] for k in m.group(1).split(",")]
        return ", ".join(f"[{cite_number(k)}]" for k in keys)
    return _CITE.sub(rep, text)


def add_runs(par, text, size=12, font=BODY_FONT, bold=None, italic=None, color=None):
    text = resolve_cites(text)
    for part in _INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = par.add_run(part[2:-2]); _font(r, font, size, True if bold is None else bold, italic, color)
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1]); _font(r, "Consolas", size - 1.5, bold, italic, color)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1]); _font(r, font, size, bold, True, color)
        else:
            r = par.add_run(part); _font(r, font, size, bold, italic, color)
    return par


def set_text(p, text):
    """Replace a template paragraph's text, keeping the first run's formatting."""
    runs = p.findall(qn("w:r")) if not hasattr(p, "runs") else None
    par_runs = p.runs if hasattr(p, "runs") else []
    if par_runs:
        par_runs[0].text = text
        for r in par_runs[1:]:
            r.text = ""


def replace_in_element(el, old, new):
    """Replace text across <w:t> nodes of an element (text boxes included)."""
    for t in el.iter(qn("w:t")):
        if t.text and old in t.text:
            t.text = t.text.replace(old, new)


def make_style(document, name, base="Normal", font=HEAD_FONT, size=12, bold=False, italic=False, align=None,
               before=0, after=6, outline=None, keep_next=False):
    from docx.enum.style import WD_STYLE_TYPE
    try:
        return document.styles[name]
    except KeyError:
        pass
    st = document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    st.base_style = document.styles[base]
    st.font.name = font; st.font.size = Pt(size); st.font.bold = bold; st.font.italic = italic
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), font)
    pf = st.paragraph_format
    pf.space_before = Pt(before); pf.space_after = Pt(after); pf.keep_with_next = keep_next
    if align == "center":
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if outline is not None:
        ppr = st.element.get_or_add_pPr()
        ol = OxmlElement("w:outlineLvl"); ol.set(qn("w:val"), str(outline)); ppr.append(ol)
    return st


def field_paragraph(document, instr, placeholder="Right-click → Update Field to refresh."):
    """A paragraph holding a complex field (TOC etc.); Word fills it on update."""
    p = document.add_paragraph()
    def r(child):
        run = OxmlElement("w:r"); run.append(child); p._p.append(run)
    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin"); b.set(qn("w:dirty"), "true"); r(b)
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "; r(it)
    s = OxmlElement("w:fldChar"); s.set(qn("w:fldCharType"), "separate"); r(s)
    t = OxmlElement("w:t"); t.text = placeholder; r(t)
    e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end"); r(e)
    return p


def simple_field_run(par, instr, size=11):
    fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), instr)
    run = OxmlElement("w:r"); t = OxmlElement("w:t"); t.text = "1"; run.append(t); fld.append(run)
    par._p.append(fld)


class Builder:
    def __init__(self, document):
        self.d = document
        self.fig_no = {}
        self.tab_no = {}
        self.chapter = 0
        self._bullet = None
        self.chap_style = make_style(document, "BB Chapter", font=HEAD_FONT, size=24, bold=True, before=0, after=18, outline=0)
        self.fig_style = make_style(document, "BB Figure Caption", font=BODY_FONT, size=11, italic=False, align="center", before=4, after=12)
        self.tab_style = make_style(document, "BB Table Caption", font=BODY_FONT, size=11, bold=True, align="center", before=8, after=4, keep_next=True)
        self.code_style = make_style(document, "BB Code", font="Consolas", size=8.5, before=0, after=0)

    # ── structure ──────────────────────────────────────────────────────────────
    def chapter_divider(self, n, title):
        first = True
        for _ in range(11):
            p = self.d.add_paragraph()
            if first:
                p.paragraph_format.page_break_before = True
                first = False
        for line in (f"CHAPTER: {n}", title.upper()):
            p = self.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(18)
            add_runs(p, line, size=17, font=HEAD_FONT, bold=True)

    def chapter_title(self, n, title):
        self.chapter = n
        p = self.d.add_paragraph(style=self.chap_style)
        p.paragraph_format.page_break_before = True
        r = p.add_run(f"Chapter {n} "); _font(r, HEAD_FONT, 24.5, True)   # trailing space keeps "Chapter 1 Introduction" in the TOC
        r.add_break()
        r2 = p.add_run(title); _font(r2, HEAD_FONT, 24, True)

    def unnumbered_title(self, title):
        p = self.d.add_paragraph(style=self.chap_style)
        p.paragraph_format.page_break_before = True
        r = p.add_run(title); _font(r, HEAD_FONT, 24, True)

    def h1(self, text):
        p = self.d.add_paragraph(style="Heading 1")
        p.paragraph_format.left_indent = Twips(0)
        p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text); _font(r, HEAD_FONT, 16, True)
        return p

    def h2(self, text):
        p = self.d.add_paragraph(style="Heading 2")
        p.paragraph_format.left_indent = Twips(0)
        p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text); _font(r, HEAD_FONT, 13.5, True)
        return p

    def h3(self, text):
        p = self.d.add_paragraph()
        p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        add_runs(p, text, size=12, bold=True)
        return p

    # ── text ───────────────────────────────────────────────────────────────────
    def p(self, text, align="justify", size=12, italic=None, after=6, indent_first=False):
        par = self.d.add_paragraph()
        pf = par.paragraph_format
        pf.space_after = Pt(after); pf.line_spacing = 1.5
        if align == "justify":
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif align == "center":
            par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if indent_first:
            pf.first_line_indent = Inches(0.4)
        add_runs(par, text, size=size, italic=italic)
        return par

    def _bullet_id(self):
        if self._bullet:
            return self._bullet
        numbering = self.d.part.numbering_part.element
        aid = max([int(a.get(qn("w:abstractNumId"))) for a in numbering.findall(qn("w:abstractNum"))] + [0]) + 1
        nid = max([int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num"))] + [0]) + 1
        absn = OxmlElement("w:abstractNum"); absn.set(qn("w:abstractNumId"), str(aid))
        lvl = OxmlElement("w:lvl"); lvl.set(qn("w:ilvl"), "0")
        for tag, val in (("w:start", "1"), ("w:numFmt", "bullet"), ("w:lvlText", "•"), ("w:lvlJc", "left")):
            e = OxmlElement(tag); e.set(qn("w:val"), val); lvl.append(e)
        ppr = OxmlElement("w:pPr"); ind = OxmlElement("w:ind"); ind.set(qn("w:left"), "540"); ind.set(qn("w:hanging"), "300")
        ppr.append(ind); lvl.append(ppr)
        rpr = OxmlElement("w:rPr"); rf = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            rf.set(qn(a), "Arial")
        rpr.append(rf); lvl.append(rpr); absn.append(lvl)
        first = numbering.find(qn("w:num"))
        (first.addprevious(absn) if first is not None else numbering.append(absn))
        num = OxmlElement("w:num"); num.set(qn("w:numId"), str(nid))
        an = OxmlElement("w:abstractNumId"); an.set(qn("w:val"), str(aid)); num.append(an); numbering.append(num)
        self._bullet = nid
        return nid

    def bullets(self, items, size=12):
        nid = self._bullet_id()
        for it in items:
            par = self.d.add_paragraph()
            ppr = par._p.get_or_add_pPr()
            numpr = OxmlElement("w:numPr")
            il = OxmlElement("w:ilvl"); il.set(qn("w:val"), "0")
            ni = OxmlElement("w:numId"); ni.set(qn("w:val"), str(nid))
            numpr.append(il); numpr.append(ni); ppr.insert(0, numpr)
            par.paragraph_format.space_after = Pt(3); par.paragraph_format.line_spacing = 1.3
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_runs(par, it, size=size)

    def numbered(self, items, size=12):
        for i, it in enumerate(items, 1):
            par = self.d.add_paragraph()
            pf = par.paragraph_format
            pf.left_indent = Inches(0.4); pf.first_line_indent = Inches(-0.3)
            pf.space_after = Pt(3); pf.line_spacing = 1.3
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_runs(par, f"{i}.  {it}", size=size)

    def code(self, text):
        lines = text.strip("\n").split("\n")
        for k, line in enumerate(lines):
            par = self.d.add_paragraph(style=self.code_style)
            ppr = par._p.get_or_add_pPr()
            shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "F2F2F2")
            ppr.append(shd)
            par.paragraph_format.left_indent = Inches(0.15)
            if k == len(lines) - 1:
                par.paragraph_format.space_after = Pt(8)
            r = par.add_run(line if line else " "); _font(r, "Consolas", 8)

    # ── figures & tables ───────────────────────────────────────────────────────
    def figure(self, path, caption, width=6.0):
        par = self.d.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True; par.paragraph_format.space_before = Pt(6)
        par.add_run().add_picture(str(path), width=Inches(width))
        n = self.fig_no.get(self.chapter, 0) + 1; self.fig_no[self.chapter] = n
        cap = self.d.add_paragraph(style=self.fig_style)
        r = cap.add_run(f"Figure {self.chapter}.{n}: {caption}"); _font(r, BODY_FONT, 11)
        return f"{self.chapter}.{n}"

    def next_table_label(self):
        n = self.tab_no.get(self.chapter, 0) + 1
        return f"{self.chapter}.{n}"

    def table(self, rows, widths, caption=None, size=10, header=True, bold_first_col=False, fill="D9D9D9"):
        if caption:
            n = self.tab_no.get(self.chapter, 0) + 1; self.tab_no[self.chapter] = n
            cap = self.d.add_paragraph(style=self.tab_style)
            r = cap.add_run(f"Table {self.chapter}.{n}: {caption}"); _font(r, BODY_FONT, 11, True)
        ncol = len(rows[0]); tot = sum(widths)
        dxa = [int(TEXT_DXA * w / tot) for w in widths]; dxa[-1] = TEXT_DXA - sum(dxa[:-1])
        t = self.d.add_table(rows=len(rows), cols=ncol)
        tbl = t._tbl
        tblPr = tbl.tblPr
        for tag in ("w:tblStyle",):
            e = tblPr.find(qn(tag))
            if e is not None:
                tblPr.remove(e)
        tw = tblPr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW"); tblPr.append(tw)
        tw.set(qn("w:w"), str(TEXT_DXA)); tw.set(qn("w:type"), "dxa")
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
            borders.append(e)
        tblPr.append(borders)
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        jc = OxmlElement("w:jc"); jc.set(qn("w:val"), "center"); tblPr.append(jc)
        for gc, w in zip(tbl.tblGrid.findall(qn("w:gridCol")), dxa):
            gc.set(qn("w:w"), str(w))
        for ri, row in enumerate(rows):
            if ri == 0 and header:
                trpr = t.rows[0]._tr.get_or_add_trPr()
                th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trpr.append(th)
            for ci, val in enumerate(row):
                cell = t.cell(ri, ci)
                cell.width = Twips(dxa[ci])
                tcpr = cell._tc.get_or_add_tcPr()
                if ri == 0 and header and fill:
                    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill)
                    tcpr.append(shd)
                lines = str(val).split("\n")
                par = cell.paragraphs[0]
                for li, line in enumerate(lines):
                    if li:
                        par = cell.add_paragraph()
                    par.paragraph_format.space_after = Pt(1); par.paragraph_format.space_before = Pt(1)
                    b = True if (ri == 0 and header) or (bold_first_col and ci == 0) else None
                    add_runs(par, line, size=size, bold=b)
        gap = self.d.add_paragraph(); gap.paragraph_format.space_after = Pt(4)
        return t

    def references_placeholder(self):
        self._ref_anchor = self.d.add_paragraph()

    def fill_references(self, refs: dict, size=11):
        """Insert the reference list at the placeholder, numbered in order of first citation."""
        order = CITE_ORDER + [k for k in refs if k not in CITE_ORDER]
        anchor = self._ref_anchor._p
        for i, key in enumerate(order, 1):
            par = self.d.add_paragraph()
            pf = par.paragraph_format
            pf.left_indent = Inches(0.45); pf.first_line_indent = Inches(-0.45)
            pf.space_after = Pt(5); pf.line_spacing = 1.15
            par.alignment = WD_ALIGN_PARAGRAPH.LEFT
            par.paragraph_format.tab_stops.add_tab_stop(Inches(0.45))
            add_runs(par, f"[{i}]\t{refs[key]}", size=size)
            anchor.addnext(par._p)
            anchor = par._p
        self._ref_anchor._p.getparent().remove(self._ref_anchor._p)
        return order

    def references(self, refs, size=11):
        for i, ref in enumerate(refs, 1):
            par = self.d.add_paragraph()
            pf = par.paragraph_format
            pf.left_indent = Inches(0.45); pf.first_line_indent = Inches(-0.45)
            pf.space_after = Pt(5); pf.line_spacing = 1.15
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_runs(par, f"[{i}]\t{ref}", size=size)

    def page_break(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
