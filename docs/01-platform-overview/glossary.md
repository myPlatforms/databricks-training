# 용어 정리

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 01장과 이후 장에서 반복해 나오는 용어를 한곳에 모은 표입니다. 정의는 공식 문서의 설명을 바탕으로 쉽게 풀어 적었고, 처음 나오는 용어는 영문을 함께 적었습니다. 정의가 공식 문서와 다르게 읽힌다면 참고 문서 링크의 원문을 우선하십시오.

## 1. 플랫폼과 구조

| 용어 | 정의 | 자세히 |
|---|---|---|
| 레이크하우스(lakehouse) | 데이터 레이크의 저렴한 저장과 데이터 웨어하우스의 트랜잭션·권한 관리를 함께 가진 데이터 관리 구조 | [플랫폼이란 무엇인가](what-is-databricks.md) |
| 계정(account) | 여러 워크스페이스를 포함하는 최상위 단위. 청구와 지원이 계정 단위로 처리됨 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 워크스페이스(workspace) | 팀이 노트북, 쿼리, 잡, 컴퓨트를 쓰는 작업 공간 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| control plane (제어 영역) | Databricks 계정 안에서 Databricks가 운영하는 백엔드 서비스와 웹 애플리케이션 | [플랫폼 아키텍처](architecture.md) |
| compute plane (컴퓨트 영역) | 데이터를 처리하는 영역. 클래식은 고객 클라우드 계정, 서버리스는 Databricks 계정 안 | [플랫폼 아키텍처](architecture.md) |
| 워크스페이스 스토리지(workspace storage) | 노트북·쿼리 같은 워크스페이스 파일과 실행 결과 같은 시스템 데이터를 담는 저장소 | [플랫폼 아키텍처](architecture.md) |
| DBFS 루트(DBFS root) | `dbfs:/` 네임스페이스의 레거시 저장 영역. 공식 문서는 deprecated이며 권장하지 않는다고 설명 | [플랫폼 아키텍처](architecture.md) |

## 2. 거버넌스와 데이터 구조

| 용어 | 정의 | 자세히 |
|---|---|---|
| Unity Catalog | 데이터와 AI 자산의 권한, 메타데이터, 계보를 중앙에서 관리하는 거버넌스 시스템 | 06장에서 다룹니다 |
| 메타스토어(metastore) | 카탈로그·스키마·테이블의 메타데이터와 권한을 등록하는 계정 수준 구성 요소 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 카탈로그(catalog) | 데이터를 구분·격리하는 최상위 컨테이너 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 스키마(schema) | 카탈로그 안의 데이터베이스 역할. 테이블, 볼륨, 함수, 모델을 담음 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 테이블(table) | 구조화된 데이터를 담는 객체. `catalog.schema.table`로 참조 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) |
| 볼륨(volume) | 파일을 Unity Catalog 아래에서 관리하는 객체 | 02장에서 다룹니다 |
| 기본 스토리지(Default storage) | Databricks 계정 안의 관리형 객체 스토리지. 클래식 컴퓨트가 데이터 자산과 직접 상호작용할 수 없음 | [플랫폼 아키텍처](architecture.md) |
| Delta Lake | 객체 스토리지 위에서 ACID 트랜잭션을 지원하는 테이블 형식 | 02장에서 다룹니다 |

## 3. 컴퓨트

| 용어 | 정의 | 자세히 |
|---|---|---|
| 서버리스 컴퓨트(serverless compute) | Databricks가 프로비저닝과 런타임 관리를 맡는 컴퓨트. 대부분의 워크스페이스에서 기본 제공 | [플랫폼 아키텍처](architecture.md) |
| 클래식 컴퓨트(classic compute) | 고객 클라우드 계정의 VM에서 실행되며 클러스터 구성을 직접 관리하는 컴퓨트 | [플랫폼 아키텍처](architecture.md) |
| SQL 웨어하우스(SQL warehouse) | SQL과 BI 워크로드용 컴퓨트. 서버리스 또는 클래식으로 만들 수 있음 | 03장에서 다룹니다 |
| Databricks Runtime (DBR) | 컴퓨트에서 쓰는 실행 환경의 버전 묶음 | 03장에서 다룹니다 |

## 4. 노트북과 개발

| 용어 | 정의 | 자세히 |
|---|---|---|
| 노트북(notebook) | 코드, 결과, 설명을 셀 단위로 담는 작업 문서 | [노트북 기초](notebooks-basics.md) |
| 셀(cell) | 노트북에서 실행하는 단위 | [노트북 기초](notebooks-basics.md) |
| 매직 명령(magic command) | `%`로 시작해 셀 언어를 바꾸거나 기능을 호출하는 명령 (`%sql`, `%run`, `%pip` 등) | [노트북 기초](notebooks-basics.md) |
| `%run` | 다른 노트북을 현재 노트북 안에서 실행하고 함수와 변수를 불러오는 명령 | [노트북 기초](notebooks-basics.md) |
| 위젯(widget) | 노트북에 입력 값을 받는 입력란을 붙이는 기능. 문자열 값만 받음 | [노트북 기초](notebooks-basics.md) |
| Git 폴더(Git folders) | Git 저장소와 연결된 워크스페이스 폴더 | 11장에서 다룹니다 |
| 번들(bundle) | 코드와 리소스 정의를 묶어 배포하는 단위. 공식 문서의 표기는 Declarative Automation Bundles | 11장에서 다룹니다 |

## 5. 과금

| 용어 | 정의 | 자세히 |
|---|---|---|
| DBU (Databricks unit) | 인스턴스 유형에 따른 시간당 처리 능력의 단위. 청구의 기본 단위 | [과금 모델 기초](billing-basics.md) |
| SKU (Stock Keeping Unit) | 청구 품목 이름. 같은 제품도 컴퓨트 유형에 따라 다른 SKU로 청구될 수 있음 | [과금 모델 기초](billing-basics.md) |
| `system.billing.usage` | 사용량 레코드를 담는 시스템 테이블 | [과금 모델 기초](billing-basics.md) |
| 종량제(pay-as-you-go) | 사용한 만큼 청구되는 방식. 무료 체험 종료 후 전환되는 방식으로도 나옴 | [시작하기](getting-started.md) |

## 6. 시작 방법과 AI 도구

| 용어 | 정의 | 자세히 |
|---|---|---|
| Free Edition | 학습·비상업적 목적의 상시 무료 제한 버전. 서버리스 워크스페이스 1개, 클래식 컴퓨트 없음 | [시작하기](getting-started.md) |
| 무료 체험판(free trial) | 업무 평가용 체험. 시작 후 14일 동안 크레딧 사용 | [시작하기](getting-started.md) |
| Genie | 워크스페이스 화면에 나타나는 AI 기능 이름의 일부. 홈 화면의 Ask Genie, SQL 그룹의 Genie Agents 등으로 표기됨 | [워크스페이스 UI](workspace-ui.md) |
| Genie One | 공식 시작하기 페이지의 튜토리얼에 나오는 제품 표기. 탐색과 대시보드 실습에 쓰임 | [시작하기](getting-started.md) |
| Genie Code | 워크스페이스의 AI 코딩 도우미. 상단바에서 열 수 있음 | [11장 개발자 도구](../11-developer-tools/README.md) |
| Lakebase | 관리형 Postgres 데이터베이스 | [10장 Lakebase](../10-lakebase/README.md) |

> **참고** Genie 계열 명칭은 바뀌는 중입니다. 공식 문서 표기가 "Genie One", "Genie Agents", "Genie Code"처럼 서로 다른 제품을 가리키므로, 문서에 옮길 때는 이름을 섞어 쓰지 마십시오. 명칭은 실습 당일 워크스페이스 화면과 공식 문서를 함께 확인하십시오.

## 7. 명칭 주의

| 현재 표기 | 과거에 쓰이던 표기 (처음 한 번 병기 권장) | 메모 |
|---|---|---|
| Lakeflow pipelines | DLT (Lakeflow Spark Declarative Pipelines) | 공식 소개 페이지의 현재 표기는 "Lakeflow pipelines" |
| OpenSharing | Delta Sharing | 공식 소개 페이지 목록의 현재 표기 |
| Genie Agents | Genie Spaces | SQL 그룹 항목의 현재 표기 |
| Data + AI Platform | Data Intelligence Platform | 다른 자료에서 보이는 표현. 공식 소개 페이지는 "Data + AI Platform"을 씀 |

> **주의** 위 표의 두 번째 열은 다른 자료에서 흔히 보이는 표기입니다. 교육 자료에 처음 나올 때만 괄호로 병기하고, 이후에는 현재 표기로 통일하십시오. 과거 명칭을 현재 명칭인 것처럼 쓰면 실습 화면과 맞지 않을 수 있습니다.

## 참고 문서

- [What is Databricks?](https://docs.databricks.com/aws/en/introduction/)
- [Concepts](https://docs.databricks.com/aws/en/getting-started/concepts)
- [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [Databricks notebooks](https://docs.databricks.com/aws/en/notebooks/)
- [Billable usage system table](https://docs.databricks.com/aws/en/admin/system-tables/billing)
- [Free trial vs. Free Edition](https://docs.databricks.com/aws/en/getting-started/free-trial-vs-free-edition)
