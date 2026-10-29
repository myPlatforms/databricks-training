# 타임 트래블과 변경 데이터 피드

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

Delta 테이블과 Iceberg 테이블은 쓰기마다 새 버전을 만듭니다. 이 버전 이력을 이용하면 과거 시점의 데이터를 조회하거나 되돌릴 수 있는데, 이를 **타임 트래블(Time travel)** 이라고 합니다. 한편 **변경 데이터 피드(Change Data Feed, CDF)** 는 두 버전 사이에서 어떤 행이 추가·수정·삭제되었는지를 행 단위로 알려 줍니다. 이 페이지는 두 기능의 동작, 보존 기간, 사용법을 다루고, 둘이 함께 맞물리는 보존 설정의 주의점을 설명합니다.

## 1. 왜 필요한가

| 상황 | 이력이 없을 때 | 타임 트래블·CDF가 있을 때 |
|---|---|---|
| 잘못된 `DELETE`나 `MERGE` | 백업에서 복구하거나 재적재해야 함 | 이전 버전을 조회하고 `RESTORE`로 되돌림 |
| 감사·재현 | 과거 시점의 결과를 재현하기 어려움 | 버전 번호나 타임스탬프로 같은 결과를 다시 조회 |
| 증분 처리 | 전체를 다시 읽어 변경분을 찾아야 함 | 변경 행만 골라 다음 단계로 전달 |
| 다운스트림 동기화 | 변경 감지 로직을 직접 구현해야 함 | 변경 피드를 소비하는 파이프라인 구성 |

타임 트래블은 "과거 상태 조회"에, CDF는 "두 상태 사이의 차이 조회"에 씁니다. 둘 다 같은 로그 이력에 기대므로 보존 기간 설정을 함께 봐야 합니다.

## 2. 어떻게 동작하는가

### 2.1 버전과 이력

Delta 테이블의 각 쓰기는 트랜잭션 로그에 새 버전을 남깁니다. `DESCRIBE HISTORY`는 이 이력을 보여 줍니다. 공식 문서 기준으로 이력의 보존 기간은 `logRetentionDuration` 테이블 속성으로 정하며, 기본값은 30일입니다.

| 설정 | 기본값 | 역할 |
|---|---|---|
| `logRetentionDuration` | 30일 | 테이블 이력(트랜잭션 로그)의 보존 기간 |
| `deletedFileRetentionDuration` | 7일 | `VACUUM`이 참조되지 않는 데이터 파일을 지우기 전 보존 기간 |

두 값이 모두 실제 조회 가능 기간을 결정합니다. 데이터 파일이 `VACUUM`으로 지워지면 그 파일을 필요로 하는 버전은 더 이상 조회하거나 복원할 수 없습니다.

### 2.2 CDF의 두 가지 방식

공식 문서는 CDF를 두 가지 방식으로 나눠 설명합니다.

| 구분 | 이름 | 동작 시점 | 설정 | 지원 범위 | 상태 |
|---|---|---|---|---|---|
| 자동 CDF | Automatic change data feed | 테이블을 읽을 때 행 계보(Row lineage) 메타데이터로 계산 | 테이블 속성 불필요 | Unity Catalog 관리형 Delta(행 추적 켜짐), 관리형 Iceberg v3, 외부 Delta(행 추적 켜짐). Databricks Runtime 19 이상 | GA (릴리스 노트 2026-09-01) |
| 레거시 CDF | Legacy change data feed | 테이블을 쓸 때 변경을 물리적으로 기록 | `delta.enableChangeDataFeed` 속성 필요 | Delta Lake만 | 공식 문서에서 레거시로 표기 |

> **주의** 자동 CDF와 레거시 CDF는 같은 테이블에서 함께 쓸 수 없습니다. 공식 문서는 두 방식을 동시에 쓸 수 없다고 명시합니다. 새 테이블은 요구 조건을 맞추면 자동 CDF를, 아니면 레거시 CDF를 쓰는 것으로 방향을 정하십시오.

### 2.3 CDF가 추가하는 컬럼

| 컬럼 | 타입 | 값 |
|---|---|---|
| `_change_type` | String | `insert`, `update_preimage`, `update_postimage`, `delete` |
| `_commit_version` | Long | 변경을 포함한 버전 번호 |
| `_commit_timestamp` | Timestamp | 커밋 생성 시각 |

`update_preimage`는 갱신 전 값, `update_postimage`는 갱신 후 값입니다. 테이블에 같은 이름의 컬럼이 이미 있으면 충돌하므로 이름을 바꿔야 합니다.

## 3. 어떻게 쓰는가

### 3.1 과거 버전 조회

```sql
-- 이력 전체 확인
DESCRIBE HISTORY main.sales.orders;

-- 마지막 작업 한 건만 확인
DESCRIBE HISTORY main.sales.orders LIMIT 1;

-- 버전 번호로 조회
SELECT * FROM main.sales.orders VERSION AS OF 3;

-- 타임스탬프로 조회
SELECT * FROM main.sales.orders TIMESTAMP AS OF '2026-10-01T09:00:00.000Z';
```

`DESCRIBE HISTORY`가 보여 주는 작업 종류(`operation`)와 시각(`timestamp`) 같은 항목으로 되돌릴 시점을 고릅니다.

### 3.2 `RESTORE`로 되돌리기

```sql
RESTORE TABLE main.sales.orders TO VERSION AS OF 3;

RESTORE TABLE main.sales.orders TO TIMESTAMP AS OF '2026-10-01 09:00:00';
```

공식 문서 기준 `RESTORE`의 요구와 제약은 다음과 같습니다.

| 항목 | 내용 |
|---|---|
| 권한 | 테이블에 `MODIFY` 권한 필요 |
| 타임스탬프 형식 | `yyyy-MM-dd HH:mm:ss` 또는 `yyyy-MM-dd` |
| 데이터 변경 | `RESTORE`도 데이터를 바꾸는 작업이므로 다운스트림 스트리밍 잡이 복원된 행을 다시 처리해 중복이 생길 수 있음 |
| 파일 삭제 후 | `VACUUM`이 지운 파일이 필요한 버전으로는 복원 불가. `spark.sql.files.ignoreMissingFiles`가 `true`이면 일부 복원은 가능 |

### 3.3 레거시 CDF 켜기와 읽기

```sql
-- 새 테이블에서 켜기
CREATE TABLE main.sales.orders_cdf (
  order_id  BIGINT,
  customer  STRING,
  amount    DECIMAL(12, 2)
)
TBLPROPERTIES (delta.enableChangeDataFeed = true);

-- 기존 테이블에서 켜기
ALTER TABLE main.sales.orders
SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
```

변경분을 SQL로 읽는 예입니다. 버전 0부터 최신까지, 또는 범위를 지정해 읽습니다. 시작과 끝 버전은 모두 포함됩니다.

```sql
-- 버전 0부터 최신까지
SELECT * FROM table_changes('main.sales.orders', 0);

-- 버전 0부터 10까지
SELECT * FROM table_changes('main.sales.orders', 0, 10);
```

Python에서 배치로 읽는 예입니다. 배치 읽기는 시작 버전이 필요합니다.

```python
changes_df = (
    spark.read
    .option("readChangeFeed", "true")
    .option("startingVersion", 0)
    .table("main.sales.orders")
)
```

스트리밍으로 읽는 예입니다. 공식 문서는 스트리밍 첫 실행이 전체 스냅샷을 `insert`로 반환한다고 설명합니다.

```python
changes_stream = (
    spark.readStream
    .option("readChangeFeed", "true")
    .table("main.sales.orders")
)
```

### 3.4 자동 CDF 쓰기 조건 확인

자동 CDF는 별도 속성이 없지만, 조건이 맞는지 먼저 확인해야 합니다. 행 추적(Row tracking)이 필요하므로 테이블 속성과 런타임을 함께 봅니다.

```sql
DESCRIBE DETAIL main.sales.orders;
```

`DESCRIBE DETAIL`의 `properties`와 `tableFeatures`에서 행 추적 기능이 켜져 있는지 확인하십시오. 이 페이지는 행 추적 속성 이름을 문서 예시로 확인하지 못했으므로 정확한 키는 적지 않았습니다.

## 4. 트레이드오프

| 항목 | 장점 | 비용·제약 |
|---|---|---|
| 타임 트래블 | 실수 복구와 재현이 쉬움 | 보존 기간만큼 파일과 로그가 쌓여 저장 비용 증가 |
| 레거시 CDF | 쓰기 시점에 변경을 기록해 읽기가 단순 | Delta 전용. 쓰기 비용 증가. 기록은 보존 정책을 따름 |
| 자동 CDF | 속성 없이 읽기 시점에 계산 | 행 추적 등 요구 조건과 Databricks Runtime 19 이상 필요 |
| 변경 피드 | 증분 처리에 적합 | 변경 기록은 일시적. 보존 창 밖의 변경은 읽을 수 없음 |

### 언제 쓰지 않는가

- 과거 시점을 몇 달 이상 보존해야 한다면 타임 트래블이 아니라 **별도 스냅샷 테이블** 이나 백업 정책을 설계하십시오. 공식 문서도 이력을 장기 아카이브로 쓰지 말라고 설명합니다.
- 변경 피드를 장기 보관용 데이터로 쓰지 마십시오. 보존 창이 지나면 읽을 수 없습니다.

## 5. 주의사항

> **주의** 공식 문서는 기본 설정에서 타임 트래블을 최근 7일로 보라고 설명합니다. 데이터 보존 설정과 로그 보존 설정을 모두 더 크게 두지 않는 한, 7일보다 오래된 버전을 기대하지 마십시오. 보존을 늘리면 저장 비용도 늘어납니다.

> **주의** Databricks Runtime 18.0 이상에서는 `deletedFileRetentionDuration`보다 오래된 버전을 요청하는 타임 트래블 조회가 차단됩니다.

- **트랜잭션 안에서는 타임 트래블을 쓸 수 없습니다.** 멀티 문장 트랜잭션 내부의 타임 트래블 조회는 지원되지 않습니다 ([Delta Lake 동작 원리](delta-lake-internals.md) 참고).
- **타임스탬프나 버전에 서브쿼리를 쓸 수 없습니다.** 공식 문서는 `timestamp_expression`과 `version`이 서브쿼리일 수 없다고 설명합니다.
- **`RESTORE`는 파괴적 작업입니다.** 복원 후 이후 버전의 데이터가 사라진 것처럼 보이므로, 복원 전에 `DESCRIBE HISTORY`로 대상 버전을 확인하고 필요하면 복제본을 먼저 만드십시오.
- **테이블 교체 문장의 이력 보존을 확인합니다.** 공식 문서는 `CREATE OR REPLACE TABLE`이 테이블 이력과 부여된 권한, 행 필터, 열 마스크를 보존한다고 설명합니다. 다만 교체가 다운스트림 CDF나 스트리밍 소비자에게 어떤 영향을 주는지는 같은 페이지에 명시되어 있지 않습니다. 교체 문장을 운영 테이블에 적용하기 전 해당 소비자를 확인하십시오.
- **레거시 CDF의 변경 파일은 테이블 보존 정책을 따릅니다.** `VACUUM`이 변경 파일을 지우므로, 소비 파이프라인이 보존 창 안에서 따라잡도록 주기를 설계하십시오.
- **변경 파일을 직접 읽지 마십시오.** 공식 문서는 Delta Lake나 Iceberg API로만 읽으라고 권장합니다.
- **CDF를 다른 시스템에 전달할 때는 Lakebase 방향을 확인합니다.** Lakebase의 변경을 Delta로 옮기는 기능은 [Lakebase 변경 데이터 반출](../10-lakebase/change-data-out.md)에서 다룹니다. 이 페이지의 CDF는 Delta 테이블의 변경 피드입니다.
- **머티리얼라이즈드 뷰의 CDF는 Beta입니다.** 릴리스 노트 2026-08-07 "Change data feed on materialized views (Beta)"는 Lakeflow pipeline이나 Databricks SQL에서 만든 구체화 뷰의 변경 피드를 Beta로 발표했습니다.
- **타임 트래블의 행 필터·열 마스크 동작은 Beta입니다.** 릴리스 노트 2026-09-23은 타임 트래블 쿼리에서 ABAC 정책을 적용하는 기능을 Beta로 발표했으며, Databricks Runtime 19에서 제공된다고 명시합니다.

## 참고 문서

- [Work with table history](https://docs.databricks.com/aws/en/tables/history)
- [Use change data feed on Databricks](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [Table properties reference](https://docs.databricks.com/aws/en/tables/table-properties)
- [Remove unused data files with vacuum](https://docs.databricks.com/aws/en/tables/operations/vacuum)
- [CREATE TABLE (USING)](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-table-using)
- [Deletion vectors in Databricks](https://docs.databricks.com/aws/en/tables/features/deletion-vectors)
