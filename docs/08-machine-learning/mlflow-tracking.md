# MLflow 실험 추적

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

MLflow는 ML 실험의 파라미터, 메트릭, 아티팩트, 모델을 기록하고 비교하는 오픈소스 플랫폼입니다. Databricks는 MLflow를 관리형으로 제공하며, 기본 추적 서버는 워크스페이스에 호스팅됩니다. MLflow 3은 모델을 실험 런과 분리된 **로깅 모델(LoggedModel)** 로 다루고, 에이전트와 LLM 애플리케이션의 관측성과 평가를 추가했습니다.

## 왜 필요한가

노트북에서 `print`로 정확도를 남기고 파일명에 날짜를 붙이는 방식은 다음 문제가 있습니다.

| 이전 방식의 한계 | MLflow가 해결하는 것 |
|---|---|
| 어떤 파라미터로 어떤 정확도가 나왔는지 기록이 흩어진다 | 실험 아래 런 단위로 파라미터와 메트릭을 모은다 |
| 같은 실험을 여러 번 비교하기 어렵다 | 실험 안의 런을 비교하고 필터링해 파라미터와 입력 데이터가 성능에 주는 영향을 본다 |
| 모델 파일이 어느 런의 결과인지 연결이 끊긴다 | 로깅 모델이 메타데이터, 메트릭, 파라미터, 코드와 연결된다 |
| 등록 모델과 실험 결과가 따로 논다 | 모델 등록 시 로깅 모델의 메트릭과 파라미터를 레지스트리 UI와 API에서 본다 |

## 핵심 개념

| 용어 | 의미 (문서 원문 요지) |
|---|---|
| 실험(Experiment) | 관련된 런의 모음. 파라미터와 입력 데이터가 성능에 주는 영향을 비교하는 단위 |
| 런(Run) | 모델 코드의 한 번 실행. 실행 중 파라미터와 결과를 기록 |
| 로깅 모델(LoggedModel) | MLflow 3의 모델 단위 기록. 고유 ID(`model_id`)로 메타데이터, 메트릭, 파라미터, 코드를 묶으며 환경 사이에 유지됨 |
| 아티팩트(Artifact) | 모델 파일, 그림, 데이터 샘플 같은 산출물 |
| 모델 레지스트리 | 검증된 모델 버전을 이름으로 관리. 자세한 내용은 [Unity Catalog의 모델](models-in-unity-catalog.md) |

## MLflow 3 설치와 변경점

문서는 노트북마다 다음 두 줄을 실행하라고 안내합니다.

```python
%pip install mlflow>=3.0 --upgrade
dbutils.library.restartPython()
```

공식 문서가 설명하는 주요 변경점은 다음과 같습니다.

| 영역 | MLflow 2 방식 | MLflow 3 방식 (문서) |
|---|---|---|
| 모델 로깅 인자 | `artifact_path` | `name`. 이름으로 검색할 수 있게 한다. `artifact_path`는 deprecated지만 여전히 동작 |
| 런 필요 여부 | 모델은 런 안에서 기록 | 활성 런 없이도 모델을 기록할 수 있다. 모델이 1급 객체가 됨 |
| 아티팩트 위치 | 런의 아티팩트 경로 | `models/<model_id>/artifacts/` |
| 모델 URI | `runs:/<run_id>/<artifact_path>` | `models:/<model_id>` (`log_model`이 반환) |
| 기본 레지스트리 | 워크스페이스 레지스트리 | `databricks-uc` (Unity Catalog, 3단계 이름) |
| 평가 API | `mlflow.evaluate` | deprecated. 전통 ML·DL은 `mlflow.models.evaluate`, LLM과 AI 앱은 `mlflow.genai.evaluate` |
| `RunInfo` 속성 | `run_uuid` | 제거됨. `run_id` 사용 |

- MLflow 3 클라이언트는 MLflow 2.x의 런, 모델, 트레이스를 읽을 수 있습니다. 반대 방향은 보장되지 않습니다.
- 레거시 워크스페이스 레지스트리가 필요하면 `mlflow.set_registry_uri("databricks")`, `MLFLOW_REGISTRY_URI` 환경 변수, 또는 init 스크립트를 쓴다고 문서가 설명합니다.
- `mlflow.spark.log_model`은 여전히 동작하지만 새 로깅 모델 개념을 쓰지 않습니다.

> **참고** 에이전트 관측성(트레이스)과 평가의 세부는 09장에서 다룹니다. 이 페이지는 실험 추적과 모델 기록에 집중합니다.

## 어떻게 쓰는가

### 1. 실험 지정

문서의 예제는 워크스페이스 실험 경로를 씁니다. 기본 추적 서버는 워크스페이스이므로 별도의 추적 URI 설정은 필요하지 않습니다.

```python
import mlflow

experiment_name = "/Shared/name_of_experiment/"
mlflow.set_experiment(experiment_name)
```

> **참고** 활성 실험을 지정하지 않으면 런은 노트북 실험으로 기록된다고 문서가 설명합니다. 여러 노트북이 같은 실험을 공유하려면 `set_experiment`로 경로를 명시하는 편이 명확합니다.

### 2. 런 기록과 로깅 모델 만들기

로깅 모델은 플레이버(flavor)별 `log_model()` 호출이 만듭니다. 이 호출은 `model_info`를 반환하며, 거기서 `model_id`를 얻습니다. 아래 코드는 원문 흐름을 따른 것입니다. 플레이버 함수 이름은 쓰는 프레임워크에 맞추십시오. 예를 들어 LangChain 예제는 `mlflow.langchain.log_model`을 씁니다.

```python
import mlflow

model_info = mlflow.pyfunc.log_model(
    name="model",
    python_model=python_model,   # 학습된 Python 모델 객체 (예시 변수)
)

logged_model = mlflow.get_logged_model(model_info.model_id)
```

메트릭은 `model_id`를 지정해 로깅 모델에 붙일 수 있습니다. 문서의 sklearn 예제 형태입니다.

```python
mlflow.log_metrics(
    metrics={"accuracy": 0.91},      # 예시 값
    model_id=logged_model.model_id,
    dataset=train_dataset,           # 데이터셋 객체 (예시 변수)
)
```

딥러닝 학습에서는 체크포인트마다 `step`과 함께 기록합니다. 문서 예제는 `mlflow.log_metric(key="accuracy", ..., model_id=model_info.model_id)` 형태입니다.

### 3. 자동 로깅 (autologging)

문서는 자동 로깅을 여러 ML과 딥러닝 프레임워크의 학습 코드를 자동으로 기록하는 가장 쉬운 시작 방법이라고 설명합니다. 예제는 scikit-learn을 쓰며, 다른 라이브러리는 MLflow 문서를 보라고 안내합니다. 이 페이지는 `mlflow.autolog()` 호출과 기록되는 항목 목록을 원문에서 확인하지 못했으므로 코드를 싣지 않았습니다.

### 4. 로깅 모델을 등록 모델로 연결

MLflow 3에서는 `models:/<model_id>` URI로 로깅 모델을 등록합니다. 전체 예제와 권한은 [Unity Catalog의 모델](models-in-unity-catalog.md)에 있습니다.

```python
mlflow.register_model(
    "models:/<model_id>",
    "catalog.schema.churn_model",   # 예시 이름
)
```

등록하면 로깅 모델의 메트릭과 파라미터가 레지스트리 UI와 API에서 보입니다. 여러 실험과 워크스페이스에 걸친 모델 성능을 한 페이지에서 보고, 트레이스 탭에서 개발과 평가 중의 트레이스를 온라인 서빙 엔드포인트의 트레이스와 함께 볼 수 있다고 문서가 설명합니다.

### 5. 배포 잡 (MLflow 3)

문서는 MLflow 3 배포 잡(deployment jobs)이 평가, 승인, 배포를 자동화하며, Unity Catalog로 관리되고 활동 로그가 남는다고 설명합니다. 세부 설정은 "MLflow 3 deployment jobs" 페이지를 따르십시오.

> **주의** 같은 문서군의 Unity Catalog 레지스트리 제약 목록에는 "활동 로그, 웹훅, 이메일 알림은 지원되지 않는다"는 항목이 있습니다. 배포 잡의 활동 로그와 레지스트리의 제약은 범위가 다를 수 있으므로, 감사 요건이 있으면 두 원문을 모두 확인하십시오.

## 트레이드오프

| 선택지 | 장점 | 단점 |
|---|---|---|
| 노트북에서 직접 MLflow 사용 | 설정이 없고 바로 기록된다 | 여러 사람이 실험을 비교하거나 권한을 나누기 어렵다 |
| 실험을 워크스페이스 경로에 둔다 | 폴더 권한으로 접근을 제어한다 | 다른 워크스페이스로 옮길 때 별도 작업이 필요하다 |
| 로깅 모델 중심으로 추적 | 모델과 메트릭, 등록이 이어진다 | MLflow 3 API 기준 코드가 필요하고, `artifact_path` 같은 옛 인자는 바꿔야 한다 |

## 주의사항

- **MLflow 3 기준으로 로깅 인자를 쓰십시오.** `artifact_path` 대신 `name`을 씁니다. 옛 코드를 옮길 때 `models:/` URI와 `databricks-uc` 기본값을 함께 확인하십시오.
- **런은 `with mlflow.start_run()` 블록으로 감싸십시오.** 예외가 나도 런이 닫히도록 하기 위함입니다. 문서의 모델 로깅은 활성 런 없이도 가능하므로, 런이 필요한 메트릭 기록인지 먼저 판단하십시오.
- **파라미터와 메트릭 이름을 일관되게 쓰십시오.** 같은 이름이 실행마다 다르면 비교가 어렵습니다.
- **학습 데이터의 식별 정보를 남기십시오.** 테이블 이름과 버전을 파라미터나 태그로 남기면 재현에 도움이 됩니다.
- **실험 런을 운영 서빙에 직접 쓰지 마십시오.** 배포 대상은 등록된 모델 버전과 별칭이어야 합니다.
- **`mlflow.evaluate`를 새 코드에 쓰지 마십시오.** deprecated이며, 대상에 따라 `mlflow.models.evaluate` 또는 `mlflow.genai.evaluate`를 씁니다.

## 참고 문서

- [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/)
- [Experiment tracking (mlflow/tracking)](https://docs.databricks.com/aws/en/mlflow/tracking)
- [Get started with MLflow 3 for models](https://docs.databricks.com/aws/en/mlflow/mlflow-3-install)
- [Track and compare models using MLflow Logged Models](https://docs.databricks.com/aws/en/mlflow/logged-model)
- [Model Registry improvements with MLflow 3](https://docs.databricks.com/aws/en/mlflow/model-registry-3)
- [MLflow 3 deployment jobs](https://docs.databricks.com/aws/en/mlflow/deployment-job)
