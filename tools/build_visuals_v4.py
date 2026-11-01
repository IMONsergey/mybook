"""Editable diagram specification shared by Word raster export and Figma layers."""
import json, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
FONTS=Path(os.environ.get('BOOK_FONTS',str(ROOT/'assets/fonts')))
INK='#20231F'; RED='#B9422B'; PAPER='#F3F0E8'; GRAY='#D9D8D0'; WHITE='#FFFFFF'
diagrams={}

def fig(key,h=600):
    d={'width':1000,'height':h,'background':PAPER,'layers':[]};diagrams[key]=d;return d
def rect(d,x,y,w,h,fill=WHITE):
    d['layers'].append(dict(type='rect',x=x,y=y,w=w,h=h,fill=fill))
def text(d,x,y,s,size=30,font='sans',color=INK,w=800):
    d['layers'].append(dict(type='text',x=x,y=y,text=s,size=size,font=font,color=color,w=w))
def panel(d,x,label,w=460,h=500):
    rect(d,x,65,w,h);text(d,x,12,label,22,color=RED)

d=fig('fig01_voice.png',350)
for x,label in [(0,'01  КОМАНДА'),(340,'02  СООБЩЕНИЕ'),(680,'03  РАЗГОВОР')]:rect(d,x,65,320,260);text(d,x+18,20,label,18,color=RED)
text(d,20,132,'ВХОД\nСО ДВОРА',46,'bold',w=290)
text(d,360,150,'Вход со двора',30,w=290)
text(d,700,140,'Вход\nсо двора',38,'italic',w=290)

d=fig('fig02_poster.png',620)
panel(d,15,'01  ПО ПОРЯДКУ',460,535);panel(d,525,'02  ПО РОЛЯМ',460,535)
for i,s in enumerate(['Вечер короткого кино','12 ноября','19:00','Зал 2','Вход свободный']):text(d,45,110+i*85,s,29,w=420)
text(d,555,100,'ВЕЧЕР\nКОРОТКОГО\nКИНО',58,'bold',w=410);rect(d,555,345,400,4,RED)
text(d,555,380,'12 ноября  /  19:00',31,'bold',w=410);text(d,555,465,'Зал 2',30,w=410);text(d,555,525,'Вход свободный',25,w=410)

d=fig('fig03_context.png',540)
panel(d,15,'01  ПРИГЛАСИТЬ',460,445);panel(d,525,'02  ПОКАЗАТЬ ПУТЬ',460,445)
text(d,45,110,'ВЕЧЕР\nКОРОТКОГО\nКИНО',52,'bold',w=415);text(d,45,360,'12 ноября / 19:00',28,w=410);text(d,45,420,'Зал 2 · Вход свободный',25,w=410)
text(d,555,120,'ЗАЛ 2',83,'bold',w=410);text(d,555,230,'→',160,'sans',RED,w=400);text(d,555,420,'Вечер короткого кино',27,w=410)

d=fig('fig04_neighbours.png',610)
panel(d,15,'01  СВОБОДНЕЕ',460,520);panel(d,525,'02  ТЕСНЕЕ',460,520)
text(d,48,110,'Б Л И Ж Е',49,'bold',w=415);text(d,555,110,'БЛИЖЕ',70,'bold',w=415)
text(d,45,220,'Встреча соседей',29,w=410);text(d,555,220,'Встреча соседей',29,w=410)
rect(d,45,310,150,110,INK);rect(d,280,310,150,110,INK)
rect(d,555,310,184,110,INK);rect(d,739,310,15,110,RED);rect(d,754,310,184,110,INK)
for x in [45,555]:text(d,x,480,'Суббота / 14:00 / во дворе',24,w=410)

d=fig('fig05_wrappers.png',620)
rect(d,70,30,370,560,'#E2D2B3');rect(d,560,30,370,560,RED)
text(d,105,100,'Рядом',73,'serif',w=310);text(d,590,100,'РЯДОМ',66,'bold',WHITE,w=320)
text(d,105,340,'Темный\nшоколад',38,'serif',w=310);text(d,590,340,'Темный\nшоколад',38,'sans',WHITE,w=310)
text(d,105,500,'70% какао / 100 г',24,w=310);text(d,590,500,'70% какао / 100 г',24,color=WHITE,w=310)

d=fig('fig06_empty_state.png',520)
panel(d,15,'01  РЕЗУЛЬТАТ',460,420);panel(d,525,'02  СЛЕДУЮЩИЙ ШАГ',460,420)
text(d,45,105,'Расписание / 12 ноября',25,w=410);text(d,555,105,'Расписание / 12 ноября',25,w=410)
text(d,65,245,'Ничего не найдено',32,'bold',w=390)
text(d,555,200,'12 ноября\nвстреч нет',39,'bold',w=400);text(d,555,310,'Выбери другую дату',26,w=400)
rect(d,555,380,400,64,INK);text(d,576,396,'Показать все события',25,color=WHITE,w=360)

d=fig('v4_compare.png',600)
text(d,25,20,'ОДНО ИЗМЕНЕНИЕ',23,'bold',RED)
rect(d,25,70,450,180,WHITE);rect(d,525,70,450,180,WHITE)
text(d,60,120,'Б Л И Ж Е',51,'bold',w=400);text(d,560,120,'БЛИЖЕ',51,'bold',w=400)
text(d,25,310,'НЕСКОЛЬКО ИЗМЕНЕНИЙ',23,'bold',RED)
rect(d,25,360,450,205,WHITE);rect(d,525,360,450,205,RED)
text(d,60,415,'Б Л И Ж Е',42,'serif',w=400);text(d,550,390,'БЛИЖЕ',83,'bold',WHITE,w=400)
text(d,550,510,'Встреча во дворе',24,color=WHITE,w=400)

d=fig('v4_menu.png',680)
for x,l in [(15,'01  ШУМ'),(350,'02  ПРОПУСК'),(685,'03  СВЯЗЬ')]:panel(d,x,l,300,590)
text(d,35,92,'ДВОР',56,'bold',RED,w=260)
for i,s in enumerate(['КАПУЧИНО','250 мл  240 ₽','ЛАТТЕ','350 мл  290 ₽','ЭСПРЕССО','30 мл  160 ₽']):text(d,35,200+i*64,s,30,'bold',RED,w=260)
text(d,375,100,'Двор',36,'serif',w=250)
for i,s in enumerate(['Капучино  240','Латте         290','Эспрессо    160']):text(d,375,240+i*110,s,24,'serif',w=250)
text(d,710,100,'Двор',36,'serif',w=250)
for i,(s,sub) in enumerate([('Капучино','250 мл · 240 ₽'),('Латте','350 мл · 290 ₽'),('Эспрессо','30 мл · 160 ₽')]):text(d,710,210+i*130,s,30,'bold',w=250);text(d,710,255+i*130,sub,24,w=250)

d=fig('v4_states.png',730)
for x,y,label,title,body,button,color in [
 (20,20,'01  ДО НАЖАТИЯ','Встреча соседей','12 ноября / 19:00','Записаться',INK),
 (520,20,'02  ОЖИДАНИЕ','Отправляем','Подтверждение еще не пришло','Подожди немного','#6B7066'),
 (20,380,'03  УСПЕХ','Ты записан','12 ноября / 19:00','Посмотреть адрес',INK),
 (520,380,'04  ОШИБКА','Не получилось','Данные сохранены в форме','Попробовать снова',RED)]:
 text(d,x,y,label,20,'bold',RED,w=460);rect(d,x,y+40,460,280,WHITE);text(d,x+24,y+75,title,32,'bold',w=410);text(d,x+24,y+140,body,23,w=410);rect(d,x+24,y+215,412,65,color);text(d,x+44,y+232,button,25,color=WHITE,w=370)

d=fig('v4_cards.png',650)
panel(d,15,'01  КОРОТКОЕ НАЗВАНИЕ',460,540);panel(d,525,'02  ДЛИННОЕ НАЗВАНИЕ',460,540)
for x in [45,555]:rect(d,x,95,400,120,'#DCD8CC');text(d,x+22,130,'ДВОР / СОБЫТИЯ',26,'bold',w=360)
text(d,45,250,'Встреча соседей',34,'bold',w=410);text(d,45,310,'12 ноября / 19:00',26,w=400)
text(d,555,250,'Знакомство жителей\nнового корпуса\nи разговор о дворе',32,'bold',w=410);text(d,555,400,'12 ноября / 19:00',26,w=400)
for x,y in [(45,400),(555,485)]:rect(d,x,y,400,65,INK);text(d,x+24,y+17,'Подробнее',25,color=WHITE,w=350)

def font_file(kind):
    return FONTS/({'serif':'PTSerif-Regular.ttf','italic':'PTSerif-Italic.ttf'}.get(kind,'IBMPlexSans-Variable.ttf'))

def render():
    out=ROOT/'assets/figures';out.mkdir(exist_ok=True)
    for name,d in diagrams.items():
        scale=2.4;im=Image.new('RGB',(2400,round(d['height']*scale)),d['background']);draw=ImageDraw.Draw(im)
        for l in d['layers']:
            if l['type']=='rect':draw.rectangle((l['x']*scale,l['y']*scale,(l['x']+l['w'])*scale,(l['y']+l['h'])*scale),fill=l['fill'])
            else:
                ft=ImageFont.truetype(str(font_file(l['font'])),round(l['size']*scale))
                if l['font']=='bold':
                    try:ft.set_variation_by_axes([700,100])
                    except (OSError,ValueError):pass
                for n,line in enumerate(l['text'].split('\n')):draw.text((l['x']*scale,(l['y']+n*l['size']*1.15)*scale),line,font=ft,fill=l['color'],anchor='lt')
        im.save(out/name)
    (ROOT/'assets/figures/diagrams-v4.json').write_text(json.dumps(diagrams,ensure_ascii=False,indent=2))
    print('Rendered',len(diagrams),'editable diagram specifications')

if __name__=='__main__':render()
