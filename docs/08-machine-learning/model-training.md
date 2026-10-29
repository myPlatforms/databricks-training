# 모델 학습 도구

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

이 페이지는 Databricks에서 모델을 학습하는 도구를 정리합니다. 고전 ML은 ML 런타임(Databricks Runtime for ML) 위에서 학습하고, 하이퍼파라미터 튜닝은 Optuna나 Ray Tune을 씁니다. 큰 데이터와 모델은 분산 학습을 씁니다. 딥러닝 GPU 워크로드는 AI Runtime(서버리스 GPU)을 씁니다.

## 왜 필요한가

| 이전 방식의 한계 | 학습 도구가 해결하는 것 |
|---|---|
| 라이브러리 버전을 맞추느라 클러스터 설정에 시간이 든다 | ML 런타임이 주요 ML·DL 라이브러리를 미리 구성한다 |
| 파라미터 탐색을 손으로 한다 | 튜닝 라이브러리(Optuna, Ray Tune)로 탐색을 자동화한다 |
| 단일 머신 메모리를 넘는 모델을 학습하지 못한다 | 분산 학습 옵션(TorchDistributor, DeepSpeed distributor, Ray, Spark ML)으로 나눠 학습한다 |
| GPU 클러스터를 직접 띄우고 내린다 | AI Runtime이 서버리스 GPU를 노트북이나 잡에서 바로 쓰게 한다 |

## 도구 지도와 상태

| 목적 | 도구 | 상태·비고 (문서 원문) |
|---|---|---|
| 고전 ML 실행 환경 | Databricks Runtime for ML | 상태 라벨 없음 |
| 자동 모델 탐색 | AutoML | DBR 18.0 ML 이상에서 내장 라이브러리 아님. 아래 "AutoML" 절 참고 |
| 단일 노드 하이퍼파라미터 튜닝 | Optuna | 문서 권장 |
| 분산 하이퍼파라미터 튜닝 | Ray Tune | ML 런타임에 Ray와 함께 포함. 문서 권장 |
| 하이퍼파라미터 튜닝 (구) | Hyperopt | **유지보수 중단**. DBR 16.4 LTS ML 이후 ML 런타임에 포함되지 않음 |
| MLlib 자동 추적 (구) | CrossValidator, TrainValidationSplit의 자동 MLflow 기록 | **deprecated**, 기본 비활성 (DBR 10.4 LTS ML 이상) |
| 분산 학습 (PyTorch) | TorchDistributor | ML 런타임에 포함 |
| 분산 학습 (메모리 제약) | DeepSpeed distributor (TorchDistributor 기반) | ML 런타임에 포함 |
| 분산 학습 (Spark ML) | `pyspark.ml.connect` | DBR 17.0 이상 Standard 컴퓨트에서 기본 활성 |
| 서버리스 GPU 학습 | AI Runtime | 온디맨드 A10, H100 |

> **참고** 분산 학습 원문에는 GA, Beta, Public Preview 같은 상태 라벨이 없습니다. 이 장은 상태를 추측해 쓰지 않습니다.

## AutoML

### 현재 지원 범위

AutoML 페이지와 ML 런타임 페이지의 설명이 다르므로 두 문서를 함께 적습니다.

| 출처 | 원문 내용 |
|---|---|
| AutoML 페이지 (2026-09-11 갱신) | "Databricks Runtime 18.0 ML 이상에서 AutoML은 내장 라이브러리로 포함되지 않는다" |
| AutoML 페이지 | 대체 기능은 명시하지 않는다. 다음 단계 목록의 "Forecasting (serverless)"가 대체라고 쓰지는 않는다 |
| ML 런타임 페이지 | AutoML을 학습 옵션으로 소개하며, 버전별 제외는 쓰지 않는다 |

AutoML 페이지가 설명하는 흐름은 다음과 같습니다.

1. 데이터셋을 정리하고 준비한다.
2. 여러 알고리즘에 대해 분산 학습과 하이퍼파라미터 튜닝을 수행한다.
3. scikit-learn, XGBoost, LightGBM, Prophet, ARIMA 등 오픈소스 알고리즘으로 후보를 평가한다.
4. 결과를 보여 주고, 각 시도(trial)의 소스 노트북을 만든다.

> **주의** DBR 18.0 ML 이상에서 AutoML이 내장되지 않는다는 문장을 기준으로, 노트북을 옮기기 전에 런타임 버전을 먼저 확인하십시오. 이 장은 "대체 기능이 AutoML과 동등하다"고 쓰지 않습니다.

## 하이퍼파라미터 튜닝

문서의 튜닝 페이지는 다음을 명시합니다.

| 항목 | 원문 내용 |
|---|---|
| 단일 노드 권장 | Optuna |
| 분산 튜닝 권장 | Ray Tune. 분산 튜닝에서 Hyperopt가 하던 역할을 한다고 설명 |
| Hyperopt | 더 이상 유지보수되지 않음. DBR 16.4 LTS ML 이후 포함되지 않음 |
| MLlib 자동 추적 | deprecated. 기본 비활성. 대체는 `mlflow.pyspark.ml.autolog()` (Databricks Autologging에서 기본 활성) |

> **주의** 오래된 노트북은 `hyperopt`를 쓰고 있을 가능성이 큽니다. 옮길 때는 Optuna나 Ray Tune의 예제 노트북을 따르십시오. 이 페이지는 Optuna와 Ray Tune의 호출 코드를 원문에서 확인하지 못해 싣지 않았습니다.

튜닝 결과는 MLflow 런으로 남기는 것을 권장합니다. 자세한 기록 방법은 [MLflow 실험 추적](mlflow-tracking.md)을 참고하십시오.

## 런타임 선택

ML 런타임은 클러스터 생성 시 Databricks Runtime ML 버전을 고릅니다. GPU 인스턴스는 워커 유형(Worker type)에서 고릅니다. 문서는 딥러닝 GPU 워크로드에 AI Runtime을 권장합니다.

| 필요 조건 | 권장 선택 | 원문 근거 |
|---|---|---|
| 고전 ML과 Spark 데이터 처리 | Databricks Runtime for ML | 사전 구성 ML 라이브러리 포함 (XGBoost, Ray 등 문서가 언급) |
| Unity Catalog 데이터에 안전하게 접근 | Dedicated 접근 모드 | ML 런타임 요구 사항 |
| 커스텀 딥러닝 학습·추론, GPU | AI Runtime | 문서가 ML 런타임 대신 권장 |
| Photon 가속 | Databricks Runtime 15.2 ML 이상 | ML 런타임 페이지 |
| Graviton 인스턴스 | Databricks Runtime 15.4 LTS ML 이상 | ML 런타임 페이지 |
| 세분화된 접근 제어, Dedicated 모드에서 Lakeflow pipeline 테이블 조회 | Databricks Runtime 15.4 LTS ML 이상 | ML 런타임 페이지 |

> **참고** 문서는 ML 런타임에 포함된 라이브러리의 전체 목록을 싣지 않고 릴리즈 노트를 보라고 안내합니다. 이 장은 목록을 추정하지 않았습니다.

## AI Runtime (서버리스 GPU)

AI Runtime은 딥러닝 학습, 파인튜닝 등을 위한 **완전 관리형 서버리스 GPU 컴퓨트** 입니다. 관리형 환경, 내장 관측성, 오케스트레이션도 제공한다고 문서가 설명합니다. 상태 라벨은 원문에 없습니다.

| 항목 | 내용 (문서 원문) |
|---|---|
| GPU 종류 | 온디맨드 A10, H100. 다른 가속기는 명시되지 않음 |
| 클러스터 설정 | 필요 없음. 노트북을 바로 연결 |
| 분산 확장 | "Flexible scaling"으로 여러 GPU와 노드에 걸친 분산 학습을 지원 |
| 과금·리전 | 원문 페이지에 없음 |

### 시작 경로

| 경로 | 설명 (문서 요약) |
|---|---|
| Quickstart | 터미널에서 AI Runtime으로 첫 워크로드를 실행 |
| Databricks CLI | YAML 작업 구성으로 분산 GPU 학습 잡을 제출하고 관리 |
| 노트북 | 노트북을 AI Runtime에 연결해 클러스터 없이 대화형으로 개발 |
| 잡(Jobs) | GPU 워크로드를 반복 잡으로 예약하고, 업스트림과 다운스트림 태스크와 연결 |
| Ray | Ray Core, Ray Data, Ray Train, Ray Tune을 AI Runtime에서 실행 |

Quickstart와 CLI의 세부 명령은 해당 페이지에서 확인하십시오. 이 장은 명령을 추정하지 않았습니다.

## 분산 학습 옵션

| 옵션 | 무엇에 쓰는가 | 원문의 요구 사항 |
|---|---|---|
| TorchDistributor | Spark 클러스터에서 PyTorch 학습을 Spark 잡으로 실행하는 PySpark 모듈 (오픈소스) | ML 런타임 포함 |
| DeepSpeed distributor | 메모리가 부족한 큰 모델. TorchDistributor 기반 (DeepSpeed는 Microsoft의 오픈소스) | ML 런타임 포함 |
| Ray | 병렬 연산과 ML 워크플로 확장 (Ray on Databricks) | ML 런타임 포함 |
| Spark ML (`pyspark.ml.connect`) | Spark ML 모델의 분산 학습과 추론 | DBR 17.0 이상, Standard 컴퓨트에서 기본 활성 |

> **참고** 분산 학습 페이지는 서버리스 GPU와 Horovod를 분산 학습 옵션으로 언급하지 않습니다. 딥러닝 GPU 분산 학습은 AI Runtime의 Flexible scaling 설명을 따르십시오.

## 트레이드오프

| 선택지 | 장점 | 단점 |
|---|---|---|
| AutoML | 여러 알고리즘을 빠르게 비교하고 노트북을 만든다 | DBR 18.0 ML 이상에서 내장되지 않는다. 생성된 노트북은 검토가 필요하다 |
| 직접 학습 코드와 튜닝 (Optuna, Ray Tune) | 모델과 피처를 완전히 통제한다 | 코드와 실험 관리 부담이 크다 |
| 분산 학습 (TorchDistributor, Ray 등) | 큰 데이터와 모델을 나눠 학습한다 | 클러스터 구성과 디버깅 부담이 있다 |
| AI Runtime (서버리스 GPU) | 클러스터 설정 없이 GPU를 쓴다 | GPU 종류가 원문 기준 A10과 H100으로 한정 |

## 주의사항

- **런타임 버전을 먼저 고정하십시오.** 같은 노트북이라도 DBR 버전에 따라 AutoML 가용성이 다를 수 있습니다.
- **Hyperopt 코드를 새로 쓰지 마십시오.** 유지보수가 중단되었고 최신 ML 런타임에 없습니다.
- **MLlib 자동 추적 대신 `pyspark.ml.autolog()`를 확인하십시오.** 구 방식은 deprecated입니다.
- **학습 결과를 MLflow 런으로 남기십시오.** 최종 모델은 [MLflow 실험 추적](mlflow-tracking.md)과 [Unity Catalog의 모델](models-in-unity-catalog.md)을 거쳐 등록해야 서빙으로 이어집니다.
- **GPU 딥러닝을 고전 ML 클러스터에 억지로 맞추지 마십시오.** 문서는 AI Runtime을 권장합니다.

## 참고 문서

- [Databricks Runtime for ML](https://docs.databricks.com/aws/en/machine-learning/databricks-runtime-ml)
- [AI Runtime](https://docs.databricks.com/aws/en/machine-learning/ai-runtime/)
- [Distributed training](https://docs.databricks.com/aws/en/machine-learning/train-model/distributed-training/)
- [Hyperparameter tuning](https://docs.databricks.com/aws/en/machine-learning/automl-hyperparam-tuning/)
- [AutoML](https://docs.databricks.com/aws/en/machine-learning/automl/)
- [Ray on Databricks](https://docs.databricks.com/aws/en/machine-learning/ray/)
