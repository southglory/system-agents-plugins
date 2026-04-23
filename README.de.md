# system-agents-plugins


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/southglory/system-agents-plugins?include_prereleases&sort=semver)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Offizielle Plugins für [system-agents-template](https://github.com/southglory/system-agents-template).

Jedes Plugin liegt in einem eigenen Unterverzeichnis und wird unabhängig veröffentlicht. Nutzer installieren nur die Plugins, die sie brauchen.

## 🚀 Installation in einer Zeile (über den Installer des Templates)

Du klonst dieses Repo nicht direkt — das `install.sh` des Templates liest den Plugin-Index hier und kopiert die ausgewählten Plugins in dein Projekt:

Rolling (immer aktuelles `main`):

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

Fixiert auf ein stabiles Release (empfohlen für Reproduzierbarkeit):

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```


Wenn der Installer fragt, welche Plugins installiert werden sollen, wähle `discord-huddle` (oder ein anderes aufgeführtes Plugin).

## Verfügbare Plugins

| Ordner | Zusammenfassung | Status |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | Team-Chat + nachverfolgte Meeting-Notizen über Discord | ✅ Veröffentlicht (`discord-huddle-v0.1.0`) |
| [`unity-gamedev/`](unity-gamedev/) | Unity-CLI-Build → GitHub-Release-Veröffentlichung | ✅ Veröffentlicht (`unity-gamedev-v0.1.0`) |

Für detaillierte Einrichtung siehe das jeweilige Plugin-README.

## Installationsmodell

Plugins werden per Dateikopie (`cp -r`) installiert, nicht über einen Paketmanager (pip/npm). Die Plugin-Dateien verschmelzen direkt mit deinem Projektbaum, daher übernimmt die verwaltete Installation das `install.sh` des Templates:

```bash
# 1. Dieses Repo klonen (der Installer erledigt es automatisch)
git clone https://github.com/southglory/system-agents-plugins.git

# 2. Gewünschtes Plugin ins Projekt kopieren (erledigt der Installer)
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. Skills in Claude Code registrieren (erledigt der Installer)
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. Python-Abhängigkeiten installieren
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

Der manuelle `cp -r`-Weg existiert als Rückfallebene für fortgeschrittene Nutzer; der Installer ist die empfohlene Variante.

## Versionierung

Jedes Plugin wird unabhängig veröffentlicht. Tag-Format: `<plugin-name>-vX.Y.Z`.

- `discord-huddle-v0.1.0` — erste öffentliche Veröffentlichung
- `unity-gamedev-v0.1.0` — geplant

Es gibt keine einzelne Repo-Version. Template-Tags (`v2.x.x`) und Plugin-Tags kollidieren nie.

## Plugins kombinieren

Plugins sind so gebaut, dass sie allein funktionieren, aber manche passen gut zusammen. Siehe [`CONTRIBUTING.md`](CONTRIBUTING.md) für die Kombinations-Matrix-Konvention, die jedes Plugin-README dokumentieren soll. Wiederverwendbare plugin-übergreifende Kombinationen leben in [`recipes/`](recipes/).

## Kompatibilität

- Claude Code (Slash-Skill-System)
- system-agents-template v2.x oder neuer
- Python ≥ 3.10
- Windows / macOS / Linux

Einzelne Plugins können weitere Anforderungen haben (zum Beispiel benötigt discord-huddle einen Discord-Bot-Token).

## Lizenz

[MIT](LICENSE) — gleich wie system-agents-template.

## Mitwirken

- Fehlermeldungen und Feedback: GitHub Issues
- Neue Plugins: folge den Struktur-Konventionen in [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
