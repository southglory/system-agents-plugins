# unity-gamedev

![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![unity-gamedev release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=unity-gamedev-*&label=unity-gamedev)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Ein [system-agents-template](https://github.com/southglory/system-agents-template)-Plugin, das das Trio Unity Editor + `unity-cli` + `gh` in eine **Ein-Kommando-Release-Pipeline** verwandelt.

- **Build**: `unity-cli exec BuildPipeline.BuildPlayer(...)` — Szenen, Ausgabename und Target übergibt der Aufrufer. **Nichts Projekt-Spezifisches ist hartkodiert.**
- **Zip**: `Builds/{NAME}{Endung}` → `dist/{NAME}_{tag}.zip`
- **Release**: `gh release create {tag}` (bei Wiederholung Fallback auf `gh release upload --clobber`)
- **Ankündigungs-fertig**: Die einzeilige JSON-Ausgabe auf stdout lässt sich direkt in `discord-huddle-post` oder andere Ankündiger piepen

## 🚀 Installation in einer Zeile (empfohlen)

Klone dieses Repo nicht direkt. Verwende den Installer des Templates:

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

Wenn der Installer fragt, wähle `unity-gamedev`. Nach der Installation müssen keine Geheimnisse eingetragen werden — das Plugin nutzt deinen bestehenden `gh`-Login.

Ausführliche Einrichtung: [`docs/SETUP.md`](docs/SETUP.md). Smoke-Test: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Alles ist ein CLI-Flag

Der Grundgedanke dieses Plugins: **keine hartkodierten Projektnamen**. Szene-Pfade, Ausgabename, Unity-BuildTarget und Projekt-Root kommen vom Aufrufer. Nichts ist an ein bestimmtes Spiel gebunden:

```bash
python bot/publish_build.py \
  --tag v0.1.0 \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --target StandaloneWindows64
```

`--scene` ist wiederholbar (Multi-Szene-Builds). `--skip-build` verwendet das bereits vorhandene `Builds/{NAME}.*`. Komplette Flag-Tabelle in `skills/publish-build/SKILL.md`.

## Ausgabe: eine JSON-Zeile auf stdout

```json
{
  "tag": "v0.1.0",
  "title": "MVP α",
  "url": "https://github.com/owner/repo/releases/tag/v0.1.0",
  "zip": "dist/MyGame_v0.1.0.zip",
  "output_name": "MyGame",
  "target": "StandaloneWindows64"
}
```

stderr trägt den menschenlesbaren Fortschritt. Diese Trennung macht das anschließende "Ankündigen"-Scripten trivial.

## Kombination mit anderen Plugins

| Ziel | Wirkung | Setup | Recipe |
|---|---|---|---|
| [`discord-huddle`](../discord-huddle/) | Unity-Build → GitHub-Release → automatische Kanal-Ankündigung | Beide Plugins installieren; `publish-build`-JSON in `discord-huddle-post` pipen | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

## Slash-Skill

| Befehl | Wirkung |
|---|---|
| `/publish-build` | Build + zip + Release in einem Rutsch |

Exakter Vertrag in [`skills/publish-build/SKILL.md`](skills/publish-build/SKILL.md).

## Voraussetzungen

- **Python ≥ 3.10** (nur stdlib — kein `pip install`)
- Unity Editor läuft, mit verbundenem `unity-cli` (`unity-cli status = ready`)
- `unity-cli v0.3+` im `PATH`
- `gh` CLI, mit `repo`-Scope authentifiziert

## Was dieses Plugin NICHT tut

- Installiert weder Unity selbst noch `unity-cli` oder `gh`.
- Pusht keine Git-Tags — es erzeugt nur GitHub-Releases. Für einen passenden Git-Tag vorher `git tag vX.Y.Z && git push --tags`.
- Signiert oder notarisiert keine Binaries. Das ist plattform-spezifisches Tooling.
- Lädt nicht zu Steam, itch.io oder App-Stores hoch. Gehört in ein separates Plugin.

## Lizenz

MIT — siehe [`LICENSE`](../LICENSE) im Repo-Root.

## Verwandte Dokumente

- [SETUP.md](docs/SETUP.md) — Installation + Erst-Release
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 7-Schritt manuelle Checkliste
- Repo-Root [README](../README.md) — Plugin-Ökosystem-Übersicht
