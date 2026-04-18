# Untertitel-Editor

## Text bearbeiten

Klicke auf das Stift-Symbol neben einer Äußerung, um den Text bearbeitbar zu machen — oder bewege dich während der Bearbeitung mit Tab bzw. Shift+Tab zwischen den Zeilen. Änderungen werden lokal gehalten, bis du speicherst; du kannst also mehrere Äußerungen bearbeiten, bevor du etwas überträgst. Esc bricht die aktuelle Bearbeitung ab. Tab übernimmt die aktuelle Änderung und springt zur nächsten Äußerung, Shift+Tab rückwärts.

## Zeitstempel und Sprecher bearbeiten

Neben jedem Start- und End-Zeitstempel öffnet ein Stift-Symbol einen Inline-Editor im Format `HH:MM:SS`. Ein geänderter Startzeitstempel wirkt rückwärts auf vorherige Zeilen, die sich sonst überschneiden würden; ein geänderter Endzeitstempel entsprechend vorwärts. Vor der Übernahme zeigt eine Rückfrage, wie viele benachbarte Zeilen betroffen wären.

In der Sprecherspalte stehen zwei Symbole: der Stift benennt den Sprecher nur in dieser Zeile um, das Personen-Symbol öffnet den Sprecherzuordnungs-Dialog, um den Sprecher überall umzubenennen. Ein farbiger Punkt markiert den Sprecher einer Zeile — Zeilen desselben Sprechers teilen sich eine Farbe.

## Zeilenoperationen

Beim Hovern über eine Zeile erscheinen im Textfeld drei Aktionen: Mit der nächsten Äußerung zusammenführen (Texte vereinen und Endzeit verlängern), Plus-Symbol für eine neue leere Zeile darunter und ein Papierkorb-Symbol zum Löschen (mit Rückfrage). Auf breiten Bildschirmen steht das Plus-Symbol zusätzlich in der Zeilennummern-Spalte bereit.

## Suche

Die Suchleiste über dem Editor filtert nach Text, Sprecher oder beidem — die Umschalter **Text** und **Sprecher** wechseln den Umfang. Treffer werden hervorgehoben, und die Zeile direkt davor und danach wird als Kontext mit angezeigt. Zeilen, die weder Treffer noch Kontext sind, werden zu Trennzeilen („… N ausgeblendet …") zusammengefasst. Die Trefferanzahl neben dem Eingabefeld zeigt, wie viele Äußerungen passen.

## Zeitstempel und Mediaplayer

Der Mediaplayer oben in der Detailansicht bleibt mit dem Editor synchronisiert. Ein Klick auf eine Zeile — egal ob Zeitstempel, Sprecher oder Text — springt im Player zum Anfang der Äußerung. Während der Wiedergabe wird die aktuelle Äußerung hervorgehoben, und der Editor scrollt automatisch mit.

## Änderungen speichern

Änderungen werden nicht automatisch gespeichert. Liegen lokale Änderungen vor, erscheinen ein Hinweis sowie die Schaltflächen **Speichern** und **Original wiederherstellen**. „Wiederherstellen" verwirft alle lokalen Bearbeitungen und lädt das gespeicherte Transkript vom Server neu. Versuchst du, die Seite mit ungespeicherten Änderungen zu verlassen, fragt ein Dialog nach. Nach dem Speichern wird der aktualisierte Text in allen Exportformaten verwendet — SRT, VTT, Nur-Text und weitere.

## Verfeinern und Übersetzen aus dem Editor

Ist ein LLM konfiguriert, zeigt die Editor-Toolbar die Schaltflächen **Transkription verfeinern** und **Übersetzen**. Jede öffnet einen kleinen Dialog — Verfeinerung nimmt optional einen Kontexthinweis entgegen (als Preset speicherbar), Übersetzung eine Zielsprache. Die erzeugte Ansicht erscheint neben dem Original, und ein Ansichts-Umschalter erlaubt den Wechsel zwischen **Original**, **Verfeinert** und der übersetzten Fassung. Verfeinerte und übersetzte Ansichten sind schreibgeschützt; Änderungen gelten nur im Original. Mit den kleinen Lösch-Schaltflächen neben dem Umschalter entfernst du eine verfeinerte oder übersetzte Fassung wieder.

## Verfeinerungsänderungen prüfen

Ist die verfeinerte Ansicht aktiv, beschreibt ein Zusammenfassungs-Banner, was das LLM geändert hat, nennt Provider und Modell und zeigt den gegebenenfalls übergebenen Kontext. Vom LLM veränderte Zeilen sind mit einem bernsteinfarbenen Punkt und einem linken Rand markiert — ein Klick auf eine solche Zeile blendet einen Vergleich zwischen Originaltext und verfeinertem Text ein. Weitere Informationen findest du unter **Verfeinerung** und **Übersetzung**.
