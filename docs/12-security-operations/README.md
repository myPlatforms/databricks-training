# 12. 보안·운영 (시스템 테이블·비용)

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

이 장은 Databricks 계정과 워크스페이스를 운영하는 관리자와 플랫폼 담당자를 대상으로 합니다. 누가 무엇에 접근할 수 있는지(ID·인증), 트래픽이 어디로 오가는지(네트워크), 데이터와 시크릿을 어떻게 보호하는지(암호화·시크릿·컴플라이언스 보안 프로필), 누가 무엇을 했는지 어떻게 남기고 조회하는지(감사 로그·시스템 테이블), 비용을 어떻게 보고 통제하는지(사용량·예산·태그·서버리스 사용량 정책)를 한 흐름으로 다룹니다. 마지막 페이지는 이 내용을 워크스페이스 운영 점검표로 정리합니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- 플랫폼 제공자와 고객의 보안 책임 범위를 나누고, 계정 관리자와 워크스페이스 관리자의 권한 차이를 설명합니다.
- 사용자·그룹·서비스 프린시펄을 계정 수준에서 관리하고, 자동 ID 관리(Automatic identity management), SCIM, SSO, JIT 프로비저닝의 역할을 구분합니다.
- OAuth U2M과 M2M의 차이를 설명하고, 개인 액세스 토큰(PAT) 정책의 기본값과 관리 항목을 확인합니다.
- 프런트엔드 PrivateLink, 백엔드 PrivateLink, IP 액세스 목록, 컨텍스트 기반 인그레스로 인바운드 접근을 제한합니다.
- 서버리스 이그레스 제어(Serverless egress control)의 Full Access와 Restricted Access 모드, 네트워크 정책, 네트워크 연결 구성(NCC)의 관계를 이해합니다.
- 고객 관리 키(Customer-managed keys)가 덮는 데이터 범위와 제약을 확인하고, 시크릿 스코프의 권한과 편집(redaction) 동작을 설명합니다.
- 시스템 테이블 스키마(access·billing·compute·query·lineage 등)의 보존 기간과 활성화 조건을 확인하고 감사 로그를 쿼리합니다.
- 사용량 대시보드, 예산(Budgets), 태그, 서버리스 사용량 정책으로 비용을 귀속하고 추적합니다.
- 위 항목을 묶어 워크스페이스 운영 점검표를 만듭니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [보안 모델 개요](security-model-overview.md) | 100 | 책임 공유 모델, 계정·워크스페이스 관리자 역할, 보안 기능의 기본 적용 변경 |
| 2 | [ID와 접근](identity-and-access.md) | 200 | 사용자·그룹·서비스 프린시펄, ID 연동(Identity federation), 자동 ID 관리·SCIM·SSO·JIT |
| 3 | [인증과 토큰](authentication-and-tokens.md) | 200 | OAuth U2M·M2M, 개인 액세스 토큰(PAT) 정책과 토큰 보고서 |
| 4 | [인바운드 네트워크 접근](network-inbound-access.md) | 300 | 프런트엔드·백엔드 PrivateLink, IP 액세스 목록, 컨텍스트 기반 인그레스 |
| 5 | [서버리스 이그레스와 NCC](serverless-egress-and-ncc.md) | 300 | 서버리스 이그레스 제어, 네트워크 정책, 네트워크 연결 구성(NCC), 서버리스 방화벽 |
| 6 | [암호화·시크릿·컴플라이언스](encryption-secrets-and-compliance.md) | 300 | 고객 관리 키, 시크릿 스코프, 컴플라이언스 보안 프로필, 향상된 보안 모니터링 |
| 7 | [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md) | 200 | 감사 로그 시스템 테이블, 시스템 스키마 목록, 보존 기간, 활성화, 계정 수준 로그 전달 |
| 8 | [비용 관리](cost-management.md) | 200 | 사용량 대시보드, 예산, 태그, 서버리스 사용량 정책, 청구 시스템 테이블 |
| 9 | [워크스페이스 운영 체크리스트](operations-checklist.md) | 300 | 영역별 점검 항목, 확인 쿼리, 정기 점검 주기 |
| 10 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 10개와 실무 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 「보안 모델 개요」와 「ID와 접근」 페이지는 이후 모든 페이지의 전제이며, 「감사 로그와 시스템 테이블」 페이지는 「비용 관리」와 「워크스페이스 운영 체크리스트」 페이지에서 반복해서 참조합니다.

## 선수 지식

- **계정과 워크스페이스 구조**: 계정 콘솔, 워크스페이스, 메타스토어의 관계를 알고 있어야 합니다. 자세한 내용은 [01장 계정·워크스페이스·메타스토어](../01-platform-overview/account-workspace-metastore.md)를 참고하십시오.
- **Unity Catalog 권한 모델**: 카탈로그·스키마·테이블 권한과 GRANT 문을 이해해야 합니다. 권한 세부 내용은 [06장 권한 모델과 소유권](../06-unity-catalog/privileges-and-ownership.md)에서 다룹니다.
- **클라우드 네트워크 기초**: AWS VPC, 서브넷, 보안 그룹, VPC 엔드포인트의 개념이 필요합니다. 이 장은 AWS 문서를 기준으로 합니다.
- **SQL 기초**: 시스템 테이블 조회는 `SELECT`, `WHERE`, `GROUP BY`를 사용합니다.
- **Databricks CLI 기초**: 시크릿과 토큰 예제는 `databricks` CLI 명령을 사용합니다.

## 이 장의 읽는 법

각 기능 페이지는 왜 필요한지, 어떻게 동작하는지, 어떻게 설정하는지, 트레이드오프, 주의사항 순서입니다. 기능마다 상태(GA, Public Preview, Beta 등)를 표기합니다. 상태 라벨은 문서 본문과 릴리즈 노트가 다르게 적힌 경우가 있어, 충돌하는 항목은 페이지 안에서 따로 표기했습니다.

단가 숫자는 이 장에 쓰지 않습니다. 비용 구조는 [03장 비용 구조 비교](../03-compute/cost-structure.md)에서, 단가는 Databricks 공식 가격 페이지에서 확인하십시오.

Unity Gateway의 사용량과 예산은 [08장 Unity Gateway](../08-machine-learning/unity-gateway.md)와 연결됩니다. Lakebase의 시스템 테이블과 과금은 [10장 Lakebase](../10-lakebase/README.md)를 참고하십시오. Genie Code의 거버넌스와 비용은 [11장 Genie Code 거버넌스와 비용](../11-developer-tools/genie-code/governance-and-cost.md)에서 다룹니다.

> **참고** 이 장은 AWS 문서(`docs.databricks.com/aws/en/`)를 기준으로 작성했습니다. Azure에서는 제공 여부나 경로가 다를 수 있으므로 Azure 문서(`learn.microsoft.com/azure/databricks/`)로 따로 확인하십시오.

> **주의** 보안 기능은 계정 설정, 워크스페이스 설정, 프리뷰 설정 세 곳에 나뉘어 있습니다. 한 곳을 켰다고 전체가 적용된 것으로 가정하지 마십시오. 각 페이지의 설정 위치를 따르십시오.

## 참고 문서

- [Security and compliance](https://docs.databricks.com/aws/en/security/)
- [Administration guide](https://docs.databricks.com/aws/en/admin/)
- [Network security](https://docs.databricks.com/aws/en/security/network/)
- [Monitor usage with system tables](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Cost management](https://docs.databricks.com/aws/en/admin/usage/)
- [Compliance security profile](https://docs.databricks.com/aws/en/security/privacy/security-profile)
