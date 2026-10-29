# Auto Loader

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Auto Loader는 클라우드 스토리지에 새로 도착하는 파일을 **증분으로** 읽는 Structured Streaming 소스입니다. 소스 이름은 `cloudFiles`이며, 입력 디렉터리 경로를 주면 새 파일을 감지해 처리합니다. 공식 문서는 Databricks가 Lakeflow 파이프라인에서 Auto Loader 사용을 권장한다고 명시합니다. 파이프라인에서는 스키마 위치와 체크포인트 위치를 직접 줄 필요가 없습니다.

## 왜 필요한가

파일을 수집하는 가장 단순한 방법은 디렉터리 전체를 매번 다시 읽는 것입니다. 이 방식에는 세 가지 문제가 있습니다.

- **확장성**: 파일이 수백만 개로 늘면 목록 조회 자체가 느려지고 비용이 커집니다.
- **중복과 누락**: 어떤 파일을 처리했는지 기록하지 않으면 재시작 때 중복 처리하거나 빠뜨립니다.
- **스키마 변경**: 원천 파일에 새 컬럼이 추가되면 쿼리가 깨집니다.

Auto Loader는 처리한 파일의 메타데이터를 체크포인트 위치의 RocksDB 키-값 저장소에 기록합니다. 문서는 이를 통해 **정확히 한 번(exactly-once) 처리** 와 장애 후 복구를 지원한다고 설명합니다.

## 어떻게 동작하는가

### 지원 소스

Amazon S3(`s3://`), ADLS(`abfss://`), Google Cloud Storage(`gs://`), Unity Catalog 볼륨(`/Volumes/`), Azure Blob Storage(`wasbs://`, 레거시)를 읽을 수 있습니다. 문서가 Azure Blob 경로를 "legacy"로 표기하므로 신규 설계에서는 다른 경로를 우선 검토하십시오.

### 파일 감지 모드

Auto Loader는 새 파일을 찾는 두 가지 방식을 제공합니다.

| 항목 | Directory listing (디렉터리 목록) | File notification (파일 이벤트) |
|---|---|---|
| 기본값 | 예. 문서상 기본 모드 | 아니오 |
| 동작 | 입력 디렉터리를 나열해 새 파일 탐색 | 클라우드 계정의 알림·큐 서비스를 사용 |
| 권한 | 스토리지 데이터 접근 권한만 필요 | Auto Loader가 서비스를 설정. 외부 위치에서 파일 이벤트를 켜면 추가 권한 불필요 (문서 명시) |
| 확장성 | 사전 순서(lexical ordering) 감지로 API 호출 감소 (DBR 9.1+) | 문서는 directory listing보다 "more performant and scalable"하다고 설명 |
| 클라우드 지원 | 모든 버전 | DBR 14.3 LTS 이상 (S3, ADLS, GCS). Azure Blob 미지원 |
| 문서 권장 | 소량·단순 원천 | "Databricks recommends file notification mode using file events instead of directory listing mode for most workloads" |

> **참고** 문서는 "Directory listing 모드에서 Trigger.ProcessingTime 같은 상시 트리거는 비용이 많이 든다"고 명시합니다. 상시 실행이 필요하면 파일 이벤트 모드를 쓰십시오.

모드는 스트림 재시작 사이에 바꿀 수 있으며, 바꿔도 정확히 한 번 처리가 유지된다고 문서가 설명합니다.

### 구성 요소

| 구성 요소 | 역할 |
|---|---|
| `cloudFiles` 소스 | 파일 감지와 읽기를 담당하는 Structured Streaming 소스 |
| 체크포인트 (`checkpointLocation`) | 처리 진행 상태와 발견한 파일 메타데이터(RocksDB) 저장 |
| 스키마 위치 (`cloudFiles.schemaLocation`) | 추론한 스키마 이력을 `_schemas` 디렉터리에 저장 |
| 파일 이벤트 (외부 위치) | 파일 생성 알림을 제공해 디렉터리 전체 목록 조회를 줄임 |

## 어떻게 쓰는가

### 기본 읽기와 쓰기

문서의 원문 예제를 옮긴 코드입니다. 파켓 파일을 읽어 대상 경로에 씁니다.

```python
(spark.readStream.format("cloudFiles")
  .option("cloudFiles.format", "parquet")
  # The schema location directory keeps track of your data schema over time
  .option("cloudFiles.schemaLocation", "<path-to-schema>")
  .load("<path-to-source-data>")
  .writeStream
  .option("checkpointLocation", "<path-to-checkpoint>")
  .start("<path-to-target>"))
```

JSON 파일을 읽어 한 번에 처리하고 종료하는 배치형 예제는 문서의 Structured Streaming 튜토리얼에 있습니다. 트리거는 `availableNow=True`를 사용합니다.

```python
file_path = "/databricks-datasets/structured-streaming/events"
checkpoint_path = "/tmp/ss-tutorial/_checkpoint"

raw_df = (spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.schemaLocation", checkpoint_path)
    .load(file_path))

transformed_df = raw_df.select(
    "*",
    col("_metadata.file_path").alias("source_file"),
    current_timestamp().alias("processing_time")
)

(transformed_df.writeStream
    .trigger(availableNow=True)
    .option("checkpointLocation", checkpoint_path)
    .option("path", "/tmp/ss-tutorial/")
    .start())
```

> **참고** 위 튜토리얼 예제는 `col`, `current_timestamp`를 `pyspark.sql.functions`에서 가져와야 합니다. 원문 코드 블록은 import를 생략했습니다.

### 스키마 추론과 진화

| 옵션 | 문서상 동작 |
|---|---|
| `cloudFiles.schemaLocation` | 지정하면 스키마 추론과 진화가 켜짐. `_schemas` 디렉터리에 이력 저장. 체크포인트와 같은 디렉터리로 지정 가능. 소스 위치마다 별도 체크포인트 필요 |
| `cloudFiles.inferColumnTypes` | 기본값에서 JSON, CSV, XML의 컬럼은 문자열로 추론. `true`로 설정하면 DataFrameReader 방식의 타입 추론 |
| `cloudFiles.schemaHints` | SQL 스키마 문법으로 특정 컬럼 타입을 강제. 예: `"tags map<string,string>, version int"`. 스키마를 직접 주지 않았을 때만 사용 |
| `cloudFiles.schemaEvolutionMode` | 아래 표 참조 |
| `_rescued_data` | 파싱하지 못한 값과 원본 파일 경로를 담는 JSON. 누락 컬럼, 타입 불일치, 대소문자 불일치 등이 원인 |

`cloudFiles.schemaEvolutionMode` 값은 다음과 같습니다.

| 값 | 동작 | 기본 여부 |
|---|---|---|
| `addNewColumns` | 새 컬럼이 추가되면 스트림이 `UnknownFieldException`으로 실패. 재시작하면 갱신된 스키마 적용 | 스키마를 주지 않았을 때 기본 |
| `addNewColumnsWithTypeWidening` | `addNewColumns`와 같되, 지원되는 타입 확장(예: `int`에서 `long`)도 반영. 지원하지 않는 변경은 rescued data로 이동 | 아님. Public Preview (DBR 16.4 이상) |
| `rescue` | 스키마는 진화하지 않음. 실패하지 않고 새 컬럼은 rescued data 컬럼에 기록 | 아님 |
| `failOnNewColumns` | 새 컬럼이 나오면 실패하고 스키마를 직접 고치거나 파일을 제거할 때까지 실패 상태 유지. 자동 갱신 없음 | 아님 |
| `none` | 스키마 진화 없음. 새 컬럼은 무시. `rescuedDataColumn`을 지정하면 rescued data로 보존 | 스키마를 제공했을 때 기본 |

> **참고** `addNewColumns`는 스키마를 직접 제공하면 허용되지 않지만, 스키마 힌트(`schemaHints`)로 주면 동작한다고 문서가 설명합니다.

Lakeflow 파이프라인에서는 스키마 위치와 체크포인트 정보를 Databricks가 자동으로 관리합니다. 문서는 파이프라인 안에서의 스키마 변경 처리 세부는 따로 설명하지 않습니다. 파이프라인이 아닌 일반 Auto Loader 스트림은 스키마 변경 후 자동 재시작이 가능하도록 Lakeflow Jobs로 실행하도록 문서가 권장합니다.

### 운영 설정

문서의 production 페이지 권장 사항은 다음과 같습니다.

- **파이프라인 우선**: 대부분의 운영 수집에는 Lakeflow 파이프라인을 쓰라고 권장합니다. `Trigger.AvailableNow`를 쓰는 배치 잡은 지연이 중요하지 않고 컴퓨트 비용 최소화가 우선일 때만 쓰라고 설명합니다.
- **감지 모드 선택**: 낮은 지연과 단순한 설정은 파일 이벤트, 매우 지연에 민감한 경우에만 classic 파일 알림을 씁니다.
- **주기 실행**: 파일 이벤트 스트림은 최소 7일에 한 번은 실행해 감지를 증분으로 유지하라고 권장합니다. 전체 디렉터리 목록 조회를 피하기 위해서입니다.
- **런타임**: 대용량·장기 스트림은 DBR 15.4 LTS 이상을 권장합니다. 시작 시 RocksDB 상태 다운로드를 기다리지 않게 하기 위해서입니다.
- **배치 크기**: `cloudFiles.maxFilesPerTrigger`(기본 1000, 하드 제한)와 `cloudFiles.maxBytesPerTrigger`(소프트 제한)로 마이크로배치 크기를 제한합니다.
- **파일 나이**: `cloudFiles.maxFileAge`의 최소값은 14일입니다. 문서는 너무 공격적으로 줄이면 중복이나 누락이 생길 수 있으며 예로 90일을 제시합니다.
- **정리**: `cloudFiles.cleanSource`로 처리한 원본을 `MOVE`(보관 위치로 이동) 또는 `DELETE`로 정리할 수 있습니다. `cloudFiles.cleanSource`는 DBR 16.4 LTS 이상에서 사용 가능하다고 문서가 명시합니다.
- **모니터링**: `cloud_files_state` 함수로 발견한 파일 상태를 확인하고, 스트리밍 쿼리 리스너 지표의 `numFilesOutstanding`, `numBytesOutstanding`, `approximateQueueSize`를 봅니다(파일 알림 모드).

## 트레이드오프

| 질문 | 답 |
|---|---|
| 파일이 적고 단순한가 | Directory listing으로 충분할 수 있음. 다만 문서는 파일 이벤트를 대부분의 워크로드에 권장 |
| 파일이 많거나 상시 실행인가 | 파일 이벤트 모드 |
| 스키마가 자주 바뀌는가 | `addNewColumns`(자동 갱신 후 재시작) 또는 `rescue`(실패 없이 보존). 운영 기준을 정해 고르십시오 |
| 파일을 읽은 뒤 원본을 지워야 하는가 | `cloudFiles.cleanSource`. 단 `foreachBatch`와 함께 쓸 때 주의 필요 |
| 파일이 아니라 SaaS API에서 가져오는가 | [Lakeflow Connect](lakeflow-connect.md)가 맞음 |

## 주의사항

- **체크포인트는 수명 주기 정책 밖에**: 문서는 체크포인트가 있는 위치에 클라우드 객체 수명 주기 정책(lifecycle policy)을 걸지 말라고 경고합니다. 정리되면 상태가 깨지고 처음부터 다시 읽게 됩니다.
- **체크포인트 공유 금지**: 쿼리마다 서로 다른 체크포인트 위치를 써야 합니다. 문서는 여러 쿼리가 같은 위치를 공유하지 말라고 명시합니다.
- **`cleanSource` MOVE 조건**: 원본과 대상이 같은 외부 위치, 볼륨, DBFS 마운트에 있어야 합니다.
- **`foreachBatch`와 정리**: `foreachBatch`에서는 배치 함수가 반환되는 순간 파일이 정리 후보가 됩니다. 배치 일부만 소비했더라도 그렇습니다. 문서는 DELETE 정리 전에 버킷 버전 관리를 안전장치로 켜라고 권장합니다.
- **백필 간격**: `cloudFiles.backfillInterval`은 classic 파일 알림에서 엄격한 완전성 SLA가 있을 때만 쓰고, 파일 이벤트에서는 쓰지 않습니다. 파일 이벤트는 자동으로 백필합니다.
- **스키마 위치 분리**: 소스마다 체크포인트와 스키마 위치를 따로 둡니다. 여러 소스가 같은 스키마 위치를 공유하면 혼선이 생깁니다.
- **Azure Blob**: 파일 이벤트 모드는 Azure Blob을 지원하지 않습니다. 이 장의 기능 가용성 표는 AWS 문서를 기준으로 합니다.

> **참고** 이 페이지의 수치(1000개, 14일, 50 GB 또는 1,000 파일 샘플링)는 공식 문서 원문 기준입니다. 워크로드에 맞게 조정하기 전 참고 문서에서 현재 값을 다시 확인하십시오.

## 참고 문서

- [What is Auto Loader?](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/)
- [Choose a file detection mode (file-detection-modes)](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/file-detection-modes)
- [Schema inference and evolution](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/schema)
- [Production considerations](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/production)
- [Structured Streaming tutorial](https://docs.databricks.com/aws/en/structured-streaming/tutorial)
- [Choose an ETL approach on Databricks](https://docs.databricks.com/aws/en/data-engineering/choose-etl-approach)
