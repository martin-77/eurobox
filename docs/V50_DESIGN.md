# Eurobox v50 – Konstruktionsidee

## Ziel

v50 ist kein kosmetisches Update von v47/v49, sondern ein Neuaufbau mit den inzwischen bekannten realen Randbedingungen des Focus THRON² EQP 2023 und der 600×400-Eurobox.

Kernziele:

1. starre, ausreichend tiefe Tragstruktur statt langer 8-mm-Flacharme;
2. echte, montierbare Rohrklemmen um Ø12.42 mm;
3. eine Klemmplatte, die geführt ist und über reale Durchgangsbohrungen von zwei Spindeln aktiv vor- **und** zurückbewegt wird;
4. getrennte Spindel und Handknopf;
5. ein Testgewinde, das grob genug zum Drucken ist, aber dieselbe Kinematik wie die spätere Metall-/M4-Version verwendet;
6. ein separater Stabilisator für die diagonale EQP-Gepäckträgerstrebe, damit der Halter beim Montieren nicht nach unten wegklappt;
7. jede kritische Geometrie wird automatisiert in GitHub Actions geprüft.

## 1. Seitenmodul statt einteiliger 600-mm-Brücke

Ein v50-Seitenmodul sitzt auf **einem** der beiden längs verlaufenden Gepäckträgerrohre. Es besitzt zwei Rohrklemmen im Abstand X = ±90 mm und reicht von dort quer nach außen zur Boxkante.

Das komplette Fahrrad verwendet zwei spiegelbildlich montierte Module. So bleiben die Teile auf einem üblichen Druckbett druckbar und links/rechts geometrisch identisch bzw. spiegelbar.

## 2. Tragstruktur

Die alten langen Arme mit ca. 28×8 mm Querschnitt waren für PETG als Biegeträger zu flach.

v50 verwendet pro Seitenmodul zwei Doppelsteg-I-Träger:

- 32 mm Gesamtbreite
- 30 mm Gesamtbauhöhe
- 4.5-mm Ober- und Unterflansch
- zwei 3.2-mm Stege

Vorteile:

- hohe vertikale Biegesteifigkeit durch große Bauhöhe;
- offene Bereiche statt Vollmaterial;
- bessere Torsionssteifigkeit als ein einzelner Mittelsteg;
- kurze Brückenweiten beim Drucken;
- Übergänge an Rohrklemme und Außenrahmen werden breit verrippt statt durch Aussparungen geschwächt.

Die Auflageoberseite bleibt auf Z = 39.54 mm. Die volle Tiefe beginnt erst außerhalb der Rohrklemme, damit das reale Ø12.42-mm-Rohr und die Montagebewegung frei bleiben.

## 3. Rohrklemme

v50 erhält eine neu aufgebaute zweiteilige Klemme:

- starre obere Hälfte ist Bestandteil der Base;
- separate untere Klemmhälfte;
- reale Rohrkontur Ø12.42 mm wird als Prüfgeometrie modelliert;
- starre obere Hälfte erhält bewusst etwas Freiraum;
- die untere PETG-Hälfte übernimmt eine kleine definierte Vorspannung.

Die untere Hälfte wird nicht über einen fragilen Rastarm gehalten. Stattdessen wird sie formschlüssig zwischen den seitlichen Ohren der Base geführt und mit gedruckten Pins gesichert. Pin, Loch und Clip werden als getrennte Teile modelliert und in der Assembly geprüft.

## 4. Boxauflage und Rand

Die Eurobox wird nicht nur seitlich geklemmt, sondern auf einer steifen Außenrahmen-/Auflagezone abgestützt. Die harte Auflagehöhe bleibt Z = 39.54 mm.

Für den unteren 16.45×16.45-mm-Rand wird im Validierungsskript ein konservatives Prüfvolumen erzeugt. Die Klemmplatte darf dieses Volumen im geschlossenen Zustand nur an den vorgesehenen Kontaktflächen tangieren und muss nach dem Öffnen vollständig freigeben.

## 5. Klemmplatte

Die Platte ist ein massiver Hauptkörper mit echten Bohrungen bei X = ±42 mm / Z = 31 mm.

Nicht mehr verwendet werden:

- offene T-Schlitze;
- große Montageschlitze durch tragende Bereiche;
- nur angedeutete Blindtaschen ohne echte axiale Verbindung;
- Gewinde direkt in der Klemmplatte.

Die Platte läuft ausschließlich in externen Führungsleisten der Base. Kleine seitliche Führungsnasen sind **zusätzliches Material**, keine Aussparungen.

Öffnungsweg: Ziel 4.5 mm, davon mindestens 4.0 mm vollständig geprüft.

## 6. Richtige Spindelkinematik

Die Spindel ist normal rechtsgängig.

Ablauf beim Zudrehen:

1. Knob dreht die Spindel;
2. feststehende Lead-Nut zwingt die Spindel axial nach innen;
3. eine Schulter auf der Spindel drückt die Platte zur Box;
4. die Platte selbst rotiert nicht.

Beim Aufdrehen:

1. die Spindel wandert nach außen;
2. ein axial gefangener Retainer hinter der Platte zieht die Platte mit;
3. die Platte öffnet aktiv – sie muss nicht von Hand herausgezogen werden.

Der innere Retainer sitzt in einer versenkten Tasche und darf die Kontaktfläche zur Box nicht überragen.

## 7. Austauschbare Lead-Nut

Das Testgewinde wird **nicht** zum festen Bestandteil der Base gemacht.

Für den Drucktest:

- RH Ø8×2 mm;
- separate Lead-Nut;
- Lead-Nut sitzt formschlüssig in einem von oben zugänglichen Käfig der Base;
- ein separater Deckel hält die Nut im Käfig;
- axiale Schraubkräfte werden von den Käfigwänden aufgenommen, nicht vom Deckel.

Später kann die Lead-Nut durch einen äußerlich identischen Einsatz für M4/Heat-Set/Metallgewinde ersetzt werden. Dadurch bleiben Base, Plattenführung und Kinematik erhalten.

## 8. Separate Spindel und separater Knob

Die frühere integrierte `screw_with_knob`-Geometrie ist verworfen.

v50:

- Spindel separat;
- Knob separat;
- Drehmoment über AF10-Sechskant;
- axiale Sicherung über einen separaten Retainer-Abschnitt und eine separate Kappe/Mutter;
- die Retainer-Verschraubung trägt nicht das Bedienmoment.

Dadurch lässt sich die Spindel zuerst durch Base/Lead-Nut montieren und der Knob anschließend außen anbringen.

## 9. Anti-Flop-Stabilisator am THRON² EQP

Die Fotos/Herstellerunterlagen zeigen die typischen seitlichen/diagonalen EQP-Trägerstreben Richtung Hinterachse. Deren exakte Rohrabmessung und Winkel liegen aber nicht als verlässliche Messung vor.

v50 verwendet deshalb einen justierbaren Stabilisator:

- breite V-Auflage für unterschiedliche Rohrdurchmesser;
- zwei Kabelbinderkanäle zur dauerhaften Befestigung an der diagonalen Strebe;
- höhenverstellbare Stützschraube;
- breite Kontaktfläche zur Unterseite des v50-Arms.

Der Stabilisator trägt nicht die reguläre Boxlast. Seine Aufgabe ist:

- Halter beim Ansetzen/Montieren abstützen;
- ungewolltes Abklappen nach unten verhindern;
- Spiel aus der Montage nehmen.

## 10. Was v50 ausdrücklich nicht behauptet

- Keine aus Fotos erfundenen Maße der diagonalen Focus-Streben.
- Keine Freigabe oberhalb der zulässigen FOCUS-Gepäckträgerlast.
- Keine FEA, solange wir nur analytische Querschnitts- und Kollisionschecks durchführen.
- Der Ø8×2-Druckmechanismus ist ein Prototyp-Lead-Screw-System, kein als M4 verkleidetes Ersatzgewinde.

## 11. Dateistruktur

Der GitHub-Build soll erzeugen:

- `eurobox_v50_base.FCStd/STEP/STL`
- `eurobox_v50_clamp_plate.FCStd/STEP/STL`
- `eurobox_v50_rack_lower.FCStd/STEP/STL`
- `eurobox_v50_lead_screw_print.FCStd/STEP/STL`
- `eurobox_v50_lead_nut_print.FCStd/STEP/STL`
- `eurobox_v50_lead_nut_cap.FCStd/STEP/STL`
- `eurobox_v50_knob.FCStd/STEP/STL`
- `eurobox_v50_knob_retainer.FCStd/STEP/STL`
- `eurobox_v50_plate_retainer_clip.FCStd/STEP/STL`
- `eurobox_v50_pin.FCStd/STEP/STL`
- `eurobox_v50_pin_clip.FCStd/STEP/STL`
- `eurobox_v50_stay_saddle.FCStd/STEP/STL`
- `eurobox_v50_stay_support_screw.FCStd/STEP/STL`
- Assembly-FCStd
- JSON-Validierungsberichte
- vollständiges ZIP-Artefakt.