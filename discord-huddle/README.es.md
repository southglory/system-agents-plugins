# discord-huddle

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Un plugin de [system-agents-template](https://github.com/southglory/system-agents-template) que convierte un canal de Discord en el chat de equipo, la tubería de notas de reunión y el canal de anuncios de tu proyecto.

- **Pull**: archiva mensajes del canal como JSONL local (`/discord-huddle-sync`)
- **Push**: permite a agentes o usuarios publicar en el canal (`/discord-huddle-post`)
- **Listen**: notificaciones en tiempo real a través del WebSocket de Discord Gateway (`/discord-huddle-listen`)
- **Summarize**: un agente lee el log crudo y produce una nota de reunión en Markdown rastreada — sin costo de API LLM más allá de tu sesión de Claude Code (`/discord-huddle-summarize`)

## 🚀 Instalación en una línea (recomendada)

No clones este repo directamente. Usa el instalador del template:

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

Cuando te pregunte, elige `discord-huddle` de la lista de plugins. El instalador copia los archivos a tu proyecto, registra skills de slash globalmente, y siembra `.claude/secrets/discord-huddle.env.example`. Después de instalar, rellena ese archivo de secretos (Bot Token + Channel ID).

Setup detallado: [`docs/SETUP.md`](docs/SETUP.md). Smoke test manual: [`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md).

## Características clave

### REST sync + listener en tiempo real

- `sync` trae todo lo posterior a `last_read` por polling REST
- `listen` (Gateway) recibe eventos vía WebSocket y escribe pequeños archivos de señal que la herramienta Monitor de Claude Code recoge
- Úsalos juntos: listener da velocidad, sync garantiza completitud (adjuntos, reacciones al recibir por primera vez)

### Canal bidireccional

- Equipo → agente: el chat deja requerimientos, feedback, preguntas en Discord
- Agente → equipo: los agentes publican análisis, diagramas, capturas de páginas web, enlaces de build de vuelta al canal

### Resúmenes como activo del equipo

- Los Markdown de resumen aterrizan en `docs/discord-huddle-summaries/` y están **rastreados por git**
- Un nuevo compañero que hace `git clone` lee inmediatamente las notas de reunión pasadas
- El puntero de progreso de resumen (`index.json`) también se rastrea, así los conflictos de merge se resuelven determinísticamente (solo hacia adelante: tomar el msg_id más nuevo)

### Gate determinístico para summarize

Antes de que un agente gaste tokens resumiendo, llama:

```bash
python bot/discord_collab.py summarize-check
```

Un escaneo solo-código devuelve `{ready, reason, stats}`. Si `ready:false` (pocos mensajes, monólogo corto, etc.), el agente se detiene inmediatamente sin cargar raw a su contexto. Las reglas completas viven en [`skills/discord-huddle-summarize/SKILL.md`](skills/discord-huddle-summarize/SKILL.md).

### Instalación no invasiva

- Los datos en runtime (`raw/`, `inbox/`, `local-state.json`, `vc-snapshots/`) viven en `.system-agents/discord-huddle/` y el plugin auto-deposita `.gitignore: *` dentro — **nunca se toca el `.gitignore` raíz de tu proyecto**
- Las overrides de ruta pasan por el mismo `.env` (sin `export` separado):
  `SYSTEM_AGENTS_PROJECT_ROOT`, `DISCORD_HUDDLE_DATA_DIR`, `DISCORD_HUDDLE_SUMMARY_DIR`

### Mensajes de error amigables

Sin tracebacks de Python. 401/403/404/429 cada uno viene con una sugerencia de una línea apuntando a la solución exacta (Reset Token, re-invitar bot, verificar channel id, rate limit).

## Skills con slash

| Comando | Qué hace |
|---|---|
| `/discord-huddle-sync` | Trae mensajes nuevos del canal al JSONL crudo |
| `/discord-huddle-listen` | Listener WebSocket de Gateway en tiempo real |
| `/discord-huddle-post` | Publica un mensaje (con adjuntos o snapshot de página web opcionales) |
| `/discord-huddle-summarize` | El agente lee raw y escribe una nota de reunión |

El contrato exacto de cada skill está en `skills/<nombre>/SKILL.md`.

## Snapshot de página web (función opcional)

`/discord-huddle-post --vc-snapshot` renderiza un URL arbitrario como PNG usando Chromium headless y lo adjunta:

- URL explícito: `--vc-url https://my-dashboard.local`
- Auto-detección (opt-in): pasa `--vc-sessions-dir DIR` o `VC_SESSIONS_DIR` a un directorio con estructura `<session>/state/server-info` (JSON con campo `url`). Al plugin no le importa qué herramienta produce esos archivos.
- Requiere: `pip install -r requirements-optional.txt` + `playwright install chromium` (~200 MB, una sola vez).

## Ubicaciones de datos (por defecto)

| Ruta | Contenido | Rastreado por git |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Dumps de mensajes crudos | No (auto-gitignore) |
| `.system-agents/discord-huddle/inbox/` | Señales en tiempo real de Gateway | No |
| `.system-agents/discord-huddle/local-state.json` | Puntero sync por usuario | No |
| `.system-agents/discord-huddle/vc-snapshots/` | PNG de Playwright | No |
| `docs/discord-huddle-summaries/*.md` | Notas de reunión del equipo | **Sí** |
| `docs/discord-huddle-summaries/index.json` | Puntero de resumen solo hacia adelante | **Sí** |
| `docs/discord-huddle-summaries/attachments/` | Imágenes referenciadas por resúmenes | **Sí** |

## Combinación con otros plugins

| Objetivo | Efecto | Configuración | Recipe |
|---|---|---|---|
| `/schedule` integrado (Claude Code) | Anuncios recurrentes en el canal (dailies, reportes semanales) | Usa `/schedule` para cronar `discord-huddle-post` | Solo-docs (ver ejemplo cron en [README.ko.md](README.ko.md#조합-가능한-플러그인)) |
| (planeado) `unity-gamedev` | Build de Unity → GitHub Release → anuncio automático del enlace en canal | Instala ambos plugins; canaliza el JSON de `publish-build` a `discord-huddle-post` | `recipes/unity-build-to-discord/` (se añadirá junto con unity-gamedev) |

## Requisitos

- Python ≥ 3.10
- Discord Bot Token (crear en [Developer Portal](https://discord.com/developers/applications))
- **Message Content Intent** habilitado (requerido para Gateway listener)

## Licencia

MIT — ver el [`LICENSE`](../LICENSE) del repo-root.

## Documentos relacionados

- [SETUP.md](docs/SETUP.md) — instalación y configuración
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — lista de smoke test manual
- [README](../README.md) del repo-root — panorama del ecosistema de plugins
