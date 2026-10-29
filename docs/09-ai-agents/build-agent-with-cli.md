# Agent Bricks CLI로 에이전트 개발하기

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 왜 필요한가

에이전트를 직접 만들 때 개발 팀은 보통 같은 작업을 반복합니다. 웹 서버를 세우고, 채팅 UI를 붙이고, 대화 상태를 저장하고, 트레이싱을 켜고, 배포 설정을 맞춥니다. 이 준비 작업이 에이전트 로직보다 오래 걸리는 경우가 많습니다.

Agent Bricks CLI(`agentbricks`)는 이 준비 작업을 프로젝트 템플릿으로 묶습니다. 프로젝트를 만들면 에이전트 코드, 선언형 설정 파일(`agent.toml`), 채팅 앱, 트레이싱 연결이 함께 생깁니다. 로컬 실행과 배포도 같은 CLI에서 합니다.

> **참고** 이 CLI는 공식 문서에서 Beta로 표기되어 있습니다. 퀵스타트 페이지는 "This feature is in Beta. No workspace setting is required to enable it."라고 명시합니다.

## 어떻게 동작하는가

프로젝트 흐름은 다음 순서입니다.

| 단계 | 명령 | 하는 일 |
|---|---|---|
| 설치 | `pip install databricks-agentbricks` | CLI 설치 |
| 인증 | `databricks auth login`, `agentbricks login` | 워크스페이스 OAuth 프로필 저장 |
| 생성 | `agentbricks init` | 프레임워크 템플릿으로 프로젝트 생성 |
| 저장소 연결 | `agentbricks sessions bind`, `agentbricks memory bind` | 세션·메모리 저장소 연결 (선택) |
| 실행 | `agentbricks dev` | 로컬에서 포트 8000으로 실행, 채팅 UI 포함 |
| 배포 | `agentbricks deploy` | Agent Runtime에 배포 |
| 운영 | `agentbricks deployments logs`, `agentbricks deployments stop` | 배포 로그 확인, 중지 |

프로젝트의 주요 파일은 다음과 같습니다.

| 파일 | 역할 |
|---|---|
| `agent/agent.py` | 에이전트 로직. 모델 값(`MODEL`)을 포함 |
| `agent.toml` | 관리되는 리소스의 선언형 기준 파일 (서버, 저장소, 도구, 트레이싱) |
| `.agentbricks/project.toml` | 템플릿 출처 정보 |
| `.env` | 선택 사항. 프로필을 시드로 담음 |

서버 옵션은 두 가지입니다. `agentbricks`는 `DurableAgentServer`를 씁니다. `custom`은 직접 만든 서버입니다. 문서는 `DurableAgentServer`를 새 에이전트의 기본으로 두고, 커스텀 엔드포인트나 프로토콜이 필요할 때만 `custom`을 쓰라고 안내합니다.

## 어떻게 쓰는가

### 1. 퀵스타트

공식 퀵스타트의 명령을 그대로 옮긴 절차입니다. 워크스페이스 URL과 프로필 이름만 바꿉니다.

```bash
pip install databricks-agentbricks

databricks auth login --host https://<your-workspace-url> --profile <profile>
agentbricks login --profile <profile>

agentbricks init --framework langgraph my-agent
cd my-agent

agentbricks dev
```

`agentbricks dev`는 로컬에서 포트 8000으로 에이전트를 띄웁니다. 배포는 다음 명령으로 합니다.

```bash
agentbricks deploy my-agent
```

`databricks auth login`과 `agentbricks login`은 두 개의 명령입니다. 한 줄로 이어 쓰지 않도록 주의하십시오. 퀵스타트 문서도 두 명령을 따로 실행하라고 안내합니다.

### 2. 프레임워크 선택

`agentbricks init --framework`에 쓸 수 있는 값은 문서에 다음 두 가지로 적혀 있습니다.

| 값 | 프레임워크 | 특징 |
|---|---|---|
| `langgraph` | LangGraph | 브라우저 채팅 앱 포함 |
| `openai` | OpenAI Agents SDK | 문서에 별도 설명 없음 |

API만 필요하면 `agentbricks init`에 `--disable-chat-app` 옵션을 붙입니다.

### 3. 세션과 메모리 저장소

`init`은 기본 저장소를 선언하므로 세션과 메모리 연결은 선택 사항입니다. 이름을 직접 지정하려면 다음처럼 바인드합니다.

```bash
agentbricks sessions bind my-agent-sessions
agentbricks memory bind my-agent-memory
```

세션은 한 번의 상호작용 상태(대화 기록, 도구 호출 결과)를 담고, 메모리는 여러 대화에 걸친 사실이나 결정을 담습니다. 두 저장소는 독립적이므로 세션을 지워도 메모리는 남습니다. 두 저장소 모두 Lakebase 위에 있다고 문서가 설명합니다. 자세한 내용은 [에이전트 메모리와 세션](https://docs.databricks.com/aws/en/agents/custom-agents/stateful-agents) 문서를 참고하십시오.

### 4. 트레이싱 연결

```bash
agentbricks tracing list
agentbricks tracing bind --experiment-id <experiment-id>
agentbricks tracing unbind
```

트레이스를 어느 MLflow 실험에 남길지를 이 명령으로 정합니다. 실험 기반 트레이싱의 개념과 평가는 [트레이싱·평가·피드백](tracing-evaluation-feedback.md)에서 다룹니다.

### 5. 도구 추가

도구는 `agentbricks tools` 명령으로 추가하고 제거합니다. 자세한 도구 종류와 인증은 [도구: UC 함수와 MCP 서버](tools-uc-functions-and-mcp.md)에서 다룹니다.

```bash
agentbricks tools list --kind mcp
agentbricks tools add mcp system.ai.web_search
agentbricks tools list
agentbricks tools remove mcp <service>
```

도구는 기본으로 **요청한 사용자의 권한** 으로 실행됩니다. 앱 서비스 프린시펄로 실행하려면 `--auth app`을 붙입니다.

```bash
agentbricks tools add mcp system.ai.web_search --auth app
```

`agent.toml`에서는 같은 설정을 다음처럼 씁니다.

```toml
[[tools]]
id = "web_search"
auth = "user"
source = { kind = "mcp", service = "system.ai.web_search" }
```

`auth`는 `user` 또는 `app`입니다. Unity Catalog 함수 도구는 `auth = "app"`만 지원한다고 문서에 명시되어 있습니다.

### 6. 기존 에이전트 이전

이미 LangGraph 또는 OpenAI Agents SDK로 만든 코드가 있다면 `--existing` 옵션으로 가져올 수 있습니다.

```bash
agentbricks init --framework langgraph --existing .
agentbricks doctor .
agentbricks dev
agentbricks deploy <agent-name>
```

`--existing`은 `--server custom`과 함께 쓸 수 없습니다. 마이그레이션 과정에서 `agent-bricks-migrate/` 폴더와 `.claude/skills/`, `.agent/skills/` 폴더가 추가된다고 문서가 설명합니다.

### 7. 배포 후 확인

```bash
agentbricks deployments logs
agentbricks deployments stop
```

배포 상태와 로그는 `agentbricks deployments` 하위 명령(`list`, `get`, `wait`, `logs`, `start`, `stop`, `delete`)으로 봅니다.

## 함수 도구 작성 예시

프레임워크별로 로컬 함수를 도구로 등록하는 방식은 다음과 같습니다. 아래 코드는 레거시 에이전트 서버 작성 페이지의 예시이므로, 새 프로젝트에서는 `agent/agent.py`의 실제 구조에 맞춰 옮겨 쓰십시오. 로컬 함수 도구는 `databricks.yml`에 별도 리소스 권한을 줄 필요가 없다고 문서가 설명합니다. 외부 데이터나 API가 필요하면 MCP 서버를 연결하고 권한을 줍니다.

OpenAI Agents SDK:

```python
from agents import Agent, function_tool

@function_tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().isoformat()

agent = Agent(
    name="My agent",
    instructions="You are a helpful assistant.",
    model="databricks-claude-sonnet-4-5",
    tools=[get_current_time],
)
```

LangGraph:

```python
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from databricks_langchain import ChatDatabricks

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().isoformat()

agent = create_react_agent(
    ChatDatabricks(endpoint="databricks-claude-sonnet-4-5"),
    tools=[get_current_time],
)
```

## 트레이드오프

| 방식 | 장점 | 제약 |
|---|---|---|
| Agent Bricks CLI 프로젝트 | 서버·채팅 UI·트레이싱·배포를 한 번에 설정 | 제품 상태 Beta, 서버 종류는 생성 시 고정 |
| 직접 서버 구현 (`custom`) | 엔드포인트와 프로토콜을 자유롭게 설계 | 채팅 UI, 세션 연결, 배포 설정을 직접 맞춰야 함 |
| 레거시 에이전트 서버 | 기존 코드를 그대로 유지 | 문서가 새 에이전트에 권장하지 않음 |

문서는 배포된 에이전트의 서버 종류를 바꿀 수 없다고 명시합니다. 서버를 바꾸려면 새 프로젝트를 `agentbricks init --server`로 만들고 새 이름으로 배포해야 합니다.

## 주의사항

- **Python 버전**: 패키지는 Python 3.10에서도 설치되지만, 생성된 프로젝트는 Python 3.11 이상이 필요합니다. 문서는 Python 3.12를 권장합니다.
- **`uv` 필요**: `init`, `dev`, `deploy`는 프로젝트 실행에 `uv`를 씁니다. 설치 실패 시 문서가 안내하는 명령은 `pip install --only-binary :all: databricks-agentbricks`와 `uv tool install --python 3.12 databricks-agentbricks`입니다.
- **배포 권한**: `agentbricks deploy`를 실행하는 사용자는 앱, 저장소, MLflow 실험을 만들거나 관리할 권한이 있어야 합니다. 문서는 `--auth app` 도구에 한해 앱 서비스 프린시펄에 접근을 부여한다고 설명합니다.
- **로컬 실행의 메모리 상태**: 로컬 채팅 앱은 메모리가 "Not connected"로 표시될 수 있습니다. 배포 전에 원격 저장소 연결을 확인하십시오.
- **템플릿 모델 값**: 모델 값은 `agent/agent.py`에 있습니다. 엔드포인트 이름을 바꿀 때 이 파일과 `agent.toml`을 함께 확인하십시오.

## 참고 문서

- [Agent Bricks quickstart](https://docs.databricks.com/aws/en/agents/quickstart)
- [Agent Bricks CLI](https://docs.databricks.com/aws/en/agents/custom-agents/agent-bricks-cli)
- [Develop agents on Databricks](https://docs.databricks.com/aws/en/agents/)
- [Agent memory and sessions](https://docs.databricks.com/aws/en/agents/custom-agents/stateful-agents)
- [Author a custom agent (레거시 에이전트 서버)](https://docs.databricks.com/aws/en/agents/custom-agents/author-agent)
- [Deploy agents on Databricks](https://docs.databricks.com/aws/en/agents/deploy/)
