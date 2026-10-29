# 보안 모델 개요

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

Databricks의 보안은 여러 층에 걸쳐 있습니다. 계정(Account) 수준의 ID와 정책, 워크스페이스(Workspace) 수준의 접근과 컴퓨트, 데이터 수준의 Unity Catalog 권한과 암호화가 함께 동작합니다. 이 장은 이 층들을 다음 세 가지 질문으로 나누어 설명합니다.

| 질문 | 담당 영역 | 다루는 페이지 |
|---|---|---|
| 누가 들어올 수 있는가 | ID, 인증, 네트워크 인바운드 | [ID와 접근](identity-and-access.md), [인증과 토큰](authentication-and-tokens.md), [인바운드 네트워크 접근](network-inbound-access.md) |
| 데이터가 어디로 나가고 어떻게 보호되는가 | 서버리스 이그레스, 암호화, 시크릿, 컴플라이언스 | [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md), [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 무엇을 했고 얼마를 썼는가 | 감사 로그, 시스템 테이블, 비용 | [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md), [비용 관리](cost-management.md) |

> **참고** 아래 "책임 공유" 표는 이 장을 나누기 위한 구분입니다. 공식 문서의 책임 공유 문구를 그대로 옮긴 것이 아닙니다. 실제 책임 범위는 계약과 클라우드 제공자 문서를 함께 확인하십시오.

## 1. 왜 필요한가

### 이전 방식의 한계

- 사용자 계정을 워크스페이스마다 따로 만들면 퇴사자 회수와 권한 점검이 워크스페이스 수만큼 반복됩니다.
- 접근 제어가 노트북과 클러스터 설정에 흩어져 있으면 "이 데이터를 누가 읽었는가"를 한 번에 답할 수 없습니다.
- 장기 자격증명(개인 토큰, 코드에 박힌 비밀번호)이 늘어나면 유출 시 피해 범위를 특정하기 어렵습니다.

Databricks는 ID를 계정에서 중앙 관리하고, 권한은 Unity Catalog에서 데이터 단위로 부여하고, 감사 기록은 시스템 테이블로 남기는 구조를 권장합니다.

## 2. 어떻게 동작하는가

### 보안 영역의 구성

공식 보안 문서는 다음 다섯 영역으로 기능을 나눕니다.

| 영역 | 주요 기능 (문서 기준) | 상세 페이지 |
|---|---|---|
| 인증과 접근 제어 (Authentication and access control) | SSO, MFA, 접근 제어 목록(ACL) | [ID와 접근](identity-and-access.md), [인증과 토큰](authentication-and-tokens.md) |
| 네트워크 (Networking) | 프런트엔드 PrivateLink, 서버리스 이그레스 제어, 고객 관리 VPC | [인바운드 네트워크 접근](network-inbound-access.md), [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md) |
| 데이터 보안과 암호화 (Data security and encryption) | 고객 관리 키(Customer-managed keys), 노드 간 암호화, 자격증명 편집(redaction) | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 시크릿 관리 (Secret management) | Databricks 시크릿 스코프 | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |
| 컴플라이언스 (Compliance) | 컴플라이언스 보안 프로필, 향상된 보안 모니터링, FedRAMP High GovCloud | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) |

### 계정과 워크스페이스의 역할

관리 권한은 두 층으로 나뉩니다. 계정 관리자는 계정 콘솔에서 사용자·서비스 프린시펄·그룹을 만들고 워크스페이스 접근을 부여합니다. 워크스페이스 관리자는 워크스페이스 안의 설정과 컴퓨트, 토큰 정책을 관리합니다.

| 역할 | 할 수 있는 일 | 할 수 없는 일 (문서 명시) |
|---|---|---|
| 계정 관리자 (Account admin) | 계정 수준 사용자·서비스 프린시펄·그룹의 추가·수정·삭제, 워크스페이스 접근 부여, 계정 콘솔 보안 설정, 토큰 보고서 조회·폐기 | 문서 명시 없음 |
| 워크스페이스 관리자 (Workspace admin) | 계정에 ID 추가와 해당 워크스페이스 접근 부여, 워크스페이스 설정, PAT 정책 관리 | 계정 사용자·서비스 프린시펄을 수정하거나 삭제하는 것 |

> **주의** 워크스페이스 관리자는 계정 수준 ID를 수정할 수 없습니다. 따라서 퇴사자 처리를 워크스페이스 관리자에게만 맡기면 계정 수준에 남은 ID가 정리되지 않습니다. 계정 관리자와 워크스페이스 관리자의 절차를 따로 정의하십시오.

### 계정 수준 보안 기능의 기본 적용 변경

릴리즈 노트에 따르면 2026년 10월 26일 기준으로 계정 수준 보안 기능(Account-level security features)은 GA 시점에 Previews 페이지에서 수동으로 켜지 않아도 모든 계정에 기본 제공됩니다. 다만 관리자는 여전히 이 기능을 직접 설정해야 합니다. 이 변경은 "기본으로 켜짐"이 "기본 설정 완료"를 뜻하지 않는다는 점에 유의하십시오.

> **참고** 이 릴리즈 노트 항목은 변경 유형이 "behavior change"로 표시되어 있습니다. 어떤 세부 기능이 포함되는지는 릴리즈 노트 원문에서 다시 확인하십시오.

## 3. 어떻게 쓰는가

보안 설정을 시작하기 전에 현재 상태를 확인하는 것이 첫 단계입니다. 아래 쿼리는 시스템 테이블에서 최근 감사 이벤트의 서비스 종류와 액션 종류를 집계합니다. 어떤 이벤트가 기록되는지 먼저 파악하는 데 쓸 수 있습니다.

```sql
SELECT service_name, action_name, COUNT(*) AS event_count
FROM system.access.audit
WHERE event_date >= current_date() - INTERVAL 7 DAYS
GROUP BY service_name, action_name
ORDER BY event_count DESC
LIMIT 50;
```

`system.access.audit`은 Public Preview 상태입니다. 조회하려면 `system` 카탈로그에 대한 `USE CATALOG`, 시스템 스키마에 대한 `USE SCHEMA`와 `SELECT` 권한이 필요합니다. 자세한 내용은 [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md)에서 다룹니다.

## 4. 트레이드오프

| 선택 | 장점 | 비용·제약 |
|---|---|---|
| ID를 계정에서 중앙 관리 (ID 연동) | 워크스페이스마다 사용자를 만들 필요가 없음 | 기존 레거시 워크스페이스는 마이그레이션 작업이 필요함 |
| 워크스페이스 로컬 그룹 유지 | 워크스페이스 단위 독립성 | 계정 수준 그룹과 별도 관리되어 권한 점검이 나뉨 |
| 보안 기능을 모두 켜기 | 감사·암호화·네트워크 통제가 넓게 적용됨 | 일부 기능은 추가 요금이나 상위 요금제가 필요함 (예: IP 액세스 목록, 고객 관리 키는 Enterprise 요금제 필요) |

## 5. 주의사항

- **관리 경계를 문서로 정하십시오.** 계정 관리자와 워크스페이스 관리자 중 누가 어떤 설정을 바꾸는지 표로 정리해 두면 감사 때 설명하기 쉽습니다.
- **기본값을 신뢰하기 전에 확인하십시오.** 기본 적용이 된 기능도 설정이 필요한 항목이 있습니다.
- **보안 설정은 한 번 바꾸면 워크스페이스 전체에 영향을 줍니다.** 특히 네트워크 설정은 사용자 접속을 끊을 수 있으므로 변경 전 롤백 경로를 준비하십시오.
- **시스템 테이블 접근 권한도 보안 설정의 일부입니다.** 감사 로그를 누구나 읽을 수 있으면 민감한 요청 파라미터가 노출될 수 있습니다.

## 참고 문서

- [Security and compliance](https://docs.databricks.com/aws/en/security/)
- [Administration guide](https://docs.databricks.com/aws/en/admin/)
- [Administration concepts](https://docs.databricks.com/aws/en/admin/admin-concepts)
- [Identity management](https://docs.databricks.com/aws/en/admin/users-groups/)
- [Audit logs](https://docs.databricks.com/aws/en/admin/account-settings/audit-logs)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
