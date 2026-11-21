from PIL import Image, ImageDraw, ImageFont
import math, os
D=os.path.dirname(os.path.abspath(__file__))
W,H=1280,720
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def f(n,b=False): return ImageFont.truetype(bold if b else font,n)
navy='#16344c'; ink='#294a5b'; cream='#f6f2e5'; yellow='#f9cc58'; teal='#36a99c'; coral='#f07259'; blue='#5c91bc'
def txt(d,xy,s,size=30,color=navy,b=True): d.text(xy,s,font=f(size,b),fill=color,stroke_width=0)
def rr(d,box,fill,r=20,outline=None,width=2): d.rounded_rectangle(box,r,fill,outline,width)
def arrow(d,x1,y1,x2,y2,color=teal):
 d.line((x1,y1,x2,y2),fill=color,width=8); a=math.atan2(y2-y1,x2-x1)
 d.polygon([(x2,y2),(x2-22*math.cos(a-.55),y2-22*math.sin(a-.55)),(x2-22*math.cos(a+.55),y2-22*math.sin(a+.55))],fill=color)
def gear(d,cx,cy,r,color):
 for a in range(0,360,45):
  a=math.radians(a); x=cx+math.cos(a)*r*.88; y=cy+math.sin(a)*r*.88; d.ellipse((x-12,y-12,x+12,y+12),fill=color)
 d.ellipse((cx-r*.78,cy-r*.78,cx+r*.78,cy+r*.78),fill=color); d.ellipse((cx-r*.24,cy-r*.24,cx+r*.24,cy+r*.24),fill=cream)
def machine(d,x,y,scale=1):
 rr(d,(x,y,x+450*scale,y+255*scale),navy,16)
 for i in range(3):
  xx=x+(25+i*140)*scale; rr(d,(xx,y+25*scale,xx+120*scale,y+215*scale),'#48728a',8)
  for j in range(4):
   for k in range(3):
    cx=xx+(25+k*34)*scale; cy=y+(52+j*42)*scale; d.ellipse((cx-7*scale,cy-7*scale,cx+7*scale,cy+7*scale),fill=yellow if (j+k+i)%2 else teal)
def card(d,x,y):
 rr(d,(x,y,x+230,y+128),'#fffaf0',12,navy,3)
 for a in range(6):
  for b in range(3):
   if (a+b)%3!=0: d.rectangle((x+20+a*33,y+25+b*29,x+32+a*33,y+37+b*29),fill=navy)
def base(num,kicker,title,sub):
 im=Image.new('RGB',(W,H),cream); d=ImageDraw.Draw(im)
 d.rectangle((0,0,W,14),fill=teal); d.ellipse((1050,-190,1430,190),fill='#dbece5'); d.ellipse((-170,530,160,860),fill='#f9e7ba')
 txt(d,(65,38),kicker.upper(),20,teal); txt(d,(65,83),title,46); txt(d,(66,150),sub,23,ink,False)
 d.line((65,643,1215,643),fill='#d9dfd7',width=3); txt(d,(65,660),'COMO NASCEU O COMPUTADOR',17,ink); txt(d,(1150,658),f'{num:02}',20,teal)
 return im,d
def save(im,n): im.save(os.path.join(D,f'cena-{n:02}.png'),optimize=True)
# 1
im,d=base(1,'Uma história de ideias','O PRIMEIRO COMPUTADOR?', 'A resposta depende do que chamamos de computador.')
for i,(year,label,col) in enumerate([('1800','IDEIA',yellow),('1941','Z3',teal),('1946','ENIAC',coral),('HOJE','CHIPS',blue)]):
 x=90+i*305; d.ellipse((x+55,270,x+190,405),fill=col); txt(d,(x+57,310),year,28); txt(d,(x+50,445),label,24)
 if i<3: arrow(d,x+200,340,x+280,340)
save(im,1)
# 2
im,d=base(2,'Século XIX','A MÁQUINA ANALÍTICA','Charles Babbage imaginou uma máquina programável.')
rr(d,(110,245,635,550),'#e0bd79',18,navy,4)
for x,y,r in [(250,375,90),(420,365,70),(530,445,45)]: gear(d,x,y,r,navy)
card(d,845,310); arrow(d,815,380,675,380); txt(d,(825,465),'CARTÕES',25); txt(d,(825,503),'INSTRUÇÕES',22,teal)
save(im,2)
# 3
im,d=base(3,'1843','ADA LOVELACE','Um método para calcular números de Bernoulli.')
rr(d,(118,230,558,570),'#dcebe6',30); d.ellipse((246,270,400,424),fill='#dca57e'); d.pieslice((230,240,410,405),180,360,fill=navy); d.polygon([(195,550),(250,420),(398,420),(460,550)],fill=teal)
card(d,705,255); arrow(d,955,320,1075,320); txt(d,(1000,365),'1  2  3',32,coral); txt(d,(697,448),'PASSO A PASSO',27); txt(d,(697,493),'PROGRAMA',35,teal)
save(im,3)
# 4
im,d=base(4,'1941','Z3: MÁQUINA AUTOMÁTICA','Konrad Zuse construiu uma máquina eletromecânica programável.')
machine(d,145,250,1.05); txt(d,(765,250),'0  1  1  0',55,teal); txt(d,(760,350),'RELÉS + CÓDIGO',27); arrow(d,650,375,730,375); txt(d,(760,405),'BINÁRIO',29,coral)
save(im,4)
# 5
im,d=base(5,'1946','ENIAC: ELETRÔNICA EM ESCALA','Um dos primeiros computadores eletrônicos digitais de uso geral.')
machine(d,105,265,1.2); machine(d,660,265,1.0); txt(d,(144,575),'MILHARES DE VÁLVULAS',23,teal); txt(d,(815,553),'UMA SALA',23,coral)
save(im,5)
# 6
im,d=base(6,'Programação','CABOS E INTERRUPTORES','Programadoras configuravam as tarefas da máquina.')
rr(d,(115,235,760,565),navy,25)
for i in range(5):
 for j in range(3):
  x=165+i*105; y=285+j*85; d.ellipse((x-12,y-12,x+12,y+12),fill=yellow)
for points,col in [([(165,285),(220,360),(375,370),(480,450)],coral), ([(270,285),(330,430),(580,370)],teal), ([(690,285),(630,420),(375,455)],blue)]: d.line(points,fill=col,width=9)
txt(d,(825,300),'CONFIGURAR',29); txt(d,(825,348),'CONECTAR',29,teal); txt(d,(825,396),'CALCULAR',29,coral)
save(im,6)
# 7
im,d=base(7,'Uma construção coletiva','DE UMA SALA A UM CHIP','A computação nasceu de muitas ideias e pessoas.')
machine(d,100,290,.7); arrow(d,490,380,665,380); rr(d,(720,275,1020,525),navy,24)
for i in range(7):
 x=740+i*40; d.line((x,248,x,275),fill=teal,width=8); d.line((x,525,x,553),fill=teal,width=8)
for i in range(5):
 y=300+i*45; d.line((690,y,720,y),fill=teal,width=8); d.line((1020,y,1050,y),fill=teal,width=8)
txt(d,(790,350),'CHIP',44,cream); txt(d,(310,580),'IDEIAS + MÁQUINAS + PESSOAS',28,teal)
save(im,7)
