# 거버넌스와 비용

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 공식 문서에 근거한 관리자 설정, 과금 구조, 사용량 확인 방법, 데이터 처리 범위를 정리합니다. 문서에 없는 내용은 "문서에 명시 없음"으로 표기합니다.

## 왜 필요한가

Genie Code는 워크스페이스 사용자가 바로 쓸 수 있어 사용량과 데이터 처리 위치를 관리자가 먼저 파악해야 합니다. 관리자가 답해야 하는 질문은 대략 다음과 같습니다.

- 누가, 얼마나 쓰고 있는가?
- 비용이 예산을 넘지 않게 어떻게 막는가?
- 모델 호출과 데이터는 어느 지역에서 처리되는가?
- 외부 도구 연결과 자동 승인은 어떻게 통제하는가?

## 과금 구조

| 항목 | 문서 내용 |
|------|-----------|
| 과금 모델 | Genie Code는 **종량제(pay-as-you-go)** 입니다. 무료 할당량을 넘는 사용량은 LLM 사용량에 근거해 DBU로 청구됩니다. |
| 과금 시작 | 2026-07-08 00:00 UTC부터 무료 할당량을 넘는 사용량을 청구합니다. |
| 무료 할당량 | 식별된 사용자마다 매월 무료 할당량이 있습니다. |
| 서비스 프린시펄 | 무료 할당량이 없고, 모든 사용량이 청구됩니다. |
| 예산과 무료 할당량 | 예산 설정으로 사용자의 월 무료 사용량을 없앨 수 없습니다. |
| 컴퓨트 | SQL 웨어하우스 같은 컴퓨트는 별도로 청구되며 Genie 예산에 포함되지 않습니다. |

> **참고** 무료 할당량의 금액은 이 문서의 본문에 명시되어 있지 않습니다. 문서는 요금 페이지를 참고하도록 안내합니다. 2026-07-08 릴리즈 노트에는 Genie 제품의 월 무료 LLM 사용량 수치가 적혀 있으나, 이 장 작성 시점에 수치를 교차 확인하지 못했으므로 여기에 적지 않습니다. 실제 금액은 요금 페이지와 계정 콘솔에서 확인합니다.

Genie One과 Genie Agents의 무료 사용은 2027-01-31까지 연장되었다고 릴리즈 노트에 나옵니다. 문서상 Genie Code는 이 무료 프로모션에 포함되지 않습니다. 2026-08-03 릴리즈 노트가 이를 명시합니다.

## 예산 설정

Genie Code 사용량은 Genie 예산(Budgets)으로 제한할 수 있습니다.

### 설정 경로와 권한

- 계정 관리자만 예산을 만들고 관리할 수 있습니다.
- 계정 콘솔에서 **Usage** → **Budgets** 탭 → **Create budget**.
- 예산 역할은 사용자, 그룹, 서비스 프린시펄에 부여해 위임할 수 있습니다.

### 설정 값

| 항목 | 값 |
|------|----|
| 범위 (Scope) | 이름을 정하고 워크스페이스를 고르거나, **All**(계정 전체) |
| 리소스 유형 (Resource type) | **Unity Gateway** |
| 리소스 태그 (Resource tag) | 키 `databricks-product`, 값 `genie` |

> **주의** 태그는 `databricks-product=genie` 하나만 씁니다. 문서는 다른 태그를 함께 붙이면 추적되지 않는다고 경고합니다.

### 임계값 (Thresholds)

| 종류 | 설명 |
|------|------|
| Shared threshold | 범위 안 모든 사용자와 워크스페이스가 함께 쓰는 월간 풀 |
| Per-user threshold | 범위 안 각 사용자에게 적용되는 월간 한도 (무료 할당량 이후) |
| Per-user overrides | 특정 사용자나 그룹에 더 높은 한도를 줍니다. 공용 임계값은 바뀌지 않습니다. 여러 그룹에 속하면 가장 관대한 override가 적용됩니다. |

임계값에 도달했을 때 **Send alert**(알림)와 **Block usage**(차단)를 고를 수 있습니다. 문서는 공용 임계값에는 **Send alert** 만 쓰고, 차단은 사용자별 임계값과 override로 설정하는 것을 권장합니다. 알림은 입력한 이메일 주소로 가며, 수신자가 Databricks 사용자일 필요는 없습니다.

| 한도 | 값 |
|------|----|
| 예산 하나당 공용 임계값 | 최대 4개 |
| 예산 하나당 사용자별 override | 최대 100개 |
| 계정당 예산 | 최대 1,000개 |

### 정확도 한계

- 사용량 추적은 **거의 실시간 추정** 이므로, 차단과 알림은 대략적으로 동작합니다.
- 임계값에 도달하기 전에 차단되거나, 차단이 적용되기 전에 한도를 넘길 수 있습니다.
- 알림이 잠시 늦게 갈 수 있습니다.
- 문서는 "Do not use this feature as a way to ensure an absolute spend cap on final billed amounts."라고 경고합니다. 청구 금액의 상한선으로 쓰지 않습니다.
- 청구 가능한 사용량의 원천은 `system.billing.usage`이며, 몇 시간 간격으로 갱신됩니다.

## 사용량 확인

### 시스템 테이블: system.access.assistant_events

| 항목 | 내용 |
|------|------|
| 테이블 | `system.access.assistant_events` |
| 상태 | **Public Preview** |
| 설명 | 사용자가 Genie Code에 보낸 메시지를 추적합니다. |
| 주요 컬럼 | 이 페이지에는 나열되어 있지 않습니다. 별도의 Genie Code 이벤트 참조 페이지를 가리킵니다. 컬럼 목록은 그 페이지에서 확인합니다. |

### 이벤트 대시보드

문서는 Databricks가 **Genie Code 이벤트 대시보드** JSON 파일을 GitHub에 제공하며, 이를 내려받아 워크스페이스에 가져오기(import)할 수 있다고 설명합니다. 가져오기 절차는 문서의 대시보드 가져오기 안내를 따릅니다.

### 임팩트 지표

문서 "Measure Genie Code impact"는 채택, 참여, 만족도의 세 축으로 지표를 나눕니다.

| 축 | 시스템 테이블 기반 지표 | 설문 기반 지표 |
|----|--------------------------|----------------|
| 채택 (Adoption) | Top users overall, Submissions data (워크스페이스별·전체) | — |
| 참여 (Engagement) | Active users by day and month, Active users per workspace | Top job roles, Top tasks, 사용 빈도, 사용 영역 |
| 만족도 (User satisfaction) | — | 도움 만족도 (1–5 척도), 생산성 향상 (1–5 척도), 절감 시간 (비율 구간) |

활성 사용자(active user)는 하루 동안 제안을 받아 수락했거나 채팅에 참여한 고유 사용자로 정의됩니다. 문서는 설문 문항 예시도 제시합니다.

## 모델과 데이터 처리 범위

### 파트너 AI 기능 (Partner-powered AI features)

Genie Code의 에이전트 기능은 파트너 AI 기능 설정에 의존합니다.

| 항목 | 내용 |
|------|------|
| 계정에서 켜기 | 계정 콘솔 → **Settings** → **Feature enablement** 탭 → **Enable partner-powered AI features** 를 **On**. 워크스페이스가 바꾸지 못하게 **Enforce** 를 쓸 수 있습니다. 변경은 감사 로그의 계정 이벤트로 기록됩니다. |
| 워크스페이스에서 켜기 | 사용자 이름 → **Settings** → **Workspace admin** → **Advanced** 탭 → **Partner-powered AI features** |
| 기본값 | 컴플라이언스 보안 프로필(CSP)이 없는 워크스페이스는 기본 켜짐. CSP 워크스페이스는 기본 꺼짐. |
| 호스팅 제공자 (켠 경우) | Azure OpenAI service, OpenAI on Databricks, Anthropic on Databricks |
| Genie Code 자동완성 | 항상 Databricks 호스팅 모델을 씁니다. |

> **주의** 이 설정은 ** 제거 예정** 입니다. 2026-11-01까지 설정이 있는 워크스페이스에서는 토글이 비활성화되어 관리 화면에서 끌 수 없습니다. Settings API로는 바꿀 수 있습니다. 2026-11-01 이후에는 변경이 Databricks 계정 담당자에게 요청해야 합니다. 설정 제거 전후로 워크스페이스의 현재 값은 유지된다고 문서가 설명합니다.

설정을 끄면 다음이 영향을 받습니다.

| 기능 | 영향 |
|------|------|
| Genie Code 에이전트 기능 | 사용할 수 없습니다. |
| Genie Code 비에이전트 기능 | 비CSP 워크스페이스는 Databricks 호스팅 모델로 계속 쓸 수 있습니다. CSP는 컴플라이언스 기준에 따릅니다. |
| Genie Agents (Chat, Agent 모드), AI/BI 대시보드 AI 시각화, Genie App Builder, 합성 데이터 생성 | 사용할 수 없습니다. |
| Genie One | 채팅이 안 되지만, 사용자는 Genie One과 데이터 자산에 접근할 수 있습니다. |
| AI 생성 주석 | Azure OpenAI service 대신 Databricks 호스팅 모델로 바뀝니다. |
| LLM as judge | 사용할 모델을 사용자가 지정해야 합니다. |

### 지정 처리 지역 (Designated Services)

Genie Code는 Designated Service로 분류되어 있으며, 워크스페이스의 Geo 안에서 콘텐츠를 처리합니다.

| 기능 | 제공자 (문서 표기) | 지역 가용성 (문서 표기) |
|------|--------------------|--------------------------|
| Genie Code agentic capabilities | Azure AI Services, OpenAI on Databricks, Anthropic on Databricks | Americas, Asia, Australia & New Zealand, Europe, India. Mainland China와 Middle East & Africa는 별표 표기 |
| Genie Code chat and cell actions | Azure AI Services, OpenAI on Databricks | 같은 지역. 별표 표기 지역 있음 |

- 워크스페이스에서 **cross-Geo 처리** 를 켜면 다른 Geo에서도 처리될 수 있습니다.
- 별표가 붙은 기능은 cross-Geo 처리를 켜야 쓸 수 있다고 문서가 명시합니다.
- cross-Geo가 꺼진 상태에서 Genie Code chat과 cell actions의 처리 위치는 국가별로 다릅니다. 문서 예시: 브라질, 캐나다, 일본, 한국, 싱가포르, 영국은 자국 또는 해당 지역에서 처리됩니다. 홍콩은 싱가포르에서 처리됩니다. 인도네시아는 Asia Geo에서 처리됩니다.

> **참고** 위 표는 문서 원문을 요약한 것입니다. 한국 워크스페이스의 실제 처리 위치와 cross-Geo 설정이 필요한지는 계정 담당자와 최신 Designated Services 문서로 확인합니다.

### 컴플라이언스 보안 프로필 (CSP) 워크스페이스

CSP 워크스페이스에서 Databricks 호스팅 Genie Code 모델을 쓸 수 있는 범위는 문서에 다음과 같이 나옵니다.

| 컴플라이언스 기준 | 가용 지역 |
|-------------------|-----------|
| HIPAA | 지원되는 모든 지역 |
| FedRAMP Moderate | 미국 지역 |
| PCI-DSS, HITRUST | 미국, 호주·뉴질랜드 지역 |

다른 컴플라이언스 기준에는 Databricks 호스팅 Genie Code 모델이 없다고 문서가 설명합니다.

## 관리자 설정 체크리스트

| 점검 항목 | 확인 위치 | 근거 |
|-----------|-----------|------|
| 파트너 AI 기능 상태 | 계정 콘솔 Feature enablement, 워크스페이스 Advanced | 파트너 AI 페이지 |
| 예산 설정 | 계정 콘솔 Usage → Budgets | 예산 페이지 |
| 외부 MCP 서버 허용 목록 | 워크스페이스 관리자 설정 | MCP 페이지 |
| 자동 승인 사용 정책 | 사용자 설정 안내 및 팀 정책 | 기능 페이지 |
| 예약 작업 사용 여부 | Compliance 프로필 기본값 확인 | 2026-10-05 릴리즈 노트 |
| 사용량 대시보드 | 이벤트 대시보드 가져오기 | 임팩트 페이지 |

문서는 "Serverless usage policy"라는 설정 항목을 Genie Code 패널의 Settings 안에 있다고 언급하지만, 세부 동작은 설명하지 않습니다. 해당 설정의 의미는 문서에서 확인되지 않으므로 이 장에서는 설명하지 않습니다.

## 트레이드오프

| 설정 | 장점 | 비용 |
|------|------|------|
| 파트너 AI 기능 켜기 | 에이전트 기능과 다수의 Genie 기능을 씁니다. | 파트너 제공자 모델 사용과 지역 처리 조건을 함께 검토해야 합니다. |
| 파트너 AI 기능 끄기 | 파트너 제공자 의존을 줄입니다. | 에이전트와 여러 Genie 기능이 빠집니다. 설정은 2026-11-01 이후 계정 담당자에게 요청해야 바꿀 수 있습니다. |
| 예산 차단 (Block usage) | 사용자별 한도를 둘 수 있습니다. | 추적이 추정치라서 정확한 상한은 아닙니다. |
| 자동 승인 허용 | 반복 작업이 빠릅니다. | 보안 경계가 아닙니다. |

## 주의사항

- **예산은 청구 상한이 아닙니다.** 문서 경고를 그대로 따릅니다.
- **태그는 `databricks-product=genie` 하나만 씁니다.**
- **파트너 AI 설정 제거 일정(2026-11-01)을 확인합니다.** 설정 방식이 바뀌면 워크스페이스 운영 절차를 같이 바꿔야 합니다.
- **CLI 사용량은 별도 해석이 필요합니다.** [Genie Code CLI](cli.md)의 주의 항목을 참고하십시오.
- **상태 라벨**: 시스템 테이블 `system.access.assistant_events`는 Public Preview입니다. 그 밖의 기능은 상태가 페이지마다 다릅니다. 각 페이지의 상태 표기를 따릅니다.
- **클라우드 차이**: 이 장은 AWS 문서를 기준으로 합니다. Azure 문서는 Microsoft Learn에 있으며 이 장에서 확인하지 않았습니다.

## 참고 문서

- [Manage budgets and cost controls for Genie](https://docs.databricks.com/aws/en/genie/budgets)
- [Partner-powered AI features](https://docs.databricks.com/aws/en/databricks-ai/partner-powered)
- [Designated Services](https://docs.databricks.com/aws/en/resources/designated-services)
- [Measure Genie Code impact](https://docs.databricks.com/aws/en/genie-code/impact)
- [Genie Code 개요](https://docs.databricks.com/aws/en/genie-code/)
- [Genie Code 릴리즈 노트 (2026년 7월)](https://docs.databricks.com/aws/en/release-notes/product/2026/july)
- [Genie Code 릴리즈 노트 (2026년 8월)](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
