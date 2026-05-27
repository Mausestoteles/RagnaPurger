# RagnaPurger

## Zusammenfassung

Der Bot stellt einen einzigen Slash-Command (`/Ragnapurge`) bereit, der zwei
Aktionen nacheinander ausführt: Erst werden alle Channels eines Discord-Servers
gelöscht, anschließend werden mehrere neue Channels mit einer vordefinierten
Nachricht erstellt. Beide Aktionen erfordern Administrator-Rechte und sind nach
Ausführung nicht rückgängig zu machen.

---

## Funktionsweise

### Phase 1 — Channel-Löschung
Der Bot iteriert über alle Channels der Guild und ruft auf jedem
`channel.delete()` auf. Es gibt keine Filterung (z.B. Whitelist bestimmter
Channels), keine Bestätigungsabfrage und keinen Test-Modus ("Dry-Run").
Gelöschte Channels und deren komplette Nachrichtenhistorie sind **dauerhaft
verloren**.

### Phase 2 — Channel-Erstellung
Anschließend werden standardmäßig **50 neue Text-Channels** mit demselben Namen
("Join Rag") erstellt. In jeden dieser Channels wird automatisch eine Nachricht
gepostet, die im Default-Zustand einen Einladungslink zum Rag Server enthält

---

## Berechtigungs-Konzept

Der Bot prüft drei Bedingungen, bevor er ausführt:

1. Wird der Command in einem Server (nicht im DM) ausgeführt?
2. Hat der ausführende User Administrator-Rechte?
3. Hat der Bot selbst die Berechtigung "Channels verwalten"?

**Wichtig:** Diese Prüfungen verhindern technische Fehlschläge, sind aber keine
Schutzmaßnahmen gegen Missbrauch. Es gibt **keine zusätzliche Bestätigung**,
**keine Wartezeit** ("Cooldown") und **keine Einschränkung auf bestimmte Server**.
Wer Admin ist, kann sofort und ohne weitere Hürde die komplette Server-Struktur
zerstören.

---

## Konfiguration

Folgende Werte lassen sich über eine `.env`-Datei einstellen, ohne den Code zu
verändern:

| Variable | Bedeutung | Default |
|---|---|---|
| `DISCORD_TOKEN` | Bot-Token | — |
| `GUILD_ID` | Optionale Beschränkung auf einen Server | global |
| `NEW_CHANNEL_COUNT` | Anzahl der nach dem Löschen erstellten Channels | 50 |
| `NEW_CHANNEL_NAME` | Name der neuen Channels | "Join Rag" |
| `NEW_CHANNEL_MESSAGE` | Nachricht in den neuen Channels | Discord-Invite |

Da alle relevanten Parameter extern konfigurierbar sind, ist der Bot **ohne
Code-Änderung gegen beliebige Server einsetzbar**, sofern er dort mit
ausreichenden Rechten eingeladen wurde.

---

## Logging und Nachvollziehbarkeit

- Jede Lösch- und Erstell-Operation übergibt einen `reason`-Parameter, der im
  **Discord Audit-Log sichtbar** ist.
- Der Name des ausführenden Users wird im Audit-Log-Eintrag genannt — die Aktion
  ist also forensisch dem Auslöser zuordenbar, nicht nur dem Bot.
- Lokal werden Aktionen über das Python-`logging`-Modul protokolliert.

---

## Fehlerbehandlung

Der Code fängt typische Discord-API-Fehler ab:
- `discord.Forbidden` (fehlende Rechte auf einzelnen Channels)
- `discord.HTTPException` (sonstige API-Fehler)

Fehlgeschlagene Operationen werden gesammelt und in einer Abschlussnachricht
gemeldet. Das `defer`/`followup`-Pattern für länger laufende Operationen ist
korrekt implementiert. Rate-Limits werden nicht aktiv behandelt.

---

## Auswirkungen bei Ausführung

- **Irreversibel:** Gelöschte Channels und deren Nachrichten können nicht über
  Discord wiederhergestellt werden.
- **Schnell:** Die Ausführung erfolgt sequentiell, aber innerhalb von Sekunden
  bis wenigen Minuten — schneller, als ein Server-Owner reagieren kann.
- **Sichtbar:** Mitglieder, die nach der Ausführung den Server betreten, sehen
  ausschließlich die neu erstellten Channels mit der konfigurierten Nachricht.

---
