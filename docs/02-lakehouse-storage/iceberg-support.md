# Apache Iceberg 지원

> 기준일: 2026-10-28 · 근거: 공식 문서

Apache Iceberg는 Delta Lake와 같은 오픈 테이블 포맷이지만, 여러 엔진이 같은 테이블을 읽고 쓰는 시나리오에 더 초점을 둔 포맷입니다. Databricks는 Unity Catalog 안에서 Iceberg 테이블을 **관리형(Managed)** 으로 만들 수 있고, Iceberg REST 카탈로그 API를 통해 외부 Iceberg 엔진이 접근하게 할 수 있습니다. 또한 Delta 테이블에 Iceberg 메타데이터를 덧붙여 Iceberg 클라이언트가 읽게 하는 방법도 있습니다. 이 페이지는 세 가지 경로를 구분하고, 외부 클라이언트가 할 수 있는 작업을 표로 정리합니다.

## 1. 왜 필요한가

한 조직에서 같은 데이터를 여러 엔진이 씁니다. Spark, Trino, DuckDB, 그 밖의 분석 엔진이 각자 데이터를 복사해 두면 다음 문제가 생깁니다.

| 문제 | 설명 |
|---|---|
| 데이터 중복 | 엔진마다 복사본을 두면 저장 비용과 정합성 관리 비용이 늘어납니다 |
| 최신성 차이 | 복사 주기에 따라 엔진마다 다른 시점의 데이터를 봅니다 |
| 권한 분산 | 복사본마다 권한을 따로 관리해야 합니다 |

Iceberg를 Unity Catalog와 함께 쓰면 하나의 테이블을 여러 엔진이 같은 카탈로그를 통해 접근할 수 있습니다. 다만 "누가 무엇을 쓸 수 있는가"는 테이블 유형과 클라이언트에 따라 다르므로 아래 표를 기준으로 설계해야 합니다.

## 2. 어떻게 동작하는가

### 세 가지 경로

| 경로 | 테이블 유형 | 설명 | 외부 클라이언트 쓰기 |
|---|---|---|---|
| 관리형 Iceberg 테이블 | Unity Catalog 관리형 (Iceberg 형식) | Unity Catalog가 데이터·메타데이터·최적화를 관리 | 가능 (Iceberg REST 카탈로그 경유) |
| Delta + Iceberg 읽기 (UniForm) | 관리형 또는 외부 Delta 테이블 | Delta 로그와 함께 Iceberg 메타데이터를 생성 | 불가 (읽기 전용) |
| 외부 Iceberg (Foreign Iceberg) | 외부 카탈로그 기반 연합 테이블 | Lakehouse Federation으로 외부 Iceberg 카탈로그를 등록 | 불가 (읽기 전용) |

공식 문서는 Unity Catalog 관리형 테이블이 Delta Lake와 Apache Iceberg를 모두 지원한다고 설명합니다. 관리형 테이블은 Unity Catalog가 읽기, 쓰기, 저장, 최적화를 담당하며, 외부 엔진은 공개 API로 접근합니다.

### Iceberg REST 카탈로그 (IRC)

외부 Iceberg 클라이언트는 Unity Catalog의 Iceberg REST 카탈로그 API로 접근합니다. 엔드포인트 경로 패턴은 `/api/2.1/unity-catalog/iceberg-rest`이며, 인증은 Databricks 개인 액세스 토큰(PAT) 또는 OAuth를 사용합니다.

### 외부 클라이언트가 할 수 있는 작업

문서의 표를 그대로 옮긴 내용입니다.

| 테이블 유형 | 읽기 | 쓰기 |
|---|---|---|
| 관리형 Iceberg (Managed Iceberg) | 가능 | 가능 |
| 외부 Iceberg (Foreign Iceberg) | 가능 | 불가 |
| 관리형 Delta, Iceberg 읽기 활성화 | 가능 | 불가 |
| 외부 Delta, Iceberg 읽기 활성화 | 가능 | 불가 |

외부 Iceberg(Foreign) 테이블은 최신 스냅샷을 읽으려면 `REFRESH FOREIGN TABLE`로 수동 갱신해야 합니다.

### 상태 라벨

| 기능 | 상태 | 근거 |
|---|---|---|
| 관리형 Iceberg 테이블 (기본 기능) | 기능 페이지에 상태 라벨 없음 (문서 명시 없음) | Iceberg v3 페이지, Iceberg 개요 |
| 관리형 Iceberg 구체화 뷰 (Managed Iceberg materialized views) | Public Preview | Iceberg 개요 페이지 |
| 관리형 Iceberg 테이블 공유 (Sharing managed Iceberg tables) | GA (2026-08-14 릴리스 노트) | 릴리스 노트 |
| Iceberg 클라이언트에 Delta 테이블 노출 (OpenSharing 수신자) | Public Preview (페이지 표기: "in Public Preview") | Delta와 Iceberg 클라이언트 접근 페이지 |
| Iceberg v3 테이블 (관리형) | 기능 페이지에 상태 라벨 없음 (문서 명시 없음). 요구 조건: Databricks Runtime 18 LTS 이상 | Iceberg v3 페이지 |
| 리퀴드 클러스터링 (Iceberg 테이블) | Public Preview, Databricks Runtime 16.4 LTS 이상 | 리퀴드 클러스터링 페이지 |
| 관리형 Iceberg 트랜잭션 | 릴리스 노트 2026-10-14 "Transactions support both managed Delta Lake and Apache Iceberg tables"에 GA로 표기 (기능 페이지에는 라벨 없음) | 트랜잭션 페이지, 릴리스 노트 |

> **참고** 관리형 Iceberg 테이블 자체의 GA 라벨은 기능 페이지에서 확인되지 않았습니다. 상태를 발표 자료에 쓰기 전에 릴리스 노트와 현재 제품 페이지를 함께 확인하십시오.

## 3. 어떻게 쓰는가

### 3.1 관리형 Iceberg 테이블 만들기

관리형 Iceberg 테이블은 Unity Catalog 안에서 `USING iceberg`로 만듭니다. 공식 문서 기준으로 Iceberg 테이블은 Unity Catalog에 만들어야 하며, 관리형 Iceberg 테이블에는 `LOCATION` 절을 쓸 수 없습니다.

```sql
CREATE TABLE main.sales.orders_iceberg (
  order_id  BIGINT,
  customer  STRING,
  amount    DECIMAL(12, 2),
  order_ts  TIMESTAMP
) USING ICEBERG;
```

### 3.2 Iceberg v3 테이블 만들기

Iceberg v3 기능(삭제 벡터 기본 활성화, VARIANT 등)을 쓰려면 `format-version` 속성을 3으로 지정합니다.

```sql
CREATE OR REPLACE TABLE main.sales.orders_v3 (
  order_id  BIGINT,
  payload   VARIANT
)
USING iceberg
TBLPROPERTIES ('format-version' = 3);
```

> **주의** 공식 Iceberg v3 페이지의 예제는 `USING iceberg`와 `TBLPROPERTIES` 사이에 공백이 빠져 보입니다(렌더링 문제로 추정). 위 예제는 공백을 넣은 형태입니다. 실행 전에 원문을 한 번 더 확인하십시오.

Iceberg v3 테이블의 주요 특징과 제한은 다음과 같습니다.

| 항목 | 내용 |
|---|---|
| 삭제 벡터 | 새 Iceberg v3 테이블에서 기본 활성화. 행 단위 삭제를 데이터 파일 재작성 없이 처리 |
| VARIANT | 반정형 데이터 저장과 처리 |
| 행 계보 (Row lineage) | 테이블 데이터의 증분 변경 추적 (자동 CDF의 기반) |
| GEOMETRY, GEOGRAPHY | 공간 데이터 저장과 조회 |
| 쓰기 기본값 (Write defaults) | 쓰기에서 컬럼이 생략되면 값 지정 |
| 제한 | 초기 기본값(Initial defaults), `unknown` 타입, 나노초 정밀도 타임스탬프, 다중 인자 변환은 지원되지 않음 |

### 3.3 외부 Iceberg 클라이언트에서 쓰기 제약

관리형 Iceberg 테이블에 외부 클라이언트가 쓸 때는 다음 제약을 지켜야 합니다.

- 외부 클라이언트는 `UUID`, `Fixed(L)`, `TIME`, 필수 필드를 가진 중첩 `STRUCT` 타입으로 관리형 Iceberg 테이블을 만들 수 없습니다.
- 외부 클라이언트는 스냅샷 만료(expire snapshots)나 고아 파일 제거(remove orphan files) 같은 테이블 유지보수를 실행할 수 없습니다.
- 관리형 Iceberg v3 테이블에서 `DELETE`, `UPDATE`, `MERGE`를 실행하려면 클라이언트가 **Copy-on-write** 모드를 쓰거나, 삭제된 행을 ** 삭제 벡터** 로 기록해야 합니다.
- 클라이언트가 Equality delete 파일을 쓰면 Unity Catalog가 커밋을 거부하며, 클라이언트는 `Can not create a Path from a null string [ErrorCode: 2015]` 오류를 받습니다.
- 공식 문서는 Iceberg 사양상 한 스냅샷에 중복 데이터 파일을 둘 수 없으며, Unity Catalog는 외부 엔진이 중복 데이터 파일을 커밋하는 것을 막는다고 설명합니다.

### 3.4 UniForm: Delta 테이블을 Iceberg 클라이언트에 노출하기

UniForm(Universal Format)은 Delta 테이블의 데이터 파일을 복사하지 않고, Delta 로그 옆에 Iceberg 메타데이터를 비동기로 만들어 주는 기능입니다. 데이터 파일 한 벌을 Delta와 Iceberg 클라이언트가 함께 읽습니다. 현재 공식 문서는 이 기능을 "Read Delta Lake tables with Iceberg clients" 페이지에서 설명합니다.

새 테이블을 만들면서 켜는 예:

```sql
CREATE TABLE main.sales.orders_uniform (c1 INT)
TBLPROPERTIES (
  'delta.columnMapping.mode' = 'id',
  'delta.enableIcebergCompatV2' = 'true',
  'delta.universalFormat.enabledFormats' = 'iceberg'
);
```

기존 테이블에 켜는 예(Databricks Runtime 15.4 LTS 이상):

```sql
ALTER TABLE main.sales.orders SET TBLPROPERTIES (
  'delta.columnMapping.mode' = 'name',
  'delta.enableIcebergCompatV2' = 'true',
  'delta.universalFormat.enabledFormats' = 'iceberg'
);
```

설정이 제대로 됐는지는 두 속성을 확인합니다. `delta.enableIcebergCompatV2`는 `true`, `delta.universalFormat.enabledFormats`는 `iceberg`여야 합니다.

#### UniForm 전제 조건

| 항목 | 요구 사항 |
|---|---|
| 카탈로그 | Unity Catalog에 등록된 테이블 (관리형·외부 모두 지원) |
| 컬럼 매핑 | 활성화 필요. `IcebergCompatV2`를 켠 뒤에는 `columnMapping` 기능을 제거할 수 없음 |
| 테이블 프로토콜 | `minReaderVersion` 2 이상, `minWriterVersion` 7 이상 |
| 쓰기 런타임 | Databricks Runtime 14.3 LTS 이상 |
| 삭제 벡터 | Iceberg 읽기가 켜진 테이블에서는 삭제 벡터를 켤 수 없음. 기존 테이블에 삭제 벡터가 있다면 `REORG`로 끄고 정리 |

#### UniForm 제약

| 항목 | 내용 |
|---|---|
| 클라이언트 쓰기 | Iceberg 클라이언트 지원은 읽기 전용. 쓰기는 지원되지 않음 |
| 삭제 벡터 | Iceberg v2 읽기에서는 지원되지 않음. Iceberg v3에서는 지원 |
| 구체화 뷰·스트리밍 테이블 | `IcebergCompatV2`로 Iceberg 읽기를 켤 수 없음. 파이프라인이 관리하는 객체는 `IcebergCompatV3` 사용 |
| 접근 방식 | 자동 Iceberg 메타데이터 생성은 경로(path)가 아닌 이름(name)으로 접근해야 트리거됨 |
| 데이터 타입 | `VOID` 타입이 있는 테이블은 지원되지 않음 |
| 레거시 CDF | Delta 클라이언트용 레거시 변경 데이터 피드는 동작하지만 Iceberg에서는 지원되지 않음 |

> **참고** 공식 문서는 `IcebergCompatV1`을 레거시 콘텐츠로 분리해 두고 있습니다. 새 테이블에는 `delta.enableIcebergCompatV2`를 사용하십시오.

### 3.5 Iceberg 클라이언트에서 읽기 예 (외부 엔진)

외부 엔진의 설정 방법은 엔진마다 다르므로 이 페이지에서는 공식 문서의 링크만 제공합니다. Databricks 측 설정은 "Access Databricks tables from Apache Iceberg clients"(`/aws/en/external-access/iceberg`) 페이지를 참고하십시오. 엔진에 넘기는 값은 카탈로그의 REST 엔드포인트와 인증 정보입니다. 인증 토큰은 코드나 노트북에 하드코딩하지 말고, 보안 저장소에서 읽어 쓰십시오.

## 4. 트레이드오프

| 선택 | 장점 | 비용·제약 |
|---|---|---|
| 관리형 Iceberg | 외부 엔진이 쓰기까지 가능. Unity Catalog가 최적화 | 외부 쓰기에 타입·유지보수 제약이 있음. 외부에서 스냅샷 만료 불가 |
| UniForm (Delta + Iceberg 읽기) | 데이터 파일 한 벌로 두 형식 제공 | 외부 쓰기 불가. 삭제 벡터·VOID 등 제약. Iceberg 메타데이터는 비동기로 생성됨 |
| 외부 Iceberg (Foreign) | 기존 외부 카탈로그를 그대로 두고 조회 | 읽기 전용. 수동 갱신 필요 |

### 언제 쓰지 않는가

- 외부 엔진이 **쓰기** 를 해야 하고 테이블을 Databricks에서 관리할 수 있다면 관리형 Iceberg가 맞습니다. 반대로 외부 엔진만 쓰고 Databricks는 읽기만 한다면 외부 Iceberg 카탈로그를 연합(Federation)으로 연결하는 편이 단순합니다.
- Iceberg 클라이언트가 읽기만 한다면 UniForm으로 Delta 테이블을 유지하는 것이 기존 파이프라인을 바꾸지 않아도 됩니다.

## 5. 주의사항

- **테이블 유형을 먼저 정합니다.** 외부 엔진의 쓰기 필요 여부에 따라 관리형 Iceberg와 UniForm 중 무엇을 쓸지 달라지므로, 설계 단계에서 쓰기 주체를 확정하십시오. 두 방식 사이의 전환 절차는 이 장의 문서 범위에서 확인하지 않았습니다.
- **외부 클라이언트의 DELETE·UPDATE·MERGE 모드를 확인합니다.** Copy-on-write 또는 삭제 벡터 기록 방식을 지원하지 않는 엔진은 실패합니다.
- **UniForm을 켠 테이블에 삭제 벡터를 켜지 않습니다.** 공식 문서가 금지하는 조합입니다(Iceberg v3 테이블 제외).
- **Iceberg 클라이언트의 기능 지원 범위를 확인합니다.** 공식 문서도 "개별 Iceberg 클라이언트는 자체 제한이 있을 수 있다"고 설명합니다.
- **상태 라벨을 발표 자료에 그대로 옮기지 않습니다.** 같은 기능이라도 기능 페이지, 릴리스 노트, 구 명칭 문서의 표기가 다를 수 있습니다.

## 참고 문서

- [What is Apache Iceberg in Databricks?](https://docs.databricks.com/aws/en/iceberg/)
- [Apache Iceberg v3 in Databricks](https://docs.databricks.com/aws/en/iceberg/iceberg-v3)
- [Access Databricks tables from Apache Iceberg clients](https://docs.databricks.com/aws/en/external-access/iceberg)
- [Read Delta Lake tables with Iceberg clients](https://docs.databricks.com/aws/en/delta/uniform)
- [Unity Catalog managed tables for Delta Lake and Apache Iceberg](https://docs.databricks.com/aws/en/tables/managed)
- [Databricks tables](https://docs.databricks.com/aws/en/tables/)
- [Transactions](https://docs.databricks.com/aws/en/transactions)
- [Use liquid clustering for tables](https://docs.databricks.com/aws/en/delta/clustering)
