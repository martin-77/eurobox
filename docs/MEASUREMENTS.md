# Eurobox v50 – Maße und feste Datums

Koordinatensystem: **X = Fahrtrichtung** (`-X` vorne, `+X` hinten), **Y = vom jeweiligen Gepäckträgerrohr nach außen**, **Z = oben**. Gemessene Werte werden nicht mit aus Fotos geschätzten Millimeterwerten vermischt.

## Direkt gemessen / daraus fest berechnet

| Parameter | Wert |
|---|---:|
| Eurobox quer | 600.00 mm |
| Eurobox in Fahrtrichtung | 400.00 mm |
| unterer Rand horizontal | 16.45 mm |
| unterer Rand vertikal | 16.45 mm |
| Gepäckträgerrohr Ø | **12.42 mm** |
| Gepäckträger Außenbreite | 123.09 mm |
| Rohr Mitte–Mitte | 110.67 mm |
| Rohrmittelpunkte global Y | ±55.335 mm |
| Klemmenabstand X | 180.00 mm |
| Klemmenpositionen je Modul | X = ±90.00 mm |
| Rohrmitte → äußere Boxkante | 244.665 mm |
| globale Boxkanten | Y = ±300.000 mm |
| Rohroberkante | Z = +6.21 mm |
| Schutzblechoberkante | Z = +34.54 mm |
| Boxauflage | Z = +39.54 mm |
| Restabstand Boxauflage → Schutzblech | 5.00 mm |

Ø12.00 mm aus frühen Varianten ist **kein** gültiger Rackdurchmesser. Die starre Base wird gegen das reale Ø12.42-mm-Rohr geprüft.

## Finale v50-Tragstruktur

Die frühere offene Doppelsteg-I-Geometrie ist nicht mehr der finale Druckstand. Die beiden langen Lastpfade pro Seitenmodul sind **geschlossene, nach unten verjüngte Solids**, damit PrusaSlicer den Innenbereich mit Infill statt mit großflächigem Support behandeln kann.

- oben 32 mm breit
- unten 20 mm breit
- 30 mm Bauhöhe
- 7 mm Verjüngung
- Oberseite / Auflage Z = 39.54 mm
- Base wird für den Druck um 180° um X gedreht; Z=39.54 liegt dann auf dem Bett

Crosshead, Guides und Käfig sind so ausgelegt, dass kein großes festes Bauteil unter dem hängenden Boxrand nach außen läuft.

## Rack-Klemme

Je Seitenmodul gibt es zwei identische Rack-Klemmstationen. Die obere Hälfte ist Bestandteil der Base, die untere Hälfte `rack_lower` ist separat.

- reales Rohr Ø12.42 mm
- obere starre Sattelkontur ca. Ø12.52 mm
- untere PETG-Sattelkontur ca. Ø12.30 mm
- Pivot Y = -12.0 mm / Z = -5.5 mm
- Pin Ø4.0 mm
- Pinbohrung Ø4.6 mm
- Öffnungssweep bis -75°; spätestens bei -45° muss das Rohr frei sein
- positiver Verschluss über separate M4-Schraube, separate Captive-Nut und Handknob

## Rear-only Montageanschlag

Die finale Base ist **handed**. Rechts sitzt der einzige Anschlag lokal hinten bei X=+150…+190 mm, links gespiegelt bei X=-190…-150 mm. Nach der 180°-Montagedrehung des linken Moduls liegen beide Anschläge global am gleichen hinteren Ende.

Der Anschlag ist 50 mm hoch und 4 mm dick und über Root/Gusset an den hinteren Lastpfad angebunden. Er ist Montage-/Anti-Flop-Hilfe, **kein zusätzlicher Hauptlastpfad**. Ein separater V-Sattel an der diagonalen Rackstrebe gehört nicht mehr zum finalen Teilesatz.

## Box-Klemmung – innerhalb des 600-mm-Umrisses

Die frühere außenliegende Spindel-/Nut-Käfiggeometrie war zu breit. Final sitzt der komplette Schraubmechanismus **innen am unteren Boxrand**.

- innere Randfläche lokal Y = 228.215 mm
- geschlossene Plattenkörper-Lage Y = 220.215…228.215 mm
- Untergriff 4.2 mm unter der inneren Randkante
- Öffnungsweg 5.5 mm **nach innen (-Y)**
- definierter Preload 0.5 mm nach außen (+Y)
- Spindelachsen X = ±42 mm
- Spindelachse Z = 31.0 mm
- RH 8×2, Gewindelänge 23 mm
- separate gedruckte Lead-Nut mit Cross-Pin/C-Clip

Die vollständige Halterung muss in Preload-, geschlossener und vollständig geöffneter Stellung zwischen global Y=-300 und +300 bleiben. Das ist ein **Hard-Gate in CI**, nicht nur ein Reportwert.

## Belastungsgrenze

Für den konkreten v50-Entwurf wird konservativ mit **16 kg maximaler Rack-Gesamtzuladung** gearbeitet, solange das Typenschild des tatsächlich montierten Massload-Trägers nicht einen anderen belastbaren Wert bestätigt. Der 3×-Dynamikfall in den Skripten ist nur ein Sanity-Check, kein FEA-Nachweis und keine Freigabe oberhalb der Herstellerlast.
