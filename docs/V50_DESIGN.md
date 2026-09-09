# Eurobox v50 – finaler Konstruktionsstand

## Ziel

Werkzeuglos abnehmbarer PETG-Trägeradapter für eine quer montierte **600×400-mm-Eurobox** auf dem originalen Massload-3-leg-Gepäckträger des FOCUS THRON² EQP MY2023.

Verbindlich sind die gemessenen Datums aus `MEASUREMENTS.md`, die Parameter in `V50_DIMENSIONS.json` und die automatischen Validierungen. Alte v45/v47/v49-BREP-Geometrie ist keine Quelle für v50.

## Koordinatensystem

- X = Fahrtrichtung, **-X vorne / +X hinten**
- Y = je Seitenmodul vom Rackrohr nach außen zur Box
- Z = oben
- Rackrohrmitte je Modul = Y0/Z0

Global liegen die Rackrohrzentren bei Y=±55.335 mm und die äußeren Boxkanten exakt bei Y=±300.000 mm.

## Handed Bases und hinterer Montageanschlag

Die finale Konstruktion benötigt zwei unterschiedliche Bases:

- RIGHT: hinterer Anschlag lokal X=+150…+190 mm
- LEFT: gespiegelter Anschlag lokal X=-190…-150 mm

Das linke Modul wird bei der Montage 180° um Z gedreht. Dadurch landen beide Anschläge global am gleichen hinteren (+X) Ende. Vorne gibt es keinen Anschlag.

Der Anschlag ist 50 mm hoch, 4 mm dick und über einen tiefen Root/Gusset in den hinteren Lastpfad eingebunden. Er ist ausschließlich Montage-/Anti-Flop-Hilfe und kein zusätzlicher primärer Lastpfad. Ein separater V-Sattel an der diagonalen Rackstrebe wird nicht mehr exportiert.

## Rackbefestigung

Pro Seitenmodul zwei Klemmstationen bei X=±90 mm auf dem realen Ø12.42-mm-Rackrohr.

- obere starre Sattelhälfte in der Base
- separate flexible `rack_lower`-Hälfte
- Pivot Y=-12.0 / Z=-5.5 mm
- Pin Ø4.0 / Loch Ø4.6 mm
- Öffnungssweep 0…-75°
- Rohr muss spätestens bei -45° vollständig frei sein
- positiver Verschluss über M4-Schraube + separate Captive-Nut + Handknob
- gedruckte M4-Hardware für den Prototyp; Metall-M4 bleibt Drop-in-Option

## Tragstruktur und Druckorientierung

Die langen Lastpfade sind keine offenen I-Träger mehr. Final werden **geschlossene, verjüngte Solids** verwendet:

- 32 mm Breite oben
- 20 mm Breite unten
- 30 mm Bauhöhe
- 7 mm Taper
- Auflageoberseite Z=39.54 mm

Die komplette Base wird für den Druck 180° um X gedreht, sodass die Z=39.54-mm-Ebene auf dem Druckbett liegt. Crosshead, Guide und Cage sind auf diese Orientierung abgestimmt. Große strukturelle Supports und ein fester Unter-Rim-Bridge sind nicht vorgesehen.

## Boxklemmung – inboard statt außen

Die frühere außenliegende Schraub-/Nut-Käfiggeometrie überschritt die 600-mm-Boxbreite und ist verworfen.

Final sitzt die Boxklemmung **innen an der inneren Vertikalfläche des unteren 16.45-mm-Randes**:

- innere Randfläche lokal Y=228.215 mm
- Plattenkörper geschlossen Y=220.215…228.215 mm
- 4.2-mm-Untergriff unter der inneren Randkante
- 5.5 mm Öffnungsweg nach innen (-Y)
- 0.5 mm Klemm-Preload nach außen (+Y)
- zwei echte Durchgangsbohrungen in der Platte
- Schraubachsen X=±42 mm / Z=31 mm

Die Platte dreht nicht. Eine Spindelschulter überträgt die Klemmkraft; die axiale Retention zieht die Platte beim Öffnen aktiv zurück.

## Lead-Screw-System

Der Prototyp bleibt beim bewährten groben Druckgewinde:

- RH 8×2
- Gewindelänge 23 mm
- separate Lead-Nut-Cartridge
- Cross-Pin + C-Clip im unteren post-thread Tail
- Base selbst besitzt kein Arbeitsgewinde
- separater Knob und separate Retainer-Nut

Für die inboard-Anordnung werden Spindel, Lead-Nut, Knob und Retainer-Nut als **proper 180° Z rotation** orientiert. Es gibt keine Spiegelung der Thread-Solids; die RH-Chiralität bleibt erhalten. Positive Öffnung bewegt die Spindel nach -Y und verwendet entsprechend das umgekehrte Welt-Y-Rotationsvorzeichen.

## Harte Breitenregel

**Kein Bauteil der montierten Halterung darf die 600-mm-Eurobox seitlich überragen.**

CI ermittelt die tatsächlichen BoundBoxes von Base, Platte, Spindel, Lead-Nut, Knob, Retainer, Pin und Clip in:

- 0.5 mm Preload
- geschlossen
- 5.5 mm vollständig geöffnet

Aus Rack-CTC und dem jeweils größten lokalen Y-Maximum wird die globale Halterbreite berechnet. Obergrenze: 600.00 mm, numerische Toleranz 0.02 mm. Der Build schlägt bei Überschreitung fehl.

## Validierung vor Publish

Publish ist nur erlaubt, wenn gleichzeitig bestanden sind:

1. FreeCAD-Source-Solids gültig und einteilig;
2. STEP-Reimport gültig;
3. reales Ø12.42-mm-Rackrohr kollisionsfrei zur Base;
4. Rack-Lower-Sweep und Pivot-Hardware funktionsfähig;
5. hinterer Anschlag korrekt handed und nur hinten;
6. Box-Rim kollisionsfrei zur Base;
7. Platte geschlossen/offen kollisionsfrei und bei voller Öffnung freigegeben;
8. RH8×2 in korrekter Phase kollisionsfrei, falsche Phase mit echter Interferenz;
9. 0.5-mm-Preload mechanisch möglich;
10. vollständige Halterbreite ≤600 mm;
11. LEFT/RIGHT-STL unterschiedlich, physikalisch gespiegelt und watertight;
12. alle STL einteilig, winding-consistent und positiv volumig;
13. Assembly-Preview gerendert;
14. erst danach FCStd/STEP/STL in `cad/v50` publiziert.

## Druckziel

- Prusa CORE One L
- PETG
- 0.4-mm-Düse
- 0.20-mm-Layer
- mindestens 3 Perimeter für den strukturellen Prototyp
- kein großflächiger Support an den langen Lastpfaden oder Boxkontaktflächen

## Lastgrenze

Bis das konkrete Typenschild des montierten Massload-Trägers verifiziert ist, bleibt **16 kg Rack-Gesamtzuladung** die konservative Obergrenze. Vereinfachte 3×-Dynamikrechnungen sind ausschließlich Sanity-Checks und keine FEA oder Herstellerfreigabe.
