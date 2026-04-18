# Analyse

## Was Analyse bedeutet

Die Analyse sendet dein Transkript an ein Sprachmodell, um ein übergeordnetes Ergebnis zu erzeugen — eine Zusammenfassung, ein strukturiertes Protokoll, Kapitelmarker oder was auch immer du anforderst. Das Transkript wird dabei nicht verändert. Die ursprünglichen Äußerungen bleiben unabhängig vom Analyseergebnis unverändert.

## Integrierte Vorlagen

Drei Vorlagen stehen direkt zur Verfügung:

- **Allgemeine Zusammenfassung** — ein kompakter Überblick über den Inhalt der Aufnahme
- **Besprechungsprotokoll** — strukturierte Ausgabe mit Teilnehmenden, Entscheidungen und Aufgaben
- **Kapitelmarker** — mit Zeitstempeln versehene Abschnitte mit Titeln, nützlich für lange Aufnahmen

Wähle die Vorlage, die am besten zum Inhalt passt.

## Eigene Prompts

Statt einer Vorlage kannst du einen eigenen Prompt eingeben. Das Modell erhält den vollständigen Transkripttext zusammen mit deinem Prompt und gibt zurück, was du anforderst. Formuliere Prompts direkt und konkret. Vermeide Fragen nach Informationen, die im Transkript nicht enthalten sind — das Modell neigt dazu, Lücken mit Vermutungen zu füllen.

## Kapitel-Hinweise und Agenda

Bei langen Aufnahmen mit bekannter Agenda füge diese in das Agenda-Feld ein (ein Thema pro Zeile). Das Modell nutzt sie als Kontext für genauere Kapitelmarker und um Diskussionen den richtigen Tagesordnungspunkten zuzuordnen.

## Mehrere Analysen

Du kannst die Analyse beliebig oft mit verschiedenen Vorlagen oder Prompts ausführen. Jedes Ergebnis wird separat gespeichert und im Analyseverlauf angezeigt. Von dort aus kannst du Ergebnisse vergleichen, ältere löschen oder eine beliebige Konfiguration erneut ausführen.

## Quelle: Original oder Verfeinert

Sobald eine Verfeinerung existiert, zeigt das Analyse-Formular einen Umschalter **Quelle** (Original / Verfeinert) — voreingestellt auf **Verfeinert**, sodass das LLM standardmäßig den bereinigten Text erhält. Wechsle auf **Original**, um stattdessen das rohe ASR-Transkript zu analysieren. Jede gespeicherte Analyse zeigt an, welche Quelle verwendet wurde („aus Verfeinerung" / „aus Original"); wenn sich die Quelle seither geändert hat oder die Verfeinerung gelöscht wurde, wird der Hinweis bernsteinfarben, und du kannst die Analyse zur Neugenerierung erneut ausführen.
