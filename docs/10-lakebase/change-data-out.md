# 변경 데이터 반출: CDF와 논리 복제

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 Lakebase 안에서 일어난 **변경(삽입·수정·삭제)** 을 밖으로 내보내는 두 기능을 다룹니다.

| 기능 | 방향 | 상태 (문서 표기) | 대상 |
|---|---|---|---|
| 변경 데이터 피드(Change Data Feed, CDF) | Lakebase → Unity Catalog Delta | **Public Preview** | 레이크하우스 (분석·파이프라인) |
| 논리 복제(Logical replication) | Lakebase ↔ 외부 Postgres | 문서에 상태 라벨 없음 | 외부 Postgres |

> **참고** 문서는 레이크하우스로 변경을 옮기려면 CDF를 쓰라고 안내합니다. 외부 Postgres와 주고받으려면 논리 복제를 씁니다.

## 1. 왜 필요한가

운영 데이터베이스의 변경을 분석 시스템에 반영하는 전통적인 방법은 두 가지입니다.

- 주기적으로 전체 테이블을 다시 읽습니다. 데이터가 커질수록 비용과 지연이 커집니다.
- 외부 CDC 도구로 Postgres의 논리 복제 슬롯(replication slot)을 읽습니다. 별도 인프라와 권한 설정이 필요합니다.

Lakebase CDF는 같은 목적을 플랫폼 안에서 처리합니다. 변경 이력을 Unity Catalog Delta 테이블에 **추가 전용(append-only)** 으로 기록합니다. 그래서 "이 행이 언제 어떻게 바뀌었는가"를 레이크하우스에서 그대로 분석할 수 있습니다.

## 2. 변경 데이터 피드 (CDF)

### 2.1 동작 원리

CDF는 Postgres의 쓰기 로그(write-ahead log)에서 변경을 읽어 Delta 테이블에 씁니다. 문서는 변경을 약 15초 간격으로 묶어 기록한다고 설명합니다.

- 소스 설정은 **스키마 단위** 입니다. 스키마에 있는 현재 테이블과 앞으로 만들 테이블이 모두 포함됩니다.
- 스키마마다 피드는 하나입니다.
- 대상 테이블 이름은 `lb_<테이블 이름>_history`입니다. 같은 이름이 충돌하면 `lb_users_history_1`처럼 숫자 접미사가 붙습니다.

### 2.2 출력 테이블 구조

| 열 | 타입 | 설명 |
|---|---|---|
| `_pg_change_type` | TEXT | `insert`, `update_preimage`, `update_postimage`, `delete` |
| `_pg_lsn` | BIGINT | Postgres 로그 시퀀스 번호 |
| `_pg_xid` | INTEGER | Postgres 트랜잭션 ID |
| `_timestamp` | TIMESTAMP | 변경이 처리된 시각 (시간대 없음) |
| `_sort_by` | BIGINT | 모든 변경을 정렬하는 단조 증가 키 |

변경 패턴은 다음과 같습니다.

| 이벤트 | 기록 방식 |
|---|---|
| 초기 스냅샷 | 기존 행이 모두 `insert`로 기록 |
| 수정 | `update_preimage`(이전 값) 행 1개와 `update_postimage`(새 값) 행 1개 |
| 삭제 | `delete` 행 1개 |

> **참고** 문서의 빠른 시작 예시는 `ORDER BY _pg_lsn DESC`로 최신 변경을 찾습니다. 소비 쪽에서 상태를 재구성하려면 `_sort_by` 또는 `_pg_lsn`으로 정렬하십시오.

### 2.3 데이터 타입 매핑 (요약)

| PostgreSQL | Delta |
|---|---|
| BOOLEAN | BOOLEAN |
| INT, SMALLINT, BIGINT | INT, SMALLINT, BIGINT |
| TEXT, VARCHAR, CHAR | STRING |
| JSONB | STRING (JSON 문자열로 저장) |
| ENUM | STRING (열거형 라벨로 저장) |
| NUMERIC / DECIMAL | DECIMAL 또는 STRING |
| DATE | DATE |
| TIMESTAMP | TIMESTAMP_NTZ |
| TIMESTAMPTZ | TIMESTAMP |
| FLOAT, DOUBLE | FLOAT, DOUBLE |

- NUMERIC은 가능하면 원본의 정밀도와 스케일을 씁니다. 정밀도가 38을 넘거나 제한 없는 NUMERIC이면 STRING으로 저장합니다.
- NUMERIC 열은 NaN이 NULL로 바뀌므로 모두 nullable로 만들어집니다.
- PostGIS 타입, pgvector의 `vector`, 복합 타입, `hstore` 같은 맵 타입은 STRING으로 저장됩니다.

### 2.4 설정 방법

**사전 준비**

1. 프로젝트의 Postgres 버전이 16, 17, 18 중 하나인지 확인합니다.
2. 워크스페이스 관리자가 워크스페이스의 **Previews** 페이지에서 프리뷰를 켭니다.
3. 피드를 설정하는 사용자는 대상 카탈로그와 스키마에서 `USE CATALOG`, `USE SCHEMA`, `CREATE TABLE` 권한이 있어야 합니다.
4. Postgres 역할은 프로젝트에 대해 **CAN MANAGE** 권한이 있어야 합니다. 프로젝트 소유자는 기본으로 가집니다.
5. 대상 카탈로그의 관리형 스토리지가 기본 스토리지(default storage)면 지원되지 않습니다. Free Edition 워크스페이스에서는 관리형 스토리지 위치를 외부 위치(external location)로 둔 카탈로그를 만듭니다.

**테이블별 복제 식별자(REPLICA IDENTITY) 설정 (SQL)**

CDF가 테이블을 포함하려면 `REPLICA IDENTITY FULL`이어야 합니다. 설정하지 않으면 Postgres 로그에는 수정·삭제 시 기본 키만 남습니다.

```sql
ALTER TABLE playing_with_lakebase REPLICA IDENTITY FULL;
```

설정이 됐는지는 `pg_class`와 `pg_namespace`로 확인합니다. `replica_identity = 'full'`인 테이블만 CDF에 참여할 수 있습니다.

**피드 시작 (UI)**

1. 앱 스위처에서 **Lakebase Postgres** 를 열고 프로젝트와 브랜치를 선택합니다.
2. 상단 경로에서 **Branch overview** 를 열고 **Lakebase CDF** 탭으로 갑니다.
3. **Start** 를 클릭합니다.
4. 대화 상자에서 원본 **Database**, 원본 **Schema**(예: `public`), 대상 **To Catalog** 와 **Schema** 를 정합니다.
5. **Start** 를 다시 클릭합니다.

초기 스냅샷은 바로 시작되고, 대상 Delta 테이블이 생깁니다.

> **주의** 테이블을 추가할 때는 `ALTER TABLE ... REPLICA IDENTITY FULL`을 실행하고 **Start를 다시 누르지 마십시오**. 스키마에는 피드가 하나만 허용됩니다. 테이블은 최소 한 행이 있어야 동기화됩니다.

**상태 확인**

- Lakebase CDF 탭의 **Schemas** 와 **Tables** 하위 탭에서 상태를 봅니다.
- SQL로는 `SELECT * FROM wal2delta.tables;`를 실행합니다. 열은 `table_oid`, `status`, `committed_lsn`, `last_write_time`입니다.
- 상태 값은 `STREAMING`(또는 `Streaming`)과 `SNAPSHOTTING`(또는 `Snapshotting`), 그리고 제외된 테이블에 대한 `skipped`입니다.

**끄기**

Branch overview > Lakebase CDF 탭에서 **Disable** 을 누르고 확인합니다. 피드는 프로젝트의 모든 스키마에 대해 중지되며 컴퓨트를 다시 시작하지는 않는다고 문서가 설명합니다.

> **참고** 문서는 CDF를 프로그램으로 관리하는 방법으로 Postgres REST API와 Databricks SDK를 가리킵니다. 이 페이지 근거 문서에는 CDF 전용 CLI 명령이나 파라미터 이름이 없으므로 여기에 쓰지 않습니다. 자동화하기 전에 해당 API 레퍼런스를 확인하십시오.

### 2.5 제약과 주의

| 항목 | 내용 |
|---|---|
| 파티션 테이블 | 지원되지 않음. 스키마에 있으면 해당 테이블이 실패 |
| 빈 테이블 | 최소 한 행이 생길 때까지 제외 |
| 기본 키가 없는 테이블 | 문서가 명시하지 않음 |
| 스키마 변경 | 열 추가·삭제·타입 변경은 해당 테이블 **재스냅샷** 유발. 대상 Delta 테이블을 다시 씀 |
| 테이블 이름 변경 | 피드는 계속되며 대상 이름은 그대로 유지 |
| 원본 테이블 삭제 | 대상 Delta 테이블은 보존 |
| 지연 | 약 15초 단위로 묶어 기록 (설정 불가) |
| 프라이빗 엔드포인트 | 대상 카탈로그의 관리형 스토리지가 PrivateLink 인터페이스 엔드포인트나 공용 접근이 꺼진 Azure 프라이빗 엔드포인트로만 접근되면 CDF가 지원되지 않음. 공용으로 접근 가능한 스토리지를 쓰는 카탈로그가 우회 방법 |
| 클라우드 | 이 페이지 근거 문서(AWS)는 클라우드·리전 목록을 제공하지 않음. Azure 상세는 확인하지 않음 |

**대상 테이블에 하면 안 되는 설정**

- 대상 Delta 테이블에 행 필터나 열 마스크를 적용하면 CDF가 그 테이블에 쓰기를 멈춥니다.
- 대상 Delta 테이블에 Delta Lake 변경 데이터 피드를 켜지 마십시오. 원본 스키마가 바뀔 때 CDF가 수행하는 `ALTER TABLE` 재스냅샷을 깨뜨립니다.

> **주의** 대상 테이블을 하류에서 소비하는 패턴(증분 처리 등)은 CDF 문서의 "Build downstream pipelines" 절에 있습니다. 이 장의 조사에서는 그 절의 세부 내용을 원문으로 확인하지 못했으므로 여기에 쓰지 않습니다. 설계할 때 해당 절을 직접 확인하십시오.

### 2.6 CDF의 트레이드오프

| 측면 | 장점 | 비용·제약 |
|---|---|---|
| 이력 보존 | 모든 변경이 추가 전용으로 남음 | 대상 테이블이 계속 커짐 |
| 지연 | 약 15초 | 실시간 스트리밍은 아님 |
| 상태 | Public Preview | 프로덕션 의존성으로 설계하기 전 기능 상태와 제약을 확인 |
| 스키마 변경 | 자동으로 재스냅샷 | 대형 테이블에서는 재스냅샷 비용 발생 |

> **주의** Public Preview 기능입니다. 프로덕션 파이프라인에 넣기 전에 대상 워크스페이스에서 프리뷰 상태와 지원 리전을 확인하십시오.

## 3. 논리 복제 (Logical replication)

### 3.1 개요

논리 복제는 Postgres의 네이티브 복제 방식으로, 행 단위 변경을 **다른 Postgres 데이터베이스** 와 주고받습니다. 문서는 Lakebase가 다음 두 역할 중 하나를 맡을 수 있다고 설명합니다.

| 역할 | 의미 | 네트워크 방향 |
|---|---|---|
| 구독자(Subscriber) | 외부 발행자(publisher)의 변경을 받음 | Lakebase가 외부 발행자로 연결(dial out) |
| 발행자(Publisher) | 외부 구독자(subscriber)에게 변경을 보냄 | 외부 구독자가 Lakebase로 연결(dial in) |

문서가 든 사용 사례는 다음과 같습니다.

- 기존 Postgres 데이터베이스를 Lakebase로 마이그레이션
- Lakebase 리전 간 복제
- Lakebase의 변경을 외부 Postgres로 스트리밍

### 3.2 지원 범위 (문서 기준)

| 항목 | 내용 |
|---|---|
| 상태 | 문서 페이지에 상태 라벨 없음 |
| 클라우드 | AWS와 Azure. GCP는 문서에 언급 없음 |
| 네트워크 | 공용 네트워크 경로 사용. PrivateLink는 양방향 모두 미지원 |
| 구독자 연결 | 계정 네트워크 정책의 허용된 인터넷 대상을 따름 |
| 발행자 연결 | 워크스페이스 IP 접근 목록을 따름 |
| 같은 리전 복제 | Lakebase 데이터베이스 간 같은 리전 복제는 미지원. 리전 간 복제는 지원 |
| 실행 위치 | 주 컴퓨트에서 실행. 읽기 복제본에서는 실행되지 않음 |
| 복제 대상 | 데이터만 복제. 스키마는 복제되지 않음. 대상 테이블을 먼저 만들어야 함 |
| 스키마 변경 | 이후 스키마 변경은 복제되지 않음 |
| 외부 테이블(foreign table) | 복제되지 않음 |

> **주의** 논리 복제 페이지는 CDF와의 관계를 이렇게 안내합니다. 레이크하우스로 옮기는 목적이면 CDF를 쓰라는 것입니다. 두 기능을 같은 목적으로 섞어 설계하지 마십시오.

### 3.3 사용 시 확인할 사항

- 발행과 구독 설정에 필요한 권한과 워크스페이스 활성화 절차는 이 페이지의 근거 문서가 명시하지 않았습니다. 활성화 방법은 논리 복제 문서 원문과 Preview 메뉴를 확인하십시오.
- 발행과 구독의 `CREATE PUBLICATION`, `CREATE SUBSCRIPTION` 같은 SQL 명령과 필요한 역할(예: `databricks_superuser`) 요건도 이 근거 문서에 명시되지 않았습니다. 따라서 이 페이지에는 SQL 예시를 넣지 않았습니다.
- 복제 대상의 스키마는 자동으로 맞춰지지 않으므로, 대상 테이블을 먼저 같은 구조로 만들어야 합니다.

## 4. 어떤 기능을 고를까

| 목적 | 기능 | 이유 |
|---|---|---|
| Lakebase 변경 이력을 Delta로 분석 | CDF | 레이크하우스 쪽 출력이 목적. 문서가 권장 |
| 레이크하우스 데이터를 Lakebase로 서빙 | 동기화 테이블 | 방향이 반대. [동기화 테이블](synced-tables.md) 참조 |
| 외부 Postgres와 Lakebase를 실시간으로 맞춤 | 논리 복제 | 외부 Postgres와의 Postgres 간 복제가 목적 |
| Lakebase 데이터를 Unity Catalog 테이블로 조회 | 카탈로그 등록 | 조회만 필요하고 이력은 필요 없을 때. [Databricks Apps와 함께 쓰기](apps-integration.md)와 연결 페이지 참조 |

## 5. 주의사항

- **Preview 상태를 확인합니다.** CDF는 Public Preview입니다. 논리 복제는 페이지에 상태 라벨이 없으므로 워크스페이스에서 실제로 쓸 수 있는지 확인하십시오.
- **REPLICA IDENTITY FULL을 빠뜨리지 않습니다.** 빠지면 수정 이전 값이 로그에 남지 않아 CDF 이력이 불완전해집니다.
- **대상 테이블에 행 필터·열 마스크를 걸지 않습니다.** 걸면 CDF가 쓰기를 멈춥니다.
- **스키마 변경 비용을 계산합니다.** 열 변경은 재스냅샷을 일으킵니다. 대형 테이블에서는 변경 빈도를 고려하십시오.
- **네트워크 경로를 설계합니다.** 논리 복제는 PrivateLink를 지원하지 않습니다. 보안 요구사항이 PrivateLink를 요구하면 설계를 다시 검토하십시오.

## 참고 문서

- [Lakebase Change Data Feed (AWS)](https://docs.databricks.com/aws/en/oltp/projects/lakebase-cdf)
- [Quickstart: Store Postgres changes in the lakehouse (AWS)](https://docs.databricks.com/aws/en/oltp/projects/quickstart-lakebase-cdf)
- [Logical replication (AWS)](https://docs.databricks.com/aws/en/oltp/projects/logical-replication)
