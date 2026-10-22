# Transkriptionseinstellungen

## Sprache und Modell

Die Gruppe **Transkription** enthält zwei Felder.

**Sprache für die Transkription:** Voreingestellt ist **Automatisch erkennen**; dann bestimmt die Spracherkennung die Sprache selbst. Kennen Sie die Sprache, wählen Sie sie aus der Liste. Oben stehen Deutsch, Englisch, Spanisch, Französisch und Türkisch, darunter nach einem Trennstrich alle weiteren Sprachen in alphabetischer Reihenfolge.

**Modell:** Das Feld ist schreibgeschützt und zeigt {{default_model}}. Es ist das einzige konfigurierte Modell, daher gibt es nichts auszuwählen. Jede Transkription verwendet es.

## Sprechende erkennen

Die Gruppe **Sprechende** enthält den Schalter **Sprechende erkennen**. Er ist voreingestellt eingeschaltet und trennt die Beiträge verschiedener Personen. Spricht nur eine Person, können Sie ihn ausschalten.

Ist der Schalter an, können Sie die Zahl der Personen eingrenzen: **Mindestanzahl Personen** (voreingestellt 1) und **Höchstanzahl Personen** (voreingestellt 2). Erlaubt sind Werte von 1 bis 20. Setzen Sie die Mindestanzahl über die Höchstanzahl, zieht die Höchstanzahl nach, und umgekehrt.

Namen für die erkannten Personen vergeben Sie nach der Transkription im Reiter **Untertitel** unter **Namen der Sprechenden**.

## Erweiterte Optionen

Mit **Erweiterte Optionen** blenden Sie zwei weitere Felder ein. Beide sind optional.

- **Anfangs-Prompt:** Kontext für die Transkription, zum Beispiel das Thema oder Eigennamen.
- **Schlüsselwörter:** kommagetrennte Fachbegriffe.

Beide Angaben gehen an die Spracherkennung. Leere Felder werden nicht übermittelt.

## Voreinstellungen

Die Gruppe **Voreinstellungen** ist die erste Gruppe.

- **Transkription:** Dieses Auswahlfeld erscheint, sobald Sie Voreinstellungen gespeichert haben. Wählen Sie dort eine Voreinstellung, übernimmt sie Sprache, Sprechende, Anfangs-Prompt und Schlüsselwörter.
- **Als Voreinstellung speichern:** Geben Sie einen Namen ein und bestätigen Sie mit dem Häkchen oder mit der Eingabetaste. transkribierBAR speichert die aktuellen Einstellungen unter diesem Namen.
- **Pakete:** Dieses Feld erscheint, sobald Sie Pakete angelegt haben. Was es bewirkt, steht im Abschnitt „Hochladen“.

Voreinstellungen verwalten Sie auf der Seite **Voreinstellungen** in der Kopfzeile.

## Die Zusammenfassung

Nach dem Klick auf **Transkribieren** ersetzt eine Zeile die Einstellungen. Sie nennt den Dateinamen, die Größe, das Modell, die Sprache (**automatisch**, wenn Sie nichts gewählt haben), die Sprechenden (**keine Sprechenden** oder zum Beispiel **1–2 Personen**) und gegebenenfalls das Paket.
