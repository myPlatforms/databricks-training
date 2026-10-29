# 퀴즈와 체크리스트

> 기준일: 2026-10-29 · 근거: 이 장 본문 · 수준: 100~300

이 장에서 다룬 내용을 확인하는 문제입니다. 정답을 펼치면 해설과 근거 페이지로 가는 링크가 있습니다.

## 퀴즈

### 1. 레이크하우스가 목표로 하는 구조로 가장 알맞은 것은? (수준 100)

- A. 데이터를 모두 독점 포맷의 웨어하우스로 옮긴다
- B. 저렴한 오브젝트 스토리지의 열린 파일 위에 트랜잭션, 스키마, 관리 계층을 얹는다
- C. 데이터 레이크를 버리고 파일 복사본을 늘린다
- D. 머신러닝 전용 저장소를 따로 만든다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 레이크하우스는 열린 파일 포맷을 그대로 두고, 그 위에 트랜잭션 로그, 스키마 검증, 버전 이력, 권한 모델 같은 테이블 계층을 얹는 구조입니다. A는 웨어하우스의 독점 포맷 문제를 그대로 가져오는 설계이고, C와 D는 본문이 해결책으로 든 방향과 반대입니다.

근거: [레이크하우스가 필요한 이유 — 레이크하우스가 해결하는 것](why-lakehouse.md#레이크하우스가-해결하는-것)

</details>

### 2. Parquet 파일만 쌓아 둔 데이터 레이크에서 쓰기 도중 작업이 실패하면 어떤 문제가 생기는가? (수준 100)

- A. 자동으로 직전 버전으로 복원된다
- B. 일부 파일만 남아 읽는 쪽이 중간 상태를 볼 수 있다
- C. 컬럼 구조가 자동으로 맞춰진다
- D. 행 하나를 삭제하는 작업이 즉시 끝난다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 트랜잭션이 없는 데이터 레이크에서는 파일 일부만 남아 테이블이 깨진 상태로 읽힐 수 있습니다. 본문은 이것을 트랜잭션 부재의 대표 문제로 듭니다. A와 C는 트랜잭션 계층이 있을 때의 동작이고, D는 행 수정이 파일 재작성 비용을 치른다는 본문 설명과 어긋납니다.

근거: [레이크하우스가 필요한 이유 — 데이터 레이크의 한계](why-lakehouse.md#데이터-레이크의-한계)

</details>

### 3. 메달리온 아키텍처의 브론즈(Bronze) 계층 목적으로 가장 알맞은 것은? (수준 100)

- A. BI 소비자에게 맞춘 집계 지표를 제공한다
- B. 검증되지 않은 원시 데이터를 원래 상태에 가깝게 보관해 재처리의 기반으로 삼는다
- C. 소비자 계약에 맞춘 고정 스키마로 데이터를 서빙한다
- D. 모델을 학습하고 서빙한다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 브론즈는 검증되지 않은 원시 데이터를 담아 원래 상태를 유지하며, 최소한의 검증만 수행하는 계층입니다. 원본이 있어야 실버와 골드를 다시 만들 수 있습니다. A와 C는 골드의 역할이고, D는 본문 범위 밖입니다.

근거: [메달리온 아키텍처 — 2.1 계층 정의](medallion-architecture.md#21-계층-정의)

</details>

### 4. Delta 테이블에서 `UPDATE`가 실행된 뒤 기존 Parquet 파일은 어떻게 되는가? (수준 200)

- A. 즉시 삭제된다
- B. 트랜잭션 로그에 제거 기록이 남고, 실제 파일 삭제는 나중에 `VACUUM`이 한다
- C. 같은 파일 안에서 행만 덮어써진다
- D. 로그에서 파일 이름만 바뀐다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — Delta 테이블의 현재 상태는 로그를 순서대로 읽어 계산한 "살아 있는 파일 목록"입니다. `UPDATE`는 로그에 파일 제거를 기록할 뿐 즉시 지우지 않으며, 실제 삭제는 `VACUUM`이 맡습니다. C는 Parquet 파일을 제자리에서 고치는 방식이므로 본문과 맞지 않습니다.

근거: [Delta Lake 동작 원리 — 트랜잭션 로그](delta-lake-internals.md#트랜잭션-로그)

</details>

### 5. Delta 테이블에 대상에 없는 컬럼 이름을 넣는 `INSERT`는 어떻게 되는가? (수준 200)

- A. 새 컬럼이 자동으로 추가된다
- B. 쓰기 시점에 거부되고 오류가 난다
- C. 해당 컬럼 값만 버려지고 나머지 행은 저장된다
- D. 다음 조회 때 재시도된다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 스키마 강제는 Delta 테이블에 쓸 때 쓰기 시점에 스키마와 맞는지 검사합니다. 대상 테이블에 없는 컬럼을 넣는 `INSERT`는 거부되고, 본문은 이때 올바른 컬럼 이름을 제안하는 오류가 난다고 설명합니다. 컬럼을 추가하려면 스키마 진화를 명시적으로 써야 합니다.

근거: [Delta Lake 동작 원리 — 3.2 스키마 강제 (Schema enforcement)](delta-lake-internals.md#32-스키마-강제-schema-enforcement)

</details>

### 6. 세션 설정으로 자동 스키마 진화를 켜 둘 때의 주의점으로 맞는 것은? (수준 200)

- A. 같은 세션의 다른 쓰기에도 영향을 줄 수 있다
- B. 스키마 진화는 테이블 단위 `ALTER`로만 가능하고 세션 설정은 효과가 없다
- C. 스키마 강제는 CSV나 JSON 같은 비-Delta 파일에도 똑같이 적용된다
- D. 같은 세션의 다른 쓰기에는 영향이 전혀 없다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: A** — 공식 설명에 따라 세션 단위 자동 진화는 같은 세션의 다른 쓰기에도 영향을 줄 수 있으므로 필요할 때만 켭니다. B는 세션 단위 설정이 실제로 존재한다는 본문 내용과 어긋나고, C는 스키마 강제가 Delta 테이블에만 적용된다는 본문 설명과 반대이며, D는 A를 부정한 오답입니다.

근거: [Delta Lake 동작 원리 — 5. 주의사항](delta-lake-internals.md#5-주의사항)

</details>

### 7. 외부(External) 테이블을 `DROP`하면 어떻게 되는가? (수준 200)

- A. 데이터 파일까지 함께 삭제된다
- B. 메타데이터만 제거되고 데이터 파일은 남는다
- C. 보존 기간이 지나면 자동으로 파일이 삭제된다
- D. 관리형 테이블과 같은 방식으로 Unity Catalog 관리 저장소에서 정리된다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 외부 테이블은 메타데이터만 Unity Catalog가 관리하고 데이터 파일 수명은 사용자가 관리합니다. 그래서 `DROP`은 메타데이터만 제거하고 파일은 남깁니다. 관리형 테이블의 `DROP`이 파일까지 정리하는 것과 대비되며, C와 D는 외부 테이블의 수명 관리 원칙과 맞지 않습니다.

근거: [관리형 vs 외부 테이블 — 비교표](managed-vs-external-tables.md#비교표)

</details>

### 8. UniForm으로 Iceberg 읽기를 켠 Delta 테이블에 대해 Iceberg 클라이언트가 할 수 있는 작업은? (수준 300)

- A. 읽기와 쓰기 모두 가능하다
- B. 읽기만 가능하며, 클라이언트 쓰기는 지원되지 않는다
- C. 쓰기는 가능하지만 스냅샷 만료만 불가하다
- D. 삭제 벡터를 켜면 쓰기가 가능해진다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문 표에서 "Delta, Iceberg 읽기 활성화" 테이블은 외부 클라이언트가 읽을 수 있지만 쓸 수 없습니다. UniForm의 Iceberg 클라이언트 지원은 읽기 전용입니다. 쓰기가 필요하면 관리형 Iceberg 테이블을 선택해야 합니다. C와 D는 본문의 제약과 맞지 않습니다.

근거: [Apache Iceberg 지원 — 외부 클라이언트가 할 수 있는 작업](iceberg-support.md#외부-클라이언트가-할-수-있는-작업), [Apache Iceberg 지원 — UniForm 제약](iceberg-support.md#uniform-제약)

</details>

### 9. 삭제 벡터(Deletion vectors)와 UniForm(Iceberg 읽기)을 함께 다룰 때 맞는 설명은? (수준 300)

- A. 두 기능을 함께 켜는 것이 권장된다
- B. Iceberg 읽기가 켜진 Delta 테이블에서는 삭제 벡터를 켤 수 없다
- C. 삭제 벡터는 Iceberg 클라이언트에서만 동작하는 기능이다
- D. 삭제 벡터 설정은 UniForm과 무관하므로 순서를 신경 쓸 필요가 없다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 Iceberg 읽기가 켜진 Delta 테이블에서 삭제 벡터를 켤 수 없다고 명시합니다. 이미 삭제 벡터가 있는 테이블에 Iceberg 읽기를 켜려면 먼저 `REORG`로 삭제 벡터를 끄고 정리해야 합니다. 본문은 Iceberg v3 테이블에는 삭제 벡터가 지원된다는 예외도 적고 있습니다. A와 D는 이 제약과 정면으로 어긋나고, C는 삭제 벡터가 Delta 테이블 기능이라는 본문 설명과 맞지 않습니다.

근거: [삭제 벡터 — 5. 주의사항](deletion-vectors.md#5-주의사항)

</details>

## 실무 체크리스트

이 장의 내용을 실제 환경에 적용할 때 확인할 항목입니다.

- [ ] 테이블을 만들기 전에 쓰기 주체와 외부 엔진의 읽기·쓰기 필요 여부를 정하고, 관리형 Iceberg와 UniForm 중 고른다 — [Apache Iceberg 지원](iceberg-support.md#5-주의사항)
- [ ] 외부 테이블을 만들기 전에 외부 위치와 권한을 확인한다 — [관리형 vs 외부 테이블](managed-vs-external-tables.md#5-주의사항)
- [ ] `MERGE` 소스의 중복 키를 제거한 뒤 실행한다 — [Delta Lake 동작 원리](delta-lake-internals.md#35-merge로-업서트)
- [ ] 자동 스키마 진화는 필요한 쓰기에만 켜고, 세션 범위가 다른 쓰기에 미치는 영향을 확인한다 — [Delta Lake 동작 원리](delta-lake-internals.md#33-스키마-진화-schema-evolution)
- [ ] 리퀴드 클러스터링 키를 바꾼 뒤 `OPTIMIZE ... FULL`로 기존 데이터를 다시 묶는다 — [테이블 레이아웃 최적화](table-layout-optimization.md#33-키를-처음-켠-뒤-전체-재클러스터링)
- [ ] `VACUUM` 보존 기간을 줄이기 전에 시간 여행 요구와 장기 실행 잡을 확인한다 — [테이블 레이아웃 최적화](table-layout-optimization.md#36-vacuum으로-오래된-파일-정리)
- [ ] 삭제 벡터를 켜기 전에 정리 계획과 외부 클라이언트의 호환성을 확인한다 — [삭제 벡터](deletion-vectors.md#5-주의사항)
- [ ] `RESTORE`를 실행하기 전에 `DESCRIBE HISTORY`로 대상 버전을 확인한다 — [타임 트래블과 변경 데이터 피드](time-travel-and-cdf.md#5-주의사항)
- [ ] 메달리온 계층별로 보존 정책과 쓰기 주체를 나눠 정한다 — [메달리온 아키텍처](medallion-architecture.md#5-주의사항)

## 참고 문서

이 페이지는 이 장 본문을 근거로 합니다. 공식 문서 링크는 각 본문 페이지의 참고 문서를 보세요.

- [레이크하우스가 필요한 이유](why-lakehouse.md)
- [Delta Lake 동작 원리](delta-lake-internals.md)
- [Apache Iceberg 지원](iceberg-support.md)
- [관리형 vs 외부 테이블](managed-vs-external-tables.md)
- [테이블 레이아웃 최적화](table-layout-optimization.md)
- [삭제 벡터](deletion-vectors.md)
- [타임 트래블과 변경 데이터 피드](time-travel-and-cdf.md)
- [메달리온 아키텍처](medallion-architecture.md)
