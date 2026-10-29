# 동기화 테이블 (Synced Tables)

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

동기화 테이블(Synced Table)은 Unity Catalog의 Delta 테이블을 Lakebase Postgres 데이터베이스에 복사해 **저지연 읽기** 를 제공하는 기능입니다. 방향은 레이크하우스 → Lakebase입니다. 반대 방향(Lakebase 변경을 Delta로 옮기는 기능)은 [변경 데이터 반출](change-data-out.md)에서 다룹니다.

> **참고** 문서는 동기화 테이블의 Postgres 쪽에서 **읽기 쿼리만 실행할 것** 을 강하게 권장합니다. 원본 데이터 수정은 레이크하우스 쪽에서 합니다.

## 1. 왜 필요한가

레이크하우스 테이블은 분석에 맞지만, 애플리케이션이 행 단위로 빠르게 조회하기에는 맞지 않습니다. 이전에는 보통 다음 방법을 썼습니다.

| 기존 방법 | 한계 |
|---|---|
| 별도 ETL로 운영 DB에 적재 | 파이프라인을 직접 만들고 운영, 지연과 실패 처리 부담 |
| 애플리케이션이 레이크하우스를 직접 조회 | 웨어하우스 비용과 지연, 행 단위 조회에 부적합 |
| 결과를 CSV 등으로 내보내 적재 | 수동이며 최신성 보장 없음 |

동기화 테이블은 Unity Catalog 테이블을 선언하면 Lakebase에 Postgres 테이블이 생기고, 원하는 모드에 따라 데이터가 갱신됩니다. 동기화는 Lakeflow 파이프라인으로 실행됩니다(파이프라인 이름은 문서에서 "Database Table Sync pipeline"으로 표기).

## 2. 어떻게 동작하는가

### 원본과 대상

| 항목 | 내용 |
|---|---|
| 지원 원본 | 관리형·외부 Delta 테이블, 관리형·외부 Iceberg 테이블, 뷰, 구체화 뷰(materialized view) |
| 대상 | Lakebase 프로젝트의 브랜치·데이터베이스 안의 Postgres 테이블 |
| 이름 규칙 | Unity Catalog 스키마가 Postgres 스키마가 되며, 테이블 이름에 `_synced`가 붙음 (UI 빠른 시작 예시 기준) |
| 쓰기 권한 | 동기화 테이블은 Unity Catalog로 관리. Postgres에서 직접 쓰기는 권장하지 않음 |

### 동기화 모드

문서 표의 설명을 옮깁니다. 상태 라벨은 페이지에 모드별로 명시되어 있지 않으며, 페이지 전체가 동기화 테이블을 "generally available"로 설명합니다. LTAP Direct Writes만 Beta로 표기되어 있습니다.

| 모드 | 문서 설명 | 적합한 경우 | 지연·효율 |
|---|---|---|---|
| **Snapshot** | 한 번에 전체 데이터를 복사하고, 동기화 때마다 전체를 다시 복사 | 원본이 한 주기에 행의 10% 넘게 바뀔 때 | 문서는 원본 데이터의 10% 넘게 바뀔 때 약 10배 효율적이라고 설명 (비교 기준은 문서에 명시 없음) |
| **Triggered** | 실행 요청 또는 주기 실행 때 변경(삽입·수정·삭제)을 반영 | 원본 변경이 정해진 주기로 일어날 때 | 5분보다 짧은 간격으로 실행하면 비싸다고 설명 |
| **Continuous** | 초 단위 지연의 실시간 스트리밍 | 변경을 거의 즉시 반영해야 할 때 | 지연은 가장 낮고 비용은 가장 높음. 최소 15초 간격 |

UI에서는 Snapshot과 Triggered가 **On-demand** 모드의 고급 설정 안에 있고, Continuous는 별도 모드로 표시됩니다.

### 기본 키와 데이터 정합성

- 기본 키(Primary key)는 보통 자동으로 감지됩니다.
- 기본 키 열은 NULL을 허용하지 않습니다. 기본 키에 NULL이 있는 행은 동기화에서 제외됩니다.
- 기본 키가 중복되면 파이프라인이 실패합니다. 단, **Timeseries Key** 를 지정하면 키별로 가장 최신 시각의 행만 남습니다.

### 타입 매핑

| Unity Catalog | Postgres |
|---|---|
| BIGINT | BIGINT |
| BINARY | BYTEA |
| BOOLEAN | BOOLEAN |
| DATE | DATE |
| DECIMAL(p,s) | NUMERIC |
| DOUBLE | DOUBLE PRECISION |
| FLOAT | REAL |
| INT | INTEGER |
| INTERVAL | INTERVAL |
| SMALLINT | SMALLINT |
| STRING | TEXT |
| TIMESTAMP | TIMESTAMP WITH TIME ZONE |
| TIMESTAMP_NTZ | TIMESTAMP WITHOUT TIME ZONE |
| TINYINT | SMALLINT |
| ARRAY, MAP, STRUCT | JSONB |

GEOGRAPHY, GEOMETRY, VARIANT, OBJECT 타입은 지원되지 않습니다.

사용자 지정 타입(`type_overrides` API 또는 UI의 **Customize column types**)으로 다음을 지정할 수 있습니다.

| 원본 | Postgres 타입 | 비고 |
|---|---|---|
| ARRAY<FLOAT>, ARRAY<DOUBLE> | `vector(n)` | 차원 1–16,000. 벡터 확장 설치 필요 |
| ARRAY<FLOAT>, ARRAY<DOUBLE> | `halfvec(n)` | 차원 1–16,000. 벡터 확장 설치 필요 |
| STRING | `varchar(n)` | 최대 길이 1–10,485,760. 확장 불필요 |

벡터 확장은 문서가 `CREATE EXTENSION IF NOT EXISTS lakebase_vector CASCADE;` 또는 pgvector만 쓸 때 `CREATE EXTENSION IF NOT EXISTS vector;`를 권장합니다.

## 3. 어떻게 쓰는가

### 원본 테이블 준비 (SQL)

문서의 빠른 시작 예시입니다. SQL 웨어하우스나 노트북에서 실행합니다.

```sql
CREATE TABLE main.default.user_segments AS
SELECT * FROM (VALUES
  (1, 'power_user', 0.92),
  (2, 'casual', 0.35),
  (3, 'power_user', 0.88)) AS segments(user_id, segment, engagement_score);
```

Triggered나 Continuous 모드를 쓸 원본은 변경 데이터 피드가 있어야 합니다. Delta 테이블이라면 다음을 설정합니다. Iceberg 같은 원본은 **자동 변경 데이터 피드(automatic change data feed)** 가 읽기 시점에 변경을 계산합니다.

```sql
ALTER TABLE main.sales.orders SET TBLPROPERTIES (delta.enableChangeDataFeed = true);
```

### 동기화 테이블 생성 (UI)

1. **Catalog** 에서 원본 테이블을 선택하고 **Create** > **Synced table** 을 클릭합니다.
2. 대화 상자에서 대상 카탈로그, 스키마, 테이블 이름을 정하고, **Database type**(Autoscaling), 프로젝트, 브랜치, Postgres 데이터베이스를 고릅니다.
3. **Sync mode** 를 고릅니다. On-demand(고급 설정에서 Snapshot 또는 Triggered), 또는 Continuous.
4. 파이프라인은 **Create new** 또는 **Use existing** 을 고르고, 필요하면 서버리스 사용 정책을 지정합니다.
5. 스키마 탭에서 기본 키(기본값 **Unique**), 선택 사항인 **Timeseries Key**, **Customize column types** 를 설정합니다.
6. **Create** 를 누르고 **Overview** 탭에서 상태를 확인합니다. 수동 갱신은 **Sync now** 입니다.

### 동기화 테이블 생성 (CLI)

문서의 CLI 예시입니다. 위치 인수는 `catalog.schema.table` 형식입니다.

```bash
databricks postgres create-synced-table my-catalog.sales.orders --json '{
  "spec": {
    "source_table_full_name": "main.sales.orders",
    "branch": "projects/my-project/branches/production",
    "primary_key_columns": ["order_id"],
    "scheduling_policy": "SNAPSHOT",
    "postgres_database": "mydb",
    "create_database_objects_if_missing": true
  }
}'
```

Python SDK는 `w.postgres.create_synced_table(...)`를 쓰고, 결과는 `.wait()`로 기다립니다. REST는 `POST /api/2.0/postgres/synced_tables?synced_table_id=...`이며 장기 실행 작업을 `done: true`가 될 때까지 폴링합니다.

> **주의** 문서의 CLI·API 예시에서 `scheduling_policy` 값으로 확인된 것은 `SNAPSHOT`뿐입니다. Triggered와 Continuous를 API로 지정하는 값은 이 장의 근거 문서에 나타나지 않았으므로 여기에 쓰지 않습니다. API로 지정하기 전에 레퍼런스에서 값을 확인하십시오.

### 결과 조회 (Postgres)

```sql
SELECT * FROM "default".user_segments_synced WHERE user_id = 1;
```

스키마 이름 `default`는 Postgres 예약어이므로 큰따옴표로 감싸야 합니다.

### 주기적 갱신 설정

Continuous는 자동으로 스트리밍합니다. Snapshot과 Triggered는 파이프라인을 **Lakeflow Job** 의 **Database Table Sync pipeline** 작업으로 넣고, 트리거를 정합니다.

| 트리거 | 적합한 모드 |
|---|---|
| **Table update** (원본 테이블 갱신 시) | Triggered |
| **Scheduled** (cron 일정과 시간대) | Snapshot |

## 4. 트레이드오프

| 항목 | 내용 |
|---|---|
| 방향 | 단방향. Lakebase에서 바꾼 내용은 원본 Delta로 돌아가지 않음 |
| 비용 구조 | 모드에 따라 다름. Continuous가 가장 비싸고 지연이 가장 짧음. 단가는 이 장에서 다루지 않음 |
| 용량 | 아래 용량 계획 참조 |
| 쓰기 | 문서는 읽기 쿼리만 권장 |

### 용량 계획 (문서 수치)

| 항목 | 값 |
|---|---|
| 동기화 테이블당 연결 | 최대 16개 (컴퓨트 크기에 따라 한도가 다름) |
| 처리량 (Continuous, Triggered 쓰기) | CU당 약 150행/초 |
| 처리량 (Snapshot 쓰기) | CU당 최대 약 2,000행/초 |
| 원본 1개당 동기화 테이블 | 최대 20개 |
| 테이블당 권장 크기 | 새로 고침이 필요한 테이블은 1 TB 이하 권장 |
| 스토리지 | 동기화된 데이터는 브랜치의 데이터베이스 스토리지 쿼터에 포함. 전체 새로 고침 중에는 이전 버전과 새 버전이 모두 집계 |

이름에 쓸 수 있는 문자는 `[A-Za-z0-9_]+`입니다(데이터베이스, 스키마, 테이블 이름).

## 5. 제약과 동작

### 스키마와 정의 변경

| 변경 | Triggered·Continuous | Snapshot |
|---|---|---|
| 열 추가 같은 추가형 변경 | 지원 | 전체 새로 고침으로 반영 |
| 기본 키, Timeseries Key 등 비추가형 변경 | 수정 불가. 동기화 테이블을 삭제하고 다시 만들어야 함 | 같음 |

### 삭제 동작

- Triggered는 각 새로 고침에서 삭제를 반영합니다.
- Snapshot은 전체 원본 복사본으로 다시 채웁니다.
- Continuous의 삭제 전파는 문서가 명시적으로 설명하지 않습니다. 운영 전에 테스트하십시오.
- **Unity Catalog에서 동기화 테이블을 삭제하면 Postgres 테이블도 함께 삭제** 된다고 문서가 설명합니다. UI 메뉴, `w.postgres.delete_synced_table(...)`, `DELETE /api/2.0/postgres/synced_tables/{name}`으로 삭제할 수 있습니다.

> **주의** 다른 자료에서 "동기화 테이블 삭제 시 Postgres 테이블은 남는다"는 설명을 본 적이 있다면, 그 설명은 현재 AWS 동기화 테이블 문서와 다릅니다. 현재 원문은 Unity Catalog 삭제 시 Postgres 테이블도 삭제된다는 것입니다. 실제 워크스페이스에서 삭제 후 Postgres 상태를 확인하십시오.

### 권한과 소유권

- 동기화 테이블은 `databricks_writer_<dbid>` 역할이 소유합니다. 따라서 소유자만 실행할 수 있는 명령(예: 행 수준 보안)은 직접 실행할 수 없습니다.
- 생성자는 테이블에 `SELECT`, `DELETE`, `TRUNCATE`를, 스키마에 `USAGE`와 `CREATE`를 받습니다. `INSERT`와 `UPDATE`는 받지 않습니다.
- 접근 제어는 Unity Catalog로 관리합니다. Postgres의 `REVOKE`로 제어하지 않습니다. 파이프라인의 **Run as** 아이덴티티를 바꿔도 소유권은 재지정되지 않습니다.
- `databricks_superuser`는 `pg_read_all_data`와 `pg_write_all_data`를 가지므로 동기화 테이블에 쓸 수 있습니다. 문서는 데이터 수정은 원본에서 하라고 권장합니다.

### 중복 키와 NULL 키

- 중복 기본 키는 파이프라인을 실패시킵니다. Timeseries Key로 해결합니다.
- NULL 기본 키 행은 제외됩니다.

### 기타

- 동기화 테이블 API는 멱등성이 있어서 일시 오류를 재시도해도 안전하다고 문서가 설명합니다.
- 동기화 중 파이프라인 상태가 `INITIALIZING`으로 길게 보일 수 있으며, 큰 동기화에서는 정상이라고 설명합니다.
- 식별자에 대문자나 특수 문자가 있으면 Postgres에서 참조할 때 따옴표로 감싸야 합니다.

## 6. 타입 주의: 널 문자와 벡터

- Unity Catalog의 STRING, ARRAY, MAP, STRUCT 열에 널 바이트(0x00)가 있으면 Postgres의 TEXT나 JSONB에서 실패합니다. 문서는 `REPLACE(column, CAST(CHAR(0) AS STRING), '')`로 제거하거나 열을 BINARY로 바꾸라고 안내합니다.
- 벡터 타입을 쓰려면 확장을 먼저 설치해야 합니다.

## 7. 주의사항

- **Snapshot으로 시작하고 필요할 때 모드를 올립니다.** 빠른 시작 문서도 Snapshot으로 시작합니다. 원본 변경률을 보고 모드를 정하십시오.
- **Triggered와 Continuous는 원본에 변경 데이터 피드가 필요합니다.** 설정하지 않으면 동기화를 설계대로 쓸 수 없습니다.
- **기본 키를 설계 단계에서 확정합니다.** 기본 키를 바꾸려면 삭제 후 재생성해야 합니다.
- **삭제 순서를 확인합니다.** 동기화 테이블 삭제는 Postgres 테이블 삭제로 이어집니다. 의존하는 뷰가 있다면 함께 영향을 받습니다.
- **재생성 전에 상태를 확인합니다.** 실패한 동기화의 상태를 본 뒤 정리하십시오.
- **상태 라벨은 모드별로 확인합니다.** 문서가 모드별 GA 라벨을 달지 않았으므로, LTAP Direct Writes(Beta)를 쓰는 경우에는 Beta 제약을 따로 확인하십시오. LTAP Direct Writes는 Postgres 16, 17, 18이 필요하고, 워크스페이스 관리자가 프리뷰를 켜야 할 수 있습니다.

### 관련 AI 기능 (릴리즈 노트)

2026년 9월 릴리즈 노트는 `ai_search`가 Lakebase 동기화 테이블을 검색할 수 있다고 적고, 상태를 **Beta** 로 표기합니다(2026-09-24). 이 기능은 Lakebase Search를 켜야 합니다.

## 참고 문서

- [Sync tables (AWS)](https://docs.databricks.com/aws/en/oltp/projects/sync-tables)
- [Quickstart: Serve lakehouse data (AWS)](https://docs.databricks.com/aws/en/oltp/projects/quickstart-synced-tables)
- [Release notes, 2026년 9월 (AWS)](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
