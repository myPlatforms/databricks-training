# AI Functions

> 기준일: 2026-10-28 · 근거: 공식 문서

AI Functions는 SQL 함수 호출만으로 텍스트 요약, 분류, 문서 파싱, 필드 추출, 모델 호출을 수행하는 함수 묶음입니다. 공식 문서는 함수를 문서 처리, 텍스트 변환, 텍스트 분석, 콘텐츠 생성, 예측, 시계열 예측, 메트릭 변화 분석, 검색 임베딩 등으로 묶어 제공합니다. 이 페이지는 함수 목록과 상태 라벨, 범용 함수인 `ai_query`와 문서 처리 함수인 `ai_extract`, `ai_parse_document`의 요구 사항과 권한을 다룹니다.

## 왜 필요한가

LLM이나 문서 처리 모델을 쓰려면 보통 엔드포인트를 만들고, 파이썬으로 요청을 보내고, 응답을 파싱해 테이블에 적재하는 코드가 필요합니다. 이 과정은 노트북이나 잡에 흩어지기 쉽고, 권한도 별도로 관리해야 합니다. AI Functions는 이를 SQL 식(expression) 한 줄로 바꿔, 데이터 옆에서 배치 처리하고 Unity Catalog 권한과 함께 관리하게 합니다.

| 작업 | 전통적 방식 | AI Functions 방식 |
|---|---|---|
| 문서에서 필드 추출 | 파싱 라이브러리와 모델 호출을 직접 작성 | `ai_parse_document`와 `ai_extract`를 SQL로 연결 |
| 임의 모델 호출 | 엔드포인트 클라이언트 코드 작성 | `ai_query`로 엔드포인트 이름과 요청을 지정 |
| 텍스트 요약·번역·분류 | 모델별 프롬프트 코드 | 전용 함수(`ai_summarize`, `ai_translate`, `ai_classify`) 호출 |

## 어떻게 동작하는가

### 함수 목록과 상태 라벨

공식 문서의 AI Functions 페이지는 함수를 묶음으로 나눕니다. 아래 표는 문서에 표시된 라벨을 그대로 옮긴 것입니다. 페이지는 GA나 Public Preview라는 말을 쓰지 않고, 일부 함수 이름 뒤에만 `(Beta)`를 붙입니다. 라벨이 없는 함수는 "라벨 없음(원문 기준)"입니다.

| 묶음 | 함수 | 상태 라벨 (원문 기준) |
|---|---|---|
| 문서 처리 | `ai_parse_document`, `ai_extract`, `ai_classify` | 라벨 없음 |
| 문서 처리 | `ai_prep_search`, `ai_search`, `ai_enrich` | (Beta) |
| 음성 | `ai_transcribe` | (Beta) |
| 텍스트 변환 | `ai_fix_grammar`, `ai_translate`, `ai_summarize`, `ai_mask` | 라벨 없음 |
| 텍스트 분석 | `ai_decide` | (Beta) |
| 텍스트 분석 | `ai_analyze_sentiment`, `ai_similarity` | 라벨 없음 |
| 콘텐츠 생성 | `ai_gen` | 라벨 없음 |
| 예측 | `ai_predict_class`, `ai_predict_value` | (Beta) |
| 시계열 예측 | `ai_forecast` | 라벨 없음 |
| 시계열 예측 | `ai_detect_anomalies` | (Beta) |
| 메트릭 변화 분석 | `ai_top_drivers` | (Beta) |
| 검색 임베딩 | `vector_search` | 라벨 없음 |
| 범용 | `ai_query` | 라벨 없음 |

> **참고** 이 표의 "라벨 없음"은 "공식 문서가 GA라고 명시했다"는 뜻이 아닙니다. 원문에 라벨이 표시되지 않았다는 뜻입니다. 운영 도입 전에는 각 함수의 상세 페이지와 릴리즈 노트를 확인하십시오.

### 실행 환경 요구 사항

공식 문서의 AI Functions 페이지가 밝히는 공통 조건은 다음과 같습니다.

| 항목 | 문서 원문 기준 |
|---|---|
| 웨어하우스 유형 | Databricks SQL Classic 웨어하우스에서는 AI Functions를 쓸 수 없음 |
| 런타임 | Databricks Runtime 15.4 LTS 이상 필요. 18.2 이상을 권장 |
| 배치 워크로드의 `ai_query` 모델 | 프로비저닝 처리량(provisioned throughput)이 아닌 Databricks 호스팅 파운데이션 모델(`databricks-` 접두사) 사용을 권장 |
| 권한 제한 | 작업별 함수 접근은 "AI Functions Unity Catalog permissions" 문서를 따라 제한 가능 |

## 대표 함수 세 가지

### ai_query: 엔드포인트 호출

`ai_query`는 파운데이션 모델 엔드포인트, 외부 모델 엔드포인트, 커스텀 엔드포인트를 SQL에서 호출하는 범용 함수입니다.

**문법 (문서 기준)**

```sql
-- 모델 스키마가 있는 엔드포인트(파운데이션 모델, 외부 모델 포함)
ai_query(endpoint, request)

-- 모델 스키마가 없는 커스텀 엔드포인트
ai_query(endpoint, request, returnType, failOnError)
```

| 인자 | 문서 설명 요약 |
|---|---|
| `endpoint` | 같은 워크스페이스의 엔드포인트 이름을 담은 `STRING` 리터럴. 정의자(definer)에게 `CAN QUERY` 권한이 필요 |
| `request` | 파운데이션·외부 모델은 `STRING`, 커스텀 엔드포인트는 단일 열 또는 `STRUCT` |
| `returnType` | 런타임 15.2 이상에서는 커스텀 엔드포인트의 모델 스키마에서 추론. 15.1 이하는 필수 |
| `failOnError` | 기본값 `true`. 런타임 15.3 이상. `false`면 파싱된 응답과 오류 메시지를 담은 `STRUCT`를 반환 |
| `modelParameters` | 런타임 15.3 이상. 상수 값만 허용 (데이터에 따라 달라지는 값 불가). `temperature` 기본값은 0.0 |
| `responseFormat` | 런타임 15.4 LTS 이상. 채팅 파운데이션 모델에서만 사용. `text`, `json_object`, `json_schema` 지원 |

```sql
-- 외부 모델 엔드포인트를 호출하는 예시 (문서 예시와 동일한 형태)
SELECT ai_query(
  'my-external-model-openai-chat',
  'Describe Databricks SQL in 30 words.'
) AS summary;
```

> **주의** `responseFormat`의 지원 여부는 모델마다 다를 수 있습니다. 공식 문서는 채팅 파운데이션 모델을 대상으로 한다고만 밝히며, 모델별 지원 범위는 명시하지 않습니다. 쓰려는 모델이 `json_schema` 같은 형식을 받는지 사용 전에 모델별로 직접 확인하십시오.

**권한**

- 정의자에게 엔드포인트에 대한 `CAN QUERY` 권한이 있어야 합니다.
- 커스텀 또는 외부 엔드포인트 호출에서 권한 오류가 나면, 워크스페이스 관리자가 Manage previews에서 기능을 끈 것일 수 있다고 문서가 안내합니다.
- 문서는 커스텀·외부 엔드포인트 쿼리가 지원 리전에서 기본으로 켜져 있다고 설명합니다.

### ai_extract: 스키마 기반 필드 추출

`ai_extract`는 텍스트나 문서에서 사용자가 정의한 스키마에 맞춰 구조화된 필드를 추출합니다.

**문법 (버전 2.1 기준, 문서가 권장)**

```
ai_extract(content, schema [, options])
```

- `content`는 `STRING` 또는 `VARIANT`입니다. `ai_parse_document`의 출력도 받을 수 있습니다.
- 공식 문서는 Databricks SQL과 Databricks Runtime에서 적용되며, Databricks SQL Classic에서는 사용할 수 없다고 명시합니다.
- 런타임 15.4 LTS 이상이 필요하고, 최적 성능을 위해 18.2 이상을 권장합니다.
- 상태 라벨은 페이지에 없습니다.

```sql
SELECT ai_extract(
  'Invoice #12345 from Acme Corp for $1,250.00 dated 2024-01-15',
  '["invoice_id", "vendor_name", "total_amount", "invoice_date"]',
  options => map('version', '2.1')
);
```

> **참고** 위 예시의 회사명은 문서 예시 문자열입니다. 실제 데이터에 넣을 때는 고객 정보가 포함되지 않도록 주의하십시오.

### ai_parse_document: 문서 구조 파싱

`ai_parse_document`는 PDF, 이미지, 오피스 문서를 텍스트, 표, 그림 설명을 포함한 구조화된 형태로 파싱합니다. 문서 처리 파이프라인의 첫 단계로 쓰이고, `ai_extract`와 연결됩니다.

**요구 사항 (문서 기준)**

| 항목 | 내용 |
|---|---|
| 적용 대상 | Databricks SQL, Databricks Runtime |
| 상태 라벨 | 페이지에 표시 없음 (라벨 없음) |
| 런타임 | Databricks Runtime 17.3 이상 |
| 서버리스 | 서버리스 컴퓨트에서는 환경 버전 3 이상, Python 또는 SQL 사용 |
| 지원 지역 | 문서는 특정 지역에서만 제공된다고 명시 (지역 목록은 페이지 참조) |
| 지원 형식 | PDF, JPG/JPEG, PNG, TIFF/TIF, DOC/DOCX, PPT/PPTX |
| 입력 | 바이너리 데이터. Spark `binaryFile` 리더의 바이너리 열 |
| 권한 | 페이지에 명시 없음. 이미지 영속화(image persistence)를 쓸 때는 대상 Unity Catalog 볼륨 권한을 확인하라고 안내 |

```sql
-- 볼륨의 파일을 binaryFile로 읽고 각 문서를 파싱한다
SELECT
  path,
  ai_parse_document(content)
FROM READ_FILES('/Volumes/<catalog>/<schema>/<volume>/', format => 'binaryFile');
```

> **주의** `/Volumes/<catalog>/<schema>/<volume>/`의 자리표시자는 실제 볼륨 경로로 바꿉니다. 문서의 예시는 `/Volumes/path/to/your/directory`입니다.

## 어떻게 쓰는가

문서 파이프라인의 일반적 흐름은 다음과 같습니다.

1. `READ_FILES`로 볼륨의 파일을 `binaryFile`로 읽습니다.
2. `ai_parse_document`로 문서를 파싱합니다.
3. `ai_extract`로 필요한 필드를 스키마에 맞춰 추출합니다.
4. 결과를 Delta 테이블로 저장하고, 필요하면 `ai_query`로 후처리합니다.

```sql
-- 파싱 결과를 테이블로 저장한 뒤, 필드를 추출하는 2단계 예시
CREATE OR REPLACE TABLE main.docs.parsed AS
SELECT path, ai_parse_document(content) AS parsed
FROM READ_FILES('/Volumes/<catalog>/<schema>/<volume>/', format => 'binaryFile');

SELECT
  path,
  ai_extract(
    parsed,
    '["invoice_id", "total_amount"]',
    options => map('version', '2.1')
  ) AS fields
FROM main.docs.parsed;
```

> **주의** `parsed` 열의 타입과 `ai_extract`가 받는 입력 형식은 실행 전 `DESCRIBE TABLE`로 확인하십시오. 이 페이지는 2단계 예시를 실행 검증하지 않았습니다.

## 트레이드오프

| 항목 | 고려할 점 |
|---|---|
| 웨어하우스 유형 | Classic 웨어하우스에서는 사용 불가. 웨어하우스 선택은 03장 |
| 런타임 버전 | `ai_parse_document`는 17.3 이상, 나머지는 15.4 LTS 이상. 버전에 따라 기능 범위가 다름 |
| 상태 라벨 | 함수마다 Beta 표기가 다름. Beta 함수는 운영 SLA와 변경 가능성을 따로 검토 |
| 비용 구조 | 문서 원문에서 함수별 단가를 확인하지 않음. 과금은 해당 함수의 과금 페이지를 따름 |
| 대안 | 정형 규칙으로 충분하면 SQL 파싱과 정규식이 더 싸고 예측 가능 |

## 주의사항

- **상태 라벨을 확인합니다.** `(Beta)` 함수를 핵심 파이프라인에 넣기 전 상세 문서와 릴리즈 노트를 확인합니다.
- **`ai_query`의 권한 오류는 엔드포인트 권한부터 봅니다.** `CAN QUERY`가 정의자에게 있는지, 관리자가 미리보기 기능을 껐는지 확인합니다.
- **배치 처리는 프로비저닝 처리량이 아닌 호스팅 모델을 씁니다.** 문서가 그렇게 권장합니다.
- **민감 데이터를 프롬프트에 넣기 전 거버넌스를 확인합니다.** 데이터가 모델 엔드포인트로 전달되므로, 허용 정책과 데이터 분류를 먼저 정합니다.
- **`ai_query` 응답 형식을 가정하지 않습니다.** `failOnError`를 `false`로 두면 오류가 행 단위 구조체에 담기므로, 후처리에서 오류 필드를 확인합니다.

## 참고 문서

- [AI Functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions)
- [ai_query 함수](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_query)
- [ai_extract 함수](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
- [ai_parse_document 함수](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document)
- [Data warehousing on Databricks](https://docs.databricks.com/aws/en/sql/)
