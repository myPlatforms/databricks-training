# 거버넌스 태그와 ABAC 정책

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

**속성 기반 접근 제어**(Attribute-based access control, ABAC)는 객체마다 권한을 주는 대신, 객체에 붙은 **속성** 을 평가해 접근을 결정하는 방식입니다. UC에서 그 속성은 주로 **거버넌스 태그**(Governed tags)입니다. 정책은 "이 태그가 붙은 객체에는 이 규칙을 적용한다"는 형태로 정의하고, 정책이 걸린 범위(메타스토어, 카탈로그, 스키마, 테이블) 안에서 조건에 맞는 객체에 자동으로 적용됩니다.

이 페이지는 다음 세 가지를 다룹니다.

| 구성 요소 | 역할 | 이 페이지 위치 |
|---|---|---|
| 거버넌스 태그(Governed tags) | 계정 수준에서 정의된 태그. 허용 값과 사용 권한이 정책으로 제한됩니다. | 1, 「권한 모델과 소유권」 페이지 |
| ABAC 정책(Policies) | 태그 조건에 따라 행 필터, 열 마스크, 권한 부여(GRANT), 권한 거부(DENY)를 적용합니다. | 2, 「거버넌스 태그와 ABAC 정책」 페이지 |
| 정책 한도와 상태 | 정책 수, 주체 수 등의 상한과 Beta 범위 | 「행 필터와 열 마스크」 페이지 |

> **참고** 행 필터와 열 마스크를 테이블마다 직접 붙이는 방식은 [행 필터와 열 마스크](row-filters-and-column-masks.md)에서 다룹니다. 이 페이지는 태그와 정책 체계를 설명합니다.

## 1. 왜 필요한가

### 이전 방식의 한계

객체별 `GRANT`와 테이블별 행 필터·열 마스크만으로 보안을 관리하면 다음 문제가 생깁니다.

- 새 테이블이 생길 때마다 같은 규칙을 다시 붙여야 합니다. 빠뜨리면 민감 열이 그대로 노출됩니다.
- 같은 규칙이 여러 테이블에 흩어져 있어, 규칙이 바뀌면 전부 찾아서 고쳐야 합니다.
- "PII가 붙은 열은 모두 가린다"처럼 **분류 기준** 으로 정책을 쓰고 싶어도 방법이 없었습니다.

태그 기반 정책은 이 문제를 **분류(태그)와 규칙(정책)을 분리** 해서 해결합니다. 새 테이블에 올바른 태그만 붙이면, 이미 정의된 정책이 자동으로 적용됩니다.

## 2. 어떻게 동작하는가

### 거버넌스 태그

공식 문서의 설명에 따르면 거버넌스 태그는 계정 수준(account-level) 태그로, 각 태그에 **태그 정책**(tag policy)이 있어 사용 방식을 통제합니다.

| 항목 | 내용 |
|---|---|
| 적용 대상 | UC 객체(테이블, 카탈로그 등), 워크스페이스 객체(대시보드, 노트북, Databricks 앱, Genie 에이전트 등) |
| 적용 불가 | SQL 웨어하우스 같은 컴퓨트, 잡. 이 객체들은 별도의 태그 방식을 씁니다. |
| 일반 태그와의 차이 | 일반 태그는 누구나 만들고 붙일 수 있습니다. 거버넌스 태그는 정책으로 누가 붙일 수 있는지와 허용 값을 제한합니다. |
| 표시 | 잠금 아이콘이 붙고, 태그 지정 드롭다운의 **Governed** 그룹에 나타납니다. |

거버넌스 태그의 동작 규칙은 다음과 같습니다.

- 정책으로 정의된 **허용 값(allowed values)** 중에서만 값을 지정할 수 있습니다.
- 카탈로그나 스키마에 붙은 거버넌스 태그는 그 안의 객체에 상속됩니다. 단 **테이블의 열** 은 상속 대상이 아닙니다.
- 같은 키의 기존 태그 할당이 있는 상태에서 같은 키로 거버넌스 태그를 만들면, 기존 할당이 거버넌스 태그가 됩니다.
- 적용 범위는 계정 수준이며 모든 워크스페이스에 걸칩니다.

### 시스템 거버넌스 태그

Databricks가 미리 정의한 시스템 거버넌스 태그도 있습니다. 편집하거나 삭제할 수 없습니다. 공식 문서가 예로 드는 것은 다음과 같습니다.

| 태그 계열 | 예 | 용도 |
|---|---|---|
| 인증 상태 | `system.certification_status` | 이름으로 보아 인증 상태 표시용. 세부 값은 원문 확인 |
| 민감 데이터 분류 | `class.*` 계열 | 데이터 분류 결과 표시(예: `class.email_address`는 데이터 분류 페이지의 `has_tag` 예제에 나옴). [계보와 데이터 분류](lineage-and-classification.md) 참고 |
| SAP 개인정보 | `sap.PersonalData.*` 계열 | 공식 문서가 계열 이름만 나열. 세부 용도는 원문 확인 |
| AI 자산 | `ai.*` 계열 | 공식 문서가 계열 이름만 나열. 세부 용도는 원문 확인 |

시스템 거버넌스 태그를 붙이거나 떼려면 해당 태그에 대한 `ASSIGN` 권한이 필요하며, 허용된 값만 쓸 수 있습니다. 공식 문서는 기본적으로 계정 관리자만 시스템 거버넌스 태그에 대한 `MANAGE`와 `ASSIGN` 권한을 가진다고 설명합니다.

### ABAC 정책의 구조

정책은 다음 요소로 정의합니다.

| 요소 | 설명 |
|---|---|
| 범위(Scope) | 메타스토어, 카탈로그, 스키마, 테이블 가운데 하나. 공식 문서는 메타스토어 수준 정책이 Beta라고 표기합니다. |
| 조건(Condition) | `has_tag()`, `has_tag_value()`를 `AND`, `OR`, `NOT`으로 조합한 식 |
| 대상 주체(Principal) | `TO`로 지정하고, 예외는 `EXCEPT`로 지정 |
| 구현 함수 | 행 필터나 열 마스크 로직을 담은 UDF |
| 권한(GRANT·DENY 정책의 경우) | 부여하거나 거부할 권한과 대상 객체 유형 |

공식 문서는 정책 유형을 네 가지로 나눕니다.

| 정책 유형 | 하는 일 | 상태 |
|---|---|---|
| 행 필터(Row filter) | 조건에 맞는 행만 보여 줍니다. | 문서에 상태 라벨 없음. 테이블에 적용 |
| 열 마스크(Column mask) | 민감 열 값을 가립니다. | 문서에 상태 라벨 없음. 테이블에 적용 |
| GRANT 정책 | 태그 조건에 맞는 객체에 권한을 부여합니다. | 모델, 모델 서비스, 모델 프로바이더 서비스, MCP 서비스: GA. 에이전트 서비스, 스킬: Beta (GRANT 정책 페이지 기준) |
| DENY 정책 | 태그 조건에 맞는 객체에서 권한을 거부합니다. `MANAGE ACCESS CONTROL`을 거부하는 등 지원되는 객체 유형에 한정됩니다. | Beta |

> **주의** 서비스 유형의 상태 라벨은 페이지마다 다릅니다. 보안 설계에 넣기 전에 해당 기능 페이지에서 최신 표기를 확인하십시오.

### 정책이 평가되는 방식

공식 문서는 정책이 **동적으로 평가된다** 고 설명합니다. 객체에 정책이 노리는 속성(태그)이 있으면 정책이 자동으로 적용됩니다. 태그를 붙이거나 바꾼 뒤 적용까지 **수 분** 이 걸릴 수 있다고 문서가 명시합니다.

GRANT 정책은 객체에 접근이 확인될 때마다 범위 안 객체의 태그를 `WHEN` 조건과 비교합니다. 직접 `GRANT`가 객체를 3단계 이름으로 지정하는 것과 달리, GRANT 정책은 태그로 객체를 고릅니다.

## 3. 어떻게 쓰는가

### 거버넌스 태그를 객체에 붙이기

Databricks Runtime 16.1 이상에서는 `SET TAG`와 `UNSET TAG`를 씁니다.

```sql
-- 카탈로그에 태그 지정(Databricks Runtime 16.1 이상)
SET TAG ON CATALOG catalog `cost_center` = `hr`;

-- 카탈로그에서 태그 제거
UNSET TAG ON CATALOG catalog cost_center;
```

Databricks Runtime 13.3 이상에서는 `ALTER ... SET TAGS`를 씁니다. 공식 문서 예제는 열에 태그를 붙이는 형태입니다.

```sql
-- ssn 열에 거버넌스 태그 지정
ALTER TABLE abac.customers.profiles
ALTER COLUMN SSN
SET TAGS ('pii' = 'ssn');

-- 열에서 태그 제거
UNSET TAG ON COLUMN abac.customers.profiles.SSN pii;
```

> **주의** 공식 문서는 `ALTER TABLE` 한 번으로 여러 열에 태그를 붙일 수 없다고 설명합니다. 열 여러 개에 태그를 붙이려면 열마다 명령을 나눠 실행하십시오.

### 정책 설계 예 (행 필터)

다음은 공식 문서의 행 필터 정책 예제 형태입니다. 한 행이 한 역할을 합니다.

```sql
-- 행 필터로 쓸 함수 정의
CREATE FUNCTION non_eu_region (geo_region STRING) RETURNS BOOLEAN
RETURN geo_region <> 'eu';

-- 민감도가 높은 스키마에서 EU 고객 행을 숨기는 정책
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

정책 문법의 구조는 다음과 같습니다. 공식 문서는 행 필터와 열 마스크 모두 이 형태를 따른다고 설명합니다.

```sql
CREATE [OR REPLACE] POLICY policy_name
ON { METASTORE | CATALOG catalog_name | SCHEMA schema_name | TABLE table_name }
[COMMENT description]
{ row_filter_body | column_mask_body }
```

- 행 필터 본문: `ROW FILTER function_name`, `TO principal`, `FOR TABLES`, `[WHEN condition]`, `[MATCH COLUMNS condition AS alias]`, `[USING COLUMNS (...)]`
- 열 마스크 본문: `COLUMN MASK function_name`, `TO principal`, `FOR TABLES`, `[WHEN condition]`, `[MATCH COLUMNS condition AS alias]`, `ON COLUMN alias`, `[USING COLUMNS (...)]`

> **참고** `TO` 절에는 사용자, 그룹, 서비스 프린시펄을 쓸 수 있습니다. 공식 문서는 `TO`와 `EXCEPT` 절을 합쳐 주체 수를 20개로 제한한다고 설명합니다.

### 정책 설계 예 (GRANT 정책)

공식 문서 예제는 분석 스키마에서 금융 태그가 붙은 MCP 서비스에 실행 권한을 주는 정책입니다.

```sql
CREATE POLICY grant_finance_mcp_services
ON SCHEMA analytics.tools
COMMENT 'Grant EXECUTE on finance MCP services'
TO `analysts`
GRANT EXECUTE FOR MCP SERVICES
WHEN has_tag_value('domain', 'finance');
```

GRANT 정책에는 다음 제약이 있습니다. 공식 문서 원문을 옮깁니다.

- `ALL_PRIVILEGES`와 `MODIFY`는 GRANT 정책에서 지원하지 않습니다.
- `USE CATALOG`와 `USE SCHEMA`는 GRANT 정책으로 줄 수 없고 직접 부여해야 합니다.
- GRANT 정책으로 받은 권한은 `SHOW GRANTS`에 나오지 않습니다.
- GRANT 정책이 걸린 모델은 Delta Sharing(공식 문서의 현재 명칭은 OpenSharing)으로 공유할 수 없습니다.

### 정책 목록과 삭제

정책의 생성, 수정, 조회, 삭제는 카탈로그 탐색기, SQL, REST API로 할 수 있다고 공식 문서가 설명합니다. 이 페이지에서는 SQL 예제만 다루었습니다. 삭제 문법은 원문 정책 관리 페이지에서 직접 확인하십시오.

## 4. 트레이드오프

### 한도

공식 문서의 자원 한도 페이지에서 확인한 정책 관련 한도입니다.

| 항목 | 한도 | 범위 |
|---|---|---|
| 정책 | 10,000 | 메타스토어 (모든 객체) |
| 정책 | 100 | 메타스토어 직접 부착 (Beta) |
| 정책 | 100 | 카탈로그 |
| 정책 | 100 | 스키마 |
| 정책 | 50 | 테이블 |
| 주체 | 20 | 정책 1개(`TO`와 `EXCEPT` 합계) |
| `MATCH COLUMNS` 조건 | 행 필터 6개, 열 마스크 3개 | 절 1개 |

GRANT 정책과 DENY 정책은 객체 하나에서 한 가지 합산 한도를 공유하며, 행 필터와 열 마스크의 한도와는 별도라고 공식 문서가 설명합니다.

태그 한도는 다음과 같습니다.

| 항목 | 한도 |
|---|---|
| 거버넌스 태그 | 계정당 1,000개 |
| 거버넌스 태그별 허용 값 | 500개 |
| 객체 하나에 붙는 태그 할당 | 50개 |
| 테이블 하나의 열 태그 합계 | 1,000개 |
| 태그 키·값 최대 길이 | 256자 |

### 상태 요약

ABAC 관련 기능은 상태가 세분화되어 있습니다. 공식 문서와 릴리즈 노트에서 확인한 항목입니다.

| 기능 | 상태 | 확인 자료 |
|---|---|---|
| 교차 엔진 ABAC(Cross-engine ABAC) | GA (2026-10-01) | 릴리즈 노트 |
| ABAC GRANT 정책: 모델·서비스 | GA (2026-08-31) | 릴리즈 노트 |
| 메타스토어 수준 ABAC 정책 | Beta | 정책 페이지 |
| ABAC 정책을 뷰에 적용 | Beta (2026-09-29 공지) | 정책 페이지, 릴리즈 노트 |
| DENY 정책 | Beta | 정책 페이지 |
| 시간 여행(Time travel) 쿼리의 ABAC 강제 | Beta | 릴리즈 노트 |
| 컨텍스트 속성, 신원 속성(열 마스크) | Beta | 릴리즈 노트 |
| 거버넌스 태그 전파(tag propagation) | Beta (2026-10-12 공지) | 릴리즈 노트 |
| 태그 자동화(Tag automations) | Beta (2026-08-07 공지) | 릴리즈 노트 |
| 행 필터와 열 마스크(테이블 대상) | 문서에 상태 라벨 없음 | 정책 페이지 |

> **참고** "문서에 상태 라벨 없음"은 GA라는 뜻이 아닙니다. 정책 페이지가 Beta로 표기한 범위(메타스토어 정책, 뷰, DENY)를 제외한 나머지 정책 기능에 대해 원문이 상태를 명시하지 않았다는 뜻입니다.

### 언제 태그 기반 정책을 쓰지 않는가

- 테이블이 몇 개뿐이고 규칙이 한 번만 필요한 경우에는 [행 필터와 열 마스크](row-filters-and-column-masks.md)의 테이블 단위 방식이 단순합니다.
- 태그를 설계하고 붙이는 프로세스가 없으면 정책은 아무것도 걸지 못합니다. 태그 부여가 사람에게만 달려 있다면 자동 분류(「계보와 데이터 분류」 페이지)와 함께 설계해야 합니다.
- Beta 범위(뷰, 메타스토어 수준, DENY)에 운영 보안을 의존하면 기능 변경의 영향을 받을 수 있습니다.

## 5. 주의사항

> **주의** 공식 문서의 거버넌스 태그 문자 제한은 `* . / < > % & ? \ =` 와 ASCII 제어 문자(0–31)입니다. 일반 태그 키 페이지는 `. , - = / :`를 금지 문자로 나열합니다. 두 페이지의 목록이 다르므로 태그 키를 정할 때는 양쪽 조건을 모두 피하십시오.

> **주의** 태그 키와 값은 대소문자를 구분합니다. 앞뒤 공백은 허용되지 않습니다. 태그를 잘못 쓰면 정책이 조용히 적용되지 않을 수 있으니, 정책 적용 결과를 테스트 계정으로 확인하십시오.

> **주의** 정책 조건(`has_tag`, `has_tag_value`)은 태그 이름과 값이 정확히 맞아야 합니다. 오타가 있으면 정책이 대상을 찾지 못합니다.

- 태그 체계는 조직 단위로 먼저 정하고, 허용 값 목록을 문서화합니다. 허용 값은 나중에 바꾸기 어렵습니다.
- 민감 데이터 태그(`class.*`)는 시스템 태그를 쓰고, 조직 고유 분류는 거버넌스 태그를 새로 정의합니다.
- 정책 한도(테이블 50개, 스키마와 카탈로그 각 100개)를 넘지 않도록 정책을 범위별로 묶습니다.
- 행 필터 정책이 여러 개 겹치면 평가 순서와 결과를 테스트하십시오. 뷰에서는 한 쿼리에 최대 20개 정책이 겹칠 수 있고, 그 이상이면 쿼리가 실패합니다. 이 한도는 뷰 ABAC(Beta)에 적용됩니다.
- 정책을 적용하려면 대상 객체에 `MANAGE`(또는 소유권)와 구현 함수에 `EXECUTE`가 필요합니다. 공식 문서는 Databricks Runtime 16.4 이상 또는 서버리스 컴퓨트를 요구합니다.

## 참고 문서

- [ABAC core concepts](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/)
- [Create and manage row filter and column mask policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/policies)
- [ABAC GRANT policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/grant-policies)
- [ABAC DENY policies (Beta)](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/deny-policies)
- [Metastore-level ABAC policies (Beta)](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/metastore-policies)
- [Requirements, quotas, and limitations for row filter and column mask policies](https://docs.databricks.com/aws/en/data-governance/unity-catalog/abac/requirements)
- [Governed tags](https://docs.databricks.com/aws/en/admin/governed-tags/)
- [Unity Catalog resource limits](https://docs.databricks.com/aws/en/resources/limits)
- [Tags (SET TAG, UNSET TAG)](https://docs.databricks.com/aws/en/database-objects/tags)
