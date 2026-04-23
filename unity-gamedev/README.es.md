# unity-gamedev

![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![unity-gamedev release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=unity-gamedev-*&label=unity-gamedev)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Un plugin [system-agents-template](https://github.com/southglory/system-agents-template) que convierte el trío Unity Editor + `unity-cli` + `gh` en una **pipeline de release de un solo comando**.

- **Build**: `unity-cli exec BuildPipeline.BuildPlayer(...)` — escenas, nombre de salida y target los decide el invocador. **Nada específico del proyecto está hardcodeado**.
- **Zip**: `Builds/{NAME}{ext}` → `dist/{NAME}_{tag}.zip`
- **Release**: `gh release create {tag}` (con fallback a `gh release upload --clobber` en reintento)
- **Listo para anunciar**: el JSON de una línea en stdout se canaliza directamente a `discord-huddle-post` u otro anunciador

## 🚀 Instalación en una línea (recomendada)

No clones este repositorio directamente; usa el instalador del template:

Rolling (siempre el último `main`):

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

Fijado a un Release estable (recomendado para reproducibilidad):

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```

Cuando pregunte, elige `unity-gamedev`. Después de instalar no hay secretos que rellenar — el plugin reutiliza tu login de `gh` existente.

Setup detallado: [`docs/SETUP.md`](docs/SETUP.md). Smoke test: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Todo es un flag CLI

La idea de este plugin es **ningún nombre de proyecto hardcodeado**. Rutas de escena, nombre de salida, target de Unity y raíz del proyecto vienen todos del invocador. Nada atado a un juego concreto:

```bash
python bot/publish_build.py \
  --tag v0.1.0 \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --target StandaloneWindows64
```

`--scene` se puede repetir (builds multi-escena). `--skip-build` reutiliza lo que ya esté en `Builds/{NAME}.*`. Tabla completa en `skills/publish-build/SKILL.md`.

## Salida: un JSON por stdout

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

stderr lleva el progreso legible. Esta separación hace trivial scriptear el paso de "anunciar el release".

## Combinando con otros plugins

| Objetivo | Efecto | Configuración | Recipe |
|---|---|---|---|
| [`discord-huddle`](../discord-huddle/) | Build Unity → GitHub Release → anuncio automático en canal | Instalar ambos; canalizar el JSON de `publish-build` a `discord-huddle-post` | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

## Skill con slash

| Comando | Qué hace |
|---|---|
| `/publish-build` | Build + zip + Release en un paso |

Contrato exacto en [`skills/publish-build/SKILL.md`](skills/publish-build/SKILL.md).

## Requisitos

- **Python ≥ 3.10** (solo stdlib — sin `pip install`)
- Unity Editor corriendo, con `unity-cli` conectado (`unity-cli status = ready`)
- **[unity-cli](https://github.com/youngwoocho02/unity-cli)** (MIT) en `PATH`, v0.3+. Instalación Windows: `irm https://raw.githubusercontent.com/youngwoocho02/unity-cli/master/install.ps1 | iex`
- `gh` CLI, autenticado con scope `repo`

## Lo que este plugin NO hace

- No instala Unity, `unity-cli` ni `gh`.
- No empuja tags git — solo crea GitHub Releases. Si quieres un tag git a juego, haz `git tag vX.Y.Z && git push --tags` antes del Release.
- No firma ni notariza binarios. Eso es tooling específico de plataforma.
- No sube a Steam, itch.io o tiendas de apps. Esto pertenece a un plugin aparte.

## Licencia

MIT — ver el [`LICENSE`](../LICENSE) de la raíz.

## Documentos relacionados

- [SETUP.md](docs/SETUP.md) — instalación + primer release paso a paso
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — lista manual de 7 pasos
- [README](../README.md) de la raíz — panorama del ecosistema de plugins
