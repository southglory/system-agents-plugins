# system-agents-plugins


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/southglory/system-agents-plugins?include_prereleases&sort=semver)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Plugins officiels pour [system-agents-template](https://github.com/southglory/system-agents-template).

Chaque plugin vit dans son propre sous-dossier et est distribué indépendamment. Les utilisateurs n'installent que les plugins dont ils ont besoin.

## 🚀 Installation en une ligne (via l'installateur du template)

Vous ne clonez pas ce dépôt directement — le `install.sh` du template lit l'index des plugins ici et copie les plugins sélectionnés dans votre projet :

Rolling (toujours le `main` le plus récent):

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

Épinglé sur une Release stable (recommandé pour la reproductibilité):

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```


Lorsque l'installateur demande quels plugins installer, choisissez `discord-huddle` (ou tout autre plugin listé).

## Plugins disponibles

| Dossier | Résumé | Statut |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | Chat d'équipe + notes de réunion suivies via Discord | ✅ Publié (`discord-huddle-v0.1.0`) |
| `unity-gamedev/` | Build Unity CLI → publication GitHub Release | 🚧 Prévu |

Ouvrez chaque dossier de plugin pour voir son propre README avec les détails d'installation.

## Modèle d'installation

Les plugins sont installés par copie de fichiers (`cp -r`), pas via un gestionnaire de paquets (pip/npm). Les fichiers du plugin fusionnent directement dans votre arbre de projet, donc l'installation gérée revient au `install.sh` du template :

```bash
# 1. Cloner ce dépôt (l'installateur le fait automatiquement)
git clone https://github.com/southglory/system-agents-plugins.git

# 2. Copier le plugin souhaité dans votre projet (fait par l'installateur)
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. Enregistrer les compétences dans Claude Code (fait par l'installateur)
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. Installer les dépendances Python
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

Le flux manuel `cp -r` existe comme solution de secours pour les utilisateurs avancés ; l'installateur est recommandé.

## Gestion des versions

Chaque plugin est publié indépendamment. Format de tag : `<nom-plugin>-vX.Y.Z`.

- `discord-huddle-v0.1.0` — première version publique
- `unity-gamedev-v0.1.0` — prévu

Il n'y a pas de version unique pour le dépôt. Les tags du template (`v2.x.x`) et ceux des plugins ne se chevauchent jamais.

## Combiner des plugins

Les plugins sont conçus pour fonctionner seuls, mais certains se complètent. Voir [`CONTRIBUTING.md`](CONTRIBUTING.md) pour la convention de matrice de compatibilité que chaque README de plugin doit documenter. Les combinaisons réutilisables inter-plugins vivent dans [`recipes/`](recipes/).

## Compatibilité

- Claude Code (système de compétences en slash)
- system-agents-template v2.x ou plus récent
- Python ≥ 3.10
- Windows / macOS / Linux

Certains plugins ajoutent des exigences supplémentaires (par exemple, discord-huddle nécessite un Bot Token Discord).

## Licence

[MIT](LICENSE) — identique à system-agents-template.

## Contribuer

- Rapports de bugs et retours : GitHub Issues
- Nouveaux plugins : suivez les conventions de structure dans [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
