import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
# paths.py liegt in src/lib — erreichbar sowohl aus src/ als auch aus src/lib und src/legacy
sys.path[:0] = [os.path.join(_HERE, 'lib'), os.path.join(os.path.dirname(_HERE), 'lib')]
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402,F401
import sqlite3, collections, os, sys
from pdfbase import *
from reportlab.lib.colors import HexColor
con=sqlite3.connect(DB); cur=con.cursor()
PHI=dict(cur.execute("SELECT name,knotenminute FROM itf_knotenzeit"))
KZ=dict(cur.execute("SELECT name,knotenzeit FROM itf_knotenzeit"))
OUTFILE=os.path.join(OUT, 'Kursbuch_Linienfahrplaene.pdf')
D=Doc(OUTFILE, landscape_=True, title='Systemtakt Deutschland – Kursbuch der Linienfahrpläne',
      subject='Integraler Taktfahrplan, Szenario A, Betriebszeit 5–23 Uhr')
c=D.c; W,H=D.W,D.H
LM,RM,TM=28,28,30

LINES=list(cur.execute("""SELECT DISTINCT z.linie, z.kategorie, z.produkt, z.betreiber,
   (SELECT bezeichnung FROM ziel_linie WHERE linie_key=z.linie) FROM fahrplan_zug z
   ORDER BY CASE z.kategorie WHEN 'ICE-Sprinter' THEN 1 WHEN 'ICE' THEN 2 ELSE 3 END, z.linie"""))
def trains(lin,r):
    return list(cur.execute("SELECT zug_id,abfahrt,ankunft,dauer FROM fahrplan_zug WHERE linie=? AND richtung=? ORDER BY abfahrt",(lin,r)))
def halts(zid):
    return list(cur.execute("SELECT station,an,ab,knoten FROM fahrplan_halt WHERE zug_id=? ORDER BY folge",(zid,)))

def head(lin,kat,bez,rich,von,nach,takt,dauer,nz,seite=None):
    col=CATCOL.get(kat,ICE)
    c.setFillColor(col); c.rect(LM,H-TM-20,7,20,fill=1,stroke=0)
    c.setFillColor(INK); c.setFont('Helvetica-Bold',15)
    c.drawString(LM+14,H-TM-15,lin)
    c.setFont('Helvetica',12); c.setFillColor(INK)
    c.drawString(LM+14+c.stringWidth(lin,'Helvetica-Bold',15)+12, H-TM-15, f"{von}  →  {nach}")
    c.setFont('Helvetica',8); c.setFillColor(MUT)
    txt=f"{kat} · Richtung {rich} · Takt {takt} min · Fahrzeit {dauer//60}:{dauer%60:02d} h · {nz} Züge/Tag"
    if bez: txt=f"{bez} · "+txt
    c.drawString(LM+14, H-TM-27, txt)
    c.setStrokeColor(col); c.setLineWidth(1); c.line(LM,H-TM-33,W-RM,H-TM-33)

PERPAGE=13
# --- Vorlauf: Seitenzahlen bestimmen
plan_pages=[]; pg=0
for lin,kat,prod,op,bez in LINES:
    for r in (1,2):
        tr=trains(lin,r)
        if not tr: continue
        nb=(len(tr)+PERPAGE-1)//PERPAGE
        h=halts(tr[0][0])
        plan_pages.append((lin,kat,r,h[0][0],h[-1][0],nb,pg))
        pg+=nb
TITEL=3   # Titel + zwei Erläuterungs-/Inhaltsseiten (Inhalt kann mehrseitig sein)
idx_rows=len(plan_pages)
INHALT=max(1,(idx_rows+47)//48)
VOR=2+INHALT
def titelseite():
    D.newpage()
    c.setFillColor(NAVY); c.rect(0,H-190,W,190,fill=1,stroke=0)
    c.setFillColor(WHITE); c.setFont('Helvetica-Bold',34)
    c.drawString(LM,H-96,'Kursbuch der Linienfahrpläne')
    c.setFont('Helvetica',15); c.setFillColor(HexColor('#B9C7DA'))
    c.drawString(LM,H-124,'Systemtakt Deutschland · Integraler Taktfahrplan für den Fernverkehr')
    c.setFont('Helvetica',10)
    c.drawString(LM,H-150,'Szenario A – Taktordnung · Betriebszeit 5 bis 23 Uhr · 20 Vollknoten · neubaufrei')
    c.setFillColor(INK); c.setFont('Helvetica',10)
    y=H-240
    for t in ['Dieses Kursbuch enthält den vollständigen Tagesfahrplan aller ICE-, ICE-Sprinter-, IC- und EC-Linien',
              'des entworfenen Systemtakts — jede Fahrt, jeder Halt, minutengenau.',
              '',
              'Der Fahrplan ist aus dem Knotenplan abgeleitet: An zwanzig Vollknoten treffen alle Züge innerhalb',
              'weniger Minuten ein und fahren gemeinsam wieder ab, sodass jeder Anschluss in jede Richtung besteht.',
              'Zwischen den Knoten fahren die Züge mit ihrer heutigen Fahrzeit zuzüglich der Reserve, die der Takt',
              'verlangt. Keine Strecke muss ausgebaut werden.']:
        c.drawString(LM,y,t); y-=15
    c.setFont('Helvetica',8); c.setFillColor(MUT)
    c.drawString(LM,60,'Datengrundlage: DELFI e. V. / gtfs.de, Fahrplan 22.08.–21.09.2026 · Knotenplan exakt gelöst (MILP, HiGHS)')
    c.drawString(LM,48,'Stand 23. August 2026 · Alle Zeiten sind Sollzeiten des Entwurfs, kein gültiger Fahrplan')
    D.footer('Systemtakt Deutschland · Kursbuch')
def legende():
    D.newpage()
    c.setFillColor(NAVY); c.setFont('Helvetica-Bold',18); c.drawString(LM,H-60,'So lesen Sie die Tabellen')
    c.setFillColor(INK); c.setFont('Helvetica',10); y=H-95
    for t in ['Jede Tabelle zeigt eine Linie in einer Richtung. Die Zeilen sind die Halte in der Reihenfolge der Fahrt,',
              'die Spalten sind die einzelnen Züge des Tages, von links nach rechts nach Abfahrtszeit geordnet.',
              '',
              '●   Vollknoten. Hier ist der Halt an die Knotenzeit gebunden; hinter dem Namen steht sie in grau.',
              '     Bei diesen Halten stehen zwei Zeiten übereinander: oben die Ankunft, unten (fett) die Abfahrt.',
              '',
              '     Durchgangshalte ohne Knotenbindung zeigen nur die Abfahrtszeit.',
              '',
              'Farben kennzeichnen die Produktebene: rot ICE-Sprinter, blau ICE, braun IC und EC.',
              'Zeiten nach Mitternacht sind als 24:xx und 25:xx angegeben.',
              '',
              'Der Fahrplan ist symmetrisch aufgebaut: In beiden Richtungen gilt dieselbe Knotenbindung.',
              'Die Ankunfts- und Abfahrtsfenster können sich je Richtung um wenige Minuten unterscheiden —',
              'das ist der Freiheitsgrad, der es erlaubt, beide Richtungen gleichzeitig an den Takt zu binden.']:
        c.drawString(LM,y,t); y-=15
    D.footer('Systemtakt Deutschland · Kursbuch')
def inhalt():
    rowsper=48
    for start in range(0,len(plan_pages),rowsper):
        D.newpage()
        c.setFillColor(NAVY); c.setFont('Helvetica-Bold',18); c.drawString(LM,H-60,'Inhalt')
        c.setFont('Helvetica-Bold',6.5); c.setFillColor(MUT)
        c.drawString(LM,H-82,'LINIE'); c.drawString(LM+158,H-82,'RELATION'); c.drawRightString(W-RM,H-82,'SEITE')
        c.setStrokeColor(LINE); c.line(LM,H-87,W-RM,H-87)
        y=H-100
        for (lin,kat,r,von,nach,nb,off) in plan_pages[start:start+rowsper]:
            c.setFillColor(CATCOL.get(kat,ICE)); c.setFont('Helvetica-Bold',7.5)
            c.drawString(LM,y,lin[:30])
            c.setFillColor(INK); c.setFont('Helvetica',7.5)
            c.drawString(LM+158,y,f"{von} → {nach}")
            c.setFillColor(MUT); c.setFont('Helvetica',7.5)
            c.drawRightString(W-RM,y,str(VOR+off+1))
            y-=9.4
        D.footer('Systemtakt Deutschland · Kursbuch')
titelseite(); legende(); inhalt()
toc=[]
for lin,kat,prod,op,bez in LINES:
    D.bookmark(lin,0)
    for r in (1,2):
        tr=trains(lin,r)
        if not tr: continue
        pattern=[h[0] for h in halts(tr[0][0])]
        rows=len(pattern)
        von,nach=pattern[0],pattern[-1]
        takt=list(cur.execute("SELECT takt FROM fahrplan_zug WHERE linie=? AND richtung=? LIMIT 1",(lin,r)))[0][0]
        blocks=[tr[i:i+PERPAGE] for i in range(0,len(tr),PERPAGE)]
        for bi,blk in enumerate(blocks):
            D.newpage()
            if bi==0: D.bookmark(f"{lin} · {von} → {nach}",1)
            head(lin,kat,bez,r,von,nach,takt,tr[0][3],len(tr))
            y0=H-TM-52
            colw=(W-LM-RM-150)/PERPAGE
            x0=LM+150
            c.setFont('Helvetica-Bold',6.5); c.setFillColor(MUT)
            c.drawString(LM,y0+10,'HALTESTELLE')
            for i in range(len(blk)):
                c.drawCentredString(x0+colw*(i+.5), y0+10, f"{i+1+bi*PERPAGE}")
            c.setStrokeColor(LINE); c.setLineWidth(.6); c.line(LM,y0+5,W-RM,y0+5)
            rh=max(11.5,min(21,(y0-55)/max(rows,1)))
            data=[halts(t[0]) for t in blk]
            for ri in range(rows):
                y=y0-6-rh*(ri+1)+3
                st=pattern[ri]; isk = st in PHI
                if ri%2==1:
                    c.setFillColor(ZEBRA); c.rect(LM,y-3,W-LM-RM,rh,fill=1,stroke=0)
                c.setFillColor(INK if isk else HexColor('#3A434D'))
                c.setFont('Helvetica-Bold' if isk else 'Helvetica', 7.4 if isk else 7)
                label=('● ' if isk else '   ')+st
                c.drawString(LM, y, label[:34])
                if isk:
                    c.setFont('Helvetica',5.6); c.setFillColor(MUT)
                    c.drawString(LM+c.stringWidth(label[:34],'Helvetica-Bold',7.4)+4, y, KZ[st])
                for ci,hh in enumerate(data):
                    if ri>=len(hh): continue
                    s,a,d,k=hh[ri]
                    c.setFont('Helvetica-Bold' if k else 'Helvetica',7)
                    c.setFillColor(INK)
                    if a is not None and d is not None and (d-a)>=4:
                        c.setFont('Helvetica',6.4)
                        c.drawCentredString(x0+colw*(ci+.5), y+3.4, hm(a))
                        c.setFont('Helvetica-Bold',6.8)
                        c.drawCentredString(x0+colw*(ci+.5), y-3.6, hm(d))
                    else:
                        c.drawCentredString(x0+colw*(ci+.5), y, hm(d if d is not None else a))
            c.setStrokeColor(LINE2); c.setLineWidth(.4)
            c.line(LM,y0-6-rh*rows,W-RM,y0-6-rh*rows)
            c.setFont('Helvetica',6); c.setFillColor(MUT)
            c.drawString(LM, y0-6-rh*rows-10,
              '●  Vollknoten mit Anschlussbindung · zweizeilige Zeiten = Ankunft / Abfahrt · Zeiten nach Mitternacht als 24:xx')
            D.footer(f"{lin}  {von} → {nach}   ({bi+1}/{len(blocks)})")
D.save()
print('Seiten',D.page, os.path.getsize(OUTFILE)//1024,'KB')
