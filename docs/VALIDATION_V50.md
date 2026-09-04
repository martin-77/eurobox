# v50 – automatische Validierung

Ein Build darf nur als `eurobox-v50` Artefakt veröffentlicht werden, wenn alle harten Checks bestanden sind.

## Geometrie

Für jedes STEP-Teil nach Export und erneutem STEP-Import:

- `Shape.isValid() == True`
- genau 1 Solid pro druckbarem Einzelteil
- positive Volumina
- plausible Bounding Box

Für jedes STL:

- watertight
- winding consistent
- genau 1 zusammenhängende Komponente
- positives Volumen

## Reales Gepäckträgerrohr

Prüfkörper: Zylinder Ø12.42 mm, Achse X.

- starre Base gegen Rohr: kein unerwünschtes Kollisionsvolumen
- obere Sattelkontur muss den dokumentierten Freiraum einhalten
- untere PETG-Klemmhälfte: nur die dokumentierte kleine Vorspannung ist erlaubt

## Rohrklemme / Pins

- beide Klemmenpositionen X = ±90 mm
- alle Pinbohrungen zylindrisch und gleichachsig
- Pin Ø4.0 mm
- Bohrung Ø4.6 mm
- geschlossene Base ↔ Rack-Lower ohne unerwünschte Solid-Kollision
- Pins laufen ausschließlich durch die vorgesehenen Lochvolumina
- Pin-Clip muss in der vorgesehenen Nut sitzen können

## Integrierter Anti-Rotationsanschlag

Der separate V-Sattel/Diagonalstreben-Stabilisator ist verboten und darf in v50 nicht mehr erzeugt werden.

Stattdessen werden an beiden Klemmenstationen integrierte nach unten gezogene Innenanschläge geprüft:

- Anschlag ist Bestandteil der Base und mit der Klemmenwurzel massiv verbunden
- X-Breite Ziel 24 mm je Station
- Wandstärke Ziel 6 mm
- Wurzelradius Ziel ≥4 mm
- Kontaktbereich umfasst den Bereich um Z=0 des oberen Gepäckträgerrohres
- nominaler Freiraum zur definierten Rack-Edge-/Tangential-Prüffläche 0.15–0.25 mm
- keine Kollision mit dem Ø12.42-mm-Prüfrohr in Montageposition
- keine Kollision mit Rack-Lower in geschlossenem Zustand
- Rack-Lower muss den vorgesehenen Montage-/Öffnungsweg weiterhin erreichen
- kein Teil des Anschlags darf in den konservativen Schutzblech-Freiraum außerhalb der lokalen Klemmenzone hineinragen

Zusätzlich wird eine kleine Rotationsprüfung ausgeführt: Bei simuliertem Abkippen des Außenarms muss der Innenanschlag vor einer relevanten Rotation die Rack-Edge-Prüffläche berühren. Damit wird bestätigt, dass er tatsächlich als Anti-Rotationsanschlag wirkt und nicht nur dekorativ in der Nähe liegt.

## Boxrand

Konservatives Prüfvolumen:

- 16.45 mm horizontal
- 16.45 mm vertikal
- Außenkante Y = 244.665 mm
- Auflage Z = 39.54 mm

Checks:

- geschlossene Platte: kein unerwünschtes Volumen im Boxrand
- Untergriff liegt hinter/unter der Außenkante
- geöffnet bei +4.5 mm: Untergriff gibt Außenkante frei
- Base/Platte: bei 0, 1, 2, 3, 4 und 4.5 mm Öffnung kein Kollisionsvolumen

## Plattenführung

- keine offenen T-Schlitze im tragenden Hauptkörper
- Schraubenbohrungen sind echte Durchgangsbohrungen
- Platte kann nur entlang Y verfahren
- Führungsspiel 0.35–0.45 mm je Seite

## Lead Screw

Print-Prototyp:

- RH Ø8×2.0 mm
- 360° = 2.0 mm axial
- 90° = 0.5 mm axial
- korrekte Rotation + Translation läuft frei
- falsche Phasenrotation erzeugt messbare Gewindeüberschneidung

## Schraube ↔ Klemmplatte

- Spindelschulter drückt auf die äußere Plattenseite
- Ø6-Journal läuft durch Ø6.5-Bohrung
- innerer Retainer liegt vollständig in der Senkung
- Retainer ragt nicht über die innere Kontaktfläche hinaus
- Spindel kann Platte drücken und beim Aufschrauben zurückziehen

## Knob

- Knob und Spindel sind getrennte Teile
- AF10-Spindelantrieb passt mit dokumentiertem FDM-Spiel in den Knob
- axiale Retainer-Mutter/Kappe ist separat
- Hauptdrehmoment wird formschlüssig über den Sechskant übertragen

## Außenmaße

Der Build schreibt die maximale Breite des geschlossenen Systems inklusive Knob in den Report. Ziel: deutliche Verbesserung gegenüber v45/v47 und möglichst <690 mm bei 600-mm-Eurobox.

## Tragarm-Sanity-Check

Automatisch dokumentieren:

- Querschnittsfläche
- Flächenträgheitsmoment Ix
- statische Biegespannung/Enddurchbiegung bei 16 kg / 4 Armen
- 3×-Dynamikfall
- Rechen-E-Modul PETG = 1500 MPa

Referenzquerschnitt v50: 32×30-mm Doppelsteg-I-Profil mit 4.5-mm Flanschen und zwei 3.2-mm Stegen, A≈422.4 mm², Ix≈52,243 mm⁴.

## Build-Gate

Der GitHub-Actions-Job beendet sich mit Fehler, wenn ein harter Check fehlschlägt. Ein ZIP mit fehlgeschlagener Validierung darf nicht als finales v50-Artefakt hochgeladen werden.
