# 퀴즈와 체크리스트

> 기준일: 2026-10-29 · 근거: 이 장 본문 · 수준: 100~300

이 장에서 다룬 내용을 확인하는 문제입니다. 정답을 펼치면 해설과 근거 페이지로 가는 링크가 있습니다.

## 퀴즈

### 1. Databricks SQL에서 모든 쿼리가 실행되는 단위는 무엇입니까? (수준 100)

- A. 노트북 클러스터
- B. SQL 웨어하우스
- C. 잡의 SQL 태스크
- D. Unity Catalog 카탈로그

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 Databricks SQL의 실행 단위가 SQL 웨어하우스이며, 쿼리는 에디터·대시보드·알림·API 같은 인터페이스에서 웨어하우스로 전달된다고 설명합니다. 데이터 자체는 Unity Catalog가 관리하는 테이블에 있으므로 D는 실행 단위가 아닙니다. A와 C는 Databricks SQL의 실행 단위로 설명되지 않습니다.

근거: [Databricks SQL 개요 — 어떻게 동작하는가](what-is-databricks-sql.md#어떻게-동작하는가)

</details>

### 2. 팩트 테이블(Fact table)에 들어가는 내용으로 가장 적절한 것은 무엇입니까? (수준 100)

- A. 고객의 이름과 지역 같은 속성
- B. 상품의 카테고리 계층
- C. 판매 금액과 수량 같은 측정값과 차원 키
- D. 날짜의 연도·분기 이름

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 팩트 테이블은 발생한 사건을 행으로 기록하고, 금액이나 수량 같은 측정값을 가지며, 차원 키로 차원 테이블을 가리킵니다. A, B, D는 사실을 설명하는 맥락, 즉 차원 테이블에 들어가는 내용입니다.

근거: [데이터 모델링 기초 — 팩트와 차원](data-modeling-basics.md#팩트와-차원)

</details>

### 3. AI Functions가 해결하려는 문제로 가장 적절한 것은 무엇입니까? (수준 100)

- A. 모델 학습용 GPU 클러스터를 자동으로 확장한다
- B. 엔드포인트 클라이언트 코드 없이 SQL 함수 호출로 텍스트 처리나 문서 파싱을 데이터 옆에서 수행한다
- C. 테이블의 행 단위 잠금을 제거한다
- D. 대시보드의 시각화 색상을 자동으로 고른다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 LLM이나 문서 처리 모델을 쓰려면 엔드포인트 생성, 파이썬 요청, 응답 파싱 코드가 필요하지만, AI Functions는 이를 SQL 식 한 줄로 바꿔 데이터 옆에서 배치 처리하게 한다고 설명합니다. A, C, D는 본문에 없는 기능입니다.

근거: [AI Functions — 왜 필요한가](ai-functions.md#왜-필요한가)

</details>

### 4. 분석가가 다른 사용자의 쿼리 실행 기록을 보려면 최소한 무엇이 필요합니까? (수준 200)

- A. 해당 쿼리의 소유자로 등록되어 있어야 한다
- B. 워크스페이스 관리자 권한이 있어야 한다
- C. 해당 SQL 웨어하우스에 최소 CAN VIEW 권한이 있어야 한다
- D. 쿼리를 대시보드에 게시받아야 한다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 쿼리 소유자는 자신의 기록을 보고, 다른 사용자는 해당 SQL 웨어하우스에 최소 CAN VIEW 권한이 있으면 실행 기록을 볼 수 있다고 본문이 설명합니다. 다른 사람의 쿼리가 보이지 않을 때는 웨어하우스 권한부터 확인하라는 주의사항도 같은 맥락입니다.

근거: [SQL 에디터와 쿼리 기록 — 쿼리 기록](sql-editor-and-query-history.md#쿼리-기록)

</details>

### 5. 쿼리 프로필을 열었더니 "Query profile is not available" 메시지가 나왔습니다. 본문이 안내하는 우회 방법은 무엇입니까? (수준 200)

- A. 웨어하우스 크기를 두 단계 키운 뒤 다시 실행한다
- B. 프로필 JSON 파일을 가져와서 연다
- C. `LIMIT`을 바꾸거나 제거해 캐시를 우회한다
- D. 권한을 관리자 권한으로 올린 뒤 다시 실행한다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 이 메시지는 쿼리가 캐시에서 실행되어 프로필이 없을 때 나타나며, 본문은 `LIMIT`을 바꾸거나 제거하는 사소한 변경으로 캐시를 우회하라고 안내합니다. A와 D는 본문에 없는 조치이며, B는 가져온 프로필을 여는 방법이지 프로필을 새로 만드는 방법이 아닙니다.

근거: [쿼리 프로필 읽기 — 프로필 열기](query-profile.md#프로필-열기)

</details>

### 6. 새로 들어오는 데이터만 점진적으로 처리하는 객체와 결과 집합을 원천에 맞춰 갱신하는 객체를 구분한 설명으로 맞는 것은 무엇입니까? (수준 200)

- A. 구체화 뷰는 새 데이터만 증분 처리하고, 스트리밍 테이블은 결과 집합 전체를 맞춘다
- B. 스트리밍 테이블은 새로 들어온 데이터를 증분 처리하고, 구체화 뷰는 결과 집합을 원천에 맞춰 갱신한다
- C. 둘 다 일반 뷰와 같아서 조회할 때마다 원천을 다시 읽는다
- D. 둘 다 Databricks SQL 웨어하우스에서만 만들 수 있다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문 비교표는 구체화 뷰를 결과 집합을 원천에 맞춰 갱신하는 객체로, 스트리밍 테이블을 새로 들어온 데이터를 증분 처리하는 객체로 설명합니다. C는 구체화하지 않는 뷰에 대한 설명입니다. D는 본문이 독립형 객체를 서버리스 범용 컴퓨트 노트북에서도 만들 수 있다고 설명하므로 틀린 설명입니다.

근거: [구체화 뷰와 스트리밍 테이블 — 비교](materialized-views-and-streaming-tables.md#구체화-뷰와-스트리밍-테이블-비교)

</details>

### 7. 같은 고객의 가장 최근 주문 한 건만 남기는 쿼리로 가장 적절한 것은 무엇입니까? (수준 200)

- A. `QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_ts DESC) = 1`을 쓴다
- B. `QUALIFY MAX(order_ts) = 1`처럼 QUALIFY 안에 집계 함수를 직접 쓴다
- C. `PIVOT`으로 고객별 주문을 열로 펼친다
- D. `UNPIVOT`으로 주문 열을 행으로 되돌린다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: A** — `QUALIFY`는 윈도 함수 결과로 행을 거르는 절이며, 본문은 `ROW_NUMBER()`를 파티션 기준으로 써서 최신 행 한 건만 남기는 패턴을 예로 듭니다. B는 집계 함수를 `QUALIFY` 안에 쓸 수 없다는 본문 설명과 어긋납니다. C와 D는 행과 열을 바꾸는 기능으로, 중복 제거와 무관합니다.

근거: [SQL 언어 기능 — QUALIFY 절](sql-language-features.md#2-qualify-절)

</details>

### 8. 인사이트 `EXCESSIVE_QUEUE_TIME`이 나왔습니다. 본문이 제시하는 권장 조치는 무엇입니까? (수준 300)

- A. 쿼리 문장을 먼저 다시 쓴다
- B. 웨어하우스의 최대 클러스터 수를 늘린다
- C. 웨어하우스 크기를 키워 디스크 spill을 줄인다
- D. 결과 캐시를 끈다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — `EXCESSIVE_QUEUE_TIME`은 쿼리 자체가 아니라 웨어하우스 큐에서 대기하는 문제이며, 권장 조치는 최대 클러스터 수 증가입니다. C는 메모리에 맞지 않아 디스크로 spill하는 `DATA_SPILL`의 조치입니다. 본문은 두 문제를 같은 문제로 보지 말라고 주의합니다.

근거: [쿼리 성능 최적화 — 쿼리 큐잉과 웨어하우스 부하](query-performance.md#쿼리-큐잉과-웨어하우스-부하)

</details>

### 9. 예측 I/O(Predictive I/O)의 업데이트 가속을 쓰려고 테이블의 삭제 벡터를 켰습니다. 본문이 강조하는 주의사항은 무엇입니까? (수준 300)

- A. 삭제 벡터를 켜도 테이블 프로토콜 버전은 바뀌지 않는다
- B. 삭제 벡터를 켜면 테이블 프로토콜 버전이 올라가 지원하지 않는 Delta 클라이언트가 테이블을 읽지 못할 수 있다
- C. 예측 I/O는 삭제 벡터 없이도 업데이트를 가속하므로 설정이 필요 없다
- D. 삭제 벡터는 읽기 가속에만 영향을 준다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 삭제 벡터를 켜면 테이블 프로토콜 버전이 올라가고, 삭제 벡터를 지원하지 않는 Delta 클라이언트는 테이블을 읽지 못할 수 있다고 경고합니다. 업데이트 가속에는 삭제 벡터가 켜져 있어야 한다는 것도 본문 설명입니다. C와 D는 본문과 어긋납니다.

근거: [쿼리 성능 최적화 — 예측 I/O](query-performance.md#예측-io-predictive-io)

</details>

### 10. 호출자에게 원본 테이블의 권한을 주지 않고, 저장 프로시저로 특정 집계 결과만 제공하려면 어떤 설정이 맞습니까? (수준 300)

- A. `SQL SECURITY INVOKER`로 만들고 호출자에게 원본 테이블 권한을 준다
- B. `SQL SECURITY DEFINER`로 만들고 본문에 허용할 작업만 넣는다
- C. 매개변수로 테이블 이름을 문자열로 받아 동적으로 조회한다
- D. 노트북의 스크립트 블록을 사용자에게 공유한다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — `DEFINER`는 프로시저 소유자의 권한으로 본문을 실행하므로, 호출자에게 원본 테이블 권한 없이 허용된 집계만 노출할 수 있습니다. 본문은 이때 본문에 허용할 작업만 넣으라고 설명합니다. A는 호출자 권한으로 실행하므로 원본 권한이 필요합니다. C는 외부 입력을 SQL 구조에 섞는 방식으로 본문이 피하라고 한 패턴입니다. D는 저장 프로시저의 권한 통제 장점을 버리는 방식입니다.

근거: [SQL 스크립팅과 저장 프로시저 — 예 3: 실행 권한을 정하는 방법](scripting-and-procedures.md#예-3-실행-권한을-정하는-방법)

</details>

## 실무 체크리스트

이 장의 내용을 실제 환경에 적용할 때 확인할 항목입니다.

- [ ] 웨어하우스를 API나 IaC로 만들 때 유형을 명시했다. UI 기본값과 API 기본값이 다를 수 있다 — [Databricks SQL 개요](what-is-databricks-sql.md#sql-웨어하우스-유형)
- [ ] 테이블을 `catalog.schema.table` 3단계 이름으로 적었다 — [Databricks SQL 개요](what-is-databricks-sql.md#unity-catalog와-delta-lake의-역할)
- [ ] 다른 사용자의 쿼리가 보이지 않을 때 웨어하우스 권한부터 확인했다 — [SQL 에디터와 쿼리 기록](sql-editor-and-query-history.md#쿼리-기록)
- [ ] 쿼리 프로필을 wall-clock 시간, Top operators, Time spent, 프루닝 비율, Performance insights 순서로 읽었다 — [쿼리 프로필 읽기](query-profile.md#읽는-순서)
- [ ] 인사이트의 권장 조치를 적용한 뒤 같은 조건에서 프로필을 다시 비교했다 — [쿼리 성능 최적화](query-performance.md#점검-순서)
- [ ] 통계 수집 명령과 예측 최적화 설정을 인사이트에 맞춰 확인했다 — [쿼리 성능 최적화](query-performance.md#통계-수집-analyze-table)
- [ ] 디스크 spill과 큐 대기를 서로 다른 조치로 처리했다 — [쿼리 성능 최적화](query-performance.md#쿼리-큐잉과-웨어하우스-부하)
- [ ] 저장 프로시저의 `SQL SECURITY`를 명시적으로 골랐고, 소유자 변경 절차를 정했다 — [SQL 스크립팅과 저장 프로시저](scripting-and-procedures.md#저장-프로시저)
- [ ] 값은 파라미터 마커로 전달하고 문자열 연결로 SQL을 만들지 않았다 — [SQL 언어 기능](sql-language-features.md#4-파라미터-마커)

## 참고 문서

이 페이지는 이 장 본문을 근거로 합니다. 공식 문서 링크는 각 본문 페이지의 참고 문서를 보세요.

- [Databricks SQL 개요](what-is-databricks-sql.md)
- [SQL 에디터와 쿼리 기록](sql-editor-and-query-history.md)
- [쿼리 프로필 읽기](query-profile.md)
- [SQL 언어 기능](sql-language-features.md)
- [SQL 스크립팅과 저장 프로시저](scripting-and-procedures.md)
- [AI Functions](ai-functions.md)
- [구체화 뷰와 스트리밍 테이블](materialized-views-and-streaming-tables.md)
- [쿼리 성능 최적화](query-performance.md)
- [데이터 모델링 기초](data-modeling-basics.md)
