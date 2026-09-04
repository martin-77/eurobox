# Focus THRON² EQP 2023 – Einbaukontext für Eurobox v50

## Zweck

Diese Datei trennt Hersteller-/Modellinformationen von direkt am Fahrrad gemessenen CAD-Daten. Werte aus Fotos werden nicht als Millimetermaße behandelt.

## Bestätigter Modellkontext

Zielrad ist ein **FOCUS THRON² 6.8 EQP Modelljahr 2023**. Die offizielle FOCUS-Spezifikation führt für dieses Modell einen **Massload 3-leg Gepäckträger mit 16 kg maximaler Zuladung**.

Für die CAD-Passung haben die Messwerte am konkreten Fahrrad Vorrang.

## Vom konkreten Fahrrad gemessene Geometrie

- oberes Gepäckträgerrohr: Ø12.42 mm
- Gepäckträger Außenbreite: 123.09 mm
- Rohr Mitte–Mitte: 110.67 mm
- nutzbare gerade Rohrlänge: ca. 220–240 mm
- zwei Klemmpunkte pro Seitenmodul: 180 mm Abstand
- Klemmpunkte: X = ±90 mm
- Rohrmitte → Euroboxkante: 244.665 mm
- Boxauflage Z = 39.54 mm
- Schutzblechoberkante Z = 34.54 mm
- verbleibende vertikale Reserve: 5.00 mm

## Relevanz der Focus-Geometrie

Die obere Gepäckträgerstruktur besitzt lange parallele Längsstreben und eignet sich damit für zwei weit auseinanderliegende Klemmpunkte pro Seitenmodul.

Für v50 wird **keine separate Befestigung an den diagonalen Streben Richtung Hinterachse mehr verwendet**. Der zuvor erwogene V-Sattel mit Kabelbindern ist verworfen, weil er unnötig zusätzlichen Bauraum beansprucht und beim realen Fahrrad stören kann.

Stattdessen wird die Base im Bereich der beiden oberen Rohrklemmen zur Fahrradseite nach unten gezogen. Dieser integrierte Innenanschlag liegt mit geringem Freiraum am Rand/der seitlichen Kontur des Gepäckträgers an und verhindert ein Abkippen des langen Außenarms um das Rundrohr.

Vorteile für das THRON² EQP:

1. kein zusätzliches Teil an der Achs-/Diagonalstrebe;
2. keine Kabelbinder am Gepäckträger;
3. keine aus Fotos geschätzten Winkel oder Streben-Durchmesser nötig;
4. Anti-Rotation entsteht direkt dort, wo die Hauptklemme sitzt;
5. der Anschlag kann zusammen mit Rohr, Rack-Lower und Schutzblechfreiraum automatisiert geprüft werden.

## Herstellerlast

Für das Modelljahr 2023 nennt FOCUS:

- Rear rack: Massload, 3-leg
- Max. load: **16 kg**

Die v50-Berechnung darf diese Herstellergrenze nicht erhöhen. Der zusätzliche 3×-Dynamikfall dient nur als Sanity-Check der gedruckten Adaptergeometrie.

## Quellenstatus

Die Herstellerangaben dienen als Modell-/Lastreferenz. Die für die reale Passung verwendeten Millimeterwerte stammen aus der Vermessung des konkreten Fahrrads und stehen in `docs/MEASUREMENTS.md`.
