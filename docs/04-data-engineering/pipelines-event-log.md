# 파이프라인 이벤트 로그

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

파이프라인 이벤트 로그(pipeline event log)는 파이프라인 한 개의 모든 이벤트를 담은 Delta 테이블입니다. 감사 로그, 데이터 품질 검사, 파이프라인 진행 상황, 데이터 리니지 정보가 들어 있으며, 파이프라인 상태를 추적하고 모니터링하는 기본 자료입니다. 공식 문서는 리전 단위로 모든 파이프라인의 이벤트를 조회할 때는 `pipeline_events` 시스템 테이블(Beta)을 권장합니다.

## 왜 필요한가

파이프라인이 실패하거나 결과가 이상할 때 확인할 방법이 없으면 원인을 찾기 어렵습니다. 이벤트 로그는 다음 질문에 답합니다.

- 어느 흐름이 언제 실패했고 상태는 무엇인가 (`flow_progress`)
- 어떤 업데이트가 완료됐고 어디서 취소됐는가 (`update_progress`)
- 데이터 품질 규칙이 몇 건 위반됐는가 (expectations 지표)
- 자동 확장(autoscale)으로 클러스터가 어떻게 바뀌었는가 (classic 컴퓨트에 한함)

## 어떻게 동작하는가

### 저장 위치

- 기본적으로 파이프라인의 기본 카탈로그와 스키마 안에 **숨겨진 Delta 테이블** 로 저장됩니다.
- 테이블 이름은 `event_log_{pipeline_id}` 형식입니다. 파이프라인 ID의 대시(-)는 밑줄(_)로 바뀝니다.
- 테이블은 `system.information_schema.tables`에는 나오지만 Catalog Explorer에는 나오지 않습니다. 따라서 `event_log()` 함수로 조회합니다.
- 기본값에서는 파이프라인의 실행 사용자(run-as user)만 조회할 수 있습니다.
- 파이프라인의 **Advanced settings** 에서 이벤트 로그를 지정한 이름의 테이블로 게시(publish)할 수 있으며, 카탈로그와 스키마를 지정할 수 있습니다.

### 조회 방법

```sql
SELECT * FROM event_log(<pipelineId>);
```

반복 조회를 편하게 하려면 뷰를 만들라고 문서가 권장합니다.

```sql
CREATE VIEW event_log_raw
AS SELECT * FROM <catalog_name>.<schema_name>.<event_log_table_name>;
```

뷰는 스트리밍 쿼리에도 쓸 수 있습니다. 예: `spark.readStream.table("event_log_raw")`.

### 주요 열

| 열 | 내용 |
|---|---|
| `event_type` | 이벤트 종류. 예: `flow_progress`, `create_update`, `update_progress`, `flow_definition`, `user_action`, `runtime_details`, `autoscale`, `cluster_resources`, `operation_progress`, `stream_progress` |
| `origin` | 식별자 묶음. `pipeline_id`, `pipeline_name`, `update_id`, `flow_name` 등 |
| `timestamp` | 이벤트 발생 시각 |
| `details` | 이벤트 종류마다 구조가 다른 JSON. `details:flow_progress`, `details:autoscale` 같은 경로로 꺼냄 |

### 이벤트 상태 값

문서 예제에 나온 상태 값입니다.

| 대상 | 값 |
|---|---|
| 흐름 진행 (`flow_progress`) | `STARTING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `EXCLUDED`, `SKIPPED`, `STOPPED`, `IDLE` |
| 업데이트 상태 | `COMPLETED`, `FAILED`, `CANCELED` (문서 예제에서 취소 철자가 두 가지로 나옴) |
| 오토스케일 (`autoscale`) | `RESIZING`, `SUCCEEDED`, `PARTIALLY_SUCCEEDED`, `FAILED` |
| 클러스터 리소스 (`cluster_resources`) | `CLUSTER_AT_DESIRED_SIZE`, `SCALE_UP_IN_PROGRESS_WAITING_FOR_EXECUTORS`, `BLOCKED_FROM_SCALING_DOWN_BY_CONFIGURATION` |
| Auto Loader 작업 | `AUTO_LOADER_LISTING`, `AUTO_LOADER_BACKFILL` |

> **참고** 업데이트 상태 `CANCELED`와 `CANCELLED`는 문서 예제 안에서 표기가 다릅니다. 필터 조건을 쓸 때 실제 데이터에서 값을 한 번 확인하십시오.

### 흐름 진행 이벤트 예시

흐름 단위 상태를 보려면 `event_type`과 `origin.flow_name`으로 걸러 `details`를 확인합니다. 아래는 열 이름을 사용한 조회 형태입니다. `<pipelineId>` 자리에 파이프라인 ID를 넣습니다.

```sql
SELECT
  timestamp,
  origin.flow_name,
  details
FROM event_log(<pipelineId>)
WHERE event_type = 'flow_progress'
ORDER BY timestamp DESC
LIMIT 100;
```

## 어떻게 쓰는가

운영 관점의 확인 순서는 다음과 같습니다.

1. 이벤트 로그를 뷰로 노출합니다(위 `CREATE VIEW` 예시).
2. 최근 업데이트의 흐름 진행 이벤트에서 `FAILED` 또는 `CANCELLED` 상태를 찾습니다.
3. 같은 `update_id`로 묶어 실패 흐름과 실행 시간을 확인합니다.
4. 데이터 품질 문제라면 expectations 지표를 확인합니다([Expectations와 AUTO CDC](pipelines-expectations-and-cdc.md)).
5. 비용은 이벤트 로그가 아니라 `system.billing.usage`에서 집계합니다(문서 명시).

## 트레이드오프

| 항목 | 파이프라인별 이벤트 로그 | `pipeline_events` 시스템 테이블 |
|---|---|---|
| 범위 | 파이프라인 한 개 | 리전 안의 모든 파이프라인 |
| 상태 | 문서에 상태 라벨 없음 (기본 기능) | **Beta** (2026-08-31 릴리즈 노트) |
| 조회 | `event_log(<pipelineId>)` | 시스템 테이블 조인 |
| 권한 | 기본은 실행 사용자만 | 시스템 테이블 권한 정책 |

## 주의사항

- **삭제 금지**: 이벤트 로그 테이블, 상위 카탈로그, 스키마를 삭제하지 마십시오. 문서는 이후 파이프라인 업데이트가 실패할 수 있다고 경고합니다.
- **지표 누락**: 일부 데이터셋은 데이터 품질 지표가 없을 수 있습니다.
- **백로그 지표**: 백로그 지표는 파이프라인의 데이터 소스 유형과 Databricks Runtime 버전에 따라 달라집니다.
- **오토스케일 범위**: 오토스케일 이벤트는 **enhanced autoscaling이 켜진 classic 컴퓨트** 의 파이프라인에만 해당합니다. 서버리스 컴퓨트에는 해당하지 않습니다.
- **스트림 진행 누락 필드**: `stream_progress` 이벤트는 `numInputRows`, `inputRowsPerSecond`, `processedRowsPerSecond`를 담지 않습니다. 이 값은 `StreamingQueryListener` 지표에 있습니다.
- **Kafka·Kinesis 오프셋 절단**: Kafka, Kinesis 스트림과 Lakeflow Connect 쿼리 기반 커넥터의 오프셋 필드는 잘릴 수 있습니다. `...Truncated` 불리언 필드로 표시됩니다.
- **레거시 게시 모드**: 레거시 게시 모드와 Hive 메타스토어 파이프라인은 이벤트 로그 동작이 다르며 별도 문서에 설명되어 있습니다.

## 참고 문서

- [Pipeline event log (monitor-event-logs)](https://docs.databricks.com/aws/en/ldp/monitor-event-logs)
- [Pipeline observability (observability)](https://docs.databricks.com/aws/en/ldp/observability)
- [Release notes, 2026년 8월 (pipeline_events 시스템 테이블 Beta)](https://docs.databricks.com/aws/en/release-notes/product/2026/august)
