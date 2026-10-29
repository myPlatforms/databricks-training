# 서버리스 제약과 지원 기능

> 기준일: 2026-10-28 · 근거: 공식 문서

서버리스 컴퓨트는 편리한 만큼 클래식 컴퓨트와 다른 제약이 있습니다. 같은 노트북 코드라도 서버리스에서 실패하거나 결과가 달라질 수 있습니다. 이 페이지는 공식 서버리스 제약 목록을 영역별로 정리하고, DataFrame 캐싱(Public Preview)과 데이터 소스 지원 범위를 다룹니다. 옮기기 전에 이 목록을 먼저 대조하는 것을 권장합니다.

## 1. 왜 필요한가

서버리스는 Databricks가 런타임을 관리하므로 사용자가 바꿀 수 있는 설정 범위가 좁습니다. 그 결과 다음 문제가 생깁니다.

| 상황 | 서버리스에서 생기는 문제 |
|---|---|
| 클러스터 설정 스크립트에 의존하는 코드 | init 스크립트와 컴퓨트 범위 환경 변수를 쓸 수 없습니다 |
| RDD 기반 코드 | Spark RDD API를 지원하지 않습니다 |
| 로컬 파일 경로 가정 | 작업 디렉터리가 보장되지 않아 상대 경로가 실패할 수 있습니다 |
| 전역 임시 뷰 | 지원하지 않습니다 |
| 서버 로그와 Spark UI 의존 | Spark UI와 Spark 로그를 쓸 수 없고, 쿼리 프로파일을 씁니다 |

이 목록을 미리 알면 이관 작업에서 실패 원인을 빨리 찾을 수 있습니다.

## 2. 어떻게 동작하는가

### 2.1 언어와 API

| 항목 | 제약 (문서 원문 요약) |
|---|---|
| R | 지원하지 않습니다 |
| Scala (노트북) | 노트북에서 지원하지 않습니다. Job의 JAR 태스크는 지원합니다 |
| Spark API | Spark Connect API만 동작합니다. Spark RDD API는 지원하지 않습니다 |
| 분석 시점 | Spark Connect는 분석과 이름 해석을 실행 시점으로 미루므로 코드 동작이 달라질 수 있습니다 |
| ANSI 모드 | 기본으로 켜져 있습니다. 잘못된 캐스트, 오버플로, 잘못된 입력은 NULL을 반환하지 않고 런타임 오류를 냅니다 |
| 세션 시간대 | 기본값은 `Etc/UTC`이며 `spark.sql.session.timeZone`으로 바꿀 수 있습니다 |
| 로컬 데이터 | `spark.createDataFrame`에 넘기는 로컬 데이터의 행 크기는 128 MB를 넘을 수 없습니다 |

> **주의** ANSI 모드가 기본으로 켜져 있으므로, 클래식에서 조용히 NULL로 넘어가던 캐스트가 서버리스에서는 오류가 됩니다. 이관 전에 `CAST`와 산술 연산의 입력 데이터를 점검하십시오.

### 2.2 데이터 접근과 저장소

- **외부 데이터 소스**: Unity Catalog가 필요하며, 클라우드 스토리지는 외부 위치(External location)를 씁니다.
- **DBFS**: 접근이 제한됩니다. 볼륨(Volume)이나 워크스페이스 파일을 쓰십시오.
- **작업 디렉터리**: 보장되지 않습니다. 상대 경로 파일 접근과 상대 경로 Python import가 실패할 수 있으므로 절대 경로를 쓰십시오.
- **Maven 좌표**: 지원하지 않습니다.
- **DBFS 마운트**: AWS 인스턴스 프로파일을 쓰는 마운트는 지원하지 않습니다.
- **전역 임시 뷰**: 지원하지 않습니다. 세션 임시 뷰나 임시 테이블을 쓰십시오.

```python
# 상대 경로 대신 볼륨의 절대 경로를 씁니다.
# 볼륨 경로는 워크스페이스 환경에 맞게 바꾸십시오.
df = spark.read.csv("/Volumes/main/raw/landing/orders.csv", header=True)
```

### 2.3 UDF와 사용자 정의 코드

| 항목 | 제약 |
|---|---|
| 인터넷 접근 | UDF가 인터넷에 접근할 수 없으므로 `CREATE FUNCTION (External)`을 지원하지 않습니다 |
| 메모리 | UDF, `map`, `mapPartitions` 같은 사용자 정의 코드는 메모리 사용량이 1 GB를 넘을 수 없습니다 |
| 고차 함수 | Scala UDF는 고차 함수(higher-order function) 안에서 쓸 수 없습니다 |

### 2.4 UI와 로그

- Spark UI를 쓸 수 없습니다. 대신 **쿼리 프로파일(Query profile)** 을 씁니다.
- Spark 로그를 쓸 수 없습니다. 클라이언트 측 애플리케이션 로그만 접근할 수 있습니다.

### 2.5 네트워크와 워크스페이스 접근

- **워크스페이스 간 접근**: 같은 리전 안에서만 동작하며, 대상 워크스페이스에 IP 액세스 리스트나 프런트엔드 PrivateLink가 없어야 합니다.
- **Databricks Container Services**: 지원하지 않습니다.
- **IPv6 전용 리소스**: 접근할 수 없습니다. IPv4가 필요합니다.

> **참고** 2026년 8월 13일 릴리즈 노트는 서버리스 워크스페이스 간 접근(Cross-workspace access for serverless)을 Beta로 발표했습니다. 위 제약 문구는 제약 페이지의 현재 표현입니다. 기능 상태는 Beta이므로 운영 적용 전 원문을 다시 확인하십시오.

### 2.6 스트리밍

| 트리거 | 상태 |
|---|---|
| `Trigger.AvailableNow()` | 지원. 문서가 권장 |
| `Trigger.Once()` | 지원하지만 문서가 Deprecated로 표기하고 권장하지 않음 |
| `Trigger.ProcessingTime(interval)` | 지원하지 않음 |
| `Trigger.Continuous(interval)` | 지원하지 않음 |
| 기본 트리거 `Trigger.ProcessingTime("0 seconds")` | 지원하지 않음. 지원되는 트리거를 명시적으로 지정해야 합니다 |

지원하지 않는 트리거를 쓰면 `INFINITE_STREAMING_TRIGGER_NOT_SUPPORTED` 오류가 납니다. 파이프라인의 처리 모드(processing mode)는 이 트리거 제한에서 예외입니다. 문서는 Lakeflow 파이프라인 처리 모드는 트리거 제한과 무관하다고 설명합니다.

```python
# 서버리스 스트리밍: 지원되는 AvailableNow 트리거를 명시합니다.
query = (
    stream_df.writeStream
    .trigger(availableNow=True)
    .option("checkpointLocation", "/Volumes/main/raw/checkpoints/orders")
    .toTable("main.sales.orders_bronze")
)
query.awaitTermination()
```

> **주의** 체크포인트 경로는 절대 경로 볼륨을 쓰십시오. 작업 디렉터리 기반 경로는 서버리스에서 보장되지 않습니다.

### 2.7 노트북 제약

- 노트북 태스크는 Scala와 R을 지원하지 않습니다.
- 노트북의 JAR 라이브러리는 지원하지 않습니다. Job의 JAR 태스크는 지원합니다.
- 노트북 범위 라이브러리는 개발 세션 사이에서 캐시되지 않습니다.
- 공유 노트북에서 TEMP 테이블과 뷰를 사용자 간에 공유할 수 없습니다.
- DataFrame 자동 완성과 변수 탐색기(Variable Explorer)를 지원하지 않습니다.
- 소스 형식으로 저장한 노트북은 서버리스 메타데이터를 제대로 담지 못할 수 있습니다. 기본 형식은 `.ipynb`입니다.
- 노트북 태그를 지원하지 않습니다. 태깅은 서버리스 사용 정책을 씁니다.

### 2.8 Job 제약

- 작업 로그가 태스크 실행별로 분리되지 않습니다. 여러 태스크의 출력이 한 로그에 섞입니다.
- 노트북 태스크에는 태스크 범위 라이브러리를 쓸 수 없습니다. 노트북 범위 라이브러리를 쓰십시오.
- 기본적으로 쿼리 실행 시간 제한이 없습니다. `spark.databricks.execution.timeout`으로 설정할 수 있습니다.
- 최대 실행 시간은 7일입니다. 이를 넘는 실행은 종료되며 재시도하지 않습니다.

> **참고** 노트북 세션의 기본 실행 제한은 2.5시간이고, Job은 기본 쿼리 시간 제한이 없다고 각각 다른 페이지에 적혀 있습니다. 두 값은 적용 범위가 다르므로(노트북 세션 대 Job 실행) 서로 충돌하는 설정은 아닌 것으로 보았습니다. 실제 값은 워크스페이스 설정에서 확인하십시오.

### 2.9 컴퓨트 범위 제약

다음은 서버리스에서 지원하지 않습니다.

- 컴퓨트 정책(Compute policies)
- 컴퓨트 범위 init 스크립트
- 컴퓨트 범위 라이브러리(사용자 정의 데이터 소스와 Spark 확장 포함)
- 인스턴스 풀(Instance pools)
- 컴퓨트 이벤트 로그
- 컴퓨트 범위 환경 변수

대부분의 Apache Spark 설정도 지원하지 않습니다. 허용된 목록에 있는 설정만 씁니다. 작업 수준 환경 변수 기능(job-level environment variables)은 Beta입니다.

## 3. 캐싱 (DataFrame caching)

### 3.1 상태와 요구 사항

DataFrame 캐싱은 서버리스에서 **Public Preview** 상태입니다. 2026년 10월 23일 릴리즈 노트가 발표했습니다. 문서 요구 사항은 다음과 같습니다.

| 항목 | 요구 사항 |
|---|---|
| 워크스페이스 설정 | 기본으로 켜져 있습니다. 관리자가 **Previews** 페이지에서 끌 수 있습니다 |
| 보안 프로필 | 컴플라이언스 보안 프로필(compliance security profile)이 켜져 있으면 사용할 수 없습니다 |
| 환경 버전 | 노트북과 Job은 환경 버전 5 이상 |
| Databricks Connect for Python | 18.1.8 이상 |
| Databricks Connect for Scala | 18.1.5 이상 |
| 리전 | AWS GovCloud와 AWS GovCloud DoD에서는 지원하지 않습니다 |

오래된 클라이언트는 `CACHE_REQUIRES_NEWER_CLIENT_ON_SERVERLESS_GC` 오류를 냅니다.

### 3.2 지원 범위

| 기능 | 지원 여부 |
|---|---|
| `df.cache()`, `df.persist()` | 지원. 즉시 계산하여 세션 스냅샷으로 저장 |
| 캐시된 DataFrame에서 파생된 DataFrame (`select`, `filter`, `groupBy`, `join`) | 지원. 연쇄 파생 포함 |
| `df.unpersist()` | 지원. 스냅샷을 조기에 해제 |
| `df.storageLevel` | 캐시 상태 확인용으로 지원 |
| `CACHE TABLE`, `spark.catalog` 테이블 캐시 메서드 | 지원하지 않음 |
| `df.checkpoint()`, `spark.catalog.cacheTable()`, `CLEAR CACHE` 등 | 지원하지 않음 (예외 발생) |

스냅샷은 세션 전용이며 세션이 끝날 때까지 유지되고, 최대 7일을 넘을 수 없습니다.

```python
# 여러 집계에서 같은 DataFrame을 반복해서 쓸 때 캐시를 씁니다.
orders = (
    spark.table("main.sales.orders")
    .where("order_status = 'COMPLETED'")
    .cache()          # 호출 즉시 계산되어 세션 스냅샷이 만들어집니다
)

revenue_by_region = orders.groupBy("region").sum("amount")
orders_by_day = orders.groupBy("order_date").count()

revenue_by_region.write.mode("overwrite").saveAsTable("main.sales.revenue_by_region")
orders_by_day.write.mode("overwrite").saveAsTable("main.sales.orders_by_day")

orders.unpersist()    # 더 이상 필요 없으면 해제합니다
```

### 3.3 캐시의 제한

- **컬럼 이름과 타입**: 중복 컬럼 이름, 공백이나 `,;{}()=`가 들어간 컬럼 이름, interval 컬럼, 배열·맵·구조체(NULL 타입 값 포함) 컬럼은 캐시할 수 없습니다. 이름을 바꾸거나 캐스트한 뒤 캐시하십시오.
- **원본 DataFrame의 컬럼 참조**: 캐시 후 원본 DataFrame으로 컬럼을 참조하면 `CANNOT_RESOLVE_DATAFRAME_COLUMN` 오류가 납니다. 캐시된 DataFrame 자신의 컬럼을 쓰십시오.
- **같은 원본 쿼리로 새로 만든 DataFrame**: 캐시를 쓰지 않습니다.
- **`persist()`의 저장 수준**: 저장 수준 인자를 무시합니다. `unpersist()`의 `blocking` 인자도 무시합니다.
- **`information_schema`**: 세션이 많은 상태에서 `information_schema.volumes`와 `information_schema.schemata` 조회가 느려지거나 시간 초과가 날 수 있습니다. `information_schema.tables`는 영향이 없다고 문서가 설명합니다.

> **주의** 캐시는 같은 세션 안에서만 유효합니다. Job의 태스크가 나뉘어 있으면 태스크 사이에서 캐시를 공유하지 않습니다. 태스크 간 중간 결과는 테이블로 저장하십시오.

## 4. 데이터 소스 지원

문서의 서버리스 데이터 소스 목록은 쓰기(Write/DML)와 읽기로 나뉩니다.

| 구분 | 지원 소스 (문서 목록) |
|---|---|
| 쓰기·DML | CSV, JSON, AVRO, DELTA, KAFKA, PARQUET, ORC, TEXT, UNITY_CATALOG, BINARYFILE, XML, SIMPLESCAN, ICEBERG |
| 읽기 추가 (Lakehouse Federation 등) | MYSQL, POSTGRESQL, SQLSERVER, REDSHIFT, SNOWFLAKE, SQLDW, DATABRICKS, BIGQUERY, ORACLE, SALESFORCE, SALESFORCE_DATA_CLOUD, TERADATA, WORKDAY_RAAS, MONGODB |

커스텀 데이터 소스는 지원하지 않습니다. 외부 DB를 읽을 때는 Lakehouse Federation 경로를 씁니다.

Hive SerDe 테이블은 지원하지 않습니다. `LOAD DATA`로 Hive SerDe 테이블에 적재하면 예외가 납니다. Hive 변수와 `${var}` 설정 참조도 지원하지 않으므로 `DECLARE VARIABLE`, `SET VARIABLE`, 세션 변수, 파라미터 마커, `IDENTIFIER` 절을 쓰십시오.

## 5. 트레이드오프

| 상황 | 판단 |
|---|---|
| 표준 Spark DataFrame과 SQL 중심 워크로드 | 서버리스가 잘 맞습니다 |
| RDD, R, Scala 노트북, GPU, 컴퓨트 범위 라이브러리 | 클래식 Dedicated 또는 Standard로 이동 |
| 세션 전반에서 캐시를 크게 쓰는 대화형 분석 | Public Preview 캐시를 쓰거나, 중간 결과를 테이블로 저장 |
| 스트리밍 처리 시간 기반 트리거(ProcessingTime) | 서버리스에서 지원하지 않으므로 AvailableNow로 바꾸거나 클래식 사용 |

## 6. 주의사항

- **이관 전에 점검 목록을 만드십시오.** 위 목록에서 기존 코드가 걸리는 항목을 먼저 표시합니다.
- **절대 경로와 볼륨을 쓰십시오.** 작업 디렉터리와 DBFS 의존 코드는 서버리스에서 깨지기 쉽습니다.
- **Spark UI 대신 쿼리 프로파일을 쓰십시오.** 튜닝 절차를 그에 맞게 바꿉니다.
- **Public Preview 기능은 운영 전 검증하십시오.** DataFrame 캐싱과 Job 관련 기능은 Preview 또는 Beta입니다.
- **환경 버전 5 이상을 쓰십시오.** 캐싱과 프로젝트 환경 등 일부 기능은 버전 요구가 있습니다.

## 참고 문서

- [Serverless compute limitations (AWS)](https://docs.databricks.com/aws/en/compute/serverless/limitations)
- [DataFrame caching on serverless compute (AWS)](https://docs.databricks.com/aws/en/compute/serverless/dataframe-cache)
- [Serverless compute 개요 (AWS)](https://docs.databricks.com/aws/en/compute/serverless/)
- [2026년 10월 릴리즈 노트 (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
- [2026년 8월 릴리즈 노트 (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
