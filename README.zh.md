# Clairvoyance

[![codecov](https://codecov.io/gh/tvna/clairvoyance/branch/main/graph/badge.svg)](https://codecov.io/gh/tvna/clairvoyance)

[English](./README.md) | [日本語](./README.ja.md) | [简体中文](./README.zh.md) | [한국어](./README.ko.md)

放大智能体到人类的交接，把工作转化为人类可以信任的、有证据支撑的决策。

Clairvoyance 是一个 Claude Code 插件：一组 Agent Skills，智能体在需要把决策交还给
人类时加载它们。每次交接都通过可检查的方式让状态可见——证据、系统上下文、可选方案、
风险、可逆性以及推荐的下一步——以便人类可以批准、拒绝或安全地提出异议。

## 技能

| 技能 | 使用场景 |
|------|----------|
| `using-clairvoyance` | SessionStart 引导路由器。从下面挑选一个交接技能；由 SessionStart 钩子注入。 |
| `clairvoyance` | 一个应由人类决定的选择阻塞了智能体：决策、批准、推迟、回滚，或 2-3 个已准备好的方案。 |
| `review-verdict` | PR、提交、分支、工作区或合并候选需要一个带证据的就绪判定。 |
| `architecture-tradeoff` | 在方案、边界、依赖或故障模式之间做出系统级的架构决策。 |
| `decision-coaching` | 面对含糊、嘈杂或缺乏架构信息的输入，人类要求 LGTM／盖章式认可。 |
| `human-harness` | 面向人类的护栏：人类下达影响面大、不可逆或违反合规的指令时。它不立即执行，而是先停下，逐个追问意图，在人为失误落地之前将其拦截。 |
| `session-handoff` | 干净地重启优于信任框架的 compaction、仓库门禁限制了本会话能改动的范围，或工作尚未完成——下一个会话需要一段可直接粘贴的提示词来继续。 |

每次交接按风险（stakes）分支：可逆、低风险的决定给出紧凑的 `Verdict` + `Next Move`；
不可逆或有争议的决定给出完整交接。

`session-handoff` 有所不同——它交接给下一个智能体会话，而非人类。关于它为何存在、
以及何时应优先于框架的自动 compaction，请参阅
[docs/session-handoff.md](docs/session-handoff.md)。

## 安装

Clairvoyance 以单一插件树发布，并为每个运行时提供各自的清单
（`plugin/.claude-plugin/` 与 `plugin/.codex-plugin/`），因此无论你的智能体走哪条路径，
安装的都是同一套技能。

### Claude Code

添加 marketplace 并安装插件：

```
/plugin marketplace add tvna/clairvoyance
/plugin install clairvoyance
```

### Codex

使用 Codex CLI 添加仓库 marketplace 并安装插件：

```
codex plugin marketplace add tvna/clairvoyance
codex plugin add clairvoyance
```

仓库 marketplace 位于 [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json)，
Codex 读取 `plugin/.codex-plugin/plugin.json` 清单。

### apm（任何受支持的智能体）

[`microsoft/apm`](https://github.com/microsoft/apm) 会把 Clairvoyance 作为 marketplace
插件安装，并将其技能部署到它检测到的每个智能体（Claude Code、Codex 等）：

```bash
apm install tvna/clairvoyance
```

如需在项目中固定版本，把依赖加入你的 `apm.yml` 并运行 `apm install`：

```yaml
dependencies:
  apm:
    - tvna/clairvoyance
```

### 钩子的作用

插件注册了一个 `SessionStart` 钩子，在会话开始、clear 和 compaction 时注入
`using-clairvoyance` 引导技能（以及项目所有者的语言）。Claude Code 读取
`plugin/hooks/hooks.json`，Codex 读取 `plugin/hooks/codex-hooks.json`；两者都经由同一个
`hooks/run-hook.cmd` 包装器，仅在各运行时所替换的插件根变量上有所不同。请参阅
[docs/hooks.md](docs/hooks.md)。

## 仓库结构

marketplace 指向 `plugin/`（`source: "./plugin"`），因此**只有 `plugin/` 会被复制到
用户的安装缓存中**，其余一切都留在仓库中，永不分发。完整的目录树见
[docs/repository-layout.md](docs/repository-layout.md)。

## 开发

- **校验技能：** `waza check`（静态；无需评估后端或配额）。
- **运行评估：** `waza run` — 执行后端及配额耗尽时的处理见
  [docs/evaluations.md](docs/evaluations.md)。
- **CI** 在每个 pull request 上校验 JSON 清单和钩子脚本（无需外部服务）。脚本测试套件
  带覆盖率运行，门禁在本地（`pyproject.toml` 中的 `--cov-fail-under=100`）。结果也会上报
  到 [Codecov](https://codecov.io/gh/tvna/clairvoyance) 以保留趋势历史（仅供参考，绝不
  阻塞）。

## 版本与发布

采用语义化版本，借助 semantic-release 从 Conventional Commits 自动完成。git 标签是唯一
真实来源；每次发布都会把版本同步写入 Claude Code 与 Codex 两个 `plugin.json` 清单。
请参阅 [docs/versioning.md](docs/versioning.md)。

## 贡献

请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。提交必须遵循 Conventional Commits——它驱动
自动版本递增。

## 许可证

MIT。请参阅 [LICENSE](LICENSE)。
