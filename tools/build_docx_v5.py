"""Render the authored v5 scene graph as editable Word text boxes and shapes."""
from pathlib import Path
import json,io
from lxml import etree
from docx import Document
from docx.shared import Mm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
import fitz
ROOT=Path(__file__).resolve().parents[1]; DATA=json.loads((ROOT/'exports/current/layout-v5.json').read_text())
D=Document();s=D.sections[0];s.page_width=Mm(190);s.page_height=Mm(250)
s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Mm(0)
s.header_distance=s.footer_distance=Mm(0)
D.core_properties.title='Почему так';D.core_properties.author='Сергей Отческов';D.core_properties.subject='Предисловие и первые пять глав'
styles=D.styles
for st in ['Normal','Title','Heading 1','Heading 2','Caption']:
 styles[st].font.name='PT Serif' if st=='Normal' else 'IBM Plex Sans'
 styles[st].font.color.rgb=RGBColor.from_string('222820')
 styles[st].paragraph_format.space_before=Pt(0);styles[st].paragraph_format.space_after=Pt(0)
 for e in list(styles[st]._element.xpath('.//w:pBdr')):e.getparent().remove(e)
V='urn:schemas-microsoft-com:vml';W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';O='urn:schemas-microsoft-com:office:office'
images={}
def shape(p,l,z):
 pict=OxmlElement('w:pict');p.add_run()._r.append(pict)
 sh=etree.SubElement(pict,'{'+V+'}rect');sh.set('id',l['id']);sh.set('style',f"position:absolute;margin-left:{l['x']:.5f}mm;margin-top:{l['y']:.5f}mm;width:{l['w']:.5f}mm;height:{l['h']:.5f}mm;mso-position-horizontal-relative:page;mso-position-vertical-relative:page;z-index:{z}")
 sh.set('stroked','f');sh.set('filled','t' if l['type']=='rect' else 'f')
 if l['type']=='rect':sh.set('fillcolor',l['color'])
 return sh
for page in DATA['pages']:
 p=D.add_paragraph();p.paragraph_format.line_spacing=Pt(1);p.paragraph_format.space_after=Pt(0);p.paragraph_format.page_break_before=page['number']>1
 shape(p,{'id':'bg'+str(page['number']),'type':'rect','x':0,'y':0,'w':190,'h':250,'color':page['background']},-251658240)
 for z,l in enumerate(page['layers'],1):
  box_layer = {**l, 'w': min(l['w']+1.5,190-l['x'])} if l['type']=='text' else l
  sh=shape(p,box_layer,z)
  if l['type']=='text':
   box=etree.SubElement(sh,'{'+V+'}textbox');box.set('inset','0,0,0,0');cont=etree.SubElement(box,'{'+W+'}txbxContent')
   el=OxmlElement('w:p');cont.append(el);pp=Paragraph(el,p._parent)
   pp.style='Title' if l['role']=='title' else 'Heading 1' if l['role']=='chapter' else 'Heading 2' if l['role']=='heading' else 'Caption' if l['role']=='caption' else 'Normal'
   fmt=pp.paragraph_format;fmt.space_before=fmt.space_after=Pt(0);fmt.line_spacing=Pt(l['leading']);fmt.keep_with_next=False;fmt.keep_together=False;fmt.widow_control=False
   if l.get('align')=='right':pp.alignment=2
   rr=pp.add_run(l['text']);role=l['font'];rr.font.name='PT Serif' if role in ['serif','italic'] else 'IBM Plex Sans';rr.font.size=Pt(l['size']);rr.bold=role=='bold';rr.italic=role=='italic';rr.font.color.rgb=RGBColor.from_string(l['color'].lstrip('#'))
   rf=rr._r.get_or_add_rPr().rFonts
   for k in ['ascii','hAnsi','eastAsia','cs']:rf.set(qn('w:'+k),rr.font.name)
   lang=OxmlElement('w:lang');lang.set(qn('w:val'),'ru-RU');rr._r.rPr.append(lang)
  elif l['type'] in ['photo','svg']:
   key=l.get('file',l.get('svg'))
   if key not in images:
    data=str(ROOT/'assets/figures'/l['file']) if l['type']=='photo' else io.BytesIO(fitz.open(stream=l['svg'].encode(),filetype='svg')[0].get_pixmap(matrix=fitz.Matrix(5,5),alpha=True).tobytes('png'))
    rid,img=D.part.get_or_add_image(data);images[key]=rid
   im=etree.SubElement(sh,'{'+V+'}imagedata');im.set(qn('r:id'),images[key]);im.set('{'+O+'}title',l.get('file','Схема'))
   if l.get('crop'):
    a,b,c,d=l['crop']
    for name,val in [('cropleft',a),('croptop',b),('cropright',1-c),('cropbottom',1-d)]:im.set(name,str(round(val*65536))+'f')
# Compatibility metadata helps preserve text box geometry across Word versions.
settings=D.settings.element
compat=settings.find(qn('w:compat'))
if compat is None:compat=OxmlElement('w:compat');settings.append(compat)
cs=OxmlElement('w:compatSetting');cs.set(qn('w:name'),'compatibilityMode');cs.set(qn('w:uri'),'http://schemas.microsoft.com/office/word');cs.set(qn('w:val'),'15');compat.append(cs)
OUT=ROOT/'exports/current/Почему_так_первые_пять_глав_v5.docx';D.save(OUT)
print(OUT)
