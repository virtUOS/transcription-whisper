# Analyse

## Was Analyse bedeutet

Die Analyse sendet dein Transkript an ein Sprachmodell, um ein übergeordnetes Ergebnis zu erzeugen — eine Zusammenfassung, ein strukturiertes Protokoll, Kapitelmarker oder was auch immer du anforderst. Das Transkript wird dabei nicht verändert. Die ursprünglichen Äußerungen bleiben unabhängig vom Analyseergebnis unverändert.

## Integrierte Vorlagen

Drei Vorlagen stehen direkt zur Verfügung, plus eine Option **Eigener Prompt**:

- **Zusammenfassung mit Kapiteln** — Gesamtzusammenfassung plus zeitcodierte Kapitelgliederung, nützlich für lange Aufnahmen
- **Besprechungsprotokoll** — strukturierte Notizen mit Kernpunkten, Entscheidungen und Aufgaben
- **Agenda-basierte Notizen** — Notizen, die sich an einer vorgegebenen Agenda orientieren

Wähle die Vorlage, die am besten zum Inhalt passt.

## Eigene Prompts

Wähle **Eigener Prompt**, um einen eigenen Prompt einzugeben. Das Modell erhält den vollständigen Transkripttext zusammen mit deinem Prompt und gibt zurück, was du anforderst. Formuliere Prompts direkt und konkret. Vermeide Fragen nach Informationen, die im Transkript nicht enthalten sind — das Modell neigt dazu, Lücken mit Vermutungen zu füllen.

## Kapitel-Hinweise und Agenda

Die Vorlage **Zusammenfassung mit Kapiteln** bietet ein optionales Feld **Kapitel definieren**, in das du Kapiteltitel und -beschreibungen (eins pro Zeile) eintragen kannst, um die Segmentierung zu steuern. Die Vorlage **Agenda-basierte Notizen** zeigt ein **Agenda**-Feld — füge dort deine Agenda ein, und das Modell strukturiert die Ausgabe entlang dieser Punkte.

## Mehrere Analysen

Du kannst die Analyse beliebig oft mit verschiedenen Vorlagen oder Prompts ausführen. Jedes Ergebnis wird separat gespeichert und im Analyseverlauf angezeigt. Von dort aus kannst du Ergebnisse vergleichen, ältere löschen oder eine beliebige Konfiguration erneut ausführen.

## Quelle: Original oder Verfeinert

Sobald eine Verfeinerung existiert, zeigt das Analyse-Formular einen Umschalter **Quelle** (Original / Verfeinert) — voreingestellt auf **Verfeinert**, sodass das LLM standardmäßig den bereinigten Text erhält. Wechsle auf **Original**, um stattdessen das rohe ASR-Transkript zu analysieren. Jede gespeicherte Analyse zeigt an, welche Quelle verwendet wurde („aus Verfeinerung" / „aus Original"); wenn sich die Quelle seither geändert hat oder die Verfeinerung gelöscht wurde, wird der Hinweis bernsteinfarben, und du kannst die Analyse zur Neugenerierung erneut ausführen.
