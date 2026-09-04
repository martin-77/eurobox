# v50 – automatische Validierung

Ein Build darf nur als `eurobox-v50` Artefakt veröffentlicht werden, wenn alle harten Checks bestanden sind.

## Geometrie

Für jedes STEP-Teil nach Export **und erneutem STEP-Import**:

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

- starre Base gegen Rohr: `common.Volume == 0`
- untere PETG-Klemmhälfte: nur die dokumentierte kleine Vorspannung ist erlaubt

## Rohrklemme / Pins

- beide Klemmenpositionen X = ±90 mm
- alle Pinbohrungen zylindrisch und gleichachsig
- Pin Ø4.0 mm
- Bohrung Ø4.6 mm
- geschlossene Base ↔ Rack-Lower ohne unerwünschte Solid-Kollision
- Pins dürfen Base/Rack-Lower nicht schneiden; nur das Lochvolumen durchlaufen
- Pin-Clip muss in der vorgesehenen Nut sitzen können

## Boxrand

Konservatives Prüfvolumen:

- 16.45 mm nach außen
- 16.45 mm nach unten
- Außenkante Y = 244.665 mm
- Auflage Z = 39.54 mm

Checks:

- geschlossene Platte: kein unerwünschtes Volumen in Boxrand
- Untergriff liegt hinter/unter der Außenkante
- geöffnet bei +4.5 mm: Untergriff gibt Außenkante frei
- Base/Platte: bei 0, 1, 2, 3, 4 und 4.5 mm Öffnung kein Kollisionsvolumen

## Plattenführung

- keine offenen T-Schlitze im tragenden Hauptkörper
- Schraubenbohrungen sind echte Durchgangsbohrungen
- Plate kann nur entlang Y verfahren
- Führungsspiel Ziel 0.35–0.45 mm pro Seite

## Lead Screw

Print-Prototyp:

- RH Ø8×2.0 mm
- 360° entsprechen 2.0 mm axialem Weg
- 90° entsprechen 0.5 mm
- korrekte Rotation + Translation muss in der Lead-Nut frei laufen
- Translation mit falscher Phasenrotation muss messbare Gewindeüberschneidung erzeugen; damit wird ausgeschlossen, dass die vermeintliche Gewindegeometrie nur aus ringförmigen Segmenten besteht

## Schraube ↔ Klemmplatte

- Spindelschulter drückt auf die äußere Plattenseite
- Ø6-Journal läuft durch Ø6.5-Bohrung
- innerer Retainer liegt vollständig in der Senkung
- Retainer darf nicht über die innere Kontaktfläche hinausragen
- Spindel kann die Platte sowohl drücken als auch beim Aufschrauben zurückziehen

## Knob

- Knob ist ein eigenes Teil
- Spindel ist ein eigenes Teil
- AF10-Spindelantrieb passt mit dokumentiertem FDM-Spiel in Knob
- axiale Retainer-Mutter/Kappe ist separat
- Hauptdrehmoment wird formschlüssig über den Sechskant übertragen

## Außenmaße

Der Build schreibt die tatsächliche maximale Breite des geschlossenen Systems inklusive Knob in den Report. Ziel ist eine deutliche Verbesserung gegenüber v45/v47 und möglichst < 690 mm für die komplette, beidseitige Montage an einer 600-mm-Eurobox.

## Tragarm-Sanity-Check

Analytisch dokumentieren:

- Querschnittsfläche
- Schwerpunkt des Doppelsteg-I-Profils
- Flächenträgheitsmoment I_x
- statische Biegespannung/Enddurchbiegung bei 16 kg / 4 Armen
- zusätzlicher 3×-Dynamikfall
- Rechen-E-Modul PETG = 1500 MPa

Dieser Check ersetzt keine FEA, verhindert aber erneut offensichtlich zu flache Tragquerschnitte.

## Focus-Strebenstütze

Weil Winkel/Durchmesser der diagonalen Strebe nicht exakt vermessen sind:

- V-Nut muss einen Bereich verschiedener Rohrdurchmesser aufnehmen können
- Kabelbinderkanäle müssen echte Durchgänge sein
- Stützschraube muss in der Höhe verstellbar sein
- dieser Part wird nicht als primärer Lastpfad der Box gerechnet

## Build-Gate

Das GitHub-Actions-Skript beendet den Job mit Fehler, wenn einer der harten Checks fehlschlägt. Ein ZIP mit fehlgeschlagener Validierung darf nicht als finales v50-Artefakt hochgeladen werden.