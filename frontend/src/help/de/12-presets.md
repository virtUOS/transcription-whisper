# Voreinstellungen

## Was Voreinstellungen sind

Eine Voreinstellung speichert Einstellungen unter einem Namen, damit Sie sie nicht für jede Aufnahme neu eingeben müssen. Es gibt Voreinstellungen für die Transkription, für die Analyse und für die Verfeinerung. Voreinstellungen gehören zu Ihrem Konto, und nur Sie sehen sie.

Sie verwenden sie an drei Stellen:

- **Transkription:** in der Gruppe **Voreinstellungen** der Ansichten **Hochladen** und **Aufnehmen**, im Feld **Transkription**. Der Abschnitt „Transkriptionseinstellungen“ erklärt es.
- **Analyse:** im Feld **Analyse** des Analyse-Formulars.
- **Verfeinerung:** oben im Dialog zum Verfeinern.

Neben jedem dieser Felder steht **Als Voreinstellung speichern**. Geben Sie dort einen Namen ein und bestätigen Sie mit dem Häkchen oder der Eingabetaste. transkribierBAR speichert die aktuellen Einstellungen unter diesem Namen. Das Kreuz oder Esc bricht ab.

## Die Seite „Voreinstellungen“

Klicken Sie in der Kopfzeile auf **Voreinstellungen**. Die Seite **Meine Voreinstellungen** hat vier Reiter: **Transkription**, **Analyse**, **Verfeinerung** und **Pakete**. Der Abschnitt „Pakete“ erklärt den letzten.

Jeder Reiter listet Ihre gespeicherten Einträge mit **Bearbeiten** und **Löschen**. **+ Neue Voreinstellung** öffnet ein Formular mit einem **Namen** und den Feldern der jeweiligen Art. **Speichern** ist erst möglich, wenn Sie einen Namen eingegeben haben. **Abbrechen** schließt das Formular.

**Löschen** fragt nach: **Voreinstellung löschen? Pakete, die sie verwenden, verlieren die Referenz.** Es wird nur die Voreinstellung entfernt. Pakete, die sie verwendet haben, bleiben bestehen, aber ohne diesen Teil. Bereits vorhandene Transkriptionen sind nicht betroffen.

## Transkriptions-Voreinstellungen

Eine Transkriptions-Voreinstellung speichert Sprache, Erkennung der Sprechenden, Anfangs-Prompt, Schlüsselwörter und Modell. Das Formular auf der Seite hat die Felder **Name**, **Sprache für die Transkription**, **Modell**, **Schlüsselwörter** und **Anfangs-Prompt**. Das Modell ist fest auf {{default_model}} eingestellt und lässt sich nicht ändern.

Wenn Sie eine solche Voreinstellung bei **Hochladen** oder **Aufnehmen** wählen, übernimmt sie Sprache, Sprechende, Anfangs-Prompt und Schlüsselwörter. Das Modell bleibt {{default_model}}.

> **Sprechende.** Die Seite „Voreinstellungen“ hat kein Feld für die Erkennung der Sprechenden. Wenn Sie dort eine Transkriptions-Voreinstellung bearbeiten, ist die Erkennung der Sprechenden in dieser Voreinstellung danach ausgeschaltet. Möchten Sie Einstellungen zu den Sprechenden ändern, stellen Sie sie bei **Hochladen** oder **Aufnehmen** ein und speichern Sie mit **Als Voreinstellung speichern** eine neue Voreinstellung.

## Analyse-Voreinstellungen

Eine Analyse-Voreinstellung speichert die Vorlage und die Ausgabesprache. Bei **Eigene Anweisung** speichert sie auch Ihre eigene Anweisung. Das Formular auf der Seite hat die Felder **Name**, **Vorlage auswählen**, **Ausgabesprache** und, bei **Eigene Anweisung**, **Prompt anpassen**.

Speichern Sie eine Voreinstellung im Analyse-Formular mit **Als Voreinstellung speichern**, speichert sie auch die Kapitel und die Agenda, die Sie dort eingegeben haben. Wählen Sie die Voreinstellung später, werden sie wieder eingetragen. Der Abschnitt „Analyse“ erklärt das Formular.

> **Kapitel und Agenda.** Die Seite „Voreinstellungen“ hat keine Felder für Kapitel und Agenda. Wenn Sie dort eine Analyse-Voreinstellung bearbeiten, werden sie aus der Voreinstellung entfernt.

## Verfeinerungs-Voreinstellungen

Eine Verfeinerungs-Voreinstellung speichert nur einen Kontexttext, zum Beispiel einen Hinweis zum Thema und zu Fachbegriffen. Das Formular auf der Seite hat die Felder **Name** und **Kontext (optional)**. Der Abschnitt „Verfeinerung“ erklärt, was der Kontext bewirkt.
