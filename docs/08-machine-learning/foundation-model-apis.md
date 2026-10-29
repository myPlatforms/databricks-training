# Foundation Model APIs

> 기준일: 2026-10-28 · 근거: 공식 문서

Foundation Model APIs는 Databricks가 호스팅하는 파운데이션 모델(foundation model)을 엔드포인트로 호출하는 기능입니다. 모델을 직접 배포하지 않고 쓸 수 있으며, 과금 방식은 **pay-per-token**, ** 우선순위 pay-per-token**, **provisioned throughput** 세 가지입니다. 문서는 Foundation Model APIs를 Databricks 지정 서비스(Databricks Designated Service)로 분류하며, 데이터 거주를 위해 Databricks Geo를 사용한다고 설명합니다.

## 왜 필요한가

| 이전 방식의 한계 | Foundation Model APIs가 해결하는 것 |
|---|---|
| 오픈 모델을 GPU 서버에 직접 올리고 운영한다 | 호스팅 모델 엔드포인트를 바로 호출한다 |
| 사용량과 무관하게 GPU를 상시 점유한다 | pay-per-token으로 호출량에 따라 과금한다 |
| 운영 트래픽에서 처리량을 예측하기 어렵다 | provisioned throughput으로 전용 용량을 확보한다 |
| 대량 텍스트 처리를 애플리케이션 코드로 짠다 | SQL의 `ai_query`로 테이블 행마다 모델을 호출한다 |

## 과금 방식 비교

| 방식 | 문서 원문 설명 | 약정 | 적합한 워크로드 |
|---|---|---|---|
| **pay-per-token** | 파운데이션 모델에 접근하는 가장 쉬운 방법. 시작 시 권장 | 없음 | 시작 단계, 호출량이 들쭉날쭉한 워크로드 |
| **우선순위 pay-per-token** (priority mode) | 요청마다 `service_tier`를 `"priority"`로 지정해 옵트인. 지연에 민감한 앱용. 더 높은 토큰 단가 | 없음 | 지연 민감 애플리케이션 |
| **provisioned throughput** | 모든 운영 워크로드에 권장. 온디맨드와 예약 두 옵션 | 온디맨드는 없음, 예약은 1개월 또는 3개월 | 운영 워크로드, 성능 보장 필요 |
| **AI Functions 최적화 모델** | 배치 추론에 권장 (문서의 설명) | 문서에 명시 없음 | 대량 배치 추론 |

### 예약과 온디맨드

| 구분 | 특징 (문서 원문) |
|---|---|
| 온디맨드 | 전용 용량을 확보하되 기간 약정이 없다. 할당한 용량에 과금되며 언제든 변경·제거할 수 있다 |
| 예약 | 1개월 또는 3개월 고정 기간 약정. 단위당 단가가 더 낮다 |

> **주의** 문서는 전용 용량이 필요 없다면 우선순위 pay-per-token을 권장합니다. provisioned throughput을 기본값으로 잡지 마십시오.

## 지원 모델 (2026-10-28 기준 문서 목록)

모델 목록은 바뀌므로 아래는 문서에 나온 예시 이름입니다. 전체 목록과 리전 가용성은 [지원 모델 페이지](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)에서 확인하십시오.

| 모델 (엔드포인트 이름) | 제공 방식 | 상태·비고 (문서 원문) |
|---|---|---|
| OpenAI GPT-6.1 Terra (`databricks-gpt-6-1-terra`) | pay-per-token, 우선순위 포함 | Databricks 호스팅 |
| OpenAI GPT-6.1 Sol (`databricks-gpt-6-1-sol`) | pay-per-token | AI Playground 미지원. Responses API 사용 |
| OpenAI GPT-6 Sol (`databricks-gpt-6-sol`) | pay-per-token | 문서에 명시 없음 |
| Google Gemini 4 Argon (`databricks-gemini-4-argon`) | pay-per-token | 글로벌 엔드포인트, 교차 지역 라우팅 필요 |
| DeepSeek V4.1 Flash (`databricks-deepseek-v4-1-flash`) | pay-per-token, 우선순위, 예약 provisioned throughput | **2026-11-19 종료 예정** |
| DeepSeek V4.1 Flash (1017) (`databricks-deepseek-v4-1-flash-1017`) | pay-per-token | 문서에 명시 없음 |
| Google Gemini 3.1 Flash Image, Gemini 3 Pro Image | pay-per-token만 | provisioned throughput, AI Functions 배치 추론, `ai_query`, AI Playground 미지원 |
| TypeSafe AI Jev 1.14.0 | pay-per-token | 제공자 호스팅. 계정 관리자가 TypeSafe AI Models 프리뷰를 켜야 함. System One API 사용 |

> **참고** 문서는 provisioned throughput이 "지원 아키텍처 계열의 모든 모델"을 포함한다고 설명하지만, 계열 목록은 다른 페이지에 있어 이 장에서 확인하지 못했습니다. 문서가 예약 provisioned throughput을 명시한 모델은 DeepSeek V4.1 Flash뿐입니다.

### 종료와 프리뷰 상태

| 항목 | 날짜·상태 (문서 원문) |
|---|---|
| DeepSeek V4 Pro (0813) | 2026-10-30 종료 |
| Thinking Machine Labs Inkling | 2026-10-30 종료 |
| DeepSeek V4 Flash (0731) | deprecated, 2026-11-05 종료 |
| DeepSeek V4.1 Flash | 2026-11-19 종료 |
| Zhipu AI GLM 5.2 | 신규 워크로드에 권장하지 않음 (legacy) |
| Alibaba Cloud Qwen3.5 122B A10B, Qwen3-Embedding-0.6B, Qwen3-Next 80B A3B Instruct, Inkling | Public Preview |

> **주의** 종료 날짜가 가까운 모델을 쓰는 코드는 대체 모델로 옮겨야 합니다. 대체 모델은 supported-models 페이지에서 고르십시오.

## 어떻게 쓰는가

### 방법 1. SQL에서 `ai_query` 호출

`ai_query`는 SQL에서 모델 추론을 직접 호출하는 함수입니다. 원문 문법은 다음과 같습니다.

```sql
ai_query(endpoint, request)
ai_query(endpoint, request, returnType, failOnError)
```

| 파라미터 | 타입·요건 (문서) |
|---|---|
| `endpoint` | `STRING` 리터럴. 같은 워크스페이스의 Foundation Model, 외부 모델, 커스텀 모델 엔드포인트 이름. 정의자는 `CAN QUERY` 필요 |
| `request` | 외부·Foundation Model 엔드포인트는 `STRING`. 커스텀 엔드포인트는 입력 피처 이름과 맞는 단일 컬럼 또는 `STRUCT` |
| `returnType` | 반환 타입 스키마. Databricks Runtime 15.2 이상에서는 선택. 15.1 이하 커스텀 엔드포인트에서는 필수 |
| `failOnError` | 불리언 리터럴, 기본값 `true`. Runtime 15.3 이상. `false`이면 응답과 `errorMessage`를 담은 `STRUCT`를 반환 |
| `modelParameters` | 채팅·완성·임베딩 상수 파라미터 `STRUCT`. Runtime 15.3 이상 |
| `responseFormat` | 채팅 모델 전용. Runtime 15.4 LTS 이상. `text`, `json_object`, `json_schema` |
| `files` | 멀티모달 요청에 필요. JPEG 또는 PNG (`read_files`의 `content` 컬럼 등) |

원문 예제는 다음과 같습니다.

```sql
SELECT *,  ai_query(
  'system.ai.meta-llama-3-3-70b-instruct',
  "Can you tell me the name of the US state that serves the provided ZIP code? zip code: " || pickup_zip
  )
FROM samples.nyctaxi.trips
LIMIT 10
```

| 제약 (문서) | 내용 |
|---|---|
| 지원 환경 | Databricks SQL Classic에서는 쓸 수 없다 |
| 런타임 | Databricks Runtime 15.4 LTS 이상. 18.2 이상 권장 |
| 리전 | 워크스페이스가 Model Serving 지원 리전에 있어야 한다 |
| 과금 | Foundation Model 엔드포인트는 task 전용 함수처럼 과금된다. 커스텀·provisioned throughput 엔드포인트는 전용 서빙 컴퓨트로 과금된다 |
| 배치 권장 | 배치 처리에는 `databricks-` 접두사의 호스팅 모델을 쓰고, provisioned throughput은 쓰지 않는다고 문서가 권장 |

> **참고** `ai_query`는 Beta 표기가 없습니다. 같은 AI Functions 목록의 `ai_search`, `ai_enrich`, `ai_decide` 등은 (Beta)로 표기되어 있습니다.

### 방법 2. OpenAI 호환 클라이언트

문서는 대부분의 Foundation Model APIs가 OpenAI와 호환되므로 OpenAI 클라이언트로 조회할 수 있다고 설명합니다. 설치 명령은 원문 그대로입니다.

```bash
pip install -U databricks-openai
```

```python
dbutils.library.restartPython()
```

클라이언트를 만드는 구체 코드와 채팅 호출 예제는 이 장에서 확인하지 못했습니다. [Use foundation models](https://docs.databricks.com/aws/en/machine-learning/model-serving/score-foundation-models) 페이지의 예제를 따르십시오. 문서는 확장된 대화형 상호작용에 OpenAI 클라이언트를 권장하고, 기능을 살펴볼 때는 UI를 권장합니다.

### 방법 3. REST API

REST 호출은 엔드포인트 호출 경로 `POST /serving-endpoints/{name}/invocations`를 씁니다. 요청 본문의 필수 파라미터와 문법은 [Foundation model REST API reference](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/api-reference)에서 확인하십시오.

### 우선순위 모드 지정

우선순위 모드는 요청마다 `service_tier` 값을 `"priority"`로 지정합니다. 문서는 이 옵션이 약정이 필요 없고, 기본보다 높은 토큰 단가로 과금된다고 설명합니다. 생략하면 기본 pay-per-token 경로를 씁니다. 요청 본문에서의 정확한 위치는 원문 API 레퍼런스에서 확인하십시오.

### provisioned throughput 설정 흐름

| 단계 | 방법 (문서 원문) |
|---|---|
| 1 | `system.ai`에서 모델을 열고 **Serve this model** 버튼 클릭 |
| 2 | Serving UI에서 **Create serving endpoint** 선택, 엔티티로 Unity Catalog 모델 선택 |
| 3 | **Up to** 드롭다운에서 최대 초당 토큰 수 선택, **Modify** 에서 최소값 확인 |
| 4 | API로 가능 여부와 단위 증분 확인: `get-model-optimization-info` (`optimizable`, `model_type`, `throughput_chunk_size` 등) |
| 5 | 생성 API: 처리량 밴드 모델은 `min_provisioned_throughput`, `max_provisioned_throughput`. 모델 유닛 모델은 `provisioned_model_units`를 `/api/2.0/serving-endpoints/pt`에 보냄 |

문서상 제약은 다음과 같습니다.

- Meta Llama 기본(base) 버전은 Unity Catalog에서 배포할 수 없고 **Instruct** 변형을 골라야 합니다.
- Unity Catalog 권한이 금지한 모델의 프로비저닝 엔드포인트는 수동으로 삭제해야 합니다.
- GPU 용량 문제로 생성·업데이트가 시간 초과될 수 있으며, 그때는 계정 팀에 문의하라고 문서가 안내합니다.
- 자동 확장은 설정한 최소와 최대 사이에서 이뤄지지만, 확장 로직은 문서에 설명되어 있지 않습니다.

## 트레이드오프

| 질문 | 판단 기준 |
|---|---|
| 시작 단계인가 | pay-per-token으로 시작 (문서 권장) |
| 지연이 중요한가 | 우선순위 pay-per-token 검토 |
| 운영 트래픽이 일정하고 성능 보장이 필요한가 | provisioned throughput 검토 |
| 약정을 피하고 싶은가 | 온디맨드 provisioned throughput |
| 테이블 전체를 SQL로 처리하는가 | `ai_query`와 배치 권장 모델 |
| 자체 파인튜닝 모델이 필요한가 | 커스텀 모델 서빙 ([Model Serving](model-serving.md)) |

## 주의사항

- **호출 한도를 확인하십시오.** 문서는 Foundation Model APIs 한도 페이지를 링크하지만, 페이지에는 수치가 없습니다. 이 장은 수치를 쓰지 않았습니다.
- **종료 날짜를 코드 리뷰에 넣으십시오.** 2026-10-30, 11-05, 11-19 종료 항목이 있습니다.
- **Gemini 이미지 모델의 제외 기능을 확인하십시오.** `ai_query`와 배치 추론에서 쓸 수 없습니다.
- **데이터 보존은 원문 문장만 인용하십시오.** 일부 모델(예: Claude Fable 5, 5.1)은 보존 정책이 다르다고 원문이 설명하며, 세부는 최신 공식 문서를 기준으로 확인하십시오.
- **게이트웨이 정책을 함께 검토하십시오.** 사용량 추적, 한도, 가드레일은 [Unity Gateway](unity-gateway.md)에서 다룹니다.

## 참고 문서

- [Databricks Foundation Model APIs](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/)
- [Supported models](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models)
- [Deploy provisioned throughput Foundation Model APIs](https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/deploy-prov-throughput-foundation-model-apis)
- [Use foundation models (score-foundation-models)](https://docs.databricks.com/aws/en/machine-learning/model-serving/score-foundation-models)
- [ai_query 함수](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [AI Functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
