# Expectations와 AUTO CDC

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

이 페이지는 Lakeflow 파이프라인에서 두 가지를 다룹니다. 첫째, **expectations** 는 레코드가 지켜야 할 품질 규칙을 선언하고 위반 시 동작(경고, 행 삭제, 업데이트 실패)을 고르는 기능입니다. 둘째, **AUTO CDC** 는 변경 데이터(insert, update, delete)를 대상 스트리밍 테이블에 반영해 SCD Type 1(덮어쓰기) 또는 SCD Type 2(이력 보존) 테이블을 만드는 기능입니다. 공식 문서는 `AUTO CDC`가 이전의 `APPLY CHANGES` API를 대체하며 구문도 같다고 설명합니다.

## 왜 필요한가

### 품질 규칙

원천 데이터의 잘못된 레코드를 방치하면 하위 집계가 조용히 틀립니다. 규칙을 파이프라인 안에 선언해 두면 다음이 가능합니다.

- 위반 레코드를 대상 테이블에 그대로 둘지, 제외할지, 업데이트 자체를 실패시킬지 명시
- 위반 건수를 데이터 품질 지표로 남겨 추적

### 변경 데이터 반영

원천 시스템이 "무엇이 바뀌었는지"를 행 단위 변경 로그로 주면, 대상 테이블에 올바르게 반영하는 로직을 직접 짜기 쉽지 않습니다. 순서가 뒤바뀐 이벤트, 삭제 이벤트, 이력 보존 요구가 겹치기 때문입니다. `AUTO CDC`는 키, 정렬 기준, 삭제 조건을 선언하면 이 로직을 처리합니다.

## Expectations

### 세 가지 동작

| 동작 | 기본값 | SQL 문법 | Python 문법 | 결과 |
|---|---|---|---|---|
| warn | 예 | `EXPECT` | `dp.expect` | 위반 레코드도 대상 테이블에 기록 |
| drop | 아니오 | `EXPECT ... ON VIOLATION DROP ROW` | `dp.expect_or_drop` | 위반 레코드를 쓰기 전에 제외. 제외 건수는 데이터셋 지표에 기록 |
| fail | 아니오 | `EXPECT ... ON VIOLATION FAIL UPDATE` | `dp.expect_or_fail` | 위반 레코드가 있으면 업데이트 중단. 재처리 전에 수동 조치 필요 |

문서는 "Retaining invalid records is the default behavior for expectations."라고 명시합니다. 즉 규칙을 쓰고도 `ON VIOLATION`을 생략하면 위반 레코드는 남습니다.

### 문법

SQL에서는 `CONSTRAINT` 절을 씁니다. 여러 규칙은 쉼표로 구분합니다.

```sql
CONSTRAINT <constraint-name> EXPECT ( <constraint-clause> )
```

Python에서는 데코레이터를 씁니다.

```python
@dp.expect(<constraint-name>, <constraint-clause>)
```

문서 예제를 그대로 옮긴 SQL 예시입니다.

```sql
-- warn: 위반 레코드도 유지
CONSTRAINT valid_timestamp EXPECT (timestamp > '2012-01-01')

-- drop: 위반 레코드 제외
CONSTRAINT valid_current_page EXPECT (current_page_id IS NOT NULL and current_page_title IS NOT NULL) ON VIOLATION DROP ROW

-- fail: 위반 시 업데이트 실패
CONSTRAINT valid_count EXPECT (count > 0) ON VIOLATION FAIL UPDATE
```

Python 예시는 다음과 같습니다.

```python
@dp.expect("valid timestamp", "timestamp > '2012-01-01'")
@dp.expect_or_drop("valid_current_page", "current_page_id IS NOT NULL AND current_page_title IS NOT NULL")
@dp.expect_or_fail("valid_count", "count > 0")
```

Python에서는 여러 규칙을 묶는 데코레이터 `expect_all`, `expect_all_or_drop`, `expect_all_or_fail`도 있습니다. 이들은 이름과 규칙을 담은 딕셔너리를 받습니다.

### 지표와 실패 메시지

- **지표**: `warn`과 `drop`은 추적 지표를 남깁니다. `fail`은 업데이트가 실패하므로 지표를 남기지 않는다고 문서가 설명합니다.
- **확인 위치**: 파이프라인 UI에서 데이터셋을 열고 오른쪽 사이드바의 **Data quality** 탭을 선택합니다. 독립형 파이프라인(Databricks SQL에서 만든 것)은 이 탭이 없으므로 이벤트 로그로 확인해야 합니다.
- **지표가 없을 수 있는 경우**: 규칙이 없을 때, 흐름이 지원하지 않는 연산자를 쓸 때, `pipelines.metrics.flowTimeReporter.enabled`가 설정되지 않았을 때입니다.
- **실패 메시지**: `fail` 규칙 위반 시 오류는 `[EXPECTATION_VIOLATION.VERBOSITY_ALL]`로 시작하고 위반된 규칙 이름을 포함합니다.

## AUTO CDC

### 두 가지 변형

| 변형 | 용도 |
|---|---|
| `AUTO CDC` | CDC 피드(변경 데이터 피드)가 있는 원천의 변경을 반영 |
| `AUTO CDC FROM SNAPSHOT` | CDC가 켜져 있지 않을 때, 순서가 있는 스냅샷을 비교해 변경을 계산 |

이름 표기는 다음과 같습니다. SQL은 `AUTO CDC INTO` 및 `CREATE FLOW` 안의 `AUTO CDC ... FROM SNAPSHOT`, Python은 `create_auto_cdc_flow()`와 `create_auto_cdc_from_snapshot_flow()`를 씁니다.

### 핵심 설정

| 설정 | SQL | Python |
|---|---|---|
| 키 | `KEYS (userId)` | `keys = ["userId"]` |
| 정렬 순서 | `SEQUENCE BY sequenceNum` | `sequence_by = col("sequenceNum")` |
| 삭제 조건 | `APPLY AS DELETE WHEN operation = "DELETE"` | `apply_as_deletes = expr("operation = 'DELETE'")` |
| 이력 방식 | `STORED AS SCD TYPE 2` | `stored_as_scd_type = "2"` |
| 제외 컬럼 | `COLUMNS * EXCEPT (operation, sequenceNum)` | `except_column_list = ["operation", "sequenceNum"]` |

정렬 기준은 **정렬 가능한 컬럼** 이어야 하며 **NULL 값을 지원하지 않습니다**. 동점을 깨려면 여러 컬럼을 구조체로 묶어 `SEQUENCE BY STRUCT(timestamp_col, id_col)`처럼 씁니다.

SCD Type은 다음과 같습니다.

- **Type 1** (`STORED AS SCD TYPE 1`, `stored_as_scd_type=1`): 덮어씁니다. 이력은 남지 않습니다.
- **Type 2** (`STORED AS SCD TYPE 2`, `stored_as_scd_type="2"`): 이력을 `__START_AT`, `__END_AT` 컬럼으로 보존합니다. `TRACK HISTORY ON * EXCEPT (...)` 또는 `track_history_except_column_list`로 어떤 컬럼 변경이 새 버전을 만들지 제한할 수 있습니다.

삭제 행을 바로 지우지 않고 보관해야 하는 경우의 보존 기간은 `pipelines.cdc.tombstoneGCThresholdInSeconds` 속성으로 조정하며, 기본 보존 기간은 2일이라고 문서가 설명합니다.

### 전체 예시: SCD Type 2 (SQL)

문서 튜토리얼의 SQL 예시입니다. 원천은 `main.cdc_tutorial.users_cdf`입니다.

```sql
CREATE OR REFRESH STREAMING TABLE users_history;

CREATE FLOW apply_cdc AS AUTO CDC INTO
  users_history
FROM
  stream(main.cdc_tutorial.users_cdf)
KEYS
  (userId)
APPLY AS DELETE WHEN
  operation = "DELETE"
SEQUENCE BY
  sequenceNum
COLUMNS * EXCEPT
  (operation, sequenceNum)
STORED AS
  SCD TYPE 2;
```

### 전체 예시: SCD Type 2 (Python)

```python
from pyspark import pipelines as dp
from pyspark.sql.functions import col, expr

@dp.view
def users():
  return spark.readStream.table("main.cdc_tutorial.users_cdf")

dp.create_streaming_table("users_history")
dp.create_auto_cdc_flow(
  target = "users_history",
  source = "users",
  keys = ["userId"],
  sequence_by = col("sequenceNum"),
  apply_as_deletes = expr("operation = 'DELETE'"),
  except_column_list = ["operation", "sequenceNum"],
  stored_as_scd_type = "2")
```

### 스냅샷 변형

`AUTO CDC FROM SNAPSHOT`은 SQL에서 필수 절 `FROM SNAPSHOT (snapshot_query)`와 선택 절 `WITH VERSION (version_query)`를 씁니다. 스냅샷은 Delta 테이블, 클라우드 스토리지 파일, JDBC에서 가져올 수 있습니다. 문서는 **JDBC 읽기에는 classic 컴퓨트가 필요** 하다고 명시합니다.

- 일회성 백필은 Python에서 `once=True`, SQL에서 `ONCE`를 씁니다.
- SCD Type 1 대상 하나를 `AUTO CDC FROM SNAPSHOT` 흐름과 `AUTO CDC` 흐름 여러 개가 함께 쓸 수 있습니다. 이 조합은 트리거 모드(triggered mode)가 필요하다고 문서가 설명합니다.

### 상태

- **Bitemporal AUTO CDC**: **Beta**.
- 나머지 `AUTO CDC` 구문에 대해서는 이 페이지에서 상태 라벨을 확인하지 못했습니다. 문서에 명시 없음.

## 트레이드오프

| 질문 | 권장 |
|---|---|
| 원천이 추가만 된다 | 스트리밍 테이블의 append flow로 충분. `AUTO CDC`는 불필요 |
| 원천 행이 수정·삭제된다 | `AUTO CDC`(CDC 피드가 있으면) 또는 `AUTO CDC FROM SNAPSHOT` |
| 과거 이력이 필요하다 | SCD Type 2 |
| 최신 상태만 필요하다 | SCD Type 1 |
| 위반 레코드를 버려도 된다 | `expect_or_drop`(`ON VIOLATION DROP ROW`) |
| 위반이 있으면 전체를 막아야 한다 | `expect_or_fail`(`ON VIOLATION FAIL UPDATE`) |

## 주의사항

- **위반 기본값**: `EXPECT`만 쓰면 위반 레코드가 남습니다. 제외하려면 `ON VIOLATION DROP ROW`를 명시하십시오.
- **`fail`의 재처리**: `fail`은 업데이트를 멈춥니다. 재처리 전에 원천을 고쳐야 하므로 운영 알림과 함께 쓰십시오.
- **정렬 키 NULL**: `SEQUENCE BY` 컬럼에 NULL이 있으면 지원되지 않습니다. 원천 단계에서 정리하십시오.
- **흐름 제약**: AUTO CDC 흐름은 스트리밍 테이블만 대상으로 삼을 수 있고, 원천은 ONCE 흐름이라도 스트리밍 원천이어야 한다고 문서가 명시합니다. 하나의 스트리밍 테이블이 AUTO CDC 대상이면 다른 AUTO CDC 흐름만 추가로 대상으로 삼을 수 있습니다.
- **Update flow**: Public Preview이며 Python에서만 쓸 수 있습니다.
- **지표 확인**: 지표가 비어 있으면 규칙이 없거나, 흐름이 지원하지 않는 연산자를 쓰거나, 지표 설정이 꺼져 있을 수 있습니다. 이벤트 로그와 함께 확인하십시오 ([파이프라인 이벤트 로그](pipelines-event-log.md)).

## 참고 문서

- [Expectations](https://docs.databricks.com/aws/en/ldp/expectations)
- [AUTO CDC](https://docs.databricks.com/aws/en/ldp/cdc)
- [Flows in Lakeflow pipelines](https://docs.databricks.com/aws/en/ldp/concepts/flows)
- [Pipeline event log](https://docs.databricks.com/aws/en/ldp/monitor-event-logs)
