"""Build the illustrated five-chapter reading edition from the manuscript."""
from pathlib import Path
import json,re
from docx import Document
from docx.shared import Mm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/current/Почему_так_первые_пять_глав_v4.docx'
SOURCE=ROOT/'manuscript/source.md'
doc=Document();sec=doc.sections[0]
sec.page_width=Mm(180);sec.page_height=Mm(250)
sec.top_margin=Mm(18);sec.bottom_margin=Mm(18);sec.left_margin=Mm(20);sec.right_margin=Mm(20)
sec.header_distance=Mm(8);sec.footer_distance=Mm(8)
sec.different_first_page_header_footer=True
styles=doc.styles
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption','Header','Footer']:
    st=styles[name];st.font.name='PT Serif' if name=='Normal' else 'IBM Plex Sans';st.font.color.rgb=RGBColor(0,0,0)
    rf=st._element.get_or_add_rPr().rFonts
    for key in list(rf.attrib):
        if 'Theme' in key:del rf.attrib[key]
    for key in ['ascii','hAnsi','eastAsia','cs']:rf.set(qn('w:'+key),st.font.name)
    st.paragraph_format.space_after=Pt(8);st.paragraph_format.widow_control=True
    st._element.get_or_add_rPr().append(OxmlElement('w:lang'));st._element.rPr[-1].set(qn('w:val'),'ru-RU')
styles['Normal'].font.size=Pt(11.5);styles['Normal'].paragraph_format.line_spacing=Pt(15)
styles['Normal'].paragraph_format.space_after=Pt(5)
styles['Title'].font.size=Pt(56);styles['Title'].font.bold=True;styles['Title'].paragraph_format.line_spacing=Pt(57)
styles['Heading 1'].font.size=Pt(30);styles['Heading 1'].font.bold=True;styles['Heading 1'].paragraph_format.space_after=Pt(18)
styles['Heading 2'].font.size=Pt(19);styles['Heading 2'].font.bold=True;styles['Heading 2'].paragraph_format.space_before=Pt(16);styles['Heading 2'].paragraph_format.space_after=Pt(10)
styles['Heading 1'].paragraph_format.line_spacing=1.08
styles['Heading 2'].paragraph_format.line_spacing=1.15
styles['Heading 3'].paragraph_format.line_spacing=1.1
styles['Subtitle'].paragraph_format.line_spacing=1.2
styles['Heading 3'].font.size=Pt(10);styles['Heading 3'].font.bold=False
styles['Caption'].font.size=Pt(8);styles['Caption'].font.italic=False;styles['Caption'].paragraph_format.line_spacing=Pt(10.5);styles['Caption'].paragraph_format.space_after=Pt(12)
styles['Header'].font.size=Pt(7.5);styles['Footer'].font.size=Pt(8)
head=sec.header.paragraphs[0];head.text='СЕРГЕЙ ОТЧЕСКОВ  /  ПОЧЕМУ ТАК'
foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');foot._p.append(fld)
doc.core_properties.title='Почему так';doc.core_properties.author='Сергей Отческов'
doc.core_properties.subject='Предисловие и первые пять глав. Рабочая редакция v4.'

p=doc.add_paragraph('Сергей Отческов','Subtitle');p.paragraph_format.space_after=Pt(75)
p=doc.add_paragraph('Почему\nтак','Title');p.paragraph_format.space_after=Pt(30)
doc.add_paragraph('О вещах, на которые\nмы смотрим каждый день','Subtitle')
p=doc.add_paragraph('Предисловие и первые пять глав\nРабочая редакция  •  1 ноября 2026','Caption');p.paragraph_format.space_before=Pt(90)
doc.add_page_break()
doc.add_paragraph('Содержание','Heading 1')
toc_file=ROOT/'exports/current/toc-v4.json'
toc=json.loads(toc_file.read_text()) if toc_file.exists() else {}
titles=['Предисловие','На двери все написано','Красиво и что дальше','Что осталось за кадром','Здесь слишком много воздуха','А потом человек нажал']
for i,title in enumerate(titles):
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(18)
    run=p.add_run(('0'+str(i)+'  ' if i else '')+title);run.font.name='IBM Plex Sans';run.font.size=Pt(14)
    if title in toc:p.add_run('   '+str(toc[title])).font.size=Pt(10)
p=doc.add_paragraph('Учебные примеры и созданные для книги сцены позволяют сравнивать решения. Они не являются отчетами о реальных событиях или результатах бизнеса.','Caption');p.paragraph_format.space_before=Pt(42)

blocks=SOURCE.read_text().split('\n\n');pending_chapter=False;figure_no=0;manifest=[]
for block in blocks:
    block=block.strip()
    if not block or block.startswith('# Почему') or block=='Сергей Отческов':continue
    # Headings may be consecutive in one block.
    if block.startswith('## Глава'):
        lines=block.splitlines()
        chapter=lines[0].removeprefix('## ')
        p=doc.add_paragraph(chapter.upper(),'Heading 3');p.paragraph_format.page_break_before=True;p.paragraph_format.space_after=Pt(10)
        title=lines[1].removeprefix('### ') if len(lines)>1 else ''
        if title:doc.add_paragraph(title,'Heading 1')
        continue
    if block=='## Предисловие':
        p=doc.add_paragraph('Предисловие','Heading 1');p.paragraph_format.page_break_before=True;continue
    if block.startswith('### '):doc.add_paragraph(block[4:],'Heading 2');continue
    match=re.fullmatch(r'\[\[FIGURE:([^|]+)\|(.+)\]\]',block,re.S)
    if match:
        filename,caption=match.groups();figure_no+=1
        path=ROOT/'assets/figures'/filename
        w,h=Image.open(path).size
        width=Mm(94) if h>w else Mm(140)
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing=1
        p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(7);p.paragraph_format.space_after=Pt(5)
        run=p.add_run();pic=run.add_picture(str(path),width=width)
        pic._inline.docPr.set('descr',caption);pic._inline.docPr.set('title',f'Иллюстрация {figure_no}')
        cp=doc.add_paragraph(f'{figure_no:02d}  {caption}','Caption');cp.paragraph_format.keep_together=True
        manifest.append(dict(index=figure_no,file=filename,caption=caption))
        continue
    doc.add_paragraph(block,'Normal')

p=doc.add_paragraph('О визуальных материалах','Heading 2');p.paragraph_format.page_break_before=True
doc.add_paragraph('Четыре предметные сцены созданы с помощью imagegen специально для этой редакции: дверь, шоколадные обертки, место за столом и лист меню. Они используются как иллюстрации к учебным ситуациям. Десять графических разборов выполнены отдельно; текст и элементы доступны для редактирования в Figma.','Normal')
doc.add_paragraph('Для дальнейшего чтения','Heading 2')
for s in ['Эллен Луптон. Thinking with Type. О шрифте, интервалах и организации текста.','Дон Норман. The Design of Everyday Things. О том, как люди разбираются с привычными вещами.']:
    doc.add_paragraph(s,'Normal')
doc.add_paragraph('Текст и концепция Сергея Отческова. Редакция v4 подготовлена для авторского чтения и оценки визуальной системы. Полное оглавление книги и параметры печатного выпуска еще не утверждены.','Caption')
for tree in [doc._element,doc.styles._element]:
    for b in tree.xpath('.//w:pBdr'):b.getparent().remove(b)
OUT.parent.mkdir(parents=True,exist_ok=True);doc.save(OUT)
(OUT.parent/'figures-v4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(OUT)
