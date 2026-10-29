# 08. 머신러닝 (MLflow·Model Serving)

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

이 장은 Databricks에서 머신러닝 모델을 **만들고(학습), 추적하고(MLflow), 등록하고(Unity Catalog 모델), 서빙하는** 흐름을 다룹니다. 대상은 데이터 사이언티스트, ML 엔지니어, 그리고 모델을 애플리케이션에 붙이는 플랫폼 담당자입니다.

이 장은 **서빙과 게이트웨이 기반까지** 를 다룹니다. 에이전트(Agent Bricks, 에이전트 프레임워크, 평가)는 09장에서 다룹니다. 즉, 이 장의 Model Serving과 Unity Gateway 페이지는 에이전트를 올리는 데 필요한 기반 기능만 설명합니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- ML 워크로드에 쓰는 컴퓨트(ML 런타임, AI Runtime 서버리스 GPU)를 구분하고 선택 기준을 설명합니다.
- MLflow 실험 추적으로 파라미터·메트릭·모델을 기록하고, MLflow 3의 로깅 모델(Logged Models) 개념을 이해합니다.
- Unity Catalog의 등록 모델에 버전을 등록하고, 별칭(alias)으로 배포 대상을 바꾸는 방법과 필요한 권한을 설명합니다.
- 피처 테이블(Feature Table)과 피처 뷰(Feature View)를 만들고, 온라인 피처 스토어(Online Feature Store)로 실시간 서빙에 연결합니다.
- AutoML의 현재 지원 범위를 확인하고, 분산 학습 옵션(TorchDistributor, DeepSpeed, Ray, Spark ML)을 비교합니다.
- Model Serving 커스텀 모델 엔드포인트를 만들고, 상태를 확인하고, 중지·삭제합니다.
- Foundation Model APIs의 과금 방식(pay-per-token, 우선순위, provisioned throughput)을 워크로드에 맞게 고릅니다.
- Unity Gateway로 사용량 추적, 한도(rate limit), 가드레일(guardrails)을 설정하는 범위를 파악합니다.
- 데이터 품질 모니터링(Data quality monitoring)의 이상 탐지와 데이터 프로파일링 기능을 구분합니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [ML 개요](ml-overview.md) | 100 | Databricks의 ML 구성 요소 지도, ML 런타임, AI Runtime(서버리스 GPU), 전체 흐름 |
| 2 | [MLflow 실험 추적](mlflow-tracking.md) | 200 | 실험(Experiment)과 런(Run), 자동 로깅, MLflow 3의 로깅 모델과 평가 |
| 3 | [Unity Catalog의 모델](models-in-unity-catalog.md) | 200 | 등록 모델·버전, 별칭(Champion 등), 권한 모델, 제약 사항 |
| 4 | [피처 스토어](feature-store.md) | 300 | 피처 테이블, 피처 뷰, 학습 시 point-in-time 조인, 온라인 피처 스토어 |
| 5 | [모델 학습 도구](model-training.md) | 200 | AutoML의 런타임별 지원, 하이퍼파라미터 튜닝, 분산 학습 옵션 |
| 6 | [Model Serving 커스텀 모델](model-serving.md) | 200 | 엔드포인트 생성·업데이트·중지·삭제, 스케일 투 제로, 상태 값 |
| 7 | [Foundation Model APIs](foundation-model-apis.md) | 300 | pay-per-token, 우선순위 모드, provisioned throughput(온디맨드·예약) |
| 8 | [Unity Gateway](unity-gateway.md) | 300 | 모델·MCP 서버 거버넌스, 사용량 추적, 한도, 가드레일, 서비스 정책 |
| 9 | [데이터 품질 모니터링](data-quality-monitoring.md) | 200 | 이상 탐지, 데이터 프로파일링, 구 명칭 Lakehouse Monitoring과의 관계 |
| 10 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 9개와 실무 체크리스트 |

권장 순서는 위 표와 같습니다. 1~3페이지(추적과 등록)를 먼저 익히면, 4~6페이지(피처, 학습, 서빙)가 같은 모델 이름 체계 위에서 이해됩니다.

## 선수 지식

- **Python과 scikit-learn 같은 ML 라이브러리 기초**: 학습 스크립트와 모델 객체(fit, predict)를 읽을 수 있어야 합니다.
- **Unity Catalog 기초**: 모델과 함수는 `catalog.schema.name` 3단계 이름을 씁니다. 권한 개념은 [권한 모델과 소유권](../06-unity-catalog/privileges-and-ownership.md)에서 다룹니다.
- **Delta 테이블 기초**: 피처 테이블은 Unity Catalog의 Delta 테이블입니다. 자세한 내용은 [02장](../02-lakehouse-storage/README.md)을 참고하십시오.
- **REST API와 Databricks CLI 기초**: 엔드포인트 생성·관리 예제는 REST API와 CLI 명령을 사용합니다.

## 이 장의 범위에서 제외한 내용

| 제외 항목 | 다루는 장 |
|---|---|
| Agent Bricks, 에이전트 프레임워크, 에이전트 평가 | 09장에서 다룹니다 |
| 노트북 기반 데이터 과학 보조 기능 | [Genie Code](../11-developer-tools/genie-code/README.md)에서 다룹니다 |
| 배치 추론을 파이프라인 태스크로 구성하는 방법 | [Lakeflow Jobs](../04-data-engineering/jobs-tasks-and-triggers.md)에서 다룹니다 |
| 온라인 피처 스토어의 백엔드 데이터베이스 | [Lakebase](../10-lakebase/what-is-lakebase.md)에서 다룹니다 |

## 이 장의 읽는 법

각 기능 페이지는 **왜 필요한가, 어떻게 동작하는가, 어떻게 쓰는가, 트레이드오프, 주의사항** 순서입니다. 기능마다 상태(GA, Public Preview, Beta)를 표기합니다. 공식 문서 원문에 상태 표기가 없으면 "문서에 명시 없음"이라고 씁니다.

> **참고** 이 장의 제품명은 2026-10-28 기준 공식 문서 표기를 따릅니다. 예를 들어 Lakehouse Monitoring은 현재 **Data quality monitoring** 아래의 데이터 프로파일링으로 안내되며, 게이트웨이 기능의 제품명은 **Unity Gateway** 입니다. 구 명칭은 페이지마다 처음 한 번만 괄호로 병기합니다.

> **주의** AutoML과 게이트웨이 기능 등 일부 항목은 문서 페이지 사이에 상태 표기가 다르거나 서로 다르게 설명되어 있습니다. 해당 내용은 각 페이지에 명시했습니다. 실제 적용 전에 참고 문서 링크에서 원문을 다시 확인하십시오.

## 참고 문서

- [Machine learning on Databricks](https://docs.databricks.com/aws/en/machine-learning/)
- [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/)
- [Feature Store](https://docs.databricks.com/aws/en/machine-learning/feature-store/)
- [Deploy models using Model Serving](https://docs.databricks.com/aws/en/machine-learning/model-serving/)
- [Databricks Foundation Model APIs](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/)
- [Unity Gateway (AI governance)](https://docs.databricks.com/aws/en/ai-gateway/)
- [Data quality monitoring](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/)
