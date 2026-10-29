# 퀴즈와 체크리스트

> 기준일: 2026-10-29 · 근거: 이 장 본문 · 수준: 100~300

이 장에서 다룬 내용을 확인하는 문제입니다. 정답을 펼치면 해설과 근거 페이지로 가는 링크가 있습니다.

## 퀴즈

### 1. 노트북, Job, 파이프라인을 Databricks가 관리하는 온디맨드 자원에서 실행하며, 사용자가 클러스터 노드나 런타임을 직접 고르지 않는 컴퓨트는? (수준 100)

- A. 클래식 컴퓨트
- B. 서버리스 컴퓨트
- C. Pro 유형 SQL 웨어하우스
- D. 인스턴스 풀

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 서버리스 컴퓨트는 노트북, 워크플로(Job), Lakeflow 파이프라인을 Databricks가 관리하는 온디맨드 자원에서 실행합니다. 클래식 컴퓨트는 사용자가 만들고 설정하고 관리하는 자원입니다. C는 SQL 작업용 웨어하우스 유형이고, D는 클래식 클러스터의 시작 시간을 줄이는 유휴 인스턴스 집합입니다.

근거: [컴퓨트 종류와 선택 기준 — 2.1 세 가지 분류](compute-types-and-selection.md#21-세-가지-분류)

</details>

### 2. `collect()`로 큰 결과를 모을 때 메모리 한도가 걸리는 곳은? (수준 100)

- A. 익스큐터
- B. 드라이버
- C. 클러스터 매니저
- D. 노트북 셀 결과 저장소

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 드라이버는 사용자 코드의 `main`을 실행하고 `SparkContext`를 만드는 한 프로세스입니다. `collect()`나 `toPandas()`는 결과를 드라이버 메모리로 가져오므로, 큰 데이터는 드라이버 메모리를 초과합니다. 익스큐터는 태스크를 실행하고 데이터를 저장하는 워커 쪽 프로세스입니다.

근거: [Spark 기초 — 2.1 드라이버 프로그램 (Driver program)](spark-basics.md#21-드라이버-프로그램-driver-program)

</details>

### 3. `filter`와 `select`를 호출했는데 계산이 바로 일어나지 않는 이유는? (수준 100)

- A. 캐시가 꺼져 있어서
- B. 지연 실행(Lazy evaluation)이라 `count`나 `write` 같은 액션이 호출될 때 계산되기 때문에
- C. 드라이버가 아직 준비되지 않아서
- D. 서버리스에서는 변환 연산이 지원되지 않아서

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — Spark의 변환은 결과를 바로 계산하지 않고 적용할 연산을 기록만 합니다. 액션이 호출될 때 기록된 변환 전체를 계산합니다. 그래서 변환 줄이 빨리 끝나도 계산이 끝났다는 뜻은 아닙니다. 본문은 서버리스에서도 DataFrame 변환을 쓸 수 있다는 점에서 D도 틀렸다고 볼 수 있습니다.

근거: [Spark 기초 — 2.6 지연 실행 (Lazy evaluation)](spark-basics.md#26-지연-실행-lazy-evaluation)

</details>

### 4. 서버리스 노트북에 PySpark를 의존성으로 설치하는 것에 대해 맞는 설명은? (수준 200)

- A. PySpark를 설치해야만 `SparkSession`을 만들 수 있다
- B. 서버리스 노트북이 Spark 세션을 이미 제공하므로 PySpark를 따로 설치하면 충돌할 수 있다
- C. 의존성 설치는 노트북마다 매번 다시 해야 한다
- D. 노트북에서 설치한 패키지는 Job에서 자동으로 함께 쓰인다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 서버리스 노트북은 Spark 세션을 이미 제공하므로 PySpark를 따로 설치하지 않도록 문서가 경고합니다. 환경은 캐시되므로 노트북을 다시 열어도 다시 설치하지 않습니다(C 틀림). 노트북이 쓰는 라이브러리는 환경 의존성으로 옮겨야 Job에서도 보입니다(D 틀림).

근거: [서버리스 컴퓨트 — 노트북에서 환경 선택](serverless-compute.md#노트북에서-환경-선택)

</details>

### 5. 시작 지연을 감수할 수 있는 정기 배치 Job에서 DBU 소비를 낮추고 싶다면 고를 성능 모드는? (수준 200)

- A. Performance optimized
- B. Standard
- C. 클래식 Dedicated 컴퓨트
- D. 서버리스 GPU 컴퓨트

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 서버리스 Job의 Standard 모드는 컴퓨트 사용량을 줄여 비용을 낮추며, 시작 지연을 감수할 수 있는 워크로드에 맞습니다. 두 성능 모드는 같은 SKU를 쓰지만 Standard가 DBU를 더 적게 소비한다고 본문이 설명합니다. A는 시간에 민감한 워크로드용이고, C와 D는 성능 모드 선택지가 아닙니다.

근거: [서버리스 컴퓨트 — 2.5 성능 모드 (Performance mode)](serverless-compute.md#25-성능-모드-performance-mode)

</details>

### 6. R 언어를 써야 하는 클래식 컴퓨트의 액세스 모드로 알맞은 것은? (수준 200)

- A. Standard
- B. Dedicated
- C. Auto는 항상 R을 지원하므로 어떤 모드든 상관없다
- D. Standard에 Photon을 켜면 R을 쓸 수 있다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문의 액세스 모드 표에서 Standard는 Python, SQL, Scala만 지원하고, Dedicated는 R을 포함합니다. Auto는 기본값이지만 기본 선택은 Standard이므로, R이 필요하면 Dedicated를 명시적으로 고르는 것이 맞습니다. Photon은 액세스 모드와 무관한 가속 엔진입니다.

근거: [클래식 컴퓨트 — 2.1 액세스 모드 (Access mode)](classic-compute.md#21-액세스-모드-access-mode)

</details>

### 7. Pro 유형 SQL 웨어하우스에 대한 설명으로 맞는 것은? (수준 200)

- A. Photon과 Predictive IO를 지원하지만 Intelligent Workload Management는 지원하지 않는다
- B. Photon을 지원하지 않는다
- C. 실행 위치가 Databricks 계정 안이다
- D. 자동 중지를 지원하지 않는다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: A** — 세 유형의 비교에서 Pro는 Photon과 Predictive IO를 지원하고 Intelligent Workload Management는 지원하지 않습니다. 실행 위치는 고객 AWS 계정입니다(C 틀림). B와 D도 본문 설명과 맞지 않습니다. 참고로 Serverless 유형이 세 가지 성능 기능을 모두 지원합니다.

근거: [SQL 웨어하우스 — 2.1 세 가지 유형](sql-warehouses.md#21-세-가지-유형)

</details>

### 8. 서버리스 Job에서 `df.cache()`를 쓰고 결과를 여러 태스크가 나눠 쓰는 구조에 대한 설명으로 맞는 것은? (수준 300)

- A. 캐시는 Job의 모든 태스크가 공유하므로 태스크를 나눠도 재계산되지 않는다
- B. 캐시는 같은 세션 안에서만 유효하고 태스크 사이에서 공유되지 않으므로, 태스크 간 중간 결과는 테이블로 저장한다
- C. `CACHE TABLE`을 쓰면 세션 밖에서도 캐시가 공유된다
- D. `df.cache()`는 호출 시점이 아니라 마지막 액션이 실행될 때 계산된다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 서버리스 DataFrame 캐시는 세션 스냅샷이며, Job의 태스크가 나뉘어 있으면 태스크 사이에서 캐시를 공유하지 않습니다. 그래서 태스크 간 중간 결과는 테이블로 저장하라고 본문이 권장합니다. C는 `CACHE TABLE`이 지원되지 않는다는 본문 내용과 반대이고, D는 `cache()`가 호출 즉시 계산한다는 설명과 어긋납니다.

근거: [서버리스 제약과 지원 기능 — 3.3 캐시의 제한](serverless-limitations.md#33-캐시의-제한)

</details>

### 9. 클래식 인스턴스 풀에서 대기 중인(유휴) 인스턴스에 대한 과금 설명으로 맞는 것은? (수준 300)

- A. DBU와 클라우드 인스턴스 요금이 모두 청구되지 않는다
- B. DBU는 청구되지 않지만 클라우드 제공자의 인스턴스 요금은 계속 적용된다
- C. DBU만 청구되고 클라우드 인스턴스 요금은 없다
- D. 풀에 있는 동안에도 DBU가 청구되고 인스턴스 요금은 면제된다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 풀의 과금 규칙은 유휴 인스턴스에 DBU는 청구되지 않지만 인스턴스 제공자의 요금은 적용된다는 것입니다. 그래서 풀 크기를 키울수록 유휴 상태의 클라우드 비용이 늘어납니다. A, C, D는 이 규칙과 맞지 않습니다.

근거: [인스턴스 풀과 컴퓨트 정책 — 과금 규칙](pools-and-policies.md#과금-규칙)

</details>

### 10. 서버리스 Job의 Standard 성능 모드와 Performance optimized 모드의 비용 차이에 대해 맞는 설명은? (수준 300)

- A. Standard는 다른 SKU로 청구된다
- B. 두 모드는 같은 SKU를 쓰고, Standard가 DBU를 더 적게 소비한다고 문서가 설명한다
- C. Performance optimized가 항상 비용이 낮다
- D. 성능 모드는 청구에 영향을 주지 않는다

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 두 모드가 같은 SKU를 쓰지만, Standard 모드는 DBU를 더 적게 소비한다고 설명합니다. 따라서 시간에 민감하지 않은 워크로드는 Standard가 유리할 수 있습니다. A와 D는 같은 SKU라는 설명과 어긋나고, C는 DBU 소비가 더 많은 쪽이 Performance optimized라는 설명과 반대입니다.

근거: [비용 구조 비교 — 2.2 DBU 소비율이 달라지는 경우](cost-structure.md#22-dbu-소비율이-달라지는-경우)

</details>

## 실무 체크리스트

이 장의 내용을 실제 환경에 적용할 때 확인할 항목입니다.

- [ ] 서버리스 가능 여부와 제약(언어, RDD API, 컴퓨트 범위 라이브러리, 장시간 실행 등)을 먼저 확인하고, 걸리면 클래식으로 옮긴다 — [컴퓨트 종류와 선택 기준](compute-types-and-selection.md#3-어떻게-쓰는가-선택-절차)
- [ ] 서버리스 노트북의 라이브러리는 환경의 Dependencies에서 설치해 Job과 재현성을 맞춘다 — [서버리스 컴퓨트](serverless-compute.md#5-주의사항)
- [ ] 서버리스 Job의 문제는 Spark UI 대신 클라이언트 로그와 쿼리 프로파일로 확인한다 — [서버리스 제약과 지원 기능](serverless-limitations.md#24-ui와-로그)
- [ ] 여러 태스크가 쓰는 중간 결과는 캐시에 기대지 않고 테이블로 저장한다 — [서버리스 제약과 지원 기능](serverless-limitations.md#33-캐시의-제한)
- [ ] 클래식 컴퓨트는 액세스 모드를 Auto에 맡기지 않고 워크로드에 맞게 명시적으로 고른다 — [클래식 컴퓨트](classic-compute.md#21-액세스-모드-access-mode)
- [ ] 인스턴스 풀은 크기를 보수적으로 잡고, 드라이버에는 스팟 인스턴스 풀을 쓰지 않는다 — [인스턴스 풀과 컴퓨트 정책](pools-and-policies.md#5-주의사항)
- [ ] Pro·Classic 웨어하우스는 자동 중지 설정과 클러스터 수 범위를 피크 부하에 맞춘다 — [SQL 웨어하우스](sql-warehouses.md#24-자동-중지-auto-stop)
- [ ] 비용 점검은 DBU와 클라우드 인스턴스 청구를 나눠 보고 `system.billing.usage`로 확인한다 — [비용 구조 비교](cost-structure.md#36-비용-점검-순서)
- [ ] Photon 사용 여부는 쿼리 프로파일이나 Spark UI에서 확인하고, 짧은 쿼리에는 기대를 낮춘다 — [Photon](photon.md#31-photon-사용-여부-관측)

## 참고 문서

이 페이지는 이 장 본문을 근거로 합니다. 공식 문서 링크는 각 본문 페이지의 참고 문서를 보세요.

- [컴퓨트 종류와 선택 기준](compute-types-and-selection.md)
- [서버리스 컴퓨트](serverless-compute.md)
- [서버리스 제약과 지원 기능](serverless-limitations.md)
- [클래식 컴퓨트](classic-compute.md)
- [인스턴스 풀과 컴퓨트 정책](pools-and-policies.md)
- [SQL 웨어하우스](sql-warehouses.md)
- [Photon](photon.md)
- [비용 구조 비교](cost-structure.md)
- [Spark 기초](spark-basics.md)
