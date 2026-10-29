# Delta Lake 동작 원리

> 기준일: 2026-10-28 · 근거: 공식 문서

Delta Lake는 Parquet 데이터 파일 위에 **트랜잭션 로그(Transaction log)** 를 얹은 오픈 테이블 포맷입니다. Databricks에서 테이블을 만들 때 별도로 지정하지 않으면 기본 형식이 Delta Lake입니다. 이 페이지는 로그가 어떻게 버전과 ACID를 만드는지, 스키마가 쓰기 시점에 어떻게 검증되고 변경되는지, 여러 문장을 하나의 트랜잭션으로 묶는 방법을 다룹니다.

## 1. 왜 필요한가

Parquet 파일만 쌓아 둔 데이터 레이크에서는 다음 상황이 실제로 일어납니다.

| 상황 | Parquet 디렉터리만 있을 때 | Delta Lake 테이블일 때 |
|---|---|---|
| 쓰기 중 작업 실패 | 일부 파일만 남아 읽는 쪽이 중간 상태를 봄 | 커밋되지 않은 파일은 로그에 없으므로 읽히지 않음 |
| 쓰기와 읽기 동시 실행 | 읽기가 파일 목록을 보는 순간 파일이 바뀔 수 있음 | 읽기는 특정 버전의 스냅샷을 기준으로 실행됨 |
| 컬럼이 다른 파일 혼입 | 나중에 쿼리에서 타입 오류 발생 | 쓰기 시점에 스키마 검증으로 거부 |
| 행 하나 수정 | 파일을 다시 써야 함 | 파일 재작성 또는 삭제 벡터로 처리 (삭제 벡터 페이지 참고) |
| 잘못된 쓰기 복구 | 백업이 없으면 불가 | 이전 버전으로 조회·복원 가능 (타임 트래블 페이지 참고) |

## 2. 어떻게 동작하는가

### 트랜잭션 로그

Delta 테이블 디렉터리에는 데이터 파일(`.parquet`)과 함께 `_delta_log/` 폴더가 있습니다. 이 폴더에는 JSON 형식의 커밋 파일이 순서대로 쌓이며, 각 커밋은 다음 내용을 기록합니다.

- 이 커밋이 **새로 추가한 데이터 파일** 목록
- 이 커밋이 **논리적으로 제거한 데이터 파일** 목록
- 스키마, 테이블 속성, 통계 같은 메타데이터 변경

테이블의 현재 상태는 로그를 처음부터 순서대로 읽어 "지금 살아 있는 파일 목록"을 계산한 결과입니다. 따라서 `UPDATE`나 `DELETE`가 기존 Parquet 파일을 즉시 지우지는 않습니다. 로그에 제거 기록을 남기고, 실제 파일 삭제는 나중에 `VACUUM`이 합니다 ([테이블 레이아웃 최적화](table-layout-optimization.md) 참고).

| 구성 요소 | 위치 | 역할 |
|---|---|---|
| 데이터 파일 | 테이블 디렉터리 | 실제 행 데이터 (Parquet) |
| 트랜잭션 로그 | `_delta_log/` | 버전별 추가·제거 파일 기록 |
| 체크포인트 | `_delta_log/` | 로그 읽기 비용을 줄이기 위한 중간 스냅샷 |

> **참고** 로그 디렉터리의 파일 구조는 공개 프로토콜입니다. 다만 로그 파일을 직접 편집하거나 삭제하면 테이블이 깨집니다. 조작은 항상 SQL이나 Delta API로 하십시오.

### ACID 보장

공식 문서는 Delta Lake가 트랜잭션을 원자적(Atomic)으로 처리한다고 설명합니다. 실무적으로 다음 의미입니다.

| 속성 | 의미 | 예 |
|---|---|---|
| 원자성 (Atomicity) | 커밋은 전부 보이거나 전부 안 보임 | 100만 행 `MERGE` 도중 실패하면 이전 버전이 그대로 유지 |
| 일관성 (Consistency) | 쓰기 시점에 스키마 규칙 검증 | 타입이 맞지 않는 `INSERT`는 거부 |
| 격리성 (Isolation) | 읽기는 스냅샷 기준, 쓰기 충돌은 감지 | 읽기 중 다른 쓰기가 커밋되어도 읽기는 시작 시점 버전 기준 |
| 지속성 (Durability) | 커밋된 로그와 파일은 저장소에 남음 | 보존 기간 내 이전 버전 조회 가능 |

> **주의** 충돌 감지의 세밀도는 작업 종류와 설정에 따라 다릅니다. 예를 들어 멀티 문장 트랜잭션의 대화형(Interactive) 트랜잭션은 테이블 단위로 충돌을 감지하고, 비대화형(Non-interactive) 트랜잭션은 행 수준 동시성이 켜져 있을 때 행 단위로 감지합니다. 자세한 내용은 아래 멀티 문장 트랜잭션 절을 보십시오.

## 3. 어떻게 쓰는가

### 3.1 테이블 생성과 쓰기

```sql
CREATE TABLE main.sales.orders (
  order_id  BIGINT,
  customer  STRING,
  amount    DECIMAL(12, 2),
  order_ts  TIMESTAMP
);

INSERT INTO main.sales.orders
VALUES (1, 'acme', 120.50, TIMESTAMP '2026-10-01 09:00:00');
```

`USING DELTA`를 명시하지 않아도 기본 형식은 Delta입니다. 공식 문서도 `USING`을 생략하면 기본값이 `DELTA`라고 설명합니다.

### 3.2 스키마 강제 (Schema enforcement)

스키마 강제는 Delta 테이블에 쓸 때 **쓰기 시점에** 스키마와 맞는지 검사하는 기능입니다. 공식 문서 기준 규칙은 다음과 같습니다.

| 작업 | 거부되는 경우 |
|---|---|
| `INSERT` | 대상 테이블에 없는 컬럼을 넣을 때, 데이터 타입이 대상과 맞지 않을 때 (Databricks가 안전하게 캐스팅할 수 있으면 통과) |
| `MERGE` | `UPDATE SET` 또는 `INSERT`의 대상 컬럼이 테이블에 없을 때. `INSERT *`나 `UPDATE SET *`를 쓰면 소스가 대상의 모든 컬럼을 가져야 함 |

예를 들어 `BIGINT` 컬럼에 정수를 넣는 것은 안전한 캐스팅으로 통과합니다. 없는 컬럼 이름을 넣으면 `UNRESOLVED_COLUMN.WITH_SUGGESTION` 오류(SQLSTATE 42703)가 나고 올바른 이름을 제안합니다.

```sql
-- 실패: 대상에 없는 컬럼
INSERT INTO main.sales.orders (order_id, customer, discount)
VALUES (2, 'globex', 0.1);
```

> **참고** 스키마 강제는 Delta 테이블에만 적용됩니다. 공식 문서는 CSV·JSON 같은 비-Delta 형식의 클라우드 스토리지 파일에는 적용되지 않는다고 명시합니다.

### 3.3 스키마 진화 (Schema evolution)

스키마 진화는 테이블 스키마를 바꾸는 방법입니다. 공식 문서가 안내하는 방법은 세 가지입니다.

| 방법 | 범위 | 예 |
|---|---|---|
| 명시적 변경 | 테이블 | `ALTER TABLE ... ADD COLUMN` |
| 세션 단위 자동 진화 | 세션 | `spark.databricks.delta.schema.autoMerge.enabled`를 `true`로 설정 후 쓰기 |
| 쓰기 단위 자동 진화 | 한 번의 쓰기 | DataFrame 쓰기에 `mergeSchema` 옵션을 `"true"`로 지정 |

```sql
ALTER TABLE main.sales.orders ADD COLUMN channel STRING;
```

```python
# DataFrame 쓰기 한 번에 새 컬럼을 추가하며 저장
(df.write
   .format("delta")
   .option("mergeSchema", "true")
   .mode("append")
   .saveAsTable("main.sales.orders"))
```

> **참고** 공식 문서는 INSERT와 MERGE에서 스키마 진화의 의미가 특별하다고 설명하며, 자세한 규칙은 "Enable schema evolution" 절을 보라고 안내합니다. 자동 진화를 켜기 전에 해당 절을 확인하십시오.

### 3.4 컬럼 이름 변경과 삭제 (컬럼 매핑)

컬럼 이름 변경과 삭제는 컬럼 매핑(Column mapping) 기능이 있어야 합니다. 컬럼 매핑은 물리 파일의 컬럼 이름과 논리 이름을 분리합니다. 문서의 설정 예는 다음과 같습니다.

```sql
ALTER TABLE main.sales.orders SET TBLPROPERTIES (
  'delta.columnMapping.mode' = 'name'
);
```

컬럼 매핑 활성화 조건과 되돌림 제약은 공식 문서의 Rename and drop columns with Delta Lake column mapping 페이지에서 확인하십시오. 이 장에서 확인한 범위에서는 되돌림 가능 여부를 단정하지 않습니다.

### 3.5 MERGE로 업서트

`MERGE`는 소스 데이터를 대상 테이블과 맞추는 기본 업서트 문법입니다.

```sql
MERGE INTO main.sales.orders AS target
USING main.staging.orders_delta AS source
ON target.order_id = source.order_id
WHEN MATCHED THEN
  UPDATE SET *
WHEN NOT MATCHED THEN
  INSERT *;
```

> **주의** 공식 문서는 대상 행 하나에 소스의 행 두 개 이상이 매칭되면 `MERGE`가 실패할 수 있다고 설명합니다. 소스에서 중복 키를 먼저 제거하십시오.

### 3.6 멀티 문장 트랜잭션

여러 문장을 하나의 원자적 단위로 묶을 수 있습니다. 문서가 제시하는 문법은 두 가지입니다.

```sql
-- 비대화형: 한 블록을 원자적으로 실행
BEGIN ATOMIC
  INSERT INTO main.sales.orders VALUES (3, 'initech', 75.00, current_timestamp());
  DELETE FROM main.sales.orders WHERE order_id = 1;
END;
```

```sql
-- 대화형: 여러 문장을 세션에서 나눠 실행한 뒤 커밋
BEGIN TRANSACTION;
UPDATE main.sales.orders SET amount = amount * 1.1 WHERE customer = 'acme';
COMMIT;
```

요구 사항과 제약은 다음과 같습니다.

| 항목 | 내용 |
|---|---|
| 대상 테이블 | 쓰기 대상은 카탈로그 커밋(Catalog commits)이 켜진 Unity Catalog 관리형 Delta 또는 Iceberg 테이블 |
| 실행 환경 | 비대화형은 서버리스 컴퓨트, Databricks Runtime 18.0 이상 클러스터, 또는 SQL 웨어하우스. 대화형은 SQL 웨어하우스 |
| DDL | `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`은 트랜잭션 안에서 실행할 수 없음 |
| 타임 트래블 | 트랜잭션 안에서는 사용할 수 없음 |
| 대화형 제한 | 10분 동안 비활성이면 롤백, 전체 48시간 초과 시 롤백 |
| 규모 | 한 트랜잭션은 합쳐서 테이블 100개까지, 뷰 100개까지 읽기 가능 |

> **참고** 트랜잭션 기능의 릴리스 상태는 릴리스 노트 2026-10-14 항목 "Transactions support both managed Delta Lake and Apache Iceberg tables"에서 확인했습니다. 릴리스 노트는 Delta 관리형 테이블의 트랜잭션이 GA라고 명시하며, 기능 페이지 본문에는 상태 라벨이 없습니다. 적용 전 원문을 다시 확인하십시오.

## 4. 트레이드오프

| 항목 | 장점 | 비용 |
|---|---|---|
| 로그 기반 버전 관리 | 원자적 커밋과 이력 | 로그가 길어지면 메타데이터 읽기 비용이 늘어납니다 (체크포인트로 완화) |
| 스키마 강제 | 잘못된 데이터가 테이블에 들어가기 전에 차단 | 소스 정리 작업이 파이프라인에 추가됩니다 |
| 스키마 진화 | 소스 변경을 빠르게 반영 | 자동 진화를 켜면 의도하지 않은 컬럼이 조용히 추가될 수 있습니다 |
| 공개 포맷 | Delta 프로토콜을 따르는 외부 엔진이 읽을 수 있음 | 외부 엔진의 기능 지원 범위가 Databricks와 다를 수 있습니다 |

### Iceberg와의 관계

Delta와 Iceberg는 둘 다 파일 목록을 메타데이터로 관리하는 오픈 테이블 포맷입니다. 이 장의 [Apache Iceberg 지원](iceberg-support.md) 페이지에서는 같은 데이터를 Iceberg 클라이언트에 노출하는 UniForm과 관리형 Iceberg 테이블을 다룹니다. 한 테이블의 형식을 바꾸는 작업이 아니라, 테이블 형식을 선택하는 작업이라는 점을 기억하십시오.

## 5. 주의사항

- **스키마 자동 진화는 필요할 때만 켭니다.** 세션 설정으로 켜 두면 같은 세션의 다른 쓰기에도 영향을 줍니다.
- **`MERGE` 소스의 중복 키를 먼저 제거합니다.** 공식 문서는 중복 매칭 시 `MERGE`가 실패할 수 있다고 설명합니다.
- **컬럼 이름을 바꾸기 전에 컬럼 매핑 제약을 확인합니다.** 이름 변경과 삭제를 지원하려면 컬럼 매핑이 필요하며, 외부 엔진이 이 기능을 지원하는지도 별도로 확인해야 합니다.
- **로그 보존 기간을 기억합니다.** 테이블 이력(로그)은 기본 `logRetentionDuration` 설정인 30일 동안 유지된다고 공식 문서가 설명합니다. 이력 조회 기간의 세부 규칙은 [타임 트래블과 변경 데이터 피드](time-travel-and-cdf.md)에서 다룹니다.
- **직접 파일을 복사하거나 삭제하지 않습니다.** 로그와 파일이 어긋나면 테이블 조회가 실패합니다.
- **Delta 테이블을 가리키는 외부 경로가 있다면 메타데이터 동기화를 확인합니다.** 자세한 내용은 [관리형 vs 외부 테이블](managed-vs-external-tables.md)에 있습니다.

## 참고 문서

- [What is Delta Lake in Databricks?](https://docs.databricks.com/aws/en/delta/)
- [Schema enforcement](https://docs.databricks.com/aws/en/tables/schema-enforcement)
- [Update table schemas with schema evolution](https://docs.databricks.com/aws/en/tables/update-schema)
- [Rename and drop columns with Delta Lake column mapping](https://docs.databricks.com/aws/en/tables/features/column-mapping)
- [Upsert into a Delta Lake table using merge](https://docs.databricks.com/aws/en/delta/merge)
- [Transactions](https://docs.databricks.com/aws/en/transactions)
- [Work with table history](https://docs.databricks.com/aws/en/tables/history)
