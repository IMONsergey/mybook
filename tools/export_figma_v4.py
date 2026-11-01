"""Export editable page geometry from the visually checked Word rendering."""
from pathlib import Path
import json,fitz
ROOT=Path(__file__).resolve().parents[1]
doc=fitz.open(next((ROOT/'render_final').glob('*.pdf')))
figures=json.loads((ROOT/'exports/current/figures-v4.json').read_text());seen={};pages=[]
for pi,p in enumerate(doc):
    texts=[];images=[]
    for b in p.get_text('dict')['blocks']:
        if b['type']!=0:continue
        lines=b['lines'];first=lines[0]['spans'][0];size=first['size']
        leading=lines[1]['spans'][0]['origin'][1]-first['origin'][1] if len(lines)>1 else {56:57,30:32.4,19:21.85,11.5:15,8:10.5,7.5:10}.get(size,size*1.2)
        if leading<=0:leading=size*1.3
        body=[];spans=[];offset=0
        for li,line in enumerate(lines):
            for s in line['spans']:
                tx=s['text'];family='PT Serif' if s['font'].startswith('PTSerif') else 'IBM Plex Sans'
                style='Bold' if 'Bold' in s['font'] else 'Italic' if 'Italic' in s['font'] or s['flags']&2 else 'Regular'
                spans.append({'start':offset,'end':offset+len(tx),'family':family,'style':style,'size':s['size']*2});body.append(tx);offset+=len(tx)
            if li<len(lines)-1:body.append('\n');offset+=1
        text=''.join(body)
        glyphH=(first['ascender']-first['descender'])*size
        x=b['bbox'][0]*2;y=b['bbox'][1]*2+glyphH-leading
        role='header' if y<75 else 'footer' if y>1300 and text.isdigit() else 'text'
        width=max((p.rect.width-56.7)*2-x+2,(b['bbox'][2]-b['bbox'][0])*2+4)
        texts.append({'text':text,'spans':spans,'x':round(x,3),'y':round(y,3),'w':round(width,3),'lineHeight':round(leading*2,3),'lines':len(lines),'role':role})
    for info in p.get_image_info(xrefs=True):
        key=info['xref']
        if key not in seen:seen[key]=figures[len(seen)]
        x0,y0,x1,y1=info['bbox'];images.append({**seen[key],'x':x0*2,'y':y0*2,'w':(x1-x0)*2,'h':(y1-y0)*2})
    pages.append({'number':pi+1,'w':p.rect.width*2,'h':p.rect.height*2,'texts':texts,'images':images})
assert len(seen)==14
payload={'version':'v4','pages':pages,'diagrams':json.loads((ROOT/'assets/figures/diagrams-v4.json').read_text())}
(ROOT/'exports/current/layout-v4.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
print({'pages':len(pages),'text_blocks':sum(len(p['texts']) for p in pages),'figures':len(seen),'native_diagrams':len(payload['diagrams'])})
