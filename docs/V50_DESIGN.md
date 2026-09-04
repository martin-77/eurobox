# Eurobox v50 – Konstruktionsidee

## Ziel

v50 ist ein Neuaufbau für das **FOCUS THRON² EQP Modelljahr 2023** und eine 600×400-mm-Eurobox. Es ist ausdrücklich kein kosmetisches Update von v47/v49.

Die Konstruktion soll:

1. die gemessene Ø12.42-mm-Rackgeometrie respektieren;
2. die Box ohne Bohrung werkzeuglos halten;
3. die langen Querarme als echte Tragprofile ausführen;
4. bei der Montage nicht um das runde Rackrohr nach unten kippen;
5. mit PETG/0.4-mm-Düse und wenig Support druckbar sein;
6. für den Test vollständig gedruckte Spindeln verwenden;
7. später auf M4/Heat-Set/Metallhardware umstellbar sein, ohne die Base neu zu konstruieren;
8. alle kritischen Maße und Prüfungen reproduzierbar in GitHub Actions halten.

Die vollständige Maßherkunft steht in `MEASUREMENTS.md`; der Fahrradkontext und die widersprüchlichen Lastangaben stehen in `FOCUS_THRON2_EQP_2023.md`.

## 1. Koordinatensystem und Seitenmodul

- X = Fahrtrichtung
- Y = vom jeweiligen oberen Gepäckträgerrohr nach außen zur Boxkante
- Z = oben
- lokale Rohrmitte = Y0/Z0
- Rohrachse = X

Ein Seitenmodul sitzt auf einem der beiden oberen Rack-Längsrohre und besitzt zwei Klemmpunkte bei X = ±90 mm. Das zweite Modul wird spiegelbildlich montiert; separate linke/rechte Druckteile sind nicht nötig.

## 2. Tragstruktur

Die alten ca. 28×8-mm-Flacharme werden nicht weiterverwendet. Die v50-Arme erhalten eine hohe U-/I-artige Struktur, weil bei PETG die Bauhöhe für die Biegesteifigkeit wesentlich wirksamer ist als zusätzliche Breite.

Der aktuelle CAD-Zielbereich beträgt:

- ca. 28–32 mm Breite je Arm;
- ca. 22–30 mm strukturelle Bauhöhe außerhalb des Rack-/Fenderbereichs;
- 4.5–5.0 mm obere Auflage;
- 3.2 mm vertikale Stege;
- Auflageoberseite immer Z = 39.54 mm.

Die volle Tiefe beginnt erst außerhalb des unmittelbaren Rohrklemmbereichs. An der Klemmenwurzel wird Material **addiert** (Gusset/Transition), nicht durch große Taschen entfernt.

Frühere einfache Querschnittsrechnungen zeigten gegenüber der alten 28×8-mm-Platte einen sehr großen Steifigkeitsgewinn. Diese Rechnung ist nur ein Sanity-Check, keine FEA und keine Freigabe der Herstellerlast.

## 3. Rohrklemme

Die Hauptbefestigung besteht aus zwei identischen Stationen:

- starre obere Sattelhälfte ist Teil der Base;
- separate flexible `rack_lower`-Hälfte;
- reales Rackrohr Ø12.42 mm ist die harte Kollisionsgeometrie;
- starre Sattelkontur ca. Ø12.52 mm, also 0.05 mm radialer Freiraum;
- flexible untere Sattelkontur ca. Ø12.30 mm für kleine definierte PETG-Vorspannung;
- Pin Ø4.0 mm;
- Pinbohrung Ø4.6 mm;
- Pivotzentrum aus dem funktionierenden Vorgängerprinzip: Y = -12.0 mm / Z = -5.5 mm, sofern der v50-Neuaufbau nicht in CI eine bessere kollisionsfreie Lage nachweist.

Die untere Hälfte muss in negativer X-Rotation öffnen. Geprüft werden 0, -15, -30, -45, -60 und -75 Grad. Spätestens ungefähr bei -45 Grad soll das reale Ø12.42-mm-Rohr frei sein.

## 4. Anti-Flop am FOCUS-Massload-3-leg

Die MY23-EQP-Bilder und -Explosionszeichnung zeigen den 3-leg-Träger mit diagonalen Streben Richtung Hinterachse. Das ist für die Montage nützlich, aber die Strebe wird **nicht zum Hauptlastpfad**.

v50 behält deshalb ein kleines separates Anti-Flop-Teil:

- Hauptlast weiterhin ausschließlich über die zwei oberen Rackklemmen pro Seitenmodul;
- Anti-Flop-Stütze liegt lediglich an einer diagonalen Rackstrebe an bzw. wird dort leicht fixiert;
- Zweck: das leere Seitenmodul klappt beim Aufsetzen der Box nicht um das runde Längsrohr nach unten;
- da Durchmesser und Winkel dieser Strebe noch nicht gemessen sind, ist die erste Version ein universeller V-Sattel mit Anpassspiel/Schlitzen, **keine erfundene formschlüssige Klemme**;
- nach einer einzigen Messung von Streben-Ø und Winkel kann daraus ein definierter Clip werden.

Wichtig: Es wird nichts zwischen Hauptrahmen und bewegtem Hinterbau verspannt. Alle Kontaktpunkte bleiben am fahrwerkmitbewegten EQP-Träger.

## 5. Boxauflage und unterer Rand

Harte Werte:

- Eurobox 600×400 mm quer montiert;
- unterer Rand 16.45 mm horizontal und 16.45 mm vertikal;
- Rohrmitte → Boxkante 244.665 mm;
- Boxauflage Z = 39.54 mm;
- Schutzblechoberkante Z = 34.54 mm;
- damit nur 5.00 mm nomineller vertikaler Restabstand.

Die Base darf diesen 5-mm-Raum nicht gedankenlos als Strukturvolumen benutzen. Der exakte Querschnitt des Schutzblechs ist noch nicht vermessen; CI darf deshalb nur gegen eindeutig bekannte Keep-outs prüfen und keine erfundene Fenderform als Realität deklarieren.

## 6. Klemmplatte

Eine breite Platte wird von zwei Spindeln geführt.

Zielwerte:

- Schraubachsen X = ±42 mm;
- Schraubachse Z = 31 mm;
- zwei **echte Durchgangsbohrungen**;
- Journal Ø6.0 mm;
- Plattenloch ca. Ø6.4–6.5 mm;
- mindestens 4.0 mm, Ziel 4.5 mm Öffnungsweg;
- Untergriff ca. 4 mm;
- keine T-Schlitze;
- keine offenen Montageschlitze durch tragende Bereiche;
- kein Gewinde in der Platte.

Die Platte darf nicht nur nach innen gedrückt werden: sie wird auf der Spindel axial gefangen und beim Lösen aktiv nach außen zurückgezogen.

## 7. Spindelkinematik

Die Hauptspindel ist normal **rechtsgängig**.

Beim Zudrehen:

1. Knob dreht Spindel über einen formschlüssigen Sechskant;
2. feststehende Lead-Nut zwingt Spindel axial nach innen;
3. eine massive Schulter drückt die Platte zur Box;
4. Platte selbst rotiert nicht.

Beim Aufdrehen:

1. Spindel läuft nach außen;
2. der innere Retainer zieht die Platte mit;
3. der Untergriff gibt den Boxrand frei.

Für den Drucktest: RH Ø8×2-mm-Leitgewinde. Korrekte Drehung+Translation und falsche Händigkeit/Phase werden in CI geometrisch gegeneinander geprüft.

## 8. Austauschbare Lead-Nut

Das Testgewinde wird nicht dauerhaft in die Base geschnitten.

Die Base erhält einen zugänglichen, gegen Verdrehung gesicherten Nut-/Cartridge-Sitz:

- Prototyp: gedruckte RH-Ø8×2-Lead-Nut;
- später: Einsatz mit M4-Heat-Set oder Metallmutter;
- Außeninterface des Einsatzes bleibt gleich;
- Axialkraft geht in den massiven Käfig/Flansch der Base, nicht in einen dünnen Deckel.

Damit bleiben Base, Platte und Kinematik beim Wechsel auf Metall erhalten.

## 9. Platte ↔ Spindel

Mechanisch einfache Schulter-/Journal-Lösung:

- glatter Ø6-mm-Journal durch das Plattenloch;
- massive Druckschulter außen, etwa Ø11 mm;
- flache Sicherungsnut auf der Innenseite;
- separater Horseshoe-/C-Clip zieht die Platte nur beim Öffnen zurück;
- die eigentliche Klemmkraft läuft über die Schulter, nicht über den Clip.

Dadurch entfällt die komplizierte und strukturell ungünstige T-Nut-/Retainer-Taschen-Geometrie aus früheren Versuchen.

## 10. Separate Spindel und separater Knob

Die frühere integrierte `screw_with_knob`-Geometrie bleibt verworfen.

v50:

- Spindel separat;
- Knob separat;
- Drehmoment über AF10-Sechskant;
- Knob-Socket ca. AF10.3 mm;
- axiale Knob-Sicherung separat;
- die Knob-Sicherung überträgt nicht das Hauptdrehmoment.

Damit kann die Spindel zuerst durch Base/Lead-Nut montiert und der Knob anschließend außen befestigt werden.

## 11. Lastannahme

Die Quellenlage zum MY23 Massload 3-leg ist widersprüchlich: Händlerdaten nennen häufig 25 kg, die aktuelle FOCUS-Archiv-FAQ dieser Generation 16 kg. Deshalb gilt für v50 **16 kg konservative Rack-Gesamtlast**, bis der konkrete Rack-Aufkleber verifiziert ist.

Ein 3×-Dynamikfall in vereinfachten Balkenrechnungen ist ausschließlich ein Sanity-Check der Adaptergeometrie. Er erhöht keine Herstellerfreigabe.

## 12. Druckziel

- Prusa CORE One L
- PETG für den ersten Funktionstest
- 0.4-mm-Düse
- 0.20-mm-Layer als Standard
- mindestens 3 Perimeter für den strukturellen Prototyp
- möglichst keine Supports an den langen Tragprofilen und den Hauptkontaktflächen

## 13. Pflichtprüfungen in GitHub Actions

Ein v50-Build darf erst als druckbar bezeichnet werden, wenn mindestens Folgendes bestanden ist:

1. alle Hauptteile `Shape.isValid()` und erwartete Solid-Anzahl;
2. STEP-Reimport gültig;
3. STL watertight, winding consistent, eine Komponente;
4. Base gegen reales Ø12.42-Rohr ohne Kollision;
5. `rack_lower` mit definierter Vorspannung;
6. vollständiger Öffnungssweep ohne Base-Kollision;
7. Pin/Bohrung/Clip geometrisch montierbar;
8. Platte bei 0/1/2/3/4 mm kollisionsfrei;
9. beide Plattenbohrungen wirklich durchgängig;
10. Lead-Nut sitzt kollisionsfrei im Cartridge-Sitz;
11. korrekte Gewindebewegung kollisionsfrei, falsche Phase/Händigkeit kollidiert;
12. Spindel/Schulter/Retainer haben nur beabsichtigte Kontakte;
13. bekannte Schutzblech-Keep-outs bleiben frei;
14. Gesamtbreite/Knob-Überstand wird im Report ausgegeben.

## 14. Noch offene Messwerte

Für die nächste Präzisionsstufe werden nur noch wenige echte Fahrradmaße benötigt:

- Ø der diagonalen 3-leg-Strebe;
- deren Winkel/Position relativ zum oberen Rackrohr;
- exakte Fender-Querkontur;
- genaue Wandstärke des verwendeten Eurobox-Unterrandes;
- Typenschild/Artikelnummer und Lastwert des tatsächlich montierten Massload-Trägers.

Diese Werte sind bewusst als offen dokumentiert und werden nicht aus Fotos in Millimeter geschätzt.