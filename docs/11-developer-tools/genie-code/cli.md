# Genie Code CLI

> 기준일: 2026-10-28 · 근거: 공식 문서 · 상태: **Beta**

## 왜 필요한가

워크스페이스의 Genie Code는 브라우저 안에서 노트북과 SQL을 다룹니다. 그런데 개발자는 로컬 저장소에서 코드를 고치고, 터미널에서 테스트하고, 워크스페이스의 데이터를 확인하는 흐름으로 일하는 경우가 많습니다. Genie Code CLI는 이 흐름을 터미널 안으로 가져옵니다.

문서는 Genie Code CLI를 "a coding agent that runs in your terminal, tuned for data and AI work on Databricks"라고 설명합니다. 로컬 파일을 다루고, Databricks CLI로 데이터를 찾고 질문에 답하며, 파이프라인, 모델, 앱을 만들고 배포하는 데 쓰인다고 합니다.

## 어떻게 동작하는가

### 상태와 주의

> **주의** 문서는 이 CLI가 **Beta** 이며 "early release, and its capabilities, commands, and interfaces change frequently"라고 명시합니다. 명령과 옵션이 바뀔 수 있으므로, 자동화 스크립트에 넣기 전에 현재 문서의 명령을 다시 확인합니다.

- 릴리즈 노트: 2026-10-06 "Genie Code CLI is in Beta"
- 문서 최종 업데이트: 2026-10-20 (문서 표기)

### 설치

macOS와 Linux에서는 다음 명령으로 설치합니다.

```bash
curl -fsSL https://github.com/databricks/genie-code-cli/releases/latest/download/install.sh | bash
```

Windows(PowerShell)는 문서가 `powershell -ExecutionPolicy Bypass -c "irm .../install.ps1 | iex"` 형식을 안내합니다. 문서는 경로의 나머지 부분을 생략해 표기하므로, 정확한 URL은 공식 문서의 설치 안내에서 복사합니다.

설치 후 확인과 갱신은 다음과 같습니다.

```bash
genie --version
genie update
```

문서는 갱신 방법으로 `genie update` 또는 설치 명령 재실행을 제시하고, CLI가 시작할 때 갱신을 확인한다고 설명합니다.

> **참고** 문서 설치 명령은 GitHub 릴리즈 스크립트를 셸로 실행하는 형식입니다. 회사 정책상 스크립트 직접 실행이 금지된 환경이라면 팀의 승인된 설치 절차를 따릅니다.

### 사전 요건과 인증

- **Databricks CLI 1.0.0 이상** 이 별도로 설치되어 있어야 합니다. Genie Code CLI는 인증과 `databricks genie` 명령에 Databricks CLI를 씁니다.
- 실행 시 Databricks CLI 프로필을 고르거나, 프로필이 없으면 인증합니다.
- 프로필은 Unity Gateway를 통해 모델에 접근하는 데 쓰입니다. 다른 워크스페이스를 보려면 다른 프로필을 씁니다.
- 문서는 "Only OAuth machine-to-machine (M2M) authentication is supported."라고 명시합니다. 사용자 신원으로 로그인하는 방식이 어떻게 맞는지는 문서만으로 확정하기 어려우므로, 실제 환경에서 인증 방식을 확인합니다.
- 실행 신원은 **본인의 Databricks 권한** 범위입니다. 문서 표현으로는 "it can only do what your Databricks permissions allow"입니다.

### 명령

| 명령 | 동작 |
|------|------|
| `genie` | 현재 디렉터리에서 새 대화를 시작합니다. |
| `genie --version` | 버전을 확인합니다. |
| `genie update` | CLI를 갱신합니다. |
| `genie resume` | 이전 대화를 목록에서 고릅니다. |
| `genie resume --last` | 가장 최근 대화를 이어 갑니다. |
| `genie mcp add <server-name> --url <server-url> --bearer-token-env-var <env-var-name>` | 원격 MCP 서버를 추가합니다. |
| `genie mcp add <server-name> -- <command> <args>` | 로컬 MCP 서버를 명령으로 실행해 추가합니다. |

세션 안에서 쓰는 슬래시 명령은 다음과 같습니다.

| 명령 | 동작 |
|------|------|
| `/resume` | 이전 대화를 고릅니다. |
| `/mcp` | MCP 연결 상태를 확인합니다. |
| `/import` | Claude Code 또는 Cursor의 설정을 가져옵니다. |

Databricks CLI 명령으로는 `databricks auth token --profile <profile-name>`과 `databricks genie ask`를 문서에서 언급합니다.

## 어떻게 쓰는가

### 1. 설치 확인

```bash
genie --version
```

프로필은 `genie`를 처음 실행할 때 고르거나 인증합니다. 프로필 준비는 Databricks CLI 문서를 따릅니다.

### 2. 대화 시작

```bash
cd ~/work/my-pipeline-repo
genie
```

현재 디렉터리의 파일을 읽고 편집합니다. 프로젝트 루트의 `AGENTS.md`가 인스트럭션으로 쓰입니다. 문서는 프로젝트 인스트럭션으로 `AGENTS.md`를 루트에 두라고 설명합니다.

### 3. 원격 MCP 서버 추가

```bash
export MY_MCP_TOKEN="<token>"
genie mcp add my-server --url https://<server-url>/mcp --bearer-token-env-var MY_MCP_TOKEN
```

문서가 제시하는 관리형 Databricks MCP 예시는 Genie One 서버입니다. 이름은 `system.ai.genie_one_mcp`입니다.

> **주의** 토큰을 명령 인자에 직접 쓰지 않습니다. 문서가 `--bearer-token-env-var`로 환경 변수 이름을 받는 방식을 씁니다. 셸 히스토리에 토큰이 남지 않도록 주의합니다.

### 4. 이전 대화 이어 가기

```bash
genie resume --last
```

### 5. 스킬 위치

| 위치 | 용도 |
|------|------|
| `~/.genie/skills/` | 사용자 스킬 |
| `~/.genie/skills/.system/` | 내장 스킬 |
| 저장소 안 `.agents/skills/` | 팀 스킬 |

문서는 CLI가 **로컬 폴더의 스킬만** 읽는다고 명시합니다. 워크스페이스나 Unity Catalog의 스킬은 읽지 않습니다. 스킬 형식은 [인스트럭션과 스킬](instructions-and-skills.md)을 참고하십시오.

## 워크스페이스 Genie Code와의 차이

| 항목 | 워크스페이스 Genie Code | Genie Code CLI |
|------|-------------------------|----------------|
| 실행 위치 | 브라우저의 노트북·SQL·대시보드 | 로컬 터미널 |
| 로컬 파일 | 워크스페이스 파일 | 로컬 저장소 파일 |
| 스킬 | 워크스페이스·사용자 경로 | 로컬 폴더만 |
| 공유 | 워크스페이스 인스트럭션과 스킬 | 워크스페이스와 스킬·도구를 공유하지 않음 |
| MCP | 워크스페이스 설정에서 추가 | `genie mcp add` 또는 `/mcp` |
| 사용량과 예산 | Genie 사용량과 Genie 예산 적용 | 문서상 Genie 사용량으로 집계되지 않고 Genie 예산의 영향을 받지 않음. 비용 통제는 Unity Gateway 예산으로 한다고 설명 (아래 주의 참고) |
| 대화 공유 | 채팅 공유 메뉴 | 문서에 명시 없음 |

## 트레이드오프

| 항목 | 내용 |
|------|------|
| 장점 | 로컬 저장소와 터미널 작업 흐름에 맞춰 쓸 수 있고, 워크스페이스 데이터를 Databricks CLI로 가져옵니다. |
| 제약 | Beta이며 명령이 바뀔 수 있습니다. 워크스페이스 스킬과 도구를 공유하지 않습니다. |
| 모델 | 모델 선택은 Databricks가 관리합니다. Beta 기간 문서는 "GPT 5.6"을 명시하며, 이 값은 바뀔 수 있다고 설명합니다. |
| 로컬 동작 | 파일 편집과 명령 실행은 **Databricks 거버넌스의 적용을 받지 않는다** 고 문서가 명시합니다. Databricks 권한은 데이터 접근만 제한합니다. |

## 주의사항

- **로컬 명령의 위험**: 문서에 따르면 로컬에서 파일을 고치고 명령을 실행하는 동작은 Databricks가 통제하지 않습니다. 민감한 저장소에서는 실행 권한이 있는 명령의 범위를 팀 정책으로 정합니다.
- **SSH 터널 세션은 지원되지 않습니다.** 문서는 "run it on your local machine"을 안내합니다.
- **MCP 토큰 만료**: 워크스페이스 MCP 토큰이 만료되면 호출이 `401` 오류로 실패합니다. 이때 CLI를 종료하고 새 토큰을 설정한 뒤 `genie`를 다시 실행합니다.
- **비용 해석에 주의**: 문서는 CLI 사용량이 Genie 사용량으로 집계되지 않으며 Genie 예산의 영향을 받지 않는다고 설명합니다. 한편 거버넌스 페이지의 예산 설정 항목은 Unity Gateway 리소스와 `databricks-product` 태그 `genie`를 기준으로 합니다. 두 설명이 완전히 일치하지 않으므로, 실제 비용은 `system.billing.usage`에서 확인합니다. 자세한 내용은 [거버넌스와 비용](governance-and-cost.md)을 참고하십시오.
- **상태 변화**: 명령과 옵션이 바뀔 수 있습니다. 버전이 바뀌면 `genie --version`과 문서를 함께 확인합니다.

## 참고 문서

- [Genie Code CLI](https://docs.databricks.com/aws/en/genie-code/genie-code-cli)
- [Agent skills](https://docs.databricks.com/aws/en/genie-code/skills)
- [Connect to MCP servers](https://docs.databricks.com/aws/en/genie-code/mcp)
- [Genie Code 릴리즈 노트 (2026년 10월)](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
