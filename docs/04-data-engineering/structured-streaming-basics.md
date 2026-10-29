# Structured Streaming 기초

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 300

## 한눈에 보기

Structured Streaming은 Apache Spark의 스트리밍 엔진입니다. 공식 문서는 배치 처리에 쓰는 것과 **같은 Spark API** 로 스트리밍 애플리케이션과 파이프라인을 만들 수 있다고 설명합니다. 이 장의 Auto Loader와 Lakeflow 파이프라인도 내부적으로 Structured Streaming 위에서 동작합니다. 이 페이지는 직접 스트리밍 쿼리를 작성할 때 알아야 할 네 가지, 즉 **처리 모드와 트리거, 체크포인트, 워터마크, 출력 모드** 를 다룹니다.

## 왜 필요한가

배치 작업은 "지금까지 쌓인 데이터 전체"를 처리하지만, 스트리밍은 "이전에 처리한 것 이후의 새 데이터"를 계속 처리해야 합니다. 이때 필요한 것은 다음 세 가지입니다.

- 어디까지 처리했는지 기록하는 장치 (체크포인트)
- 시간이 지나면서 쌓이는 상태(집계, 조인, 중복 제거)를 제한하는 장치 (워터마크)
- 결과를 어떤 방식으로 싱크에 쓸지 정하는 장치 (출력 모드, 트리거)

## 어떻게 동작하는가

### 처리 모드

| 모드 | 설명 (문서 원문 요지) |
|---|---|
| 실시간 모드 (real-time mode) | 서브 초 단위 워크로드용. 엔드투엔드 지연이 최소 5밀리초 수준. 트리거와 컴퓨트 설정으로 활성화 |
| 마이크로 배치 모드 (micro-batch, 기본) | 분석과 ETL 파이프라인용. 데이터를 작은 배치로 나누어 처리하며, 컴퓨트 비용과 초·분 단위 지연 요구의 균형을 맞춤 |

문서 개요 페이지에서 상세 설명(무한 테이블 모델 등)은 연결된 하위 페이지에 있습니다. 이 페이지는 실무에 필요한 항목만 정리합니다.

### 트리거

`writeStream`에서 `trigger()`로 배치 실행 주기를 정합니다. 문서의 트리거 페이지 기준입니다. 상태 라벨은 이 페이지에서 확인하지 못했습니다.

| 트리거 | Python 문법 (문서) | 동작 |
|---|---|---|
| 기본값 (지정 없음) | 없음 | 일반 목적 스트리밍. 문서는 3~5초 지연을 설명 |
| 고정 간격 | `.trigger(processingTime='10 seconds')` | 지정한 간격마다 마이크로배치 실행. 비용과 성능의 균형 |
| 사용 가능한 데이터 전부 | `.trigger(availableNow=True)` | 트리거 시점에 쌓인 데이터를 모두 처리한 뒤 종료 |
| 실시간 모드 | `.trigger(realTime='5 minutes')` | 서브 초 단위 지연이 필요한 운영 워크로드 |
| Once | (문서에 Python 예시 없음) | Databricks Runtime 11.3 LTS 이상에서 **사용 중단(deprecated)**. `Trigger.AvailableNow` 사용 권장 |
| Continuous | `.trigger(continuous='1 second')` | **지원되지 않음**. 실시간 모드 사용 권장 |

> **참고** `availableNow=True`는 "배치처럼 한 번 돌고 끝나는" 스트리밍입니다. 증분 처리 상태는 유지되므로 다음 실행은 새 데이터만 처리합니다. Auto Loader 튜토리얼도 이 트리거를 씁니다.

### 체크포인트

체크포인트(`checkpointLocation`)는 스트림의 진행 상태를 저장하는 위치입니다. 문서는 체크포인트가 다음을 저장한다고 설명합니다.

- **오프셋(offsets)**: 마이크로배치마다 처리한 원천 오프셋. 재시작 시 중복 없이 이어 읽는 근거입니다.
- **커밋(commits)**: 어떤 마이크로배치가 싱크에 커밋됐는지. 정확히 한 번 처리(exactly-once)의 근거입니다.
- **상태(state)**: 상태 저장 쿼리(집계, 스트림-스트림 조인, 중복 제거, `transformWithState`)의 연산자 메타데이터, 상태 스키마, 상태 저장소 내용.
- **메타데이터**: 쿼리 고유 ID. 설정값은 오프셋 로그에 저장됩니다.

문서 예시입니다. Unity Catalog 볼륨 경로를 체크포인트로 씁니다.

```python
(df.writeStream
  .option("checkpointLocation", "/Volumes/catalog/schema/volume/path")
  .toTable("catalog.schema.table"))
```

`checkpointLocation`은 스트리밍 쿼리를 실행하기 전에 반드시 지정해야 합니다. 노트북의 `display()`나 `memory` 싱크는 옵션을 생략하면 임시 체크포인트를 만들지만, 문서는 이 임시 위치가 장애 복구나 일관성을 보장하지 않으며 정리되지 않을 수도 있다고 경고합니다. 항상 명시하십시오.

**쿼리 변경과 체크포인트**: 다음 변경은 보통 새 체크포인트가 필요합니다.

- 입력 소스의 개수나 종류 변경, Kafka 토픽 변경, Auto Loader 경로 변경
- 상태 저장 연산자 종류 변경, 상태 스키마 변경, 싱크 종류 변경

다음은 대체로 안전합니다. 필터 추가·제거, 속도 제한이나 트리거 간격 변경, `mapGroupsWithState`의 UDF 로직 수정(의미가 바뀔 수 있음).

다음은 상태 저장 연산자에서 허용되지 않습니다. 스트리밍 집계나 중복 제거의 키·집계 변경, 스트림-스트림 조인의 스키마·동등 조인 컬럼·조인 종류 변경. 문서는 이런 변경이 재시작 후 예측할 수 없이 실패할 수 있다고 설명합니다. 파일 싱크의 출력 디렉터리 변경도 허용되지 않습니다. Kafka 싱크의 출력 토픽 변경은 허용됩니다.

**소스 진화(Source evolution)**: 기본적으로 소스는 **위치(순서)** 로 식별되므로 소스 순서를 바꾸거나 개수를 바꾸면 체크포인트 호환이 깨집니다. DBR 18.2 이상에서는 소스에 이름을 주고 순서를 바꾸거나 추가·제거할 수 있습니다.

```python
spark.conf.set("spark.sql.streaming.queryEvolution.enableSourceEvolution", "true")
```

소스 이름은 `.name()`으로 주며 유일하고 문자, 숫자, 밑줄만 씁니다. 이 기능을 켜려면 새 체크포인트가 필요하며, 체크포인트 단위로 되돌릴 수 없습니다.

### 워터마크

워터마크는 **상태 저장 연산(윈도우 집계, 조인 키 등)이 상태를 얼마나 오래 들고 있을지** 를 정하는 임계값입니다. 문서 설명입니다. "Watermarks control the threshold for when a query stops processing a state entity." 워터마크가 오래된 상태를 자동으로 지워 메모리 오류와 지연 증가를 막습니다. 임계값 안에 도착한 레코드는 항상 처리되며, 임계값 밖의 레코드는 처리될 수도 있지만 보장되지 않습니다.

Python 문법입니다.

```python
from pyspark.sql.functions import window

(df
  .withWatermark("event_time", "10 minutes")
  .groupBy(
    window("event_time", "5 minutes"),
    "id")
  .count())
```

- 워터마크는 입력 스트림마다 하나씩 줄 수 있습니다(예: `input_stream1.withWatermark("eventTime1", "1 hour")`).
- `groupBy()`와 `window()`에서는 컬럼을 **이름으로** 참조해 이벤트 시간 표시를 유지하라고 문서가 설명합니다.
- 문서는 Python과 Scala 문법만 보여 줍니다. SQL 형태는 이 페이지에서 확인하지 못했습니다.

**트레이드오프**: 워터마크가 짧으면 지연이 줄고 상태가 작아지지만 늦은 데이터를 덜 받아들입니다. 길면 늦은 데이터를 더 받아들이지만 상태가 커지고 결과 출력이 늦어집니다.

### 출력 모드

| 출력 모드 | 워터마크가 있을 때 동작 (문서 요지) |
|---|---|
| append | 워터마크 임계값을 지난 뒤에만 행을 씀. 쓰기가 늦춰지고, 오래된 집계 상태는 임계값 후 버려짐 |
| update | 계산되는 대로 행을 쓰고, 새 데이터가 오면 덮어쓸 수 있음. 오래된 상태는 임계값 후 버려짐 |
| complete | 집계 상태를 버리지 않음. 매 트리거마다 대상 테이블 전체를 다시 씀 |

- 스트림-스트림 조인은 **append 모드만** 지원합니다. 내부 조인은 워터마크를 권장하고, 외부 조인은 필수라고 문서가 설명합니다. 매칭되지 않은 레코드는 임계값이 지나야 써지기 때문입니다.
- 모든 출력 모드가 모든 상태 저장 연산에 지원되는 것은 아닙니다.

## 어떻게 쓰는가

### 파일을 읽어 테이블에 쓰는 기본 흐름

문서 튜토리얼의 Delta 테이블 조인 예시입니다. 테이블 이름과 체크포인트 경로는 자리 표시자입니다.

```python
(spark.readStream
    .table("<table-name1>")
    .join(spark.read.table("<table-name2>"), on="<id>", how="left")
    .writeStream
    .trigger(availableNow=True)
    .option("checkpointLocation", "<checkpoint-path>")
    .toTable("<table-name3>"))
```

이 예시는 `trigger(availableNow=True)`를 쓰므로 실행 후 종료합니다. 상시 실행이 필요하면 트리거를 바꾸거나 생략하고, 운영에서는 Lakeflow 파이프라인이나 Jobs를 쓰는 편이 관리하기 쉽습니다([스트리밍 테이블과 구체화된 뷰](pipelines-streaming-tables-and-mvs.md), [Lakeflow Jobs 태스크와 트리거](jobs-tasks-and-triggers.md) 참고).

## 트레이드오프

| 질문 | 권장 |
|---|---|
| 몇 초 이내 지연이 필요한가 | 마이크로 배치 (기본) 또는 고정 간격 트리거 |
| 밀리초 단위 지연이 필요한가 | 실시간 모드 검토 |
| 쌓인 데이터를 주기적으로 한꺼번에 처리하는가 | `availableNow` 트리거 + Jobs 스케줄 |
| 집계나 조인에 늦은 데이터가 있는가 | 워터마크로 상태 상한 설정 |
| 운영 수집과 변환을 관리해야 하는가 | 직접 쓰기보다 Lakeflow 파이프라인 (문서가 대부분의 ETL에 권장) |

## 주의사항

- **체크포인트 공유 금지**: 쿼리마다 서로 다른 체크포인트 위치를 씁니다. 여러 쿼리가 같은 위치를 쓰면 안 됩니다.
- **체크포인트 삭제**: 체크포인트 파일을 지우거나 다른 위치로 바꾸면 다음 실행은 처음부터 시작합니다.
- **임시 체크포인트**: `display()`와 `memory` 싱크의 임시 체크포인트에는 장애 복구 보장이 없습니다. 명시하십시오.
- **`dropDuplicates` 재시작**: `dropDuplicates()`나 `dropDuplicatesWithinWatermark()`를 쓰는 쿼리는 상태 스키마 호환성 검사에서 재시작이 실패할 수 있습니다. 문서는 전용(dedicated)과 격리 없음(no isolation) 모드 사이 또는 표준과 서버리스 모드 사이의 전환은 허용하지만, 그 밖의 조합은 피하라고 권장합니다.
- **무워터마크 상태**: 워터마크 없이 무한 상태를 키우면 메모리 압박으로 실패할 수 있습니다. 워터마크를 두십시오.
- **Once 트리거 사용 금지**: 사용 중단된 `Trigger.Once` 대신 `availableNow`를 쓰십시오.

## 참고 문서

- [Structured Streaming concepts](https://docs.databricks.com/aws/en/structured-streaming/concepts)
- [Triggers](https://docs.databricks.com/aws/en/structured-streaming/triggers)
- [Checkpoints](https://docs.databricks.com/aws/en/structured-streaming/checkpoints)
- [Watermarks](https://docs.databricks.com/aws/en/structured-streaming/watermarks)
- [Structured Streaming tutorial](https://docs.databricks.com/aws/en/structured-streaming/tutorial)
- [Auto Loader (이 장)](auto-loader.md)
