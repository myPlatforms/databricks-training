# 관리형 vs 외부 테이블

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

Unity Catalog에서 테이블은 **관리형(Managed)** 과 **외부(External)** 두 유형으로 나뉩니다. 두 유형의 차이는 "데이터 파일의 수명을 누가 관리하는가"입니다. 관리형 테이블은 Databricks(Unity Catalog)가 데이터 파일의 저장, 최적화, 삭제까지 맡고, 외부 테이블은 메타데이터만 관리하고 데이터 파일은 사용자가 소유한 클라우드 스토리지에 둡니다. 이 페이지는 두 유형을 구분하는 기준, 생성 문법, 삭제 동작, 외부 쓰기의 주의점을 다룹니다.

## 1. 왜 필요한가

테이블을 만들 때 가장 먼저 정해야 하는 질문은 다음 두 가지입니다.

| 질문 | 관리형이 맞는 경우 | 외부가 맞는 경우 |
|---|---|---|
| 데이터 파일 위치를 직접 정해야 하는가 | 아니오. Unity Catalog가 위치를 정함 | 예. 기존 버킷·경로를 그대로 써야 함 |
| 테이블을 지우면 파일도 지워져야 하는가 | 예. `DROP`이 파일 수명과 함께 정리 | 아니오. 파일은 남기고 메타데이터만 제거 |
| 다른 시스템이 같은 파일 경로를 직접 쓰는가 | 아니오 | 예. 외부 파이프라인이 파일을 계속 적재 |
| 최적화와 유지보수를 맡기고 싶은가 | 예. 자동 최적화 대상 | 아니오. 사용자가 직접 관리 |

공식 문서는 새 테이블에 대해서는 관리형 테이블을 권장합니다. 자동 최적화, 더 빠른 쿼리, 더 낮은 비용을 근거로 듭니다. 외부 테이블은 기존 데이터 레이크를 그대로 두고 Unity Catalog로 조회·권한을 붙이고 싶을 때 씁니다.

## 2. 어떻게 동작하는가

### 비교표

| 항목 | 관리형 테이블 (Managed) | 외부 테이블 (External) |
|---|---|---|
| 데이터 파일 저장 위치 | 테이블이 속한 스키마 또는 카탈로그의 관리형 저장소 | 사용자가 지정한 외부 위치(External location)의 경로 |
| 데이터 수명 관리 | Unity Catalog가 관리 | 사용자가 관리 (Unity Catalog는 메타데이터만) |
| 최적화 (OPTIMIZE, VACUUM, 예측 최적화) | 대상 | 사용자가 직접 실행. 문서상 Unity Catalog가 레이아웃을 관리하지 않음 |
| `DROP TABLE` 동작 | 메타데이터와 데이터 파일 모두 정리 | 메타데이터만 제거. 데이터 파일은 남음 |
| 기본 형식 | Delta Lake (Iceberg는 `USING iceberg`로 지정) | 문서 기준으로 Delta 등 사용자가 지정한 형식 |
| 경로 기반 접근 | 지원되지 않음 (Compatibility Mode 제외) | 외부 시스템이 파일에 직접 접근하면 Unity Catalog 권한이 적용되지 않음 |
| 외부 엔진 접근 | Unity REST API (Delta), Iceberg REST 카탈로그 (Iceberg) | 엔진이 파일을 직접 읽음. 권한은 Unity Catalog 밖 |
| 비용 구조 | 저장·조회 비용이 낮다고 문서가 설명 | 외부 스토리지 비용을 사용자가 부담 |

> **참고** 관리형 테이블의 "저장·조회 비용이 낮다"는 설명은 공식 문서의 표현입니다. 구체적인 금액은 이 장에서 다루지 않습니다. 비용 산정은 해당 페이지의 단가 기준을 따르십시오.

### 관리형 테이블의 저장 위치

관리형 테이블의 데이터 파일은 테이블이 들어 있는 **스키마 또는 카탈로그** 의 저장 위치에 놓입니다. 사용자가 개별 경로를 정할 수 없습니다. 이 구조 때문에 관리형 테이블은 `DROP` 시 파일까지 정리할 수 있습니다.

### 외부 테이블의 저장 위치

외부 테이블은 **외부 위치(External location)** 를 통해서만 만들 수 있습니다. 외부 위치는 Unity Catalog에 등록된 클라우드 스토리지 경로와 자격 증명의 조합입니다. 공식 문서는 외부 테이블 생성 시 "저장 위치를 지정해야 한다"고 설명합니다.

## 3. 어떻게 쓰는가

### 3.1 관리형 Delta 테이블

```sql
CREATE TABLE main.sales.orders (
  order_id  BIGINT,
  customer  STRING,
  amount    DECIMAL(12, 2),
  order_ts  TIMESTAMP
);
```

### 3.2 관리형 Iceberg 테이블

```sql
CREATE TABLE main.sales.orders_iceberg (
  order_id  BIGINT,
  customer  STRING,
  amount    DECIMAL(12, 2),
  order_ts  TIMESTAMP
) USING ICEBERG;
```

관리형 Iceberg 테이블에는 `LOCATION` 절을 쓸 수 없습니다. Iceberg 형식의 세부 사항은 [Apache Iceberg 지원](iceberg-support.md)을 참고하십시오.

### 3.3 외부 테이블

외부 테이블은 `LOCATION`에 클라우드 스토리지 경로를 지정합니다. 아래 예의 버킷 경로는 자리표시자입니다. 실제 경로는 Unity Catalog에 등록된 외부 위치 아래에 있어야 합니다.

```sql
CREATE TABLE main.raw.clickstream_ext (
  event_id  BIGINT,
  user_id   STRING,
  event_ts  TIMESTAMP
)
LOCATION 's3://<bucket-path>/<table-directory>';
```

### 3.4 외부 쓰기 정책 확인

Unity Catalog 관리형 Delta 테이블은 외부 엔진에서 생성과 쓰기가 가능합니다. 2026-10-13 릴리스 노트는 "External writes to managed Delta tables are now generally available"을 GA로 발표했으며, 외부 Apache Spark 클라이언트가 대상입니다. 이 쓰기에는 **카탈로그 커밋(Catalog commits)** 이 켜져 있어야 합니다.

테이블 유형별로 외부 클라이언트가 할 수 있는 작업은 다음과 같습니다.

| 테이블 | 외부 클라이언트 경로 | 읽기 | 쓰기 |
|---|---|---|---|
| 관리형 Delta | Unity REST API | 가능 | 가능 (카탈로그 커밋 필요) |
| 관리형 Iceberg | Iceberg REST 카탈로그 | 가능 | 가능 |
| Delta, Iceberg 읽기 활성화 | Iceberg REST 카탈로그 | 가능 | 불가 |
| 외부 Delta, Iceberg 읽기 활성화 | Iceberg REST 카탈로그 | 가능 | 불가 |

> **참고** 관리형 테이블의 외부 쓰기 GA 발표는 2026-10 릴리스 노트에 있습니다. 이전에 "관리형 테이블은 외부에서 조작할 수 없다"는 식으로 정리된 자료가 있다면, 현재 기준으로는 그 설명이 맞지 않으므로 갱신이 필요합니다.

### 3.5 삭제 복구 기간 (Preview)

관리형 테이블을 `DROP`한 뒤 복구 가능한 기간을 설정하는 기능은 문서 기준 **Public Preview** 입니다. 상태가 바뀔 수 있으므로 적용 전 원문을 확인하십시오.

## 4. 트레이드오프

### 관리형 테이블

| 장점 | 비용·제약 |
|---|---|
| 자동 최적화와 유지보수 | 파일 경로를 직접 지정할 수 없음 |
| `DROP`이 파일까지 정리 | 같은 파일을 다른 시스템이 직접 쓰는 구조에는 맞지 않음 |
| Unity Catalog 권한과 파일 접근이 일치 | 경로 기반 접근이 막힘 (Compatibility Mode 예외) |
| 외부 엔진 쓰기 경로 제공 (위 표 참고) | 외부 쓰기에는 카탈로그 커밋 등 전제가 있음 |

### 외부 테이블

| 장점 | 비용·제약 |
|---|---|
| 기존 데이터 위치를 그대로 유지 | 최적화와 파일 레이아웃을 사용자가 관리 |
| 다른 시스템과 파일을 공유하기 쉬움 | Unity Catalog 권한이 파일 접근에 적용되지 않음 |
| `DROP`해도 데이터가 남아 안전 | 데이터 정리는 사용자 몫 |
| 기존 파이프라인과 병행 가능 | 외부에서 메타데이터가 바뀌면 동기화가 필요함 |

### 언제 외부 테이블을 쓰지 않는가

- 새로 적재하는 데이터를 Databricks 안에서만 쓴다면 관리형 테이블이 기본 선택입니다.
- 외부 파이프라인이 같은 파일을 계속 쓰는 구조라면 외부 테이블은 메타데이터 동기화와 권한 우회 문제를 함께 안고 가야 합니다. 쓰기 주체를 하나로 정하는 편이 낫습니다.

## 5. 주의사항

> **주의** 외부 테이블 경로에 Unity Catalog 밖의 도구나 다른 워크스페이스가 직접 접근하면 Unity Catalog 권한이 적용되지 않습니다. 공식 문서는 외부 시스템이 데이터 파일에 접근할 때 Unity Catalog 권한이 강제되지 않는다고 설명합니다.

> **주의** 외부 테이블을 `DROP`하면 데이터 파일은 남습니다. 파일을 지우려면 스토리지에서 직접 삭제해야 합니다. 관리형 테이블의 `DROP`과 기대 동작이 다르므로 운영 절차에 명시하십시오.

- **메타데이터 동기화:** 비-Databricks 클라이언트가 메타데이터를 바꾸거나, Databricks에서 경로 기반 접근으로 바꾼 경우 Unity Catalog가 자동으로 동기화하지 않습니다. 공식 문서는 이런 방식을 권하지 않으며, 발생했다면 `MSCK REPAIR TABLE <table-name> SYNC METADATA`를 실행하라고 안내합니다.

```sql
MSCK REPAIR TABLE main.raw.clickstream_ext SYNC METADATA;
```

- **외부 위치를 여러 메타스토어에 붙이지 않습니다.** 공식 문서는 S3 외부 위치 하나가 여러 메타스토어에 연결되어 있으면, 그 위치의 외부 테이블에 여러 메타스토어에서 쓰기를 하면 일관성 문제가 생길 수 있다고 설명합니다. 읽기는 안전하다고 합니다.
- **스키마 강제는 Delta 테이블에 적용됩니다.** 외부 테이블의 메타데이터가 외부에서 바뀌면 스키마 강제가 제대로 동작하지 않을 수 있습니다. 동기화 명령을 확인하십시오 ([Delta Lake 동작 원리](delta-lake-internals.md) 참고).
- **관리형 테이블을 외부 경로처럼 쓰지 마십시오.** 파일 경로를 직접 읽거나 쓰는 방식은 Compatibility Mode 외에는 지원되지 않습니다.
- **외부 테이블을 새로 만들기 전에 외부 위치와 권한을 먼저 확인합니다.** 외부 위치가 없으면 `LOCATION` 생성이 실패합니다.

## 참고 문서

- [Databricks tables](https://docs.databricks.com/aws/en/tables/)
- [Unity Catalog managed tables for Delta Lake and Apache Iceberg](https://docs.databricks.com/aws/en/tables/managed)
- [Work with external tables](https://docs.databricks.com/aws/en/tables/external)
- [Access Databricks tables from Apache Iceberg clients](https://docs.databricks.com/aws/en/external-access/iceberg)
- [Transactions](https://docs.databricks.com/aws/en/transactions)
