# Eurobox v50 – Maße und Datums

Koordinatensystem des CAD-Modells:

- **X** = Fahrtrichtung
- **Y** = quer zum Fahrrad, vom Gepäckträgerrohr zur Eurobox-Außenkante
- **Z** = nach oben

Gemessene Werte werden nicht mit aus Fotos geschätzten Werten vermischt.

## 1. Direkt am Fahrrad / an der Box gemessen

| Parameter | Wert | Status |
|---|---:|---|
| Eurobox Breite quer | 600.00 mm | hart |
| Eurobox Länge in Fahrtrichtung | 400.00 mm | hart |
| unterer Boxrand, horizontaler Vorsprung | 16.45 mm | hart |
| unterer Boxrand, vertikale Höhe | 16.45 mm | hart |
| Materialstärke am Rand | ca. 2–3 mm | Mess-/Praxiswert |
| Gepäckträgerrohr Außendurchmesser | **12.42 mm** | harte Kollisionsgrenze |
| Gepäckträger Außenbreite | 123.09 mm | hart |
| Rohr Mitte–Mitte quer | 110.67 mm | hart |
| nutzbare gerade Rohrlänge | ca. 220–240 mm | gemessen |
| Klemmenabstand in X | 180.00 mm | hart |
| Klemmenpositionen im Modul | X = ±90.00 mm | hart |
| Rohrmitte → Boxkante | 244.665 mm | berechnet aus Messung |
| Rohraußenfläche → Boxkante | 238.455 mm | berechnet |
| Rohroberkante Z | +6.21 mm | aus Ø12.42 |
| Schutzblechoberkante Z | +34.54 mm | hart |
| Eurobox-Auflage Z | +39.54 mm | hart |
| Restabstand Auflage → Schutzblech | 5.00 mm | hart |

Wichtig: Ø12.00 mm aus älteren Versionen war nur ein Vorspann-/Konstruktionsziel. Das reale Rohr ist Ø12.42 mm; starre Geometrie darf dieses Volumen nicht schneiden.

## 2. v50 Tragstruktur

Pro Seitenmodul zwei Doppelsteg-I-Träger:

- 32 mm Gesamtbreite
- 30 mm Gesamtbauhöhe
- 4.5-mm Ober- und Unterflansch
- zwei 3.2-mm Stege
- Querschnittsfläche ca. 422.4 mm²
- Ix ca. 52,243 mm⁴
- Auflageoberseite Z = 39.54 mm

Die volle Tiefe beginnt erst außerhalb des unmittelbaren Rohr-/Klemmbereichs.

## 3. Rohrklemme und integrierter Anti-Rotationsanschlag

Die Klemme besteht aus starrer Base oben und separatem `rack_lower` unten.

- starre obere Sattelkontur: Zielradius 6.31 mm
- reales Rohr: Radius 6.21 mm
- untere PETG-Hälfte: Zielradius 6.15 mm für kleine definierte Vorspannung
- Pin Ø4.0 mm
- Pinbohrung Ø4.6 mm

Der frühere separate V-Sattel an der diagonalen Focus-Strebe ist verworfen.

Stattdessen bekommt die Base an **beiden Klemmenstationen** einen nach unten gezogenen Innenanschlag zur Fahrradseite. Dieser Anschlag liegt mit geringem Montagefreiraum am Rand/der inneren Tangente der äußeren Gepäckträger-Längsstrebe und verhindert, dass das lange Außenmodul um das Rundrohr nach unten kippt.

Zielwerte für den ersten CAD-Stand:

- X-Breite des Anschlags je Klemmenstation: 24 mm
- Wandstärke: 6 mm
- Z-Bereich ungefähr +5 bis −8 mm um den Rohrmittelpunkt
- nominaler Freiraum: 0.15–0.25 mm
- Wurzelradius Ziel ≥4 mm

Der Anschlag ist ein **massiver Teil der Klemmenwurzel**. Es gibt keine V-Nut, keine Kabelbinder und keine separate Halterung an der diagonalen Strebe.

## 4. Box-Klemmung

- Schraubachsen: X = ±42.0 mm
- Schraubachse: Z = 31.0 mm
- geschlossene Plattenposition: Innenfläche bei Y = 244.665 mm
- Plattendicke Hauptkörper: 8.0 mm
- Plattenbreite Hauptkörper: 140 mm Ziel
- Öffnungsweg: 4.5 mm Ziel
- Untergriff: 4.2 mm Ziel
- Führungsspiel: 0.35–0.45 mm je Seite
- echte Durchgangsbohrungen; keine T-Schlitze

## 5. Test-Leitspindel

Für den vollständig gedruckten Funktionstest:

- RH Ø8×2 mm
- separate Lead-Nut
- Base bleibt unabhängig vom Testgewinde
- später austauschbar gegen M4-/Metall-/Heat-Set-Einsatz bei gleicher Kinematik

Platte ↔ Spindel:

- Lagerzapfen Ø6.0 mm
- Plattenloch Ø6.5 mm
- Druckschulter ca. Ø11 mm
- innerer Retainer versenkt und nicht überstehend

Knob ↔ Spindel:

- getrennte Teile
- AF10 an der Spindel
- Knob-Socket AF10.35 mm Ziel
- axiale Sicherung separat; Drehmomentübertragung über den Sechskant

## 6. Belastungsziel

Für das FOCUS THRON² 6.8 EQP Modelljahr 2023 nennt FOCUS einen Massload-3-leg-Gepäckträger mit **16 kg maximaler Zuladung**. Diese 16 kg sind die obere Zielgröße des Originalträgers.

Einfacher Balken-Sanity-Check der gedruckten Tragarme, E(PETG)=1500 MPa, angenommene freie Länge 220 mm:

- 16 kg / vier Arme: ca. 2.48 MPa, ca. 1.78 mm Enddurchbiegung
- 3× Dynamikfall: ca. 7.44 MPa, ca. 5.33 mm

Das ist kein FEA-Nachweis und keine Freigabe oberhalb der Herstellerlast.
