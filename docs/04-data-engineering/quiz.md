# 퀴즈와 체크리스트

> 기준일: 2026-10-29 · 근거: 이 장 본문 · 수준: 100~300

이 장에서 다룬 내용을 확인하는 문제입니다. 정답을 펼치면 해설과 근거 페이지로 가는 링크가 있습니다.

## 퀴즈

### 1. 원천이 SaaS 애플리케이션일 때 수집의 시작점은 무엇입니까? (수준 100)

- A. 노트북에서 SaaS API를 직접 호출하는 코드를 작성한다
- B. Lakeflow Connect 관리형 커넥터가 원천 목록에 있는지 먼저 확인한다
- C. Kafka용 Structured Streaming 소스를 사용한다
- D. 사람이 파일 업로드 화면으로 데이터를 내려받아 올린다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 공식 선택 절차는 가장 관리된 계층부터 확인하라고 권장하며, SaaS와 데이터베이스는 관리형 커넥터를 먼저 봅니다. A는 인증, 증분 읽기, 스키마 변경, 재시도를 직접 떠안게 하므로 맞지 않습니다. C는 메시지 버스 원천용이고, D는 사람이 직접 올리는 파일용입니다.

근거: [수집 방법 선택 기준 — 선택 절차](choose-ingestion-method.md#선택-절차)

</details>

### 2. 관리형 커넥터가 플랫폼 쪽에서 처리한다고 설명되는 항목은 무엇입니까? (수준 100)

- A. 대상 BI 대시보드의 레이아웃 설계
- B. 인증, 증분 읽기, 스키마 변경, 재시도
- C. 원천 시스템의 데이터 모델 정의
- D. 비즈니스 KPI 정의

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — Lakeflow Connect 문서는 커넥터가 원천별 인증, 증분 읽기, 스키마 변경, 자동 재시도를 처리한다고 설명합니다. 사용자는 연결과 수집 파이프라인 설정에 집중합니다. A, C, D는 수집 도구의 범위 밖에 있는 일이므로 사용자가 직접 정해야 합니다.

근거: [Lakeflow Connect — 왜 필요한가](lakeflow-connect.md#왜-필요한가)

</details>

### 3. 클라우드 스토리지에 계속 쌓이는 파일 중 새로 도착한 파일만 증분으로 읽는 소스는 무엇입니까? (수준 100)

- A. Auto Loader (`cloudFiles` 소스)
- B. Zerobus Ingest API
- C. Lakehouse Federation
- D. OpenSharing

<details markdown="1">
<summary>정답과 해설</summary>

**정답: A** — Auto Loader는 처리한 파일의 메타데이터를 체크포인트에 기록해 새 파일만 증분으로 처리하고, 정확히 한 번 처리와 장애 후 복구를 지원한다고 설명됩니다. B는 애플리케이션이 스트리밍 테이블에 직접 쓰는 경로, C는 데이터를 옮기지 않고 질의하는 도구, D는 데이터 공유 방식이므로 파일 증분 읽기와 다릅니다.

근거: [Auto Loader — 한눈에 보기](auto-loader.md#한눈에-보기)

</details>

### 4. 문서가 대부분의 워크로드에 권장하는 Auto Loader 파일 감지 방식은 무엇입니까? (수준 200)

- A. 디렉터리 목록(directory listing) 모드
- B. 파일 이벤트(file notification) 모드
- C. 사용자가 매 실행마다 파일 경로를 수동으로 나열하는 방식
- D. 체크포인트 없이 입력 디렉터리를 스캔하는 방식

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 문서는 대부분의 워크로드에 파일 이벤트 모드를 권장합니다. 디렉터리 목록 모드는 기본 설정이지만 권장 방식은 아닙니다. 문서는 디렉터리 목록 모드에서 상시 트리거를 쓰면 비용이 많이 든다고 설명합니다. D는 Auto Loader가 체크포인트에 파일 메타데이터를 저장한다는 본문과 맞지 않습니다.

근거: [Auto Loader — 파일 감지 모드](auto-loader.md#파일-감지-모드)

</details>

### 5. 스키마를 직접 지정하지 않았을 때 Auto Loader의 `cloudFiles.schemaEvolutionMode` 기본값은 무엇입니까? (수준 200)

- A. `none`
- B. `rescue`
- C. `addNewColumns`
- D. `failOnNewColumns`

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 스키마를 직접 제공하지 않으면 기본값은 `addNewColumns`입니다. 새 컬럼이 나오면 스트림이 실패하고, 재시작하면 갱신된 스키마가 적용됩니다. `none`은 스키마를 제공했을 때의 기본값입니다. `rescue`는 실패하지 않고 새 컬럼을 rescued data에 보존하며, `failOnNewColumns`는 자동 갱신 없이 실패 상태를 유지합니다.

근거: [Auto Loader — 스키마 추론과 진화](auto-loader.md#스키마-추론과-진화)

</details>

### 6. Lakeflow 파이프라인 expectation을 `EXPECT (...)`만 쓰고 `ON VIOLATION` 절을 생략하면 위반 레코드는 어떻게 됩니까? (수준 200)

- A. 대상 테이블에 쓰기 전에 제외된다
- B. 위반 시점에 업데이트 전체가 실패한다
- C. 대상 테이블에 그대로 남는다
- D. 대상 테이블이 삭제된 뒤 다시 만들어진다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 문서는 expectation의 기본 동작이 위반 레코드를 유지하는 것(warn)이라고 명시합니다. 제외하려면 `ON VIOLATION DROP ROW`를, 업데이트를 멈추려면 `ON VIOLATION FAIL UPDATE`를 명시해야 합니다. A는 drop 동작, B는 fail 동작에 해당합니다. D는 본문에 없는 동작입니다.

근거: [Expectations와 AUTO CDC — 세 가지 동작](pipelines-expectations-and-cdc.md#세-가지-동작)

</details>

### 7. 차원 테이블(예: 고객 마스터)이 나중에 바뀌어도 조인 결과가 항상 맞아야 하는 집계를 Lakeflow 파이프라인으로 만들려면 무엇을 고릅니까? (수준 300)

- A. 스트리밍 테이블로 정의하고 새로 들어온 원천 행만 추가 처리한다
- B. 구체화된 뷰(materialized view)로 정의한다
- C. 스트리밍 테이블에 워터마크 값만 크게 설정한다
- D. Auto Loader 파일 이벤트 모드로 차원 파일을 읽는다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 문서는 구체화된 뷰가 차원이 바뀌면 조인을 자동으로 다시 계산하므로 항상 맞다고 설명합니다. 스트리밍 테이블은 원천 행을 한 번만 처리하므로 차원 변경을 과거 결과에 반영하지 않습니다. 워터마크는 상태 보관 기간을 정하는 장치이지 차원 변경을 반영하는 장치가 아닙니다. D는 파일 감지 방식이므로 조인 재계산과 관계가 없습니다.

근거: [스트리밍 테이블과 구체화된 뷰 — 선택 기준](pipelines-streaming-tables-and-mvs.md#선택-기준-스트리밍-테이블-대-구체화된-뷰)

</details>

### 8. 실패 시 정리(cleanup) 태스크를 상위 태스크의 결과와 관계없이 실행하려면 Run if 옵션으로 무엇을 고릅니까? (수준 200)

- A. All succeeded (기본값)
- B. At least one succeeded
- C. All done
- D. All failed

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — All done은 결과와 관계없이 모든 의존 태스크가 끝나면 실행되며, 정리 태스크에 적합하다고 설명됩니다. A는 상위 태스크가 실패하면 Upstream failed가 되어 실행되지 않습니다. B와 D도 특정 결과를 조건으로 하므로, 결과와 관계없이 실행되어야 하는 정리 태스크에는 맞지 않습니다.

근거: [파라미터·태스크 값·조건 분기 — Run if](jobs-parameters-and-control-flow.md#run-if-실행-조건), [재시도·알림·Repair run — 실패 정리 태스크 연결](jobs-retries-notifications-repair.md#실패-정리-태스크-연결)

</details>

### 9. Lakeflow Jobs에서 마지막 태스크 하나가 실패한 실행을 Repair run으로 복구하면 어떤 태스크가 다시 실행됩니까? (수준 300)

- A. 성공한 태스크를 포함해 잡 전체를 처음부터 다시 실행한다
- B. 실패했거나 미성공인 태스크와 그에 의존하는 태스크만 다시 실행한다
- C. 실패한 태스크만 실행하고 그 하위 태스크는 건너뛴다
- D. 복구 전에 바꾼 설정은 무시하고 최초 실행의 설정으로만 다시 실행한다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 성공한 태스크는 다시 실행되지 않고, 미성공 태스크와 그에 의존하는 태스크가 다시 실행됩니다. 미성공 태스크는 현재 잡과 태스크 설정으로 처음부터 실행되므로 D도 틀립니다. 태스크가 멱등하지 않으면 실패 전에 쓴 부분 결과가 중복될 수 있다는 점도 함께 확인해야 합니다.

근거: [재시도·알림·Repair run — Repair run](jobs-retries-notifications-repair.md#repair-run)

</details>

### 10. 스트리밍 집계 쿼리의 집계 키를 바꾸었습니다. 가장 안전한 대응은 무엇입니까? (수준 300)

- A. 기존 체크포인트를 그대로 두고 재시작한다
- B. 체크포인트 파일 일부를 지워 상태만 초기화하고 재시작한다
- C. 새 체크포인트 위치로 시작하는 것을 검토한다
- D. 워터마크 시간을 늘려 기존 체크포인트와의 호환성을 확보한다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 문서는 스트리밍 집계의 키나 집계 변경이 상태 저장 연산자에서 허용되지 않으며, 재시작 후 예측할 수 없이 실패할 수 있다고 설명합니다. 이런 변경에는 새 체크포인트가 필요합니다. A는 허용되지 않는 변경이므로 맞지 않습니다. B는 체크포인트를 지우면 처음부터 다시 시작한다는 본문과 맞지 않는 방식입니다. D는 워터마크로 체크포인트 호환성을 바꿀 수 없습니다.

근거: [Structured Streaming 기초 — 체크포인트](structured-streaming-basics.md#체크포인트)

</details>

## 실무 체크리스트

이 장의 내용을 실제 환경에 적용할 때 확인할 항목입니다.

- [ ] 원천 유형을 파일, SaaS, 데이터베이스, 메시지 버스로 나누고 관리형 커넥터 목록을 먼저 확인했다 — [수집 방법 선택 기준](choose-ingestion-method.md#선택-절차)
- [ ] 커넥터의 상태 라벨(GA, Public Preview, Beta)을 커넥터 페이지나 릴리즈 노트에서 확인했다 — [Lakeflow Connect](lakeflow-connect.md#상태-라벨-ga--public-preview--beta)
- [ ] 관리형 커넥터 사용량을 `system.billing.usage`에서 `LAKEFLOW_CONNECT`로 따로 집계하도록 설정했다 — [Lakeflow Connect](lakeflow-connect.md#과금-구조)
- [ ] Auto Loader 파일 감지 모드를 파일 수와 실행 주기에 맞춰 골랐다 — [Auto Loader](auto-loader.md#파일-감지-모드)
- [ ] 스키마 진화 모드를 자동 반영 후 재시작할지, 보존만 할지 운영 기준으로 정했다 — [Auto Loader](auto-loader.md#스키마-추론과-진화)
- [ ] 모든 expectation에 `ON VIOLATION` 동작을 명시했다 — [Expectations와 AUTO CDC](pipelines-expectations-and-cdc.md#세-가지-동작)
- [ ] 이벤트 로그를 뷰로 노출하고, 최근 업데이트의 FAILED·CANCELLED 흐름을 확인하는 순서를 정했다 — [파이프라인 이벤트 로그](pipelines-event-log.md#운영-확인-순서)
- [ ] 재시도나 Repair run 대상 태스크가 멱등한지 확인했다 — [재시도·알림·Repair run](jobs-retries-notifications-repair.md#repair-run)
- [ ] 정리 태스크의 Run if를 All done으로 설정했다 — [파라미터·태스크 값·조건 분기](jobs-parameters-and-control-flow.md#run-if-실행-조건)
- [ ] 쿼리 변경 전에 체크포인트가 필요한 변경인지 확인했다 — [Structured Streaming 기초](structured-streaming-basics.md#체크포인트)

## 참고 문서

이 페이지는 이 장 본문을 근거로 합니다. 공식 문서 링크는 각 본문 페이지의 참고 문서를 보세요.

- [수집 방법 선택 기준](choose-ingestion-method.md)
- [Lakeflow Connect](lakeflow-connect.md)
- [Auto Loader](auto-loader.md)
- [스트리밍 테이블과 구체화된 뷰](pipelines-streaming-tables-and-mvs.md)
- [Expectations와 AUTO CDC](pipelines-expectations-and-cdc.md)
- [파이프라인 이벤트 로그](pipelines-event-log.md)
- [Lakeflow Jobs 태스크와 트리거](jobs-tasks-and-triggers.md)
- [파라미터·태스크 값·조건 분기](jobs-parameters-and-control-flow.md)
- [재시도·알림·Repair run](jobs-retries-notifications-repair.md)
- [Structured Streaming 기초](structured-streaming-basics.md)
