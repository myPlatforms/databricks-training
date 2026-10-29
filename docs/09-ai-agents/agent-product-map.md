# Databricks 에이전트 제품 지도

> 기준일: 2026-10-28 · 근거: 공식 문서

## 왜 필요한가

에이전트 관련 제품은 이름이 자주 바뀌고, 같은 기능이 여러 이름으로 불렸습니다. 예전 자료를 보고 Knowledge Assistant나 Supervisor Agent로 새 에이전트를 만들면 공식 문서가 권장하지 않는 방식을 택하게 됩니다. 반대로 최신 기능을 모르면 제품이 이미 해주는 일을 코드로 다시 구현하게 됩니다.

이 페이지는 공식 문서의 현재 표기, 상태 라벨, 안내 문장을 기준으로 제품을 나눕니다. 제품마다 **무엇인지, 언제 쓰는지, 상태가 어떤지, 대체 경로가 있는지** 를 정리합니다.

## 어떻게 동작하는가

Databricks 공식 문서는 에이전트 제품을 두 방향으로 나눕니다.

- **코드로 만드는 에이전트**: Agent Bricks CLI로 프로젝트를 만들고 Python 코드로 로직을 씁니다. 공식 FAQ는 이 방식을 "developers who build custom agents in code"를 위한 것이라고 설명합니다. "from a single agent to many agents that serve production traffic"까지 포함합니다.
- **저코드로 만드는 에이전트**: Genie Agents가 해당합니다. FAQ는 "Genie Agents is a low-code way to build agents that answer questions over your tables and documents."라고 정의합니다. 데이터 분석가가 Unity Catalog 데이터셋, 예시 SQL, 지침을 설정합니다.

Agent Bricks FAQ는 두 방식 사이의 선택 기준을 한 줄로 정리합니다. "For new low-code agents, use Genie Agents. For agents written in code, use the Agent Bricks CLI." 레거시 제품인 Knowledge Assistant와 Supervisor Agent도 같은 두 대체 경로를 안내합니다.

## 한눈에 보기

| 제품 또는 기능 | 문서 표기 | 상태 라벨 | 한 줄 용도 |
|---|---|---|---|
| Agent Bricks CLI | `agentbricks`, 패키지 `databricks-agentbricks` | Beta | 코드 에이전트의 생성, 로컬 실행, 배포 |
| Genie Agents | Genie Agents (구 Genie Spaces) | 제품 라벨 없음 (기능별 라벨 있음) | 저코드 데이터·문서 질의 에이전트 |
| AI Search | AI Search (구 Vector Search) | 제품 라벨 없음 (전체 텍스트 인덱스 Beta) | 검색 컨텍스트 제공 |
| MCP 서비스 | MCPs (관리형·외부·커스텀) | 항목별로 다름 | 에이전트에 도구 연결 |
| Unity Gateway | Unity Gateway | 페이지 라벨 없음 (아래 상충 항목 참고) | 모델·도구·스킬의 단일 제어 지점 |
| Databricks Apps 배포 | Databricks Apps, Agent Runtime | 라벨 없음 | 에이전트와 MCP 서버의 실행 환경 |
| Knowledge Assistant | Knowledge Assistant | Legacy | 레거시. Genie Agents로 대체 |
| Supervisor Agent | Supervisor Agent | Legacy | 레거시. 저코드는 Genie Agents, 코드는 Agent Bricks CLI |

> **참고** "제품 라벨 없음"은 해당 페이지에서 상태 라벨을 찾지 못했다는 뜻입니다. 정식(GA) 제품이라는 뜻이 아닙니다. 적용 전에 해당 페이지에서 라벨을 다시 확인하십시오.

## 제품별 상세

### 1. Agent Bricks CLI

| 항목 | 내용 |
|---|---|
| 무엇 | 에이전트 프로젝트를 만들고(`agentbricks init`), 로컬에서 실행하고(`agentbricks dev`), 배포하는(`agentbricks deploy`) CLI |
| 언제 | 코드로 에이전트 로직을 직접 쓰고, 프로덕션 트래픽을 받는 에이전트를 운영할 때 |
| 상태 | Beta (퀵스타트와 CLI 페이지 모두 표기). 퀵스타트는 "No workspace setting is required to enable it."라고 명시 |
| 대체 경로 | 기존 LangGraph 또는 OpenAI Agents SDK 코드는 `agentbricks init --existing`으로 이전. 레거시 에이전트 서버는 CLI 프로젝트로 옮기도록 안내 |
| 제약 | 배포된 에이전트의 서버 종류는 바꿀 수 없음. 바꾸려면 새 프로젝트를 새 이름으로 배포 |

프레임워크 옵션은 `langgraph`와 `openai` 두 가지입니다. 서버 옵션은 `agentbricks`(DurableAgentServer)와 `custom` 두 가지이며, `agent.toml`의 `server` 값으로 정합니다. 문서는 서버 종류를 바꾸려면 `agentbricks init --server`로 새 프로젝트를 만들라고 안내합니다. `--existing` 이전에는 `custom` 서버를 쓸 수 없습니다. 자세한 명령은 [Agent Bricks CLI로 에이전트 개발하기](build-agent-with-cli.md)에 있습니다.

### 2. Genie Agents (구 Genie Spaces)

| 항목 | 내용 |
|---|---|
| 무엇 | 데이터셋(UC 테이블, 뷰, 메트릭 뷰, 구체화 뷰), 지식 저장소, 지침, 예시 SQL, SQL 함수, 신뢰 자산, 벤치마크로 구성되는 도메인 채팅 에이전트 |
| 언제 | 정형 데이터에 대해 한 번의 SQL로 답할 수 있는 질문. 복잡한 탐색형 질문은 Agent 모드. 파일과 외부 도구는 Agent 모드 필요 |
| 상태 | 제품 라벨 없음. 기능별로 Inspect는 Public Preview, Flash는 Beta, 볼륨 접근은 Beta, Agent 모드는 리전 가용성이 다름 |
| 대체 경로 | Knowledge Assistant의 대체(문서 권장). 코드가 필요하면 Agent Bricks CLI |
| 제약 | Chat 모드는 정형 데이터만 다룸. 사용자가 권한이 없는 데이터를 물으면 빈 응답. 생성 쿼리는 항상 읽기 전용 |

Genie Agents 문서는 모드별 차이를 명확히 나눕니다. Chat 모드는 단일 쿼리 답변으로 제한됩니다. Agent 모드는 "breaks complex questions into sub-tasks"하고 발견 사항과 시각화가 담긴 보고서를 돌려줍니다. Flash는 속도를 우선하고 응답이 더 간결합니다. 문서는 대화 중간에 모드를 바꿀 수 없으므로 새 대화를 시작해야 한다고 명시합니다.

Genie Agents는 에이전트의 도구로도 쓸 수 있습니다. 레거시 페이지는 `agentbricks tools add genie-agent` 명령으로 추가할 수 있다고 안내합니다. 워크스페이스 MCP 엔드포인트 경로도 있습니다. 이 경로는 Public Preview이며 Managed MCP Servers 설정이 필요합니다.

### 3. AI Search (구 Vector Search)

| 항목 | 내용 |
|---|---|
| 무엇 | 벡터와 키워드를 함께 다룰 수 있는 검색 인덱스. 페이지 제목은 "Databricks AI Search", formerly Databricks Vector Search |
| 언제 | 사내 문서나 텍스트처럼 정해진 행 형태가 아닌 콘텐츠를 검색해 에이전트 컨텍스트에 넣을 때 |
| 상태 | 제품 라벨 없음. 전체 텍스트 검색 인덱스(full-text index)와 `FULL_TEXT` 질의는 Beta. 워크스페이스 MCP 엔드포인트는 Public Preview |
| 대체 경로 | 인덱스 유형 선택으로 대응. 임베딩을 직접 관리하면 Direct Vector Access 유형 |
| 제약 | 자체 임베딩 인덱스를 관리형으로 바꾸려면 새 인덱스가 필요 |

인덱스 유형, 소스 조건, 생성과 질의 코드는 [AI Search와 검색 기반 에이전트](ai-search-and-retrieval.md)에 있습니다.

### 4. MCP 서비스

MCP(Model Context Protocol) 서버는 에이전트가 도구를 호출하는 표준 통로입니다. 공식 MCP 페이지는 세 유형을 구분합니다.

| 유형 | 문서 설명 | 상태 |
|---|---|---|
| 관리형 (Databricks-provided MCPs) | "Use Genie One, Databricks SQL, GitHub, Slack, and other tools without hosting a server." | 항목별로 다름. Genie One MCP는 generally available. `system.ai.dbsql`, `system.ai.web_search`, `system.ai.sandbox`는 Unity Gateway Beta |
| 외부 (External MCP servers) | "Add a self-hosted or third-party server through the MCPs UI, then share it with your team." | 페이지에 라벨 없음 |
| 커스텀 (Custom MCP servers) | "Build custom tools or turn an HTTP REST API into MCP tools with Databricks Apps templates." | 페이지에 라벨 없음 |

관리형 목록에는 **레거시** 로 표시된 항목이 있습니다. 워크스페이스 MCP 엔드포인트의 Databricks SQL 서버(`/api/2.0/mcp/sql`)는 "Databricks SQL (legacy)"로 적혀 있습니다. 같은 목록에서 새 방식은 Unity Gateway 경로의 `system.ai.dbsql`입니다. 기존에 워크스페이스 엔드포인트를 쓰던 에이전트는 이 차이를 확인해야 합니다.

MCP 서비스의 인증, 등록 절차, 커스텀 서버 배포는 [도구: UC 함수와 MCP 서버](tools-uc-functions-and-mcp.md)에 있습니다.

### 5. Unity Gateway

공식 페이지의 정의입니다. "Unity Gateway is a single control plane for model inference, tools, and skills across your AI applications and coding agents." 목적은 비용 관리, 일관된 보안 적용, 팀의 AI 접근 제공입니다.

| 기능 영역 | 문서가 나열하는 내용 |
|---|---|
| 모델 접근 | Databricks가 호스팅하는 모델, 또는 자체 용량을 가져오는 방식. 문서가 드는 제공자는 OpenAI, Anthropic, Amazon Bedrock, Azure Foundry |
| 비용과 성능 | 최적 모델로 요청 라우팅, 사용량과 지출 추적, 예산과 지출 상한 설정 |
| 안전한 접근 | 모델, 에이전트, MCP 서버, 도구에 대한 신원 기반 정책과 권한, PII 마스킹, AI 활동 감사 로그 |

상태는 이 페이지에 라벨이 없습니다. 같은 문서군의 거버넌스 페이지는 Unity Gateway를 generally available로, 서비스 정책은 Beta로 적고 있습니다. 서비스 정책과 가드레일은 [가드레일·거버넌스·모니터링](guardrails-governance-monitoring.md)에서 다룹니다.

> **주의** Unity Gateway 페이지는 MCP 거버넌스, 가드레일, 속도 제한을 별도 기능으로 적지 않습니다. 이 기능들은 거버넌스 페이지에서 확인해야 합니다. 두 페이지의 범위가 다르므로 한 페이지만 보고 기능 범위를 판단하지 마십시오.

### 6. Databricks Apps와 에이전트 배포

Databricks Apps의 정의는 다음과 같습니다. "Databricks Apps enables developers to build and deploy secure data and AI applications directly on the Databricks platform." 문서가 드는 사례는 인터랙티브 대시보드, RAG 채팅 앱, 데이터 입력 폼, 사용자 정의 운영 인터페이스입니다. Apps 페이지 자체는 에이전트나 MCP 서버를 배포 대상으로 언급하지 않습니다.

에이전트 배포는 두 페이지가 다르게 설명합니다.

| 항목 | 내용 |
|---|---|
| 새 에이전트 배포 | Agent Runtime. 배포마다 `agent-bricks-<name>`이라는 앱이 생기고 고유 URL을 가짐 |
| 실행 위치 설명 | 배포 페이지는 Agent Runtime이 "runs your agent on Databricks Apps"라고 설명. Agent Runtime 페이지는 "runs your agent on Databricks-hosted serverless compute"라고 설명 |
| 상태 | 두 페이지 모두 Agent Runtime의 상태 라벨 없음 |
| 레거시 배포 | Model Serving (legacy). 기존 에이전트는 Databricks Apps 이전 가이드 참고 |

MCP 서버는 Databricks Apps 템플릿으로 만듭니다. 이때 Apps는 MCP 서버의 실행 환경입니다. 실행 위치 설명이 엇갈리는 항목은 아래 상충 항목에서 다시 다룹니다. 배포 권한과 인증 모델은 [배포와 인증](deploy-and-authentication.md)에 있습니다.

### 7. 레거시 제품: Knowledge Assistant와 Supervisor Agent

문서의 레거시 안내 문장을 그대로 옮깁니다.

| 제품 | 문서 원문 | 대체 경로 | 날짜 |
|---|---|---|---|
| Knowledge Assistant | "This is a legacy offering. For new low-code agents over your documents and data, use Genie Agents." / "For new agents written in code, use the Agent Bricks CLI." | 저코드는 Genie Agents, 코드는 Agent Bricks CLI | 퇴역일 없음. 페이지 갱신일 2026-10-14 |
| Supervisor Agent | "Supervisor Agent is a legacy offering and is not recommended for new systems." | 저코드는 Genie Agents, 다중 에이전트 조율을 코드로 하려면 Agent Bricks CLI | 퇴역일 없음. 페이지 갱신일 2026-10-14 |
| Supervisor API | "(deprecated)" 표기 | 직접 에이전트 루프를 작성해 Agent Bricks CLI로 배포 | 명시 없음 |
| 레거시 에이전트 서버 | 문서에 "legacy" 표기 | Agent Bricks CLI, DurableAgentServer | 명시 없음 |
| Model Serving 커스텀 에이전트 | 레거시 | Agent Bricks CLI, 기존 에이전트는 마이그레이션 가이드 | 명시 없음 |

레거시 허브 페이지는 두 제품을 포함한 전체 원칙을 적습니다. "Legacy agent offerings are earlier Databricks agent products that are no longer best practice for building agents." 그리고 "Don't use them for new agents."

> **참고** 문서는 두 제품에 대해 퇴역일을 명시하지 않습니다. 신규 고객에게 생성이 막혔는지도 적지 않습니다. Supervisor 페이지는 "not recommended for new systems"라고 하면서 설정, 권한, 엔드포인트 사용 방법을 여전히 문서화하고 있습니다. 기존 시스템을 운영 중이라면 마이그레이션 계획을 공식 문서와 Databricks 담당자에게 확인하십시오.

## 레거시와 현재 제품의 구분

| 질문 | 현재 권장 | 레거시 또는 사용 중단 |
|---|---|---|
| 코드로 새 에이전트를 만들려면 | Agent Bricks CLI | 레거시 에이전트 서버, Model Serving 커스텀 에이전트 |
| 저코드로 데이터 질의 에이전트를 만들려면 | Genie Agents | Knowledge Assistant |
| 여러 에이전트를 조율하려면 | 직접 작성한 루프를 Agent Bricks CLI로 배포 | Supervisor Agent, Supervisor API |
| 에이전트 배포 대상은 | Agent Runtime | Model Serving (legacy) |
| 대화 상태와 장기 기억은 | 에이전트 세션과 에이전트 메모리 | Managed agent memory (legacy) |
| 모델 접근과 도구 거버넌스는 | Unity Gateway | 문서에 명시 없음 |

## 상충 항목과 확인이 필요한 점

| 항목 | 상충 또는 공백 | 이 장의 처리 |
|---|---|---|
| Agent Runtime 실행 위치 | 배포 페이지는 Apps 위에서 실행한다고 설명. Agent Runtime 페이지는 서버리스 컴퓨트에서 실행한다고 설명 | 두 설명을 모두 적고 원문 확인을 요청 |
| Unity Gateway 상태 | Unity Gateway 페이지는 라벨 없음. 거버넌스 페이지는 generally available | 거버넌스 페이지 표기를 인용 |
| 레거시 신규 생성 가능 여부 | 레거시 페이지는 "Don't use them for new agents"만 적음 | 생성 가능 여부는 "문서에 명시 없음"으로 처리 |
| Agent Bricks 제품 라벨 | 퀵스타트와 CLI는 Beta, 우산 개념 페이지는 라벨 없음 | CLI와 퀵스타트 기준 Beta 표기 |

## 트레이드오프

| 선택 | 장점 | 제약 |
|---|---|---|
| Agent Bricks CLI로 코드 작성 | 로직, 도구, 세션, 메모리를 세밀하게 제어 | 개발 역량이 필요하고, CLI 상태가 Beta |
| Genie Agents | 데이터 분석가가 설정으로 구현 | 에이전트 로직 제어 제한. Chat 모드는 정형 데이터만 |
| 레거시 제품 유지 | 기존 구현 재사용 | 문서가 새 에이전트 사용을 권장하지 않음. 이전 부담 |

## 어떻게 쓰는가

제품을 고르는 순서는 다음과 같습니다.

1. 개발자가 직접 코드를 쓰는지 확인합니다. 아니라면 Genie Agents를 먼저 검토합니다.
2. 코드를 쓴다면 Agent Bricks CLI 프로젝트를 기준으로 설계합니다. 자세한 절차는 [Agent Bricks CLI로 에이전트 개발하기](build-agent-with-cli.md)에 있습니다.
3. 검색이 필요하면 AI Search 인덱스를 도구로 붙입니다. [AI Search와 검색 기반 에이전트](ai-search-and-retrieval.md)를 참고하십시오.
4. 외부 시스템 연결은 MCP 서비스로 합니다. [도구: UC 함수와 MCP 서버](tools-uc-functions-and-mcp.md)를 참고하십시오.
5. 모델과 도구 접근은 Unity Gateway에서 정책으로 관리합니다. 모델 엔드포인트 자체의 사용법은 [08장 Model Serving 커스텀 모델](../08-machine-learning/model-serving.md)과 [08장 Foundation Model APIs](../08-machine-learning/foundation-model-apis.md)에서 다룹니다.
6. 배포 방식과 인증 주체를 정합니다. [배포와 인증](deploy-and-authentication.md)을 참고하십시오.

## 주의사항

> **주의** Agent Bricks CLI 퀵스타트와 CLI 문서는 Beta로 표기되어 있습니다. 운영 환경에 올리기 전에 지원 조건을 확인하십시오.

- 제품 이름을 강의 자료에 옮기기 전에 해당 제품 페이지의 현재 제목을 확인하십시오. 예를 들어 Vector Search 문서는 현재 AI Search 제목을 씁니다.
- 레거시 제품 설명을 인용할 때는 날짜를 함께 적으십시오. 레거시 페이지는 2026-10-14 갱신본입니다.
- Genie 이름은 세 가지가 섞여 나옵니다. Genie Agents(구 Genie Spaces), Genie One(비즈니스 사용자용 통합 채팅), Genie Code(개발자용). 이름을 혼동하지 마십시오. Genie Code는 [11장 Genie Code](../11-developer-tools/genie-code/README.md)에서 다룹니다.

## 참고 문서

- [What is Agent Bricks?](https://docs.databricks.com/aws/en/agents/concepts/)
- [Agent Bricks FAQ](https://docs.databricks.com/aws/en/agents/concepts/faq)
- [Develop agents on Databricks](https://docs.databricks.com/aws/en/agents/)
- [Agent Bricks quickstart](https://docs.databricks.com/aws/en/agents/quickstart)
- [Agent Bricks CLI](https://docs.databricks.com/aws/en/agents/custom-agents/agent-bricks-cli)
- [Legacy agent offerings](https://docs.databricks.com/aws/en/agents/legacy/)
- [Knowledge Assistant (legacy)](https://docs.databricks.com/aws/en/agents/agent-bricks/knowledge-assistant)
- [Supervisor Agent (legacy)](https://docs.databricks.com/aws/en/agents/agent-bricks/multi-agent-supervisor)
- [Genie Agents](https://docs.databricks.com/aws/en/genie-agents/)
- [Genie Agents concepts](https://docs.databricks.com/aws/en/genie-agents/concepts)
- [AI Search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- [MCPs](https://docs.databricks.com/aws/en/agents/mcp-tools/)
- [Unity Gateway](https://docs.databricks.com/aws/en/unity-gateway/)
- [Databricks Apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [Deploy agents on Databricks](https://docs.databricks.com/aws/en/agents/deploy/)
- [Agent Runtime](https://docs.databricks.com/aws/en/agents/deploy/agent-runtime)
