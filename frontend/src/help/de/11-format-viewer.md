# Formatansicht

## Die vier Formate

Die Detailansicht bietet vier Exportformate, die sich für unterschiedliche Anwendungsfälle eignen:

- **SRT** — Das am weitesten verbreitete Untertitelformat. Nummerierte Einträge mit `HH:MM:SS,mmm`-Zeitstempeln. Funktioniert mit nahezu jedem Videoplayer und Schnittprogramm.
- **VTT** — Der moderne WebVTT-Standard für HTML5-Video. Ähnlich aufgebaut wie SRT, aber mit übersichtlicherer Syntax und nativer Browser-Unterstützung.
- **JSON** — Eine strukturierte Liste von Äußerungen mit Start- und Endzeit, Text und Sprecherbeschriftung. Die richtige Wahl, wenn du das Transkript programmatisch weiterverarbeiten möchtest. Wenn eine Verfeinerung existiert, ist der JSON-Export ein Objekt, das beide Arrays enthält: `{ "utterances": [...], "refined_utterances": [...] }`.
- **TXT** — Reiner Text mit Sprecherbeschriftungen, aber ohne Zeitstempel. Leicht lesbar, teilbar oder in ein Dokument einfügbar.

## Herunterladen

Jedes Format hat seinen eigenen Reiter. Klicke auf einen Reiter, um eine Vorschau anzuzeigen, und klicke dann auf **Herunterladen**, um die Datei zu speichern. Namen, die du im Speaker Mapping vergeben hast, werden in allen vier Formaten übernommen.

## Welches Format passt?

| Ziel | Bestes Format |
|---|---|
| Untertitel zu einem Video hinzufügen | SRT oder VTT |
| Programmatisch weiterverarbeiten | JSON |
| Transkript lesen oder teilen | TXT |
| In einen Web-Player einbetten | VTT |
