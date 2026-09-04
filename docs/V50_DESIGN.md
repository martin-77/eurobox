# Eurobox v50 – Konstruktionsidee

## Ziel

v50 ist kein kosmetisches Update von v47/v49, sondern ein Neuaufbau mit den inzwischen bekannten realen Randbedingungen des Focus THRON² EQP 2023 und der 600×400-Eurobox.

Kernziele:

1. starre, ausreichend tiefe Tragstruktur statt langer 8-mm-Flacharme;
2. echte, montierbare Rohrklemmen um Ø12.42 mm;
3. integrierter Anti-Rotationsanschlag an der Gepäckträgerkante statt separatem V-Sattel an einer diagonalen Strebe;
4. eine Klemmplatte, die geführt ist und über reale Durchgangsbohrungen von zwei Spindeln aktiv vor- und zurückbewegt wird;
5. getrennte Spindel und Handknopf;
6. ein Testgewinde, das grob genug zum Drucken ist, aber dieselbe Kinematik wie die spätere Metall-/M4-Version verwendet;
7. jede kritische Geometrie wird automatisiert in GitHub Actions geprüft.

## 1. Seitenmodul

Ein v50-Seitenmodul sitzt auf einem der beiden längs verlaufenden Gepäckträgerrohre. Es besitzt zwei Rohrklemmen im Abstand X = ±90 mm und reicht von dort quer nach außen zur Boxkante.

Das komplette Fahrrad verwendet zwei spiegelbildlich montierte Module. Die beiden Module tragen die 600-mm-Box gemeinsam.

## 2. Tragstruktur

Die alten langen Arme mit ca. 28×8 mm Querschnitt waren für PETG als Biegeträger zu flach.

v50 verwendet pro Seitenmodul zwei Doppelsteg-I-Träger:

- 32 mm Gesamtbreite
- 30 mm Gesamtbauhöhe
- 4.5-mm Ober- und Unterflansch
- zwei 3.2-mm Stege
- Querschnittsfläche ca. 422.4 mm²
- Flächenträgheitsmoment Ix ca. 52,243 mm⁴

Die Auflageoberseite bleibt auf Z = 39.54 mm. Die volle Tiefe beginnt erst außerhalb des Rohr-/Klemmbereichs. Übergänge an Rohrklemme und Außenrahmen werden mit großen Radien/Gussets verstärkt; keine tragenden Aussparungen direkt an der Klemmenwurzel.

Analytischer Sanity-Check bei 220 mm angenommener freier Biegelänge, vier Armen, E(PETG)=1500 MPa:

- 16 kg Gesamtlast: ca. 2.48 MPa Biegespannung und ca. 1.78 mm Balken-Enddurchbiegung;
- 3× Dynamikfall: ca. 7.44 MPa und ca. 5.33 mm.

Das ist kein FEA-Nachweis, aber die Geometrie liegt damit nicht mehr in der Größenordnung der v45-Flacharme.

## 3. Rohrklemme

v50 erhält eine neu aufgebaute zweiteilige Klemme:

- starre obere Hälfte ist Bestandteil der Base;
- separate untere Klemmhälfte;
- reale Rohrkontur Ø12.42 mm wird als Prüfgeometrie modelliert;
- starre obere Hälfte erhält bewusst etwas Freiraum;
- die untere PETG-Hälfte übernimmt eine kleine definierte Vorspannung;
- untere Hälfte formschlüssig zwischen seitlichen Ohren geführt und mit gedruckten Pins gesichert.

Pin, Loch und Clip werden als getrennte Teile modelliert und in der Assembly geprüft.

## 4. Integrierter Anti-Rotationsanschlag

Der separate V-Sattel für die diagonale Gepäckträgerstrebe ist vollständig verworfen.

Stattdessen wird die Base an jeder der beiden Klemmenstationen auf der zum Fahrrad zeigenden Seite nach unten gezogen. Es entsteht ein massiver, nach unten gezogener Innenanschlag unmittelbar an der Gepäckträgerkante/äußeren Längsstrebe.

Konstruktionsprinzip:

- oberer Sattel trägt auf dem Ø12.42-mm-Rohr;
- Rack-Lower klemmt das Rohr von unten;
- zusätzlich liegt ein breiter Innenanschlag seitlich am Gepäckträgerrand an;
- versucht der lange Außenarm mit der Box nach unten zu rotieren, wird das Kippmoment nicht nur über Reibung der Rundrohrklemme aufgenommen: der Innenanschlag geht auf Druck gegen den Gepäckträgerrand;
- der Anschlag ist integraler Bestandteil der massiven Klemmenwurzel und kein dünner Zusatzsteg.

Erste CAD-Zielwerte pro Klemmenstation:

- Anschlagbreite in X: 24 mm;
- Wandstärke nach innen: 6 mm;
- Kontaktbereich umfasst Z=0 des Gepäckträgerrohres und reicht ungefähr von Z=+5 bis Z=-8 mm;
- nominaler Montagefreiraum zur Rohr-/Randtangente: 0.15–0.25 mm;
- große Innenradien am Übergang zur Klemmenwurzel, Ziel ≥4 mm;
- kein Bauteil unterhalb/in Richtung Schutzblech außerhalb des lokalen Rohrklemmenbereichs.

Die endgültige Kontaktposition wird im CAD gegen das reale Ø12.42-Prüfrohr und die gemessene Trägerbreite geprüft. Dieser Anschlag ersetzt ausdrücklich den früher vorgesehenen V-Sattel und alle Kabelbinder-/Diagonalstrebenlösungen.

## 5. Boxauflage und Rand

Die Eurobox wird auf einer steifen Außenrahmen-/Auflagezone abgestützt. Die harte Auflagehöhe bleibt Z = 39.54 mm.

Für den unteren 16.45×16.45-mm-Rand wird im Validierungsskript ein konservatives Prüfvolumen erzeugt. Die Klemmplatte darf dieses Volumen nur an vorgesehenen Kontaktflächen berühren und muss es nach dem Öffnen vollständig freigeben.

## 6. Klemmplatte

Die Platte ist ein massiver Hauptkörper mit echten Durchgangsbohrungen bei X = ±42 mm / Z = 31 mm.

Nicht mehr verwendet werden:

- offene T-Schlitze;
- große Montageschlitze durch tragende Bereiche;
- Blindtaschen ohne axiale Verbindung;
- Gewinde direkt in der Klemmplatte.

Die Platte läuft in externen Führungen der Base. Führungsnasen sind zusätzliches Material und schwächen den Hauptkörper nicht.

Öffnungsweg: 4.5 mm Ziel, mindestens 4.0 mm zwingend kollisionsfrei.

## 7. Spindelkinematik

Die Spindel ist normal rechtsgängig.

Beim Zudrehen:

1. Knob dreht die Spindel;
2. feststehende Lead-Nut zwingt die Spindel axial nach innen;
3. eine Schulter auf der Spindel drückt die Platte zur Box;
4. die Platte selbst rotiert nicht.

Beim Aufdrehen:

1. die Spindel wandert nach außen;
2. ein axial gefangener Retainer hinter der Platte zieht die Platte mit;
3. die Platte öffnet aktiv.

Der innere Retainer sitzt in einer Senkung und darf die Boxkontaktfläche nicht überragen.

## 8. Austauschbare Lead-Nut

Das Testgewinde wird nicht zum festen Bestandteil der Base gemacht.

Drucktest:

- RH Ø8×2 mm;
- separate Lead-Nut;
- Lead-Nut formschlüssig in einem zugänglichen Käfig der Base;
- Deckel hält die Nut nur im Käfig; Axialkräfte laufen in die Käfigwände.

Später kann derselbe Bauraum einen M4-/Heat-Set-/Metallgewinde-Einsatz aufnehmen. Base, Plattenführung und Kinematik bleiben unverändert.

## 9. Separate Spindel und separater Knob

Die integrierte `screw_with_knob`-Geometrie ist verworfen.

v50:

- Spindel separat;
- Knob separat;
- Drehmomentübertragung formschlüssig über AF10-Sechskant;
- axiale Sicherung über separaten Retainer und separate Mutter/Kappe;
- Sicherung überträgt nicht das Hauptdrehmoment.

Dadurch wird zuerst die Spindel durch Base/Lead-Nut montiert und der Knob anschließend außen aufgesetzt.

## 10. Lastgrenze

Das Zielrad ist das FOCUS THRON² 6.8 EQP Modelljahr 2023. FOCUS nennt für dieses Modell einen Massload-3-leg-Gepäckträger mit 16 kg maximaler Zuladung. Diese 16 kg bleiben die harte obere Zielgröße des originalen Gepäckträgers; der 3×-Rechenfall ist nur ein Sanity-Check des gedruckten Adapters und erhöht die Herstellerfreigabe nicht.

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
- Assembly-FCStd
- JSON-Validierungsberichte
- vollständiges ZIP-Artefakt.
