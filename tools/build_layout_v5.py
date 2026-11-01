"""Author the v5 book layout in millimetres, independently of Word pagination.
The resulting scene graph feeds editable Word objects and native Figma layers.
"""
from pathlib import Path
import json,re,math,os
from PIL import ImageFont,Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'exports/current'; OUT.mkdir(exist_ok=True,parents=True)
INK='#222820'; PAPER='#F5F2E8'; RED='#BE432D'; GREEN='#244B3D'; WHITE='#FFFFFF'; MUTED='#62665E'; SAND='#E3D7BA'
PT=72/25.4
FONTDIR=Path(os.environ['BOOK_FONTS']) if os.environ.get('BOOK_FONTS') else (ROOT/'assets/fonts' if (ROOT/'assets/fonts/PTSerif-Regular.ttf').exists() else Path('/usr/local/share/fonts/book-v4'))
FONTS={'serif':'PTSerif-Regular.ttf','italic':'PTSerif-Italic.ttf','sans':'IBMPlexSans-Variable.ttf','bold':'IBMPlexSans-Variable.ttf'}
cache={}
def font(role,size):
 key=(role,size)
 if key not in cache:
  f=ImageFont.truetype(str(FONTDIR/FONTS[role]),round(size*10))
  if role in ['sans','bold']:f.set_variation_by_axes([700 if role=='bold' else 400,100])
  cache[key]=f
 return cache[key]
def wrap(s,width,size,role):
 f=font(role,size); limit=width*PT*10
 out=[]
 for line in s.split('\n'):
  words=line.split(); current=''
  for word in words:
   trial=(current+' '+word).strip()
   if current and f.getlength(trial)>limit:out.append(current);current=word
   else:current=trial
  out.append(current)
 return '\n'.join(out)
BLOCKS=[];chapter=''
for raw in (ROOT/'manuscript/source.md').read_text().strip().split('\n\n'):
 s=raw.strip()
 if not s or s.startswith('# Почему') or s=='Сергей Отческов':continue
 if s.startswith('## '):
  lines=s.splitlines();chapter=lines[0][3:];s=lines[-1].lstrip('# ');kind='chapter'
 elif s.startswith('### '):s=s[4:];kind='heading'
 elif s.startswith('[[FIGURE:'):kind='figure'
 else:kind='body'
 BLOCKS.append({'id':len(BLOCKS),'kind':kind,'chapter':chapter,'text':s})
SPECS=json.loads((ROOT/'assets/figures/diagrams-v4.json').read_text())
PAGES=[]; USED=[]; NOTES=[]; COUNTER=0

def page(name,chapter='',bg=PAPER,motif=''):
 p={'number':len(PAGES)+1,'name':name,'chapter':chapter,'width':190,'height':250,'background':bg,'motif':motif,'layers':[]};PAGES.append(p);return p

def layer(p,kind,**kw):
 global COUNTER
 COUNTER+=1;d={'id':f'L{COUNTER:04d}','type':kind,**kw};p['layers'].append(d);return d

def tx(p,s,x,y,w,size=11,leading=14.8,role='serif',color=INK,kind='detail',source=None,align='left'):
 lines=wrap(s,w,size,role);h=lines.count('\n')*leading/PT+leading/PT+0.7
 d=layer(p,'text',text=lines,original=s,x=x,y=y,w=w,h=h,size=size,leading=leading,font=role,color=color,role=kind,align=align)
 if source is not None:d['source_id']=source;USED.append(source)
 if kind=='note':NOTES.append({'page':p['number'],'text':s})
 return y+h

def rect(p,x,y,w,h,color):return layer(p,'rect',x=x,y=y,w=w,h=h,color=color)

def rule(p,x,y,w,color=INK,h=.25):return rect(p,x,y,w,h,color)

def photo(p,file,x,y,w,h=None,crop=None):
 iw,ih=Image.open(ROOT/'assets/figures'/file).size
 if crop:iw*=crop[2]-crop[0];ih*=crop[3]-crop[1]
 h=h or w*ih/iw
 return layer(p,'photo',file=file,x=x,y=y,w=w,h=h,crop=crop)

def svg(p,path,x,y,w,h,color=INK):
 return layer(p,'svg',svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><path d="{path}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',x=x,y=y,w=w,h=h)

def arrow(p,x,y,w=18,h=18,color=RED):return svg(p,'M10 50 H88 M66 28 L88 50 L66 72',x,y,w,h,color)

def heading(p,i,x=18,y=25,w=152,size=22,color=INK):return tx(p,BLOCKS[i]['text'],x,y,w,size,size*1.1,'bold',color,'heading',i)

def body(p,ids,x=18,y=50,w=126,size=11,leading=14.8,color=INK,gap=2.6):
 for i in ids:
  assert BLOCKS[i]['kind']=='body',(i,BLOCKS[i])
  y=tx(p,BLOCKS[i]['text'],x,y,w,size,leading,'serif',color,'body',i)+gap
 return y

def note(p,s,x,y,w=30,color=RED):return tx(p,s,x,y,w,8.5,11,'sans',color,'note')

def caption(p,i,x,y,w):
 m=re.fullmatch(r'\[\[FIGURE:([^|]+)\|(.+)\]\]',BLOCKS[i]['text'],re.S);assert m
 USED.append(i);number=sum(1 for b in BLOCKS[:i+1] if b['kind']=='figure')
 d=tx(p,f'{number:02d}  '+m[2],x,y,w,8.2,10.6,'sans',MUTED,'caption')
 p['layers'][-1]['figure_source_id']=i
 return d

def diagram(p,file,x,y,w):
 spec=SPECS[file];f=w/spec['width'];height=spec['height']*f
 group_id=f'D{p["number"]}-{file}'
 for a in spec['layers']:
  if a['type']=='rect':
   color=a['fill'];color=PAPER if color.upper()=='#F3F0E8' else color
   d=rect(p,x+a['x']*f,y+a['y']*f,a['w']*f,a['h']*f,color)
  else:
   if a['text']=='→':arrow(p,x+a['x']*f,y+a['y']*f,a.get('w',160)*f,160*f);continue
   size=a['size']*f*PT
   # Labels retain readable sizes at the chosen physical scale.
   if size<8:size=8
   color=INK if a['color'].upper()=='#20231F' else RED if a['color'].upper()=='#B9422B' else a['color']
   natural=max(font(a['font'],size).getlength(line)/(10*PT) for line in a['text'].split('\n'))+1.2
   width=min(min(a.get('w',spec['width']-a['x']),spec['width']-a['x'])*f,natural)
   tx(p,a['text'],x+a['x']*f,y+a['y']*f,width,size,size*1.22,a['font'],color,'diagram')
   d=p['layers'][-1]
  d['diagram']=group_id
 return y+height

def folios():
 for p in PAGES:
  if p['number']==1:continue
  c=WHITE if p['background']==GREEN or p['background']==INK else INK
  tx(p,p['chapter'] or 'ПОЧЕМУ ТАК',18,10,148,7.5,9,'sans',c,'header')
  tx(p,f'{p["number"]:02d}',164,238,10,10,12,'sans',c,'folio')

def chapter_title(p,i,n,x,y,w,size=38,color=INK):
 tx(p,f'{n:02d}',x,y-14,25,10,12,'sans',RED if color==INK else '#DBA58F','chapter-label')
 return tx(p,BLOCKS[i]['text'],x,y,w,size,size*1.04,'bold',color,'chapter',i)

# 1. Title: scale, asymmetry, and a concrete object instead of generic ornament.
p=page('Титул',motif='Название и дверь как вход в книгу')
tx(p,'Сергей Отческов',18,18,145,12,15,'sans')
tx(p,'Почему\nтак',14,43,173,80,78,'bold',INK,'title')
photo(p,'v4_door.png',114,130,76)
tx(p,'О вещах, на которые\nмы смотрим каждый день',18,187,87,14,18,'serif')
arrow(p,87,216,19,19)
tx(p,'Предисловие и первые пять глав',18,235,140,8,10,'sans',MUTED)
# 2. Contents: recognisable objects and one stable number column.
p=page('Содержание',motif='Визуальный маршрут по предметам')
tx(p,'Содержание',18,25,154,29,33,'bold')
tx(p,'Предисловие',18,49,122,11,14,'serif');tx(p,'03',161,49,13,11,14,'sans')
chapters=[(1,8,5,'v4_door.png'),(2,39,11,'v4_chocolate.png'),(3,68,16,'v4_chair.png'),(4,98,21,'v4_menu_photo.png'),(5,125,27,None)]
for j,(n,i,start,file) in enumerate(chapters):
 y=73+j*30
 tx(p,f'{n:02d}',18,y,16,18,21,'sans',RED)
 if file:photo(p,file,43,y-1,18,22.5)
 else:
  rect(p,43,y+3,18,13,INK);arrow(p,47,y+5,10,9,WHITE)
 tx(p,BLOCKS[i]['text'],70,y,82,12,15,'sans')
 tx(p,f'{start:02d}',161,y,13,11,14,'sans')
 if j<4:rule(p,70,y+23,104,'#D6D3C8',.2)
# 3-4. Preface: readable prose plus a visual demonstration of the author's claim.
p=page('Предисловие: смотреть скучно','ПРЕДИСЛОВИЕ',motif='Увеличенная авторская реплика и спокойный основной набор')
heading(p,0,y=24,size=29)
tx(p,'«Все мимо.\nДавай еще».',18,51,145,37,40,'serif',INK,'quote')
body(p,[1,2,3],y=99,w=112)
rule(p,145,112,27,RED,.6)
note(p,'Что именно\nпеределывать?',145,118,29)
p=page('Предисловие: подпись меняет историю','ПРЕДИСЛОВИЕ',motif='Одна подпись между двумя разными сценами')
photo(p,'v4_door.png',18,26,44,55);photo(p,'v4_chair.png',99,26,44,55)
note(p,'Одна подпись',64,46,28);arrow(p,71,62,17,17)
note(p,'Рядом',60,83,37)
body(p,[4,5,6],y=105,w=126)
body(p,[7],y=219,w=126,size=13,leading=17)
# Chapter 1, six pages. The opener, voice, route, hierarchy and use form a sequence.
p=page('01 На двери все написано','01 / НА ДВЕРИ ВСЕ НАПИСАНО',motif='Дверь крупно, короткий текст у внешнего края')
chapter_title(p,8,1,18,28,150,38)
photo(p,'v4_door.png',0,82,118)
body(p,[9,11],x=131,y=99,w=43,size=10.5,leading=14)
caption(p,10,18,231,124)
p=page('Три голоса одной фразы','01 / НА ДВЕРИ ВСЕ НАПИСАНО',motif='Типографическое сравнение в одинаковых условиях')
body(p,[12,13],y=25,w=126)
diagram(p,'fig01_voice.png',18,67,156);caption(p,14,18,124,156)
body(p,[15,16,17],y=143,w=126)
p=page('Где находится вход','01 / НА ДВЕРИ ВСЕ НАПИСАНО',motif='Условный план двух арок переводит разговор о шрифте в пространство')
heading(p,18,y=25,size=25)
body(p,[19,20,21,22,23],y=46,w=126)
# abstract courtyard, explicitly a schematic rather than geographical data
rule(p,18,190,156,INK,.7);rect(p,56,188,22,5,PAPER);rect(p,118,188,22,5,PAPER)
tx(p,'Арка 1',52,196,35,9,11,'sans');tx(p,'Арка 2',114,196,35,9,11,'sans')
arrow(p,139,172,21,21);tx(p,'Вход',139,163,32,10,12,'bold',RED)
note(p,'Учебная схема. «Справа» зависит от точки подхода.',18,218,136)
p=page('Семь вечера','01 / НА ДВЕРИ ВСЕ НАПИСАНО',motif='Две афиши на одной оптической плоскости')
heading(p,24,y=25,size=29);body(p,[25],y=45,w=152)
diagram(p,'fig02_poster.png',18,75,156);caption(p,26,18,174,156)
body(p,[27,28],y=192,w=152)
p=page('Заметность и момент','01 / НА ДВЕРИ ВСЕ НАПИСАНО',motif='Время из афиши становится крупным знаком перехода')
body(p,[29,30,31],y=25,w=126)
tx(p,'19:00',16,115,158,70,72,'sans',RED,'diagram')
heading(p,32,y=155,size=24);body(p,[33,34],y=177,w=126)
note(p,'Теперь нужен зал.',18,220,130)
p=page('Афиша и указатель','01 / НА ДВЕРИ ВСЕ НАПИСАНО',motif='Смена задачи видна через крупный указатель и тихое объяснение')
diagram(p,'fig03_context.png',18,29,156);caption(p,35,18,116,156)
body(p,[36,37,38],y=143,w=126)
rule(p,18,222,125,RED,.5);arrow(p,145,213,23,19)
tx(p,'Вход',18,228,35,8,10,'sans');tx(p,'Развилка',70,228,45,8,10,'sans');tx(p,'Зал',130,228,30,8,10,'sans')
# Chapter 2.
p=page('02 Красиво и что дальше','02 / КРАСИВО И ЧТО ДАЛЬШЕ',motif='Материал оберток и ожидание до вкуса')
chapter_title(p,39,2,18,30,154,40)
photo(p,'v4_chocolate.png',77,81,113)
body(p,[40,41],x=18,y=114,w=48,size=11,leading=15)
caption(p,42,18,228,154)
p=page('Буквы на обертке','02 / КРАСИВО И ЧТО ДАЛЬШЕ',motif='Этикетки показаны как самостоятельные объекты')
body(p,[43,44,45],y=25,w=126)
diagram(p,'fig05_wrappers.png',26,83,144);caption(p,46,18,176,156)
body(p,[47,48],y=195,w=152)
p=page('Обещание на обертке','02 / КРАСИВО И ЧТО ДАЛЬШЕ',motif='Малозаметное слово увеличено до главного предмета страницы')
heading(p,49,y=25,size=27);body(p,[50,51,52,53,54],y=50,w=126)
rule(p,18,193,156,RED,.5);tx(p,'горький',17,199,157,45,47,'serif',RED,'diagram')
p=page('Собрать соседей','02 / КРАСИВО И ЧТО ДАЛЬШЕ',motif='Расстояние между буквами и полосы меняют характер приглашения')
heading(p,55,y=25,size=29);body(p,[56,57,58],y=47,w=152)
diagram(p,'fig04_neighbours.png',18,102,156);caption(p,59,18,200,156)
body(p,[60],y=218,w=152,size=10.5,leading=14)
p=page('Мне нравится и мне подходит','02 / КРАСИВО И ЧТО ДАЛЬШЕ',motif='Свободное место у стола связывает две главы')
body(p,[61,62],y=25,w=126);heading(p,63,y=77,w=145,size=25)
body(p,[64,65],y=105,w=126)
photo(p,'v4_chair.png',119,169,55)
body(p,[66,67],x=18,y=174,w=88)
# Chapter 3.
p=page('03 Что осталось за кадром','03 / ЧТО ОСТАЛОСЬ ЗА КАДРОМ',bg=GREEN,motif='Фото и его окружение показаны рядом с коротким чтением')
chapter_title(p,68,3,18,29,156,36,WHITE)
photo(p,'v4_chair.png',78,87,112)
body(p,[69,71],x=18,y=96,w=48,size=10.5,leading=14,color=WHITE)
caption(p,70,18,231,137)
p['layers'][-1]['color']='#D3DED3'
p=page('Общий вид и фрагмент','03 / ЧТО ОСТАЛОСЬ ЗА КАДРОМ',motif='Обрезка одного и того же изображения убирает сведения')
photo(p,'v4_chair.png',18,25,52);photo(p,'v4_chair.png',104,57.5,52,crop=[0,.5,1,1])
note(p,'Полный кадр',18,94,65);note(p,'Нижняя половина',104,94,67)
body(p,[72,73],y=114,w=126)
heading(p,74,y=161,size=23);body(p,[75,76],y=185,w=126)
p=page('Картинка и событие','03 / ЧТО ОСТАЛОСЬ ЗА КАДРОМ',motif='Миниатюра сцены рядом с уточнением ее статуса')
body(p,[77,78,79],y=25,w=126)
heading(p,80,y=112,size=23);body(p,[81,82,83,84],y=131,w=130)
photo(p,'v4_chair.png',153,48,21)
note(p,'Сцена\nдля\nразбора',151,80,25)
p=page('Двадцать красивых стульев','03 / ЧТО ОСТАЛОСЬ ЗА КАДРОМ',motif='Три разных действия вместо ряда разных фактур')
heading(p,85,y=25,size=26);body(p,[86,87],y=51,w=126)
# Exact, deliberately simple line diagrams of actions from the manuscript.
svg(p,'M28 18 V60 H75 V18 M28 42 H75 M34 60 V88 M69 60 V88',20,112,30,30)
arrow(p,50,121,16,16);note(p,'Придвинуть\nстул',18,148,46)
svg(p,'M20 30 H64 V65 Q42 84 20 65 Z M64 36 H78 Q93 49 78 60 H64 M12 82 H81',77,112,30,30)
arrow(p,105,123,15,15);note(p,'Передать\nчашку',76,148,44)
tx(p,'Ближе',130,121,45,19,22,'serif',INK,'diagram');note(p,'Работать\nсо словом',131,148,43)
body(p,[88,89,90],y=170,w=152)
p=page('Что доказывает сравнение','03 / ЧТО ОСТАЛОСЬ ЗА КАДРОМ',motif='Отдельно один интервал и несколько одновременных изменений')
heading(p,91,y=25,size=24);body(p,[92,93],y=47,w=152)
diagram(p,'v4_compare.png',35,86,120);caption(p,94,18,160,156)
body(p,[95,96,97],y=172,w=152)
# Chapter 4.
p=page('04 Здесь слишком много воздуха','04 / ЗДЕСЬ СЛИШКОМ МНОГО ВОЗДУХА',motif='Пустое поле становится частью разбора меню')
chapter_title(p,98,4,18,29,158,40)
photo(p,'v4_menu_photo.png',112,117,78)
body(p,[99,101],x=18,y=128,w=84)
caption(p,100,18,229,156)
p=page('Три версии меню','04 / ЗДЕСЬ СЛИШКОМ МНОГО ВОЗДУХА',motif='Шум, удаленная информация и восстановленная связь')
body(p,[102],y=25,w=126)
diagram(p,'v4_menu.png',14,62,162);caption(p,103,18,176,156)
body(p,[104],y=207,w=152)
p=page('Убрать линию','04 / ЗДЕСЬ СЛИШКОМ МНОГО ВОЗДУХА',motif='Две строки меню показывают работу разделителя')
heading(p,105,y=25,size=31);body(p,[106,107,108,109],y=49,w=126)
for x,show in [(18,True),(101,False)]:
 tx(p,'Капучино',x,181,51,11,14,'sans');tx(p,'240 ₽',x+51,181,22,11,14,'sans')
 tx(p,'Латте',x,199,51,11,14,'sans');tx(p,'290 ₽',x+51,199,22,11,14,'sans')
 if show:rule(p,x,193,73,INK,.3)
note(p,'С линией',18,218,73);note(p,'С промежутком',101,218,73)
p=page('Убрать слово','04 / ЗДЕСЬ СЛИШКОМ МНОГО ВОЗДУХА',motif='Сокращенная кнопка и исчезнувшее условие стоят рядом')
heading(p,110,y=25,size=31);body(p,[111,112,113,114],y=49,w=126)
rect(p,18,173,156,19,INK);tx(p,'Оформить предварительный заказ',24,178,144,13,16,'sans',WHITE,'diagram')
rect(p,18,204,67,19,INK);tx(p,'Заказать',24,209,55,13,16,'sans',WHITE,'diagram')
note(p,'Что произойдет\nпосле нажатия?',99,204,75)
p=page('Убрать характер','04 / ЗДЕСЬ СЛИШКОМ МНОГО ВОЗДУХА',motif='Возвращение приглашения показывает потерю характера')
heading(p,115,y=25,size=31)
tx(p,'БЛИЖЕ',17,52,151,44,46,'bold',RED,'diagram')
tx(p,'Ближе',19,78,150,16,20,'sans',INK,'diagram')
body(p,[116,117,118,119],y=105,w=126)
p=page('Сколько места нужно паузе','04 / ЗДЕСЬ СЛИШКОМ МНОГО ВОЗДУХА',motif='Бумажная полоса и экранное окно показывают разные масштабы паузы')
heading(p,120,y=25,size=27);body(p,[121,122,123,124],y=52,w=126)
# same content markers, two viewports
rect(p,20,178,42,55,WHITE);rule(p,25,185,25,INK,.6);rule(p,25,220,30,INK,.6)
rect(p,110,178,42,55,WHITE);rect(p,110,178,42,25,PAPER)
rule(p,110,178,42,RED,.5);rule(p,110,203,42,RED,.5);rule(p,115,185,25,INK,.6);rule(p,115,220,30,INK,.6)
note(p,'Лист',68,181,29);note(p,'Видимая\nобласть\nэкрана',157,179,23)
# Chapter 5.
p=page('05 А потом человек нажал','05 / А ПОТОМ ЧЕЛОВЕК НАЖАЛ',bg=INK,motif='Крупная кнопка и отсутствие ответа задают сюжет главы')
chapter_title(p,125,5,18,29,156,40,WHITE)
body(p,[126],y=91,w=145,color=WHITE)
rect(p,18,121,156,28,PAPER);tx(p,'Записаться',27,128,118,24,28,'sans',INK,'diagram');arrow(p,148,126,20,20,INK)
body(p,[127],y=162,w=150,size=18,leading=22,color=WHITE)
body(p,[128,129],y=181,w=152,color=WHITE)
p=page('На эту дату ничего нет','05 / А ПОТОМ ЧЕЛОВЕК НАЖАЛ',motif='Пустой результат и понятный следующий шаг')
heading(p,130,y=25,size=28);body(p,[131],y=49,w=152)
diagram(p,'fig06_empty_state.png',25,63,140);caption(p,132,18,140,156)
body(p,[133,134,135,136],y=152,w=156)
p=page('Пока идет работа','05 / А ПОТОМ ЧЕЛОВЕК НАЖАЛ',motif='После ожидания возможны два исхода; успех и ошибка не идут друг за другом')
heading(p,137,y=25,size=29);body(p,[138,139],y=47,w=152)
# Redrawn state comparison at a readable scale with explicit branch semantics.
state_rows=[('01 / До нажатия','Встреча соседей','12 ноября / 19:00','Записаться'),('02 / Ожидание','Отправляем','Подтверждение еще не пришло','Подожди немного'),('03 / Успех','Ты записан','12 ноября / 19:00','Посмотреть адрес'),('04 / Ошибка','Не получилось','Данные сохранены в форме','Попробовать снова')]
for j,(label,title,sub,button) in enumerate(state_rows):
 x=18+(j%2)*82;y=96+(j//2)*39
 tx(p,label,x,y,73,7.6,9.5,'sans',RED,'diagram');tx(p,title,x,y+7,73,14,16,'bold',INK,'diagram');tx(p,sub,x,y+15,73,8.2,10,'sans',MUTED,'diagram');tx(p,button,x,y+26,73,9,11,'sans',INK,'diagram');rule(p,x,y+33,73,'#C9C9BF',.2)
caption(p,140,18,174,156)
body(p,[141,142],y=192,w=152)
p=page('Текст который не влез','05 / А ПОТОМ ЧЕЛОВЕК НАЖАЛ',motif='Высота карточки меняется вслед за длиной названия')
heading(p,143,y=25,size=29);body(p,[144,145,146],y=48,w=152)
diagram(p,'v4_cards.png',18,123,156);caption(p,147,18,228,156)
p=page('Кнопка выглядит как обещание','05 / А ПОТОМ ЧЕЛОВЕК НАЖАЛ',motif='Спокойный набор и связка названия действия с последствием')
body(p,[148,149],y=25,w=126);heading(p,150,y=84,size=24)
body(p,[151,152,153,154],y=112,w=126)
tx(p,'Действие',151,143,25,8.5,11,'sans',RED,'diagram');svg(p,'M50 12 V88 M28 66 L50 88 L72 66',155,154,17,17,RED);tx(p,'Результат',151,176,25,8.5,11,'sans',RED,'diagram')
p=page('Вернуться к двери','05 / А ПОТОМ ЧЕЛОВЕК НАЖАЛ',motif='Ручка двери и кнопка замыкают маршрут книги')
heading(p,155,y=25,size=32)
photo(p,'v4_door.png',18,54,52,65)
rect(p,97,72,77,22,INK);tx(p,'Войти',106,78,53,16,19,'sans',WHITE,'diagram');arrow(p,72,79,23,20)
body(p,[156,157,158,159],y=137,w=152)
# Colophon and reading references, not a claim of production clearance.
p=page('Визуальные материалы','ПОЧЕМУ ТАК',motif='Предметный индекс возвращает четыре сцены книги')
tx(p,'Визуальные\nматериалы',18,25,156,28,31,'bold')
tx(p,'Дверь, обертки, место за столом и лист меню созданы с помощью imagegen для учебных ситуаций этой книги. Они не являются фотографиями реальных проектов или встреч.',18,58,126,11,14.8,'serif')
for j,(file,label) in enumerate([('v4_door.png','Дверь'),('v4_chocolate.png','Обертки'),('v4_chair.png','Стул'),('v4_menu_photo.png','Меню')]):
 x=18+j*40;photo(p,file,x,104,33);tx(p,label,x,149,33,8.5,11,'sans')
tx(p,'Для дальнейшего чтения',18,170,155,20,24,'bold')
tx(p,'Эллен Луптон. Thinking with Type.\nО шрифте, интервалах и организации текста.',18,186,153,10,13,'serif')
tx(p,'Дон Норман. The Design of Everyday Things.\nО том, как люди разбираются с привычными вещами.',18,203,153,10,13,'serif')
tx(p,'Сергей Отческов · Почему так · 2026',18,228,150,8,10,'sans',MUTED)
folios()
# Full source accounting, independent of paragraphs changing their line wrapping.
missing=sorted(set(range(len(BLOCKS)))-set(USED));dup=sorted({i for i in USED if USED.count(i)>1})
assert not missing and not dup,(missing,dup)
violations=[]
for p in PAGES:
 for l in p['layers']:
  if l['type']=='text' and (l['x']<0 or l['y']<0 or l['x']+l['w']>190.1 or l['y']+l['h']>249):violations.append({'page':p['number'],'id':l['id'],'text':l['text'][:50],'bottom':round(l['y']+l['h'],2)})
result={'version':'v5','text_version':'v4','units':'mm','figma_px_per_pt':2,'pages':PAGES,'source_blocks':BLOCKS,'validation':{'source_blocks':len(BLOCKS),'used_once':len(USED),'bounds_warnings':violations}}
(OUT/'layout-v5.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(ROOT/'manuscript/visual-notes-v5.md').write_text('# Дополнительные визуальные комментарии v5\n\nРедакторские подписи и пояснения для новой верстки. Основная рукопись v4 сохранена. Это предложения редактора, не новые биографические сведения или утверждения автора.\n\n'+'\n'.join(f'- Страница {a["page"]}: {a["text"].replace(chr(10)," ")}' for a in NOTES)+'\n')
print(json.dumps({'pages':len(PAGES),'layers':COUNTER,'source_blocks':len(BLOCKS),'bounds_warnings':violations},ensure_ascii=False,indent=2))
