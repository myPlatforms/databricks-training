# 행 필터와 열 마스크

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 한눈에 보기

**행 필터**(Row filter)는 사용자에 따라 테이블의 **행** 을 숨기고, **열 마스크**(Column mask)는 **열의 값** 을 가립니다. 둘 다 같은 테이블을 조회하더라도 사용자마다 다른 결과를 보여 주는 행-열 수준 보안(row- and column-level security)입니다.

UC에서 이를 적용하는 방법은 두 가지입니다.

| 방법 | 범위 | 적용 단위 | 공식 권장 |
|---|---|---|---|
| 테이블 단위 행 필터·열 마스크 | 테이블 하나 | `ALTER TABLE`로 테이블마다 붙임 | 테이블별 고유 로직이 필요하거나 아직 ABAC를 도입하지 않은 경우 |
| ABAC 정책 | 메타스토어, 카탈로그, 스키마, 테이블 | 태그 조건에 맞는 객체에 자동 적용 | 중앙 관리와 확장이 필요한 경우 |

공식 문서의 액세스 제어 페이지는 이렇게 권장합니다. "Use row filters and column masks only when you need per-table logic or haven't adopted ABAC yet." 즉 **테이블별 로직이 꼭 필요하거나, ABAC를 아직 도입하지 않았을 때만** 테이블 단위 방식을 쓰라는 뜻입니다.

> **참고** 이 페이지는 테이블 단위 방식과 ABAC 정책 예제를 함께 다룹니다. 정책 체계 전체(태그, GRANT·DENY 정책, 한도)는 [거버넌스 태그와 ABAC 정책](governed-tags-and-abac.md)에서 설명합니다.

## 1. 왜 필요한가

### 이전 방식의 한계

테이블 한 개를 여러 부서가 나눠 쓸 때 흔한 방법은 뷰를 만들어 부서별로 다른 `WHERE`와 마스킹 식을 넣는 것입니다. 이 방식에는 다음 문제가 있습니다.

- 부서마다 뷰가 늘어나, 뷰 목록과 권한이 함께 복잡해집니다.
- 원본 테이블에 직접 접근 권한이 남아 있으면 뷰를 우회할 수 있습니다.
- 마스킹 규칙이 여러 뷰에 복사되면 규칙이 바뀔 때 모든 뷰를 고쳐야 합니다.

행 필터와 열 마스크는 **원본 테이블에 규칙을 붙이고**, 사용자가 누구인지에 따라 결과를 바꾸는 방식입니다. 뷰를 따로 만들지 않아도 같은 테이블을 가리키는 쿼리가 사용자별로 다른 결과를 냅니다.

## 2. 어떻게 동작하는가

### 테이블 단위 방식

테이블 단위 방식은 다음 순서로 동작합니다.

1. 필터나 마스크 로직을 **UDF**(사용자 정의 함수)로 만듭니다.
2. `ALTER TABLE`로 테이블에 행 필터 또는 열 마스크를 연결합니다.
3. 사용자가 테이블을 조회하면 UC가 연결된 함수를 실행해 결과를 바꿉니다.

공식 문서는 행 필터와 열 마스크를 "테이블 수준 필터(Table-level row/column filters)"라고 부르며, 테이블 단위 로직을 위한 방식이라고 설명합니다.

| 항목 | 내용 |
|---|---|
| 구현 방식 | UDF를 테이블에 연결 |
| 열 마스크 제한 | 열 하나에 마스크는 하나만 붙일 수 있습니다. 공식 문서: "Each column can have one mask." |
| 관리 권한 | 테이블 소유자 또는 `MANAGE`를 가진 사용자가 `ALTER TABLE`로 관리 |
| 최소 런타임 | Databricks Runtime 12.2 LTS 미만은 행 필터와 열 마스크를 지원하지 않습니다. |
| 상태 라벨 | 이 페이지에는 상태 라벨이 없습니다. 시간 여행과 ABAC 조합만 Beta로 언급합니다. |

### ABAC 정책 방식

ABAC 정책 방식은 정책 본문에 함수와 조건을 넣고, 태그가 맞는 객체에 자동으로 적용합니다. 정책 자체의 구조는 [거버넌스 태그와 ABAC 정책](governed-tags-and-abac.md)에서 다루었으므로, 여기서는 행 필터와 열 마스크 쪽만 봅니다.

| 항목 | 내용 |
|---|---|
| 적용 단위 | 태그 조건으로 선택된 객체 |
| 필요 권한 | 정책을 붙일 대상 객체에 `MANAGE`(또는 소유권)와 구현 함수에 `EXECUTE` |
| 필요 런타임 | Databricks Runtime 16.4 이상, 또는 서버리스 컴퓨트 |
| 뷰 적용 | Beta. 워크스페이스 관리자가 "ABAC on Views" 미리보기를 켜야 합니다. |
| 열 마스크 조건 | `MATCH COLUMNS` 조건은 열 마스크 정책에서 절당 3개까지 |

## 3. 어떻게 쓰는가

### 테이블 단위 행 필터

공식 문서 예제는 함수를 만든 뒤 `ALTER TABLE`로 연결하는 형태입니다.

```sql
-- 행 필터 함수 정의
CREATE FUNCTION salary_filter(dept STRING) RETURNS BOOLEAN
RETURN dept IS NULL;

-- employees 테이블의 department 열에 행 필터 연결
ALTER TABLE employees SET ROW FILTER salary_filter ON (department);
```

> **주의** 위 예제의 함수 본문은 공식 문서의 예제 그대로이며, 실제 운영에서는 사용자 식별 함수(`current_user()`, 그룹 멤버십 함수 등)와 조합해 **누구에게 어떤 행을 보일지** 를 정해야 합니다. 예제의 `dept IS NULL` 조건은 설명용이므로 운영 규칙으로 쓰지 마십시오.

공식 문서는 행 필터 함수의 인자 타입을 열 타입과 맞추라고 설명합니다(예: 열이 `STRING`이면 함수 인자도 `STRING`). 타입이 맞지 않으면 실행 시 오류가 나거나 결과가 예상과 다를 수 있습니다.

### 테이블 단위 열 마스크

열 마스크는 `ALTER TABLE ... ALTER COLUMN ... SET MASK` 형태로 연결합니다. 공식 문서의 이 페이지는 마스크 함수 예제를 싣지 않으므로, 마스크 함수 작성 예는 ABAC 정책 예제로 대신 보입니다. 아래 예는 ABAC 정책 문서의 열 마스크 예제입니다.

```sql
-- 마스크 함수: 뒤쪽 nr 자리만 남기고 가림
CREATE FUNCTION ssn_to_last_nr (ssn STRING, nr INT) RETURNS STRING
RETURN right(ssn, nr);

-- 스키마 단위 열 마스크 정책: pii=ssn 태그가 붙은 열에 적용
CREATE POLICY mask_ssn
ON SCHEMA prod.customers
COLUMN MASK ssn_to_last_nr
TO us_analysts EXCEPT admins
FOR TABLES
MATCH COLUMNS has_tag_value('pii', 'ssn') AS ssn
ON COLUMN ssn
USING COLUMNS (4);
```

이 예제는 ABAC 정책 방식입니다. 같은 기능을 테이블마다 붙이는 방식과 비교하면 다음과 같습니다.

| 항목 | 테이블 단위 | ABAC 정책 |
|---|---|---|
| 적용 방법 | 테이블마다 `ALTER TABLE` | 스키마에 정책 한 개 |
| 새 테이블 | 붙이기 전까지 노출 | 태그만 맞으면 자동 적용 |
| 규칙 변경 | 테이블마다 수정 | 정책 한 곳에서 수정 |
| 상태 | 페이지에 상태 라벨 없음 | 기능별 상태가 다름(「거버넌스 태그와 ABAC 정책」 페이지 표) |

### 정책 기반 행 필터

공식 문서 예제입니다. 민감도가 높은 테이블에서 EU 고객 행을 숨기는 정책입니다.

```sql
CREATE FUNCTION non_eu_region (geo_region STRING) RETURNS BOOLEAN
RETURN geo_region <> 'eu';

CREATE POLICY hide_eu_customers
ON SCHEMA prod.customers
COMMENT 'Exclude rows with European customers from sensitive tables'
ROW FILTER non_eu_region
TO us_analysts
FOR TABLES
WHEN has_tag_value('sensitivity', 'high')
MATCH COLUMNS has_tag('geo_region') AS region
USING COLUMNS (region);
```

`WHEN`은 정책이 적용될 객체를 태그로 고르는 조건입니다. `MATCH COLUMNS`는 함수 인자에 넘길 열을 태그로 고릅니다. 이 예는 `geo_region` 태그가 붙은 열을 함수의 `region` 인자로 넘깁니다.

## 4. 트레이드오프

### 테이블 단위 방식이 맞는 경우

- 테이블 두세 개에 한정된 규칙이고, 그 규칙이 다른 테이블과 공유되지 않습니다.
- 규칙이 테이블 고유 로직이라 태그로 표현하기 어렵습니다.
- ABAC 정책 한도(테이블당 정책 50개 등)나 Beta 범위를 피해야 합니다.

### ABAC 정책 방식이 맞는 경우

- 민감 열이 여러 스키마와 테이블에 흩어져 있고, 태그로 분류되어 있습니다.
- 같은 규칙을 여러 테이블에 일관되게 적용해야 합니다.
- 「계보와 데이터 분류」 페이지의 데이터 분류 결과를 자동 태그로 받아 정책을 걸 계획이 있습니다.

### 한계와 주의점

| 항목 | 설명 |
|---|---|
| 성능 | 행 필터와 열 마스크는 조회 시 함수를 실행합니다. 함수가 무거우면 쿼리가 느려질 수 있습니다. 공식 문서는 성능 영향을 별도로 명시하지 않으므로, 대용량 테이블은 실측으로 확인하십시오. |
| 우회 | 원본 테이블에 여전히 `SELECT`가 있으면 필터가 적용된 결과를 받게 되므로, 우회 문제는 권한 설계로 막아야 합니다. |
| 타입 캐스트 | 공식 문서는 ANSI 모드(`spark.sql.ansi.enabled = true`)를 켜서 실패한 타입 캐스트가 `NULL`을 조용히 반환하지 않고 오류를 내게 하라고 권장합니다. |

## 5. 주의사항

> **주의** 공식 문서는 Databricks Runtime 12.2 LTS 미만에서는 행 필터와 열 마스크가 동작하지 않는다고 명시합니다. 구형 클러스터에서 실행하면 보안 규칙이 적용되지 않는 것이 아니라 아예 지원되지 않습니다. 실행 환경의 런타임을 먼저 확인하십시오.

> **주의** 열 마스크 정책의 `MATCH COLUMNS` 조건은 절당 3개까지입니다. 행 필터는 6개입니다. 이 한도를 넘으면 정책 설계를 나누십시오.

> **참고** 2026년 8월 21일과 17일 릴리즈 노트는 ABAC 열 마스크와 행 필터에 컨텍스트 속성, 신원 속성을 쓰는 기능을 Beta로 공지했습니다. 9월 16일 릴리즈 노트는 ABAC 열 마스크에서 `VARIANT` 캐스트가 `ARRAY`와 `MAP` 열까지 확장되었다고 공지했습니다(상태 라벨 없음).

- ABAC 정책을 만드는 사용자는 대상 객체에 `MANAGE`(또는 소유권)와 구현 함수에 `EXECUTE`가 필요합니다. 함수 권한이 빠지면 정책 생성이 실패하므로 정책 생성 전에 확인하십시오. 정책을 받는 사용자 쪽의 함수 권한 요구는 이 장에서 확인한 원문에 명시되지 않았습니다.
- 마스크 함수는 원본 값을 그대로 반환하지 않도록 작성하십시오. 가리기가 불완전하면 민감 정보가 노출됩니다.
- 테이블 단위 규칙과 정책이 같은 열에 겹치면 어느 규칙이 최종 적용되는지 테스트 계정으로 확인하십시오.
- 공식 문서 페이지에는 행 필터 제거(`DROP ROW FILTER`)와 열 마스크 제거(`DROP MASK`) 문법이 없었습니다. 제거 문법은 원문 정책 관리 페이지에서 확인해 쓰십시오.

## 참고 문서

- [Access control in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/)
- [Row filters and column masks](https://docs.databricks.com/aws/en/tables/row-and-column-filters)
- [Create and manage row filter and column mask policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- [Requirements, quotas, and limitations for row filter and column mask policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
