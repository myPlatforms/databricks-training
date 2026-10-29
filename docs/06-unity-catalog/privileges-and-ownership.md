# 권한 모델과 소유권

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

UC의 권한 모델은 **모든 securable 객체는 소유자(owner)를 가지며, 소유자나 권한을 위임받은 주체가 `GRANT`로 다른 주체에게 권한을 준다** 는 구조입니다. 권한은 객체에 붙고, 주체(사용자, 서비스 프린시펄, 그룹)에게 부여됩니다. 노트북이나 클러스터의 설정이 권한을 결정하지 않습니다.

이 페이지는 다음 네 가지를 다룹니다.

- 소유권: 누가 객체를 소유하고, 소유권을 어떻게 넘기는가
- 상속: 상위 객체에 준 권한이 하위 객체에 어떻게 적용되는가
- `GRANT`·`REVOKE`: 권한을 주고 회수하는 기본 문법과 요구 사항
- 주체: 사용자, 서비스 프린시펄, 그룹을 어떻게 구분하고 쓰는가

## 1. 왜 필요한가

### 이전 방식의 한계

워크스페이스별 권한 모델에서는 같은 테이블이라도 워크스페이스마다 권한이 달랐습니다. 노트북을 실행하는 클러스터의 접근 모드에 따라 결과가 바뀌는 경우도 있었습니다. 감사 담당자가 "이 사람이 이 테이블을 읽을 수 있는가"를 확인하려면 여러 곳을 뒤져야 했습니다.

UC는 권한을 **객체 계층에 한 번만 정의** 하도록 합니다. 권한을 어디서 실행하든 같은 결과가 나오고, `SHOW GRANTS`로 한 객체의 권한 목록을 확인할 수 있습니다.

### 그룹 중심 설계가 필요한 이유

사용자마다 `GRANT`를 주면 인원이 바뀔 때마다 권한을 고쳐야 합니다. 공식 문서 예제도 `finance-team`, `ml-team-acme` 같은 **그룹** 을 권한 대상으로 씁니다. 따라서 개인이 아니라 그룹에 권한을 주고, 사람은 그룹에 넣고 빼는 방식이 기본 설계입니다.

## 2. 어떻게 동작하는가

### 소유권

공식 문서의 소유권 규칙은 다음과 같습니다.

- 모든 securable 객체는 소유자를 가집니다. 소유자는 그 객체의 모든 권한을 가지며, 다른 주체에게 권한을 줄 수 있습니다.
- 권한은 다음 주체가 부여할 수 있습니다.
  - 객체의 소유자
  - 그 객체를 담고 있는 카탈로그나 스키마의 소유자
  - 그 객체에 `MANAGE` 권한을 가진 사용자
  - 메타스토어 관리자(metastore admin)
- 메타스토어 수준에서는 계정 관리자(account admin)도 권한을 직접 부여할 수 있다고 공식 문서가 설명합니다.

소유권 이전(`ALTER ... OWNER TO`)에도 규칙이 있습니다.

| 대상 객체 | 이전 가능한 주체 |
|---|---|
| 일반 객체 | 현재 소유자, 메타스토어 관리자, 상위 컨테이너 소유자, `MANAGE` 보유자 |
| 뷰, 함수, 모델 | 메타스토어 관리자만 임의의 주체로 이전 가능. 다른 소유자나 `MANAGE` 보유자는 자기 자신 또는 자기가 속한 그룹으로만 이전 가능 |
| OpenSharing 공유(Share) | 메타스토어 관리자만 이전 가능 |

> **참고** 공식 문서는 뷰를 그룹에 넘기면 협업 편집이 가능해진다고 팁으로 설명합니다. 뷰 소유자를 개인에서 그룹으로 바꾸는 것이 실무에서 자주 쓰는 패턴입니다.

> **주의** Lakeflow 파이프라인으로 만든 구체화된 뷰(materialized view)와 스트리밍 테이블은 소유권을 직접 이전할 수 없습니다. 공식 문서는 이 경우 파이프라인의 실행 사용자(run-as user)를 바꾸라고 안내합니다.

### 상속

공식 문서의 권한 모델 개념 페이지는 상속을 다루지만, 이 장에서 확인한 페이지 중에는 상속 규칙을 한 문장으로 정리한 원문이 없었습니다. 확인된 사실은 다음과 같습니다.

| 확인된 사실 | 출처 |
|---|---|
| 메타스토어 수준에서 부여한 권한은 하위 객체로 상속되지 않습니다. | 객체 종류 페이지: "Privileges granted at the metastore level do not inherit to child objects in the hierarchy." |
| 카탈로그나 스키마의 소유자는 그 안에 있는 객체에 대해 권한을 줄 수 있습니다. | 권한 관리 페이지 |
| `CREATE VOLUME` 권한을 카탈로그에 주면 그 카탈로그의 기존 스키마와 앞으로 만들어질 스키마에 볼륨을 만들 수 있습니다. | 권한 참조 페이지 |

> **참고** 카탈로그에 `SELECT`를 주었을 때 그 아래 모든 테이블이 자동으로 읽히는지는 이 장에서 확인한 원문에 명시되어 있지 않습니다. 상속 규칙의 정확한 범위는 공식 문서의 "Unity Catalog permissions model concepts" 페이지에서 직접 확인하십시오. 이 장에서는 그 확인을 하지 않았으므로 상속 범위를 단정하지 않습니다.

### 필수 권한 조합

`SELECT`를 주는 것만으로는 테이블을 읽을 수 없습니다. 공식 문서의 권한 참조 페이지는 다음을 명시합니다.

> "The user must also have `USE CATALOG` on the parent catalog and `USE SCHEMA` on the parent schema."

즉 테이블에 `SELECT`가 있어도 상위 카탈로그에 `USE CATALOG`, 상위 스키마에 `USE SCHEMA`가 없으면 접근할 수 없습니다. `USE CATALOG`와 `USE SCHEMA`는 객체 접근 권한이 아니라 진입 권한으로 쓰입니다. 공식 문서도 두 권한이 카탈로그나 스키마의 내용에 접근할 권한을 주지는 않는다고 설명합니다.

> **참고** 2026년 8월 3일 릴리즈 노트는 "`MANAGE` no longer requires `USE CATALOG` or `USE SCHEMA` on the same object"라는 변경을 공지했습니다. `MANAGE`에 대한 요구 사항이 바뀌었으므로, `SELECT`와 `USE` 권한 요구 사항과는 구분해서 이해하십시오. 상태 라벨은 릴리즈 노트에 명시되어 있지 않습니다.

### 권한 종류

공식 문서의 권한 참조 페이지가 나열하는 권한 가운데 자주 쓰는 것은 다음과 같습니다.

| 권한 | 적용 대상 | 허용하는 것 | 상태 |
|---|---|---|---|
| `SELECT` | 테이블, 뷰, 구체화된 뷰, 공유 | 객체를 조회합니다. 공유에 대해서는 수신자가 공유에서 조회하도록 합니다. | 문서에 상태 라벨 없음 |
| `USE CATALOG` | 카탈로그 | 카탈로그 안의 객체와 상호작용하는 데 필요합니다. 카탈로그나 객체 데이터에 대한 접근 권한은 주지 않습니다. | 문서에 상태 라벨 없음 |
| `USE SCHEMA` | 스키마 | 스키마 안의 객체와 상호작용하는 데 필요합니다. 스키마나 객체 데이터에 대한 접근 권한은 주지 않습니다. | 문서에 상태 라벨 없음 |
| `MANAGE` | Clean Room, 연결, 외부 위치, 테이블, 볼륨 등 다수 | 소유하지 않아도 권한을 관리하고, 소유권을 이전하고, 이름을 바꾸고, 삭제합니다. `ALL PRIVILEGES`에는 포함되지 않습니다. | 문서에 상태 라벨 없음 |
| `READ METADATA` | 대부분의 객체, 메타스토어, 스키마, 카탈로그 | 데이터를 읽지 않고 소유자 수준 메타데이터(권한, 행 필터, 열 마스크, ABAC 정책)를 봅니다. | GA (릴리즈 노트 2026-08-10) |
| `BROWSE` | Clean Room, 외부 위치, 외부 메타데이터 | `USE CATALOG`나 `USE SCHEMA` 없이 객체를 찾고 메타데이터를 봅니다. | 문서에 상태 라벨 없음 |
| `APPLY TAG` | 테이블, 뷰, 볼륨, 모델, 시크릿 등 | 태그를 추가하고 수정합니다. 테이블과 뷰에서는 열 태그도 포함합니다. | 문서에 상태 라벨 없음 |
| `EXECUTE` | 함수 | 함수를 호출하거나 등록된 모델로 추론합니다. 정의와 메타데이터도 봅니다. | 문서에 상태 라벨 없음 |
| `READ VOLUME` / `WRITE VOLUME` | 볼륨 | 볼륨의 파일을 읽거나, 추가·수정·삭제합니다. | 문서에 상태 라벨 없음 |
| `CREATE VOLUME` | 스키마, 카탈로그 | 스키마나 카탈로그 안에 볼륨을 만듭니다. | 문서에 상태 라벨 없음 |
| `INSERT`, `UPDATE`, `DELETE` | 테이블 | 테이블 데이터를 추가, 수정, 삭제합니다. | Beta |

> **주의** `INSERT`, `UPDATE`, `DELETE`는 Beta입니다. 운영 권한 설계에 넣기 전에 해당 워크스페이스에서 기능이 열려 있는지 확인하십시오.

> **주의** 권한 목록의 `MANAGE`는 "관리자 권한"이 아닙니다. 객체를 소유하지 않아도 권한을 바꿀 수 있으므로, 개발자에게 넓게 주면 권한 체계가 빠르게 흐트러집니다.

## 3. 어떻게 쓰는가

### 권한 부여와 회수

공식 문서 예제를 기준으로 한 기본 형태입니다.

```sql
-- 스키마 권한 확인
SHOW GRANTS ON SCHEMA main.default;

-- 그룹에 테이블 생성, 스키마 진입, 카탈로그 진입 권한 부여
GRANT CREATE TABLE ON SCHEMA main.default TO `finance-team`;
GRANT USE SCHEMA ON SCHEMA main.default TO `finance-team`;
GRANT USE CATALOG ON CATALOG main TO `finance-team`;

-- 함수(등록된 모델 포함)에 실행 권한 부여
GRANT EXECUTE ON FUNCTION prod.ml_team.iris_model TO `ml-team-acme`;

-- 권한 회수
REVOKE CREATE TABLE ON SCHEMA main.default FROM `finance-team`;
```

> **참고** 등록된 모델(registered model)은 함수로 구현되어 있으므로 모델 권한은 `GRANT ... ON FUNCTION`으로 부여합니다. 공식 문서 예제도 같은 형태입니다.

> **참고** 공식 문서는 `REVOKE`가 실제로 부여되지 않은 권한에 대해서도 성공한다고 설명합니다. 회수 명령이 성공했다고 해서 권한이 실제로 있었던 것은 아닙니다. 권한 상태는 `SHOW GRANTS`로 확인하십시오.

### 메타스토어 수준 권한

```sql
GRANT <privilege-type> ON METASTORE TO <principal>;
REVOKE <privilege-type> ON METASTORE FROM <principal>;
SHOW GRANTS [principal] ON METASTORE
```

위 문법에서 `<privilege-type>`과 `<principal>`은 공식 문서의 자리표시자입니다. 실제 값은 권한 참조 페이지에서 확인해 넣으십시오.

### 소유자 확인과 이전

```sql
-- 객체의 상세 정보(소유자 포함) 확인
DESCRIBE TABLE EXTENDED mycatalog.myschema.orders;

-- 테이블 소유권을 그룹으로 이전
ALTER TABLE mycatalog.myschema.orders OWNER TO `accounting`;
```

공식 문서의 소유권 이전 형식은 `ALTER <securable-type> <securable-name> OWNER TO <principal>`입니다. 위 예는 테이블의 경우를 쓴 것입니다.

### 주체 이름 쓰기

| 주체 종류 | 식별 방법 | 예 |
|---|---|---|
| 사용자 | 계정에 등록된 사용자 이름 | `user@example.com` (예시) |
| 그룹 | 그룹 이름 | `` `finance-team` `` |
| 서비스 프린시펄 | 공식 문서는 `applicationId` 값으로 참조한다고 설명합니다. | `` `<application-id>` `` (자리표시자) |

> **참고** 이름에 특수 문자가 있으면 백틱으로 감쌉니다. 서비스 프린시펄은 이름 대신 `applicationId` 값으로 지정하는 것이 공식 문서의 설명입니다.

### 권한 목록 점검

```sql
-- 현재 사용자가 볼 수 있는 권한 목록
SHOW GRANTS ON TABLE main.sales.orders;

-- 메타스토어 수준 권한 목록(주체 지정 형식은 SHOW GRANTS [principal] ON METASTORE)
SHOW GRANTS ON METASTORE;
```

> **주의** `MANAGE` 권한만 가진 사용자는 `INFORMATION_SCHEMA`에서 자기 자신의 권한만 보입니다. 공식 문서는 전체 권한을 보려면 SQL이나 카탈로그 탐색기(Catalog Explorer)를 쓰라고 안내합니다. 권한 점검을 `INFORMATION_SCHEMA`만으로 하면 누락이 생깁니다.

## 4. 트레이드오프

### 객체별 GRANT와 정책 기반 접근의 선택

| 방식 | 장점 | 한계 |
|---|---|---|
| 객체별 `GRANT` | 명시적이고 단순하며 감사하기 쉽습니다. | 객체 수가 많아지면 관리 비용이 커집니다. 새 객체마다 권한을 따로 줘야 합니다. |
| 태그 기반 정책(ABAC) | 태그가 붙은 모든 객체에 정책이 자동 적용됩니다. | 태그 설계와 정책 조건을 먼저 정해야 합니다. 상태 라벨이 Beta인 범위가 남아 있습니다. [거버넌스 태그와 ABAC 정책](governed-tags-and-abac.md) 참고. |

실무에서는 두 방식을 섞습니다. 그룹과 기본 진입 권한(`USE CATALOG`, `USE SCHEMA`)은 객체별로 명시하고, 민감 데이터 보호는 태그 기반 정책으로 자동화하는 구성이 흔합니다.

### 소유자 중심 설계의 장단점

| 항목 | 장점 | 단점 |
|---|---|---|
| 개인 소유 | 누가 만들었는지 명확합니다. | 사람이 퇴사하거나 이동하면 소유권 이전 작업이 필요합니다. |
| 그룹 소유 | 사람 변경과 무관하게 관리가 이어집니다. | 그룹의 구성원이 많으면 책임 범위가 흐려집니다. |

## 5. 주의사항

> **주의** 권한을 회수하기 전에 그 권한을 쓰는 소비자(노트북, 잡, 대시보드, Genie 공간, 다른 리포의 코드)가 있는지 먼저 확인하십시오. 권한을 줄이면 소비자가 조용히 실패하고, 실패 원인을 찾기 어렵습니다.

- 권한은 그룹에 주고, 그룹 구성은 신원 제공자(IdP)나 계정 콘솔에서 관리하는 것을 권장합니다.
- 서비스 프린시펄은 자동화 작업의 실행 주체로 쓰고, 사람 계정에 자동화를 묶지 않습니다.
- `ALL PRIVILEGES`는 `MANAGE`를 포함하지 않는다는 점을 기억하십시오. 공식 문서는 `MANAGE`를 `ALL PRIVILEGES`에 포함하지 않는다고 설명합니다.
- 권한 변경은 코드(예: 잡이나 DAB 설정)로 관리해 감사 이력을 남기는 것을 권장합니다.

## 참고 문서

- [Manage privileges in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/)
- [Unity Catalog privileges and securable objects](https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/privileges)
- [Securable objects in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/securable-objects)
- [Access control in Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/)
