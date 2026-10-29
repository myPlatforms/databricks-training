# 09. AI 에이전트

> 기준일: 2026-10-28 · 근거: 공식 문서

AI 에이전트(AI Agent)는 언어 모델이 도구를 골라 호출하고, 그 결과를 보고 다음 행동을 정하는 반복 루프를 가진 애플리케이션입니다. Databricks는 에이전트를 만들고, 데이터에 접근하게 하고, 배포하고, 평가하고, 감시하는 도구를 한 플랫폼 안에 모아 두고 있습니다. 이 장은 데이터 엔지니어, ML 엔지니어, 애플리케이션 개발자를 대상으로, 에이전트 개념과 Databricks의 에이전트 제품 지도, 직접 개발하는 방법, 도구·검색·평가·배포·가드레일을 공식 문서 원문 기준으로 정리합니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- 에이전트가 필요한 경우와 단순 모델 호출·RAG 파이프라인으로 충분한 경우를 구분합니다.
- Databricks 에이전트 제품 지도에서 Agent Bricks, Genie Agents, Knowledge Assistant, Supervisor Agent의 현재 위치(현재 제품 또는 레거시)를 구분합니다.
- Agent Bricks CLI(`agentbricks`)로 에이전트 프로젝트를 만들고, 로컬에서 실행하고, 배포하는 흐름을 따라 할 수 있습니다.
- UC 함수, 관리형 MCP 서버, 외부 MCP 서버, 커스텀 MCP 서버를 도구로 붙이는 방식과 인증 주체의 차이를 설명합니다.
- AI Search(구 Vector Search) 인덱스의 유형과 소스 테이블 조건을 확인하고 인덱스를 만듭니다.
- MLflow 트레이싱, 스코어러 기반 평가, 사람 피드백, 프로덕션 모니터링을 구분해 설계합니다.
- 에이전트 배포 방식(Agent Runtime, Model Serving 레거시)과 인증 모델(앱 서비스 프린시펄, 사용자 권한 위임)을 비교합니다.
- 서비스 정책(가드레일), 속도 제한, 사용량 추적의 역할을 나눠 거버넌스를 설계합니다.

## 페이지 안내

| 순서 | 페이지 | 다루는 내용 |
|---|---|---|
| 1 | [AI 에이전트란 무엇인가](what-is-ai-agent.md) | 에이전트의 동작 원리, 단순 호출·RAG·에이전트의 선택 기준, Databricks 에이전트 구성 요소 |
| 2 | [Databricks 에이전트 제품 지도](agent-product-map.md) | Agent Bricks, Genie Agents, 레거시 에이전트 제품, 각 제품의 상태 라벨 |
| 3 | [Agent Bricks CLI로 에이전트 개발하기](build-agent-with-cli.md) | 퀵스타트, 프로젝트 구조, `agent.toml`, 로컬 실행·배포, 세션과 메모리 |
| 4 | [도구: UC 함수와 MCP 서버](tools-uc-functions-and-mcp.md) | 관리형·외부·커스텀 MCP 서버, UC 함수 도구, 도구별 인증 주체 |
| 5 | [AI Search와 검색 기반 에이전트](ai-search-and-retrieval.md) | 인덱스 유형, 소스 테이블 조건, 인덱스 생성·쿼리, 검색 모드 |
| 6 | [트레이싱·평가·피드백](tracing-evaluation-feedback.md) | MLflow 트레이싱, 내장 스코어러, 리뷰 앱과 리뷰 큐, 프로덕션 모니터링 |
| 7 | [배포와 인증](deploy-and-authentication.md) | Agent Runtime, Model Serving 레거시, Databricks Apps 사용자 권한, 호출 인증 |
| 8 | [가드레일·거버넌스·모니터링](guardrails-governance-monitoring.md) | 서비스 정책(Beta), 속도 제한, 사용량 추적, 추론 테이블, 운영 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 2장의 제품 지도에서 상태 라벨을 먼저 확인하면, 3장 이후의 설정 예시가 어떤 제품에 해당하는지 헷갈리지 않습니다.

## 선수 지식

- **Python 기초**: 예제 코드는 Python과 TOML·YAML 설정 파일을 사용합니다.
- **Unity Catalog 기초**: 함수·테이블·볼륨의 3단계 이름(`catalog.schema.name`)과 `USE CATALOG`, `EXECUTE` 같은 권한 모델을 알고 있어야 합니다. 자세한 내용은 [06장 Unity Catalog 거버넌스](../06-unity-catalog/what-is-unity-catalog.md)에서 다룹니다.
- **SQL과 AI 함수**: `ai_query` 같은 AI 함수는 [05장 AI Functions](../05-data-warehousing/ai-functions.md)에서 다룹니다.
- **Databricks CLI 인증**: `databricks auth login`으로 프로필을 만들 수 있어야 합니다.
- **LLM 기초**: 토큰, 프롬프트, 도구 호출(Tool calling)의 개념을 알고 있으면 충분합니다.

Model Serving 엔드포인트의 기본 사용법은 [08장 Model Serving 커스텀 모델](../08-machine-learning/model-serving.md)에서, 모델 접근 API는 [08장 Foundation Model APIs](../08-machine-learning/foundation-model-apis.md)에서, AI 게이트웨이 설정은 [08장 Unity Gateway](../08-machine-learning/unity-gateway.md)에서 다룹니다. 에이전트의 상태 저장소(세션·메모리)는 Lakebase 위에 놓이므로, 필요하면 [10장 Lakebase 개요](../10-lakebase/what-is-lakebase.md)를 먼저 읽으십시오. 코딩 에이전트(Genie Code)는 [11장 Genie Code](../11-developer-tools/genie-code/README.md)에서 다룹니다. 이 장은 사용자가 만드는 에이전트를 다룹니다.

## 이 장의 읽는 법

각 기능 페이지는 왜 필요한지, 어떻게 동작하는지, 어떻게 쓰는지, 트레이드오프, 주의사항 순서로 씁니다. 기능마다 상태 라벨(GA, Beta, Public Preview, Legacy)을 원문 표기대로 적었습니다. 라벨이 원문에 없으면 "문서에 명시 없음"이라고 적었습니다.

> **참고** 에이전트 문서는 최근 몇 달 사이 경로와 제품명이 여러 번 바뀌었습니다. 예를 들어 `generative-ai/` 아래 허브와 `agent-framework/`, `vector-search/`, `mlflow3/genai/` 허브 경로는 2026-10-28 기준 404를 반환했고, 같은 내용은 `agents/`, `ai-search/`, `mlflow3/genai/` 하위 개별 페이지로 옮겨져 있습니다. 실제 적용 전에 각 페이지의 참고 문서 링크에서 최신 원문을 다시 확인하십시오.

> **참고** 이 장은 AWS 문서(`docs.databricks.com/aws/en/`)를 기준으로 합니다. Azure 문서에서 제품 가용성이나 상태가 다를 수 있으므로, 고객 환경에 적용하기 전에 해당 클라우드 문서를 확인하십시오.

## 참고 문서

- [Develop agents on Databricks](https://docs.databricks.com/aws/en/agents/)
- [What is Agent Bricks?](https://docs.databricks.com/aws/en/agents/concepts/)
- [Agent Bricks quickstart](https://docs.databricks.com/aws/en/agents/quickstart)
- [Legacy agent offerings](https://docs.databricks.com/aws/en/agents/legacy/)
