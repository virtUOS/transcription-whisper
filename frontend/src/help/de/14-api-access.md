# API-Zugriff

## Worum es geht

Wenn in Ihrer Installation API-Tokens aktiviert sind, können Sie einen persönlichen Bearer-Token erzeugen und damit die REST-Schnittstelle der Anwendung direkt aus Skripten, CI-Jobs oder beliebigen HTTP-Clients aufrufen. Ein Token ist an Ihr Konto gebunden — er kann Ihre eigenen Dateien, Transkriptionen und Voreinstellungen lesen und schreiben, aber niemals Daten anderer Nutzer sehen.

Ist das Feature in Ihrer Installation deaktiviert, erscheint der Eintrag **Einstellungen** in der Kopfzeile nicht und der Bereich ist nicht verfügbar.

## Token erstellen

Öffnen Sie **Einstellungen** in der Kopfzeile und klicken Sie auf **Token erstellen**. Vergeben Sie einen kurzen Namen, der Ihnen hilft, den Verwendungszweck wiederzuerkennen (z. B. `mein-laptop` oder `ci-pipeline`), wählen Sie eine Gültigkeit (30, 90, 365 Tage oder Nie) und bestätigen Sie mit **Erstellen**.

Der Token wird **einmalig** als `tw_…`-Zeichenkette angezeigt. Kopieren Sie ihn sofort — sobald Sie den Dialog schließen, ist der vollständige Wert nicht mehr abrufbar. In der Liste ist nur das kurze Präfix zur Wiedererkennung sichtbar.

## Token verwenden

Senden Sie den Token als HTTP-Bearer-Header:

```
Authorization: Bearer tw_...
```

Beispiel mit curl:

```
curl -H "Authorization: Bearer tw_abc..." https://ihr-host/api/tokens
```

Für den Status-WebSocket der Transkription übergeben Sie den Token als Query-Parameter (Browser erlauben keine eigenen Header auf WebSocket-Verbindungen):

```
wss://ihr-host/api/ws/status/{transcription_id}?token=tw_abc...
```

## Token widerrufen

Klicken Sie neben einem aktiven Token auf **Widerrufen**. Der Token wird sofort ungültig. Widerrufene Tokens bleiben (abgeblendet) in der Liste, damit Sie nachvollziehen können, welche Sie bereits rotiert haben.

## Hinweise

- **Token rotieren, wenn sich Geräte ändern.** Geht ein Laptop verloren oder wird ein CI-Secret erneuert, widerrufen Sie den passenden Token und erstellen einen neuen.
- **Ein Token pro Einsatzzweck.** Teilen Sie einen Token möglichst nicht zwischen mehreren Werkzeugen oder Geräten — Namen pro Einsatzort erleichtern den gezielten Widerruf.
- **Gleiche Rechte wie in der Oberfläche.** Ein Token erbt Ihre Berechtigungen: Ist in der Installation kein LLM konfiguriert, liefern Analyse, Übersetzung und Überarbeitung auch für Token-Anfragen den Status 503.
