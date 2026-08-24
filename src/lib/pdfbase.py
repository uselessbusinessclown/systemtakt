from reportlab.pdfgen import canvas as rlcanvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
NAVY=HexColor('#1F3864'); INK=HexColor('#14181E'); MUT=HexColor('#5A6472')
LINE=HexColor('#C9D2DA'); LINE2=HexColor('#E7EDF2'); ZEBRA=HexColor('#F2F5F8')
SPR=HexColor('#C31C26'); ICE=HexColor('#25648F'); IC=HexColor('#96692A')
WHITE=HexColor('#FFFFFF')
CATCOL={'ICE-Sprinter':SPR,'ICE':ICE,'IC/EC':IC}
def hm(t):
    if t is None: return ''
    return f"{(t//60)%24:02d}:{t%60:02d}"
class Doc:
    def __init__(self, path, landscape_=False, title='', subject=''):
        self.size = landscape(A4) if landscape_ else A4
        self.c = rlcanvas.Canvas(path, pagesize=self.size, pageCompression=1)
        self.c.setTitle(title); self.c.setSubject(subject); self.c.setAuthor('Systemtakt-Studie')
        self.W,self.H = self.size
        self.page=0; self.outline=[]
        self._toplevel=None
    def bookmark(self, title, level=0):
        key=f"bm{self.page}_{len(self.outline)}"
        self.c.bookmarkPage(key)
        self.c.addOutlineEntry(title[:90], key, level=level, closed=(level==0))
        self.outline.append((title,level,self.page))
    def footer(self, left, right=None):
        c=self.c; c.setFont('Helvetica',7); c.setFillColor(MUT)
        c.drawString(28, 20, left)
        c.drawRightString(self.W-28, 20, right or f"Seite {self.page}")
        c.setStrokeColor(LINE2); c.setLineWidth(.5); c.line(28,30,self.W-28,30)
    def newpage(self):
        if self.page>0: self.c.showPage()
        self.page+=1
    def save(self):
        self.c.showPage(); self.c.save()
