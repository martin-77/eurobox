# Focus THRON² EQP 2023 – Einbaukontext für Eurobox v50

## Zweck dieser Datei

Diese Datei trennt Hersteller-/Modellinformationen von direkt am Fahrrad gemessenen CAD-Daten. Werte aus Fotos werden nicht als Millimetermaße behandelt.

## Bestätigter Modellkontext

Zielrad ist ein **FOCUS THRON² EQP Modelljahr 2023**. Für die Recherche wurden offizielle FOCUS-Produkt-/Archivunterlagen zum THRON² EQP 2023 sowie verfügbare Modellabbildungen herangezogen.

Die EQP-Ausstattung besitzt einen integrierten Gepäckträger über dem Hinterrad mit seitlichen bzw. diagonal Richtung Hinterachse laufenden Stützstreben. Das ist für v50 relevant, weil unser Seitenmodul nicht nur am oberen Rohr befestigt wird, sondern optional über einen kleinen Anti-Flop-Stabilisator an einer dieser Streben abgestützt werden kann.

## Vom konkreten Fahrrad gemessene Geometrie

Diese Werte haben für das CAD Vorrang vor Fotointerpretationen:

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

## Was aus den Focus-Unterlagen für die Formgebung relevant ist

Die Modellabbildungen bestätigen qualitativ:

1. Die oberen Gepäckträgerrohre verlaufen über eine längere Strecke in Fahrtrichtung und eignen sich damit für zwei weit auseinanderliegende Klemmpunkte.
2. Der EQP-Träger ist über Streben Richtung Hinterachse abgestützt.
3. Das Schutzblech sitzt eng innerhalb/unterhalb des Gepäckträgerbereichs; unnötig tiefe Bauteile auf der Innenseite des oberen Rohres sind daher zu vermeiden.
4. Ein Zusatzteil zur Montageabstützung kann sinnvoll auf einer diagonalen Strebe sitzen, muss aber tolerant sein, solange Winkel und Rohrdurchmesser nicht direkt vermessen wurden.

## Herstellerlast

Für die Konstruktion wird die in den bisherigen FOCUS-Unterlagen für diesen EQP-Träger verwendete Größenordnung von **16 kg Gesamtlast** als obere Zielgröße des originalen Gepäckträgers geführt. Vor einer finalen Lastfreigabe wird der konkrete Herstellerhinweis für genau das am Fahrrad verbaute Trägermodell nochmals gegen dessen Kennzeichnung/Bedienunterlage abgeglichen.

Wichtig: Der in v50 verwendete dynamische 3×-Rechenfall ist **nur ein Sanity-Check der gedruckten Haltergeometrie**. Er erhöht die zulässige Herstellerlast des Gepäckträgers nicht.

## Nicht bekannte Focus-Maße

Noch nicht direkt gemessen:

- Durchmesser der diagonalen Strebe
- Winkel der diagonalen Strebe relativ zu unserem Arm
- exakter Abstand der diagonalen Strebe zur Unterseite des montierten v50-Moduls

Daraus folgt für v50:

- kein hart dimensionierter Snap-Fit auf diese Strebe;
- V-Sattel statt exakter Halbkreis;
- Kabelbinderbefestigung statt starrer Rohrschelle;
- höhenverstellbare Stütze statt festem Abstandshalter.

## Quellenstatus

Die verwendeten FOCUS-Unterlagen werden im Projekt als externe Modellreferenz behandelt. Die für die eigentliche Passung relevanten Millimeterwerte stammen dagegen aus der Vermessung des konkreten Fahrrads und stehen in `docs/MEASUREMENTS.md`.

Sobald am Fahrrad der Durchmesser und der Winkel der diagonalen Strebe nachgemessen sind, können diese drei offenen Werte ergänzt werden, ohne die Hauptkonstruktion zu ändern.