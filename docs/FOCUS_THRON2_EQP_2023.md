# Focus THRON² EQP 2023 – Einbaukontext für Eurobox v50

## Zweck

Diese Datei trennt Hersteller-/Modellinformationen von direkt am Fahrrad gemessenen CAD-Daten. Werte aus Produktfotos werden **nicht** als Millimetermaße behandelt.

## Bestätigter Modellkontext

Zielrad ist ein **FOCUS THRON² EQP Modelljahr 2023**. Die FOCUS-Archivseite führt für MY23 eigene EQP-Datenblätter und eine eigene `THRON² EQP MY23`-Explosionszeichnung. Das Rad ist ein 29-Zoll-Fully mit F.O.L.D.-Hinterbau; der EQP-Gepäckträger ist ein **Massload 3-leg** und bewegt sich mit dem Hinterbau.

Für die CAD-Passung haben die Messwerte am konkreten Fahrrad Vorrang.

## Hersteller-/Quellenlage zum Gepäckträger

Die publizierte Lastangabe ist nicht völlig konsistent:

- mehrere MY23 Händler-/Spezifikationsseiten nennen den Massload 3-leg mit **25 kg max. load**;
- die aktuelle FOCUS-Archiv-FAQ für diese THRON²-EQP-Generation nennt für den eigenen Gepäckträger **16 kg**, bzw. 8 kg pro Seite.

v50 setzt deshalb **16 kg als konservative Systemobergrenze für den Originalträger**, bis Typenschild/Artikelnummer des tatsächlich montierten Gepäckträgers am Fahrrad geprüft sind. Der Adapter darf diese Herstellergrenze nicht erhöhen.

## Quellen

FOCUS Archiv THRON² EQP 2022–2024:
https://www.focus-bikes.com/int/archive/e-bikes/thron/pdp-thron-eqp-2022-2024-bosch

FOCUS Archiv / FAQ THRON² 2022–2024:
https://www.focus-bikes.com/de_de/archive/e-bikes/thron/pdp-thron-2022-2024-bosch

MY23 Händler-Spezifikation mit Massload 3-leg / 25 kg als Gegenquelle:
https://www.bikes.de/shop/e-bikes/marke.focus/focus-thron2-6-8-eqp-2023/

## Vom konkreten Fahrrad gemessene Geometrie

- oberes Gepäckträgerrohr: **Ø12.42 mm**
- Gepäckträger Außenbreite: **123.09 mm**
- Rohr Mitte–Mitte: **110.67 mm**
- nutzbare gerade Rohrlänge: ca. **220–240 mm**
- zwei Klemmpunkte pro Seitenmodul: **180 mm** Abstand
- Klemmpunkte: **X = ±90 mm**
- Rohrmitte → Euroboxkante: **244.665 mm**
- Boxauflage **Z = 39.54 mm**
- Schutzblechoberkante **Z = 34.54 mm**
- verbleibende vertikale Reserve: **5.00 mm**

## Relevanz der Focus-Geometrie

Die obere Gepäckträgerstruktur besitzt zwei lange parallele Längsrohre. Die MY23-3-leg-Konstruktion besitzt zusätzlich diagonale Streben Richtung Hinterradachse. Daraus folgen für v50 zwei getrennte Aufgaben:

1. **Hauptlast:** ausschließlich über die beiden weit auseinanderliegenden Rohrklemmen eines Seitenmoduls und die steifen Tragarme.
2. **Montage-Stabilisierung / Anti-Flop:** optionaler kleiner Anschlag an einer diagonalen Rack-Strebe, damit das Seitenmodul ohne Box nicht um das runde obere Rohr nach unten klappt.

Die Diagonalstrebe wird ausdrücklich **nicht** zum primären Lastpfad. Ihr Durchmesser und Winkel sind noch nicht gemessen; deshalb ist dort keine erfundene formschlüssige Klemme zulässig. Die erste v50-Ausführung verwendet einen universellen V-Sattel / Anschlag mit großzügiger Anpassbarkeit. Nach Vermessung kann daraus ein definierter Clip werden.

Damit bleibt die Konstruktion mit dem vollgefederten Hinterbau kompatibel: Es wird nichts zwischen Hauptrahmen und bewegtem Hinterbau verspannt.

## Herstellerlast

Bis zur Prüfung des konkreten Rack-Aufklebers gilt für die Konstruktion:

- konservative Nutzlastgrenze Originalträger: **16 kg**;
- 25 kg wird als dokumentierte MY23-Gegenangabe geführt, aber nicht als v50-Auslegungsfreigabe verwendet;
- ein 3×-Dynamikfall in der Balkenrechnung ist nur ein Geometrie-Sanity-Check und keine Freigabe oberhalb der Herstellerlast.

## Noch zu messen

- Durchmesser einer diagonalen 3-leg-Strebe;
- Winkel/Position dieser Strebe relativ zum oberen Rackrohr;
- exakte Querkontur des Schutzblechs;
- Typenschild/Artikelnummer und Lastangabe des tatsächlich montierten Massload-Trägers.
