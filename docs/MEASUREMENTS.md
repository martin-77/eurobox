# Eurobox v50 – Maße und Datums

Koordinatensystem des CAD-Modells:

- **X** = Fahrtrichtung
- **Y** = quer zum Fahrrad, vom Gepäckträgerrohr zur Eurobox-Außenkante
- **Z** = nach oben

Die Werte sind bewusst nach Herkunft getrennt. Gemessene Werte werden nicht mit aus Fotos geschätzten Werten vermischt.

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

Wichtig: Ø12.00 mm aus älteren Versionen war nur ein Vorspann-/Konstruktionsziel. **Das reale Rohr ist Ø12.42 mm; starre Geometrie darf dieses Volumen nicht schneiden.**

## 2. Für v50 festgelegte Konstruktionswerte

### Tragstruktur

- zwei tragende Arme pro Seitenmodul, X-Mitten weiterhin ±90 mm
- Armquerschnitt Ziel: **32 mm breit × 30 mm strukturelle Höhe**
- obere und untere Flansche: **4.5 mm**
- zwei innere Stege: **3.2 mm**
- volle Tiefe beginnt erst außerhalb des Rohr-/Klemmbereichs
- Auflageoberseite bleibt exakt **Z = 39.54 mm**

Der Doppelsteg-I-Querschnitt ersetzt die alten 28 × 8 mm Flacharme. Er erhöht die vertikale Biegesteifigkeit stark, ohne einen massiven Vollquerschnitt zu erzeugen.

### Box-Klemmung

- Schraubachsen: X = ±42.0 mm
- Schraubachse: Z = 31.0 mm
- geschlossene Plattenposition: Innenfläche bei Y = 244.665 mm
- Plattendicke im Hauptkörper: 8.0 mm
- Plattenbreite Hauptkörper: 118 mm
- Öffnungsweg Ziel: **4.5 mm**; mindestens 4.0 mm müssen kollisionsfrei nutzbar sein
- Untergriff unter Boxrand: Ziel **4.0–4.3 mm**
- Führungsfreiraum für PETG: 0.35–0.45 mm je Führungsseite
- echte Durchgangsbohrungen in der Klemmplatte; keine offenen T-Schlitze

### Test-Leitspindel

Für den ersten vollständig gedruckten Funktionstest wird bewusst kein miniaturisiertes Pseudo-M4 verwendet:

- rechtsgängiges Leitgewinde
- Nenn-Ø: **8.0 mm**
- Steigung: **2.0 mm/U**
- gedruckter Gewindeeinsatz ist ein **separates austauschbares Lead-Nut-Modul**
- Base selbst bleibt damit vom Testgewinde unabhängig
- später kann derselbe Bauraum einen M4-/Metallgewinde-Adapter bzw. Heat-Set-Insert-Träger aufnehmen

Die Kinematik ändert sich bei der späteren Metallversion nicht: Spindel dreht in feststehendem Gewinde, wandert axial und nimmt die nicht rotierende Klemmplatte über Schulter + axialen Retainer mit.

### Platte ↔ Spindel

- glatter Lagerzapfen an der Testspindel: Ø6.0 mm
- Platten-Durchgangsloch: Ø6.5 mm
- Druckschulter an Spindel: ca. Ø11 mm
- innerer Retainer liegt in einer versenkten Tasche und darf die Boxkontaktfläche nicht überragen
- Retainer wird als separates C-/E-Clip-artiges Testteil ausgeführt

### Knob ↔ Spindel

- **Knob und Spindel sind getrennte Druckteile**
- Drehmomentübertragung formschlüssig über Sechskant
- Ziel AF Spindel: 10.0 mm
- Ziel AF Knob-Socket: 10.3–10.4 mm
- axiale Sicherung über separates Retainer-Gewinde + separate Mutter/Kappe
- die Sicherung überträgt nicht das Hauptdrehmoment

### Rohrklemme

- starre obere Sattelkontur: Ziel Ø12.52–12.56 mm
- reale Rohrkontur: Ø12.42 mm
- starre Base/Rohr: Kollisionsvolumen muss 0.000 mm³ sein
- untere Klemmhälfte darf eine kleine definierte PETG-Vorspannung erzeugen
- Pin-Löcher werden als echte Zylinder modelliert und nach Export erneut vermessen

## 3. Noch nicht exakt vermessene Focus-Geometrie

Folgende Daten werden **nicht** aus Fotos in Millimeterwerte umgedeutet:

- Durchmesser der diagonalen Gepäckträgerstreben Richtung Achse
- exakter Winkel dieser Streben
- exakte Lage dieser Streben relativ zur Unterseite unseres Arms

Deshalb bekommt v50 dort keine starre, vermeintlich passgenaue Rohrschelle. Der Anti-Flop-Stabilisator verwendet eine breite V-Auflage, Kabelbinderkanäle und eine höhenverstellbare Auflage. Dadurch kann er am realen THRON² EQP angepasst werden, ohne eine nicht gemessene Geometrie zu erfinden.

## 4. Belastungsziel

Die Konstruktion wird intern auf die bekannte Größenordnung des originalen EQP-Gepäckträgers ausgelegt und mit einem zusätzlichen dynamischen Faktor für den **Halter selbst** geprüft. Dieser Faktor erhöht nicht die zulässige Herstellerlast des Fahrrads/Gepäckträgers.

Für die einfache Balkenprüfung von v50 wird dokumentiert:

- 16 kg Gesamtlast als Träger-Zielgröße, sofern durch FOCUS-Unterlage bestätigt
- 4 tragende Arme im kompletten System (2 pro Seite)
- zusätzliche 3×-Last als geometrischer Sanity-Check gegen Schlag-/Dynamiklasten
- PETG-Rechen-E-Modul 1500 MPa als konservativer Näherungswert

Das ist kein FEA-Nachweis und keine Freigabe oberhalb der Herstellerlast.