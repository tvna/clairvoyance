# Clairvoyance

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/tvna/clairvoyance)
[![codecov](https://codecov.io/gh/tvna/clairvoyance/branch/main/graph/badge.svg)](https://codecov.io/gh/tvna/clairvoyance)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English](./README.md) | [日本語](./README.ja.md) | [简体中文](./README.zh.md) | [한국어](./README.ko.md)

에이전트에서 사람으로의 인계를 증폭하여, 작업을 사람이 신뢰할 수 있는 증거 기반
의사결정으로 바꿉니다.

Clairvoyance는 Claude Code 플러그인입니다. 에이전트가 의사결정을 사람에게 되돌려야
할 때 로드하는 Agent Skills 모음으로 구성됩니다. 각 인계는 상태를 검사 가능한 형태로
가시화하여(증거, 시스템 맥락, 선택지, 위험, 가역성, 권장되는 다음 행동) 사람이 승인,
거부 또는 안전하게 이의를 제기할 수 있게 합니다.

## 스킬

| 스킬 | 사용 시점 |
|------|-----------|
| `using-clairvoyance` | SessionStart 부트스트랩 라우터. 아래 인계 스킬 중 하나를 선택하며, SessionStart 훅이 주입합니다. |
| `clairvoyance` | 사람이 결정해야 할 선택이 에이전트를 막고 있을 때: 의사결정, 승인, 보류, 롤백, 또는 준비된 2~3개의 선택지. |
| `review-verdict` | PR, 커밋, 브랜치, 워킹 트리 또는 머지 후보에 증거를 갖춘 준비 완료 판정이 필요할 때. |
| `architecture-tradeoff` | 선택지, 경계, 의존성 또는 장애 모드 사이의 시스템 수준 아키텍처 결정. |
| `decision-coaching` | 모호하거나 잡음이 많거나 아키텍처 정보가 부족한 입력에 대해 사람이 LGTM／형식적 승인을 요청할 때. |
| `human-harness` | 사람을 위한 하니스: 영향 범위가 크거나 되돌릴 수 없거나 규정을 위반하는 지시를 사람이 내릴 때. 즉시 실행하지 않고 멈춰서 의도를 한 번에 하나씩 추궁해 사람의 실수가 발생하기 전에 잡아낸다. |
| `session-handoff` | 하네스의 compaction을 신뢰하기보다 깔끔하게 재시작하는 편이 나을 때, 저장소 게이트가 이 세션이 바꿀 수 있는 범위를 제한할 때, 또는 작업이 미완료라 다음 세션이 이어가기 위한 붙여넣기 가능한 프롬프트가 필요할 때. |

각 인계는 위험도(stakes)에 따라 분기합니다. 가역적이고 위험이 낮은 결정은 간결한
`Verdict` + `Next Move`를, 비가역적이거나 논쟁의 여지가 있는 결정은 전체 인계를
제공합니다.

`session-handoff`는 다릅니다. 사람이 아니라 다음 에이전트 세션으로 인계합니다. 그것이
왜 존재하며 언제 하네스의 자동 compaction보다 우선해야 하는지는
[docs/session-handoff.md](docs/session-handoff.md)를 참고하세요.

## 설치

Clairvoyance는 런타임별 매니페스트(`.claude-plugin/`와 `.codex-plugin/`)와
함께 하나의 플러그인 트리로 배포되므로, 에이전트가 어떤 경로를 사용하든 동일한
스킬이 설치됩니다.

### Claude Code

마켓플레이스를 추가하고 플러그인을 설치합니다:

```
/plugin marketplace add tvna/clairvoyance
/plugin install clairvoyance
```

### Codex

Codex CLI로 저장소 마켓플레이스를 추가하고 플러그인을 설치합니다:

```
codex plugin marketplace add tvna/clairvoyance
codex plugin add clairvoyance
```

저장소 마켓플레이스는 [.agents/plugins/marketplace.json](.agents/plugins/marketplace.json)
에 있으며, Codex는 `.codex-plugin/plugin.json` 매니페스트를 읽습니다.

### apm (지원되는 모든 에이전트)

[`microsoft/apm`](https://github.com/microsoft/apm)은 Clairvoyance를 마켓플레이스
플러그인으로 설치하고, 감지한 모든 에이전트(Claude Code, Codex 등)에 스킬을
배포합니다:

```bash
apm install tvna/clairvoyance
```

프로젝트에 고정하려면 `apm.yml`에 의존성을 추가하고 `apm install`을 실행합니다:

```yaml
dependencies:
  apm:
    - tvna/clairvoyance
```

### 훅의 역할

플러그인은 `SessionStart` 훅을 등록하여 세션 시작, clear, compaction 시점에
`using-clairvoyance` 부트스트랩 스킬(과 프로젝트 소유자의 언어)을 주입합니다.
Claude Code는 `hooks/hooks.json`을, Codex는 `hooks/codex-hooks.json`을
읽습니다. 둘 다 동일한 `hooks/run-hook.cmd` 래퍼를 거치며, 각 런타임이 치환하는
플러그인 루트 변수만 다릅니다. [docs/hooks.md](docs/hooks.md)를 참고하세요.

## 저장소 구조

플러그인은 **저장소 루트**(`source: "./"`)에 위치합니다. 이는 apm이 요구하는
레이아웃으로, apm은 패키지 루트의 `skills/`에서 스킬을, `hooks/`에서 훅을 찾아
배포합니다. 소비자 에이전트에 배포되는 런타임 프리미티브는 스킬과 훅뿐이며,
테스트·도구·CI·문서·eval 스위트는 개발용으로 저장소에 남고 배포되지 않습니다.
전체 트리는 [docs/repository-layout.md](docs/repository-layout.md)를 참고하세요.

## 개발

- **스킬 검증:** `waza check` (정적, 평가 백엔드나 쿼터 불필요).
- **평가 실행:** `waza run` — 실행 백엔드와 쿼터 소진 시 대처는
  [docs/evaluations.md](docs/evaluations.md)를 참고하세요.
- **CI**는 모든 pull request에서 JSON 매니페스트와 훅 스크립트를 검증합니다(외부 서비스
  불필요). 스크립트 테스트 스위트는 커버리지와 함께 실행되며, 게이트는 로컬
  (`pyproject.toml`의 `--cov-fail-under=100`)입니다. 결과는 추세 기록을 위해
  [Codecov](https://codecov.io/gh/tvna/clairvoyance)에도 보고됩니다(참고용이며 절대
  차단하지 않습니다).

## 버전 관리와 릴리스

시맨틱 버저닝을 따르며, Conventional Commits로부터 semantic-release로 자동화됩니다.
git 태그가 단일 진실 공급원이며, 각 릴리스는 버전을 Claude Code와 Codex 양쪽
`plugin.json` 매니페스트에 동기화하여 기록합니다.
[docs/versioning.md](docs/versioning.md)를 참고하세요.

## 기여

[CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요. 커밋은 Conventional Commits를 따라야
하며, 이것이 자동 버전 증가를 구동합니다.

## 라이선스

MIT. [LICENSE](LICENSE)를 참고하세요.
