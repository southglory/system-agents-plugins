# discord-huddle

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Ein Plugin für [system-agents-template](https://github.com/southglory/system-agents-template), das einen Discord-Kanal zum Team-Chat, zur Meeting-Notizen-Pipeline und zum Ankündigungskanal deines Projekts macht.

- **Pull**: archiviert Kanal-Nachrichten als lokales JSONL (`/discord-huddle-sync`)
- **Push**: lässt Agenten oder Nutzer in den Kanal posten (`/discord-huddle-post`)
- **Listen**: Echtzeit-Benachrichtigungen über den Discord-Gateway-WebSocket (`/discord-huddle-listen`)
- **Summarize**: ein Agent liest das Rohlog und erstellt ein getracktes Markdown-Meetingprotokoll — keine zusätzlichen LLM-API-Kosten über deine Claude-Code-Sitzung hinaus (`/discord-huddle-summarize`)

## 🚀 Installation in einer Zeile (empfohlen)

Nicht dieses Repo direkt klonen. Verwende den Installer des Templates:

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

Wähle `discord-huddle`, wenn gefragt wird. Der Installer kopiert Dateien in dein Projekt, registriert Slash-Skills global und legt `.claude/secrets/discord-huddle.env.example` an. Nach der Installation füllst du die Secrets-Datei (Bot Token + Channel ID) aus — fertig.

Detaillierte Einrichtung: [`docs/SETUP.md`](docs/SETUP.md). Manueller Smoke-Test: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Hauptmerkmale

### REST-Sync + Echtzeit-Listener

- `sync` holt per REST-Polling alles nach `last_read`
- `listen` (Gateway) empfängt Events per WebSocket und schreibt winzige Signaldateien, die das Monitor-Tool von Claude Code aufnimmt
- Zusammen verwenden: Listener liefert Geschwindigkeit, Sync sorgt für Vollständigkeit (Anhänge, Reaktionen beim ersten Empfang)

### Bidirektionaler Kanal

- Team → Agent: Chat platziert Anforderungen, Feedback, Fragen in Discord
- Agent → Team: Agenten posten Analysen, Diagramme, Webseiten-Screenshots, Build-Release-Links direkt zurück in den Kanal

### Zusammenfassungen als Team-Asset

- Zusammenfassungs-Markdowns liegen in `docs/discord-huddle-summaries/` und sind **git-getrackt**
- Ein neues Teammitglied liest nach `git clone` sofort vergangene Meetingprotokolle
- Der Zusammenfassungs-Pointer (`index.json`) wird ebenfalls getrackt, sodass Merge-Konflikte deterministisch auflösbar sind (forward-only: neuere msg_id gewinnt)

### Deterministisches Summarize-Gate

Bevor ein Agent Tokens fürs Zusammenfassen ausgibt, ruft er auf:

```bash
python bot/discord_collab.py summarize-check
```

Ein reiner Code-Scan liefert `{ready, reason, stats}`. Bei `ready:false` (zu wenige Nachrichten, kurzer Monolog usw.) bricht der Agent sofort ab, ohne Raw in den Kontext zu laden. Die vollständigen Regeln stehen in [`skills/discord-huddle-summarize/SKILL.md`](skills/discord-huddle-summarize/SKILL.md).

### Nicht-invasive Installation

- Laufzeitdaten (`raw/`, `inbox/`, `local-state.json`, `vc-snapshots/`) leben in `.system-agents/discord-huddle/`, und das Plugin legt dort automatisch `.gitignore: *` ab — **die `.gitignore` im Projekt-Root bleibt unberührt**
- Pfad-Overrides über dieselbe `.env` (kein separates `export`):
  `SYSTEM_AGENTS_PROJECT_ROOT`, `DISCORD_HUDDLE_DATA_DIR`, `DISCORD_HUDDLE_SUMMARY_DIR`

### Freundliche Fehlermeldungen

Keine Python-Tracebacks nach außen. 401/403/404/429 bringen jeweils eine einzeilige Hinweiszeile zur exakten Abhilfe (Reset Token, Bot neu einladen, Channel-ID prüfen, Rate-Limit).

## Slash-Skills

| Befehl | Wirkung |
|---|---|
| `/discord-huddle-sync` | Neue Kanal-Nachrichten ins Raw-JSONL ziehen |
| `/discord-huddle-listen` | Gateway-WebSocket-Echtzeit-Listener |
| `/discord-huddle-post` | Eine Nachricht posten (optional mit Anhängen oder Webseiten-Snapshot) |
| `/discord-huddle-summarize` | Der Agent liest Raw und schreibt ein Meetingprotokoll |

Der genaue Vertrag jeder Skill steht in `skills/<name>/SKILL.md`.

## Webseiten-Snapshot (optionales Feature)

`/discord-huddle-post --vc-snapshot` rendert eine beliebige URL als PNG via Headless-Chromium und hängt sie an:

- Explizite URL: `--vc-url https://my-dashboard.local`
- Auto-Erkennung (opt-in): `--vc-sessions-dir DIR` oder `VC_SESSIONS_DIR` auf ein Verzeichnis mit `<session>/state/server-info`-Layout (JSON mit `url`-Feld). Dem Plugin ist egal, welches Tool diese Dateien erzeugt.
- Benötigt: `pip install -r requirements-optional.txt` + `playwright install chromium` (~200 MB, einmalig).

## Datenorte (Standard)

| Pfad | Inhalt | Git-getrackt? |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Rohdaten-Dumps | Nein (auto-gitignore) |
| `.system-agents/discord-huddle/inbox/` | Gateway-Echtzeit-Signale | Nein |
| `.system-agents/discord-huddle/local-state.json` | Nutzerlokaler Sync-Pointer | Nein |
| `.system-agents/discord-huddle/vc-snapshots/` | Playwright-PNGs | Nein |
| `docs/discord-huddle-summaries/*.md` | Team-Meetingprotokolle | **Ja** |
| `docs/discord-huddle-summaries/index.json` | Forward-only Summary-Pointer | **Ja** |
| `docs/discord-huddle-summaries/attachments/` | In Summaries referenzierte Bilder | **Ja** |

## Kombination mit anderen Plugins

| Ziel | Wirkung | Setup | Recipe |
|---|---|---|---|
| Eingebautes `/schedule` (Claude Code) | Wiederkehrende Ankündigungen im Kanal (Daily Standups, Wochenberichte) | `/schedule` nutzt `discord-huddle-post` per cron | Nur-Doku-Kombi (cron-Beispiel siehe [README.ko.md](README.ko.md#조합-가능한-플러그인)) |
| (geplant) `unity-gamedev` | Unity-Build → GitHub-Release → automatische Kanal-Ankündigung | Beide Plugins installieren; `publish-build`-JSON in `discord-huddle-post` pipen | `recipes/unity-build-to-discord/` (wird mit unity-gamedev hinzugefügt) |

## Voraussetzungen

- Python ≥ 3.10
- Discord-Bot-Token (im [Developer Portal](https://discord.com/developers/applications) erstellen)
- **Message Content Intent** aktivieren (erforderlich für Gateway-Listener)

## Lizenz

MIT — siehe [`LICENSE`](../LICENSE) im Repo-Root.

## Verwandte Dokumente

- [SETUP.md](docs/SETUP.md) — Installation und Konfiguration
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — manuelle Smoke-Test-Checkliste
- Repo-Root [README](../README.md) — Plugin-Ökosystem-Übersicht
