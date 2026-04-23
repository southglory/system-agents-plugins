# unity-gamedev

![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![unity-gamedev release](https://img.shields.io/github/v/tag/southglory/system-agents-plugins?filter=unity-gamedev-*&label=unity-gamedev)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

Unity Editor + `unity-cli` + `gh` の組み合わせを**ワンコマンドのリリースパイプライン**に変える [system-agents-template](https://github.com/southglory/system-agents-template) プラグイン。

- **Build**: `unity-cli exec BuildPipeline.BuildPlayer(...)` — シーン・成果物名・ターゲットは呼び出し側が指定。**プロジェクト名のハードコーディングなし**
- **Zip**: `Builds/{NAME}{拡張子}` → `dist/{NAME}_{tag}.zip`
- **Release**: `gh release create {tag}`（再実行時は `gh release upload --clobber` にフォールバック）
- **アナウンス用**: stdout の 1 行 JSON はそのまま `discord-huddle-post` などに渡せる

## 🚀 ワンラインインストール（推奨）

このリポジトリを直接クローンせず、テンプレートのインストーラーを使います：

ローリング（常に最新 `main`）：

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

安定 Release を固定（再現性のため推奨）：

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```

プラグイン選択画面で `unity-gamedev` を選びます。インストール後に埋める秘密情報はありません — 既存の `gh` ログインをそのまま使います。

詳細：[`docs/SETUP.md`](docs/SETUP.md)。スモークテスト：[`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md)。

## すべて CLI フラグ

このプラグインの肝は **プロジェクト名をハードコードしないこと**。シーン、成果物名、Unity ビルドターゲット、プロジェクトルートは全部呼び出し側から渡します。特定のゲームに紐づく値は一切埋め込まれていません：

```bash
python bot/publish_build.py \
  --tag v0.1.0 \
  --scene Assets/Scenes/Main.unity \
  --output-name MyGame \
  --target StandaloneWindows64
```

`--scene` は繰り返し可（複数シーン）。`--skip-build` は既存の `Builds/{NAME}.*` を再利用。全フラグ表は `skills/publish-build/SKILL.md`。

## 出力: stdout に 1 行 JSON

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

stderr は人間が読む進捗ログ。この分離で、後段の「告知」ステップをスクリプト化しやすくなります。

## 他プラグインとの組み合わせ

| 対象 | 効果 | セットアップ | Recipe |
|---|---|---|---|
| [`discord-huddle`](../discord-huddle/) | Unity ビルド → GitHub Release → チャンネルに自動告知 | 両方をインストール。`publish-build` の JSON を `discord-huddle-post` にパイプ | [`recipes/unity-build-to-discord/`](../recipes/unity-build-to-discord/) |

## スラッシュスキル

| コマンド | 役割 |
|---|---|
| `/publish-build` | Build + zip + Release を一度で |

正式な契約は [`skills/publish-build/SKILL.md`](skills/publish-build/SKILL.md)。

## 要件

- **Python ≥ 3.10**（標準ライブラリのみ — `pip install` 不要）
- Unity Editor が起動していて、`unity-cli` が接続済み（`unity-cli status = ready`）
- `unity-cli v0.3+` が `PATH` にある
- `gh` CLI、`repo` scope で認証済み

## このプラグインがやらないこと

- Unity 自体、`unity-cli`、`gh` のインストールは行いません
- git タグは push しません — GitHub **Release** のみ作成。必要なら Release 前に `git tag vX.Y.Z && git push --tags`
- バイナリの署名 / 公証は行いません。プラットフォーム固有のツール範疇
- Steam / itch.io / アプリストアへのアップロードは行いません。別プラグインで扱うべき領域

## ライセンス

MIT — リポジトリルートの [`LICENSE`](../LICENSE) を参照。

## 関連ドキュメント

- [SETUP.md](docs/SETUP.md) — インストール + 初回リリース手順
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 7 ステップの手動テストチェックリスト
- ルート [README](../README.md) — プラグインエコシステム概観
