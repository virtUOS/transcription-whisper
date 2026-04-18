# Verfeinerung

## Was Verfeinerung bewirkt

Die Verfeinerung führt einen Bereinigungsdurchlauf mit einem Sprachmodell über dein Transkript aus. Sie entfernt Füllwörter (äh, ähm, also), behebt Sprecherzuordnungsfehler, bei denen mitten im Satz der falsche Sprecher getaggt wurde, und glättet fragmentierte oder zu lange Sätze zu lesbarem Text. Das Original-Transkript bleibt vollständig erhalten — die Verfeinerung erzeugt eine eigene Ansicht, keine direkte Bearbeitung. Sie bleibt in der Ausgangssprache; sie ist keine Übersetzung.

## Wann sie hilft

Die Verfeinerung ist am nützlichsten bei rauschreichen Quellen: informellen Gesprächen, Interviews, Gruppendiskussionen mit Überlappungen oder Aufnahmen mit vielen Füllwörtern und Sprechunflüssigkeiten. Sie hilft auch dann, wenn die Diarisierung Zuordnungsfehler bei aufeinanderfolgenden Äußerungen gemacht hat. Das verfeinerte Transkript ist oft deutlich lesbarer als die rohe ASR-Ausgabe.

## Wann du sie überspringen solltest

Bei sauberen Einzelsprecher-Aufnahmen — Vorlesungen, Kommentaren, vorbereiteten Reden — ist die rohe ASR-Ausgabe in der Regel bereits von hoher Qualität. Die Verfeinerung verursacht dann LLM-Kosten und Verarbeitungszeit ohne nennenswerten Gewinn. Überspringe sie, wenn das Original bereits gut lesbar ist.

## Reihenfolge mit anderen Schritten

In einer Bundle-Pipeline läuft die Verfeinerung immer vor Analyse und Übersetzung. Sobald eine Verfeinerung vorhanden ist, verwenden Analyse und Übersetzung standardmäßig diese als Eingabe — ein Bundle mit Verfeinerungsschritt reicht den bereinigten Text also automatisch an die nachfolgenden Stufen weiter. Du kannst dies pro Durchlauf über den **Quelle**-Umschalter in den Dialogen „Übersetzen" und „Analysieren" überschreiben oder den Verfeinerungsschritt im Bundle weglassen, wenn nachgelagerte Stufen auf dem Original arbeiten sollen. Die verfeinerte Fassung bleibt zudem als eigenständige Ansicht nutzbar — lesbar, bearbeitbar und herunterladbar neben dem Original. Mehr dazu unter **Analyse**, **Übersetzung** und **Bundles**.
