# 퀴즈와 체크리스트

> 기준일: 2026-10-29 · 근거: 이 장 본문 · 수준: 100~300

이 장에서 다룬 내용을 확인하는 문제입니다. 정답을 펼치면 해설과 근거 페이지로 가는 링크가 있습니다.

## 퀴즈

### 1. 피처 스토어가 해결하려는 대표 문제로 옳은 것은? (수준 100)

- A. 모델 버전마다 GPU 인스턴스 타입을 자동으로 고른다.
- B. 학습과 서빙에서 같은 피처 정의를 재사용해 학습-서빙 왜곡을 줄인다.
- C. 노트북 실행 결과를 MLflow 대신 파일로 저장한다.
- D. 엔드포인트 트래픽을 여러 모델 버전에 나눈다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 학습용 피처를 배치 파이프라인에서, 서빙용 피처를 애플리케이션 코드에서 따로 계산하면 생기는 불일치 문제를 짚고, 피처 정의를 한 곳에 두어 학습과 서빙이 같은 정의를 쓰게 한다고 설명합니다. A는 컴퓨트 선택, C는 MLflow 기록, D는 Model Serving의 트래픽 설정에 해당하며 피처 스토어의 역할이 아닙니다.

근거: [피처 스토어 — 왜 필요한가](feature-store.md#왜-필요한가)

</details>

### 2. MLflow 3의 로깅 모델(LoggedModel)에 대한 설명으로 옳은 것은? (수준 100)

- A. 실험 런과 분리되어, `model_id`로 메타데이터·메트릭·파라미터·코드를 묶는 모델 단위 기록이다.
- B. 활성 런 바깥에서는 모델을 기록할 수 없다.
- C. 모델 레지스트리의 스테이지 이름과 같은 개념이다.
- D. 노트북의 자동 로깅을 끄는 설정 값이다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: A** — 본문은 MLflow 3이 모델을 실험 런과 분리된 로깅 모델로 다루며, 고유 ID인 `model_id`로 메타데이터, 메트릭, 파라미터, 코드를 묶는다고 설명합니다. 본문은 MLflow 3에서 활성 런 없이도 모델을 기록할 수 있다고도 설명하므로 B는 틀립니다. C는 본문이 Unity Catalog 레지스트리에서 스테이지를 지원하지 않는다고 명시한 점과 어긋납니다. D는 본문에 없는 설명입니다.

근거: [MLflow 실험 추적 — 핵심 개념](mlflow-tracking.md#핵심-개념), [MLflow 실험 추적 — MLflow 3 설치와 변경점](mlflow-tracking.md#mlflow-3-설치와-변경점)

</details>

### 3. Unity Gateway의 역할을 가장 잘 설명한 것은? (수준 100)

- A. 모델 학습에 쓸 GPU 클러스터를 자동으로 만든다.
- B. 모델과 MCP 서버 등의 런타임 호출에 접근 제어, 트래픽 한도, 가드레일, 사용량 추적을 적용하는 거버넌스 계층이다.
- C. 피처 테이블을 온라인 스토어에 게시한다.
- D. 데이터 적재가 늦어지면 테이블을 stale로 표시한다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 Unity Gateway를 Unity Catalog 위에서 모델, 모델 제공자 서비스, MCP 서버, 에이전트 도구의 런타임 호출을 관리하는 거버넌스 계층으로 설명합니다. 접근 제어, 트래픽 한도, 가드레일, 사용량 추적을 한 체계로 묶는다고 합니다. A는 학습 컴퓨트, C는 피처 스토어, D는 데이터 품질 모니터링의 기능으로, 본문에서 각각 다른 페이지에 속합니다.

근거: [Unity Gateway — 왜 필요한가](unity-gateway.md#왜-필요한가)

</details>

### 4. 커스텀 딥러닝 모델을 GPU로 파인튜닝하려고 합니다. 노트북을 클러스터 설정 없이 바로 연결하고 싶습니다. 본문 기준 가장 적절한 선택은? (수준 200)

- A. Databricks Runtime for ML 클래식 클러스터에 GPU 워커를 붙인다.
- B. AI Runtime(서버리스 GPU)을 쓴다.
- C. 단일 노드 Python 프로세스에서 CPU로 학습한다.
- D. 피처 스토어의 온라인 스토어를 학습 컴퓨트로 쓴다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문의 선택 기준 표는 커스텀 딥러닝 학습과 파인튜닝, GPU 중심 워크로드에는 AI Runtime을 권장하고, 노트북을 클러스터 설정 없이 바로 쓰고 싶은 경우에도 AI Runtime을 권장합니다. A는 본문이 고전 ML과 Spark 데이터 처리를 같은 클러스터에서 함께 쓸 때 맞는 선택으로 설명한 경로입니다. C와 D는 본문에 근거가 없습니다.

근거: [ML 개요 — 선택 기준](ml-overview.md#선택-기준)

</details>

### 5. 운영 서빙 워크로드가 `models:/prod.ml_team.churn_model@Champion`을 로드하고 있습니다. 새로 검증한 버전을 운영에 올리려면 어떻게 해야 하는가? (수준 200)

- A. 클라이언트 코드에 버전 번호를 하드코딩해 재배포한다.
- B. Champion 별칭을 새 버전으로 재지정한다.
- C. 기존 버전을 삭제해 새 버전이 자동으로 가리키게 한다.
- D. 스테이지를 Production으로 바꾼다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 별칭은 버전을 가리키는 변경 가능한 이름이며, 재지정하면 그 별칭을 참조하는 워크로드가 코드 변경 없이 새 버전을 읽는다고 본문이 설명합니다. 다만 별칭은 즉시 반영되므로 새 버전을 먼저 평가한 뒤 옮기라고 본문이 권장합니다. A는 본문이 피하라고 설명한 방식입니다. C처럼 버전을 지우면 별칭이 새 버전으로 자동으로 옮겨진다는 설명은 본문에 없습니다. D는 본문이 스테이지를 지원하지 않는다고 명시한 방식입니다.

근거: [Unity Catalog의 모델 — 별칭으로 배포 대상 바꾸기](models-in-unity-catalog.md#별칭으로-배포-대상-바꾸기), [Unity Catalog의 모델 — 주의사항](models-in-unity-catalog.md#주의사항)

</details>

### 6. SQL 테이블의 많은 행에 `ai_query`를 적용하는데, 일부 행의 호출이 실패해도 전체 쿼리가 멈추지 않게 하려면 어떻게 해야 하는가? (수준 200)

- A. `failOnError`를 `true`로 두고 오류를 SQL 예외 처리로 잡는다.
- B. `failOnError`를 `false`로 설정해, 응답과 `errorMessage`를 담은 `STRUCT`를 받는다.
- C. `returnType` 인자를 생략한다.
- D. 호출 대상 엔드포인트를 중지한다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 `failOnError`의 기본값이 `true`이며, `false`로 두면 응답과 `errorMessage`를 담은 `STRUCT`를 반환한다고 설명합니다. A는 SQL 예외 처리 구문을 본문이 설명하지 않으며, 기본 동작은 오류 시 실패입니다. C의 `returnType`은 반환 타입 스키마이며 오류 처리와 무관합니다. D는 호출 자체를 막아 목적과 어긋납니다.

근거: [Foundation Model APIs — 방법 1. SQL에서 ai_query 호출](foundation-model-apis.md#방법-1-sql에서-ai_query-호출)

</details>

### 7. 운영 중인 Model Serving 엔드포인트의 모델 버전을 올리려고 합니다. 클라이언트 쪽 변경을 최소화하는 방법은? (수준 200)

- A. 새 엔드포인트 이름을 만들고 클라이언트의 호출 주소를 모두 바꾼다.
- B. 엔드포인트 이름은 그대로 두고, 서빙 엔티티와 트래픽 설정을 새 버전으로 업데이트한다.
- C. 엔드포인트를 삭제한 뒤 같은 이름으로 다시 만든다.
- D. 모델 파일을 서빙 서버에 직접 복사한다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 엔드포인트 이름을 클라이언트가 알고, 교체는 서빙 엔티티 업데이트로 하는 구성이 유지보수에 좋다고 설명합니다. 구성 업데이트는 `config`의 `served_entities`와 `traffic_config`를 보내는 방식입니다. A와 C는 클라이언트 변경을 늘리거나 삭제 위험을 키우며, 삭제는 되돌릴 수 없다고 본문이 명시합니다. D는 본문이 설명하는 서빙 방식이 아닙니다.

근거: [Model Serving 커스텀 모델 — 구성 업데이트](model-serving.md#구성-업데이트), [Model Serving 커스텀 모델 — 주의사항](model-serving.md#주의사항)

</details>

### 8. Unity Gateway 서비스 정책을 붙였는데 정책 평가 과정에서 오류가 발생했습니다. 본문 기준으로 옳은 설명은? (수준 300)

- A. 평가 실패 요청은 ALLOW로 처리되어 서비스가 계속된다.
- B. 평가 오류(타임아웃 포함)는 DENY로 처리되므로, 운영 전에 타임아웃과 장애 시 동작을 테스트하고 로그 모드로 먼저 관찰하는 편이 안전하다.
- C. 정책은 평가 실패 시 사용자의 쿼리 권한을 자동으로 회수한다.
- D. 로그 모드에서는 정책이 DENY 결정을 내리면 요청이 차단된다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 평가 중 발생한 오류를 DENY로 처리하는 fail closed 방식이며, 타임아웃도 오류에 포함된다고 설명합니다. 동시에 정책 시스템에 장애가 나면 정상 요청도 모두 차단될 수 있으므로, 로그 모드로 먼저 관찰하고 장애 시 동작을 테스트하라고 주의를 줍니다. A는 fail closed와 반대입니다. C는 본문에 없는 동작입니다. D는 본문이 로그 모드를 차단하지 않고 결정만 기록하는 모드로 설명한 점과 어긋납니다.

근거: [Unity Gateway — 평가 순서와 실패 동작](unity-gateway.md#평가-순서와-실패-동작)

</details>

### 9. 전용 용량을 따로 확보하지 않고, 요청마다 지연 민감도를 높여 처리하고 싶습니다. 본문 기준 가장 적절한 Foundation Model APIs 과금 방식은? (수준 300)

- A. 예약 provisioned throughput
- B. 온디맨드 provisioned throughput
- C. 우선순위 pay-per-token
- D. AI Functions 배치 추론에 최적화된 모델

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 본문은 우선순위 pay-per-token이 요청마다 `service_tier`를 `"priority"`로 지정해 옵트인하는 방식이며, 지연에 민감한 애플리케이션용이라고 설명합니다. 약정이 필요 없지만 토큰 단가는 기본보다 높다고 합니다. A는 1개월 또는 3개월 약정과 전용 용량이 필요하고, B는 전용 용량을 확보하는 방식입니다. D는 배치 추론에 권장되는 옵션으로, 요청 단위 지연 우선 처리와 목적이 다릅니다.

근거: [Foundation Model APIs — 과금 방식 비교](foundation-model-apis.md#과금-방식-비교)

</details>

## 실무 체크리스트

이 장의 내용을 실제 환경에 적용할 때 확인할 항목입니다.

- [ ] 학습 파이프라인과 온라인 서빙이 같은 피처 정의를 쓰는지 확인하고, 온라인 게시 전에 기본 키와 NOT NULL 조건을 맞춘다 — [피처 스토어](feature-store.md#4-온라인-스토어에-게시)
- [ ] 운영 모델은 버전 번호가 아니라 별칭(예: Champion)으로 가리키고, 별칭을 옮기기 전에 새 버전의 평가를 끝낸다 — [Unity Catalog의 모델](models-in-unity-catalog.md#주의사항)
- [ ] 서빙 워크로드가 쓰는 서비스 계정에 실행 권한만 부여하고, 등록과 별칭 변경 권한은 학습 파이프라인 계정에만 둔다 — [Unity Catalog의 모델](models-in-unity-catalog.md#권한)
- [ ] 운영 엔드포인트는 스케일 투 제로를 끄고, 콜드 스타트 지연 영향을 확인한다 — [Model Serving 커스텀 모델](model-serving.md#스케일링)
- [ ] 엔드포인트를 삭제하기 전에 이를 호출하는 클라이언트가 없는지 확인한다. 삭제는 되돌릴 수 없다 — [Model Serving 커스텀 모델](model-serving.md#상태-조회-중지-시작-삭제)
- [ ] 사용 중인 Foundation Model의 종료 날짜를 정기적으로 확인하고, 대체 모델을 미리 정한다 — [Foundation Model APIs](foundation-model-apis.md#종료와-프리뷰-상태)
- [ ] 게이트웨이 서비스 정책은 로그 모드로 먼저 관찰한 뒤 차단 모드로 바꾸고, 평가 모델 장애 시 동작을 테스트한다 — [Unity Gateway](unity-gateway.md#평가-순서와-실패-동작)
- [ ] 한도 초과(429)를 받는 클라이언트가 지수 백오프로 재시도하도록 구현한다 — [Unity Gateway](unity-gateway.md#트래픽-관리-속도-제한-rate-limits)
- [ ] 사용량 시스템 테이블과 대시보드를 조회할 주체에게 필요한 권한을 설계한다 — [Unity Gateway](unity-gateway.md#권한과-대시보드-설정)
- [ ] 데이터 품질 모니터링을 스키마 단위로 켜기 전에 대상 테이블과 제외할 테이블을 정하고, 끄면 결과가 삭제된다는 점을 운영 절차에 넣는다 — [데이터 품질 모니터링](data-quality-monitoring.md#스키마에서-켜기)

## 참고 문서

이 페이지는 이 장 본문을 근거로 합니다. 공식 문서 링크는 각 본문 페이지의 참고 문서를 보세요.

- [ML 개요](ml-overview.md)
- [MLflow 실험 추적](mlflow-tracking.md)
- [Unity Catalog의 모델](models-in-unity-catalog.md)
- [피처 스토어](feature-store.md)
- [모델 학습 도구](model-training.md)
- [Model Serving 커스텀 모델](model-serving.md)
- [Foundation Model APIs](foundation-model-apis.md)
- [Unity Gateway](unity-gateway.md)
- [데이터 품질 모니터링](data-quality-monitoring.md)
