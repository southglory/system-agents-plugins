# discord-huddle


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![discord-huddle release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=discord-huddle-*&label=discord-huddle)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Un plugin [system-agents-template](https://github.com/southglory/system-agents-template) qui transforme un canal Discord en chat d'équipe, pipeline de notes de réunion et canal d'annonces pour votre projet.

- **Pull** : archivez les messages du canal en JSONL local (`/discord-huddle-sync`)
- **Push** : laissez les agents ou utilisateurs poster dans le canal (`/discord-huddle-post`)
- **Listen** : notifications temps-réel via le WebSocket de la Gateway Discord (`/discord-huddle-listen`)
- **Summarize** : un agent lit le log brut et produit une note de réunion Markdown suivie par git — pas de coût API LLM au-delà de votre session Claude Code (`/discord-huddle-summarize`)

## 🚀 Installation en une ligne (recommandée)

Ne clonez pas ce dépôt directement. Utilisez l'installateur du template :

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


Quand on vous le demande, choisissez `discord-huddle`. L'installateur copie les fichiers dans votre projet, enregistre les skills slash globalement, et dépose `.claude/secrets/discord-huddle.env.example`. Après l'installation, remplissez ce fichier de secrets (Bot Token + Channel ID) et c'est bon.

Installation détaillée : [`docs/SETUP.md`](docs/SETUP.md). Smoke test manuel : [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Fonctionnalités clés

### Sync REST + listener temps-réel

- `sync` récupère tout ce qui suit `last_read` via polling REST
- `listen` (Gateway) reçoit les événements par WebSocket et écrit de petits fichiers de signal que l'outil Monitor de Claude Code récupère
- À utiliser ensemble : listener pour la vitesse, sync pour la complétude (pièces jointes, réactions à la première réception)

### Canal bidirectionnel

- Équipe → agent : le chat dépose besoins, retours, questions dans Discord
- Agent → équipe : les agents postent analyses, diagrammes, captures de pages web, liens de build directement dans le canal

### Résumés comme actif d'équipe

- Les Markdown de résumé atterrissent dans `docs/discord-huddle-summaries/` et sont **suivis par git**
- Un nouveau coéquipier qui fait `git clone` lit immédiatement les notes de réunion passées
- Le pointeur de progression des résumés (`index.json`) est lui aussi suivi, donc les conflits de merge se résolvent de façon déterministe (avant seulement : on prend le msg_id le plus récent)

### Gate déterministe pour summarize

Avant qu'un agent dépense des tokens pour résumer, il appelle :

```bash
python bot/discord_collab.py summarize-check
```

Un scan uniquement code renvoie `{ready, reason, stats}`. Si `ready:false` (trop peu de messages, monologue court, etc.), l'agent s'arrête immédiatement sans charger le raw dans son contexte. Les règles complètes sont dans [`skills/discord-huddle-summarize/SKILL.md`](skills/discord-huddle-summarize/SKILL.md).

### Installation non invasive

- Les données runtime (`raw/`, `inbox/`, `local-state.json`, `vc-snapshots/`) vivent dans `.system-agents/discord-huddle/`, et le plugin y dépose automatiquement un `.gitignore: *` — **le `.gitignore` racine de votre projet n'est jamais touché**
- Les overrides de chemin passent par le même `.env` (pas besoin d'`export` séparé) :
  `SYSTEM_AGENTS_PROJECT_ROOT`, `DISCORD_HUDDLE_DATA_DIR`, `DISCORD_HUDDLE_SUMMARY_DIR`

### Messages d'erreur conviviaux

Pas de traceback Python qui fuit. 401/403/404/429 viennent chacun avec un indice d'une ligne pointant vers la remédiation exacte (Reset Token, réinviter le bot, vérifier l'ID du canal, rate limit).

## Skills slash

| Commande | Rôle |
|---|---|
| `/discord-huddle-sync` | Récupère les nouveaux messages du canal dans le JSONL brut |
| `/discord-huddle-listen` | Listener temps-réel WebSocket Gateway |
| `/discord-huddle-post` | Poste un message (avec pièces jointes ou snapshot de page web optionnels) |
| `/discord-huddle-summarize` | L'agent lit le raw et écrit une note de réunion |

Le contrat exact de chaque skill est dans `skills/<nom>/SKILL.md`.

## Snapshot de page web (fonction optionnelle)

`/discord-huddle-post --vc-snapshot` rend une URL arbitraire en PNG avec Chromium headless et l'attache :

- URL explicite : `--vc-url https://my-dashboard.local`
- Auto-détection (opt-in) : passez `--vc-sessions-dir DIR` ou `VC_SESSIONS_DIR` vers un dossier en structure `<session>/state/server-info` (JSON contenant un champ `url`). Le plugin se moque de quel outil produit ces fichiers.
- Nécessite : `pip install -r requirements-optional.txt` + `playwright install chromium` (~200 Mo, une fois).

## Emplacements des données (par défaut)

| Chemin | Contenu | Suivi par git ? |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Dumps de messages bruts | Non (auto-gitignore) |
| `.system-agents/discord-huddle/inbox/` | Signaux temps-réel Gateway | Non |
| `.system-agents/discord-huddle/local-state.json` | Pointeur de sync par utilisateur | Non |
| `.system-agents/discord-huddle/vc-snapshots/` | PNG Playwright | Non |
| `docs/discord-huddle-summaries/*.md` | Notes de réunion d'équipe | **Oui** |
| `docs/discord-huddle-summaries/index.json` | Pointeur de résumé avant seulement | **Oui** |
| `docs/discord-huddle-summaries/attachments/` | Images référencées par les résumés | **Oui** |

## Combinaison avec d'autres plugins

| Cible | Effet | Configuration | Recipe |
|---|---|---|---|
| `/schedule` intégré (Claude Code) | Annonces récurrentes dans le canal (daily, rapports hebdos) | Utiliser `/schedule` pour cron `discord-huddle-post` | Docs-only combo (exemple cron dans [README.ko.md](README.ko.md#조합-가능한-플러그인)) |
| [`unity-gamedev`](../unity-gamedev/) | Build Unity → GitHub Release → annonce auto du lien dans le canal | Installer les deux plugins ; piper le JSON de `publish-build` vers `discord-huddle-post` | `recipes/unity-build-to-discord/` (sera ajouté avec unity-gamedev) |

## Prérequis

- Python ≥ 3.10
- Discord Bot Token (à créer dans le [Developer Portal](https://discord.com/developers/applications))
- **Message Content Intent** activé (requis pour le listener Gateway)

## Licence

MIT — voir le [`LICENSE`](../LICENSE) à la racine du dépôt.

## Documents connexes

- [SETUP.md](docs/SETUP.md) — installation et configuration
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — checklist de smoke test manuel
- [README](../README.md) à la racine du dépôt — vue d'ensemble de l'écosystème de plugins

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
