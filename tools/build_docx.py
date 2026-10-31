from pathlib import Path
import re
import json
import argparse
from datetime import datetime, timezone
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'manuscript'
FIGURES = ROOT / 'assets' / 'figures'
parser = argparse.ArgumentParser(description='Собрать рабочую рукопись в Word')
parser.add_argument('--output', type=Path, default=ROOT / 'exports' / 'current' / 'Почему_так_главы_1_2.docx')
args = parser.parse_args()
OUT = args.output

def font_props(style, name, size, bold=False):
    style.font.name = name
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn('w:rFonts'))
    if fonts is None:
        fonts = OxmlElement('w:rFonts')
        rpr.insert(0, fonts)
    for key in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        fonts.set(qn('w:' + key), name)
    for attr in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        fonts.attrib.pop(qn('w:' + attr), None)
    lang = rpr.find(qn('w:lang'))
    if lang is None:
        lang = OxmlElement('w:lang')
        rpr.append(lang)
    lang.set(qn('w:val'), 'ru-RU')

def hyperlink(paragraph, label, url):
    rel_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement('w:hyperlink')
    h.set(qn('r:id'), rel_id)
    run = OxmlElement('w:r')
    props = OxmlElement('w:rPr')
    color = OxmlElement('w:color'); color.set(qn('w:val'), '000000'); props.append(color)
    u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); props.append(u)
    run.append(props)
    t = OxmlElement('w:t'); t.text = label; run.append(t)
    h.append(run); paragraph._p.append(h)

doc = Document()
sec = doc.sections[0]
sec.page_width = Inches(8.5)
sec.page_height = Inches(11)
sec.top_margin = Inches(.8)
sec.bottom_margin = Inches(.8)
sec.left_margin = Inches(1.0)
sec.right_margin = Inches(1.0)
sec.header_distance = Inches(.3)
sec.footer_distance = Inches(.35)

styles = doc.styles
font_props(styles['Normal'], 'Georgia', 11.5)
styles['Normal'].paragraph_format.line_spacing = 1.24
styles['Normal'].paragraph_format.space_after = Pt(7)
styles['Normal'].paragraph_format.widow_control = True
styles['Normal'].paragraph_format.keep_together = False
font_props(styles['Title'], 'Arial', 34, True)
styles['Title'].paragraph_format.space_before = Pt(0)
styles['Title'].paragraph_format.space_after = Pt(10)
font_props(styles['Subtitle'], 'Arial', 11)
styles['Subtitle'].paragraph_format.space_after = Pt(4)
font_props(styles['Heading 1'], 'Arial', 24, True)
styles['Heading 1'].paragraph_format.space_before = Pt(0)
styles['Heading 1'].paragraph_format.space_after = Pt(15)
styles['Heading 1'].paragraph_format.keep_with_next = True
font_props(styles['Heading 2'], 'Arial', 14, True)
styles['Heading 2'].paragraph_format.space_before = Pt(16)
styles['Heading 2'].paragraph_format.space_after = Pt(8)
styles['Heading 2'].paragraph_format.keep_with_next = True
font_props(styles['Caption'], 'Arial', 9.5)
styles['Caption'].paragraph_format.line_spacing = 1.13
styles['Caption'].paragraph_format.space_before = Pt(4)
styles['Caption'].paragraph_format.space_after = Pt(12)
styles['Caption'].paragraph_format.keep_together = True
styles['Caption'].font.italic = False

for name in ['Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Header', 'Footer']:
    styles[name].font.color.rgb = RGBColor(0, 0, 0)
    ppr = styles[name].element.find(qn('w:pPr'))
    if ppr is not None:
        for tag in ('w:pBdr', 'w:shd'):
            for e in ppr.findall(qn(tag)):
                ppr.remove(e)

footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = footer.add_run(); r.font.name = 'Arial'; r.font.size = Pt(9)
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE')
field_run = OxmlElement('w:r'); value=OxmlElement('w:t'); value.text='1'; field_run.append(value); field.append(field_run)
r._r.addnext(field)

props = doc.core_properties
props.title = 'Почему так'
props.subject = 'Предисловие и первые две главы книги о дизайне и повседневной визуальной среде'
props.author = 'Сергей Отческов'
props.last_modified_by = 'Редактор'
props.keywords = 'дизайн, визуальная коммуникация, типографика, композиция'
props.comments = ''
props.language = 'ru-RU'
props.modified = datetime.now(timezone.utc)

manifest = json.loads((FIGURES / 'manifest.json').read_text())
if isinstance(manifest, dict):
    data = manifest.get('figures', manifest.get('files', []))
else:
    data = manifest
alts = {}
for item in data:
    if isinstance(item, dict):
        path = item.get('path', item.get('file', item.get('filename','')))
        alts[Path(path).name] = item.get('alt', item.get('alt_text',''))

comments = {}

source = (WORK/'source.md').read_text()
source = re.sub(r'(?m)^(#{1,4} [^\n]+)\n(?!\n)', r'\1\n\n', source)
chapter_num = 0
figure_count = 0
comment_count = 0

for block in source.strip().split('\n\n'):
    block = block.strip()
    if not block:
        continue
    if block.startswith('# '):
        p = doc.add_paragraph(block[2:], style='Title')
    elif block == 'Сергей Отческов':
        doc.add_paragraph(block, style='Subtitle')
        p = doc.add_paragraph('Предисловие и главы 1 и 2', style='Subtitle')
        p.paragraph_format.space_after = Pt(25)
    elif block == '## Предисловие':
        doc.add_paragraph('Предисловие', style='Heading 1')
    elif block.startswith('## Глава '):
        chapter_num = int(block.rsplit(' ',1)[1])
        p = doc.add_paragraph(block[3:], style='Subtitle')
        if chapter_num >= 1:
            p.paragraph_format.page_break_before = True
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
    elif block.startswith('### '):
        doc.add_paragraph(block[4:], style='Heading 1')
    elif block.startswith('#### '):
        doc.add_paragraph(block[5:], style='Heading 2')
    elif block.startswith('## '):
        p=doc.add_paragraph(block[3:], style='Heading 2')
        p.paragraph_format.space_before=Pt(24)
    elif block.startswith('[[FIGURE:'):
        match = re.fullmatch(r'\[\[FIGURE:([^|]+)\|(.+)\]\]', block, flags=re.S)
        if not match:
            raise ValueError(block)
        filename, caption = match.groups()
        figure_count += 1
        p = doc.add_paragraph()
        p.paragraph_format.space_before=Pt(5)
        p.paragraph_format.space_after=Pt(0)
        p.paragraph_format.keep_with_next=True
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        pic = p.add_run().add_picture(str(FIGURES/filename), width=Inches(6.4))
        pic._inline.docPr.set('descr', alts.get(filename) or caption)
        pic._inline.docPr.set('title', f'Иллюстрация {figure_count}')
        doc.add_paragraph(f'{figure_count}. {caption}', style='Caption')
    elif 'Страница издателя:' in block:
        desc, url = block.split('Страница издателя:',1)
        author, title, annotation = desc.strip().split('. ', 2)
        p=doc.add_paragraph(author + '. ')
        hyperlink(p, title, url.strip())
        p.add_run('. ' + annotation)
        p.paragraph_format.space_after=Pt(9)
        p.paragraph_format.keep_together=True
        for run in p.runs:
            run.font.size=Pt(10)
    else:
        p=doc.add_paragraph(block)
        for marker, comment in comments.items():
            if block.startswith(marker):
                doc.add_comment(p.runs, text=comment, author='Редактор', initials='Р')
                comment_count += 1

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(json.dumps({'output':str(OUT),'bytes':OUT.stat().st_size,'figures':figure_count,'comments':comment_count,'paragraphs':len(doc.paragraphs)},ensure_ascii=False))
