# 파이프라인 이벤트 로그

> 기준일: 2026-10-29 · 근거: 공식 문서

## 한눈에 보기

파이프라인 이벤트 로그(pipeline event log)는 파이프라인 한 개의 모든 이벤트를 담은 Delta 테이블입니다. 감사 로그, 데이터 품질 검사, 파이프라인 진행 상황, 데이터 리니지 정보가 들어 있으며, 파이프라인 상태를 추적하고 모니터링하는 기본 자료입니다. 공식 문서는 리전 단위로 모든 파이프라인의 이벤트를 조회할 때는 `pipeline_events` 시스템 테이블(Beta)을 권장합니다. 이 시스템 테이블은 리전 안의 모든 워크스페이스 파이프라인 이벤트를 담습니다.

## 왜 필요한가

파이프라인이 실패하거나 결과가 이상할 때 확인할 방법이 없으면 원인을 찾기 어렵습니다. 이벤트 로그는 다음 질문에 답합니다.

- 어느 흐름이 언제 실패했고 상태는 무엇인가 (`flow_progress`)
- 어떤 업데이트가 완료됐고 어디서 취소됐는가 (`update_progress`)
- 데이터 품질 규칙이 몇 건 위반됐는가 (expectations 지표)

공식 문서는 공식 문서는 목록 화면, 모니터링 UI, 이벤트 로그 SQL의 세 층으로 모니터링을 나눕니다.

## 어떻게 동작하는가

### 저장 위치

- 기본적으로 파이프라인의 기본 카탈로그와 스키마 안에 **숨겨진 Delta 테이블** 로 저장됩니다.
- 테이블 이름은 `event_log_{pipeline_id}` 형식입니다. 파이프라인 ID의 대시(-)는 밑줄(_)로 바뀝니다.
- 테이블은 `system.information_schema.tables`에는 나오지만 Catalog Explorer에는 나오지 않습니다. 따라서 `event_log()` 함수로 조회합니다.
- 숨겨져 있어도 충분한 권한이 있는 사용자는 조회할 수 있습니다. 기본값에서는 파이프라인의 실행 사용자(run-as user)만 조회할 수 있습니다.
- 파이프라인의 **Advanced settings** 에서 이벤트 로그를 지정한 이름의 테이블로 게시(publish)할 수 있으며, 카탈로그와 스키마를 지정할 수 있습니다. 게시한 이벤트 로그 위치는 파이프라인의 Auto Loader 쿼리가 쓰는 스키마 위치 역할도 합니다.

게시 설정은 파이프라인 설정 JSON에서 다음 형태입니다.

```json
{
  "id": "ec2a0ff4-d2a5-4c8c-bf1d-d9f12f10e749",
  "name": "billing_pipeline",
  "event_log": {
    "catalog": "catalog_name",
    "schema": "schema_name",
    "name": "event_log_table_name"
  }
}
```

### 조회 방법

파이프라인 ID로 실행 사용자 권한에서 조회하는 기본 형태는 다음과 같습니다.

```sql
SELECT * FROM event_log(<pipelineId>);
```

반복 조회에는 뷰를 만들라고 문서가 권장합니다. 테이블을 직접 공유하면 일부 컴퓨트 설정에서 스키마 메타데이터가 노출될 수 있기 때문입니다.

```sql
CREATE VIEW event_log_raw
AS SELECT * FROM <catalog_name>.<schema_name>.<event_log_table_name>;
```

Unity Catalog에서는 뷰도 스트리밍 쿼리를 지원합니다.

```python
df = spark.readStream.table("event_log_raw")
```

### 이벤트 레코드의 구조

이벤트 한 건은 `id`, `sequence`, `origin`(`pipeline_id`, `pipeline_name`, `update_id`, 흐름 이벤트는 `flow_name` 등), `timestamp`, `message`, `level`, `event_type`, `details`(종류마다 구조가 다른 JSON, `details:flow_progress`처럼 경로로 꺼냄), `maturity_level` 열을 가집니다. 주요 `event_type`은 `flow_progress`(흐름 상태·처리 행 수·데이터 품질·백로그), `create_update`(업데이트 시작 기준), `update_progress`, `flow_definition`(리니지), `user_action`, `runtime_details`, `autoscale`·`cluster_resources`(classic 컴퓨트), `operation_progress`(Auto Loader), `stream_progress`입니다.

### 이벤트 상태 값

| 대상 | 값 |
|---|---|
| 흐름 진행 (`flow_progress`) | `STARTING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `EXCLUDED`, `SKIPPED`, `STOPPED`, `IDLE` |
| 업데이트 상태 (`update_progress`) | `COMPLETED`, `FAILED`, `CANCELED` |
| 오토스케일 (`autoscale`) | `RESIZING`, `SUCCEEDED`, `PARTIALLY_SUCCEEDED`, `FAILED` |
| 클러스터 리소스 (`cluster_resources`) | `CLUSTER_AT_DESIRED_SIZE`, `SCALE_UP_IN_PROGRESS_WAITING_FOR_EXECUTORS`, `BLOCKED_FROM_SCALING_DOWN_BY_CONFIGURATION` |
| Auto Loader 작업 (`operation_progress`) | `AUTO_LOADER_LISTING`, `AUTO_LOADER_BACKFILL` |

> **주의** 취소 철자가 흐름과 업데이트에서 다릅니다. 흐름 진행 상태는 `CANCELLED`, 업데이트 상태는 `CANCELED`입니다. 필터 조건을 쓸 때 두 값을 모두 넣거나, 실제 데이터에서 값을 한 번 확인하십시오.

## 어떻게 쓰는가

### 운영 확인 순서

운영 관점의 확인 순서는 다음과 같습니다.

1. 이벤트 로그를 뷰로 노출합니다(위 `CREATE VIEW` 예시).
2. 최근 업데이트의 흐름 진행 이벤트에서 `FAILED` 또는 `CANCELLED` 상태를 찾습니다.
3. 같은 `update_id`로 묶어 실패 흐름과 실행 시간을 확인합니다.
4. 데이터 품질 문제라면 expectations 지표를 확인합니다([Expectations와 AUTO CDC](pipelines-expectations-and-cdc.md)).
5. 비용은 이벤트 로그가 아니라 `system.billing.usage`에서 집계합니다(`usage_metadata.dlt_pipeline_id`로 필터). 파이프라인 알림은 파이프라인이나 잡에 직접 설정하고, 이벤트 훅으로 이벤트에 맞춘 동작을 정의할 수 있습니다.

### 원문 예제: 데이터 품질 지표

expectations의 통과·실패 건수는 `details:flow_progress.data_quality.expectations`에 있습니다. 문서가 제시한 최근 업데이트 집계 예제입니다.

```sql
WITH latest_update AS (
  SELECT
    origin.pipeline_id,
    origin.update_id AS latest_update_id
  FROM event_log_raw AS origin
  WHERE origin.event_type = 'create_update'
  ORDER BY timestamp DESC
  LIMIT 1 -- remove if you want all of the update_ids
)
SELECT
  row_expectations.dataset as dataset,
  row_expectations.name as expectation,
  SUM(row_expectations.passed_records) as passing_records,
  SUM(row_expectations.failed_records) as failing_records
FROM
  (
    SELECT
      explode(
        from_json(
          details:flow_progress:data_quality:expectations,
          "array<struct<name: string, dataset: string, passed_records: int, failed_records: int>>"
        )
      ) row_expectations
    FROM
      event_log_raw,
      latest_update
    WHERE
      event_type = 'flow_progress'
      AND origin.update_id = latest_update.latest_update_id
  )
GROUP BY
  row_expectations.dataset,
  row_expectations.name;
```

### 원문 예제: 리니지

`flow_definition` 이벤트에는 출력 데이터셋과 입력 데이터셋 목록이 들어 있습니다. 최근 업데이트의 리니지를 뽑는 원문 예제입니다.

```sql
with latest_update as (
  SELECT origin.update_id as id
    FROM event_log_raw
    WHERE event_type = 'create_update'
    ORDER BY timestamp DESC
    limit 1 -- remove if you want all of the update_ids
)
SELECT
  details:flow_definition.output_dataset as flow_name,
  details:flow_definition.input_datasets as input_flow_names,
  details:flow_definition.flow_type as flow_type,
  details:flow_definition.schema, -- the schema of the flow
  details:flow_definition -- overall flow_definition object
FROM event_log_raw inner join latest_update on origin.update_id = latest_update.id
WHERE details:flow_definition IS NOT NULL
ORDER BY timestamp;
```

### 원문 예제: 처리량과 백로그

백로그 크기는 `details:flow_progress.metrics.backlog_bytes`에 있습니다. 백로그가 쌓이는지 보면 스트리밍 지연 원인을 찾을 수 있습니다.

```sql
with latest_update as (
  SELECT origin.update_id as id
    FROM event_log_raw
    WHERE event_type = 'create_update'
    ORDER BY timestamp DESC
    limit 1 -- remove if you want all of the update_ids
)
SELECT
  timestamp,
  Double(details :flow_progress.metrics.backlog_bytes) as backlog
FROM
  event_log_raw,
  latest_update
WHERE
  event_type ='flow_progress'
  AND
  origin.update_id = latest_update.id;
```

백로그 지표는 데이터 소스 유형과 Runtime 버전에 따라 없을 수 있습니다.

흐름별 처리량은 `details:flow_progress.metrics`의 `num_output_rows`, `num_upserted_rows`, `num_deleted_rows`를 `TRY_CAST`로 꺼내 집계합니다(원문 "Query metrics for all flows in a pipeline" 예제).

## 트레이드오프

| 항목 | 파이프라인별 이벤트 로그 | `pipeline_events` 시스템 테이블 |
|---|---|---|
| 범위 | 파이프라인 한 개 | 리전 안의 모든 파이프라인 (모든 워크스페이스) |
| 상태 | 문서에 상태 라벨 없음 (기본 기능) | **Beta** (2026-08-31 릴리즈 노트) |
| 조회 | `event_log(<pipelineId>)` 또는 게시한 테이블 | 시스템 테이블 조인 |
| 권한 | 기본은 실행 사용자만 | 시스템 테이블 권한 정책 |

## 주의사항

- **삭제 금지**: 이벤트 로그 테이블, 상위 카탈로그, 스키마를 삭제하지 마십시오. 문서는 이후 파이프라인 업데이트가 실패할 수 있다고 경고합니다.
- **권한 노출과 실행 주체**: 이벤트 로그 테이블을 직접 공유하면 컴퓨트 설정에 따라 스키마 메타데이터가 노출될 수 있으니 뷰로 범위를 좁히십시오. 파이프라인은 소유자의 자격 증명으로 업데이트를 실행하므로, 소유자를 바꾸면 조회·실행 주체도 바뀝니다.
- **오토스케일 범위**: 오토스케일 이벤트와 클러스터 리소스 이벤트는 **enhanced autoscaling이 켜진 classic 컴퓨트** 의 파이프라인에만 해당합니다. 서버리스 컴퓨트에는 해당하지 않습니다.
- **Kafka·Kinesis 오프셋 절단**: Kafka, Kinesis 스트림과 Lakeflow Connect 쿼리 기반 커넥터의 오프셋 필드(`startOffset`, `endOffset`, `latestOffset`)는 잘릴 수 있습니다. 각 필드에 대응하는 `...Truncated` 불리언 필드로 표시됩니다.

## 참고 문서

- [Pipeline event log (monitor-event-logs)](https://docs.databricks.com/aws/en/ldp/monitor-event-logs)
- [Pipeline observability (observability)](https://docs.databricks.com/aws/en/ldp/observability)
- [Release notes, 2026년 8월 (pipeline_events 시스템 테이블 Beta)](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
