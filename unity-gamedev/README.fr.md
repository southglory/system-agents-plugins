# unity-gamedev

![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![unity-gamedev release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=unity-gamedev-*&label=unity-gamedev)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Un plugin [system-agents-template](https://github.com/southglory/system-agents-template) qui transforme le trio Unity Editor + `unity-cli` + `gh` en un **pipeline de release en une seule commande**.

- **Build** : `unity-cli exec BuildPipeline.BuildPlayer(...)` — scènes, nom de sortie et cible passés par l'appelant. **Rien de spécifique au projet n'est codé en dur.**
- **Zip** : `Builds/{NAME}{ext}` → `dist/{NAME}_{tag}.zip`
- **Release** : `gh release create {tag}` (avec fallback `gh release upload --clobber` au retry)
- **Prêt pour l'annonce** : le JSON d'une ligne sur stdout se canalise tel quel vers `discord-huddle-post` ou un autre annonceur

## 🚀 Installation en une ligne (recommandée)

Ne clonez pas ce dépôt directement, utilisez l'installateur du template :

Rolling (toujours le `main` le plus récent) :

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

Épinglé sur une Release stable (recommandé pour la reproductibilité) :

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```

Quand on vous le demande, choisissez `unity-gamedev`. Aucun secret à renseigner après l'installation — le plugin utilise votre login `gh` existant.

Installation détaillée : [`docs/SETUP.md`](docs/SETUP.md). Smoke test : [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Tout passe par un flag CLI

Le principe du plugin : **aucun nom de projet codé en dur**. Chemins de scène, nom de sortie, cible Unity et racine de projet sont tous fournis par l'appelant. Rien n'est lié à un jeu particulier :

```bash
python bot/publish_build.py \
  --tag v0.1.0 \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --target StandaloneWindows64
```

`--scene` peut être répété (builds multi-scènes). `--skip-build` réutilise ce qui est déjà dans `Builds/{NAME}.*`. Tableau complet dans `skills/publish-build/SKILL.md`.

## Sortie : une ligne JSON sur stdout

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

stderr porte le progrès lisible. Cette séparation rend trivial le scripting de l'étape "annoncer la release".

## Combinaison avec d'autres plugins

| Cible | Effet | Configuration | Recipe |
|---|---|---|---|
| [`discord-huddle`](../discord-huddle/) | Build Unity → GitHub Release → annonce automatique du lien dans un canal | Installer les deux plugins ; piper le JSON de `publish-build` vers `discord-huddle-post` | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

## Skill slash

| Commande | Rôle |
|---|---|
| `/publish-build` | Build + zip + Release en une étape |

Contrat exact dans [`skills/publish-build/SKILL.md`](skills/publish-build/SKILL.md).

## Prérequis

- **Python ≥ 3.10** (stdlib uniquement — pas de `pip install`)
- Unity Editor lancé, avec `unity-cli` connecté (`unity-cli status = ready`)
- **[unity-cli](https://github.com/youngwoocho02/unity-cli)** (MIT) dans le `PATH`, v0.3+. Installation Windows : `irm https://raw.githubusercontent.com/youngwoocho02/unity-cli/master/install.ps1 | iex`
- `gh` CLI, authentifié avec le scope `repo`

## Ce que ce plugin NE fait PAS

- N'installe pas Unity, `unity-cli` ni `gh`.
- Ne pousse pas de tags git — il ne crée que des GitHub Releases. Pour un tag git assorti, faire `git tag vX.Y.Z && git push --tags` avant la Release.
- Ne signe ni ne notarise de binaires. Outils spécifiques à la plateforme.
- Ne publie pas vers Steam, itch.io ou les stores. À voir comme un plugin séparé.

## Licence

MIT — voir le [`LICENSE`](../LICENSE) à la racine.

## Documents connexes

- [SETUP.md](docs/SETUP.md) — installation + première release
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — liste manuelle en 7 étapes
- [README](../README.md) à la racine — vue d'ensemble de l'écosystème
