# system-agents-plugins


![tests CI](https://github.com/southglory/system-agents-plugins/actions/workflows/tests.yml/badge.svg)
![Release](https://img.shields.io/github/v/release/southglory/system-agents-plugins?include_prereleases&sort=semver)
![License](https://img.shields.io/github/license/southglory/system-agents-plugins)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

[system-agents-template](https://github.com/southglory/system-agents-template) の公式プラグイン集。

各プラグインは独立したサブディレクトリに配置され、個別に配布されます。ユーザーは必要なプラグインだけ選んでインストールします。

## 🚀 ワンラインインストール（テンプレートのインストーラー経由）

このリポジトリを直接クローンする必要はありません — テンプレートの `install.sh` がここのプラグイン索引を読み込み、選択したプラグインをあなたのプロジェクトにコピーします：

ローリング（常に最新 `main`）:

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

安定 Release を固定（再現性のため推奨）:

```bash
curl -sSL https://github.com/southglory/system-agents-template/releases/latest/download/install.sh -o install.sh
bash install.sh
```


インストール先プラグインを訊かれたら、`discord-huddle`（または他の掲載プラグイン）を指定してください。

## 利用可能なプラグイン

| フォルダ | 概要 | ステータス |
|---|---|---|
| [`discord-huddle/`](discord-huddle/) | Discord チャンネルを用いたチーム会話 + 追跡型会議メモ | ✅ リリース済 (`discord-huddle-v0.1.0`) |
| [`unity-gamedev/`](unity-gamedev/) | Unity CLI ビルド → GitHub Release 公開 | ✅ リリース済 (`unity-gamedev-v0.1.0`) |

各プラグインフォルダを開くと、それぞれの README に詳細なセットアップ手順があります。

## インストールモデル

プラグインはファイルコピー（`cp -r`）でインストールされ、パッケージマネージャ（pip/npm）は使いません。プラグインファイルはプロジェクトツリーに直接マージされるため、管理されたインストールはテンプレートの `install.sh` が担います：

```bash
# 1. このリポジトリをクローン（インストーラーが自動で行う）
git clone https://github.com/southglory/system-agents-plugins.git

# 2. 必要なプラグインをプロジェクトにコピー（インストーラーが自動で行う）
cp -r discord-huddle/bot/* /path/to/your-project/bot/
cp -r discord-huddle/skills/* /path/to/your-project/skills/

# 3. Claude Code にスキルを登録（インストーラーが自動で行う）
cp -r discord-huddle/skills/* ~/.claude/skills/

# 4. Python 依存パッケージをインストール
cd /path/to/your-project
pip install -r discord-huddle/requirements.txt
```

手動の `cp -r` 手順は上級者向けのフォールバックです。通常はインストーラーの使用を推奨します。

## バージョン管理

各プラグインは独立してリリースされます。タグ形式：`<プラグイン名>-vX.Y.Z`。

- `discord-huddle-v0.1.0` — 初回公開リリース
- `unity-gamedev-v0.1.0` — 計画中

リポジトリ全体の単一バージョンはありません。テンプレート側のタグ（`v2.x.x`）とプラグイン側のタグは衝突しません。

## プラグインの組み合わせ

プラグインは単体で動くように設計されていますが、組み合わせて価値が増すものもあります。各プラグイン README は [`CONTRIBUTING.md`](CONTRIBUTING.md) に従って組み合わせ表を明記します。再利用可能な複合レシピは [`recipes/`](recipes/) に置きます。

## 互換性

- Claude Code（スラッシュスキルシステム）
- system-agents-template v2.x 以降
- Python ≥ 3.10
- Windows / macOS / Linux

プラグインが追加で要件を課す場合があります（例えば discord-huddle は Discord Bot Token が必要）。

## ライセンス

[MIT](LICENSE) — system-agents-template と同じ。

## コントリビュート

- バグ報告・フィードバック：GitHub Issues
- 新プラグイン：[`CONTRIBUTING.md`](CONTRIBUTING.md) の構造規約に従ってください

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=southglory/system-agents-template,southglory/system-agents-plugins&type=Date)](https://star-history.com/#southglory/system-agents-template&southglory/system-agents-plugins&Date)
