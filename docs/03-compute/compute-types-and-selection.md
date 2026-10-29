# 컴퓨트 종류와 선택 기준

> 기준일: 2026-10-28 · 근거: 공식 문서

Databricks의 컴퓨트는 크게 세 가지로 나뉩니다. 서버리스 컴퓨트(Serverless compute), 클래식 컴퓨트(Classic compute), SQL 웨어하우스(SQL warehouses)입니다. 공식 Compute 개요 페이지는 세 가지 옵션을 각각 "Databricks가 관리하는 온디맨드 자원", "직접 만들고 설정하고 관리하는 자원", "SQL과 BI 작업에 최적화된 자원으로, 서버리스 또는 클래식으로 제공"으로 요약합니다. 이 페이지는 세 분류를 구분하고, 워크로드에 맞는 선택 기준을 정리합니다.

## 1. 왜 필요한가

데이터 작업은 종류가 다양합니다. 대화형 노트북 탐색, 정기 배치 Job, 스트리밍 파이프라인, BI 대시보드 쿼리는 필요한 자원의 크기와 시작 속도, 격리 수준이 서로 다릅니다. 컴퓨트 종류가 하나뿐이라면 다음 문제가 생깁니다.

| 문제 | 설명 |
|---|---|
| 과잉 프로비저닝 | 피크에 맞춘 클러스터를 항상 띄우면 한가한 시간에도 비용이 나갑니다. |
| 과소 프로비저닝 | 평균에 맞추면 큰 Job이나 동시 쿼리에서 대기가 길어집니다. |
| 관리 부담 | 클러스터 이미지, 라이브러리, 패치를 사용자가 모두 관리해야 합니다. |
| 격리 요구 | 여러 사용자가 한 자원을 나눠 쓸 때 데이터 격리 수준이 워크로드마다 다릅니다. |

Databricks는 이 문제를 세 가지 컴퓨트 유형으로 나눠서 풀도록 제공합니다. 서버리스는 관리 부담과 시작 대기를 줄이는 쪽에, 클래식은 설정 자유도와 세밀한 제어 쪽에, SQL 웨어하우스는 SQL과 BI 동시 쿼리 쪽에 맞춥니다.

## 2. 어떻게 동작하는가

### 2.1 세 가지 분류

| 분류 | 문서상 정의 | 실행 위치 | 사용자가 하는 일 |
|---|---|---|---|
| 서버리스 컴퓨트 | Databricks가 관리하는 온디맨드 자원. 노트북, 워크플로(Job), Lakeflow 파이프라인에 쓰입니다. | Databricks 계정 안의 컴퓨트 레이어 | 환경(Environment)과 의존성 선택 |
| 클래식 컴퓨트 | 올-퍼포즈(All-purpose), Job, Lakeflow 파이프라인용 자원. 사용자가 직접 만들고 설정하고 관리합니다. | 고객 클라우드 계정 | 노드 유형, 버전, 액세스 모드, 오토스케일링 설정 |
| SQL 웨어하우스 | SQL과 BI 작업용 자원. 서버리스, Pro, Classic 유형이 있습니다. | Serverless는 Databricks 계정, Pro·Classic은 고객 클라우드 계정 | 유형, 크기, 클러스터 수 범위 설정 |

문서 기준으로 클래식 컴퓨트는 "all-purpose, jobs, and Lakeflow pipelines compute resources"를 가리킵니다. 즉 Job 전용 클러스터도 클래식 컴퓨트의 한 종류입니다.

### 2.2 평면(Plane) 개념으로 보기

공식 아키텍처 문서는 컨트롤 플레인(Control plane)과 컴퓨트 플레인(Compute plane)을 구분합니다.

- **컨트롤 플레인**: Databricks가 관리하는 백엔드 서비스로, Databricks 계정 안에 있습니다.
- **컴퓨트 플레인**: 데이터가 실제로 처리되는 곳입니다.

서버리스 컴퓨트 플레인은 "Databricks compute resources run in a compute layer within your Databricks account"라고 문서에 나와 있습니다. 클래식 컴퓨트 플레인은 "Databricks compute resources run in your AWS account"입니다. 같은 워크스페이스 안에서도 워크로드가 어느 플레인에서 도는지에 따라 네트워크와 비용 구조가 달라집니다.

> **참고** 공식 아키텍처 문서는 SQL 웨어하우스가 어느 플레인에 속하는지 직접 언급하지 않습니다. SQL 웨어하우스 유형 페이지에서 Pro와 Classic은 고객 AWS 계정에서, Serverless는 Databricks 계정에서 실행된다고 설명하므로, 이 장은 그 설명을 따릅니다.

### 2.3 워크로드별 선택 표

| 워크로드 | 1순위 선택 | 이유 | 대안과 조건 |
|---|---|---|---|
| 노트북 탐색과 개발 | 서버리스 노트북 | 노트북을 열면 자동으로 서버리스가 선택되고, 시작 대기가 짧습니다 | 라이브러리 요구가 서버리스 제약에 걸리면 클래식 올-퍼포즈 컴퓨트 |
| 정기 배치 Job (표준 Spark) | 서버리스 Job | 환경 버전으로 의존성을 관리하고, 성능 모드로 시작 시간과 비용을 조절합니다 | 서버리스 제약에 걸리면 클래식 Job 컴퓨트 |
| 스트리밍 파이프라인 | 서버리스 파이프라인 | 파이프라인 전용 서버리스 실행 | 특정 트리거·모드 제약은 서버리스 제약 페이지 확인 |
| 여러 사용자의 BI·SQL 쿼리 | 서버리스 SQL 웨어하우스 | 시작이 빠르고 자동 확장 | 특정 네트워크·Pro 기능 요구 시 Pro 웨어하우스 |
| 특정 제약의 Spark 작업 (R, RDD, GPU, 커스텀 Hive 등) | 클래식 Dedicated 액세스 모드 | 서버리스와 Standard 모드가 지원하지 않는 기능 | 필요 기능을 확인한 뒤 결정 |
| 권한 격리가 필요한 다중 사용자 Spark 작업 | 클래식 Standard 액세스 모드 | 여러 사용자가 동시에 쓰며 데이터 격리 | Dedicated로 한 사용자·그룹에 고정 |

> **주의** 이 표는 시작점입니다. 서버리스가 지원하는 기능과 제약은 워크로드마다 다르므로, 실제 선택 전에 [서버리스 제약과 지원 기능](serverless-limitations.md) 페이지를 확인하십시오.

## 3. 어떻게 쓰는가 (선택 절차)

실제 선택은 다음 순서로 확인하는 방법이 실용적입니다.

1. **서버리스 가능 여부 확인**: 워크스페이스가 Unity Catalog에 연결되어 있는지 확인합니다. 문서는 Unity Catalog가 없는 레거시 워크스페이스는 서버리스 컴퓨트에 접근할 수 없다고 설명합니다.
2. **워크로드가 서버리스 제약에 걸리는지 확인**: 언어(R, Scala 노트북 등), RDD API, 컴퓨트 범위 라이브러리, 컴퓨트 범위 init 스크립트를 쓰는지 봅니다. 하나라도 걸리면 클래식으로 갑니다.
3. **SQL 워크로드인지 확인**: SQL과 BI 쿼리만 있다면 SQL 웨어하우스를 고릅니다. 문서는 Databricks가 가능하면 서버리스 SQL 웨어하우스를 권장한다고 설명합니다.
4. **클래식이면 액세스 모드 결정**: 여러 사용자가 공유하면 Standard, 한 사용자나 그룹이 독점하거나 R, GPU, RDD가 필요하면 Dedicated를 씁니다.
5. **비용 구조 확인**: DBU와 클라우드 인스턴스 청구가 어떻게 나뉘는지 [비용 구조 비교](cost-structure.md) 페이지에서 확인합니다.

결정 결과를 한 줄로 적는다면 다음 형식을 권합니다.

```text
워크로드: 일 1회 배치 ETL, 노트북 2개, 사용자 5명
제약 확인: R 미사용, RDD 미사용, 컴퓨트 범위 라이브러리 미사용
선택: 서버리스 Job (성능 모드 Standard, 허용 시간 내 시작 지연 4~6분 감수)
```

## 4. 트레이드오프

| 기준 | 서버리스 | 클래식 | SQL 웨어하우스 |
|---|---|---|---|
| 시작 속도 | 빠른 편 (노트북은 자동 연결) | 클러스터 시작 시간이 필요합니다. 풀(Pool)로 줄일 수 있습니다 | 서버리스는 2~6초, Pro·Classic은 약 4분 (문서 기재) |
| 설정 자유도 | 제한적. 허용된 Spark 설정만 세션 단위로 지정 | 노드 유형, 런타임, 라이브러리, init 스크립트까지 설정 | 유형과 크기, 클러스터 수 범위 |
| 관리 부담 | 낮음 | 높음 (정책과 패치 포함) | 낮음 (서버리스) ~ 중간 (Pro·Classic) |
| 기능 범위 | 제약이 많음 (서버리스 제약 페이지) | 가장 넓음 | SQL 중심 |
| 과금 구조 | DBU 중심 | DBU와 클라우드 인스턴스 별도 | 서버리스는 DBU 중심, Pro·Classic은 인스턴스 별도 |

> **주의** "클래식이 무조건 싸다"는 판단은 DBU 단가만 비교하면 틀리기 쉽습니다. 클래식은 클라우드 인스턴스 요금이 따로 붙고, 서버리스는 그 인프라가 Databricks 계정 안에서 돌아갑니다. 자세한 구조는 [비용 구조 비교](cost-structure.md) 페이지를 보십시오.

## 5. 주의사항

- **문서 표기를 기준으로 용어를 맞추십시오.** 클래식 컴퓨트의 액세스 모드는 현재 문서에서 Standard, Dedicated, Auto로 표기합니다. 예전 자료에 나오는 다른 이름은 현재 문서와 다를 수 있습니다.
- **서버리스와 클래식은 같은 워크로드를 같은 방식으로 돌리지 않습니다.** 같은 노트북이라도 서버리스에서는 Spark 설정이나 UDF 메모리 제한이 다르게 적용됩니다. 옮길 때는 제약 페이지를 대조하십시오.
- **상태 라벨을 확인하십시오.** 서버리스의 일부 기능(예: 서버리스 GPU 관련, 특정 사용 정책, 고메모리 컴퓨트)은 Public Preview나 Beta입니다. 운영 워크로드에 넣기 전에 해당 페이지의 상태를 확인하십시오.
- **워크스페이스 설정에 따라 가용성이 다를 수 있습니다.** 서버리스 가용성은 Unity Catalog 여부, 보안 프로필, 리전에 따라 달라집니다.

## 참고 문서

- [Compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/)
- [Serverless compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/)
- [Classic compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/use-compute)
- [SQL warehouse 유형 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)
- [High-level architecture — 컨트롤 플레인과 컴퓨트 플레인 (AWS)](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [Standard compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/standard-overview)
- [Dedicated compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/dedicated-overview)
