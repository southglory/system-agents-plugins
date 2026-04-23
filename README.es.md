# system-agents-plugins


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/southglory/system-agents-plugins?include_prereleases&sort=semver)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Plugins oficiales para [system-agents-template](https://github.com/southglory/system-agents-template).

Cada plugin vive en su propio subdirectorio y se distribuye de forma independiente. Los usuarios instalan solo los plugins que necesiten.

## 🚀 Instalación en una línea (mediante el instalador del template)

No clones este repositorio directamente — el `install.sh` del template lee el índice de plugins aquí y copia los plugins seleccionados a tu proyecto:

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


Cuando el instalador pregunte qué plugins instalar, responde `discord-huddle` (o cualquier otro listado).

## Plugins disponibles

| Carpeta | Resumen | Estado |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | Chat de equipo + notas de reunión vía Discord | ✅ Publicado (`discord-huddle-v0.1.0`) |
| [`unity-gamedev/`](unity-gamedev/) | Build con Unity CLI → publicación en GitHub Release | ✅ Publicado (`unity-gamedev-v0.1.0`) |

Abre cada carpeta de plugin para ver su README detallado.

## Modelo de instalación

Los plugins se instalan por copia de archivos (`cp -r`), no mediante un gestor de paquetes (pip/npm). Los archivos del plugin se fusionan directamente en tu árbol de proyecto, por lo que la instalación gestionada la realiza el `install.sh` del template:

```bash
# 1. Clonar este repositorio (el instalador lo hace automáticamente)
git clone https://github.com/southglory/system-agents-plugins.git

# 2. Copiar el plugin deseado a tu proyecto (el instalador lo hace)
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. Registrar skills en Claude Code (el instalador lo hace)
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. Instalar dependencias de Python
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

El flujo manual `cp -r` existe como respaldo para usuarios avanzados; se recomienda el instalador.

## Versionado

Cada plugin se publica independientemente. Formato de etiqueta: `<nombre-plugin>-vX.Y.Z`.

- `discord-huddle-v0.1.0` — primera versión pública
- `unity-gamedev-v0.1.0` — planeado

No hay una versión única para el repo. Las etiquetas del template (`v2.x.x`) y las de plugins nunca chocan.

## Combinar plugins

Los plugins están diseñados para funcionar por sí solos, pero algunos se complementan. Ver [`CONTRIBUTING.md`](CONTRIBUTING.md) para la convención de matriz de combinaciones que cada README de plugin debe documentar. Las combinaciones reutilizables viven en [`recipes/`](recipes/).

## Compatibilidad

- Claude Code (sistema de skills con slash)
- system-agents-template v2.x o superior
- Python ≥ 3.10
- Windows / macOS / Linux

Algunos plugins añaden requisitos adicionales (por ejemplo, discord-huddle necesita un Bot Token de Discord).

## Licencia

[MIT](LICENSE) — igual que system-agents-template.

## Contribuir

- Reportes de bugs y feedback: GitHub Issues
- Nuevos plugins: sigue las convenciones de estructura en [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
