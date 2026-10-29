# ID와 접근

> 기준일: 2026-10-29 · 근거: 공식 문서

## 한눈에 보기

Databricks에서 ID는 세 종류입니다. **사용자**(User, 이메일로 식별), **서비스 프린시펄**(Service principal, 잡·도구·CI/CD용 비인간 ID), **그룹**(Group, 접근 권한을 묶는 단위)입니다. 계정 수준에서 이 ID를 만들고, 워크스페이스에는 필요한 ID만 배정하는 방식이 권장됩니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 워크스페이스마다 사용자를 따로 만들면 같은 사람이 워크스페이스 수만큼 다른 계정으로 존재합니다.
- 그룹이 워크스페이스 로컬이면 여러 워크스페이스에 걸친 권한 정의가 중복됩니다.
- 사용자 추가와 제거가 사람이 하는 수작업이면 누락과 지연이 생깁니다. 퇴사자의 접근이 남는 것이 가장 흔한 결과입니다.

Databricks는 계정 수준 ID 관리로 이 문제를 줄입니다. 계정 관리자가 ID를 한 번 만들고, 여러 워크스페이스에 배정합니다. 문서는 IdP의 사용자와 그룹을 계정 콘솔에 동기화하면 "일관된 퇴사 절차(consistent offboarding)"가 보장되고 "권한 없는 사용자가 민감한 데이터에 접근하는 것"을 막을 수 있다고 설명합니다.

## 2. 어떻게 동작하는가

### 2.1 계정 수준 ID 관리

계정은 사용자와 서비스 프린시펄을 합쳐 최대 **10,000개**, 그룹은 최대 **5,000개** 를 지원합니다. 워크스페이스도 같은 한도를 가집니다.

ID 연동(Identity federation)이 켜진 워크스페이스에서는 관리자가 계정에 이미 있는 ID 중에서 골라 배정합니다. 문서는 이 설정이 새 워크스페이스에 기본으로 켜지며 끌 수 없다고 명시합니다. 원문은 "Databricks enables identity federation by default for all new workspaces, and you cannot disable it."입니다.

레거시 워크스페이스(ID 연동이 없는 워크스페이스)는 사용자와 서비스 프린시펄을 워크스페이스에서 직접 추가하고, 그 ID는 계정에도 추가됩니다. 이메일 주소가 계정의 기존 사용자와 같으면 두 ID가 병합됩니다. 이 워크스페이스의 그룹은 워크스페이스 로컬 그룹이며 계정에 올라가지 않습니다.

워크스페이스 페이지의 **Identity federation: Enabled** 라벨로 연동 상태를 확인할 수 있습니다. 연동을 켜려면 계정 관리자가 Unity Catalog 메타스토어를 워크스페이스에 할당해야 합니다.

| 항목 | 계정 수준 ID (ID 연동 워크스페이스) | 워크스페이스 로컬 ID (레거시) |
|---|---|---|
| 생성 위치 | 계정 콘솔 | 워크스페이스 |
| 그룹의 범위 | 계정 전체, 여러 워크스페이스에 배정 가능 | 해당 워크스페이스 안에서만 |
| 계정 관리자의 가시성 | 전체 | 워크스페이스에서 추가된 ID도 계정에 올라감 |

### 2.2 프로비저닝과 인증 방식

| 방식 | 설명 (문서 기준) |
|---|---|
| 자동 ID 관리 (Automatic identity management) | 문서가 권장하는 동기화 방식. Microsoft Entra ID와 Okta를 지원하며 IdP가 원본(source of record) |
| SCIM 프로비저닝 | 자동 ID 관리를 쓸 수 없는 IdP에서 사용하는 대체 방식. 계정 수준 커넥터로 사용자와 그룹을 동기화 |
| SSO (Single sign-on) | 제3자 IdP로 사용자를 인증 |
| JIT 프로비저닝 (Just-in-time) | 사용자가 SSO로 처음 로그인할 때 계정을 자동 생성 |

#### 자동 ID 관리 (AIM)

| 항목 | 문서 기준 |
|---|---|
| 원본 (source of record) | IdP. IdP의 사용자와 그룹 변경이 Databricks에 반영됨 |
| 지원 IdP | Microsoft Entra ID, Okta |
| 서비스 프린시펄·중첩 그룹 동기화 | Entra ID만 지원. Okta는 "Okta does not support service principal or nested group sync." |

그룹 멤버십은 로그인, 토큰 인증, 잡 실행 같은 활동 때 IdP에서 새로 가져옵니다. 중첩 멤버십은 전이적으로(transitive) 가져오며, Databricks에 추가된 그룹의 멤버십만 가져옵니다. 새로 고침 시점은 활동에 따라 다릅니다.

| 활동 | 새로 고침 기준 |
|---|---|
| 브라우저 로그인 | 마지막 동기화 후 5분 초과 |
| 토큰 인증, 잡 실행 등 그 밖의 활동 | 마지막 동기화 후 10분 미만이면 새로 고침 없음 |
| 그 밖의 활동 | 10~40분 경과 시 비동기로 새로 고침 |
| 그 밖의 활동 | 40분 초과 경과 시 요청이 끝나기 전에 새로 고침 |

IdP에서 삭제된 사용자는 **Active: Removed From [IdP]** 상태가 됩니다(예: "Active: Removed From EntraID"). 이 상태에서는 로그인하거나 API로 인증할 수 없으며, 다음 동기화에서 Databricks가 비활성화합니다. 문서는 해당 사용자의 개인 액세스 토큰도 폐기하라고 권장합니다.
자동 ID 관리를 끄면 사용자와 서비스 프린시펄은 남지만, 그룹 멤버가 제거되고 IdP 변경 동기화는 멈춥니다.

#### SCIM 프로비저닝

SCIM은 자동 ID 관리를 쓸 수 없을 때의 대체 방식입니다. 필요 조건은 Premium 플랜 이상과 계정 관리자 역할입니다. SSO는 권장되지만 필수는 아닙니다.

계정 콘솔의 **Security** → **Identity provider setup** 탭에서 **Identity management** 절의 **Enable user provisioning** 을 누릅니다. 표시되는 SCIM 토큰과 Account SCIM URL을 IdP SCIM 커넥터의 SAML 프로비저닝 URL과 프로비저닝 API 토큰으로 입력합니다.

토큰을 바꿀 때는 **Regenerate token** 을 누르고 새 토큰을 저장합니다. 이전 토큰은 24시간 동안 유효하므로 그 안에 SCIM 애플리케이션을 갱신하십시오.

SCIM이 할 수 있는 것과 없는 것은 다음과 같습니다.

| 구분 | 내용 |
|---|---|
| 동기화 가능 | 사용자와 그룹을 계정으로 |
| 동기화 불가 | Microsoft Entra ID 서비스 프린시펄, 중첩 그룹 (이 둘은 자동 ID 관리 사용) |
| 서비스 프린시펄 | "SCIM provisioning does not support syncing service principals." |
| 속성 (Beta) | 계정 SCIM 2.1은 `title`, `department`, `costCenter` 같은 고정 속성을 계정 사용자에게 프로비저닝 가능. 활용 예는 [Unity Catalog 행 필터와 열 마스크](../06-unity-catalog/row-filters-and-column-masks.md) 참고 |

> **주의** 계정 수준 커넥터를 켜면 워크스페이스에 직접 동기화하던 워크스페이스 수준 SCIM 커넥터를 끄십시오. 워크스페이스 수준 SCIM 프로비저닝은 레거시 기능이며 Public Preview 상태입니다.

### 2.3 역할 구분

| 역할 | 권한 |
|---|---|
| 계정 관리자 | 계정 수준 사용자·서비스 프린시펄·그룹의 추가, 수정, 삭제, 워크스페이스 접근 부여 |
| 워크스페이스 관리자 | 계정에 ID를 추가하고 해당 워크스페이스 접근을 부여. 계정 사용자·서비스 프린시펄은 수정·삭제 불가 |
| 서비스 프린시펄 관리자 (SP manager) | 서비스 프린시펄의 역할을 추가·수정·삭제. 계정 관리자는 계정의 모든 서비스 프린시펄에, 워크스페이스 관리자는 자신이 만든 서비스 프린시펄에 자동으로 받음 |

> **주의** 워크스페이스 관리자는 계정 수준 ID를 수정할 수 없습니다. 따라서 퇴사자 처리를 워크스페이스 관리자에게만 맡기면 계정 수준에 남은 ID가 정리되지 않습니다. 계정 관리자와 워크스페이스 관리자의 절차를 따로 정의하십시오.

## 3. 어떻게 쓰는가

### 3.1 서비스 프린시펄 만들고 배정하기

잡이나 CI/CD가 쓸 서비스 프린시펄은 사람 계정으로 실행하지 않는 것이 원칙입니다.

계정 콘솔에서 만드는 방법은 다음과 같습니다.

1. 계정 관리자로 계정 콘솔에 로그인합니다.
2. 사이드바의 **User management** 를 엽니다.
3. **Service principals** 탭에서 **Add service principal** 을 누르고 이름을 입력한 뒤 **Add** 를 누릅니다.

워크스페이스 관리자는 워크스페이스의 **Settings** → **Identity and access** 탭에서 **Service principals** 옆 **Manage** → **Add service principal** → **Add new** 순서로 만들 수 있습니다. 이때 계정에도 추가됩니다.

만든 서비스 프린시펄을 워크스페이스에 배정하려면 계정 콘솔에서 **Workspaces** → 워크스페이스 → **Permissions** 탭 → **Add permissions** 를 엽니다. 서비스 프린시펄을 고르고 권한(entitlement)을 지정한 뒤 **Save** 를 누릅니다. 배정은 다음 API 경로가 처리합니다.

```text
{account-domain}/api/2.0/accounts/{account_id}/workspaces/{workspace_id}/permissionassignments
{workspace-domain}/api/2.0/preview/permissionassignments/principals/{principal_id}
```

서비스 프린시펄의 역할과 실행 권한은 다음 규칙으로 정해집니다.

| 질문 | 답 (문서 기준) |
|---|---|
| 만든 사람은 어떤 역할을 받나 | 서비스 프린시펄을 만든 사람은 자동으로 서비스 프린시펄 관리자가 됨 |
| 관리자는 실행 권한을 받나 | 관리자 역할은 서비스 프린시펄 사용자(Service Principal User) 역할을 상속하지 않음 |
| 잡을 그 신원으로 실행하려면 | 실행자에게 Service Principal User 역할을 명시적으로 부여 |
| 사용자·그룹에 잡 실행 권한을 주려면 | 서비스 프린시펄을 대상으로 잡을 실행할 권한을 줌. 사용자가 떠나도 잡이 실패하지 않음 |

### 3.2 퇴사·폐기 시 비활성화

서비스 프린시펄을 더 쓰지 않을 때는 삭제보다 먼저 비활성화합니다. 문서의 SCIM 예시는 다음과 같습니다.

```bash
curl --netrc -X PATCH \
https://${DATABRICKS_HOST}/api/2.1/accounts/{account_id}/scim/v2/ServicePrincipals/{id} \
--header 'Content-type: application/scim+json' \
--data '{"schemas":["urn:ietf:params:scim:api:messages:2.0:PatchOp"],"Operations":[{"op":"replace","path":"active","value":[{"value":"false"}]}]}' \
| jq .
```

### 3.3 서비스 프린시펄에 UC 권한 주기

서비스 프린시펄은 Unity Catalog 권한으로 데이터 접근 범위를 정합니다.

```sql
-- 서비스 프린시펄을 워크스페이스에 배정한 뒤 실행합니다.
-- 식별자 형식(표시 이름 또는 애플리케이션 ID)은 Unity Catalog 권한 문서에서 확인하십시오.
GRANT USE CATALOG ON CATALOG main TO `my-service-principal`;
GRANT USE SCHEMA ON SCHEMA main.sales TO `my-service-principal`;
GRANT SELECT ON TABLE main.sales.orders TO `my-service-principal`;
```

> **참고** 위 GRANT 예시는 Unity Catalog 권한 구문입니다. 권한 모델의 전체 구조는 [권한 모델과 소유권](../06-unity-catalog/privileges-and-ownership.md)에서 다룹니다.

### 3.4 그룹으로 권한 묶기

개별 사용자에게 GRANT하지 말고 그룹에 GRANT한 뒤 그룹에 사용자를 넣는 방식이 관리하기 쉽습니다.

```sql
GRANT SELECT ON SCHEMA main.sales TO `analysts`;
```

그룹 설계에 대해 모범 사례 페이지가 권장하는 원칙은 다음과 같습니다. 문서의 원문을 옮긴 것입니다.

| 원칙 | 문서 원문 (요지) |
|---|---|
| 그룹에 권한 부여 | "Databricks recommends that you assign groups permissions to workspaces instead of assigning workspace permissions to users" |
| 계정 그룹 사용 | "Databricks recommends using account groups instead of workspace-local groups" |
| 운영 데이터는 서비스 프린시펄로 | "Databricks recommends creating service principals to run production jobs or modify production data." |
| 사람은 운영 쓰기 권한 없음 | "interactive users do not need any write, delete, or modify privileges in production." |

### 3.5 서비스 프린시펄 ACL

서비스 프린시펄을 어떤 사용자나 그룹이 쓸 수 있는지는 **서비스 프린시펄 ACL**(Service principal ACL) 페이지에서 설정합니다. 세부 권한 값은 원문에서 확인하십시오.

## 4. 트레이드오프

| 방식 | 장점 | 제약 |
|---|---|---|
| 자동 ID 관리 | IdP가 원본이 되어 수작업이 줄어듦. 서비스 프린시펄과 중첩 그룹까지 동기화 가능 (Entra ID) | 지원 IdP는 Entra ID와 Okta. Okta는 서비스 프린시펄과 중첩 그룹 동기화 불가. 비ID 연동 워크스페이스에서 쓸 수 없음 |
| SCIM | 자동 ID 관리를 쓸 수 없을 때의 대체 방식 | 서비스 프린시펄과 중첩 그룹 동기화 불가. 동기화 실패 처리를 직접 점검해야 함 |
| 워크스페이스 로컬 그룹 | 워크스페이스 단위로 독립 운영 가능 | 계정 전체 권한 점검이 어려움. 모범 사례는 계정 그룹 사용을 권장 |

## 5. 주의사항

- **퇴사 처리는 IdP에서 비활성화하는 것부터 시작하십시오.** 자동 ID 관리와 SCIM은 IdP를 원본으로 삼는 방식입니다. IdP에서 삭제된 사용자는 "Active: Removed From [IdP]" 상태를 거쳐 다음 동기화에서 비활성화됩니다. 개인 액세스 토큰은 따로 폐기하십시오.
- **그룹 이름 변경은 바로 반영되지 않습니다.** IdP에서 바꾼 그룹 이름은 계정 관리자가 계정 콘솔의 그룹 상세 페이지를 열어야 Databricks에 반영됩니다. 그룹을 이름으로 참조하는 GRANT 문이 있는지 먼저 점검하십시오. 동기화된 그룹은 계정 관리자가 워크스페이스에 배정하기 전까지 접근이 생기지 않습니다.
- **SCIM으로 들어온 멤버십은 자동 ID 관리로 지워지지 않습니다.** 자동 ID 관리 전환 후에도 SCIM으로 동기화된 멤버는 SCIM API로 제거해야 합니다. 반대로 SCIM에서 자동 ID 관리로 옮기면 그룹, UC 권한, 워크스페이스 배정이 그대로 옮겨집니다.
- **서비스 프린시펄을 개인 계정처럼 쓰지 마십시오.** 잡과 도구는 서비스 프린시펄로 인증하고, 사용자 권한은 그룹으로 주십시오.
- **레거시 워크스페이스는 ID 연동 상태를 먼저 확인하십시오.** 이메일이 같은 계정이 병합되는 동작을 모르고 옮기면 권한이 예상과 다르게 합쳐질 수 있습니다.

> **참고** 사용자 상태(비활성, 삭제)가 감사 로그와 데이터 소유권에 미치는 영향은 이 페이지 범위에서 확인하지 못했습니다. 실제 운영 전 계정 콘솔의 해당 설정을 직접 확인하십시오.

## 참고 문서

- [Identity management](https://docs.databricks.com/aws/en/admin/users-groups/)
- [Identity management best practices](https://docs.databricks.com/aws/en/admin/users-groups/best-practices)
- [Automatic identity management](https://docs.databricks.com/aws/en/admin/users-groups/automatic-identity-management/)
- [SCIM provisioning](https://docs.databricks.com/aws/en/admin/users-groups/scim/)
- [Manage service principals](https://docs.databricks.com/aws/en/admin/users-groups/manage-service-principals)
- [Automatically provision users (JIT)](https://docs.databricks.com/aws/en/security/auth/jit)
- [Access control](https://docs.databricks.com/aws/en/security/auth/access-control/)
- [Identity attributes (Beta)](https://docs.databricks.com/aws/en/admin/users-groups/identity-attributes/)
