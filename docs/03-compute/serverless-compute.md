# 서버리스 컴퓨트

> 기준일: 2026-10-28 · 근거: 공식 문서

서버리스 컴퓨트(Serverless compute)는 노트북, 워크플로(Job), Lakeflow 파이프라인을 Databricks가 관리하는 온디맨드 자원에서 실행하는 방식입니다. 이 페이지는 서버리스가 어떤 워크로드를 지원하는지, 환경 버전(Environment version)과 기본 환경(Base environment)이 무엇인지, 노트북과 Job에서 각각 어떻게 설정하는지, 성능 모드와 타임아웃을 다룹니다. 제약과 지원 기능의 세부 목록은 [서버리스 제약과 지원 기능](serverless-limitations.md) 페이지에 있습니다.

## 1. 왜 필요한가

클래식 컴퓨트에서는 사용자가 클러스터를 만들고 노드 유형, 런타임, 라이브러리를 정한 뒤 시작을 기다려야 합니다. 노트북을 열고 몇 초 만에 실행하려면 클러스터를 상시로 띄워 두어야 하고, 그러면 한가한 시간에도 비용이 나갑니다.

서버리스 컴퓨트는 이 부담을 줄입니다. 공식 문서는 워크로드가 프로비저닝 없이 Databricks 계정 안에서 실행되어 시작과 확장이 빨라지고, 유휴 시간이 줄며, 컴퓨트 관리 부담이 낮아진다고 설명합니다.

| 항목 | 클래식 컴퓨트 | 서버리스 컴퓨트 |
|---|---|---|
| 클러스터 생성 | 사용자가 설정하고 만듭니다 | 필요 없습니다 |
| 시작 대기 | 클러스터 시작 시간이 필요합니다 | 노트북은 실행 시 자동 연결됩니다 |
| 런타임 관리 | Databricks Runtime 버전을 고릅니다 | 문서는 "versionless product"라고 설명하며, 환경 버전으로 의존성을 고릅니다 |
| 라이브러리 | 컴퓨트 범위 라이브러리, init 스크립트 | 환경(Environment)의 의존성 |

> **주의** 문서 간 표현이 엇갈립니다. 서버리스 개요 페이지는 "Serverless workloads always run on the latest runtime version"이라고 하고 제품을 버전리스(versionless)라고 설명합니다. 반면 노트북·Job 페이지는 환경 버전과 기본 환경을 고르라고 안내합니다. 두 설명이 실제로 어떻게 맞물리는지는 이 장에서 원문으로 확인하지 못했습니다. 운영 전에 워크스페이스에서 실제 선택지를 확인하십시오.

## 2. 어떻게 동작하는가

### 2.1 지원 워크로드

| 워크로드 | 서버리스 지원 | 비고 |
|---|---|---|
| 노트북 (Notebooks) | 지원 | 대화형 실행. Unity Catalog 필요 |
| 워크플로 (Jobs) | 지원 | 작업 유형에 따라 다름. Unity Catalog 필요 |
| Lakeflow 파이프라인 | 지원 | 배치와 스트리밍 파이프라인 (문서 "Serverless pipelines") |
| SQL 웨어하우스 | 지원 | 서버리스 유형. [SQL 웨어하우스](sql-warehouses.md) 페이지 |
| AI Runtime (GPU 포함) | 지원 | Public Preview 상태로 표기됨 |

서버리스 개요 페이지 기준 지원 워크로드는 노트북, 워크플로(Job), Lakeflow 파이프라인입니다. SQL 웨어하우스와 AI Runtime은 같은 서버리스 인프라를 쓰는 별도 기능으로 소개됩니다.

### 2.2 환경과 환경 버전

서버리스 노트북과 Job은 환경(Environment)에 따라 실행됩니다. 환경은 다음으로 구성됩니다.

- **기본 환경(Base environment)**: Python과 Scala 런타임 버전, 미리 설치된 라이브러리를 정합니다.
- **환경 버전(Environment version)**: 기본 환경의 버전 번호입니다. 문서에 따르면 각 환경 버전은 특정 Python 버전과 버전이 고정된 Python 패키지 세트를 포함합니다.
- **의존성(Dependencies)**: 사용자가 추가로 설치하는 패키지입니다.

문서는 기본 환경의 종류를 다음과 같이 나눕니다.

| 기본 환경 | 설명 (문서 원문 요약) |
|---|---|
| Standard | 기본 서버리스 기본 환경. Databricks 제공 라이브러리 포함 |
| ML | Databricks Runtime for Machine Learning의 Python과 시스템 패키지 포함 |
| AI | GPU 가속기를 선택했을 때만 표시 |
| More | 이전 버전의 Standard·ML·AI와 사용자 정의(Custom, YAML 파일) |
| 워크스페이스 환경 | 관리자가 구성 |

> **참고** 기준일 현재 최신 환경 버전은 **6** 입니다. 2026년 9월 3일 출시, 지원 종료 2029년 9월 3일, Python 3.12.3, Databricks Connect 19이며 CPU와 AI Runtime 변형이 있습니다. 일부 기능(예: Unity Catalog Python UDF의 일부 기능, 서버리스에서 세션 범위 Scala UDF의 시크릿 접근)은 환경 버전 6 이상을 요구합니다. 버전별 구성은 [서버리스 환경 버전 릴리즈 노트](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)에서 확인합니다.

#### 노트북에서 환경 선택

문서가 설명한 절차는 다음과 같습니다.

1. 노트북 오른쪽의 **Environment** 사이드 패널을 엽니다.
2. **Base environment** 에서 값을 고릅니다.
3. **Apply** 를 누릅니다.

의존성은 같은 패널의 **Dependencies** 아래에서 설치하고 **Apply** 를 누릅니다. 환경은 캐시되므로 노트북을 다시 열어도 의존성을 다시 설치하지 않습니다. 캐시를 지우고 다시 설치하려면 **Reset to defaults** 를 씁니다.

> **주의** 문서는 서버리스 노트북에 PySpark나 PySpark를 의존성으로 가진 라이브러리를 설치하지 말라고 경고합니다. 서버리스 노트북은 Spark 세션을 이미 제공하므로 PySpark를 따로 설치하면 충돌할 수 있습니다.

#### Job에서 환경 선택

Job에서는 **Configure environment** 대화상자의 **Base environment** 드롭다운에서 고릅니다. 워크스페이스에 기본 환경 미리보기가 없으면 같은 자리에 **Environment version** 드롭다운이 나타납니다. 문서 설명에 따르면 Job 태스크는 환경 버전의 기본 설치 라이브러리를 상속합니다.

> **참고** 관리형 기본 환경을 Job에 선택하는 기능은 문서에 Beta로 표기되어 있습니다. 2026년 10월 22일 릴리즈 노트는 `pyproject.toml`로 서버리스 Job 환경을 만드는 기능도 Beta로 발표했습니다.

### 2.3 노트북에서 서버리스 쓰기

서버리스 노트북을 쓰려면 워크스페이스가 Unity Catalog에 연결되어 있어야 합니다. 문서에 따르면 서버리스 대화형 컴퓨트가 켜져 있으면 워크스페이스의 모든 사용자가 노트북용 서버리스에 접근할 수 있고, 별도 권한은 필요하지 않습니다.

- **수동 연결**: 노트북 상단의 컴퓨트 드롭다운에서 **Serverless** 를 고릅니다.
- **자동 연결**: 새 노트북은 다른 리소스를 고르지 않은 상태에서 코드를 실행하면 서버리스가 기본으로 선택됩니다.
- **Git 폴더와 번들**: Shared Serverless(Beta)로 `pyproject.toml`에서 정의한 컴퓨트와 환경을 여러 파일이 함께 쓸 수 있습니다.

서버리스 노트북에서 지원하는 기능의 예는 다음과 같습니다.

| 기능 | 상태 | 설명 |
|---|---|---|
| 쿼리 인사이트(Query insights) | 문서 명시 없음 | 실행 후 **See performance** 에서 쿼리 메트릭과 쿼리 프로파일 확인 |
| 쿼리 기록(Query history) | 문서 명시 없음 | 서버리스에서 실행한 모든 쿼리가 워크스페이스 쿼리 기록 페이지에 남습니다 |

노트북 세션의 실행 제한 시간은 기본 2.5시간(9,000초)입니다. 제한을 넘는 쿼리는 취소됩니다. 관리자는 **Settings** > **Compute** 에서 워크스페이스 기본값을 바꿀 수 있고, 노트북은 `spark.databricks.execution.timeout` 설정으로 덮어쓸 수 있습니다.

```python
# 노트북 세션의 쿼리 실행 제한을 설정합니다 (단위: 초)
# 서버리스에서 지원하는 Spark 설정만 세션 단위로 지정할 수 있습니다.
spark.conf.set("spark.databricks.execution.timeout", "3600")
```

> **주의** 서버리스는 Spark 설정을 전부 허용하지 않습니다. 문서는 "Databricks allows setting only specific Spark configuration parameters"라고 설명하고, 허용 목록에 없는 설정은 세션 수준에서만 지정할 수 있다고 안내합니다. 설정이 적용되지 않으면 제약 페이지의 Spark 설정 항목을 확인하십시오.

### 2.4 Job에서 서버리스 쓰기

Job 작업 유형이 서버리스를 지원하면 Job 생성 시 서버리스 컴퓨트가 기본으로 선택됩니다. 기존 Job은 Job 상세 창의 **Compute** 설정에서 서버리스로 바꿀 수 있습니다. 사용 정책(Usage policy)이 하나만 할당된 사용자라면 그 정책이 새 Job에 자동 선택됩니다.

문서 기준 Job 설정 요점은 다음과 같습니다.

| 항목 | 문서 설명 (요약) |
|---|---|
| 자동 최적화(Auto-optimization) | 기본으로 켜져 있으며, 문서는 켜 두기를 권장합니다 |
| 고메모리(High memory) | 노트북 태스크 유형에서만 쓸 수 있습니다. Public Preview |
| Spark 설정 | 허용된 일부 파라미터만 지정할 수 있고, 세션 수준에서만 적용됩니다 |
| 사용 정책(Usage policy) | 한 개만 할당되면 자동 선택. Public Preview |

Job 실행 시간의 상한은 7일입니다. 이 한도를 넘는 실행은 종료되며 재시도하지 않습니다. 상한 값은 [서버리스 제약 페이지](serverless-limitations.md)에서 확인한 값입니다.

### 2.5 성능 모드 (Performance mode)

서버리스 Job은 성능 모드를 고를 수 있습니다. 문서 설명은 다음과 같습니다.

| 모드 | 문서 설명 (요약) | 시작 지연 |
|---|---|---|
| Standard | 컴퓨트 사용량을 줄여 비용을 낮춥니다. 시작 지연 4~6분을 감수할 수 있는 워크로드에 맞습니다 | 4~6분 (문서 명시) |
| Performance optimized | 시간에 민감한 워크로드용으로 Job이 더 빨리 시작하고 더 빨리 실행됩니다 | 문서에 수치 없음 |

두 모드는 같은 SKU를 쓰지만, Standard 모드는 DBU를 더 적게 소비한다고 문서가 설명합니다. 이 설정은 Job 안의 서버리스 태스크에만 영향을 주며, 서버리스 태스크가 최소 한 개 있어야 합니다. 기본 모드는 문서에 명시되어 있지 않습니다.

2026년 9월 11일 릴리즈 노트는 Jobs API의 일회성 실행(one-time run)에도 Standard 성능 모드를 쓸 수 있다고 발표했습니다. 2026년 8월 10일 릴리즈 노트는 연속 파이프라인을 연속 Job(continuous jobs)으로 오케스트레이션하는 기능을 서버리스 Standard 성능 모드와 함께 소개했습니다.

> **주의** Job에서 대량 메모리를 쓰거나 태스크 수가 많으면 시작 시간이 길어질 수 있다고 문서가 경고합니다. 시작 지연이 허용되지 않는 스케줄 Job이라면 Performance optimized 모드를 검토하십시오.

## 3. 어떻게 쓰는가 (Python 예시)

서버리스 노트북에서 쓰는 가장 기본적인 패턴입니다. 세션이 Spark Connect를 쓰므로 `spark` 객체로 바로 DataFrame을 만듭니다.

```python
# 서버리스 노트북 예시: 테이블 읽기, 변환, 저장
# 카탈로그·스키마·테이블 이름은 워크스페이스 환경에 맞게 바꾸십시오.
from pyspark.sql import functions as F

source = spark.table("main.sales.orders")  # Unity Catalog 3단계 이름

daily = (
    source
    .where(F.col("order_status") == "COMPLETED")
    .groupBy(F.to_date("order_ts").alias("order_date"))
    .agg(F.sum("amount").alias("total_amount"))
)

daily.write.mode("overwrite").saveAsTable("main.sales.daily_totals")
```

Job으로 옮길 때는 같은 코드를 노트북 태스크로 등록하고, 작업 설정에서 서버리스와 환경 버전을 고르면 됩니다. 노트북이 쓰는 라이브러리는 환경 의존성으로 옮겨야 Job 실행에서도 같은 패키지가 보입니다.

## 4. 트레이드오프

| 항목 | 장점 | 한계 |
|---|---|---|
| 시작 속도 | 노트북은 자동 연결, 빠른 시작 | Job Standard 모드는 4~6분 시작 지연 |
| 관리 부담 | 클러스터·런타임 관리 없음 | 환경 버전과 기본 환경 범위 안에서만 설정 |
| 설정 자유도 | 허용된 Spark 설정 | 컴퓨트 범위 라이브러리, init 스크립트, 인스턴스 풀 불가 |
| 기능 상태 | GA 기능이 많음 | 고메모리, 사용 정책, AI Runtime, 일부 Job 기능은 Public Preview 또는 Beta |
| 비용 구조 | DBU 중심 청구 | 사용 내역은 청구 시스템 테이블에 최대 24시간 지연 후 반영 |

> **참고** 문서는 서버리스 사용 내역이 청구 가능 사용 시스템 테이블(billable usage system table)에 최대 24시간 뒤에 나타날 수 있다고 설명합니다. 실시간 비용 점검에는 맞지 않습니다.

## 5. 주의사항

- **환경 버전을 고정해서 기록하십시오.** 노트북은 환경 설정이 노트북 메타데이터에 남습니다. 문서가 `environment_version = "5"` 같은 형태의 예시를 보여 줍니다. 팀 공유 전에 버전과 의존성 목록을 저장소에 함께 두면 재현이 쉽습니다.
- **Python 패키지는 환경의 Dependencies에서 설치하십시오.** 노트북 안에서 임의로 패키지를 설치하면 같은 환경을 다른 노트북이나 Job이 재현하기 어렵습니다. 설치 절차는 문서의 **Dependencies** 절차를 따르십시오.
- **상태 라벨을 확인하십시오.** 노트북 기능과 Job 기능이 같은 상태를 갖지 않습니다. 운영 Job에 쓰기 전에 기능별 상태를 봅니다.
- **사용 정책과 태깅.** 문서는 서버리스 노트북에서 노트북 태그를 지원하지 않으며, 태깅은 서버리스 사용 정책으로 하라고 안내합니다.
- **Unity Catalog 전제.** 레거시 워크스페이스는 Unity Catalog를 활성화하기 전까지 서버리스 컴퓨트를 쓸 수 없습니다.

## 참고 문서

- [Serverless compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/)
- [Serverless compute limitations (AWS)](https://docs.databricks.com/aws/en/compute/serverless/limitations)
- [Serverless notebooks (AWS)](https://docs.databricks.com/aws/en/compute/serverless/notebooks)
- [서버리스 Job 실행 (AWS)](https://docs.databricks.com/aws/en/jobs/run-serverless-jobs)
- [서버리스 환경 의존성 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/dependencies)
- [서버리스 릴리즈 노트 (AWS)](https://docs.databricks.com/aws/en/release-notes/serverless/)
- [2026년 9월 릴리즈 노트 (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [2026년 10월 릴리즈 노트 (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
- [Serverless environment versions](https://docs.databricks.com/aws/en/release-notes/serverless/environment-version/)
