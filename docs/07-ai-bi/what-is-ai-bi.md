# AI/BI 개요와 제품 구분

> 기준일: 2026-10-29 · 근거: 공식 문서 · 수준: 100

## 한눈에 보기

Databricks AI/BI는 데이터 소비(분석과 질의응답)를 위한 제품군입니다. 공식 개념 문서는 AI/BI를 ETL 파이프라인, 계보, 다른 쿼리 등 플랫폼 전체의 데이터 수명 주기를 활용하는 **복합 AI 시스템**(compound AI system) 기반의 BI 제품으로 설명합니다. 같은 Unity Catalog(UC) 데이터 위에서 세 가지 소비 방식을 함께 제공합니다.

| 소비 방식 | 제품 이름(현재 docs 표기) | 적합한 질문 | 핵심 특징 |
|---|---|---|---|
| 정해진 시각화 | **AI/BI 대시보드**(AI/BI dashboards) | 매일 보는 KPI, 정해진 질문 | 로우코드 작성, 교차 필터, 이메일로 보내는 주기적 PDF 스냅샷 |
| 자연어 질의 | **Genie Agents** (구 Genie Spaces) | 열린 질문, 탐색적 분석 | 대화형 작업 공간. 질문마다 답을 만들고 시각화와 설명을 반환 |
| 통합 진입점 | **Genie One** | 현업 사용자의 일상 업무 | 대시보드 보기, 데이터 질문, Databricks Apps를 한곳에서 사용 |

공식 개념 문서에 따르면 AI/BI 대시보드는 정해진 소수의 비즈니스 질문을 운영하는 데 맞고, 시맨틱 모델(semantic model)이나 데이터 추출본(extract)을 따로 만들 필요가 없습니다. 개념 문서는 데이터를 외부 BI 엔진으로 추출하지 않는다는 점도 강조합니다.

## 1. 왜 필요한가

### 이전 방식의 한계

분석 소비 계층은 보통 세 가지 문제를 겪습니다.

- **정의의 분산**: 같은 지표(예: 매출)가 노트북, 대시보드, BI 도구마다 다른 SQL로 다시 계산되어 숫자가 엇갈립니다.
- **요청 병목**: 사용자가 새 질문을 할 때마다 데이터 팀이 쿼리나 대시보드를 새로 만들어야 합니다.
- **권한과 배포의 이원화**: BI 도구의 접근 제어가 데이터 플랫폼의 권한과 따로 놀아, 같은 테이블인데 보는 사람에 따라 결과가 달라지는 상황을 관리하기 어렵습니다.

AI/BI는 세 문제를 다음 방식으로 줄입니다.

- 지표 정의는 메트릭 뷰(Metric view)로 UC에 한 번 정의하고, 대시보드와 Genie Agent가 같은 정의를 씁니다. 정의와 거버넌스는 [메트릭 뷰의 거버넌스](../06-unity-catalog/metric-views-governance.md)에서 확인합니다.
- 자주 나오는 질문은 대시보드로 고정하고, 나머지 열린 질문은 Genie Agent에 맡깁니다.
- 접근 제어는 UC 권한을 기준으로 합니다. Genie Agent 문서 항목은 상호작용하려면 사용자에게 적절한 데이터·컴퓨트 권한이 있어야 한다고 설명합니다. 즉 결과는 질문자의 UC 권한에 따라 달라집니다.

### 플랫폼 통합에서 얻는 것

개념 문서는 AI/BI의 플랫폼 특징을 다음과 같이 설명합니다.

| 특징 | 문서 설명 |
|---|---|
| 통합 거버넌스와 계보 | UC에 통합되어 관리자 정책을 따르며, UC 계보 시각화로 자산 사용 추적 가능 |
| 사용자 라이선스 | 좌석 기반 제한이 없어 조직 구성원을 새 라이선스 없이 추가 가능 |
| 성능 | SQL 웨어하우스와 Photon 엔진에 최적화 |
| 데이터 추출 불필요 | 별도 BI 엔진으로 데이터를 추출하지 않아 최신성과 거버넌스가 단순해짐 |

## 2. 어떻게 동작하는가

### 제품 관계

| 구성 요소 | 역할 | 데이터 근거 |
|---|---|---|
| AI/BI 대시보드 | 데이터셋을 위젯으로 시각화해 여러 페이지로 구성 | 데이터셋(SQL, UC 테이블·뷰, 업로드 파일, 메트릭 뷰) |
| Genie Agents | 자연어 질문을 SQL로 바꾸고 결과를 표와 시각화로 반환 | UC 테이블 메타데이터, 인스트럭션, 예제 SQL, 지식 저장소 |
| Genie | Genie Agents를 구동하는 기술 | 위와 같음. 문서에서는 단독으로도 "Genie"라고 씁니다 |
| Genie One | 비즈니스 사용자용 소비 인터페이스 | 대시보드, Genie Agents, Databricks Apps |
| Ask Genie | 게시된 대시보드의 버튼. 열린 후속 질문을 위한 동반 Genie Agent를 엽니다 | 대시보드의 데이터셋과 시각화 |
| Genie Code | 개발자와 기술 사용자를 위한 AI 어시스턴트. 대시보드·Genie Agent 생성을 돕습니다 | [11장 Genie Code](../11-developer-tools/genie-code/README.md) |

공식 개념 문서는 다음 관계를 설명합니다.

- 대시보드를 게시하면 그 대시보드의 데이터셋과 시각화를 바탕으로 **동반 Genie Agent**(companion Genie Agent)가 자동으로 생성된다고 설명합니다.
- 게시된 대시보드의 **Ask Genie** 버튼을 누르면 동반 Genie Agent가 대시보드 옆에 열리고, 보고 있는 차트를 맥락으로 후속 질문을 할 수 있습니다.
- Genie One은 대시보드, Genie 기반 데이터 질문, Databricks Apps를 한 곳에 모읍니다.
- 이 모든 구성 요소를 UC가 거버넌스합니다.

> **주의** "동반 Genie Agent가 자동 생성된다"는 설명은 개념 문서의 서술입니다. 실제 생성 범위와 조건은 대상 워크스페이스에서 확인하십시오. 이 장에서는 개념 설명 수준으로만 씁니다.

### 제품 이름 변경

Genie Agents는 이전 명칭 **Genie Spaces** 에서 이름이 바뀌었습니다. Genie Agents 문서는 "formerly known as Genie Spaces"라고 명시합니다. 2026 AI/BI 릴리즈 노트는 Genie Agents(구 Genie Spaces)로의 이름 변경을 발표했습니다. 또한 릴리즈 노트는 Agent mode가 이전 명칭 "Research Agent"에서 바뀌었다고 설명합니다.

> **참고** 이전 자료나 API 응답에서 "Genie Space"라는 표현이 보일 수 있습니다. 새 자료를 쓸 때는 현재 docs 표기인 Genie Agents를 쓰고, 구 명칭은 처음 한 번만 괄호로 병기합니다.

## 3. 어떻게 쓰는가

### 어떤 제품을 고를지 정하기

| 질문 유형 | 권장 제품 | 이유 |
|---|---|---|
| 매일 같은 KPI를 같은 필터로 본다 | AI/BI 대시보드 | 정해진 시각화와 주기적 스냅샷이 적합 |
| 같은 데이터로 질문이 계속 바뀐다 | Genie Agents | 질문마다 답을 만들고 설명을 붙임 |
| 대시보드를 보다가 더 깊이 묻고 싶다 | 게시된 대시보드의 Ask Genie | 보고 있는 차트를 맥락으로 후속 질문 |
| 현업 사용자가 여러 자산을 한곳에서 쓴다 | Genie One | 대시보드·Genie·Apps 통합 진입점 |
| 개발자가 대시보드나 Genie 설정 자체를 만든다 | Genie Code 또는 코드형 관리 | 11장에서 다룹니다 |

### 접근 권한 기초 확인

AI/BI를 쓰는 사용자는 **엔타이틀먼트**(entitlement, 워크스페이스 수준 접근 유형)에 따라 할 수 있는 일이 다릅니다. 관리 가이드 기준의 구분은 다음과 같습니다.

| 사용자 유형 | 할 수 있는 일 | 근거 |
|---|---|---|
| Databricks SQL access 엔타이틀먼트 보유자 | 대시보드와 Genie Agent를 만들 수 있음. 대시보드·Genie Agent를 보고 편집하고 관리할 권한 부여 가능 | AI/BI 관리 가이드 |
| Consumer access 엔타이틀먼트 보유자 | 공유된 게시 대시보드, Genie Agent, Databricks Apps를 보고 대화. 접근 화면은 Genie One | Consumer access 문서 |
| 계정 사용자(Account user) | 공유 데이터 권한으로 게시된 대시보드를 봄. 워크스페이스 추가와 컴퓨트 접근은 필요 없음 | AI/BI 관리 가이드 |

Genie Agent와 상호작용하려면 사용자가 적절한 데이터 권한과 컴퓨트 권한을 가져야 하며, 이 권한은 워크스페이스 사용자에게만 부여할 수 있습니다. 계정 사용자는 공유된 게시 대시보드를 보는 용도로만 씁니다.

> **참고** Consumer access 엔타이틀먼트를 가진 사용자는 새 객체를 만들 수 없습니다. 문서는 "Users with only consumer access cannot create new objects in the workspace."라고 명시합니다. Consumer access 사용자는 SQL 웨어하우스와 Query History를 볼 수 없다는 제약도 문서에 있습니다.

## 4. 트레이드오프

### 대시보드와 Genie Agents의 선택

| 항목 | AI/BI 대시보드 | Genie Agents |
|---|---|---|
| 답의 형태 | 고정된 시각화와 페이지 | 질문마다 생성되는 SQL과 결과 표 |
| 반복성 | 높음(같은 화면을 매번 봄) | 낮음(질문마다 다름) |
| 준비 비용 | 데이터셋과 위젯을 설계 | 데이터 소스, 인스트럭션, 예제 SQL을 설계 |
| 결과 일관성 | 같은 쿼리이므로 결정적 | 생성형이므로 질문 표현에 따라 답이 달라질 수 있음 (일반 원칙) |
| 적합하지 않은 경우 | 열린 탐색, 임시 질문 | 정확한 정기 보고, 법적 효력이 있는 수치 |

Genie Agents의 답 일관성을 높이는 장치(인스트럭션, 신뢰 자산, 신뢰도 점검)는 [Genie Agents 신뢰도 높이기](genie-agents-quality.md)에서 다룹니다. 정기 보고처럼 같은 답이 반드시 필요한 값은 대시보드나 검증된 쿼리로 고정하는 편이 맞습니다.

### 대안과의 비교

- **외부 BI 도구**(Power BI, Tableau 등)와 병행할 수 있습니다. 연결 패턴은 [외부 BI 도구와 병행](external-bi-tools.md)에서 다룹니다.
- **노트북이나 SQL 에디터** 는 임시 분석에는 충분하지만, 게시·공유·예약을 위한 UI가 없습니다.

## 5. 주의사항

- **제품 이름을 혼용하지 않습니다.** Genie One은 소비 인터페이스이고, Genie Agents는 대화형 작업 공간입니다. 둘을 같은 것으로 설명하면 권한 설명이 틀어집니다.
- **라벨을 확인합니다.** AI/BI 개념 문서와 대시보드 문서, Genie 랜딩 페이지에는 GA, Public Preview, Beta 라벨이 붙어 있지 않습니다. 기능 단위 라벨은 릴리즈 노트와 각 기능 페이지에서 확인하십시오. 이 장의 각 페이지에 확인된 라벨만 적었습니다.
- **Genie Code와 혼동하지 않습니다.** Genie Code는 개발 작업을 돕는 제품이고, Genie One과 Genie Agents는 비즈니스 소비 제품입니다. 둘의 과금 구조도 다르므로 [Genie Code 거버넌스와 비용](../11-developer-tools/genie-code/governance-and-cost.md)을 따로 확인하십시오.
- **엔타이틀먼트를 먼저 정합니다.** 사용자가 새 객체를 만들어야 하는지 보기만 하면 되는지에 따라 엔타이틀먼트가 달라집니다. 보기만 하는 사용자에게 SQL access를 주면 불필요한 생성 권한이 생깁니다.
- **Genie One 체험 기간**: 2026-08 릴리즈 노트 기준으로 Genie One과 Genie Agents의 무료 사용 기간은 2027-01-31까지 연장되었습니다. 이 기간에는 예산 제어가 적용되지 않으며, 서비스 프린시펄의 사용량은 청구 대상입니다. 기간과 조건은 최신 릴리즈 노트에서 다시 확인하십시오.

## 참고 문서

- [AI/BI 개요 (Databricks AI/BI)](https://docs.databricks.com/aws/en/ai-bi/)
- [AI/BI 개념](https://docs.databricks.com/aws/en/ai-bi/concepts)
- [AI/BI 도구(BI tools)](https://docs.databricks.com/aws/en/ai-bi/tools)
- [Genie 개요](https://docs.databricks.com/aws/en/genie/)
- [Genie Agents](https://docs.databricks.com/aws/en/genie-agents/)
- [AI/BI 관리 가이드](https://docs.databricks.com/aws/en/ai-bi/admin/)
- [Consumer access](https://docs.databricks.com/aws/en/ai-bi/consumers/)
- [AI/BI 릴리즈 노트 (2026)](https://docs.databricks.com/aws/en/ai-bi/release-notes/2026)
