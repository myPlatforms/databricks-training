# 삭제 벡터 (Deletion vectors)

> 기준일: 2026-10-28 · 근거: 공식 문서

삭제 벡터(Deletion vectors)는 Delta Lake와 Apache Iceberg 테이블에서 `DELETE`, `UPDATE`, `MERGE`를 빠르게 처리하기 위한 기능입니다. 행 하나를 지우거나 고칠 때 그 행이 들어 있는 Parquet 파일 전체를 다시 쓰지 않고, 어떤 행이 삭제되었는지를 **메타데이터에 표시** 해 둡니다. 읽는 쪽은 그 표시를 적용해서 현재 데이터를 보여 줍니다. 이 페이지는 이 방식이 왜 필요한지, 어떻게 켜고 확인하는지, 그리고 파일을 실제로 정리하는 `REORG`·`PURGE`·`VACUUM` 흐름을 다룹니다.

## 1. 왜 필요한가

삭제 벡터가 없을 때 Delta Lake는 행 하나를 바꾸더라도 그 행이 속한 파일 전체를 새 파일로 다시 씁니다. 파일 하나에 행이 수백만 개 들어 있다면, 행 한 개를 고치는 데 파일 한 개 분량의 쓰기가 필요합니다.

| 상황 | 삭제 벡터 없음 | 삭제 벡터 있음 |
|---|---|---|
| 행 1개 삭제 | 해당 행이 있는 파일 전체를 재작성 | 삭제 표시만 메타데이터에 기록. 데이터 파일은 그대로 |
| 산발적인 `MERGE` 갱신 | 갱신이 흩어진 파일마다 재작성 | 갱신 행을 표시하고 필요할 때 정리 |
| 쓰기 비용 | 파일 크기에 비례 | 변경된 행 수에 비례 (대략적인 경향) |
| 읽기 비용 | 파일이 깨끗함 | 읽을 때 삭제 표시를 적용하므로 정리 전에는 약간의 부담 |

공식 문서는 삭제 벡터가 `DELETE`, `UPDATE`, `MERGE`를 가속한다고 설명합니다. 핵심은 **쓰기 시점의 비용을 줄이고, 파일 정리를 나중으로 미루는 것** 입니다.

## 2. 어떻게 동작하는가

### 쓰기 경로

1. 쓰기 작업이 삭제 또는 갱신 대상 행을 찾습니다.
2. 해당 행이 들어 있는 데이터 파일은 그대로 두고, 행의 위치를 삭제 벡터 메타데이터에 기록합니다.
3. 갱신의 경우 새 값은 새 파일에 기록되고, 이전 값은 삭제 벡터로 가려집니다.

### 읽기 경로

읽기 엔진은 데이터 파일을 스캔할 때 삭제 벡터를 함께 적용해, 표시된 행을 결과에서 빼고 보여 줍니다. 그래서 같은 테이블을 읽는 모든 클라이언트가 같은 결과를 봅니다.

### 정리 경로

삭제 벡터가 쌓이면 실제 데이터 파일에는 의미 없는 행이 남습니다. 이를 정리하는 방법은 세 가지입니다.

| 방법 | 동작 | 비고 |
|---|---|---|
| `OPTIMIZE` | 파일을 다시 쓰면서 삭제 표시된 행을 반영 | 파일 압축 이벤트는 삭제 벡터 변경을 해결하는 엄격한 보장이 없다고 공식 문서가 설명 |
| `REORG TABLE ... APPLY (PURGE)` | 삭제 표시된 행을 물리적으로 제거하도록 파일을 재작성 | 삭제 벡터를 끄거나 정리할 때 씀 |
| 자동 압축 (auto-compaction) 포함 쓰기 | 쓰기 중 파일을 압축하면서 정리 | 공식 문서는 세 가지 방법 중 하나로 파일을 재작성할 수 있다고 설명 |

물리 삭제까지 끝내려면 `REORG ... APPLY (PURGE)` 후 `VACUUM`을 실행해 옛 파일을 지웁니다. 자세한 흐름은 아래 3.4 절에서 봅니다.

### 개념 비교

| 개념 | 역할 | 이 페이지에서의 위치 |
|---|---|---|
| 데이터 파일 | 행이 실제로 들어 있는 Parquet | 쓰기 때 재작성되지 않음 (삭제 벡터 사용 시) |
| 삭제 벡터 | 어떤 행이 무효인지 기록 | 쓰기 때 갱신 |
| `OPTIMIZE` | 작은 파일 합치기와 재배치 | 정리의 한 방법 |
| `REORG ... PURGE` | 삭제 표시 행을 물리적으로 제거 | 정리의 강한 방법 |
| `VACUUM` | 참조되지 않는 옛 파일 삭제 | 보존 기간 적용 |

## 3. 어떻게 쓰는가

### 3.1 새 테이블에서 켜기 (Delta)

```sql
CREATE TABLE main.sales.orders_dv (
  order_id  BIGINT,
  customer  STRING,
  amount    DECIMAL(12, 2)
)
TBLPROPERTIES ('delta.enableDeletionVectors' = true);
```

### 3.2 기존 테이블에서 켜기 (Delta)

```sql
ALTER TABLE main.sales.orders
SET TBLPROPERTIES ('delta.enableDeletionVectors' = true);
```

> **주의** 삭제 벡터를 켜면 테이블 프로토콜이 올라갑니다. 삭제 벡터를 지원하지 않는 클라이언트는 이 테이블을 읽을 수 없습니다. 외부 엔진과 공유하기 전에 호환성을 확인하십시오.

### 3.3 Iceberg 테이블에서 켜기

Iceberg 테이블에서는 속성 이름이 다릅니다.

```sql
ALTER TABLE main.sales.orders_iceberg
SET TBLPROPERTIES ('iceberg.enableDeletionVectors' = true);
```

공식 문서는 모든 Apache Iceberg v3 테이블에 삭제 벡터가 기본으로 포함된다고 설명합니다. v3 테이블에서는 위 속성을 따로 켤 필요가 없을 수 있습니다. 설정 전 원문을 확인하십시오.

### 3.4 물리 정리: REORG와 VACUUM

삭제 벡터로 표시된 행을 파일에서 실제로 없애려면 `REORG`를 씁니다. 공식 문서는 이후 `VACUUM`을 **퍼지(purge) 완료 시점을 보존 기준으로 삼아** 실행하라고 설명합니다.

```sql
-- 삭제 표시 행을 물리적으로 제거
REORG TABLE main.sales.orders APPLY (PURGE);
```

퍼지가 끝난 뒤 `VACUUM`을 실행하되, 보존 기준을 퍼지 완료 시각으로 맞춥니다. 이 보존 기준을 지정하는 구문은 공식 문서 예시를 그대로 따르십시오. 이 장에서는 구문을 추측해 싣지 않았습니다.

대용량 테이블에서는 퍼지 모드를 `rows`로 바꾸는 설정을 공식 문서가 권장합니다. 기본값은 `all`입니다.

```python
# 대용량 테이블에서 퍼지 모드를 행 단위로 설정
spark.conf.set("spark.databricks.delta.reorg.purgeMode", "rows")
```

> **참고** `VACUUM`의 보존 기준을 퍼지 완료 시각으로 맞추라는 안내는 공식 문서의 삭제 벡터 페이지 설명입니다. 정확한 타임스탬프 지정 문법은 실행 전에 해당 페이지의 예시를 확인하십시오.

## 4. 트레이드오프

| 항목 | 장점 | 비용·제약 |
|---|---|---|
| 쓰기 성능 | `DELETE`, `UPDATE`, `MERGE` 가속 | 정리 전까지 파일에 무효 행이 남음 |
| 저장 공간 | 쓰기 중 재작성량 감소 | 정리 전까지 죽은 행이 쌓여 공간을 더 씀 |
| 읽기 성능 | 정리 후에는 일반 파일과 같음 | 정리 전에는 삭제 표시를 적용하는 비용이 있음 |
| 호환성 | Databricks Runtime 12.2 LTS 이상에서 읽기 | 프로토콜 상승으로 구 클라이언트가 읽지 못할 수 있음 |
| 정리 | `OPTIMIZE`, `REORG`로 정리 가능 | 정리 작업 자체가 파일을 재작성하므로 비용이 들음 |

### 런타임 요구 사항 (공식 문서)

| 목적 | 최소 런타임 |
|---|---|
| 삭제 벡터를 쓰면서 모든 최적화 사용 | Databricks Runtime 14.3 LTS 이상 |
| 읽기 | Databricks Runtime 12.2 LTS 이상 |
| 행 수준 동시성 | Databricks Runtime 14.2 이상 |

### 언제 쓰지 않는가

- 삭제·갱신이 거의 없는 **추가 전용(append-only)** 테이블이라면 삭제 벡터의 이득이 작습니다.
- 외부 클라이언트가 삭제 벡터를 지원하지 않는다면 프로토콜 상승 때문에 읽기 실패가 생깁니다. 공유 대상을 먼저 확인하십시오.

## 5. 주의사항

> **주의** Iceberg 읽기가 켜진 Delta 테이블에서는 삭제 벡터를 켤 수 없습니다. 공식 문서는 Iceberg v2 읽기에서 삭제 벡터를 지원하지 않는다고 설명합니다. 반대로 Iceberg v3 테이블은 삭제 벡터를 지원합니다. UniForm을 쓸 계획이라면 [Apache Iceberg 지원](iceberg-support.md)의 제약을 함께 확인하십시오.

> **주의** 기존 Delta 테이블에 삭제 벡터가 있고 Iceberg 읽기를 켜려면, 먼저 `REORG`로 삭제 벡터를 끄고 정리해야 합니다. 공식 문서가 안내하는 순서입니다.

- **정리 계획 없이 켜지 않습니다.** 삭제 벡터는 정리 작업과 세트입니다. 주기적인 `OPTIMIZE` 또는 `REORG`를 함께 설계하십시오 ([테이블 레이아웃 최적화](table-layout-optimization.md) 참고).
- **`VACUUM` 보존 기간을 함부로 줄이지 않습니다.** 삭제 벡터가 가리킨 옛 파일이 필요한 버전이 있다면 시간 여행이 깨집니다 ([타임 트래블과 변경 데이터 피드](time-travel-and-cdf.md) 참고).
- **"압축하면 삭제 표시가 완전히 해결된다"고 가정하지 않습니다.** 공식 문서는 파일 압축 이벤트가 삭제 벡터 변경을 해결하는 엄격한 보장을 주지 않는다고 설명합니다. 물리 제거가 필요하면 `REORG ... APPLY (PURGE)`를 명시적으로 실행하십시오.
- **쓰기 런타임 버전을 맞춥니다.** 모든 최적화를 쓰려면 Databricks Runtime 14.3 LTS 이상이 필요합니다. 쓰기와 읽기 클러스터의 런타임 차이를 확인하십시오.
- **삭제 벡터 활성화는 테이블 속성 변경입니다.** 실행 이력은 `DESCRIBE HISTORY`로 남고, 일괄 적용 전에 테스트 테이블에서 먼저 확인하는 것을 권장합니다.

## 참고 문서

- [Deletion vectors in Databricks](https://docs.databricks.com/aws/en/tables/features/deletion-vectors)
- [Apache Iceberg v3 in Databricks](https://docs.databricks.com/aws/en/iceberg/iceberg-v3)
- [Read Delta Lake tables with Iceberg clients](https://docs.databricks.com/aws/en/delta/uniform)
- [Optimize data file layout](https://docs.databricks.com/aws/en/tables/operations/optimize)
- [Remove unused data files with vacuum](https://docs.databricks.com/aws/en/tables/operations/vacuum)
