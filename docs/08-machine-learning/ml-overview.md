# ML 개요

> 기준일: 2026-10-29 · 근거: 공식 문서 · 수준: 100

Databricks의 머신러닝 기능은 하나의 제품이 아니라 **데이터 준비 → 학습 → 추적 → 등록 → 서빙 → 모니터링** 의 각 단계에 대응하는 구성 요소 묶음입니다. 이 페이지는 전체 지도를 먼저 잡고, 각 구성 요소가 어느 페이지에서 다뤄지는지 연결합니다.

## 왜 필요한가

ML 프로젝트에서 모델 코드보다 어려운 부분은 대개 주변 작업입니다.

| 이전 방식의 문제 | 생기는 일 |
|---|---|
| 학습 데이터와 서빙 데이터의 피처 계산 로직이 다르다 | 온라인 예측 값이 학습 때와 달라지는 학습-서빙 왜곡(training-serving skew)이 생긴다 |
| 모델 파일이 노트북이나 개인 저장소에 흩어진다 | 어떤 데이터·코드로 만든 모델인지 추적하기 어렵다 |
| 배포 대상 모델을 코드에서 직접 바꾼다 | 배포마다 코드 변경과 재배포가 필요하다 |
| 엔드포인트와 GPU 인프라를 직접 운영한다 | 클러스터 기동, 스케일링, 드라이버 관리 부담이 크다 |

Databricks는 이 단계들을 Unity Catalog(권한·계보·검색)와 MLflow(추적·등록)를 중심으로 묶어 제공합니다.

## 구성 요소 지도

공식 ML 랜딩 페이지는 기능을 다음 묶음으로 나눕니다. 이 장의 페이지 구성도 같은 묶음을 따릅니다.

| 단계 | 공식 문서의 항목 | 이 장의 페이지 |
|---|---|---|
| 준비 | Feature Store (피처 관리, Unity Catalog에서 관리, 운영 서빙) | [피처 스토어](feature-store.md) |
| 학습 (고전 ML) | Databricks Runtime for ML, 모델 학습 예제, MLflow tracking | [모델 학습 도구](model-training.md), [MLflow 실험 추적](mlflow-tracking.md) |
| 학습 (딥러닝) | AI Runtime, 분산 학습 예제, Ray on Databricks | [모델 학습 도구](model-training.md) |
| 등록 | Models in Unity Catalog | [Unity Catalog의 모델](models-in-unity-catalog.md) |
| 서빙 | Model Serving, AI Gateway, Batch inference, Foundation model APIs | [Model Serving 커스텀 모델](model-serving.md), [Foundation Model APIs](foundation-model-apis.md), [Unity Gateway](unity-gateway.md) |
| 모니터링·거버넌스 | Unity Catalog, MLflow for Models, Anomaly detection, Data profiling | [데이터 품질 모니터링](data-quality-monitoring.md) |
| 운영 자동화 | Lakeflow Jobs, Declarative Automation Bundles, MLOps workflows | [Lakeflow Jobs](../04-data-engineering/jobs-tasks-and-triggers.md) (상세 MLOps는 문서 링크 참고) |

> **참고** 랜딩 페이지의 "AI Gateway" 항목은 문서 URL 경로가 `ai-gateway`이지만, 게이트웨이 문서 본문은 **Unity Gateway** 를 제품명으로 씁니다("Unity Gateway is the Databricks governance solution for enterprise AI"). 이 장은 본문 표기인 Unity Gateway를 씁니다.

## 컴퓨트 선택: ML 런타임과 AI Runtime

ML 워크로드의 컴퓨트는 두 갈래로 나뉩니다.

| 항목 | Databricks Runtime for ML (클래식 컴퓨트) | AI Runtime (서버리스 GPU) |
|---|---|---|
| 성격 | 사전 구성된 ML·DL 라이브러리가 들어 있는 클러스터 런타임 | 관리형 서버리스 GPU 컴퓨트 |
| 문서 설명 | 가장 흔한 ML·DL 라이브러리를 포함한 인프라를 자동으로 만든다 | 학습·파인튜닝 등 딥러닝 워크로드용 완전 관리형 GPU 컴퓨트 |
| 클러스터 설정 | 클러스터를 만들고 워커 유형에서 GPU 인스턴스를 선택한다 | 클러스터 설정 없이 노트북을 바로 연결한다 |
| 접근 모드 | Machine learning 체크박스를 켜면 **Dedicated** 접근 모드가 자동 설정된다. Unity Catalog 데이터 접근에 Dedicated가 필요하다 | 서버리스 컴퓨트로 실행된다 |
| GPU 종류 | 클러스터의 GPU 인스턴스 타입에 따른다 (지원 인스턴스는 별도 목록) | AI Runtime 개요가 명시한 GPU는 온디맨드 A10과 H100 |
| 상태 표기 | 문서에 명시 없음 | 문서에 명시 없음 |

### 선택 기준

공식 Runtime ML 페이지는 GPU 워크로드에 대해 명시적인 권장을 둡니다. 사용자 정의 딥러닝 워크로드(파인튜닝, 학습)는 Databricks Runtime ML 대신 AI Runtime을 권장하며, AI Runtime은 설정이 단순하고 프로비저닝이 빠르며 성능이 낫다고 설명합니다.

| 상황 | 문서 기준 권장 |
|---|---|
| 커스텀 딥러닝 학습·파인튜닝, GPU 중심 | AI Runtime (서버리스 GPU) |
| 노트북을 클러스터 설정 없이 바로 쓰고 싶다 | AI Runtime |
| Ray Core·Data·Train·Tune을 쓴다 | AI Runtime의 Ray 연결 (문서 목록에 포함) |
| 고전 ML 라이브러리와 Spark 데이터 처리를 한 클러스터에서 함께 쓴다 | Databricks Runtime for ML (Dedicated 클러스터) |
| 기존 클래식 GPU 클러스터 워크로드를 이미 운영 중 | 마이그레이션 가이드 검토 (Runtime ML 페이지 안내) |

### Databricks Runtime for ML 확인 사항

Databricks Runtime for ML에 대한 원문 확인 사항은 다음과 같습니다.

- 포함 라이브러리: 랜딩 페이지는 scikit-learn, XGBoost, MLflow 등을 사전 구성 라이브러리로 명시합니다. 전체 목록과 버전은 릴리즈 노트에서 확인합니다. 문서는 상위 등급(top-tier) 라이브러리 집합을 따로 지정하고, 이 집합은 메이저 릴리즈에서만 추가·제거된다고 설명합니다.
- Photon은 Databricks Runtime 15.2 ML 이상에서 켤 수 있습니다. 문서는 Spark SQL, DataFrame, 피처 엔지니어링, xgboost4j 같은 JVM 워크로드에 효과가 있고, XGBoost·PyTorch·TensorFlow 같은 Python 패키지는 효과가 없다고 설명합니다.
- Graviton 인스턴스는 Databricks Runtime 15.4 LTS ML 이상에서 지원됩니다.
- 세분화된 접근 제어(fine-grained access control)와 Dedicated 모드에서 Lakeflow pipeline 테이블(스트리밍 테이블, 구체화된 뷰) 조회는 Databricks Runtime 15.4 LTS ML 이상이 필요합니다.
- 라이브러리 설치 범위: 컴퓨트 전체는 컴퓨트 범위 라이브러리나 init 스크립트로, 특정 노트북 세션만은 노트북 범위 Python 라이브러리로 설치합니다.

> **주의** AI Runtime 페이지는 GPU 종류로 A10과 H100만 명시합니다. 문서가 명시하지 않은 GPU나 리전·가격은 이 장에 쓰지 않았습니다. 사용 전 최신 문서에서 확인하십시오.

## 기본 흐름 예시

아래는 전체 흐름을 한눈에 보는 표입니다. 각 단계의 실제 코드는 해당 페이지에서 다룹니다.

| 순서 | 작업 | 사용하는 기능 | 결과물 |
|---|---|---|---|
| 1 | 피처 테이블을 만든다 | Feature Store | Unity Catalog의 피처 테이블 |
| 2 | 피처를 사용해 모델을 학습하고 실행을 기록한다 | MLflow 실험 추적 | 런(Run)과 로깅 모델 |
| 3 | 검증한 모델 버전을 등록하고 별칭을 붙인다 | Unity Catalog 모델 | `catalog.schema.model@Champion` |
| 4 | 엔드포인트로 서빙한다 | Model Serving | 실시간 REST 엔드포인트 |
| 5 | 사용량·한도·가드레일을 적용한다 (LLM·MCP 호출인 경우) | Unity Gateway | 거버넌스 정책 |
| 6 | 입력 데이터와 예측의 품질을 감시한다 | 데이터 품질 모니터링 | 프로파일·이상 탐지 결과 |

## AI Runtime 개요

AI Runtime은 딥러닝 학습과 파인튜닝을 위한 **완전 관리형 서버리스 GPU 컴퓨트** 입니다. 문서는 관리형 환경, 내장 관측성(MLflow 실험 추적, 로깅, 디버깅 에이전트), 오케스트레이션(잡과 CI/CD)을 함께 제공한다고 설명합니다. 문서 원문에는 상태 라벨이 없습니다.

| 항목 | 내용 (문서 원문) |
|---|---|
| GPU | 온디맨드 A10, H100. 다른 가속기는 이 페이지에서 명시되지 않음 |
| 연결 | 노트북을 클러스터 설정 없이 바로 연결 |
| 환경 | 최소 Standard 환경 또는 ML 프레임워크가 미리 들어 있는 Databricks AI 환경, 필요하면 커스텀 Docker 이미지 |
| 진입 경로 | Quickstart(터미널), Databricks CLI(YAML 잡 제출), 노트북, 잡, Ray(Ray Core·Data·Train·Tune) |
| 데이터 로딩 | Unity Catalog 볼륨에서 스트리밍 로더로 데이터를 읽어 GPU 활용률을 높이는 방식 |
| 배포 | 학습한 모델을 Model Serving으로 배포 가능 |

> **참고** AI Runtime 세부 옵션과 분산 학습은 [모델 학습 도구](model-training.md)에서 다룹니다.

## 흐름을 API로 보면

전체 흐름은 다음 이름의 API로 이어집니다. 각 단계의 정확한 코드는 해당 페이지에서 확인하십시오.

| 단계 | 대표 API·기능 (원문 이름) | 이 장의 페이지 |
|---|---|---|
| 피처 조회와 학습 세트 | `FeatureLookup`, `fe.create_training_set` | [피처 스토어](feature-store.md) |
| 기록 | `mlflow.set_experiment`, `log_model`(`model_info.model_id`), `mlflow.get_logged_model` | [MLflow 실험 추적](mlflow-tracking.md) |
| 등록과 별칭 | `mlflow.register_model("models:/<model_id>", ...)`, `set_registered_model_alias` | [Unity Catalog의 모델](models-in-unity-catalog.md) |
| 서빙 | 서빙 엔드포인트 `config.served_entities` | [Model Serving 커스텀 모델](model-serving.md) |
| LLM 호출 | `ai_query`, `POST /serving-endpoints/{name}/invocations` | [Foundation Model APIs](foundation-model-apis.md) |
| 정책 | 가드레일 서비스 정책, 한도, `system.ai_gateway.usage` | [Unity Gateway](unity-gateway.md) |
| 품질 | 이상 탐지, 데이터 프로파일링 | [데이터 품질 모니터링](data-quality-monitoring.md) |

## 트레이드오프

- **통합의 대가**: 한 플랫폼 안에서 흐름이 이어지지만, 오픈소스 MLflow 서버를 직접 운영하는 방식과 설정 모델이 다릅니다. 기능 세부는 Databricks 관리형 MLflow 기준으로 봐야 합니다.
- **서버리스와 클래식의 선택**: GPU 딥러닝 학습은 AI Runtime이 설정 부담이 적고, 고전 ML과 Spark 데이터 처리를 같은 클러스터에서 하려면 ML 런타임이 맞습니다. 두 경로의 과금 구조는 다릅니다. 과금 단가는 이 장에서 다루지 않습니다.
- **Unity Catalog 의존**: 모델 등록, 피처 테이블, 게이트웨이, 모니터링 대부분이 Unity Catalog를 전제로 합니다. 워크스페이스가 Unity Catalog에 연결되어 있지 않으면 여러 기능을 쓸 수 없습니다.
- **분산 학습 방식**: AI Runtime은 Ray, 분산 학습 예제(TorchDistributor, DeepSpeed 등)와 함께 쓰입니다. 어떤 방식을 고를지는 [모델 학습 도구](model-training.md)에서 확인하십시오.

## 주의사항

- 노트북 하나에서 학습과 서빙까지 끝내는 구조가 아닙니다. 등록 → 별칭 → 서빙 순서로 분리하면 나중에 모델을 바꾸기가 쉽습니다.
- **Dedicated 모드를 확인합니다.** Runtime ML 클러스터에서 Unity Catalog 데이터를 읽으려면 Dedicated 접근 모드가 필요합니다. 그룹에 할당하면 사용자 권한이 그룹 권한으로 축소됩니다.
- **Photon 기대치를 맞춥니다.** Python 패키지 중심 워크로드(XGBoost, PyTorch, TensorFlow)에는 Photon이 개선 효과를 주지 않습니다.
- AutoML이 모든 ML 런타임에 내장되어 있다고 가정하지 마십시오. 런타임 버전별 지원은 [모델 학습 도구](model-training.md)에서 확인합니다.
- 상태 라벨(GA, Public Preview, Beta)은 기능마다 다릅니다. 이 장의 각 페이지에 표기된 값만 신뢰하고, 표기가 없으면 "문서에 명시 없음"으로 읽으십시오.

## 참고 문서

- [Machine learning on Databricks](https://docs.databricks.com/aws/en/machine-learning/)
- [Databricks Runtime for ML](https://docs.databricks.com/aws/en/machine-learning/databricks-runtime-ml)
- [AI Runtime](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/)
- [Feature Store](https://docs.databricks.com/aws/en/machine-learning/feature-store/)
- [Unity Gateway (AI governance)](https://docs.databricks.com/aws/en/ai-gateway/)
