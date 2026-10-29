# 플랫폼이란 무엇인가

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Databricks는 데이터를 수집하고, 저장하고, 가공하고, 분석하고, 머신러닝과 생성형 AI 모델까지 다루는 **관리형 플랫폼** 입니다. 공식 소개 페이지는 Databricks를 "a unified, open analytics platform for building, deploying, sharing, and maintaining enterprise-grade data, analytics, and AI solutions at scale"로 설명하며, 플랫폼을 **Databricks Data + AI Platform** 이라고 부릅니다.

핵심은 세 가지입니다.

| 키워드 | 의미 |
|---|---|
| 통합(unified) | 데이터 엔지니어링, SQL 분석, 머신러닝, AI를 같은 데이터와 같은 권한 체계 위에서 다룹니다. |
| 개방(open) | 저장 형식과 엔진의 기반이 오픈 소스(Apache Spark, Delta Lake, MLflow 등)입니다. 공식 소개 페이지도 Spark, Delta, MLflow를 플랫폼의 기반 기술로 연결합니다. |
| 관리형(managed) | 클러스터 기동, 런타임 업그레이드, 메타데이터 관리 같은 운영 작업의 상당 부분을 플랫폼이 맡습니다. 고객 클라우드 계정 안에서 동작하는 구조는 [아키텍처](architecture.md) 페이지에서 설명합니다. |

> **참고** 공식 소개 페이지는 Databricks가 "클라우드 스토리지와 보안을 고객 클라우드 계정 안에서 통합"하며 그 아래 인프라를 관리한다고 설명합니다. 데이터는 고객의 클라우드 저장소에 남고, Databricks는 그 데이터를 처리하는 제어 계층을 제공한다고 이해하면 됩니다.

## 1. 왜 필요한가

### 이전 방식의 한계

데이터 플랫폼은 오랫동안 용도별로 나뉘어 왔습니다.

| 방식 | 장점 | 한계 |
|---|---|---|
| 데이터 웨어하우스 | SQL 분석과 BI가 빠르고 권한 관리가 명확합니다. | 비정형 데이터, 머신러닝 학습, 스트리밍 처리에 약하고 저장 비용이 높아지기 쉽습니다. |
| 데이터 레이크(data lake) | 값싼 객체 스토리지에 원본을 그대로 쌓을 수 있습니다. | 데이터 품질·트랜잭션·권한이 약하고, 파일이 쌓이면 "데이터 늪(data swamp)"이 되기 쉽습니다. |
| 두 시스템을 조합 | 각 시스템의 장점을 취할 수 있습니다. | 같은 데이터가 두 벌 이상 복제되고, 파이프라인이 늘고, 권한 체계가 이원화됩니다. |
| 별도 ML 플랫폼 추가 | 실험 추적과 모델 배포를 따로 할 수 있습니다. | 학습 데이터 접근 권한, 피처 정의, 모델 거버넌스가 다시 분산됩니다. |

이 문제를 줄이려면 저장 계층과 처리 계층, 거버넌스 계층을 하나의 플랫폼에서 공유해야 합니다. Databricks가 이 역할을 맡습니다.

### 플랫폼이 해결하는 것

| 문제 | Databricks의 접근 | 자세히 보는 곳 |
|---|---|---|
| 데이터 복제가 여러 벌 | 같은 테이블을 SQL, 노트북, 머신러닝이 함께 읽습니다. | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 권한 체계 이원화 | Unity Catalog에서 카탈로그·스키마·테이블 단위로 한 번 정의합니다. | 06장에서 다룹니다 (Unity Catalog) |
| 인프라 운영 부담 | 서버리스 컴퓨트는 프로비저닝과 런타임 업그레이드를 플랫폼이 맡습니다. | 03장에서 다룹니다 (컴퓨트) |
| 파이프라인 관리 | 수집과 변환을 파이프라인 단위로 선언하고 실행을 관리합니다. | 04장에서 다룹니다 (파이프라인과 잡) |

## 2. 레이크하우스(Lakehouse) 개념

Databricks의 기본 설계 개념은 **레이크하우스** 입니다. 공식 용어 설명은 다음과 같습니다.

> A data lakehouse is a data management system that combines the benefits of data lakes and data warehouses.

즉, 데이터 레이크의 **저렴한 객체 스토리지와 개방형 형식** 에 데이터 웨어하우스의 ** 트랜잭션, 스키마, 권한 관리** 를 더한 구조입니다. Databricks에서 이 구조를 떠받치는 것이 다음 두 기술입니다.

- **Delta Lake**: 객체 스토리지 위에서 ACID 트랜잭션을 지원하는 테이블 형식입니다. 저장 계층의 세부는 02장에서 다룹니다.
- **Unity Catalog**: 테이블, 볼륨, 모델 같은 데이터·AI 자산의 권한과 계보(lineage)를 중앙에서 관리합니다. 06장에서 다룹니다.

> **참고** 공식 문서는 Delta Lake를 "What is Delta Lake in Databricks?" 페이지에서 따로 다룹니다. 이 장에서는 개념만 소개하고 형식의 내부 동작은 다루지 않습니다.

## 3. 기능 영역 지도

공식 소개 페이지는 플랫폼의 기능을 여러 영역으로 나누어 소개합니다. 이 교육 자료의 장 구성은 그 영역을 따릅니다.

| 영역 | 대표 기능(공식 소개 페이지 기준) | 이 교육에서의 위치 |
|---|---|---|
| 데이터 저장 | Delta Lake, 클라우드 스토리지, 기본 스토리지(Default storage) | 02장에서 다룹니다 (스토리지) |
| 컴퓨트 | 서버리스 컴퓨트, 클래식 컴퓨트, SQL 웨어하우스(SQL warehouses) | 03장에서 다룹니다 (컴퓨트) |
| 수집·파이프라인 | Auto Loader, Lakeflow pipelines | 04장에서 다룹니다 |
| 거버넌스 | Unity Catalog, 메트릭 뷰(Metric views), 데이터 공유(OpenSharing) | 06장에서 다룹니다 (Unity Catalog) |
| SQL 분석·BI | SQL 에디터, AI/BI 대시보드, Genie Agents | 05·07장에서 다룹니다 |
| 머신러닝·AI | MLflow, AI Functions, Databricks Runtime for Machine Learning | 08·09장에서 다룹니다 |
| 트랜잭션(OLTP) | Lakebase Postgres | [10장 Lakebase](../10-lakebase/README.md)에서 다룹니다 |
| 개발 도구 | Declarative Automation Bundles(DAB), Git 폴더, Genie Code | [11장 개발자 도구](../11-developer-tools/README.md)에서 다룹니다 |

> **참고** 위 표의 제품명과 기능명은 공식 소개 페이지에 나온 현재 표기를 따랐습니다. 예를 들어 Lakeflow pipelines, Genie Agents, OpenSharing은 문서의 현재 명칭입니다. 과거 명칭(예: DLT, Genie Spaces, Delta Sharing)을 함께 쓸 때는 처음 한 번만 괄호로 병기합니다.

## 4. 어떤 사람에게 맞는가

| 역할 | 주로 쓰는 영역 | 이 장에서 먼저 볼 것 |
|---|---|---|
| 데이터 분석가 | SQL 에디터, 대시보드, Genie | 워크스페이스 UI, 시작하기 |
| 데이터 엔지니어 | 노트북, 파이프라인, 잡, 스토리지 | 아키텍처, 노트북 기초 |
| 데이터 과학자·ML 엔지니어 | 노트북, 실험 추적, 모델 서빙 | 노트북 기초, 과금 모델 |
| 플랫폼 관리자 | 계정 콘솔, 메타스토어, 권한 | 계정·워크스페이스·메타스토어 |
| 애플리케이션 개발자 | Apps, Lakebase, API | 아키텍처, 10장과 11장 |

## 5. 트레이드오프와 맞지 않는 경우

Databricks가 모든 상황에 맞는 것은 아닙니다. 다음 경우에는 설계를 다시 검토하십시오.

- **단일 소규모 데이터베이스만 필요한 경우**: 트랜잭션 애플리케이션용 DB 하나만 필요하다면, 레이크하우스 전체를 도입하는 것보다 관리형 Postgres(Lakebase 포함) 같은 단일 목적 서비스가 단순할 수 있습니다.
- **분석 대상 데이터가 거의 없는 경우**: 데이터 규모가 작고 변경이 드물면 스프레드시트나 단일 웨어하우스로 충분할 수 있습니다.
- **플랫폼 종속을 최소화해야 하는 경우**: 개방형 형식을 쓰더라도 Unity Catalog, 서버리스 같은 플랫폼 기능을 깊게 쓰면 이전 비용이 커집니다. 기능별로 어디까지 쓸지 아키텍처 단계에서 정하십시오.

## 6. 주의사항

> **주의** "Databricks = Spark 클러스터"로 이해하면 이후 장에서 혼란이 생깁니다. Spark는 처리 엔진의 하나이고, 이 플랫폼에는 거버넌스, 서버리스 컴퓨트, SQL 분석, 머신러닝, 파이프라인 등이 함께 들어 있습니다.

> **주의** 공식 소개 페이지의 플랫폼 명칭은 "Databricks Data + AI Platform"입니다. 다른 자료에서 보이는 "Data Intelligence Platform"이라는 표현을 그대로 옮기면 공식 표기와 어긋날 수 있으니, 문서에 인용할 때는 원문 표기를 확인하십시오.

> **참고** 이 장은 AWS 문서 기준입니다. 기능의 가용 리전과 상태 라벨은 클라우드와 리전에 따라 다를 수 있으므로, 실제 적용 전에 해당 워크스페이스에서 기능 가용성을 확인하십시오.

## 다음으로 읽을 페이지

플랫폼의 세 가지 구성 요소가 어디서 실행되는지는 [플랫폼 아키텍처](architecture.md)에서 이어집니다.

## 참고 문서

- [What is Databricks?](https://docs.databricks.com/aws/en/introduction/)
- [What is a data lakehouse?](https://docs.databricks.com/aws/en/lakehouse/)
- [What is Delta Lake in Databricks?](https://docs.databricks.com/aws/en/delta/)
- [What is Unity Catalog?](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)
- [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
