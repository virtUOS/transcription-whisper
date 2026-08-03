# Transkriptionseinstellungen

## Sprechererkennung

Die Sprechererkennung (Diarization) erkennt, wer wann gesprochen hat, und versieht jede Äußerung mit einer Bezeichnung wie SPEAKER_00, SPEAKER_01 usw. Schalte sie für Aufnahmen mit mehreren Sprechern ein und für Einzelsprecher-Inhalte aus, um Verarbeitungszeit zu sparen. Optional kannst du eine minimale und maximale Sprecheranzahl angeben, um die Erkennung zu steuern. Die Sprechererkennung erhöht die Verarbeitungszeit spürbar. Nach der Transkription kannst du Sprecher über das **Speaker Mapping** umbenennen.

## Modell und Qualität

Welche Whisper-Modelle zur Verfügung stehen, hängt von der Konfiguration deiner Installation ab.

**Ist nur ein Modell konfiguriert**, zeigt der Einstellungsbereich ein schreibgeschütztes Feld **Modell** mit dessen Namen an (zum Beispiel `large-v3-turbo`). Es gibt nichts auszuwählen — jede Transkription verwendet dieses Modell.

**Sind mehrere konfiguriert**, wird daraus ein Auswahlfeld **Qualität**. Jeder Eintrag nennt eine Stufe und das dahinterliegende Modell:

| Stufe | Geschwindigkeit | Hinweis |
|---|---|---|
| Entwurf (tiny) | Schnellste | Gut für schnelle Vorschauen langer Dateien |
| Standard (base) | Schnell | — |
| Gut (small) | Mittel | — |
| Besser (medium) | Langsam | — |
| Ausgewogen (large-v3-turbo) | Schnell/genau | Empfohlene Standardwahl |
| Beste Qualität (large-v3) | Langsamste | Maximale Genauigkeit |

Es erscheinen nur die Stufen, die deine Installation anbietet. Die Abstände sind nicht gleichmäßig — der Sprung hinauf zu `large-v3-turbo` ist groß, während der Unterschied zwischen `large-v3-turbo` und `large-v3` klein ist.

## Erweiterte Optionen

**Initial Prompt** ermöglicht es, dem Modell einen kurzen Kontext mitzugeben — nützlich für Fachthemen, Eigennamen oder erwartetes Vokabular. **Hotwords** ist eine kommagetrennte Liste von Fachbegriffen, die das Modell bevorzugen soll. Setze beide Optionen sparsam ein; zu viele Vorgaben können Fehler erzeugen.

## Voreinstellungen

Speichere deine aktuellen Einstellungen als benannte Voreinstellung, um sie jederzeit wieder aufzurufen. Voreinstellungen erstellst und verwaltest du auf der Seite **Voreinstellungen**.
