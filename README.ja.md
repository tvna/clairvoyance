# Clairvoyance

[![codecov](https://codecov.io/gh/tvna/clairvoyance/branch/main/graph/badge.svg)](https://codecov.io/gh/tvna/clairvoyance)

[English](./README.md) | [日本語](./README.ja.md) | [简体中文](./README.zh.md) | [한국어](./README.ko.md)

エージェントから人間への引き継ぎを増幅し、作業を人間が信頼できる証拠ベースの
意思決定へと変えます。

Clairvoyance は Claude Code プラグインです。意思決定を人間に差し戻す必要が生じた
ときにエージェントが読み込む Agent Skills の集合で構成されます。各引き継ぎは状態を
検査可能な形で可視化し（証拠、システム文脈、選択肢、リスク、可逆性、推奨される次の
一手）、人間が承認・却下・安全に異議を唱えられるようにします。

## スキル

| スキル | 使う場面 |
|--------|----------|
| `using-clairvoyance` | SessionStart のブートストラップ・ルーター。下記の引き継ぎスキルを1つ選ぶ。SessionStart フックが注入する。 |
| `clairvoyance` | 人間に委ねるべき選択がエージェントを止めている場合：意思決定、承認、保留、ロールバック、または2〜3個の準備済み選択肢。 |
| `review-verdict` | PR・コミット・ブランチ・作業ツリー・マージ候補に、証拠付きの可否判定が必要な場合。 |
| `architecture-tradeoff` | 選択肢・境界・依存関係・障害モードの間で行うシステムレベルのアーキテクチャ判断。 |
| `decision-coaching` | 曖昧・ノイズの多い・アーキテクチャ情報の乏しい入力に対して、人間が LGTM／追認を求めてきた場合。 |
| `human-harness` | 人に対するハーネス：blast radius が大きい・不可逆・コンプライアンス違反となる指示を人間が出した場合。即実行せず、いったん止めて意図を一問ずつ追求し、ヒューマンエラーが起きる前に捕まえる。 |
| `session-handoff` | ハーネスの compaction を信頼するよりクリーンに再起動した方がよい、リポジトリのゲートでこのセッションが変更できる範囲が制限される、または作業が未完了で、次のセッションが再開のために貼り付け可能なプロンプトを必要としている場合。 |

各引き継ぎは賭け金（stakes）で分岐します。可逆で低リスクなものはコンパクトな
`Verdict` + `Next Move` を、不可逆または異論のあるものは完全な引き継ぎを生成します。

`session-handoff` は別物です。人間ではなく次のエージェント・セッションへ引き継ぎます。
なぜ存在し、いつハーネスの自動 compaction より優先すべきかは
[docs/session-handoff.md](docs/session-handoff.md) を参照してください。

## インストール

Clairvoyance は1つのプラグインツリーをランタイムごとのマニフェスト
（`.claude-plugin/` と `.codex-plugin/`）と共に配布するため、エージェントが
使う経路を問わず同じスキルがインストールされます。

### Claude Code

マーケットプレイスを追加してプラグインをインストールします:

```
/plugin marketplace add tvna/clairvoyance
/plugin install clairvoyance
```

### Codex

Codex CLI でリポジトリ・マーケットプレイスを追加し、プラグインをインストールします:

```
codex plugin marketplace add tvna/clairvoyance
codex plugin add clairvoyance
```

リポジトリ・マーケットプレイスは [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json)
にあり、Codex は `.codex-plugin/plugin.json` マニフェストを読み込みます。

### apm（対応する任意のエージェント）

[`microsoft/apm`](https://github.com/microsoft/apm) は Clairvoyance をマーケットプレイス
プラグインとしてインストールし、検出したすべてのエージェント（Claude Code、Codex
ほか）にスキルを展開します:

```bash
apm install tvna/clairvoyance
```

プロジェクトで固定するには、`apm.yml` に依存関係を追加して `apm install` を実行します:

```yaml
dependencies:
  apm:
    - tvna/clairvoyance
```

### フックの役割

プラグインは `SessionStart` フックを登録し、セッション開始・clear・compaction の
タイミングで `using-clairvoyance` ブートストラップスキル（とプロジェクトオーナーの言語）
を注入します。Claude Code は `hooks/hooks.json` を、Codex は
`hooks/codex-hooks.json` を読み込みます。両者は同じ `hooks/run-hook.cmd`
ラッパーを経由し、各ランタイムが差し込むプラグインルート変数だけが異なります。
[docs/hooks.md](docs/hooks.md) を参照してください。

## リポジトリ構成

プラグインは**リポジトリのルート**（`source: "./"`）に置かれます。これは apm が
要求するレイアウトで、apm はパッケージのルート直下の `skills/` からスキルを、
`hooks/` からフックを検出して展開します。コンシューマーのエージェントに展開される
ランタイムプリミティブはスキルとフックだけで、テスト・ツール・CI・ドキュメント・
eval スイートは開発用にリポジトリへ残り、展開されることはありません。完全なツリーは
[docs/repository-layout.md](docs/repository-layout.md) を参照してください。

## 開発

- **スキルの検証:** `waza check`（静的。評価バックエンドやクォータは不要）。
- **評価の実行:** `waza run` — 実行バックエンドとクォータ枯渇時の対処は
  [docs/evaluations.md](docs/evaluations.md) を参照。
- **CI** は各プルリクエストで JSON マニフェストとフックスクリプトを検証します（外部
  サービスは不要）。スクリプトのテストスイートはカバレッジ付きで実行され、ゲートは
  ローカル（`pyproject.toml` の `--cov-fail-under=100`）です。結果はトレンド履歴のため
  [Codecov](https://codecov.io/gh/tvna/clairvoyance) にも報告されます（情報提供のみ、
  ブロックはしません）。

## バージョニングとリリース

セマンティック・バージョニングを採用し、Conventional Commits から semantic-release で
自動化しています。git タグが真実の源であり、各リリースはバージョンを Claude Code と
Codex 両方の `plugin.json` マニフェストへ同期して書き込みます。
[docs/versioning.md](docs/versioning.md) を参照してください。

## コントリビュート

[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。コミットは Conventional Commits
に従う必要があります — これが自動バージョンアップを駆動します。

## ライセンス

MIT。[LICENSE](LICENSE) を参照してください。
