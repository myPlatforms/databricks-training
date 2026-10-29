# 피처 스토어

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 300

Databricks 피처 스토어(Databricks Feature Store)는 모델 학습과 서빙에 쓰는 피처(feature)를 Unity Catalog에 등록하고, 같은 정의를 학습과 실시간 서빙에서 재사용하게 하는 기능입니다. 피처를 담는 기본 단위는 **피처 테이블(Feature Table)** 이며, 문서는 신규 작업에 **피처 뷰(Feature View)** 를 권장합니다. 실시간 조회용 저장소는 **Databricks Online Feature Stores** 로, Lakebase 기반입니다.

## 왜 필요한가

| 이전 방식의 한계 | 피처 스토어가 해결하는 것 |
|---|---|
| 학습용 피처는 배치 파이프라인에서, 서빙용 피처는 애플리케이션 코드에서 따로 계산한다 | 피처 정의를 한 곳에 두고 학습과 서빙에서 같은 정의를 쓴다 |
| 학습 데이터를 만들 때 과거 시점 값을 잘못 섞는다 (데이터 누수) | 학습 세트 생성 시 point-in-time 조인으로 각 라벨 시점에 맞는 피처 값을 가져온다 |
| 피처를 팀마다 다시 만든다 | Unity Catalog에 등록해 검색, 태그, 계보를 쓴다. 문서는 워크스페이스 간 공유와 검색도 설명한다 |
| 실시간 서빙에 쓸 피처를 어디서 읽을지 정하기 어렵다 | 온라인 피처 스토어에 피처 테이블을 게시하고 키로 조회한다 |

## 핵심 개념

| 용어 | 의미 |
|---|---|
| 피처 테이블(Feature Table) | 기본 키(primary key)가 있는 Unity Catalog의 Delta 테이블 |
| 피처 뷰(Feature View) | 피처 정의(원본과 집계 로직)를 Unity Catalog에 등록한 객체. 문서는 "피처를 정의하고 계산하는 권장 방법"이라고 설명한다 |
| 구체화(Materialize) | 피처 뷰의 값을 계산해 저장하는 작업 |
| 백필(Backfill) | 과거 기간의 피처 값을 다시 계산해 채우는 작업 |
| 온라인 스토어(Online Store) | 실시간 조회용 저장소. 문서는 Lakebase 기반이라고 설명한다 |
| 워크스페이스 피처 스토어 | 구형 방식. 문서에서 **deprecated** 로 표기된다 |

> **참고** 문서 제품명은 "Databricks Feature Store"입니다. 온라인 쪽은 "Databricks Online Feature Stores"와 "Online Feature Store"가 섞여 쓰입니다. 이 페이지는 같은 개념으로 다룹니다.

## 피처 테이블 확인 조건

학습 세트에 쓰는 피처 테이블은 Unity Catalog에 있어야 합니다. 문서는 Databricks Feature Store 사용 요건으로 워크스페이스의 Unity Catalog 활성화를 명시합니다. 온라인 게시 조건은 아래 "온라인 스토어에 게시"에서 다룹니다.

## 어떻게 쓰는가

### 1. 학습 세트 만들기 (FeatureLookup)

라벨 데이터프레임(`training_df`)에 피처 테이블의 피처를 키로 조인하는 흐름입니다. 원문 예제를 그대로 옮겼습니다. `ml.recommender_system.customer_features`는 문서 예시 이름입니다.

```python
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup

feature_lookups = [
    FeatureLookup(
        table_name='ml.recommender_system.customer_features',
        feature_names=['total_purchases_30d', 'total_purchases_7d'],
        lookup_key='customer_id'
    ),
]

fe = FeatureEngineeringClient()

training_set = fe.create_training_set(
    df=training_df,              # 라벨과 키 컬럼을 가진 DataFrame
    feature_lookups=feature_lookups,
    label='rating',
    exclude_columns=['customer_id', 'product_id']
)
training_df = training_set.load_df()
```

| 파라미터 | 역할 (원문 예제 기준) |
|---|---|
| `table_name` | 피처를 가져올 피처 테이블 (`catalog.schema.table`) |
| `feature_names` | 가져올 피처 이름 목록 |
| `lookup_key` | 학습 DataFrame과 피처 테이블을 잇는 키 컬럼 |
| `label` | 예측 대상 컬럼 |
| `exclude_columns` | 학습 입력에서 제외할 컬럼 (키 등) |

### 2. 피처 세트와 함께 모델 기록하기

학습 세트를 모델과 함께 기록하면, 서빙 시 모델이 피처를 자동으로 조회하는 전제가 됩니다. 원문 예제입니다.

```python
fe.log_model(
    model=model,
    artifact_path="recommendation_model",
    flavor=mlflow.sklearn,
    training_set=training_set,
    registered_model_name="recommendation_model"
)
```

> **참고** 등록 모델 이름은 Unity Catalog 3단계 이름을 쓰는 것이 권장 구성입니다. 위 예제는 원문 그대로 짧은 이름을 썼습니다. 실제 적용 시에는 `catalog.schema.model` 형태로 바꾸십시오.

### 3. 피처 뷰 정의 (개념 예제)

피처 뷰는 원본 테이블, 엔터티(키), 타임스탬프 컬럼, 집계 함수를 정의합니다. 문서는 대부분의 단일 단계 배치 피처를 피처 뷰가 네이티브로 처리한다고 설명합니다. 교차 테이블 조인, 다단계 집계, 지원되지 않는 집계는 선언형 파이프라인(Spark Declarative Pipelines)으로 Delta 테이블에 쓰는 방법을 권장합니다.

```python
latest_amount = fe.create_feature(
    source=source,
    function=ColumnSelection("amount"),
    entity=["user_id"],
    timeseries_column="transaction_time",
    catalog_name=CATALOG_NAME,
    schema_name=SCHEMA_NAME,
    name="latest_amount",
)
```

> **참고** 위 코드는 원문 예제의 형태입니다. `source`, `ColumnSelection`, `CATALOG_NAME`, `SCHEMA_NAME`은 사용자가 먼저 정의하거나 import해야 합니다. 시간 윈도우 집계(`TumblingWindow`, `AggregationFunction`)는 같은 문서의 `Feature` 생성자 예제를 참고하십시오.

### 4. 온라인 스토어에 게시

온라인 게시는 다섯 단계로 진행합니다. 원문 예제를 따릅니다.

| 단계 | 작업 | 요건·비고 |
|---|---|---|
| 준비 | `%pip install databricks-feature-engineering>=0.13.0` 후 `dbutils.library.restartPython()` | Databricks Runtime 16.4 LTS ML 이상 또는 서버리스 컴퓨트 |
| 1 | 온라인 스토어 생성 | `capacity`는 `CU_1`, `CU_2`, `CU_4`, `CU_8` 중 선택. 테스트는 `CU_2`부터 권장 |
| 2 | 오프라인 피처 테이블 준비 | 기본 키 제약, 키 컬럼 NOT NULL, Change Data Feed 활성화 |
| 3 | 테이블 게시 | `publish_table`. 온라인 테이블이 없으면 만들고, 데이터를 동기화하고, 동기화 인프라를 설정 |
| 4 | 온라인 테이블 삭제 | SDK의 `delete_online_table` (원문이 "유일하게 권장되는 방법"이라고 명시) |
| 5 | 온라인 스토어 삭제 | `delete_online_store`. 삭제 전 피처를 쓰는 서빙 엔드포인트가 없는지 확인 |

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# 1. 온라인 스토어 생성 (name은 63바이트 이하)
fe.create_online_store(
    name="my-online-store",
    capacity="CU_2"
)
```

```sql
-- 2. 오프라인 피처 테이블 준비
ALTER TABLE catalog.schema.your_feature_table
SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

ALTER TABLE catalog.schema.your_feature_table
ALTER COLUMN user_id SET NOT NULL;
```

```python
# 3. 게시 (스토어가 AVAILABLE 상태가 된 뒤 실행)
online_store = fe.get_online_store(name="my-online-store")

fe.publish_table(
    online_store=online_store,
    source_table_name="catalog_name.schema_name.feature_table_name",
    online_table_name="catalog_name.schema_name.online_feature_table_name",
    # publish_mode는 선택. 기본값 "TRIGGERED"
)
```

```python
# 4. 온라인 테이블 삭제 (SDK)
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.feature_store.delete_online_table(
    online_table_name="catalog_name.schema_name.online_feature_table_name"
)

# 5. 온라인 스토어 삭제
fe.delete_online_store(name="my-online-store")
```

#### 게시 모드

| 모드 | 동작 (원문) | 요건 |
|---|---|---|
| `TRIGGERED` (기본) | API 호출 또는 스케줄로 증분 업데이트 | Change Data Feed 필요 |
| `CONTINUOUS` | 오프라인 테이블에 쓰일 때마다 스트리밍 파이프라인이 온라인 스토어를 갱신 | Change Data Feed 필요 |
| `SNAPSHOT` | 한 번 전체 복사 | 여러 행이 동기화 사이에 많이 바뀌는 경우에 유용 |

`publish_mode`는 v0.13.0.1부터 `streaming` 인자를 대체합니다. `streaming=True`는 `publish_mode="CONTINUOUS"`와 같습니다.

### 상태 값과 제약

| 항목 | 내용 (원문) |
|---|---|
| 게시 가능 상태 | 온라인 스토어가 `AVAILABLE`이어야 게시할 수 있다 |
| 읽기 복제본 | 생성·업데이트 시 `read_replica_count`로 설정. 최대 3개(기본 인스턴스 포함 4개 컴퓨트). 고가용성을 끄면 연결된 엔드포인트를 재시작할 때까지 깨진다 |
| 지원 테이블 | Unity Catalog 피처 테이블만 지원 |
| 게시 시 미지원 인자 | `filter_condition`, `checkpoint_location`, `mode`, `trigger`, `features` |
| 같은 피처 테이블의 여러 온라인 테이블 | 특정 온라인 테이블을 지정할 수 없고, 엔드포인트는 생성 시각이 가장 오래된 온라인 테이블을 쓴다 |
| 이름 규칙 | 온라인 테이블의 카탈로그 이름은 Lakebase 데이터베이스 이름과 같아야 한다. 아니면 서빙 엔드포인트 배포가 실패한다 |
| Lakebase 자동 확장 인스턴스 | API나 UI로 만든 인스턴스는 `creator`, `read_replica_count`, `capacity`를 업데이트할 수 없다 |
| 다중 스토어 조회 | Lakebase 자동 확장 인스턴스에서 여러 온라인 스토어의 피처를 조회하는 새 엔드포인트는 만들 수 없다. 기존 엔드포인트는 계속 동작한다 |
| 스케일 투 제로 | Lakebase 스케일 투 제로는 지원되지 않는다 |

### 온라인 스토어 비용 구조

문서는 온라인 스토어가 "지속적으로 비용이 발생한다"고 설명하며, 더 이상 쓰지 않는 스토어는 삭제하고 가능하면 프로젝트 간에 하나를 재사용하라고 권장합니다. 세부 단가는 이 장에서 다루지 않습니다.

## 트레이드오프

| 선택지 | 장점 | 단점 |
|---|---|---|
| Unity Catalog 피처 스토어 | 거버넌스, 계보, 공유가 통합된다 | Unity Catalog 워크스페이스가 필요하다 |
| 워크스페이스 피처 스토어 (구형) | 기존 자산과 호환된다 | deprecated. 신규 적용을 피한다 |
| 피처를 애플리케이션에서 직접 계산 | 구조가 단순하다 | 학습-서빙 불일치 위험이 커지고 재사용이 어렵다 |
| 온라인 스토어 게시 | 실시간 조회 경로를 표준화한다 | 상시 비용이 발생하고, 게시 모드와 제약을 관리해야 한다 |

> **참고** 온라인 스토어 백엔드인 Lakebase의 동작은 [Lakebase 개요](../10-lakebase/what-is-lakebase.md)에서 다룹니다.

## 주의사항

- **기본 키와 NOT NULL을 먼저 설계하십시오.** 게시 전 조건이며, 온라인 조회는 키로 이루어집니다.
- **CDF를 켜 두십시오.** `TRIGGERED`와 `CONTINUOUS` 모두 필요합니다.
- **같은 피처 테이블을 여러 번 게시하지 마십시오.** 문서는 한 테이블당 `publish_table` 한 번을 권장하며, 진행 중인 동기화가 있으면 `get_status()`로 기다리라고 설명합니다.
- **삭제 전에 엔드포인트를 확인하십시오.** 온라인 스토어 삭제는 이를 쓰는 서빙 엔드포인트를 깨뜨릴 수 있습니다.
- **학습 시점 컬럼을 정확히 정하십시오.** point-in-time 조인의 정확도는 시점 컬럼에 달려 있습니다. 세부 옵션은 [Point-in-time feature joins](https://docs.databricks.com/aws/en/machine-learning/feature-store/time-series) 페이지를 참고하십시오.
- **deprecated 표기를 확인하십시오.** 구형 워크스페이스 피처 스토어 코드는 Unity Catalog 방식으로 옮겨야 합니다.

## 참고 문서

- [Feature Store (개요)](https://docs.databricks.com/aws/en/machine-learning/feature-store/)
- [Feature Views](https://docs.databricks.com/aws/en/machine-learning/feature-store/feature-views)
- [Feature tables in Unity Catalog](https://docs.databricks.com/aws/en/machine-learning/feature-store/uc/feature-tables-uc)
- [Train models with feature tables](https://docs.databricks.com/aws/en/machine-learning/feature-store/train-models-with-feature-store)
- [Online Feature Store](https://docs.databricks.com/aws/en/machine-learning/feature-store/online-feature-store)
- [Model Serving with automatic feature lookup](https://docs.databricks.com/aws/en/machine-learning/feature-store/automatic-feature-lookup)
