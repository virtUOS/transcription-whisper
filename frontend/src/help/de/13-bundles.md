# Bundles

## Was ein Bundle ist

Ein Bundle ist eine benannte Zusammenstellung von Pipeline-Stufen: Transkription, Verfeinerung, Analyse und Übersetzung. Jede Stufe ist optional außer der Transkription, und jede Stufe enthält eine Voreinstellung (oder eine Zielsprache für die Übersetzung). Wenn du in der Upload- oder Aufnahme-Ansicht ein Bundle auswählst, laufen alle konfigurierten Stufen nach Abschluss der Transkription automatisch nacheinander ab — kein manuelles Auslösen nötig.

## Die Pipeline

![Bundle pipeline](./assets/bundle-pipeline.svg)

Die Stufen laufen immer in dieser Reihenfolge: **Transkription → Verfeinerung → Analyse → Übersetzung**. Ist ein Verfeinerungsschritt konfiguriert, lesen Analyse und Übersetzung standardmäßig den verfeinerten Text statt des Originals — der bereinigte Text fließt also durch die Pipeline weiter. Lass den Verfeinerungsschritt weg (oder stelle den **Quelle**-Umschalter beim manuellen Ausführen um), damit diese Stufen auf dem Original-Transkript arbeiten.

## Standard-Bundle und Automatik

Du kannst ein Bundle als Standard markieren. Es wird dann für jeden neuen Upload und jede Aufnahme vorausgewählt. Sobald die Transkription abgeschlossen ist, starten die verbleibenden Stufen automatisch, und Fortschrittsanzeigen zeigen den Status jeder Stufe. Wenn eine einzelne Stufe fehlschlägt, kannst du den Fehler schließen und weitermachen, ohne die gesamte Pipeline neu zu starten.

## Bundles erstellen und verwenden

Erstelle Bundles auf der **Voreinstellungen**-Seite, indem du pro Stufe eine Voreinstellung auswählst und dem Bundle einen Namen gibst. Markiere es als Standard, wenn es automatisch angewendet werden soll. In der Upload- oder Aufnahme-Ansicht kannst du das aktive Bundle jederzeit über das Bundle-Dropdown wechseln.

## Bundle oder manuelle Schritte?

Nutze ein Bundle, wenn du dieselbe Pipeline regelmäßig anwendest — zum Beispiel „jede Besprechungsaufnahme: verfeinern, dann auf Englisch zusammenfassen, dann ins Deutsche übersetzen". Wähle manuelle Schritte für einmalige Aufnahmen, die eine andere Behandlung benötigen, oder wenn du Zwischenergebnisse prüfen möchtest, bevor du weitermachst.
