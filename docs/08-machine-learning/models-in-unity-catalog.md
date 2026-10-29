# Unity Catalog의 모델

> 기준일: 2026-10-28 · 근거: 공식 문서

Unity Catalog의 모델 레지스트리(Model Registry)는 MLflow 모델을 `catalog.schema.model` 3단계 이름으로 등록하고, 버전과 별칭(alias)으로 배포 대상을 관리하는 저장소입니다. 권한, 계보(lineage), 검색을 다른 데이터 자산과 같은 체계로 묶습니다.

## 왜 필요한가

워크스페이스 단위 레지스트리는 워크스페이스마다 모델이 따로 존재합니다. 다른 워크스페이스에서 같은 모델을 쓰려면 복사하거나 다시 등록해야 합니다. Unity Catalog 레지스트리는 다음 문제를 해결합니다.

| 워크스페이스 단위 레지스트리의 한계 | Unity Catalog 레지스트리의 방식 |
|---|---|
| 워크스페이스 간 모델 공유가 번거롭다 | 메타스토어 안에서 여러 워크스페이스가 같은 모델 이름을 본다 |
| 접근 제어가 워크스페이스 설정에 흩어진다 | 카탈로그·스키마·모델 단위 GRANT로 통합 관리한다 |
| 배포 코드가 버전 번호에 묶인다 | 별칭(예: Champion)을 옮기면 코드 변경 없이 대상이 바뀐다 |
| 모델이 어떤 데이터·테이블에서 나왔는지 추적하기 어렵다 | Unity Catalog 계보로 연결을 본다 |

> **참고** 공식 문서는 Unity Catalog 레지스트리의 이점으로 "워크스페이스 간 중앙 접근 제어, 감사, 계보, 모델 검색"을 듭니다.

## 핵심 개념

| 용어 | 의미 |
|---|---|
| 등록 모델(Registered Model) | `catalog.schema.model` 이름을 가진 모델 엔터티 |
| 모델 버전(Model Version) | 등록할 때마다 생기는 번호가 붙은 스냅샷. 서명(signature)이 필요하다 |
| 별칭(Alias) | 버전을 가리키는 변경 가능한 이름. 예: `Champion`. 재지정하면 참조하는 워크로드가 새 버전을 읽는다 |
| 태그(Tag) | 모델이나 버전에 붙이는 키·값 메타데이터 |

> **주의** 공식 문서는 "스테이지(Stage)는 지원하지 않는다"고 명시합니다. 개발·운영 구분은 카탈로그나 스키마 이름과 별칭으로 나누십시오.

## 어떻게 동작하는가

### 등록과 버전 생성

1. 실험 런 또는 로깅 모델에서 모델을 등록합니다.
2. 같은 이름으로 다시 등록하면 새 버전이 생깁니다.
3. 버전에는 모델 서명이 있어야 입력 검증이 자동으로 됩니다. `log_model`에 입력 예시(input example)를 넘기면 서명이 추론됩니다.
4. 서명이 없는 버전은 자동 입력 검증을 잃고, AI 함수에 스키마 없이 쓸 수 없다고 문서가 설명합니다.

### 별칭으로 배포 대상 바꾸기

| 구성 요소 | 예시 값 | 역할 |
|---|---|---|
| 등록 모델 | `prod.ml_team.churn_model` | 모델 이름. 버전이 쌓이는 단위 |
| 모델 버전 | `v1`, `v2`, `v3` | 등록할 때마다 생기는 스냅샷 |
| 별칭 | `Champion` → `v2` | 현재 운영 중인 버전을 가리킴 |
| 참조 URI | `models:/prod.ml_team.churn_model@Champion` | 배치 추론·서빙이 로드하는 경로 |

작업별로 무엇이 바뀌는지 정리하면 다음과 같습니다.

| 작업 | 바뀌는 것 | 바뀌지 않는 것 |
|---|---|---|
| 별칭을 v3로 재지정 | 별칭을 로드하는 워크로드가 읽는 버전 | 워크로드 코드, 모델 이름 |
| 새 버전 등록 | 버전 목록 | 기존 별칭 (수동으로 옮겨야 함) |
| 버전 삭제 | 해당 버전 | 별칭이 가리키는 다른 버전 (문서의 삭제 규칙 참고) |

## 어떻게 쓰는가

### 레지스트리 URI 설정

MLflow 3에서 기본 레지스트리 URI는 `databricks-uc`입니다. 다른 워크스페이스에서 명시하려면 다음과 같이 씁니다.

```python
import mlflow

mlflow.set_registry_uri("databricks-uc")
```

> **참고** 공식 문서는 컴퓨트가 Dedicated 접근 모드(Databricks Runtime 15.4 LTS ML 이상에서는 dedicated group access mode 포함)여야 한다고 설명합니다.

### 등록

```python
import mlflow

# MLflow 2.x 방식: 실행(run) 아티팩트에서 등록
mlflow.register_model(
    "runs:/<run_id>/model",
    "prod.ml_team.churn_model",
)

# MLflow 3 방식: 로깅 모델에서 등록
mlflow.register_model(
    "models:/<model_id>",
    "prod.ml_team.churn_model",
)
```

`<run_id>`와 `<model_id>`는 실제 값으로 바꿔 쓰십시오.

### 별칭 설정과 조회

```python
from mlflow import MlflowClient

client = MlflowClient()

# 버전 1을 Champion으로 지정
client.set_registered_model_alias("prod.ml_team.churn_model", "Champion", 1)

# 버전 2로 재지정 (코드 변경 없이 대상이 바뀜)
client.set_registered_model_alias("prod.ml_team.churn_model", "Champion", 2)

# 현재 Champion 버전 확인
champion = client.get_model_version_by_alias("prod.ml_team.churn_model", "Champion")
print(champion.version)

# 별칭 삭제
client.delete_registered_model_alias("prod.ml_team.churn_model", "Champion")
```

### 별칭으로 로드 (배치 추론)

```python
import mlflow.pyfunc

champion = mlflow.pyfunc.load_model("models:/prod.ml_team.churn_model@Champion")
predictions = champion.predict(input_df)  # input_df는 예시 입력 DataFrame
```

버전 번호로 로드하려면 `models:/prod.ml_team.churn_model/1` 형식을 씁니다.

### 권한

공식 문서가 명시한 작업별 권한은 다음과 같습니다. 모든 작업에는 해당 스키마와 카탈로그에 대한 `USE SCHEMA`, `USE CATALOG`가 함께 필요합니다.

| 작업 | 필요한 권한 (스키마·모델 기준) |
|---|---|
| 등록 모델 생성 | 스키마에 `CREATE MODEL` (또는 `CREATE FUNCTION`) |
| 모델 버전 생성 | 등록 모델의 소유자이거나 `CREATE MODEL VERSION` |
| 별칭 설정·삭제 | 등록 모델의 소유자 |
| 별칭으로 로드(추론), UI 조회 | 등록 모델에 `EXECUTE` |
| 태그 설정·삭제 | 소유자 또는 `APPLY TAG` |
| 이름 변경 | 소유자 + 스키마에 `CREATE MODEL` |
| 설명 추가, 삭제 | 소유자 |

등록 모델은 Unity Catalog에서 `FUNCTION` 보안 객체로 취급되므로 GRANT는 `GRANT ON FUNCTION`을 씁니다. REST API에서는 `securable_type`을 `"FUNCTION"`으로 지정합니다.

```sql
-- 추론 서비스 계정에 모델 실행 권한 부여 (계정 이메일은 예시)
GRANT USE CATALOG ON CATALOG prod TO `ml-serving-sp@example.com`;
GRANT USE SCHEMA ON SCHEMA prod.ml_team TO `ml-serving-sp@example.com`;
GRANT EXECUTE ON FUNCTION prod.ml_team.churn_model TO `ml-serving-sp@example.com`;
```

> **참고** 권한 모델 전반은 [권한 모델과 소유권](../06-unity-catalog/privileges-and-ownership.md)에서 다룹니다.

## 트레이드오프

| 항목 | 내용 |
|---|---|
| 스테이지 대신 별칭 | 운영·스테이징 구분을 별칭과 이름으로 표현한다. 워크스페이스 레지스트리의 Stage 방식과 다르다 |
| 웹훅·알림 | 문서는 Unity Catalog 레지스트리에서 웹훅과 이메일 알림을 지원하지 않는다고 명시한다 |
| 검색 | `order_by`, 태그 필터를 쓸 수 없고 정확 일치(equality) 연산자만 쓸 수 있다. 이름으로 찾을 때는 `get_registered_model`을 쓴다 |
| 삭제 | 등록 모델 삭제는 되돌릴 수 없으며 아티팩트와 메타데이터를 함께 지운다 |

## 주의사항

- **별칭을 옮길 때는 검증을 먼저 끝내십시오.** 별칭은 즉시 참조 워크로드에 반영되므로, 새 버전의 평가 결과를 확인한 뒤 재지정하는 절차를 두십시오.
- **서명 없는 모델을 등록하지 마십시오.** 입력 예시를 넘겨 서명을 추론하게 하거나 명시적 서명을 붙이십시오.
- **서빙 서비스 계정에는 `EXECUTE`만 주십시오.** 등록과 별칭 변경 권한은 학습 파이프라인 계정에만 두는 것이 권장 구성입니다 (권장 구성은 본 장의 설계 제안이며 문서의 강제 규정은 아닙니다).
- **Databricks 워크스페이스 레지스트리 표기 혼동에 주의하십시오.** 같은 이름의 모델이 워크스페이스 레지스트리와 Unity Catalog에 따로 있을 수 있습니다. 등록 URI를 확인하십시오.

## 참고 문서

- [Manage model lifecycle in Unity Catalog](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/)
- [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/)
- [Unity Catalog 권한](https://docs.databricks.com/aws/en/data-governance/unity-catalog/)
