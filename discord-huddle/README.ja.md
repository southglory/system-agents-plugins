# discord-huddle

[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Français](README.fr.md)

[system-agents-template](https://github.com/southglory/system-agents-template) プラグイン。Discord チャンネルをプロジェクトのチームチャット、会議メモのパイプ、通知チャネルに変えます。

- **プル**：チャンネルメッセージをローカル JSONL としてアーカイブ (`/discord-huddle-sync`)
- **プッシュ**：エージェントやユーザーがチャンネルに投稿 (`/discord-huddle-post`)
- **リッスン**：Discord Gateway WebSocket によるリアルタイム通知 (`/discord-huddle-listen`)
- **要約**：エージェントが raw ログを読み、git 追跡される Markdown 会議メモを作成。Claude Code セッション以外の LLM API 費用は発生しません (`/discord-huddle-summarize`)

## 🚀 ワンラインインストール（推奨）

このリポジトリを直接クローンしないでください。テンプレートのインストーラーを使います：

```bash
curl -sSL https://raw.githubusercontent.com/southglory/system-agents-template/main/install.sh -o install.sh
bash install.sh
```

インストール対象プラグインを訊かれたら `discord-huddle` を選択。インストーラーがファイルをプロジェクトにコピーし、スラッシュスキルをグローバル登録し、`.claude/secrets/discord-huddle.env.example` を配置します。インストール後はその `.env` ファイルに Bot Token と Channel ID を入れれば完了です。

詳細セットアップ：[`docs/SETUP.md`](docs/SETUP.md)。手動スモークテスト：[`docs/SMOKE_TEST.md`](docs/SMOKE_TEST.md)。

## 主な機能

### REST sync + リアルタイム listener

- `sync` は `last_read` 以降のすべてを REST ポーリングで取得
- `listen`（Gateway）は WebSocket でイベントを受け、小さなシグナルファイルを書き出します。Claude Code の Monitor ツールがそれを拾います
- 併用が基本：listener は速度、sync は完全性（初回受信時の添付・リアクションなど）を担保

### 双方向チャネル

- チーム → エージェント：Discord から要件、フィードバック、質問が流れ込む
- エージェント → チーム：分析、ダイアグラム、ウェブページのスクリーンショット、ビルドリリースリンクをチャンネルへ返送

### 要約をチーム資産に

- 要約 Markdown は `docs/discord-huddle-summaries/` に置かれ、**git で追跡**されます
- 新メンバーが `git clone` するだけで過去の会議メモがすぐに読める
- 要約進捗ポインタ（`index.json`）も追跡されるため、マージコンフリクトは決定的に解決（前進専用：新しい msg_id を採る）

### 決定的な summarize ゲート

エージェントが要約のためにトークンを使う前に、以下を呼びます：

```bash
python bot/discord_collab.py summarize-check
```

コードだけで走査し、`{ready, reason, stats}` を返します。`ready:false` ならエージェントは raw をコンテキストに読み込まずすぐに終了。詳細ルールは [`skills/discord-huddle-summarize/SKILL.md`](skills/discord-huddle-summarize/SKILL.md)。

### 非侵襲なインストール

- ランタイムデータ（`raw/`、`inbox/`、`local-state.json`、`vc-snapshots/`）は `.system-agents/discord-huddle/` に格納され、プラグインがその中に `.gitignore: *` を自動投下 — **プロジェクトルートの `.gitignore` は触りません**
- パスのオーバーライドは同じ `.env` で可能（別途 `export` 不要）：
  `SYSTEM_AGENTS_PROJECT_ROOT`、`DISCORD_HUDDLE_DATA_DIR`、`DISCORD_HUDDLE_SUMMARY_DIR`

### 親切なエラーメッセージ

生の Python トレースバックが漏れません。401/403/404/429 それぞれに 1 行の改善策ヒント（Reset Token、Bot 再招待、Channel ID 確認、レート制限など）が付きます。

## スラッシュスキル

| コマンド | 役割 |
|---|---|
| `/discord-huddle-sync` | 新しいチャンネルメッセージを raw JSONL に取り込む |
| `/discord-huddle-listen` | Gateway WebSocket のリアルタイム listener |
| `/discord-huddle-post` | メッセージを投稿（添付やウェブページスナップショット可） |
| `/discord-huddle-summarize` | エージェントが raw を読んで会議メモを書く |

各スキルの正確な契約は `skills/<name>/SKILL.md` にあります。

## ウェブページスナップショット（オプション機能）

`/discord-huddle-post --vc-snapshot` は任意の URL をヘッドレス Chromium で PNG レンダリングして添付します：

- 明示的 URL：`--vc-url https://my-dashboard.local`
- 自動検出（オプトイン）：`--vc-sessions-dir DIR` または `VC_SESSIONS_DIR` を `<session>/state/server-info` 構造のディレクトリに向ける（`url` フィールドを持つ JSON）。プラグインはどのツールが書いたファイルかを気にしません。
- 要件：`pip install -r requirements-optional.txt` + `playwright install chromium`（約 200MB、初回のみ）。

## データ配置（デフォルト）

| パス | 内容 | git 追跡 |
|---|---|---|
| `.system-agents/discord-huddle/raw/*.jsonl` | Raw メッセージダンプ | なし（自動 gitignore） |
| `.system-agents/discord-huddle/inbox/` | Gateway リアルタイムシグナル | なし |
| `.system-agents/discord-huddle/local-state.json` | ユーザーローカルの sync ポインタ | なし |
| `.system-agents/discord-huddle/vc-snapshots/` | Playwright PNG | なし |
| `docs/discord-huddle-summaries/*.md` | チーム会議メモ | **あり** |
| `docs/discord-huddle-summaries/index.json` | 前進専用の要約ポインタ | **あり** |
| `docs/discord-huddle-summaries/attachments/` | 要約が参照する画像 | **あり** |

## 他プラグインとの組み合わせ

| 対象 | 効果 | セットアップ | Recipe |
|---|---|---|---|
| 組み込み `/schedule`（Claude Code） | チャンネルで定期告知（デイリースタンドアップ、週次レポート） | `/schedule` で `discord-huddle-post` を cron | ドキュメントのみの組み合わせ（cron 例は [README.ko.md](README.ko.md#조합-가능한-플러그인)） |
| （計画中）`unity-gamedev` | Unity ビルド → GitHub Release → チャンネルリンク自動告知 | 両方のプラグインをインストール。`publish-build` の JSON を `discord-huddle-post` に流す | `recipes/unity-build-to-discord/`（unity-gamedev と共に追加予定） |

## 要件

- Python ≥ 3.10
- Discord Bot Token（[Developer Portal](https://discord.com/developers/applications) で作成）
- **Message Content Intent** 有効化（Gateway listener に必須）

## ライセンス

MIT — リポジトリルートの [`LICENSE`](../LICENSE) を参照。

## 関連ドキュメント

- [SETUP.md](docs/SETUP.md) — インストールと設定
- [SMOKE_TEST.md](docs/SMOKE_TEST.md) — 手動スモークテストチェックリスト
- リポジトリルート [README](../README.md) — プラグインエコシステム概観
