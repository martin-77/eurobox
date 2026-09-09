# Eurobox v50 – Design-Dokumentation

Die frühere zweite, teilweise widersprüchliche v50-Konstruktionsbeschreibung wurde entfernt, damit Maße und Architektur nicht erneut auseinanderlaufen.

Verbindliche Quellen sind jetzt:

1. **`V50_DESIGN.md`** – finale Architektur und Konstruktionslogik.
2. **`V50_DIMENSIONS.json`** – maschinenlesbare harte Datums und finale Designparameter.
3. **`MEASUREMENTS.md`** – gemessene Werte und deren Herkunft.
4. **`VALIDATION_V50.md`** – Pflichtprüfungen vor einem Publish.
5. **`scripts/build_v50.py` + geordnete `apply_v50_*`-Finalisierung** – tatsächlich gebaute Geometrie.

Wichtig für den finalen v50-Stand: explizite handed LEFT/RIGHT-Bases mit genau einem hinteren Montageanschlag, geschlossene supportarme Lastpfade und eine **inboard** liegende Boxklemmung. Die komplette montierte Halterung muss innerhalb der globalen Euroboxkanten Y=±300 mm bleiben; CI behandelt 600 mm als Hard-Gate.
