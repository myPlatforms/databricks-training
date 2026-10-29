# ID와 접근

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Databricks에서 ID는 세 종류입니다. **사용자**(User, 이메일로 식별), ** 서비스 프린시펄**(Service principal, 잡·도구·CI/CD용 비인간 ID), ** 그룹**(Group, 접근 권한을 묶는 단위)입니다. 계정 수준에서 이 ID를 만들고, 워크스페이스에는 필요한 ID만 배정하는 방식이 권장됩니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 워크스페이스마다 사용자를 따로 만들면 같은 사람이 워크스페이스 수만큼 다른 계정으로 존재합니다.
- 그룹이 워크스페이스 로컬이면 여러 워크스페이스에 걸친 권한 정의가 중복됩니다.
- 사용자 추가와 제거가 사람이 하는 수작업이면 누락과 지연이 생깁니다.

Databricks는 계정 수준 ID 관리로 이 문제를 줄입니다. 계정 관리자가 ID를 한 번 만들고, 여러 워크스페이스에 배정합니다.

## 2. 어떻게 동작하는가

### 계정 수준 ID 관리

공식 문서 기준으로 계정은 사용자와 서비스 프린시펄을 합쳐 최대 10,000개, 그룹은 최대 5,000개를 지원합니다.

ID 연동(Identity federation)이 켜진 워크스페이스에서는 관리자가 계정에 이미 있는 ID 중에서 골라 배정합니다. 이 설정은 새 워크스페이스에 기본으로 켜지며, 문서는 끌 수 없다고 명시합니다.

레거시 워크스페이스(ID 연동이 없는 워크스페이스)는 사용자와 서비스 프린시펄을 워크스페이스에서 직접 추가하고, 그 ID는 계정에도 추가됩니다. 이메일 주소가 계정의 기존 사용자와 같으면 두 ID가 병합됩니다. 이 워크스페이스의 그룹은 워크스페이스 로컬 그룹이며 계정에 올라가지 않습니다.

워크스페이스 페이지의 **Identity federation: Enabled** 라벨로 연동 상태를 확인할 수 있습니다. 연동을 켜려면 계정 관리자가 Unity Catalog 메타스토어를 워크스페이스에 할당해야 합니다.

| 항목 | 계정 수준 ID (ID 연동 워크스페이스) | 워크스페이스 로컬 ID (레거시) |
|---|---|---|
| 생성 위치 | 계정 콘솔 | 워크스페이스 |
| 그룹의 범위 | 계정 전체, 여러 워크스페이스에 배정 가능 | 해당 워크스페이스 안에서만 |
| 계정 관리자의 가시성 | 전체 | 워크스페이스에서 추가된 ID도 계정에 올라감 |

### 프로비저닝과 인증 방식

| 방식 | 설명 (문서 기준) |
|---|---|
| 자동 ID 관리 (Automatic identity management) | 문서가 권장하는 동기화 방식. Microsoft Entra ID와 Okta를 지원하며 IdP가 원본(source of record) |
| SCIM 프로비저닝 | 자동 ID 관리를 쓸 수 없는 IdP에서 사용하는 대체 방식 |
| SSO (Single sign-on) | 제3자 IdP로 사용자를 인증 |
| JIT 프로비저닝 (Just-in-time) | 사용자가 SSO로 처음 로그인할 때 계정을 자동 생성 |

### 역할 구분

| 역할 | 권한 |
|---|---|
| 계정 관리자 | 계정 수준 사용자·서비스 프린시펄·그룹의 추가, 수정, 삭제, 워크스페이스 접근 부여 |
| 워크스페이스 관리자 | 계정에 ID를 추가하고 해당 워크스페이스 접근을 부여. 계정 사용자·서비스 프린시펄은 수정·삭제 불가 |

### 아이덴티티 속성 (Beta)

사용자에 직책, 부서, 비용 센터 같은 속성을 저장해 접근 정책에 쓸 수 있는 기능입니다. 상태는 **Beta** 입니다. 구체적인 사용 예는 [Unity Catalog 행 필터와 열 마스크](../06-unity-catalog/row-filters-and-column-masks.md)를 참고하십시오.

## 3. 어떻게 쓰는가

### 서비스 프린시펄을 만들고 권한을 주는 흐름

잡이나 CI/CD가 쓸 서비스 프린시펄은 사람 계정으로 실행하지 않는 것이 원칙입니다. 계정 콘솔에서 서비스 프린시펄을 만든 뒤 워크스페이스에 배정하고, Unity Catalog에서 필요한 권한만 부여합니다.

```sql
-- 서비스 프린시펄을 워크스페이스에 배정한 뒤 실행합니다.
-- 'my-service-principal'은 applicationId 값이 아니라 표시 이름으로 대체해 쓰십시오.
GRANT USE CATALOG ON CATALOG main TO `my-service-principal`;
GRANT USE SCHEMA ON SCHEMA main.sales TO `my-service-principal`;
GRANT SELECT ON TABLE main.sales.orders TO `my-service-principal`;
```

> **참고** 위 GRANT 예시는 Unity Catalog 권한 구문입니다. 표시 이름에 하이픈이 있으면 백틱으로 감쌉니다. 권한 모델의 전체 구조는 [권한 모델과 소유권](../06-unity-catalog/privileges-and-ownership.md)에서 다룹니다.

### 그룹으로 권한 묶기

개별 사용자에게 GRANT하지 말고 그룹에 GRANT한 뒤 그룹에 사용자를 넣는 방식이 관리하기 쉽습니다.

```sql
GRANT SELECT ON SCHEMA main.sales TO `analysts`;
```

그룹 멤버 변경은 계정 콘솔이나 SCIM으로 처리하면 SQL 권한 문장을 바꿀 필요가 없습니다.

### 서비스 프린시펄 ACL

서비스 프린시펄을 어떤 사용자나 그룹이 쓸 수 있는지는 서비스 프린시펄 ACL(Service principal ACL) 페이지에서 설정합니다. 이 장에서는 설정 위치만 소개하며, 세부 권한 값은 원문 페이지에서 확인하십시오.

## 4. 트레이드오프

| 방식 | 장점 | 제약 |
|---|---|---|
| 자동 ID 관리 | IdP가 원본이 되어 수작업이 줄어듦 | 문서가 지원 IdP로 Microsoft Entra ID와 Okta를 명시. 그 외 IdP는 SCIM으로 대체 |
| SCIM | 자동 ID 관리를 쓸 수 없을 때의 대체 방식 | 동기화 주기와 실패 처리를 직접 점검해야 함 |
| JIT 프로비저닝 | 로그인 시점에 계정이 생김 | 문서 범위에서 퇴사 시 제거 방식은 확인하지 못함. 퇴사 처리 절차를 별도로 마련해야 함 |
| 워크스페이스 로컬 그룹 | 워크스페이스 단위로 독립 운영 가능 | 계정 전체 권한 점검이 어려움 |

## 5. 주의사항

- **퇴사 처리는 IdP에서 비활성화하는 것부터 시작하십시오.** 자동 ID 관리와 SCIM은 IdP를 원본으로 삼는 방식입니다. JIT로 만들어진 계정의 제거 동작은 이 장에서 확인하지 못했으므로 원문을 확인하십시오.
- **서비스 프린시펄을 개인 계정처럼 쓰지 마십시오.** 잡과 도구는 서비스 프린시펄로 인증하고, 사용자 권한은 그룹으로 주십시오.
- **레거시 워크스페이스는 ID 연동 상태를 먼저 확인하십시오.** 이메일이 같은 계정이 병합되는 동작을 모르고 옮기면 권한이 예상과 다르게 합쳐질 수 있습니다.
- **그룹 이름 변경은 권한 영향을 확인하십시오.** 그룹을 이름으로 참조하는 GRANT 문이 있는지 먼저 점검하십시오.
- **계정 수준 ID 한도(사용자·서비스 프린시펄 합계 10,000, 그룹 5,000)를 대규모 도입 시 확인하십시오.**

> **참고** 사용자 상태(비활성, 삭제)가 감사 로그와 데이터 소유권에 미치는 영향은 문서에서 이 페이지 범위로 확인하지 못했습니다. 실제 운영 전 계정 콘솔의 해당 설정을 직접 확인하십시오.

## 참고 문서

- [Identity management](https://docs.databricks.com/aws/en/admin/users-groups/)
- [Identity management best practices](https://docs.databricks.com/aws/en/admin/users-groups/best-practices)
- [Automatic identity management](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)
- [SCIM provisioning](https://docs.databricks.com/aws/en/admin/users-groups/scim/)
- [Configure SSO in Databricks](https://docs.databricks.com/aws/en/security/auth/single-sign-on/)
- [Automatically provision users (JIT)](https://docs.databricks.com/aws/en/security/auth/jit)
- [Access control](https://docs.databricks.com/aws/en/security/auth/access-control/)
- [Identity attributes (Beta)](https://docs.databricks.com/aws/en/admin/users-groups/identity-attributes/)
