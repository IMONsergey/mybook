from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

OUT = Path(__file__).resolve().parent
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')
INK = '#151515'
PAPER = '#F5F3ED'
LINE = '#D9D7D1'
ORANGE = '#E34227'

def font(size, family='sans', bold=False):
    names = {'sans': 'DejaVuSans', 'serif': 'DejaVuSerif', 'mono':'DejaVuSansMono'}
    return ImageFont.truetype(str(FONT_DIR / (names[family] + ('-Bold' if bold else '') + '.ttf')), size)

def canvas(h):
    im = Image.new('RGB', (2400,h), 'white')
    return im, ImageDraw.Draw(im)

def txt(d, xy, s, size, family='sans', bold=False, fill=INK, anchor='lt'):
    d.text(xy,s,font=font(size,family,bold),fill=fill,anchor=anchor)

def lines(d, xy, arr, size, lead=None, family='sans', bold=False, fill=INK, anchor='lt'):
    x,y=xy
    for s in arr:
        txt(d,(x,y),s,size,family,bold,fill,anchor)
        y += lead or int(size*1.2)
    return y

def label(d, x, s):
    txt(d,(x,42),s,38,family='mono',fill='#66645E')

def panel(d, box, fill=PAPER):
    d.rectangle(box,fill=fill)

def italic(im, xy, s, size, fill=INK):
    f=font(size,'serif')
    b=f.getbbox(s)
    w=b[2]-b[0]+20
    h=b[3]-b[1]+30
    temp=Image.new('RGBA',(w,h),(255,255,255,0))
    dd=ImageDraw.Draw(temp)
    dd.text((8,8-b[1]),s,font=f,fill=fill)
    slant=.20
    shift=int(h*slant)
    result=temp.transform((w+shift,h),Image.Transform.AFFINE,(1,slant,-shift,0,1,0),resample=Image.Resampling.BICUBIC)
    im.paste(result,(int(xy[0]),int(xy[1])),result)

MANIFEST=[]
def save(im,name,alt):
    path=OUT/name
    im.save(path,dpi=(300,300),optimize=True)
    MANIFEST.append({'path':path.name,'width':im.width,'height':im.height,'alt':alt})

# 1. Identical wording, three typographic voices.
im,d=canvas(760)
cols=[(70,780),(845,1555),(1620,2330)]
for (x,r),letter in zip(cols,['А','Б','В']):
    label(d,x,letter)
    panel(d,(x,115,r,700))
lines(d,(110,270),['ВХОД','СО ДВОРА'],100,130,bold=True)
lines(d,(900,288),['Вход','со двора'],88,116)
italic(im,(1660,289),'Вход',94)
italic(im,(1660,408),'со двора',94)
save(im,'fig01_voice.png','Одна фраза «Вход со двора» в трёх типографических характерах: строгом, спокойном и камерном.')

# 2. Identical information; only size, spacing and arrangement change.
im,d=canvas(1200)
label(d,70,'А');label(d,1250,'Б')
panel(d,(70,110,1150,1140));panel(d,(1250,110,2330,1140))
cx=610
for y,s in [(280,'Вечер'),(365,'короткого кино'),(520,'12 ноября'),(625,'19:00'),(790,'Зал 2'),(895,'Вход свободный')]:
    txt(d,(cx,y),s,65,anchor='mt')
lines(d,(1330,195),['Вечер','короткого','кино'],124,144)
txt(d,(1330,730),'12 ноября',76)
txt(d,(2145,730),'19:00',76,anchor='rt')
txt(d,(1330,944),'Зал 2',54)
txt(d,(1330,1020),'Вход свободный',54)
save(im,'fig02_poster.png','Две афиши вечера короткого кино с одинаковыми данными и разной иерархией размеров, интервалов и расположения.')

# 3. Same event, a change of the communication task.
im,d=canvas(1150)
label(d,70,'А');label(d,1250,'Б')
panel(d,(70,110,1150,1090));panel(d,(1250,110,2330,1090))
lines(d,(150,190),['Вечер','короткого','кино'],118,140)
txt(d,(150,710),'12 ноября',70)
txt(d,(1070,710),'19:00',70,anchor='rt')
txt(d,(150,930),'Зал 2',52)
txt(d,(1070,930),'Вход свободный',52,anchor='rt')
txt(d,(1330,260),'ЗАЛ 2',150,bold=True)
# A deliberately simple, high-contrast navigation arrow.
d.line([(1965,354),(2250,354)],fill=INK,width=20)
d.line([(2168,276),(2250,354),(2168,432)],fill=INK,width=20)
lines(d,(1330,655),['Вечер короткого','кино'],67,86)
txt(d,(1330,875),'12 ноября • 19:00',56)
txt(d,(1330,968),'Вход свободный',52)
save(im,'fig03_context.png','Слева афиша события, справа указатель к залу с теми же сведениями: акценты зависят от места и задачи.')

# 4. Two valid concepts for a fictional neighbourhood gathering.
im,d=canvas(1200)
label(d,70,'А');label(d,1250,'Б')
panel(d,(70,110,1150,1140));panel(d,(1250,110,2330,1140))
txt(d,(150,185),'Встреча соседей',51)
txt(d,(145,335),'БЛИЖЕ',156,bold=True)
# Regular, evenly arranged geometrical benches.
d.rectangle((150,670,500,720),fill=INK)
d.rectangle((700,670,1070,720),fill=INK)
d.rectangle((175,720,205,804),fill=INK)
d.rectangle((445,720,475,804),fill=INK)
d.rectangle((725,720,755,804),fill=INK)
d.rectangle((1015,720,1045,804),fill=INK)
d.rectangle((545,670,655,720),fill=ORANGE)
txt(d,(150,950),'Суббота 14:00',48)
txt(d,(150,1023),'Двор дома',48)
txt(d,(1330,185),'Встреча соседей',51)
# A larger, tightened word with slight baseline shifts.
letters=list('БЛИЖЕ');sizes=font(190,'sans',True)
x=1315
for ch,dy in zip(letters,[0,8,0,-7,0]):
    txt(d,(x,325+dy),ch,190,bold=True)
    x += d.textlength(ch,font=sizes)-9
d.rectangle((1330,680,1777,805),fill=INK)
d.rectangle((1801,680,2250,805),fill=INK)
d.rectangle((1783,680,1795,805),fill=ORANGE)
txt(d,(1330,950),'Суббота 14:00',48)
txt(d,(1330,1023),'Двор дома',48)
save(im,'fig04_neighbours.png','Два плаката вымышленной встречи «Ближе»: спокойная регулярная композиция и выразительное сближение букв и форм.')

# 5. Two flat label designs. No product-quality or origin claims are added.
im,d=canvas(1200)
label(d,250,'А');label(d,1350,'Б')
panel(d,(250,110,1050,1140),'#E9DFCA')
panel(d,(1350,110,2150,1140),ORANGE)
txt(d,(650,235),'РЯДОМ',99,family='serif',anchor='mt')
lines(d,(650,515),['Тёмный','шоколад'],75,104,family='serif',anchor='mt')
txt(d,(335,880),'70%',126,family='serif')
txt(d,(335,1031),'какао',47,family='serif')
txt(d,(965,1031),'100 г',47,family='serif',anchor='rt')
txt(d,(1750,235),'РЯДОМ',107,bold=True,fill='white',anchor='mt')
lines(d,(1430,455),['Тёмный','шоколад'],74,92,bold=True,fill='white')
txt(d,(1410,760),'70%',200,bold=True,fill='white')
txt(d,(1430,1031),'какао',47,fill='white')
txt(d,(2070,1031),'100 г',47,fill='white',anchor='rt')
save(im,'fig05_wrappers.png','Две учебные этикетки одного тёмного шоколада «Рядом»: бумажная с антиквой и яркая с рубленым шрифтом. Состав информации совпадает.')

# 6. Minimal schematic product UI. Empty state with or without a next action.
im,d=canvas(1100)
label(d,70,'А');label(d,1250,'Б')
for x in [70,1250]:
    # Surface outline is part of the interface illustration, not a prose callout.
    d.rectangle((x,110,x+1080,1040),fill='#FAFAF8',outline=LINE,width=2)
    txt(d,(x+70,170),'События',76,bold=True)
    d.rectangle((x+70,300,x+435,389),fill='white',outline='#B6B5B0',width=2)
    txt(d,(x+96,320),'12 ноября',48)
    d.line((x+70,430,x+1010,430),fill=LINE,width=2)
txt(d,(610,620),'Ничего не найдено',61,anchor='mt')
lines(d,(1320,510),['На 12 ноября','событий нет'],68,82,bold=True)
lines(d,(1320,735),['Выбери другую дату','или посмотри все события'],44,61)
d.rectangle((1320,905,2210,995),fill=INK)
txt(d,(1765,927),'Показать все события',47,fill='white',anchor='mt')
save(im,'fig06_empty_state.png','Два учебных пустых состояния поиска событий: сообщение без следующего действия и объяснение с кнопкой просмотра всех событий.')

(OUT/'manifest.json').write_text(json.dumps(MANIFEST,ensure_ascii=False,indent=2),encoding='utf-8')
for x in MANIFEST:
    print(x['path'],x['width'],x['height'])
