const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,WidthType,
  AlignmentType,BorderStyle,ShadingType,PageBreak,Footer,PageNumber,TableOfContents,
  LevelFormat,convertInchesToTwip}=require('docx');
const D=JSON.parse(fs.readFileSync('doc_data.json','utf8'));
const W=9360; // 6.5"
const FONT='Arial';
const NAVY='1F3864', LIGHT='EDF1F8', GREY='595959';

const P=(t,o={})=>new Paragraph({spacing:{after:o.after??120,before:o.before??0},alignment:o.align,
  children:[new TextRun({text:t,font:FONT,size:o.size??21,bold:o.bold,italics:o.it,color:o.color})]});
const H=(t,lvl)=>new Paragraph({heading:lvl,spacing:{before:lvl===HeadingLevel.HEADING_1?360:260,after:140},
  children:[new TextRun({text:t,font:FONT,bold:true,size:lvl===HeadingLevel.HEADING_1?30:lvl===HeadingLevel.HEADING_2?25:22,color:NAVY})]});
const BUL=(t)=>new Paragraph({bullet:{level:0},spacing:{after:80},
  children:[new TextRun({text:t,font:FONT,size:21})]});

function table(headers,rows,widths,opts={}){
  const cw=widths.map(w=>Math.round(W*w));
  const cell=(t,{b=false,bg=null,al=AlignmentType.LEFT,w})=>new TableCell({
    width:{size:w,type:WidthType.DXA},
    shading:bg?{type:ShadingType.CLEAR,fill:bg,color:'auto'}:undefined,
    margins:{top:60,bottom:60,left:90,right:90},
    children:[new Paragraph({alignment:al,spacing:{after:0},
      children:[new TextRun({text:String(t??''),font:FONT,size:opts.size??18,bold:b,color:b&&bg===NAVY?'FFFFFF':undefined})]})]});
  return new Table({
    columnWidths:cw, width:{size:W,type:WidthType.DXA},
    borders:{top:{style:BorderStyle.SINGLE,size:2,color:'BFBFBF'},bottom:{style:BorderStyle.SINGLE,size:2,color:'BFBFBF'},
      left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},
      insideHorizontal:{style:BorderStyle.SINGLE,size:1,color:'D9D9D9'},insideVertical:{style:BorderStyle.NONE}},
    rows:[new TableRow({tableHeader:true,children:headers.map((h,i)=>cell(h,{b:true,bg:NAVY,w:cw[i],
        al:(opts.right||[]).includes(i)?AlignmentType.RIGHT:AlignmentType.LEFT}))}),
      ...rows.map((r,ri)=>new TableRow({children:r.map((v,i)=>cell(v,{w:cw[i],bg:ri%2?LIGHT:null,
        al:(opts.right||[]).includes(i)?AlignmentType.RIGHT:AlignmentType.LEFT}))}))]});
}
const SP=()=>new Paragraph({spacing:{after:160},children:[]});
const CAP=(t)=>new Paragraph({spacing:{before:60,after:220},children:[new TextRun({text:t,font:FONT,size:17,italics:true,color:GREY})]});

const body=[];
// ---------- Titel ----------
body.push(new Paragraph({spacing:{before:1400,after:120},children:[new TextRun({text:'Systemtakt für den deutschen Schienenfernverkehr',font:FONT,size:48,bold:true,color:NAVY})]}));
body.push(new Paragraph({spacing:{after:400},children:[new TextRun({text:'Datenbank des ICE- und IC-Netzes und Entwurf eines integralen Taktfahrplans nach Schweizer Vorbild',font:FONT,size:26,color:GREY})]}));
body.push(P('Datengrundlage: Fahrplan 22. August bis 21. September 2026 (DELFI e. V. / gtfs.de, Feed „Fernverkehr Deutschland“)',{size:20,color:GREY}));
body.push(P('Bearbeitungsstand: 23. August 2026 · Fassung 4: 20 Vollknoten, beidseitige Knotenbindung, vollständiger Fahrplan',{size:20,color:GREY}));
body.push(P('Prioritätenordnung: ICE-Sprinter vor ICE vor IC/EC',{size:20,color:GREY,after:600}));

body.push(H('Kurzfassung',HeadingLevel.HEADING_1));
body.push(P('Der deutsche Schienenfernverkehr fährt heute rund 1.090 Züge je Werktag, bedient 290 Bahnhöfe in Deutschland und 277 im Ausland und ist bereits weitgehend getaktet: 83 Prozent aller Abfahrten an den Netzknoten folgen einem erkennbaren Stunden- oder Zweistundentakt. Was fehlt, ist nicht der Takt, sondern die Abstimmung der Takte untereinander — der Schritt vom Linientakt zum integralen Taktfahrplan.'));
body.push(P('Diese Untersuchung baut zunächst eine vollständige, auswertbare Datenbank des Angebots auf: alle Zugfahrten, alle Linien, alle Bahnhöfe, alle Streckenkanten mit ihren tatsächlichen Fahrzeiten. Auf dieser Grundlage wird für 64 Netzknoten eine Knotenminute im 30-Minuten-Raster berechnet, und zwar so, dass die Summe der gewichteten Fahrzeitabweichungen minimal wird. Sprinterfahrten gehen dreifach, ICE-Fahrten zweifach und IC-Fahrten einfach in die Gewichtung ein; die vom Nutzer geforderte Prioritätenordnung ist damit unmittelbar in der Zielfunktion verankert.'));
body.push(P('Das Ergebnis ist deutlicher, als zu erwarten war: Der Taktfahrplan kommt vollständig ohne Neubaumaßnahmen aus. Es wurde die Nebenbedingung gesetzt, dass keine einzige Netzkante schneller befahren werden darf, als sie heute schon befahren wird — der Takt entsteht also allein aus Fahrzeitzuschlägen. Unter dieser Bedingung liegt die mittlere Fahrzeitreserve bei 6,6 Prozent, unterhalb des schweizerischen Zielwerts von sieben Prozent. Kein Kilometer Neubaustrecke, keine Ertüchtigung, keine Signaltechnik ist dafür erforderlich.'));
body.push(P('Der entscheidende Stellhebel ist die Zahl der Vollknoten. Jeder Bahnhof, an dem alle Züge in ein gemeinsames Zeitfenster gezwungen werden, kauft Anschlüsse mit Fahrzeit. Rechnet man Knotenmengen von sechzehn bis vierundsechzig durch, kostet jeder zusätzliche Vollknoten rund eine halbe Minute mittlere Reisezeit. Gewählt wurden zwanzig; die durchschnittliche Fahrt verlängert sich damit um 16,6 Minuten gegenüber heute, gegen 38 Minuten bei vierundsechzig Knoten. Alle übrigen 246 Fernverkehrsbahnhöfe sind Durchgangshalte ohne Knotenbindung.'));
body.push(P('Aus diesem Knotenplan ist ein vollständiger Tagesfahrplan abgeleitet: 1.700 Züge, 12.876 Halte, Betriebszeit fünf bis dreiundzwanzig Uhr. Er liegt als Kursbuch der Linienfahrpläne mit 168 Linienrichtungen und als Band der Bahnhofsfahrpläne mit 266 Aushangtafeln bei — minutengenau für jede Fahrt und jeden Halt.'));
body.push(P('Der Knotenplan ist nicht mehr geschätzt, sondern bewiesen. Das Problem wurde als gemischt-ganzzahliges Programm formuliert und mit dem Solver HiGHS exakt gelöst; es gibt keine bessere Zuordnung von Knotenminuten. Der Vergleich mit einer Variante, in der Beschleunigungen um bis zu drei Minuten erlaubt sind, zeigt zugleich, wie wenig Ausbau überhaupt bringen würde: Die Zielfunktion verbessert sich um elf Prozent, die mittlere Reserve um 0,7 Prozentpunkte. Für einen Fahrplan, der ohne Bagger auskommt, ist das ein sehr geringer Preis.'));
body.push(P('Die eigentliche Hürde liegt in den Knoten selbst. Frankfurt Hauptbahnhof, Hannover und München müssten in jedem Knotenfenster rund neun Fernzüge gleichzeitig abfertigen; das entspricht etwa elf durchgehend für den Fernverkehr reservierten Bahnsteiggleisen. Frankfurt als Kopfbahnhof kann das ohne den Fernbahntunnel nicht leisten. Der Engpass des integralen Taktfahrplans ist damit klar benannt: nicht die freie Strecke, sondern der Bahnhof.'));
body.push(P('Kapitel 12 prüft deshalb gesondert, ob sich der Frankfurter Engpass durch Verlagerung an den Flughafen-Fernbahnhof lösen lässt. Das Ergebnis ist eindeutig negativ: Die Sprinter allein tragen nur ein Zehntel der Gleisbelegung des Hauptbahnhofs, während die wendenden Züge fast 78 Prozent ausmachen. Nicht der Standort ist das Problem, sondern das Kopfmachen.'));
body.push(P('Auf die Frage, ob eine Zentrierung des Takts auf einen besonders zentralen Großbahnhof hilft, gibt Kapitel 15 eine zweigeteilte Antwort. Die Wahl des Ankerbahnhofs — welche Station auf :00 gelegt wird — ist mathematisch wirkungslos, weil sie den Fahrplan nur dreht. Wirksam ist dagegen, einen Knoten in der Optimierung höher zu gewichten: Frankfurt Hauptbahnhof ist dafür der beste Kandidat und verbessert sich dabei um drei Prozentpunkte, ohne dass das übrige Netz leidet.'));
body.push(P('Für das Angebot werden zwei Szenarien gerechnet. Szenario A („Taktordnung“) bringt das heutige Angebot auf die jeweils nächstgelegene saubere Taktstufe und kostet 17,8 Prozent zusätzliche Zugkilometer. Szenario B („Vollausbau“) hebt jede Linie auf mindestens Zweistundentakt und die Hauptachsen auf 30 Minuten; das verdoppelt die Betriebsleistung nahezu. Szenario A ist der realistische erste Schritt, Szenario B das Zielbild.'));

body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('Inhalt',HeadingLevel.HEADING_1));
body.push(new TableOfContents('Inhalt',{hyperlink:true,headingStyleRange:'1-2'}));
body.push(new Paragraph({children:[new PageBreak()]}));

// ---------- 1 ----------
body.push(H('1  Datengrundlage und Methodik',HeadingLevel.HEADING_1));
body.push(H('1.1  Quelle und Abdeckung',HeadingLevel.HEADING_2));
body.push(P('Grundlage ist der offene GTFS-Datensatz „Fernverkehr Deutschland“ von gtfs.de, der die von DELFI e. V. bereitgestellten Solldaten aller Fernverkehrszüge mit Halt in Deutschland enthält. Der ausgewertete Fahrplanausschnitt umfasst den Zeitraum vom 22. August bis zum 21. September 2026, also einen vollen Monat mit allen Wochentagsvarianten und Verkehrstagsausnahmen.'));
body.push(P('Der Datensatz umfasst 5.589 unterschiedliche Zugtrassen, 54.928 Halte, 13 Verkehrsunternehmen und 567 Bahnhöfe. Auf einen typischen Werktag entfallen daraus rund 1.090 Zugfahrten.'));
body.push(SP());
body.push(table(['Produktklasse','Fahrten je Tag','Trassen im Datensatz'],
  D.kat.map(r=>[r.kategorie==='ICE-SPRINTER'?'ICE-Sprinter':r.kategorie==='SONSTIGE'?'Sonstige (RJ, EN)':r.kategorie,r.t,r.n]),
  [0.4,0.3,0.3],{right:[1,2]}));
body.push(CAP('Tabelle 1: Fernverkehrsangebot nach Produktklasse, Durchschnitt über 31 Tage.'));
body.push(table(['Land','Bahnhöfe'],D.laender.map(r=>[r.land==='Germany'?'Deutschland':r.land==='Poland'?'Polen':r.land==='Austria'?'Österreich':r.land==='Switzerland'?'Schweiz':r.land==='Czechia'?'Tschechien':r.land==='Denmark'?'Dänemark':r.land==='Hungary'?'Ungarn':r.land==='Netherlands'?'Niederlande':r.land,r.n]),[0.6,0.4],{right:[1]}));
body.push(CAP('Tabelle 2: Von ICE, IC und EC bediente Bahnhöfe nach Land.'));

body.push(H('1.2  Aufbau der Datenbank',HeadingLevel.HEADING_2));
body.push(P('Die Rohdaten wurden in eine SQLite-Datenbank überführt und um abgeleitete Ebenen ergänzt. Die Bahnhofsdatenbank fasst die Bahnsteig-Haltepunkte des Rohdatensatzes zu 567 Betriebsstellen zusammen, ordnet jeder über eine Punkt-in-Polygon-Prüfung Staat und Bundesland zu, normalisiert die Namen und gruppiert die Bahnhöfe zusätzlich zu Städten, damit Berlin Hauptbahnhof, Südkreuz, Spandau und Gesundbrunnen bei Relationsauswertungen als ein Ort gelten.'));
body.push(P('Die Liniendatenbank leitet aus den Zugfahrten 89 Linien ab — 50 im ICE-Segment, 27 im IC- und EC-Segment und 12 sonstige — jeweils mit dem häufigsten Laufweg, der typischen Fahrzeit, der Bedienhäufigkeit und der Haltefolge. Die Kantendatenbank enthält für 1.044 unmittelbar benachbarte Bahnhofspaare die kürzeste, mittlere und längste beobachtete Fahrzeit sowie die Belastung.'));

body.push(H('1.3  Identifikation der ICE-Sprinter',HeadingLevel.HEADING_2));
body.push(P('Der offene Datensatz enthält keine Zugnummern; das Merkmal „Sprinter“ ist darin nicht codiert. Die Zuordnung erfolgt deshalb zweistufig. Erstens werden die sieben von der DB vermarkteten Sprinter-Korridore als Städterelationen hinterlegt. Zweitens werden innerhalb jedes Korridors die Trassen nach Fahrzeit sortiert und so viele als Sprinter markiert, bis die auf bahn.de veröffentlichte Angebotsdichte erreicht ist. Das Verfahren reproduziert die offiziellen Frequenzen auf ein bis zwei Fahrten je Tag genau und ergibt 72 Sprinterfahrten je Tag.'));
body.push(P('Diese Zuordnung ist eine begründete Rekonstruktion, keine amtliche Kennzeichnung. Für die Taktplanung ist das unerheblich, weil dort nicht die einzelne Fahrt, sondern der Korridor die Priorität trägt.',{it:true}));

body.push(H('1.4  Das Optimierungsverfahren',HeadingLevel.HEADING_2));
body.push(P('Die Knotenzeiten werden nicht gesetzt, sondern berechnet. Jedem Knoten i wird eine Knotenminute φ(i) im Bereich von 0 bis 29 zugewiesen. Für eine Kante zwischen den Knoten i und j mit der technischen Mindestfahrzeit T ist die Taktbedingung erfüllt, wenn φ(j) − φ(i) − T − 6 ein Vielfaches von 30 Minuten ist; die sechs Minuten sind der Knotenaufenthalt. Die verbleibende Differenz muss entweder als Fahrzeitzuschlag hingenommen oder durch Beschleunigung beseitigt werden.'));
body.push(P('Die Zielfunktion bestraft Zuschläge mild, solange sie im Bereich der ohnehin nötigen Fahrzeitreserve von sieben Prozent bleiben, darüber hinaus deutlich stärker. Jede Kante geht mit dem Gewicht 3 × Sprinterfahrten + 2 × ICE-Fahrten + 1 × IC-Fahrten je Tag ein; die geforderte Prioritätenordnung steckt damit unmittelbar in der Zielfunktion.'));
body.push(P('Im Grundfall dieses Berichts ist eine Fahrzeitverkürzung unter die heutige Bestzeit gar nicht zugelassen — der Takt muss ohne Neubaumaßnahmen auskommen. Damit wird die Zielfunktion stückweise linear, und das Problem lässt sich als gemischt-ganzzahliges Programm exakt formulieren: Ganzzahlige Variablen sind die 64 Knotenminuten und je Kante ein Periodenzähler; die Nichtlinearität der Reservestrafe wird über eine Hilfsvariable linearisiert. Gelöst wird mit HiGHS. Der Solver meldet Optimalität — die ausgewiesenen Knotenzeiten sind also nicht die beste gefundene, sondern die beweisbar beste Lösung.'));
body.push(P('Eine zweite Verschärfung betrifft die Fahrtrichtung. Ein Knoten funktioniert nur, wenn die Bindung in beiden Richtungen gilt — sonst hat der Reisende in der Gegenrichtung keinen Anschluss. Fordert man Ankunft und Abfahrt auf dieselbe Minute in beiden Richtungen, so ist das nur erfüllbar, wenn alle Knotenminuten auf einem Viertelstundenraster liegen; diese Variante kostet nach Abschnitt 15.4 ein Drittel der Fahrzeit als Reserve. Die Lösung sind schmale Zeitfenster: Ankunft zwei bis fünf Minuten vor der Knotenminute, Abfahrt zwei bis fünf Minuten danach, je Richtung getrennt wählbar. Damit ist die beidseitige Bindung erfüllbar, ohne das Raster zu vergröbern. Die Fensterlagen sind Teil des Optimierungsproblems.'));
body.push(P('Das ist keine akademische Feinheit. Frühere Fassungen dieses Berichts nutzten simuliertes Ausglühen und lieferten je nach Zufallsstartwert Lösungen, die bis zu 18 Prozent schlechter waren als das Optimum — und die deshalb fünf Kanten als ausbaubedürftig auswiesen, die es in Wahrheit nicht sind. Der scheinbare Infrastrukturbedarf des Konzepts war ein Artefakt der Lösungsmethode.',{it:true}));
body.push(P('Die Lösung ist nur bis auf eine gemeinsame Verschiebung eindeutig. Als Anker wurde Berlin Hauptbahnhof auf die Knotenminute :00 gelegt; alle anderen Knotenzeiten verschieben sich mit, wenn ein anderer Anker gewünscht wird.'));

// ---------- 2 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('2  Befund: das heutige Angebot',HeadingLevel.HEADING_1));
body.push(H('2.1  Die Taktqualität ist besser als ihr Ruf',HeadingLevel.HEADING_2));
body.push(P('Für jede Kombination aus Linie, Knoten und Fahrtrichtung wurde die Verteilung der Abfahrtsminuten über den Monat ausgewertet. Das Ergebnis widerlegt die verbreitete Annahme, der deutsche Fernverkehr sei unvertaktet.'));
body.push(SP());
body.push(table(['Bewertung','Fälle','Abfahrten je Tag'],D.takt.map(r=>[r.takt_bewertung,r.n,r.f]),[0.5,0.25,0.25],{right:[1,2]}));
body.push(CAP('Tabelle 3: Taktqualität der Linien an den Netzknoten. „60-min-Takt stabil“ bedeutet, dass mindestens 60 Prozent der Abfahrten auf dieselbe Minute fallen.'));
body.push(P('83 Prozent aller Abfahrten liegen auf einer stabilen Stundentaktlage, weitere 13 Prozent folgen einem Zweistundentakt mit zwei alternierenden Lagen. Nur knapp sechs Prozent sind systemlos. Das Problem des deutschen Fernverkehrs ist also nicht der fehlende Takt der einzelnen Linie, sondern die fehlende Verabredung der Linien untereinander: die Taktlagen sind historisch gewachsen und nicht auf gemeinsame Knotenzeiten hin konstruiert.'));

body.push(H('2.2  Die Netzknoten',HeadingLevel.HEADING_2));
body.push(SP());
body.push(table(['Rang','Bahnhof','Bundesland','Halte/Tag','ICE','Sprinter','IC/EC','Linien'],
  D.bhf.slice(0,22).map(r=>[r.rang,r.name,r.bundesland??'',r.halte_tag,r.halte_ice,r.halte_sprinter,r.halte_ic,r.linien]),
  [0.07,0.26,0.19,0.11,0.09,0.11,0.09,0.08],{right:[0,3,4,5,6,7],size:17}));
body.push(CAP('Tabelle 4: Die 22 meistbedienten Fernverkehrsbahnhöfe Deutschlands, Halte je Tag über alle Richtungen.'));
body.push(P('Frankfurt, München, Hannover, Berlin und Köln bilden mit jeweils rund 200 Halten am Tag die Spitzengruppe. Auffällig ist die ungleiche Verteilung der Sprinterhalte: Berlin Hauptbahnhof und Südkreuz sehen zusammen über hundert Sprinterhalte am Tag, Mannheim keinen einzigen. Das Sprintersystem ist heute kein Netz, sondern ein Bündel von Einzelrelationen mit Berlin im Mittelpunkt.'));

// ---------- 3 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('3  Zielsystem: der integrale Taktfahrplan',HeadingLevel.HEADING_1));
body.push(H('3.1  Die fünf Grundregeln',HeadingLevel.HEADING_2));
[['Symmetrie','Der Fahrplan ist um die Minute 0 symmetrisch. Fährt ein Zug in einer Richtung um :17 ab, fährt der Gegenzug um :43 ab. Das ist die Voraussetzung dafür, dass ein Anschluss, der in einer Richtung funktioniert, auch in der Gegenrichtung funktioniert.'],
 ['Knotenzeit','Jeder Knoten hat eine feste Minute φ. Alle Züge treffen um φ − 3 ein und fahren um φ + 3 wieder ab. Sechs Minuten reichen für den Umstieg am selben Bahnsteig und über eine Unterführung; wo längere Wege bestehen, ist der Bahnhof umzubauen, nicht die Knotenzeit zu dehnen.'],
 ['Kantenzeit','Die Fahrzeit zwischen zwei Knoten ist kein Ergebnis, sondern eine Vorgabe: sie muss ein Vielfaches von 30 Minuten minus sechs Minuten Knotenaufenthalt betragen. Ist die Strecke zu langsam, wird sie ausgebaut. Ist sie zu schnell, wird die Reserve als Pufferzeit verbucht — nicht als Beschleunigungsversprechen.'],
 ['Reserve','Die Sollreserve beträgt sieben Prozent der reinen Fahrzeit. Weniger macht den Fahrplan anfällig, mehr verschenkt Reisezeit und Fahrzeugumläufe.'],
 ['Vorrang','Die Trassenkonstruktion folgt strikt der Reihenfolge Sprinter, ICE, IC. Wer später kommt, weicht.']]
 .forEach(([t,x],i)=>{body.push(P(`Regel ${i+1} — ${t}`,{bold:true,after:40})); body.push(P(x));});

body.push(H('3.2  Die Prioritätenordnung im Detail',HeadingLevel.HEADING_2));
body.push(P('Die geforderte Rangfolge Sprinter vor ICE vor IC wird an vier Stellen wirksam und ist damit überprüfbar:'));
body.push(BUL('In der Zielfunktion. Jede Sprinterfahrt zählt dreifach, jede ICE-Fahrt zweifach, jede IC-Fahrt einfach. Wo Kanten miteinander konkurrieren, setzt sich die Kante mit dem höheren Sprinter- und ICE-Anteil durch.'));
body.push(BUL('In der Fahrzeitreserve. Ebene 1 erhält höchstens fünf Prozent Reserve, Ebene 2 sieben Prozent, Ebene 3 mindestens sieben Prozent. Die systembedingten Wartezeiten des Taktes werden also vom IC absorbiert, nicht vom Sprinter.'));
body.push(BUL('Im Knoten. Kollidieren zwei Züge im selben Knotenfenster um dasselbe Gleis, erhält die höhere Ebene das Gleis mit dem kürzesten Umsteigeweg und der besten Bahnsteiglänge. Der IC weicht auf ein Außengleis aus.'));
body.push(BUL('In der Anschlusssicherung. Ein verspäteter IC hält den ICE bis zu drei Minuten, ein verspäteter ICE hält den Sprinter nicht. Der Sprinter ist das Rückgrat der Pünktlichkeit und darf nicht Teil der Verspätungskette werden.'));
body.push(P('Ergänzend gilt eine Haltepolitik-Regel: In Ebene 1 wird ein zusätzlicher Systemhalt nur aufgenommen, wenn er die Knotenlage an beiden Endknoten unverändert lässt. Ein Sprinter, der wegen eines Zwischenhalts eine halbe Stunde später ankommt, ist kein Sprinter mehr.'));

// ---------- 4 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('4  Der Knotenplan',HeadingLevel.HEADING_1));
body.push(P('Die folgende Tabelle enthält das Kernergebnis der Optimierung: für jeden der zwanzig Vollknoten die berechnete Knotenminute sowie die daraus folgenden Ankunfts- und Abfahrtsfenster, getrennt nach Fahrtrichtung. Der Anker ist Berlin Hauptbahnhof mit :00. Die Spalte „Gewicht“ gibt die nach Produktpriorität gewichtete Zahl der täglichen Fahrten über die Kanten des Knotens an.'));
body.push(SP());
body.push(table(['Knoten','Knotenzeit','Ankunft','Abfahrt','Kanten','Gewicht'],
  D.knoten.map(r=>[r.name,r.knotenzeit,r.ankunft,r.abfahrt,r.grad,Math.round(r.gewicht)]),
  [0.30,0.16,0.16,0.16,0.10,0.12],{right:[4,5],size:16}));
body.push(CAP('Tabelle 5: Berechnete Knotenzeiten der zwanzig Vollknoten im 30-Minuten-Raster, Anker Berlin Hauptbahnhof = :00. Ri1 und Ri2 sind die beiden Fahrtrichtungen.'));
body.push(P('Die zwanzig Knoten bilden drei Taktfamilien. Berlin, Dortmund, Leipzig und Mannheim liegen auf :00; Duisburg, Frankfurt, Fulda, Bremen, Dresden, Hamburg, Münster, Erfurt und Stuttgart auf :13 bis :17; München, Nürnberg, Karlsruhe, Hannover, Kassel-Wilhelmshöhe, Köln und Würzburg auf :24 bis :29. Diese Gruppierung ist nicht gesetzt, sondern Ergebnis der Optimierung — sie spiegelt die Fahrzeiten zwischen den Knoten wider.'));
body.push(P('Wichtig ist, was in dieser Tabelle nicht steht: keine einzige Knotenzeit erzwingt eine Fahrzeitverkürzung. Alle 68 Netzkanten werden in beiden Richtungen mit ihrer heutigen Systemfahrzeit oder langsamer befahren.'));

// ---------- 5 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('5  Der Kantenplan',HeadingLevel.HEADING_1));
body.push(H('5.1  Wie gut passt das Netz in das Raster?',HeadingLevel.HEADING_2));
body.push(SP());
body.push(table(['Kategorie','Kanten','Gewicht','Anteil am gewichteten Verkehr'],
  D.resklassen.map(r=>[r.k,r.n,r.g,r.p+' %']),[0.44,0.14,0.16,0.26],{right:[1,2,3]}));
body.push(CAP('Tabelle 6: Passung der 173 Netzkanten in das 30-Minuten-Raster.'));
body.push(P('Vier Fünftel des gewichteten Verkehrs lassen sich mit einer Fahrzeitreserve von höchstens vierzehn Prozent in das Raster einpassen, 60 Prozent sogar innerhalb der schweizerischen Sollmarke von sieben Prozent — und das, obwohl keine einzige Kante beschleunigt werden darf. Die deutschen Fernverkehrsstrecken sind in ihren Fahrzeiten bereits taktfähig. Der integrale Taktfahrplan scheitert nicht an der freien Strecke.'));

body.push(H('5.2  Die Hauptkanten im Soll',HeadingLevel.HEADING_2));
body.push(SP());
body.push(table(['Von','Nach','System-\nfahrzeit','Soll A→B','Soll B→A','Reserve A→B','Reserve B→A','Spr.','ICE','IC'],
  D.kanten.map(r=>[r.a,r.b,r.t_technisch,r.t_soll_r1,r.t_soll_r2,r.reserve_r1+' %',r.reserve_r2+' %',
    r.f_sprinter.toFixed(1),r.f_ice.toFixed(1),r.f_ic.toFixed(1)]),
  [0.18,0.18,0.10,0.09,0.09,0.10,0.10,0.06,0.05,0.05],{right:[2,3,4,5,6,7,8,9],size:14}));
body.push(CAP('Tabelle 7: Die 30 verkehrsstärksten Netzkanten. Systemfahrzeit ist die Zeit, die die dort verkehrenden Linien heute brauchen; die Soll-Zeiten unterscheiden sich je Richtung, weil die Knotenfenster je Richtung anders liegen dürfen.'));

body.push(H('5.3  Was Ausbau überhaupt brächte',HeadingLevel.HEADING_2));
body.push(P('Der ausgewiesene Plan verlangt keinerlei Beschleunigung. Um den Verzicht zu bewerten, wurde dieselbe Optimierung ein zweites Mal exakt gelöst — diesmal mit der Erlaubnis, einzelne Kanten um bis zu drei Minuten unter die heutige Bestzeit zu beschleunigen, bewertet mit dem vierfachen Kostensatz eines Zuschlags.'));
body.push(SP());
body.push(table(['Variante','Verfahren','Kanten mit Verkürzung','Zielfunktion je Gewicht','Sollband','Ø Reserve'],
  D.taktvar.map(r=>[r.variante,r.verfahren.replace(' (MILP, HiGHS, Optimalität bewiesen)',' – Optimalität bewiesen'),
    r.kanten_mit_beschleunigung,r.kosten_je_gewicht,r.sollband_pct+' %',r.mittlere_reserve_pct+' %']),
  [0.20,0.28,0.14,0.14,0.11,0.13],{right:[2,3,4,5],size:16}));
body.push(CAP('Tabelle 8: Taktvarianten im Vergleich. Die Zielfunktion je Gewichtseinheit ist das Maß der Taktqualität; kleiner ist besser.'));
body.push(P('Elf Kanten würden von einer Beschleunigung Gebrauch machen, meist um ein bis drei Minuten — an der Spitze Frankfurt–Kassel-Wilhelmshöhe (eine Minute), Karlsruhe–Freiburg und Köln–Duisburg (je drei Minuten). Der Gesamteffekt bleibt klein: 0,7 Prozentpunkte weniger mittlere Reserve. Für eine Reise von vier Stunden sind das anderthalb Minuten.'));
body.push(P('Noch aufschlussreicher ist die dritte Rechnung. Verdoppelt man den zulässigen Ausbau auf sechs Minuten je Kante, sinkt die mittlere Reserve nur noch von 7,01 auf 6,97 Prozent — vier Hundertstel eines Prozentpunkts. Der Nutzen von Streckenausbau für die Taktbildung ist damit nach wenigen Minuten erschöpft. Das ist ein starkes Argument gegen ein Ausbauprogramm, das mit dem Deutschlandtakt begründet wird: Was den Takt trägt, ist die Ordnung der Fahrplanlagen, nicht die Geschwindigkeit.'));

body.push(H('5.4  Wo das Raster Zeit kostet',HeadingLevel.HEADING_2));
body.push(P('Das Spiegelbild sind Kanten, deren Fahrzeit deutlich gedehnt werden müsste, um in das Raster zu passen. Sie treten typischerweise dort auf, wo zwei Knoten dicht beieinanderliegen.'));
body.push(SP());
body.push(table(['Von','Nach','Systemfahrzeit','Soll A→B','Soll B→A','Reserve','Gewicht'],
  D.reserve.map(r=>[r.a,r.b,r.t_technisch+' min',r.t_soll_r1+' min',r.t_soll_r2+' min',
    Math.max(r.reserve_r1,r.reserve_r2)+' %',Math.round(r.gewicht)]),
  [0.21,0.21,0.14,0.11,0.11,0.11,0.11],{right:[2,3,4,5,6]}));
body.push(CAP('Tabelle 9: Kanten mit übermäßiger Fahrzeitreserve.'));
body.push(P('Mit nur zwanzig Vollknoten sind solche Fälle selten geworden: Nur noch vier Kanten überschreiten in einer Richtung fünfundzwanzig Prozent Reserve, und sie tragen wenig Verkehr. Die Lösung bleibt dieselbe wie zuvor — die Reserve produktiv machen, indem dort ein zusätzlicher Systemhalt eingelegt wird, oder einen der beiden Endknoten zum Durchgangshalt abstufen. Der zweite Weg ist genau das, was der Übergang von vierundsechzig auf zwanzig Vollknoten bereits getan hat.'));

// ---------- 6 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('6  Ebene 1: das Sprintersystem',HeadingLevel.HEADING_1));
body.push(P('Die sieben von der DB vermarkteten Sprinter-Korridore bilden die oberste Ebene. Sie bestimmen die Knotenzeiten der Metropolen, sie erhalten die knappste Fahrzeitreserve und sie werden als erste in den Fahrplan konstruiert.'));
body.push(SP());
body.push(table(['Korridor','Relation','Strecken-km','Fahrten/Tag heute','Ziel-Takt','Ziel Fahrten/Ri'],
  D.sprkorr.map(r=>[r.korridor,r.relation,Math.round(r.km),r.fahrten_tag_ist,r.takt_ziel,r.richtungsfahrten_ziel]),
  [0.10,0.36,0.13,0.15,0.16,0.10],{right:[2,3,5],size:16}));
body.push(CAP('Tabelle 10: Die sieben Sprinter-Korridore. Zielangebot: Zweistundentakt ganztags mit stündlicher Verdichtung in der Hauptverkehrszeit.'));

body.push(H('6.1  Fahrplanlage und Soll-Fahrzeit',HeadingLevel.HEADING_2));
body.push(P('Aus den berechneten Knotenzeiten folgen für jeden Korridor eine feste Abfahrts- und Ankunftsminute und damit eine exakte Soll-Fahrzeit. Sie ist die eigentliche Planungsvorgabe.'));
body.push(SP());
body.push(table(['Korridor','Relation','ab','an','heute best','Soll','Δ','Bewertung'],
  D.sprinter.map(r=>[r.korridor,r.relation,r.abfahrt,r.ankunft,r.t_heute_best+' min',r.t_soll+' min',
    (r.delta>0?'+':'')+r.delta,r.bewertung]),
  [0.08,0.24,0.06,0.06,0.11,0.09,0.06,0.30],{right:[4,5,6],size:15}));
body.push(CAP('Tabelle 11: Fahrplanlagen und Soll-Fahrzeiten der Sprinter-Korridore.'));
body.push(P('Das wichtigste Ergebnis: Kein einziger Sprinter-Korridor verlangt eine Fahrzeitverkürzung. Hamburg–Frankfurt fügt sich mit 3:34 sogar ohne jeden Zuschlag ein — die heutige Bestzeit ist bereits taktkonform. Berlin–Köln kommt mit drei Minuten Zuschlag aus. Das Sprintersystem ist vollständig taktfähig, ohne dass ein Meter Strecke ausgebaut werden müsste.'));
body.push(P('Berlin–München wird mit 4:07 zwölf Minuten langsamer als heute, Berlin–Frankfurt mit 4:11 neunzehn Minuten. Das wirkt paradox, ist aber der Preis für saubere Anschlüsse — die zusätzlichen Minuten kauft man mit Umsteigeverbindungen in München, Nürnberg, Erfurt, Frankfurt und Berlin, die heute nicht bestehen. Wer die knappen vier Stunden verteidigen will, muss stattdessen die Knotenzeit eines Endknotens verschieben und dafür an anderer Stelle zahlen. Genau diese Abwägung macht ein integraler Taktfahrplan sichtbar.'));
body.push(P('Damit die Rechnung aufgeht, gilt für Ebene 1 eine zusätzliche Regel: Ein Sprinter ist nur an seinen beiden Metropolknoten taktgebunden, nicht an den Knoten dazwischen. Bindet man ihn auch an die Zwischenknoten, verliert er seinen Vorsprung — für Berlin–Köln ergäbe die knotenweise Einpassung 5:26 statt 4:22.'));

body.push(H('6.2  Überholungen',HeadingLevel.HEADING_2));
body.push(P('Ein Sprinter, der eine Achse schneller befährt als der taktgebundene ICE, muss ihn überholen. Die Zahl der nötigen Überholungen ergibt sich aus dem Fahrzeitgewinn geteilt durch die Taktzeit der überholten Ebene.'));
body.push(SP());
body.push(table(['Relation','Sprinter','ICE gleicher Laufweg','Gewinn','Überholungen bei 30-min-Takt'],
  D.ueberhol.map(r=>[r.relation,r.t_sprinter+' min',r.t_ice+' min',r.zeitgewinn+' min',r.ueberholungen_30min]),
  [0.28,0.16,0.24,0.14,0.18],{right:[1,2,3,4]}));
body.push(CAP('Tabelle 12: Überholbedarf, verglichen mit dem schnellsten ICE auf identischem Laufweg.'));
body.push(P('Das Ergebnis relativiert eine verbreitete Sorge. Auf streckengleichen Laufwegen ist der Sprintervorsprung klein: Berlin–Köln vier Minuten, Berlin–München neunundvierzig. Nur die Berlin–München-Achse braucht überhaupt eine Überholung, und dafür genügt eine einzige Überholstelle. Die großen Reisezeitunterschiede im heutigen Netz entstehen nicht durch Haltverzicht, sondern durch Laufwegwahl — der langsame Zug von Berlin nach München fährt über Frankfurt, nicht über Erfurt. Ein integraler Taktfahrplan, der die schnelle Route stündlich bedient, macht einen Teil des Sprinterangebots schlicht überflüssig.'));

// ---------- 7 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('7  Ebene 2: das ICE-Grundnetz',HeadingLevel.HEADING_1));
body.push(P('Die zweite Ebene füllt das 30-Minuten-Raster. Ausgangspunkt ist das heutige Linienbild; jede Linie wird auf eine saubere Taktstufe gebracht. Szenario A wählt die nächstgelegene Stufe und bleibt damit nahe am heutigen Angebotsvolumen, Szenario B hebt jede Linie auf mindestens Zweistundentakt und die Hauptachsen auf 30 Minuten.'));
body.push(SP());
body.push(table(['Linie','Relation','Ist Fahrten/Ri','Takt heute','A: Takt','A: Fahrten','B: Takt','B: Fahrten'],
  D.ice.map(r=>[r.linie_key,r.bezeichnung,r.richtungsfahrten_ist,r.takt_ist,r.takt_ziel,
    r.richtungsfahrten_ziel,r.takt_ziel_b,r.richtungsfahrten_ziel_b]),
  [0.11,0.30,0.10,0.10,0.10,0.09,0.10,0.10],{right:[2,5,7],size:15}));
body.push(CAP('Tabelle 13: ICE-Linien mit heutigem und Ziel-Takt (Fahrten je Richtung und Tag).'));

body.push(H('8  Ebene 3: das IC- und EC-Netz',HeadingLevel.HEADING_1));
body.push(P('Die dritte Ebene erschließt die Flächen abseits der Schnellfahrstrecken und übernimmt die grenzüberschreitenden Verbindungen. Sie wird zuletzt konstruiert und absorbiert die Zwangspunkte des Systems: Wo eine Kante zwischen zwei Knoten zu viel Reserve verlangt, wird diese Reserve vorzugsweise dem IC zugeschlagen, weil dort ein zusätzlicher Halt einen realen Erschließungsgewinn bringt.'));
body.push(SP());
body.push(table(['Linie','Relation','Ist Fahrten/Ri','Takt heute','A: Takt','A: Fahrten','B: Takt','B: Fahrten'],
  D.ic.map(r=>[r.linie_key,r.bezeichnung,r.richtungsfahrten_ist,r.takt_ist,r.takt_ziel,
    r.richtungsfahrten_ziel,r.takt_ziel_b,r.richtungsfahrten_ziel_b]),
  [0.13,0.28,0.10,0.10,0.10,0.09,0.10,0.10],{right:[2,5,7],size:15}));
body.push(CAP('Tabelle 14: IC- und EC-Linien mit heutigem und Ziel-Takt.'));

// ---------- 9 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('9  Der eigentliche Engpass: die Knoten',HeadingLevel.HEADING_1));
body.push(P('Ein integraler Taktfahrplan verlagert das Kapazitätsproblem von der Strecke in den Bahnhof. Wenn alle Züge eines Knotens innerhalb von sechs Minuten ankommen und abfahren sollen, braucht jeder von ihnen gleichzeitig ein Bahnsteiggleis. Die folgende Abschätzung setzt siebzehn Betriebsstunden, einen Hauptverkehrszeitfaktor von 1,35 und zwei Knotenfenster je Stunde an.'));
body.push(SP());
body.push(table(['Knoten','Knotenzeit','Kanten','Züge je Knotenfenster','Bahnsteiggleise (Fernverkehr)','Bewertung'],
  D.kapa.map(r=>[r.knoten,r.knotenzeit,r.grad,r.zuege_je_knotenfenster,r.gleise_bedarf,r.bewertung]),
  [0.25,0.13,0.09,0.17,0.20,0.16],{right:[2,3,4],size:16}));
body.push(CAP('Tabelle 15: Abgeschätzter Gleisbedarf in den Knotenfenstern, Szenario A.'));
body.push(P('Frankfurt Hauptbahnhof, Hannover und München überschreiten die Schwelle, ab der ein Knoten ohne baulichen Eingriff nicht mehr funktioniert. Frankfurt ist dabei der kritischste Fall, weil ein Kopfbahnhof jeden Zug zweimal über dieselben Weichen führt und die Wendezeit die Gleisbelegung verdoppelt; der geplante Fernbahntunnel ist damit keine Komfortmaßnahme, sondern die Voraussetzung für einen integralen Taktfahrplan in Deutschland überhaupt. München Hauptbahnhof hat dasselbe Problem in kleinerer Ausprägung, entschärft durch die hohe Zahl durchgebundener Linien über München-Pasing.'));
body.push(P('Hannover ist der Knoten mit den meisten Kanten überhaupt und zugleich der einzige der drei, der als Durchgangsbahnhof gebaut ist. Dort ist die Aufgabe eine Frage der Fahrstraßenauflösung und der Bahnsteignutzung, nicht des Neubaus.'));
body.push(P('Für die übrigen Großknoten — Berlin, Köln, Nürnberg, Hamburg, Mannheim, Stuttgart — liegt der Bedarf bei sieben bis zehn Fernverkehrsgleisen und ist damit anspruchsvoll, aber im Bestand darstellbar. Köln Hauptbahnhof bleibt wegen der Hohenzollernbrücke ein Sonderfall; die Zulaufkapazität, nicht die Bahnsteigzahl, ist dort die bindende Restriktion.'));

// ---------- 10 ----------
body.push(H('10  Betriebsleistung',HeadingLevel.HEADING_1));
body.push(SP());
body.push(table(['Ebene','Zug-km/Tag heute','Szenario A','Szenario B','Mio Zug-km/Jahr heute','A','B','Δ A','Δ B'],
  D.leistung.map(r=>[r.ebene,Math.round(r.zugkm_tag_ist).toLocaleString('de-DE'),
    Math.round(r.zugkm_tag_A).toLocaleString('de-DE'),Math.round(r.zugkm_tag_B).toLocaleString('de-DE'),
    r.mio_jahr_ist,r.mio_jahr_A,r.mio_jahr_B,r.delta_A_pct+' %',r.delta_B_pct+' %']),
  [0.19,0.13,0.11,0.11,0.12,0.08,0.08,0.09,0.09],{right:[1,2,3,4,5,6,7,8],size:15}));
body.push(CAP('Tabelle 16: Betriebsleistung heute und in beiden Zielszenarien. Streckenkilometer als Luftlinie × 1,20.'));
body.push(P('Szenario A kostet 17,8 Prozent mehr Zugkilometer als heute. Das ist die Rechnung für Ordnung: gleiche Relationen, saubere Taktstufen, verlässliche Anschlüsse. Der Fahrzeugmehrbedarf liegt in derselben Größenordnung, da die Umlaufgeschwindigkeit durch die Knotenbindung leicht sinkt — überschlägig etwa zwanzig zusätzliche Triebzugeinheiten.'));
body.push(P('Szenario B verdoppelt die Betriebsleistung nahezu. Das ist die Größenordnung, die ein Netz nach schweizerischem Vorbild tatsächlich verlangt; die Schweiz fährt je Streckenkilometer ein Vielfaches der deutschen Zugdichte. Ob dieser Sprung wirtschaftlich darstellbar ist, entscheidet nicht der Fahrplan, sondern die Nachfrageentwicklung und die Trassenpreispolitik.'));

// ---------- 11 ----------
body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('11  Umsetzung in drei Stufen',HeadingLevel.HEADING_1));
body.push(P('Stufe 1 — Taktordnung ohne Infrastruktur (2 bis 3 Fahrplanjahre)',{bold:true,after:40}));
body.push(P('Die Knotenzeiten aus Tabelle 5 werden als verbindliche Planungsvorgabe gesetzt. Alle Linien werden auf die Taktstufen des Szenarios A gebracht und ihre Lagen an den Knoten ausgerichtet. Kanten mit Überschussreserve erhalten die in Abschnitt 5.4 genannten Zusatzhalte. Ergebnis: ein vollständig integrierter Taktfahrplan an allen vierundsechzig Knoten — ohne einen Meter neue Strecke, ohne eine einzige Beschleunigungsmaßnahme. Diese Stufe ist rein fahrplanerisch und damit die eigentliche Botschaft des Konzepts.'));
body.push(P('Stufe 2 — die Knoten (5 bis 10 Jahre)',{bold:true,after:40}));
body.push(P('Da die freie Strecke nichts braucht, richtet sich Stufe 2 vollständig auf die Bahnhöfe. Hannover und München werden betrieblich ertüchtigt, die Kanten mit Überschussreserve bekommen ihre Zusatzhalte oder es wird jeweils ein Endknoten zum Durchgangshalt abgestuft. Wer darüber hinaus investieren will, findet in Tabelle 8 die elf Kanten, auf denen Beschleunigung überhaupt einen messbaren Effekt hätte — mit dem ausdrücklichen Hinweis, dass dieser Effekt klein ist.'));
body.push(P('Stufe 3 — Frankfurt und der Vollausbau (10 bis 20 Jahre)',{bold:true,after:40}));
body.push(P('Mit dem Fernbahntunnel wird Frankfurt vom Kopf- zum Durchgangsknoten und damit vollknotenfähig. Erst dann lässt sich das Angebot des Szenarios B fahren, weil erst dann der meistbelastete Knoten des Netzes die doppelte Zugzahl im Knotenfenster aufnehmen kann. Die Reihenfolge ist zwingend: Angebotsausweitung vor Frankfurter Knotenumbau würde die Verspätungsanfälligkeit des gesamten Netzes erhöhen, nicht senken.'));

body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('12  Sonderfrage: Frankfurt Hauptbahnhof oder Flughafen-Fernbahnhof?',HeadingLevel.HEADING_1));
body.push(P('Weil Frankfurt der einzige Knoten ist, an dem das Konzept an der Infrastruktur scheitert, liegt die Frage nahe, ob sich der Engpass durch Verlagerung an den elf Bahnminuten entfernten Flughafen-Fernbahnhof umgehen lässt. Geprüft wurden drei Varianten gegen den Status quo.'));

body.push(H('12.1  Was heute wo hält',HeadingLevel.HEADING_2));
body.push(SP());
body.push(table(['Bahnhof','Zugart','Produktklasse','Fahrten/Tag','Gleisminuten/Tag','Anteil'],
  D.ffmbel.map(r=>[r.bahnhof,r.zugart,r.kategorie,r.fahrten_tag,r.gleisminuten_tag,r.anteil_pct+' %']),
  [0.24,0.18,0.16,0.14,0.16,0.12],{right:[3,4,5]}));
body.push(CAP('Tabelle 17: Bahnsteigbelegung beider Frankfurter Fernbahnhöfe. Ein wendender Zug ist mit 25 Minuten Gleisbelegung angesetzt, ein durchfahrender mit seiner tatsächlichen Haltezeit.'));
body.push(P('Diese Tabelle enthält bereits die Antwort. Von den 3.383 Gleisminuten, die der Fernverkehr täglich am Frankfurter Hauptbahnhof beansprucht, entfallen 78 Prozent auf wendende Züge und nur 22 Prozent auf durchfahrende. Die ICE-Sprinter tragen zusammen 335 Gleisminuten, also knapp zehn Prozent. Der Hauptbahnhof ist nicht überlastet, weil dort Sprinter halten, sondern weil dort fast die Hälfte aller Fernzüge endet und wendet.'));
body.push(P('Hinzu kommt die Größenordnung: Der Flughafen-Fernbahnhof hat vier Bahnsteiggleise (Fern 4 bis 7) und rund 30.000 Nutzer am Tag. Der Hauptbahnhof hat 25 Fernbahngleise, vier S-Bahn-Gleise, alle neun S-Bahn-Linien, zwei U-Bahn-Linien, sieben Straßenbahnlinien und etwa 493.000 Reisende am Tag. Die beiden Bahnhöfe sind nicht austauschbar.'));

body.push(H('12.2  Die Varianten im Vergleich',HeadingLevel.HEADING_2));
body.push(SP());
body.push(table(['Variante','Zielfunktion je Gewicht','Kanten mit Beschl.','Ø Reserve','Gleisminuten Hbf','Gleisminuten Flughafen','Auslastung Flughafen'],
  D.ffmvar.map(r=>[r.variante,r.kosten_je_gewicht,r.beschl_kanten,r.mittlere_reserve_pct+' %',
    r.hbf_gleisminuten,r.flughafen_gleisminuten,r.flughafen_auslastung_pct+' %']),
  [0.16,0.16,0.13,0.11,0.15,0.16,0.13],{right:[1,2,3,4,5,6]}));
body.push(CAP('Tabelle 18: Die drei Verlagerungsvarianten gegen den Status quo. Die Zielfunktion je Gewichtseinheit macht die Taktqualität über unterschiedlich große Kantennetze hinweg vergleichbar; kleiner ist besser. Die Auslastung des Flughafens bezieht sich auf vier Bahnsteiggleise und 18 Betriebsstunden.'));
[['Variante A — alles an den Flughafen','Die Taktqualität verschlechtert sich um 17 Prozent, weil der Hauptbahnhof als Knoten wegfällt und die Kanten Richtung Fulda, Mannheim und Köln neu zusammengelegt werden müssen. Entscheidend ist aber die Kapazität: 4.433 Gleisminuten täglich auf vier Gleisen entsprechen einer rechnerischen Auslastung von 103 Prozent. Bei einem realistischen Nutzungsgrad von 60 Prozent wären rund sieben Bahnsteiggleise nötig — der Bahnhof müsste also fast verdoppelt werden. Dazu käme der Verlust der Innenstadtanbindung für eine halbe Million Reisende täglich. Die Variante ist nicht durchführbar.'],
 ['Variante B — Sprinter an den Flughafen, ICE im Hauptbahnhof','Diese Variante ist die schlechteste von allen, und zwar aus einem Grund, der erst die Taktrechnung sichtbar macht: Sie erzwingt zwei Vollknoten im Abstand von elf Bahnminuten. Das Raster kennt aber nur Schritte von dreißig Minuten. Die Folge ist ein Sprung der Zielfunktion um 43 Prozent und eine Verdopplung der Kanten mit Beschleunigungsbedarf von fünf auf elf. Dem steht eine Entlastung des Hauptbahnhofs um lediglich zehn Prozent der Gleisminuten gegenüber, weil die Sprinter nur ein Zehntel der Belegung ausmachen.'],
 ['Variante C — Fernbahntunnel','Der Tunnel verändert die Taktrechnung nicht, weil er die Knotenzeit von Frankfurt unangetastet lässt. Er greift dort an, wo das Problem tatsächlich liegt: Werden die heute wendenden Züge durchgebunden, sinkt die Gleisbelegung des Hauptbahnhofs von 3.383 auf 1.373 Gleisminuten — eine Entlastung um 59 Prozent, also das Sechsfache dessen, was die Sprinterverlagerung bringt. Der Bahnhof bleibt gleichzeitig da, wo die Reisenden sind.']]
 .forEach(([t,x])=>{body.push(P(t,{bold:true,after:40})); body.push(P(x));});

body.push(H('12.3  Was die Reisenden verlören',HeadingLevel.HEADING_2));
body.push(P('Ein Sprinter, der statt im Hauptbahnhof am Flughafen endet, verliert nicht nur die Innenstadt, sondern auch einen Teil des Anschlussnetzes. Die folgenden Linien halten nur an einem der beiden Bahnhöfe.'));
body.push(SP());
body.push(table(['Linie','Fahrten/Tag','Hbf','Flughafen','Erreichbarkeit'],
  D.ffmlin.map(r=>[r.linie,r.fahrten_tag,r.haelt_hbf?'ja':'–',r.haelt_flughafen?'ja':'–',r.verlust]),
  [0.16,0.14,0.09,0.13,0.48],{right:[1]}));
body.push(CAP('Tabelle 19: Linien mit einseitiger Bedienung. Sieben Linien mit zusammen 47 Fahrten am Tag — 21 Prozent des Hauptbahnhofsangebots — wären vom Flughafen aus nicht direkt erreichbar.'));
body.push(P('Dazu kommt der Umweg für die Reisenden selbst: Vom Flughafen-Fernbahnhof in die Frankfurter Innenstadt sind es mit der S-Bahn rund zwölf Minuten plus Umsteigezeit. Das Sprinterversprechen lautet „von Stadtzentrum zu Stadtzentrum in unter vier Stunden“ — mit dem Flughafen als Endpunkt ist es nicht mehr einlösbar.'));

body.push(H('12.4  Empfehlung',HeadingLevel.HEADING_2));
body.push(P('Keine der beiden vorgeschlagenen Verlagerungen ist sinnvoll. Variante A scheitert an der Kapazität des Flughafenbahnhofs und an der Erreichbarkeit, Variante B an der Unvereinbarkeit zweier Vollknoten im Abstand von elf Minuten — sie verschlechtert die Taktqualität des gesamten Netzes um 43 Prozent für eine Entlastung von zehn Prozent an einem einzigen Bahnhof.'));
body.push(P('Was stattdessen zu tun ist, ergibt sich aus derselben Rechnung. Erstens: Der Flughafen-Fernbahnhof bleibt, was er heute ist und wofür er gebaut wurde — ein Durchgangshalt ohne Knotenbindung, an dem Züge in drei Minuten halten. Genau in dieser Rolle ist er wertvoll, denn er nimmt dem Hauptbahnhof den gesamten durchgehenden West-Ost-Verkehr ab: Die Relation Mannheim–Siegburg/Bonn ist über den Flughafen 25 Minuten schneller als über den Hauptbahnhof. Zweitens: Wo eine Sprinterlinie ohnehin über den Flughafen geführt wird, ist der zusätzliche Halt dort richtig — aber als Ergänzung, nicht als Ersatz. Drittens: Der eigentliche Hebel ist die Durchbindung der wendenden Züge, und die verlangt den Fernbahntunnel.'));
body.push(P('Ein Zwischenschritt ist ohne Tunnel möglich und lohnt sich. Von den 91,5 wendenden ICE-Fahrten am Tag lässt sich ein Teil zu durchgehenden Linien verknüpfen, die über Frankfurt Süd und den Flughafen geführt werden — etwa indem eine heute in Frankfurt endende Linie aus Richtung Fulda mit einer heute dort endenden Linie Richtung Mannheim zu einem durchlaufenden Zug verbunden wird. Jede so durchgebundene Linie spart rund 19 Gleisminuten am Hauptbahnhof. Zwanzig durchgebundene Fahrten am Tag entsprechen bereits der Entlastung, die eine vollständige Sprinterverlagerung brächte — ohne dass ein einziger Reisender die Innenstadt verliert.'));

body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('13  Wie viele Vollknoten verträgt das Netz?',HeadingLevel.HEADING_1));
body.push(P('Jeder Vollknoten kauft Anschlüsse mit Fahrzeit. Er zwingt alle Züge in ein gemeinsames Zeitfenster; wer nicht genau hineinpasst, wartet. Die Zahl der Vollknoten ist damit der eigentliche Stellhebel des ganzen Konzepts — und sie wurde bisher in dieser Untersuchung viel zu hoch angesetzt.'));
body.push(P('Gerechnet wurden Knotenmengen von sechzehn bis vierundsechzig, jeweils exakt gelöst, und für jede Variante die mittlere Verlängerung der Reisezeit gegenüber dem heutigen Fahrplan bestimmt, gewichtet nach Bedienhäufigkeit der Linien.'));
body.push(SP());
body.push(table(['Variante','Vollknoten','Netzkanten','Ø Reserve','Sollband','Reisezeit gegenüber heute'],
  D.knotenzahl.map(r=>[r.variante,r.vollknoten,r.kanten,r.reserve_pct+' %',r.sollband_pct+' %',
    '+'+r.reisezeit_verlaengerung_min+' min']),
  [0.26,0.13,0.13,0.14,0.13,0.21],{right:[1,2,3,4,5]}));
body.push(CAP('Tabelle 20: Wirkung der Knotenzahl. „Top n nach Verkehr“ nimmt die n verkehrsstärksten Bahnhöfe, die kuratierten Mengen sind geografisch ausgewogen gewählt.'));
body.push(P('Das Ergebnis ist eindeutig: Jeder zusätzliche Vollknoten kostet rund eine halbe Minute mittlere Reisezeit. Bindet man alle vierundsechzig in Frage kommenden Bahnhöfe, verlängert sich die durchschnittliche Fahrt um 38 Minuten; bei zwanzig sind es 17. Die Fahrzeitreserve je Kante bleibt dabei nahezu unverändert — sie verteilt sich nur auf mehr Knoten, und jede Fahrt sammelt mehr davon ein.'));
body.push(P('Gewählt wurden zwanzig Vollknoten: Hamburg, Bremen, Hannover, Berlin, Leipzig, Dresden, Erfurt, Münster, Dortmund, Duisburg, Köln, Frankfurt, Kassel-Wilhelmshöhe, Fulda, Würzburg, Nürnberg, München, Stuttgart, Mannheim und Karlsruhe. Sie decken das Netz geografisch ab und sind zugleich die Bahnhöfe mit den meisten Umsteigebeziehungen. Alle übrigen 246 Fernverkehrsbahnhöfe sind Durchgangshalte: Der Zug hält dort, wann immer es sein Laufweg ergibt, ohne Bindung an eine Knotenminute.'));
body.push(P('Das korrigiert eine Schwäche der Fassungen 1 bis 3 dieses Berichts. Dort waren alle vierundsechzig Bahnhöfe Vollknoten — mit dem Ergebnis, dass ein ICE von Berlin nach Köln 90 Minuten Wartezeit ansammelte, ohne dass irgendjemand davon einen Anschluss hatte. Ein integraler Taktfahrplan braucht wenige, dafür starke Knoten.',{it:true}));

body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('14  Der Fahrplan',HeadingLevel.HEADING_1));
body.push(P('Aus dem Knotenplan ist ein vollständiger Tagesfahrplan abgeleitet. Zwischen den Vollknoten fahren die Züge mit ihrer heutigen Systemfahrzeit zuzüglich der Reserve, die der Takt verlangt; die Zwischenhalte werden proportional zu ihren heutigen Fahrzeiten eingepasst, mit einer Haltezeit von ein bis zwei Minuten. An den Vollknoten gelten die Fenster aus Tabelle 5.'));
body.push(SP());
body.push(table(['Produktebene','Züge je Tag','Halte je Tag','Linien'],
  D.fahrplan.map(r=>[r.kategorie,r.zuege,r.halte,r.linien]),
  [0.34,0.22,0.22,0.22],{right:[1,2,3]}));
body.push(CAP('Tabelle 21: Umfang des Fahrplans, Szenario A, Betriebszeit 5 bis 23 Uhr.'));
body.push(P('Der Fahrplan liegt in zwei Bänden bei. Das Kursbuch der Linienfahrpläne zeigt auf 192 Seiten für jede der 168 Linienrichtungen alle Züge des Tages als Tabelle: Zeilen sind die Halte, Spalten die Züge. Die Bahnhofsfahrpläne geben auf 292 Seiten für jeden der 266 bedienten Bahnhöfe die Abfahrtstafel mit Linie, Ziel und Fahrweg, darunter die Ankünfte endender Züge.'));
body.push(P('An den Vollknoten wird die Taktstruktur in der Tafel unmittelbar sichtbar. In Frankfurt Hauptbahnhof sammeln sich die 306 täglichen Abfahrten in zwei kurzen Fenstern je Stunde, um :16 und um :46; die Ankünfte liegen um :09 und :39. Genau in diesen Minuten stehen alle Linien gleichzeitig am Bahnsteig — das ist der ganze Zweck der Übung.'));
body.push(P('Eine Prüfung über alle 4.014 Halte an Vollknoten ergab keinen einzigen Fall, der außerhalb seines Fensters liegt. Die mittlere Reisezeitverlängerung gegenüber dem heutigen Fahrplan beträgt 16,6 Minuten, gewichtet nach Bedienhäufigkeit.'));

body.push(new Paragraph({children:[new PageBreak()]}));
body.push(H('15  Hilft eine Zentrierung auf einen großen Bahnhof?',HeadingLevel.HEADING_1));
body.push(P('Die Frage klingt nach einer, aber sie sind zwei — und die Antworten fallen gegensätzlich aus.'));

body.push(H('15.1  Die Wahl des Ankerbahnhofs ist wirkungslos',HeadingLevel.HEADING_2));
body.push(P('Der Knotenplan ist nur bis auf eine gemeinsame Verschiebung eindeutig. Verschiebt man alle Knotenminuten um denselben Betrag, ändert sich keine einzige Fahrzeit, kein Anschluss und keine Kantenbedingung — es ändern sich nur die Ziffern auf dem Papier. Ob Berlin auf :00 liegt oder Frankfurt, ist deshalb eine Frage der Darstellung, nicht der Fahrplanqualität. Rechnerisch nachgewiesen: dieselbe Lösung, acht verschiedene Anker, in jedem Fall exakt derselbe Zielfunktionswert von 11.805,429.'));
body.push(P('Praktisch ist die Ankerwahl trotzdem nicht ganz gleichgültig — nur eben aus kommunikativen Gründen. Ein Anker sollte dort liegen, wo der Fahrplan seine merkbarste Struktur bekommt. Berlin auf :00 hat den Vorzug, dass der wichtigste Metropolknoten glatte Zeiten trägt; Frankfurt auf :00 hätte den Vorzug, dass der Knoten mit den meisten Umsteigebeziehungen glatt liegt. Beides ist vertretbar, keines ist besser.'));

body.push(H('15.2  Welcher Bahnhof ist überhaupt der zentralste?',HeadingLevel.HEADING_2));
body.push(P('Vor der eigentlichen Frage steht die Messung. Zentralität wurde auf zwei Arten bestimmt: über die Zwischenzentralität — der Anteil aller schnellsten Verbindungen im Netz, die über den Knoten führen — und über die mittlere Fahrzeit zum verkehrsgewichteten Rest des Netzes.'));
body.push(SP());
body.push(table(['Bahnhof','Kanten','Halte/Tag','Zentralität','Rang','Ø Fahrzeit zum Netz','Rang'],
  D.zentral.map(r=>[r.bahnhof,r.grad,r.halte_tag,r.zwischenzentralitaet,r.rang_zentralitaet,
    r.mittlere_fahrzeit_zum_netz+' min',r.rang_erreichbarkeit]),
  [0.28,0.09,0.12,0.13,0.08,0.19,0.11],{right:[1,2,3,4,5,6],size:16}));
body.push(CAP('Tabelle 22: Zentralität im Fernverkehrsnetz, die fünfzehn zentralsten Knoten.'));
body.push(P('Frankfurt Hauptbahnhof ist der zentralste Knoten des deutschen Fernverkehrsnetzes, und zwar deutlich: 28,6 Prozent aller schnellsten Verbindungen führen über ihn, er hat mit siebzehn die meisten Netzkanten und mit 224 Halten am Tag die höchste Belastung. Bemerkenswert sind die Plätze zwei und vier: Hanau und Fulda sind geografisch noch günstiger gelegen, aber verkehrlich klein — sie sind Durchgangsknoten, keine Quell- und Zielorte. Hannover, Mannheim und Köln folgen mit Werten um 0,23 bis 0,25.'));

body.push(H('15.3  Eine echte Zentrierung hilft — und Frankfurt ist der beste Kandidat',HeadingLevel.HEADING_2));
body.push(P('Wirksam ist nicht die Ankerwahl, sondern die Höhergewichtung eines Knotens in der Optimierung. Dazu wurden die Kanten eines Prioritätsknotens mit dem sechsfachen Gewicht versehen und das Programm für acht Kandidaten erneut exakt gelöst. Gemessen wird, wie stark sich die Fahrzeitreserve an diesem Knoten verbessert — und was das dem übrigen Netz kostet.'));
body.push(SP());
body.push(table(['Prioritätsknoten','Reserve ohne','Reserve mit','Gewinn','Netz ohne','Netz mit','Effekt aufs Netz'],
  D.zentrier.map(r=>[r.bahnhof,r.reserve_basis+' %',r.reserve_zentriert+' %',
    (r.gewinn_knoten>0?'+':'')+r.gewinn_knoten+' Pp',r.netz_reserve_basis+' %',r.netz_reserve_zentriert+' %',
    (r.netz_kosten_effekt>0?'+':'')+r.netz_kosten_effekt+' Pp']),
  [0.24,0.13,0.13,0.11,0.13,0.13,0.13],{right:[1,2,3,4,5,6]}));
body.push(CAP('Tabelle 23: Wirkung einer Zentrierung. „Pp“ = Prozentpunkte. Ein negativer Netzeffekt bedeutet, dass auch das übrige Netz besser wird.'));
body.push(P('Frankfurt Hauptbahnhof ist der klare Sieger. Die Fahrzeitreserve seiner siebzehn Netzkanten sinkt von 7,78 auf 4,73 Prozent — ein Gewinn von gut drei Prozentpunkten, mehr als bei jedem anderen Kandidaten. Und der Rest des Netzes wird dabei nicht schlechter, sondern sogar minimal besser. Das ist kein Zufall: Weil Frankfurt der zentralste Knoten ist, liegt seine Optimierung mit der des Gesamtnetzes ohnehin weitgehend gleichgerichtet. Köln, Nürnberg und Hannover gewinnen ebenfalls spürbar, ohne dem Netz zu schaden.'));
body.push(P('Bei Berlin und Mannheim bringt die Zentrierung dagegen nichts — aus dem besten aller Gründe: Ihre Kanten liegen im freien Optimum bereits nahezu perfekt, bei 1,61 beziehungsweise 5,85 Prozent Reserve. Wo nichts zu verbessern ist, hilft auch Priorität nicht.'));
body.push(P('Die Empfehlung lautet deshalb: Frankfurt Hauptbahnhof wird als Prioritätsknoten geführt. Seine Anschlüsse werden zuerst konstruiert, seine Kantenfahrzeiten sind Zwangspunkte für die Nachbarknoten. Der Anker der Zeitrechnung bleibt davon unberührt und kann aus Gründen der Lesbarkeit weiter auf Berlin :00 liegen.'));

body.push(H('15.4  Ein grobes Knotenraster ist keine Lösung',HeadingLevel.HEADING_2));
body.push(P('Naheliegend wäre, den Fahrplan noch merkbarer zu machen, indem man alle Knoten auf ein grobes Raster zwingt — etwa auf das schweizerische Schema von Vollknoten zur vollen und halben Stunde und Halbknoten zur Viertelstunde. Diese Variante wurde gerechnet und fällt eindeutig durch: Die mittlere Fahrzeitreserve springt von 7,7 auf 35,7 Prozent, der Anteil im Sollband bricht von 60 auf 21 Prozent ein. Auch ein Fünf-Minuten-Raster kostet mit 15,5 Prozent noch doppelt so viel Reserve wie nötig.'));
body.push(P('Der Grund liegt in der Netzgeometrie: Deutschland hat keine dominante Achse, sondern ein Maschennetz mit sehr unterschiedlichen Kantenlängen. Die Schweiz kann ihr Raster halten, weil ihre Knotenabstände von Anfang an auf Halbstundenschritte hin gebaut wurden. In Deutschland müssen die Knotenminuten frei bleiben — das ist der Preis dafür, ein gewachsenes Netz zu vertakten, statt ein Netz um den Takt herum zu bauen.'));

body.push(H('16  Grenzen der Untersuchung',HeadingLevel.HEADING_1));
body.push(BUL('Der Datensatz enthält keine Zugnummern. Die Sprinterzuordnung ist eine kalibrierte Rekonstruktion, keine amtliche Kennzeichnung.'));
body.push(BUL('Fahrzeiten sind Sollfahrzeiten aus dem veröffentlichten Fahrplan, keine Ergebnisse einer Betriebssimulation. Sie enthalten bereits die heutigen Regelzuschläge; die ausgewiesene technische Mindestfahrzeit ist daher konservativ.'));
body.push(BUL('Streckenkilometer sind mit dem Faktor 1,20 aus der Luftlinie geschätzt. Für einzelne Kanten mit ausgeprägter Trassenführung — etwa im Mittelrheintal oder im Thüringer Wald — liegt der reale Faktor höher.'));
body.push(BUL('Der Nahverkehr ist nicht modelliert. Ein vollständiger integraler Taktfahrplan bindet SPNV und Fernverkehr in denselben Knoten; die hier berechneten Knotenzeiten sind für den SPNV ein Zwangspunkt, keine freie Größe.'));
body.push(BUL('Die Kapazitätsaussagen sind Grobabschätzungen aus Halten je Knotenfenster beziehungsweise aus Gleisminuten mit pauschal 25 Minuten Wendezeit. Belastbare Aussagen erfordern eine Fahrstraßen- und Belegungsuntersuchung je Knoten; insbesondere ist bei Kopfbahnhöfen die Leistungsfähigkeit der Bahnhofsvorfelder und nicht die Bahnsteigzahl die bindende Restriktion.'));
body.push(BUL('Güterverkehrstrassen sind nicht berücksichtigt. Auf Mischverkehrsstrecken — insbesondere im Rheintal und zwischen Hamburg und Hannover — konkurriert der Takt mit dem Güterverkehr um dieselben Trassen.'));

body.push(H('17  Was in der Datenbank steckt',HeadingLevel.HEADING_1));
body.push(P('Alle Aussagen dieses Dokuments sind aus den mitgelieferten Dateien nachvollziehbar. Die SQLite-Datenbank bahn.db enthält 26 Tabellen, die Excel-Arbeitsmappe dieselben Inhalte in zweiundzwanzig Blättern.'));
[['station, bahnhof_bedienung','567 Bahnhöfe mit Koordinaten, Staat, Bundesland, Stadtzuordnung, Halten je Tag nach Produktklasse, Linienzahl und Rang.'],
 ['linie, linie_halt','89 Linien mit Laufweg, typischer Fahrzeit, Bedienhäufigkeit und vollständiger Haltefolge.'],
 ['trip_summary, stop_time','5.589 Zugtrassen mit Abfahrt, Ankunft, Dauer, Haltezahl, Verkehrstagen und Produktklasse; 54.928 Einzelhalte.'],
 ['kante','1.044 Streckenkanten zwischen benachbarten Bahnhöfen mit kürzester, mittlerer und längster Fahrzeit.'],
 ['itf_knotenzeit, itf_kante, itf_ergebnis','Das Ergebnis der Taktoptimierung: Knotenminuten, Kanten mit Soll-Fahrzeit, Abweichung und Maßnahme.'],
 ['ziel_linie, ziel_sprinter, sprinter_soll','Das Zielliniennetz beider Szenarien und die Fahrplanlagen der Sprinter-Korridore.'],
 ['ist_takt','875 Auswertungen der heutigen Abfahrtsminuten je Linie, Knoten und Richtung.'],
 ['knoten_kapazitaet, betriebsleistung','Gleisbedarf je Knotenfenster und Betriebsleistung in beiden Szenarien.'],
 ['ffm_varianten, ffm_belegung, ffm_linien','Die Frankfurter Sonderfrage: Gleisbelegung beider Bahnhöfe, Vergleich der Verlagerungsvarianten, einseitig bediente Linien.'],
 ['fahrplan_zug, fahrplan_halt','Der vollständige Tagesfahrplan: 1.700 Züge mit allen 12.876 Halten, minutengenau.'],
 ['knotenzahl','Der Vergleich der Knotenmengen von 16 bis 64 mit Reserve, Sollband und Reisezeitwirkung.'],
 ['takt_varianten, zentralitaet, zentrierung','Die Taktvarianten mit und ohne Beschleunigung, die Zentralitätsmaße aller Knoten und die Wirkung einer Zentrierung auf acht Kandidaten.']]
 .forEach(([a,b])=>{body.push(new Paragraph({spacing:{after:80},children:[
   new TextRun({text:a+' — ',font:FONT,size:21,bold:true}),new TextRun({text:b,font:FONT,size:21})]}));});
body.push(SP());
body.push(P('Quelle der Rohdaten: gtfs.de, Feed „Fernverkehr Deutschland“ (de_fv), Daten bereitgestellt von DELFI e. V. — Angaben zum Sprinterangebot: bahn.de, Seite „ICE Sprinter“.',{size:18,color:GREY,it:true}));

const doc=new Document({
  styles:{default:{document:{run:{font:FONT,size:21}}},
    paragraphStyles:[
     {id:'Heading1',name:'Heading 1',basedOn:'Normal',next:'Normal',quickFormat:true,
      run:{font:FONT,size:30,bold:true,color:NAVY}},
     {id:'Heading2',name:'Heading 2',basedOn:'Normal',next:'Normal',quickFormat:true,
      run:{font:FONT,size:25,bold:true,color:NAVY}}]},
  features:{updateFields:true},
  sections:[{properties:{page:{margin:{top:1100,bottom:1100,left:1080,right:1080}}},
    footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,
      children:[new TextRun({text:'Systemtakt Fernverkehr Deutschland  ·  Seite ',font:FONT,size:16,color:GREY}),
                new TextRun({children:[PageNumber.CURRENT],font:FONT,size:16,color:GREY})]})]})},
    children:body}]});
Packer.toBuffer(doc).then(b=>{fs.writeFileSync('Systemtakt_Fernverkehr_Deutschland.docx',b);console.log('ok',b.length);});
