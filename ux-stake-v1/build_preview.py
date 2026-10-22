from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
parts = []
def rect(x,y,w,h,fill='#141e30',r=14,stroke='none'):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>')
def text(x,y,s,size=14,fill='#eaf0f8',weight=400,anchor='start'):
    parts.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(s)}</text>')
def button(x,y,w,h,label,primary=False,size=14):
    rect(x,y,w,h,'#e5bc73' if primary else '#223049',10)
    text(x+w/2,y+h/2+size*.35,label,size,'#152035' if primary else '#eaf0f8',700,'middle')
def symbol(x,y,code,s):
    shapes={
      'diamond':'<path d="M50 9 81 50 50 91 19 50Z"/>',
      'heart':'<path d="M50 83 18 51C0 22 30 6 50 29 70 6 100 22 82 51Z"/>',
      'crown':'<path d="M16 30 34 44 50 17 66 44 84 30 76 76H24Z"/><path d="M25 85h50" fill="none" stroke="currentColor" stroke-width="5"/>',
      'shield':'<path d="M25 17h50v40Q75 76 50 90 25 76 25 57Z" fill="none" stroke="currentColor" stroke-width="5"/><path d="M50 28 63 63 50 55 37 63Z"/>',
      'wild':'<path d="m50 9 12 27 29 3-22 20 6 31-25-16-25 16 6-31L9 39l29-3Z"/>',
      'scatter':'<circle cx="50" cy="50" r="31" fill="none" stroke="currentColor" stroke-width="6"/><path d="m50 25 8 16 18 3-13 13 3 18-16-9-16 9 3-18-13-13 18-3Z"/>'}
    colors={'diamond':'#8bd5cc','heart':'#dd8eac','crown':'#e5bc73','shield':'#c5b1ec','wild':'#e5bc73','scatter':'#d7c99c'}
    parts.append(f'<g transform="translate({x},{y}) scale({s/100})" fill="{colors[code]}" color="{colors[code]}">{shapes[code]}</g>')
def grid(x,y,w,h):
    codes=['diamond','crown','shield','heart','scatter','heart','shield','wild','diamond','crown','crown','heart','diamond','shield','heart']
    rect(x-5,y-5,w+10,h+10,'#0a1221',14,'#736044')
    for row in range(3):
        for col in range(5):
            cw,ch=w/5,h/3
            rect(x+col*cw+3,y+row*ch+3,cw-6,ch-6,'#17243a',8)
            s=min(cw*.7,ch*.78)
            symbol(x+col*cw+(cw-s)/2,y+row*ch+(ch-s)/2,codes[row*5+col],s)

parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="1520" height="1040" viewBox="0 0 1520 1040" role="img" aria-labelledby="title desc"><title id="title">Polska Gurom — koncepcja UX v1</title><desc id="desc">Makieta ekranu komputera i telefonu z planszą 5 na 3, saldem demonstracyjnym, stawką, obrotem oraz dostępem do zasad i dźwięku.</desc>')
rect(0,0,1520,1040,'#eeeae3',0)
text(52,59,'POLSKA GUROM / UX 01',18,'#6f6557',700)
text(52,106,'Gra na pierwszym planie.',36,'#182335',700)
text(52,140,'Koncepcja dla Stake Engine • komputer + telefon • 20.10.2026',17,'#635e56')
text(52,194,'KOMPUTER',13,'#6f6557',700)
text(1110,194,'TELEFON / UKŁAD 390 × 780',13,'#6f6557',700)

# Desktop: the game is the visual centre, without tester statistics above it.
rect(52,216,995,638,'#0d1525',22)
text(83,258,'POLSKA GUROM',21,'#e5bc73',700)
text(83,282,'DEMO • ŚRODKI TESTOWE',10,'#b8c4d8',700)
button(844,237,74,44,'Dźwięk',False,11)
button(929,237,87,44,'Zasady',False,12)
rect(83,304,933,45,'#1b293d',10)
text(105,333,'20 linii • kaskady',14)
text(995,333,'3 / 4 / 5 Scatterów → 8 / 10 / 12 obrotów',14,'#c5cddd',400,'end')
grid(211,370,675,273)
text(549,680,'Wybierz stawkę i rozpocznij rundę.',15,'#c5cddd',400,'middle')
text(83,720,'SALDO TESTOWE',11,'#abb9ce',700)
text(83,752,'1 000,00 USD',24,weight=700)
text(316,720,'STAWKA',11,'#abb9ce',700)
button(316,733,44,46,'−',False,22)
text(418,762,'1,00 USD',18,weight=700,anchor='middle')
button(479,733,44,46,'+',False,22)
text(578,720,'WYPŁATA RUNDY',11,'#abb9ce',700)
text(578,752,'0,00 USD',24,weight=700)
button(798,718,218,64,'ZAKRĘĆ',True,19)
text(83,817,'RTP 96% • maks. 5000× • tabela wypłat w zasadach',12,'#abb9ce')
button(929,795,87,40,'Opcje',False,12)

# Mobile is shown at 0.86 scale; all key controls fit into the proposed viewport.
parts.append('<g transform="translate(1100,216) scale(.86)">')
rect(0,0,390,780,'#0d1525',24)
text(20,35,'POLSKA GUROM',19,'#e5bc73',700)
text(20,57,'DEMO • ŚRODKI TESTOWE',10,'#b8c4d8',700)
button(273,16,48,44,'♪',False,20)
button(329,16,44,44,'i',False,20)
rect(16,81,358,42,'#1b293d',10)
text(32,108,'20 linii • kaskady',13)
text(358,108,'Bonus 8–12',13,'#e5bc73',700,'end')
grid(21,147,348,291)
text(195,476,'Wybierz stawkę i zakręć.',15,'#c5cddd',400,'middle')
rect(16,498,358,73,'#1b293d',10)
text(30,520,'SALDO TESTOWE',10,'#abb9ce',700)
text(30,548,'1 000,00 USD',20,weight=700)
text(222,520,'WYPŁATA RUNDY',10,'#abb9ce',700)
text(222,548,'0,00 USD',20,weight=700)
text(20,597,'STAWKA',10,'#abb9ce',700)
button(16,609,44,56,'−',False,22)
text(112,643,'1,00 USD',16,weight=700,anchor='middle')
button(164,609,44,56,'+',False,22)
button(218,609,156,56,'ZAKRĘĆ',True,18)
button(16,684,169,44,'Zasady i wypłaty',False,13)
button(195,684,179,44,'Opcje',False,13)
text(195,755,'RTP 96% • maks. 5000×',12,'#abb9ce',400,'middle')
parts.append('</g>')

text(52,910,'01 / Mniej przewijania',18,'#182335',700)
text(52,939,'Plansza, saldo, stawka i obrót w jednym widoku.',15,'#635e56')
text(552,910,'02 / Czytelne wyniki',18,'#182335',700)
text(552,939,'Stawka i wypłata opisane osobno.',15,'#635e56')
text(1110,927,'03 / Własny charakter',18,'#182335',700)
text(1110,956,'Granat, złoto i geometria.',15,'#635e56')
text(52,1000,'MAKIETA STATYCZNA • nazwa i symbole robocze • kwoty przykładowe • bez zatwierdzenia prawnego lub platformowego',13,'#6f6557')
parts.append('</svg>')
(ROOT/'makieta-ux-v1.svg').write_text('\n'.join(parts),encoding='utf-8')
print('Makieta SVG gotowa.')

