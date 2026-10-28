# 모드·기능과 데이터 접근 권한

> 기준일: 2026-10-28 · 근거: 공식 문서

## 왜 필요한가

데이터 작업은 노트북, SQL 에디터, 파이프라인, 대시보드, 카탈로그 탐색으로 흩어져 있습니다. 예전에는 각 화면의 AI 도움이 따로 놀았습니다. 노트북 자동완성은 테이블 구조를 모르고, SQL 도우미는 테이블 설명을 모르고, 대시보드 도구는 노트북의 코드를 모르는 식입니다.

Genie Code는 한 에이전트가 여러 화면을 가로지르며 **Unity Catalog 메타데이터**(테이블, 컬럼, 설명, 자주 쓰는 자산)와 ** 워크스페이스의 코드** 를 함께 참고하도록 설계되어 있습니다. 문서에 따르면 이 맥락이 응답 정확도를 높입니다.

## 어떻게 동작하는가

### 열기 방식

| 방식 | 조작 | 특징 |
|------|------|------|
| 채팅 패널 | 우상단 Genie Code(스파클) 아이콘 | 대부분의 페이지에서 열립니다. 현재 작업 옆에 붙어 있습니다. |
| 전체 화면 | 워크스페이스 홈의 프롬프트 박스에서 Genie Code 선택 후 제출, 또는 패널의 **Maximize** | 문서는 "starting work from scratch or running multiple tasks in parallel"에 권장한다고 설명합니다. |

전체 화면 모드의 사이드바에는 **Close chat bar**, **More options**, **New chat**, **Customization**(스킬·인스트럭션·MCP 서버), **Schedules**, **Search** 가 있습니다. 채팅은 전환해도 백그라운드에서 계속 실행됩니다. 채팅 항목의 케밥 메뉴에서 공유, 복사, 이름 변경, 삭제를 할 수 있습니다.

### 프롬프트 박스

| 조작 | 기능 |
|------|------|
| Enter 또는 전송 아이콘 | 전송. 줄바꿈은 Shift + Enter |
| + (플러스) | 파일 첨부, 컨텍스트 참조, 커넥션 추가 |
| @ | 테이블, 파이프라인, 노트북, 쿼리, 파일 등 리소스 참조 |
| / | 슬래시 명령 실행 (예: `/findTables`) |
| 노력 수준 선택기 | **Auto**(기본, 권장) 또는 **Low** |

### "모드"는 무엇으로 구분되는가

문서는 채팅 모드와 에이전트 모드를 별도 설정으로 나누지 않습니다. 대신 다음 세 축으로 동작이 갈립니다.

| 축 | 값 | 요구 사항·설명 |
|----|----|----------------|
| 에이전트 기능 | Genie Code agentic capabilities | 파트너 AI 기능(Partner-powered AI features)이 켜져 있어야 합니다. 꺼져 있으면 **agentic capabilities 없이**, Databricks 호스팅 모델로 동작한다고 문서에 나옵니다. |
| 승인 방식 | Ask first / Auto-approve | 아래 "승인" 절 참고 |
| 응답 방식 | 대화형 답변 | 문서 개요는 작업을 실행하지 않고 대화형 답변만 받을 수 있다고 설명합니다. 전환 방법은 문서에 자세히 나오지 않습니다. |

> **참고** 파트너 AI 설정이 꺼지면 에이전트 기능만 빠지는 것이 아닙니다. 문서 기준으로 Genie Agents의 Chat·Agent 모드, AI/BI 대시보드의 AI 시각화, Genie App Builder, 합성 데이터 생성도 사용할 수 없습니다. 자세한 내용은 [거버넌스와 비용](governance-and-cost.md)을 참고하십시오.

### 승인 (Approve tool actions)

Genie Code가 코드 실행, 노트북 편집, 테이블 질의 같은 **도구(tool)** 를 쓰려면 승인이 필요할 수 있습니다.

**요청별 프롬프트** 는 **Allow** 또는 **Skip** 버튼이 나오며, 다음 선택지가 있습니다.

| 선택지 | 의미 |
|--------|------|
| Ask every time | 도구를 쓸 때마다 묻습니다. |
| Allow in current chat | 현재 채팅 안에서 같은 도구를 다시 묻지 않습니다. |
| Always allow | 모든 채팅에서 같은 도구를 묻지 않습니다. |
| Auto-approve (Recommended) | 현재 채팅에서 도구 실행을 자동 승인합니다. AI 분류기가 요청 범위를 벗어난 동작을 막습니다. |

**기본 설정** 은 패널 헤더의 톱니바퀴 아이콘 → **Settings** → **Actions** 에서 바꿉니다. 옵션은 **Ask first** 와 **Auto-approve** 입니다. 문서는 처음 사용하는 사용자의 기본값이 **Auto-approve** 라고 설명합니다. 도구별 예외 설정은 그대로 적용됩니다.

**Auto-approve 동작 범위** 는 다음과 같이 문서에 정리되어 있습니다.

| 자동 승인되는 것 | 차단되는 것 |
|------------------|-------------|
| 내가 소유하거나 요청에서 참조한 리소스에 대한 읽기 전용 질의 | 요청 범위 밖의 동작 (예: 언급하지 않은 테이블 삭제) |
| 내 파일과 노트북 편집 | `DROP`에 `CASCADE` 추가 |
| 내가 명시적으로 요청한 파괴적 작업 | 공유 리소스 변경 |
| 내가 소유한 테이블 쓰기 | |

문서는 이 기능을 두고 **"Auto-approve is a productivity feature, not a security boundary."** 라고 명시합니다. 운영, 민감 데이터, 공유 리소스에서는 끄는 것이 권장된다고 합니다.

### 세션 간 메모리 (Remember context across sessions)

Genie Code는 세션을 넘어 지속될 가치가 있는 사실을 기억합니다. 문서는 기억 대상을 네 범주로 나눕니다.

| 범주 | 예시 성격 |
|------|-----------|
| How you like to work | 작업 방식 선호 |
| Who you are | 사용자 역할 정보 |
| Your data and workspace | 자주 쓰는 데이터와 워크스페이스 정보 |
| Project context | 프로젝트 맥락 |

- **저장 방식**: Genie Code가 작업 중 무엇을 저장할지 스스로 판단합니다. 별도 설정 화면이나 메모리 파일은 문서에 나오지 않습니다.
- **관리 방식**: 채팅으로 요청합니다. 무엇을 기억하는지 묻거나, 갱신·잊기·삭제를 요청할 수 있습니다. 저장과 회상은 채팅 안의 단계로 표시됩니다.
- **인스트럭션과의 차이**: 인스트럭션은 사용자가 직접 쓰고 모든 응답에 적용됩니다. 메모리는 작업 중 수집되고 관련이 있을 때 회상됩니다.
- **문서에 없는 것**: 저장 위치, 범위(사용자별인지 워크스페이스별인지), 용량 한도, 상태 라벨.

### 기능 목록

문서 "Features and capabilities" 페이지 기준입니다.

| 표면 | 기능 (문서 원문 명칭) | 설명 |
|------|-----------------------|------|
| 노트북 | Use Genie Code for data science | 다단계 데이터 과학 작업을 계획하고 자동화 |
| 노트북 | AI-based autocomplete, Diagnose Error, Quick Fix | 자동완성, 오류 진단, 수정안 제시 후 수락·실행 |
| 노트북 | Serverless code execution | 서버리스 실행 |
| Lakeflow Pipelines | Pipeline development in Lakeflow | ETL 워크로드와 Lakeflow 파이프라인 작성 |
| SQL | Genie Ontology (Public Preview), Explore sample data | 지표 정의와 조인 힌트 등 비즈니스 맥락 검색, 샘플 데이터 탐색용 SQL 생성 |
| 문서 처리 | Document processing | 비정형 문서를 파싱·분류·추출하는 파이프라인 구축과 점검 (릴리즈 노트 2026-09-25). `ai_parse_document`, `ai_classify`, 인용(citation)과 신뢰도 점수(confidence score)를 포함한 `ai_extract`로 Lakeflow job을 만들고, 라벨 테이블 기준 필드별 평가(Measure), 수정안 제시(Improve), 재평가(Re-evaluate) 루프를 자동화합니다. 수정안은 승인 후 적용되는 diff로 제시됩니다 (블로그 2026-10-27) |
| AI/BI 대시보드 | Data analysis in dashboards | 대시보드 계획·생성과 데이터 분석 |
| AI/BI 대시보드 | Bulk import from Power BI and Tableau | Power BI 또는 Tableau 파일을 한 번에 최대 100개까지 AI/BI 대시보드와 메트릭 뷰(metric view)로 가져오기 (릴리즈 노트 2026-10-22) |
| MLflow | Observability and evaluation in MLflow | AI 애플리케이션 관찰·평가·개선 |
| Lakeflow Jobs | Improved Lakeflow Performance Observability | 지원되는 태스크의 Job 수준 쿼리 성능 지표·인사이트에서 **Optimize** 버튼으로 Genie Code를 열어 쿼리 개선을 돕습니다. 쿼리 프로파일링은 서버리스 컴퓨트, SQL Warehouses, Lakeflow Pipelines를 지원합니다. compliance security profile 워크스페이스에는 2026-11-25 이후 기본 제공 예정 (What's coming) |
| 전체 공통 | Chat with Genie Code, Inline suggestions, Quick fix, Diagnose error, /slash commands, Command shortcuts, Filter data | 기본 대화와 편집 보조 |
| 전체 공통 | Schedule tasks with Genie Code | 예약 작업 ([상세](scheduled-tasks.md)) |
| 전체 공통 | Branch and edit chats | 채팅 분기와 수정 (릴리즈 노트 2026-09-09 "conversation controls") |
| 전체 공통 | Search the web | 웹 검색, Beta (릴리즈 노트 2026-08-06) |
| 전체 공통 | 파일 첨부 | 현재 채팅의 컨텍스트로 첨부. 첨부 파일은 기본적으로 워크스페이스 파일 시스템에 저장되지 않는다고 문서에 나옵니다. |

## 어떻게 쓰는가

### 컨텍스트 붙이기

질문 품질은 컨텍스트에 좌우됩니다. 문서의 "Improve Genie Code responses"에서 권장하는 방식입니다.

```text
@sales_orders 테이블에서 지역별 월간 매출을 집계하는 SQL을 작성해 줘.
결과는 region, month, revenue 세 컬럼으로 해줘.
```

- `@<resource-name>`으로 테이블, 파이프라인, 노트북을 참조합니다. 같은 채팅에서는 선택한 컨텍스트가 유지됩니다.
- 노트북 셀만 가리키려면 **Add context** → **Cells**, 또는 `@cell`을 씁니다.
- 테이블 구조를 모를 때는 `SELECT * FROM <table_name>` 같은 쿼리를 먼저 주면 컬럼명을 정확히 읽습니다.
- 테이블과 컬럼에 설명을 달아 두면 Genie Code가 스키마를 이해하는 데 쓰입니다. 예를 들어 키를 `6-2` 형식으로 저장한다면 그 예시를 컬럼 주석에 적어 둘 수 있습니다.

### 승인 설정 바꾸기

```text
패널 헤더 톱니바퀴 → Settings → Actions → Ask first
```

운영 워크스페이스에서는 위 설정을 `Ask first`로 두고, 도구 실행 결과를 하나씩 확인하는 흐름을 권장합니다. 문서가 이 설정을 기본 권장값으로 제시하지는 않으므로, 팀 정책에 맞춰 정하면 됩니다.

## 트레이드오프

| 항목 | 장점 | 제약 |
|------|------|------|
| 여러 화면을 가로지르는 맥락 | 노트북·SQL·대시보드 작업을 한 채팅에서 이어 갑니다. | 화면마다 노출되는 기능이 다릅니다. 문서가 화면별 기능을 모두 명시하지 않습니다. |
| Auto-approve 기본값 | 반복 작업이 빠릅니다. | 보안 경계가 아닙니다. 운영 리소스에서는 위험합니다. |
| 메모리 | 반복 설명을 줄입니다. | 저장 위치와 범위가 문서에 없어 민감 정보 기억 여부를 통제하기 어렵습니다. |
| 파트너 AI 의존 | 에이전트 기능과 다수 Genie 기능을 씁니다. | 설정을 끄면 여러 기능이 함께 사라집니다. |

> **주의** 접근 권한은 Unity Catalog 권한을 따릅니다. 문서 개요는 "Access follows your Unity Catalog permissions."라고 명시합니다. 다만 Genie Code가 호출자의 권한을 어떤 방식으로 상속하는지는 이 페이지에 자세히 나오지 않습니다. 권한 설계는 Unity Catalog 권한을 기준으로 하고, 예약 작업과 Job 태스크의 실행 주체는 각 페이지를 함께 확인하십시오.

## 주의사항

- **Auto-approve를 운영에서 켜 두지 않습니다.** 문서도 운영, 민감, 공유 리소스에서 끄기를 권장합니다.
- **파트너 AI 설정을 확인합니다.** 에이전트 기능이 꺼져 있으면 기대한 동작이 나오지 않습니다. 설정 경로는 [거버넌스와 비용](governance-and-cost.md)을 참고하십시오.
- **상태 라벨을 구분합니다.** 기능 페이지 대부분에는 GA·Beta 라벨이 없습니다. Genie Ontology만 Public Preview로 명시되어 있습니다.
- **기능 노출 범위는 실제 화면에서 확인합니다.** SQL 에디터와 파이프라인 에디터에서 쓸 수 있는 기능 목록이 문서 페이지마다 다르게 서술됩니다.

## 참고 문서

- [Navigate Genie Code](https://docs.databricks.com/aws/en/genie-code/navigate-genie-code)
- [Features and capabilities](https://docs.databricks.com/aws/en/genie-code/features-capabilities)
- [Remember context across sessions](https://docs.databricks.com/aws/en/genie-code/memory)
- [Improve Genie Code responses](https://docs.databricks.com/aws/en/genie-code/tips)
- [Genie Code 개요](https://docs.databricks.com/aws/en/genie-code/)
- [AI/BI 릴리즈 노트 (2026) — Dashboard enhancements](https://docs.databricks.com/aws/en/ai-bi/release-notes/2026#dashboard-enhancements)
- [From spot fixes to measured gains: improving document extraction accuracy with ai_extract and MLflow Prompt Registry](https://www.databricks.com/blog/spot-fixes-measured-gains-improving-document-extraction-accuracy-aiextract-and-mlflow-prompt)
- [What's coming — Improved Lakeflow Performance Observability](https://docs.databricks.com/aws/en/release-notes/whats-coming#improved-lakeflow-performance-observability-will-soon-be-available-by-default-for-workspaces-with-the-compliance-security-profile-enabled)
