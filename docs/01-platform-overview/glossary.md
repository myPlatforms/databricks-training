# 용어 정리

> 기준일: 2026-10-29 · 근거: 공식 문서

이 페이지는 01장과 이후 장에서 반복해 나오는 용어를 한곳에 모은 표입니다. 각 정의는 Databricks 공식 문서(docs.databricks.com/aws/en/)의 원문 정의를 한국어로 옮기고, 필요한 곳에만 짧은 설명을 덧붙였습니다. 처음 나오는 용어는 영문을 함께 적었습니다. 한국어 표현이 원문과 다르게 읽힌다면 참고 문서 링크의 원문을 우선하십시오.

## 이 페이지를 쓰는 방법

| 상황 | 볼 곳 |
|---|---|
| 처음 보는 용어의 뜻을 빠르게 확인 | 1~6절의 표 |
| 문서·화면에서 본 이름이 현재 이름인지 확인 | 7절 (구 명칭 대응) |
| 같은 용어가 문서마다 다르게 표기되는지 확인 | 7절의 표기 주의 |

## 1. 플랫폼과 구조

| 용어 | 정의 (공식 문서 기준) | 자세히 |
|---|---|---|
| Databricks | 엔터프라이즈급 데이터, 분석, AI 솔루션을 대규모로 구축·배포·공유·유지하기 위한 통합된 오픈 분석 플랫폼 | [플랫폼이란 무엇인가](what-is-databricks.md) |
| Data + AI Platform | 소개 페이지의 표기. 클라우드 계정의 스토리지·보안과 통합되어 동작하는 Databricks 플랫폼 | [플랫폼이란 무엇인가](what-is-databricks.md) |
| 레이크하우스(data lakehouse) | 엔터프라이즈 데이터 웨어하우스와 데이터 레이크를 결합해 데이터 솔루션을 가속·단순화·통합하는 구조 | [플랫폼이란 무엇인가](what-is-databricks.md) |
| 계정(account) | 여러 워크스페이스를 포함할 수 있는 단일 엔티티 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 워크스페이스(workspace) | 팀이 Databricks 자산에 접근하는 환경 역할을 하는, 클라우드의 Databricks 배포. 워크스페이스 문서는 이를 모든 Databricks 객체와 기능에 접근하는 중심 허브라고 설명 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 제어 영역(control plane) | Databricks가 Databricks 계정 안에서 관리하는 백엔드 서비스 | [플랫폼 아키텍처](architecture.md) |
| 서버리스 컴퓨트 영역(serverless compute plane) | Databricks 컴퓨트 리소스가 Databricks 계정 안의 컴퓨트 계층에서 실행되는 영역 | [플랫폼 아키텍처](architecture.md) |
| 클래식 컴퓨트 영역(classic compute plane) | Databricks 컴퓨트 리소스가 고객의 AWS 계정에서 실행되는 영역 | [플랫폼 아키텍처](architecture.md) |
| 워크스페이스 스토리지(workspace storage) | 워크스페이스 파일 시스템 데이터와 워크스페이스 시스템 데이터, 두 범주의 데이터를 담는 저장소. Unity Catalog 객체와는 별개 | [플랫폼 아키텍처](architecture.md) |
| DBFS 루트(DBFS root) | 사용자가 접근할 수 있는 파일 시스템. 공식 문서는 deprecated 패턴이며 Databricks가 권장하지 않는다고 설명하고, 데이터 접근 관리에는 Unity Catalog를 권장 | [플랫폼 아키텍처](architecture.md) |

> **참고** 제어 영역의 공식 정의는 "Databricks가 관리하는 백엔드 서비스"까지입니다. 웹 애플리케이션이 제어 영역에서 동작한다는 설명은 아키텍처 페이지에서 확인하십시오.

## 2. 거버넌스와 데이터 구조

| 용어 | 정의 (공식 문서 기준) | 자세히 |
|---|---|---|
| Unity Catalog | 데이터와 AI 자산을 위한 통합 거버넌스 솔루션(Concepts). Unity Catalog 소개 페이지는 Databricks에 내장된, 데이터와 AI를 위한 통합 거버넌스 계층이라고 설명 | 06장에서 다룹니다 |
| 보안 객체(securable object) | Unity Catalog에서 거버넌스 대상이 되는 모든 자산은 보안 객체로 모델링됨 | 06장에서 다룹니다 |
| 메타스토어(metastore) | 데이터, AI, 권한에 관한 메타데이터를 카탈로그·스키마·테이블 단위로 등록하는 계정 수준 메타스토어 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 카탈로그(catalog) | Databricks에서 데이터를 구성하고 격리하는 가장 높은 수준의 컨테이너 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 스키마(schema) | 데이터베이스라고도 부름. 카탈로그 안에 포함되며 더 세분화된 조직 수준을 제공 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 테이블(table) | 정형 데이터에 대한 접근을 조직하고 거버넌스하는 객체. `catalog.schema.table` 3단계 이름으로 참조 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 뷰(view) | 하나 이상의 테이블·뷰에서 파생된 읽기 전용 객체 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 볼륨(volume) | 클라우드 객체 스토리지 위치에 있는 논리적 스토리지 볼륨. 파일을 Unity Catalog 아래에서 관리 | 02장에서 다룹니다 |
| 관리형 테이블·볼륨 | Unity Catalog가 거버넌스와 기반 파일 스토리지의 수명 주기를 모두 처리하는 테이블과 볼륨 | 02장에서 다룹니다 |
| 기본 스토리지(default storage) | 내부 워크스페이스 시스템 데이터를 위한 완전 관리형 스토리지 위치. 서버리스 워크스페이스에서 쓰이고, 고객 클라우드 스토리지를 연결할 수도 있음 | [플랫폼 아키텍처](architecture.md) |
| Delta Lake / Delta 테이블 | 클라우드 객체 스토리지 위에서 고성능 ACID 테이블 저장을 제공하는 프레임워크 | 02장에서 다룹니다 |

> **주의** "메타스토어"의 원문은 "account-level metastore"입니다. 워크스페이스마다 따로 있는 것이 아니라 계정 수준 구성 요소로 이해하십시오.

## 3. 컴퓨트

| 용어 | 정의 (공식 문서 기준) | 자세히 |
|---|---|---|
| 클러스터(cluster) | 노트북과 잡을 실행하는 컴퓨팅 리소스와 구성의 집합 | [플랫폼 아키텍처](architecture.md) |
| 서버리스 컴퓨트(serverless compute) | 컴퓨트 리소스가 Databricks 계정 안에서 실행되는 컴퓨트. 프로비저닝과 런타임 관리는 Databricks가 맡음 | [플랫폼 아키텍처](architecture.md) |
| 클래식 컴퓨트(classic compute) | 컴퓨트 리소스가 고객 클라우드 계정에서 실행되는 컴퓨트 | [플랫폼 아키텍처](architecture.md) |
| SQL 웨어하우스(SQL warehouse) | SQL 쿼리를 실행하는 컴퓨팅 리소스. 소개 페이지는 관리자가 확장 가능한 컴퓨트 클러스터를 SQL 웨어하우스로 구성한다고 설명 | 03장에서 다룹니다 |
| Databricks Runtime (DBR) | Databricks가 관리하는 클러스터에서 실행되는 핵심 구성 요소의 집합 | 03장에서 다룹니다 |

## 4. 노트북과 개발

| 용어 | 정의 (공식 문서 기준) | 자세히 |
|---|---|---|
| 노트북(notebook) | 데이터 사이언스·머신러닝 워크플로를 만드는 웹 기반 인터페이스. SQL 외에 Python, R, Scala 지원 | [노트북 기초](notebooks-basics.md) |
| 셀(cell) | 노트북에서 실행하는 단위 | [노트북 기초](notebooks-basics.md) |
| 매직 명령(magic command) | `%`로 시작해 셀 언어를 바꾸거나 기능을 호출하는 명령 (`%sql`, `%run`, `%pip` 등) | [노트북 기초](notebooks-basics.md) |
| `%run` | 다른 노트북을 현재 노트북 안에서 실행하고 함수와 변수를 불러오는 명령 | [노트북 기초](notebooks-basics.md) |
| 위젯(widget) | 노트북에 입력란을 붙이는 기능. 문자열 값만 받음 | [노트북 기초](notebooks-basics.md) |
| 잡(Jobs) | Databricks 노트북, SQL 쿼리, 기타 임의의 코드를 스케줄링 | 04장에서 다룹니다 |
| Lakeflow pipelines | 데이터셋 간 의존성을 지능적으로 관리해 ETL을 더 단순하게 만드는 파이프라인. Concepts 페이지는 신뢰할 수 있고 유지보수·테스트가 쉬운 데이터 처리 파이프라인을 만드는 선언형 프레임워크라고 설명 | 04장에서 다룹니다 |
| Auto Loader | 클라우드 객체 스토리지의 데이터를 증분적이고 멱등하게 로드하는 효율적이고 확장 가능한 도구 | 04장에서 다룹니다 |
| Git 폴더(Git folders) | Databricks 프로젝트를 여러 Git 제공자와 동기화하는 폴더 | 11장에서 다룹니다 |
| 번들(bundle) | 소개 페이지의 표기는 Declarative Automation Bundles. Databricks 리소스를 정의·배포·실행하게 해 줌 | 11장에서 다룹니다 |
| 메트릭 뷰(metric views) | 비즈니스 KPI를 한 번 정의해 두고 재사용하는 객체 | 06장에서 다룹니다 |

## 5. 과금

| 용어 | 정의 (공식 문서 기준) | 자세히 |
|---|---|---|
| DBU (Databricks unit) | VM 인스턴스 유형에 따른 시간당 처리 능력의 단위 | [과금 모델 기초](billing-basics.md) |
| SKU | 청구 품목 이름(`sku_name`). 일부 제품은 서로 다른 SKU로 청구될 수 있음 | [과금 모델 기초](billing-basics.md) |
| `system.billing.usage` | 사용량 레코드를 담는 시스템 테이블. `usage_unit`(사용량 측정 단위)과 `usage_quantity`(레코드별 소비 단위 수) 등의 열을 가짐 | [과금 모델 기초](billing-basics.md) |
| 종량제(pay-as-you-go) | 사용한 만큼 청구되는 방식. 무료 체험 종료 후 전환되는 방식으로도 나옴 | [시작하기](getting-started.md) |

## 6. 시작 방법과 AI 도구

| 용어 | 정의 (공식 문서 기준) | 자세히 |
|---|---|---|
| 무료 체험판(free trial) | 업무용으로 Databricks를 평가하는 조직과 전문가를 위한 체험. 시작 후 14일간 유효한 무료 사용 크레딧(최대 $400)이 제공되고, 이후 결제 방법은 신용카드, Marketplace 연결, 약정 계약 중 하나 | [시작하기](getting-started.md) |
| Free Edition | 학생, 교육자, 취미 사용자를 위한 무료 버전. 일일 사용 한도가 있는 상시 무료. 서버리스 워크스페이스 1개, 클래식 컴퓨트 접근 불가, 컴퓨트 크기·사용량 제한, 일부 기능 잠김 | [시작하기](getting-started.md) |
| Genie | 조직의 모든 사용자에게 자연어로 데이터 질문을 하는 단일 공간을 제공하는 Databricks의 AI 경험 | [워크스페이스 UI](workspace-ui.md) |
| Genie One | 비즈니스 사용자가 데이터 자산을 탐색하고 상호작용하도록 한 단순화된 인터페이스 | [워크스페이스 UI](workspace-ui.md) |
| Genie Agents | 데이터 팀이 신뢰할 수 있는 데이터, 지표, 비즈니스 규칙을 구성하는 도메인 특화 환경 | [워크스페이스 UI](workspace-ui.md) |
| Genie Code | 워크스페이스 안에서 개발자와 기술 실무자를 위한 AI 코딩·데이터 도우미 | [개발자 도구](../11-developer-tools/README.md) |
| Lakebase | 완전 관리형 Postgres 기반의 온라인 트랜잭션 처리(OLTP) 데이터베이스 | [Lakebase](../10-lakebase/README.md) |
| AI Functions | SQL 분석가가 LLM에 접근할 때 쓰는 Databricks 제공 함수 | 05장에서 다룹니다 |
| OpenSharing | Databricks의 보안 데이터 공유 플랫폼. Unity Catalog는 관리형 OpenSharing을 제공 | 06장에서 다룹니다 |
| Data profiling | 테이블의 요약 통계를 시간에 따라 계산해 제공하는 기능 | 08장에서 다룹니다 |

> **참고** Genie 계열 명칭은 서로 다른 대상을 가리킵니다. 사용자 경험 전체(Genie), 업무 사용자용 인터페이스(Genie One), 도메인 환경(Genie Agents), 코딩 도우미(Genie Code)를 섞어 쓰지 마십시오.

## 7. 명칭 주의

### 7.1 원문에 구 명칭이 명시된 항목

| 현재 표기 | 구 명칭 | 근거 |
|---|---|---|
| Git folder (Git 폴더) | Repos | Concepts 페이지의 "Git folder (formerly Repos)" |
| Databricks AI Search | Databricks Vector Search | AI Search 페이지의 "Databricks AI Search (formerly Databricks Vector Search)" |
| Declarative Automation Bundles | Databricks Asset Bundles | 번들 릴리즈 노트의 "(formerly known as Databricks Asset Bundles)", 2026-03-16 개명 항목 |
| Genie Agents | Genie Spaces | Genie Agents 페이지의 "Genie Agents were formerly known as Genie Spaces." |
| Data profiling (Data quality monitoring의 일부) | Lakehouse Monitoring | Data quality monitoring 페이지의 "Data profiling was formerly known as Lakehouse Monitoring." |

### 7.2 표기 확인이 필요한 항목

아래 항목은 현재 docs에서 현재 표기를 확인했지만, 이번에 연 페이지에는 구 명칭이 "formerly" 등으로 명시되어 있지 않습니다. 따라서 대응 관계를 단정하지 않고 현재 표기만 적습니다.

| 현재 docs 표기 | 확인한 페이지 | 비고 |
|---|---|---|
| Lakeflow pipelines | 소개 페이지, Spark Declarative Pipelines on Lakeflow | 해당 페이지는 Lakeflow pipelines가 Apache Spark Declarative Pipelines 위에 구축되어 상호 운용된다고 설명하며 이전 제품명은 적지 않음 |
| OpenSharing | What is OpenSharing? | 페이지에 이전 이름 언급 없음 |
| Genie Code | Genie Code 페이지 | 페이지에 이전 이름 언급 없음 |
| Data + AI Platform | 소개 페이지 | 소개 페이지의 표기 |

> **주의** 다른 자료나 이전 교육 자료에서 위 항목의 다른 이름을 보게 되면, 현재 docs 표기를 우선 쓰고 대응 관계는 해당 원문에서 직접 확인한 뒤에만 병기하십시오. 대응 관계를 추정해 "구 명칭"으로 적으면 실습 화면과 맞지 않을 수 있습니다.

### 7.3 문서 간 표기 차이

| 항목 | 차이 |
|---|---|
| 컴퓨트 | Concepts 페이지는 "cluster"를 정의하지만 "compute"라는 독립 항목은 없음. 이 책은 아키텍처 페이지의 클래식·서버리스 구분을 따름 |
| Unity Catalog 정의 | Concepts는 "통합 거버넌스 솔루션", Unity Catalog 소개 페이지는 "내장된 통합 거버넌스 계층"으로 표현이 다름 (의미는 같음) |
| 메타스토어·카탈로그·스키마 | Unity Catalog 소개 페이지에는 독립 정의가 없고 3단계 이름 `catalog.schema.object`로만 나옴. 정의는 Concepts 기준 |

## 참고 문서

- [What is Databricks?](https://docs.databricks.com/aws/en/introduction/)
- [Concepts](https://docs.databricks.com/aws/en/getting-started/concepts)
- [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [Databricks notebooks](https://docs.databricks.com/aws/en/notebooks/)
- [Billable usage system table](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Free trial vs. Free Edition](https://docs.databricks.com/aws/en/getting-started/free-trial-vs-free-edition)
- [Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)
- [Genie](https://docs.databricks.com/aws/en/genie/)
- [Genie Code](https://docs.databricks.com/aws/en/genie-code/)
- [Spark Declarative Pipelines on Lakeflow](https://docs.databricks.com/aws/en/ldp/)
- [What is OpenSharing?](https://docs.databricks.com/aws/en/delta-sharing/)
- [Data profiling](https://docs.databricks.com/aws/en/lakehouse-monitoring/)
- [Navigate the workspace](https://docs.databricks.com/aws/en/workspace/)
- [Databricks AI Search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- [Declarative Automation Bundles 릴리즈 노트](https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles)
- [Genie Agents](https://docs.databricks.com/aws/en/genie-agents/)
- [Data quality monitoring](https://docs.databricks.com/aws/en/data-quality-monitoring/)
