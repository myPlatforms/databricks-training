# 컴퓨트 종류와 선택 기준

> 기준일: 2026-10-29 · 근거: 공식 문서

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

| 워크로드 | 1순위 선택 | 근거(원문) | 대안과 조건 |
|---|---|---|---|
| 대화형 노트북 탐색과 개발 | 서버리스 노트북 | 노트북의 컴퓨트 드롭다운에서 **Serverless** 를 선택해 붙입니다. 워크스페이스에 Unity Catalog가 필요합니다. 기본 실행 시간 제한은 2.5시간(9,000초)입니다 | Scala·R, JAR 라이브러리, Spark UI가 필요하면 클래식 |
| 정기 배치 Job | 서버리스 Job | 성능 모드 두 가지(Standard는 시작 지연 4~6분, Performance optimized는 더 빠른 시작). 두 모드는 같은 SKU이며 Standard가 DBU를 덜 씁니다 | 서버리스 제약(컴퓨트 범위 라이브러리·init 스크립트, 최대 7일 실행 등)에 걸리면 클래식 Job 컴퓨트 |
| Lakeflow 파이프라인 | 서버리스 파이프라인 | 인프라를 Databricks가 관리해 설정 옵션이 적습니다. 트리거·연속·실시간 모드 지원. `ADVANCED` 에디션과 서버리스 지원 리전이 필요합니다 | Hive 메타스토어 등 일부 워크로드는 클래식 파이프라인 컴퓨트 |
| SQL·BI 쿼리 | 서버리스 SQL 웨어하우스 | 문서: "Databricks recommends using serverless SQL warehouses when available." 시작 시간 보통 2~6초 | 서버리스가 불가하면 Pro(Predictive IO), 그다음 Classic |
| R, RDD API, GPU, 분산 ML, 권한 높은 시스템 접근 | 클래식 Dedicated | Standard 문서가 이 항목들을 Dedicated 대상으로 명시합니다 | 서버리스 GPU(AI Runtime)가 있으나 별도 제품 페이지에서 확인 |
| 여러 사용자가 공유하는 ETL·탐색 | 클래식 Standard | 문서가 대부분의 워크로드에 권장하는 모드입니다. Lakeguard로 사용자 코드를 격리합니다 | 한 사용자·그룹 전용이면 Dedicated |

> **주의** 이 표는 시작점입니다. 서버리스가 지원하는 기능과 제약은 워크로드마다 다르므로, 실제 선택 전에 [서버리스 제약과 지원 기능](serverless-limitations.md) 페이지를 확인하십시오.

### 2.4 SQL 웨어하우스 유형 비교

| 유형 | Photon | Predictive IO | Intelligent Workload Management | 시작 시간(문서) | 실행 위치 |
|---|---|---|---|---|---|
| Serverless | 지원 | 지원 | 지원 | 보통 2~6초 | Databricks 계정 |
| Pro | 지원 | 지원 | 미지원 | 보통 약 4분 | 고객 AWS 계정 |
| Classic | 지원 | 미지원 | 미지원 | 보통 약 4분 | 고객 AWS 계정 |

SQL 웨어하우스는 자격 증명 패스스루(credential passthrough)를 지원하지 않습니다. 페이지에는 Lakehouse Real-Time 유형(Beta, SELECT 쿼리만 지원)도 나오지만 실행 위치는 명시되어 있지 않습니다. 시작 시간 수치는 공식 SQL warehouse 유형 페이지에서 확인했습니다.

### 2.5 액세스 모드: Standard와 Dedicated

| 항목 | Standard | Dedicated |
|---|---|---|
| 정의 | 여러 사용자가 동시에 쓰는 공유 컴퓨트. CAN ATTACH TO 권한 필요 | 한 사용자 또는 그룹(그룹 할당은 Public Preview)에 할당 |
| 격리 | Lakeguard로 사용자 코드를 Spark 인프라와 분리 | 할당된 사용자·그룹 전용 |
| 언어 | Python·SQL 전 버전, Scala는 Databricks Runtime 13.3 LTS 이상, R 미지원 | 문서에 전체 목록 없음. R 사용 시 Dedicated 권장 |
| RDD API | 미지원 | 지원 대상으로 안내 |
| GPU, Databricks Runtime for ML | 미지원 | 지원 대상으로 안내 |
| 기타 제약 | Hive UDF, spark-submit 태스크, 소켓 소스 미지원 | 세분화 접근 제어(fine-grain access control)는 Databricks Runtime 15.4 LTS 이상과 서버리스 활성화 필요 |

API에서는 `data_security_mode`로 지정하며, 값은 `DATA_SECURITY_MODE_AUTO`, `DATA_SECURITY_MODE_STANDARD`, `DATA_SECURITY_MODE_DEDICATED`입니다. `USER_ISOLATION`과 `SINGLE_USER`는 각각 Standard, Dedicated의 레거시 별칭입니다.

UI 기본값은 **Auto** 입니다. Auto는 Standard를 고르되, ML 런타임이나 GPU 인스턴스 유형, Databricks Runtime 14.3 미만을 선택하면 Dedicated를 씁니다.

## 3. 어떻게 쓰는가 (선택 절차)

실제 선택은 다음 순서로 확인하는 방법이 실용적입니다.

1. **서버리스 가능 여부 확인**: 문서는 서버리스 컴퓨트가 대부분의 워크스페이스에서 기본 제공되며 별도 활성화가 필요 없다고 설명합니다. 다만 Unity Catalog가 없는 레거시 워크스페이스는 접근할 수 없습니다. 서버리스 파이프라인은 서버리스 지원 리전이 필요합니다.
2. **워크로드가 서버리스 제약에 걸리는지 확인**: 언어(R, 노트북의 Scala), Spark RDD API, 컴퓨트 범위 라이브러리·init 스크립트, Databricks Container Services, 7일을 넘는 실행, Spark UI·Spark 로그 의존 여부를 봅니다. 하나라도 걸리면 클래식으로 갑니다.
3. **SQL 워크로드인지 확인**: SQL과 BI 쿼리만 있다면 SQL 웨어하우스를 고릅니다. 문서는 Databricks가 가능하면 서버리스 SQL 웨어하우스를 권장한다고 설명합니다.
4. **클래식이면 액세스 모드 결정**: 문서는 대부분의 워크로드에 Standard를 권장합니다. R, GPU, RDD API, 시스템 저수준 접근이 필요하면 Dedicated를 씁니다.
5. **비용 구조 확인**: DBU와 클라우드 인스턴스 청구가 어떻게 나뉘는지 [비용 구조 비교](cost-structure.md) 페이지에서 확인합니다.

결정 결과를 한 줄로 적는다면 다음 형식을 권합니다.

```text
워크로드: 일 1회 배치 ETL, 노트북 2개, 사용자 5명
제약 확인: R 미사용, RDD 미사용, 컴퓨트 범위 라이브러리 미사용
선택: 서버리스 Job (성능 모드 Standard, 시작 지연 4~6분 감수)
```

## 4. 트레이드오프

| 기준 | 서버리스 | 클래식 | SQL 웨어하우스 |
|---|---|---|---|
| 시작 속도 | 노트북은 컴퓨트 드롭다운에서 선택. Job·파이프라인은 Standard 성능 모드에서 4~6분, Performance optimized에서 더 빠름 | 클러스터 시작 시간이 필요합니다. 인스턴스 풀(Instance pools)로 줄일 수 있습니다 | 서버리스 보통 2~6초, Pro·Classic 보통 약 4분 (문서 기재) |
| 설정 자유도 | 제한적. 대부분의 Spark 컴퓨트 설정과 컴퓨트 정책·인스턴스 풀·컴퓨트 범위 환경 변수를 지원하지 않음 | 노드 유형, 런타임, 라이브러리, init 스크립트까지 설정 | 유형과 크기, 클러스터 수 범위 |
| 관리 부담 | 낮음 | 높음 (정책과 패치 포함) | 낮음 (서버리스) ~ 중간 (Pro·Classic) |
| 기능 범위 | 제약이 많음 (Spark Connect API만, ANSI 모드 기본 ON 등. 서버리스 제약 페이지) | 가장 넓음 | SQL 중심 |
| 과금 구조 | DBU 중심 | DBU와 클라우드 인스턴스 별도 | 서버리스는 DBU 중심, Pro·Classic은 인스턴스 별도 |

> **주의** "클래식이 무조건 싸다"는 판단은 DBU 단가만 비교하면 틀리기 쉽습니다. 클래식은 클라우드 인스턴스 요금이 따로 붙고, 서버리스는 그 인프라가 Databricks 계정 안에서 돌아갑니다. 자세한 구조는 [비용 구조 비교](cost-structure.md) 페이지를 보십시오.

## 5. 주의사항

- **문서 표기를 기준으로 용어를 맞추십시오.** 클래식 컴퓨트의 액세스 모드는 현재 문서에서 Standard, Dedicated, Auto로 표기합니다. 예전 자료에 나오는 다른 이름은 현재 문서와 다를 수 있습니다.
- **서버리스와 클래식은 같은 워크로드를 같은 방식으로 돌리지 않습니다.** 같은 노트북이라도 서버리스에서는 Spark 설정이나 UDF 메모리 제한이 다르게 적용됩니다. 옮길 때는 제약 페이지를 대조하십시오.
- **상태 라벨을 확인하십시오.** 원문 기준으로 서버리스 사용 정책(usage policies)과 노트북 태스크의 고메모리는 Public Preview, Git 폴더·번들용 Shared Serverless는 Beta입니다. 운영 워크로드에 넣기 전에 해당 페이지의 상태를 확인하십시오.
- **서버리스 Job은 로그가 다릅니다.** Spark UI와 Spark 로그가 없고 클라이언트 측 로그만 제공되며, 태스크 로그가 태스크별로 분리되지 않습니다.
- **워크스페이스 설정에 따라 가용성이 다를 수 있습니다.** 서버리스 가용성은 Unity Catalog 여부에 좌우되고, 서버리스 파이프라인은 서버리스 지원 리전이 필요합니다.

## 참고 문서

- [Compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/)
- [Serverless compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/)
- [Classic compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/use-compute)
- [SQL warehouse 유형 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/warehouse-types)
- [High-level architecture — 컨트롤 플레인과 컴퓨트 플레인 (AWS)](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [Standard compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/standard-overview)
- [Dedicated compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/dedicated-overview)
- [Standard compute 제약 (AWS)](https://docs.databricks.com/aws/en/compute/standard-limitations)
- [서버리스 컴퓨트 제약 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/limitations)
- [서버리스 노트북 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [서버리스 Job 실행 (AWS)](https://docs.databricks.com/aws/en/jobs/run-serverless-jobs)
- [서버리스 Lakeflow 파이프라인 (AWS)](https://docs.databricks.com/aws/en/ldp/serverless)
- [서버리스 GPU / AI Runtime (AWS)](https://docs.databricks.com/aws/en/compute/serverless/gpu)
- [SQL warehouse 개요 (AWS)](https://docs.databricks.com/aws/en/compute/sql-warehouse/)
- [Clusters API 레퍼런스](https://docs.databricks.com/api/workspace/clusters/create)
