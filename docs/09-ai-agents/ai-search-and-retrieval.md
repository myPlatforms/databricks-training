# AI Search와 검색 기반 에이전트

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 왜 필요한가

에이전트가 사내 문서나 대량의 텍스트를 다루려면 질문과 관련된 조각을 찾아 프롬프트에 넣어야 합니다. 모델의 학습 데이터에는 회사 문서가 없고, 프롬프트에 전부 넣기에는 문서가 너무 큽니다. 검색 기반 생성(RAG, Retrieval-Augmented Generation)은 이 문제를 검색 단계로 해결합니다.

키워드 검색만으로는 "계약 해지 조건"과 "해지 시 위약금"처럼 표현이 다른 질문을 놓치기 쉽습니다. 반대로 임베딩(벡터) 유사도만 쓰면 제품 코드나 고유명사처럼 정확한 단어가 중요한 질의에 약합니다. Databricks AI Search는 벡터 검색과 키워드 검색을 같은 인덱스에서 다룰 수 있게 합니다.

> **참고** 제품 명칭은 문서 표기에 따라 **AI Search** 입니다. 문서 페이지에는 "Databricks AI Search, formerly Databricks Vector Search"라고 적혀 있습니다. 이 장에서는 AI Search를 쓰고, 구 명칭 Vector Search는 처음 한 번만 병기합니다. 과거 자료의 `vector_search` 이름은 공식 문서의 SQL 함수 이름이므로 그대로 씁니다.

## 어떻게 동작하는가

AI Search 인덱스는 **엔드포인트**(인덱스를 담는 서버 자원)와 **인덱스**(검색 대상 테이블을 가리키는 객체)로 나뉩니다. 인덱스는 Unity Catalog에 3단계 이름으로 등록됩니다.

인덱스는 임베딩을 누가 계산하는지와 소스가 자동으로 동기화되는지에 따라 네 가지 유형으로 나뉩니다.

| 인덱스 유형 | 임베딩 계산 | 동기화 | 설명 |
|---|---|---|---|
| Delta Sync, Databricks 계산 임베딩 | Databricks가 선택한 모델로 계산 | 소스와 자동 동기화 | 텍스트 컬럼을 지정하면 임베딩을 만들고, 선택 시 UC 테이블에 저장 |
| Delta Sync, 자체 임베딩 | 소스 테이블에 이미 있음 | 소스와 자동 동기화 | 임베딩 벡터 컬럼을 지정. 나중에 관리형 임베딩으로 바꿀 수 없음 (새 인덱스 필요) |
| Direct Vector Access | 사용자가 계산 | 수동 (REST API로 갱신) | 임베딩 테이블이 바뀔 때 API로 직접 갱신. 소스 유형 목록은 문서에 없음 |
| 전체 텍스트 검색 인덱스 (Beta) | 없음 | 트리거 방식 | 임베딩 컬럼 없는 Delta Sync 인덱스. BM25 키워드 검색. 스토리지 최적화 엔드포인트 필요 |

인덱스 유형 중 Delta Sync 두 가지가 가장 많이 쓰입니다. 소스 테이블이 바뀌면 인덱스가 따라 갱신되기 때문입니다.

### 소스 테이블 조건

Delta Sync 인덱스의 소스로 쓸 수 있는 객체는 다음과 같습니다.

| 소스 유형 | 조건 |
|---|---|
| Delta Lake 테이블 | 표준 엔드포인트는 변경 데이터 피드(Change Data Feed)가 켜져 있어야 함. 행 추적(Row tracking)이 켜진 테이블은 자동으로 사용 |
| 스트리밍 테이블(Streaming Table) | 문서 목록에 포함 |
| 구체화된 뷰(Materialized View) | 외부 메타데이터(Smart Clone)를 먼저 켜야 함 |
| 관리형 Iceberg 테이블 | Iceberg v3 이상 |

> **참고** 스트리밍 테이블, 구체화된 뷰, 관리형 Iceberg 테이블은 공식 AI Search 페이지의 소스 목록에 있는 항목입니다. 구체화된 뷰는 외부 메타데이터 설정이, Iceberg 테이블은 v3 이상이 조건입니다. 이 목록은 문서가 바뀌면 달라질 수 있으므로 적용 전에 확인하십시오.

## 어떻게 쓰는가

### 1. 엔드포인트 만들기

```python
from databricks.ai_search.client import AISearchClient

client = AISearchClient()
client.create_endpoint(
    name="vector_search_endpoint_name",
    endpoint_type="STANDARD" # or "STORAGE_OPTIMIZED"
)
```

엔드포인트 유형은 `STANDARD`와 `STORAGE_OPTIMIZED` 두 가지입니다. 전체 텍스트 검색 인덱스는 스토리지 최적화 엔드포인트가 필요합니다.

### 2. 관리형 임베딩 Delta Sync 인덱스

Databricks가 텍스트 컬럼에서 임베딩을 계산합니다.

```python
client = AISearchClient()
index = client.create_delta_sync_index(
    endpoint_name="vector_search_demo_endpoint",
    source_table_name="vector_search_demo.vector_search.en_wiki",
    index_name="vector_search_demo.vector_search.en_wiki_index",
    pipeline_type="TRIGGERED",
    primary_key="id",
    embedding_source_column="text",
    embedding_model_endpoint_name="databricks-qwen3-embedding-0-6b", # Used for ingestion, and also for querying unless model_endpoint_name_for_query is specified.
    model_endpoint_name_for_query="qwen3-embedding-low-latency"      # Optional. A separate endpoint serving the same model, used only for querying.
)
```

`model_endpoint_name_for_query`를 지정하면 질의용 엔드포인트를 따로 쓸 수 있습니다. 문서는 같은 모델을 서빙하는 별도 엔드포인트라고 설명합니다. 지정하지 않으면 적재와 질의에 같은 `embedding_model_endpoint_name`을 씁니다.

### 3. 자체 임베딩 Delta Sync 인덱스

소스 테이블에 벡터 컬럼이 이미 있을 때 씁니다.

```python
client = AISearchClient()
index = client.create_delta_sync_index(
    endpoint_name="vector_search_demo_endpoint",
    source_table_name="vector_search_demo.vector_search.en_wiki",
    index_name="vector_search_demo.vector_search.en_wiki_index",
    pipeline_type="TRIGGERED",
    primary_key="id",
    embedding_dimension=1024,
    embedding_vector_column="text_vector"
)
```

### 4. 파라미터 정리

| 파라미터 | 의미 | 쓰는 경우 |
|---|---|---|
| `endpoint_name` | 인덱스를 담을 엔드포인트 | 항상 |
| `source_table_name` | 소스 테이블 (`catalog.schema.table`) | 항상 |
| `index_name` | 인덱스 이름 (3단계) | 항상 |
| `pipeline_type` | 동기화 모드 (`TRIGGERED` 등) | 항상 |
| `primary_key` | 기본 키 컬럼 | 항상 |
| `embedding_source_column` | 임베딩을 계산할 텍스트 컬럼 | 관리형 임베딩 |
| `embedding_model_endpoint_name` | 임베딩 모델 서빙 엔드포인트 | 관리형 임베딩 |
| `model_endpoint_name_for_query` | 질의 전용 엔드포인트 | 선택 사항 |
| `embedding_dimension` | 미리 계산된 벡터의 차원 | 자체 임베딩 |
| `embedding_vector_column` | 벡터가 있는 컬럼 | 자체 임베딩 |

### 5. 동기화 모드

| 모드 | 동작 | 비고 |
|---|---|---|
| Continuous | 소스 변경을 몇 초 안에 반영 | UI에서 설정. 비용 높음 |
| Triggered | UI, SDK, REST API에서 동기화 시작 (`index.sync()`) | 스토리지 최적화 엔드포인트는 이 모드만 지원 |

### 6. 질의

검색은 Python SDK, REST API, SQL 함수 `vector_search()`로 합니다. 문서는 SQL 함수의 문법을 보여 주지 않고 함수 레퍼런스를 참고하라고 안내하므로, 이 페이지에서는 SDK 예시만 씁니다.

```python
results = index.similarity_search(
    query_text="Greek myths",
    columns=["id", "field2"],
    num_results=2,
    query_type="hybrid"
)
```

검색 방식은 `query_type`으로 고릅니다.

| `query_type` | 방식 | 설명 |
|---|---|---|
| `ANN` (기본값) | 벡터 유사도 | 개념적인 질의에 적합 |
| `hybrid` | 키워드와 유사도 결합 | 문서가 대부분의 경우 시작점으로 권장 |
| `FULL_TEXT` (Beta) | 키워드만 (임베딩 없음) | 최대 10,000건 결과 |
| 리랭커(Reranker) | 1차 결과를 다시 점수화 | 선택 사항. 지연 시간이 늘어나는 대신 정밀도 향상 |

주요 질의 인자는 다음과 같습니다.

| 인자 | 설명 |
|---|---|
| `query_text` | 검색 텍스트. 미리 계산된 벡터가 있으면 `query_vector` 사용 |
| `columns` | 반환할 컬럼 |
| `num_results` | 결과 수. 1,000을 넘으면 SDK가 자동으로 페이지를 나눔 |
| `filters` | 표준 엔드포인트는 딕셔너리(예: `{"title": ["Ares", "Athena"]}`), 스토리지 최적화 엔드포인트는 SQL 유사 문자열(예: `'title IN ("Ares", "Athena")'`) |

리랭커가 실패하면 응답의 디버그 정보에 `RERANKER_TEMPORARILY_UNAVAILABLE` 경고 코드가 들어가고, 결과는 리랭킹 없이 돌아옵니다. 이때는 나중에 다시 호출하면 리랭킹 결과를 받을 수 있습니다.

### 7. 에이전트에 붙이기

에이전트가 인덱스를 직접 SDK로 호출할 수도 있고, 워크스페이스 MCP 엔드포인트(Public Preview)를 도구로 붙일 수도 있습니다. MCP 경로는 `https://<workspace-hostname>/api/2.0/mcp/ai-search/{catalog}/{schema}/{index_name}`이며 OAuth 범위는 `ai-search`입니다. 자세한 등록과 인증은 [도구: UC 함수와 MCP 서버](tools-uc-functions-and-mcp.md)에서 다룹니다.

## 트레이드오프

| 질문 | 판단 기준 |
|---|---|
| 관리형 임베딩인가 자체 임베딩인가 | 임베딩 모델을 Databricks에 맡기면 파이프라인이 단순. 이미 벡터를 관리하고 있다면 자체 임베딩. 자체 임베딩 인덱스를 관리형으로 바꾸려면 새 인덱스가 필요하다고 문서가 명시 |
| Continuous인가 Triggered인가 | 몇 초 안의 반영이 필요하면 Continuous. 비용을 줄이고 주기적으로 갱신하면 Triggered |
| 표준인가 스토리지 최적화인가 | 스토리지 최적화는 Triggered만 지원. 임베딩 차원이 16으로 나누어 떨어져야 함 |
| 벡터만인가 하이브리드인가 | 정확한 식별자나 고유명사가 많으면 `hybrid`. 개념 질의 중심이면 `ANN` |

## 주의사항

- **소스 테이블 권한**: 인덱스를 만들려면 인덱스가 놓일 스키마에 `CREATE TABLE` 권한이 필요합니다. 서버리스 컴퓨트가 켜져 있어야 합니다.
- **변경 데이터 피드**: 표준 엔드포인트에서 Delta 소스는 변경 데이터 피드가 필요합니다. 행 추적이 켜져 있으면 자동입니다. 소스를 만든 뒤 설정을 빠뜨리기 쉽습니다.
- **구체화된 뷰 소스**: 외부 메타데이터(Smart Clone)를 먼저 켜야 합니다.
- **예약된 컬럼 이름**: `_id`는 예약 이름이라 쓸 수 없습니다.
- **인덱스 이름 규칙**: 공백, 마침표, 슬래시, 제어 문자를 쓸 수 없습니다.
- **임베딩 엔드포인트 설정**: 대규모 데이터에는 GPU 엔드포인트를 쓰고, CPU 엔드포인트는 소규모 데이터와 테스트에만 씁니다. 임베딩 엔드포인트의 기본 "Scale to zero" 선택은 해제하십시오. 그대로 두면 첫 질의가 시간 초과될 수 있다고 문서가 설명합니다.
- **QPS 조정 상태**: 엔드포인트의 목표 QPS를 바꾸면 응답 상태가 `SCALING_CHANGE_IN_PROGRESS`에서 `SCALING_CHANGE_APPLIED`로 바뀝니다. 적용이 끝나기 전에 부하 테스트 결과를 해석하지 마십시오.
- **전체 텍스트 검색의 Beta 상태**: 전체 텍스트 인덱스와 `FULL_TEXT` 질의는 Beta입니다. 운영 적용 전에 상태를 확인하십시오.
- **청킹 설계**: 문서 분할 방식과 청크 크기는 공식 AI Search 페이지에서 권장값을 찾지 못했습니다. 이 장은 그 부분을 특정 수치로 제시하지 않습니다. 소스 테이블을 설계할 때 청크 단위와 메타데이터(출처, 문서 ID, 날짜)를 함께 두는 편이 나중에 필터링과 출처 표시에 유리합니다. 이는 설계 판단이며 문서 권장 사항이 아닙니다.

## 참고 문서

- [Databricks AI Search](https://docs.databricks.com/aws/en/ai-search/ai-search)
- [Create AI Search endpoints and indexes](https://docs.databricks.com/aws/en/ai-search/create-ai-search)
- [Query an AI Search index](https://docs.databricks.com/aws/en/ai-search/query-ai-search)
- [Use AI Search as an MCP tool](https://docs.databricks.com/aws/en/agents/mcp-tools/built-in-mcp-services)
- [Change data feed](https://docs.databricks.com/aws/en/tables/features/change-data-feed)
- [Iceberg v3](https://docs.databricks.com/aws/en/iceberg/iceberg-v3)
