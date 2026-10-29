# 워크스페이스 운영 체크리스트

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

이 페이지는 앞의 여덟 페이지에서 다룬 설정을 운영 점검표로 묶습니다. 항목마다 **점검 질문**, ** 확인 방법**, ** 권장 기준** 을 적었습니다. 확인 방법에 SQL이 있으면 시스템 테이블로 실제 상태를 볼 수 있고, 없으면 콘솔이나 API에서 확인합니다. 권장 기준은 문서가 명시한 값이나 권장 사항만 옮겼습니다.

## 1. 왜 필요한가

### 설정은 맞게 되어 있어도 시간이 지나면 어긋납니다

- 퇴사자의 계정과 토큰은 정리되지 않은 채 남기 쉽습니다.
- 임시로 열어 둔 IP 대역과 네트워크 정책 예외는 사라지지 않습니다.
- 새 기능이 GA나 기본 적용으로 바뀌면 이전 설정과 충돌할 수 있습니다.

그래서 점검은 한 번으로 끝나지 않고 정해진 주기로 반복해야 합니다.

## 2. 어떻게 동작하는가

### 점검 주기

| 주기 | 점검 대상 |
|---|---|
| 매주 | 예산 알림, 인바운드·아웃바운드 거부 기록, 실패한 잡의 네트워크 오류 |
| 매월 | 토큰 보고서, 사용량 대시보드와 태그 귀속, 사용자·서비스 프린시펄·그룹 변경 |
| 분기 | 시크릿 스코프 ACL, IP 액세스 목록과 네트워크 정책, 컴플라이언스 설정 |
| 릴리즈 노트 발표 시 | 기본 적용 변경, 상태 변경(Preview → GA, Beta), 지원 중단 |

## 3. 어떻게 쓰는가

### 영역 1: 신원과 인증

| 점검 질문 | 확인 방법 | 권장 기준 |
|---|---|---|
| 퇴사자 계정이 남아 있는가 | 계정 콘솔의 사용자 목록과 IdP 상태 비교 | IdP에서 비활성화된 계정이 계정 콘솔에도 없어야 함 |
| 워크스페이스가 ID 연동 상태인가 | 워크스페이스 페이지의 **Identity federation** 라벨 | 레거시 워크스페이스는 메타스토어 할당으로 연동 전환 계획 수립 |
| 장기 PAT가 남아 있는가 | 계정 콘솔 **Security > Token report**, `databricks token-management list` | 90일 이상 미사용 토큰 정리. 신규 토큰은 90일 미만 수명 권장 |
| PAT 최대 수명이 설정되었는가 | 워크스페이스 설정 `maxTokenLifetimeDays` | 문서 권장값(90일 미만) 적용. 미설정 시 기본 730일 |
| 잡이 사람 계정으로 도는가 | 잡 실행 주체(run as) 목록 | 잡과 CI/CD는 서비스 프린시펄로 실행 |

```sql
-- 최근 30일간 감사 이벤트를 서비스별로 집계해 이상 행동의 기준선을 잡습니다.
SELECT service_name, COUNT(*) AS event_count
FROM system.access.audit
WHERE event_date >= current_date() - INTERVAL 30 DAYS
GROUP BY service_name
ORDER BY event_count DESC;
```

### 영역 2: 네트워크

| 점검 질문 | 확인 방법 | 권장 기준 |
|---|---|---|
| 프런트엔드 PrivateLink가 검증되었는가 | 계정 콘솔 **Security > Private endpoints** 등록 상태, 워크스페이스 프라이빗 액세스 설정 | 사설 경로 테스트 후 공개 접근 설정을 False로 전환 |
| 공개 접근 설정이 의도한 값인가 | 워크스페이스 네트워크 설정의 **Public access enabled** | 테스트 중에는 True, 운영 전환 후 False 검토 |
| IP 액세스 목록이 최신인가 | 계정·워크스페이스 IP 액세스 목록 조회(REST API) | 목록에 관리자 IP 포함 여부 확인. 컨텍스트 기반 인그레스와 중복 정책 정리 |
| 인바운드 거부가 정상 트래픽을 막는가 | `system.access.inbound_network` 조회 | dry run 기록에서 정상 사용자 거부가 없어야 함 |
| 서버리스 아웃바운드 정책이 적용되었는가 | 워크스페이스에 연결된 네트워크 정책, `system.access.outbound_network` | dry run 결과 검토 후 Restricted 모드 강제 적용 |
| 고정 IP 목록(stable IP list)을 쓰는가 | NCC 구성과 자원 방화벽 규칙 | 지원 중단된 방식이면 NCC 방식으로 이전. 미이전 시 `403` 가능 |
| 백엔드 PrivateLink 엔드포인트가 맞는가 | 클래식 컴퓨트가 있는 워크스페이스의 VPC 엔드포인트 등록 | 워크스페이스 엔드포인트와 SCC 릴레이 엔드포인트 모두 등록. Private DNS 활성화 |

```sql
-- 최근 7일간 인바운드 네트워크 기록을 확인합니다. dry run과 실제 거부를 구분해서 보십시오.
SELECT *
FROM system.access.inbound_network
WHERE event_date >= current_date() - INTERVAL 7 DAYS
LIMIT 200;
```

### 영역 3: 데이터 보호

| 점검 질문 | 확인 방법 | 권장 기준 |
|---|---|---|
| 고객 관리 키가 필요한 범위에 적용되었는가 | 워크스페이스 암호화 설정, Unity Catalog 카탈로그별 키 | 규제 대상 데이터의 범위(관리형 서비스, 워크스페이스 스토리지, Unity Catalog)를 문서로 정의 |
| 쿼리 기록이 비어 보이지 않는가 | `system.query.history`의 `statement_text` 확인 | 관리형 서비스 키를 쓰면 `system` 카탈로그 키 설정 필요 |
| 시크릿 스코프가 역할 단위인가 | 스코프 목록을 확인하고, 스코프별 ACL을 `databricks secrets list-acls`로 조회 | 개인 단위 스코프 금지. 스코프 이름은 모든 사용자가 볼 수 있음을 전제 |
| 노트북에 평문 자격증명이 없는가 | 노트북과 잡 코드 검색 | `dbutils.secrets.get`으로 대체. 편집은 우회를 막지 못함 |
| 컴플라이언스 프로필 적용 범위가 맞는가 | 워크스페이스 보안 설정 | 규제 대상 워크스페이스만 적용. 추가 요금과 Nitro 인스턴스 제한 사전 검토 |
| 향상된 보안 모니터링 로그를 검토하는가 | 감사 로그 시스템 테이블의 파일 무결성·악성코드 기록, 관리자 이메일의 취약점 보고서 | 로그 검토 담당자와 주기 지정. 문서상 검토는 고객 책임 |

### 영역 4: 감사와 보존

| 점검 질문 | 확인 방법 | 권장 기준 |
|---|---|---|
| 감사 테이블을 누가 읽을 수 있는가 | `system` 카탈로그와 `system.access` 스키마의 GRANT 현황 | 감사 담당 그룹으로 한정. 요청 파라미터의 민감 정보 노출 검토 |
| 보존 기간이 요구 기간보다 짧은 테이블이 있는가 | [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md)의 보존 표 | 필요한 기간이 더 길면 주기적 복사 또는 S3 전달 설정 |
| 보존 기간 확장을 켰는가 | 계정 Previews 페이지의 "System Tables Configurable Retention" | Beta. 지원 스키마만 395일. 적용까지 최대 24시간 |
| 계정 수준 감사 로그 전달이 살아 있는가 | 로그 전달 구성의 `log_delivery_status` | 실패 상태가 없어야 함. 로그 타입별 활성 구성은 최대 두 개 |
| 계보가 1년 넘게 필요한가 | 계보 시스템 테이블(롤링 1년) | 1년 이상 기록이 필요하면 카탈로그 탐색기나 계보 API로 별도 보관 |

```sql
-- 최근 7일간 계보 기록의 건수를 날짜별로 확인합니다.
SELECT event_date, COUNT(*) AS lineage_events
FROM system.access.table_lineage
WHERE event_date >= current_date() - INTERVAL 7 DAYS
GROUP BY event_date
ORDER BY event_date;
```

### 영역 5: 비용

| 점검 질문 | 확인 방법 | 권장 기준 |
|---|---|---|
| 워크스페이스별·팀별 비용이 보이는가 | 사용량 대시보드(계정 콘솔 **Usage**) 또는 `system.billing.usage` | 태그 키 체계를 정하고 주기적으로 집계 |
| 예산 알림이 설정되었는가 | 계정 콘솔 예산 목록 | 임계값마다 수신자 지정. 메일 지연 최대 24시간 |
| Unity Gateway 차단이 필요한가 | 예산 상세 페이지의 Block usage | 차단은 근사치. 절대 상한으로 가정하지 않음 |
| 서버리스 사용량에 정책 태그가 붙는가 | `system.billing.usage`의 `custom_tags` | 정책 할당 확인. 잡이 트리거한 파이프라인은 정책을 상속하지 않음 |
| 클래식 컴퓨트 태그가 있는가 | 클러스터와 웨어하우스 태그 | 사용량 정책은 클래식에 적용되지 않으므로 클러스터 태그로 따로 관리 |

```sql
-- 최근 30일간 워크스페이스와 SKU별 사용량 합계입니다. 단가는 곱하지 않습니다.
SELECT workspace_id, sku_name, SUM(usage_quantity) AS total_usage
FROM system.billing.usage
WHERE usage_date >= current_date() - INTERVAL 30 DAYS
GROUP BY workspace_id, sku_name
ORDER BY total_usage DESC;
```

### 영역 6: 변경 관리

| 점검 질문 | 확인 방법 | 권장 기준 |
|---|---|---|
| 기본 적용 변경을 알고 있는가 | 릴리즈 노트 확인 | 2026년 10월 26일 계정 수준 보안 기능의 GA 기본 적용을 기준 문서에 기록 |
| 프리뷰 기능을 운영에 쓰고 있는가 | 시스템 테이블과 기능 상태 라벨 | Preview·Beta 기능은 운영 의존을 줄이고, 상태 변화를 주기적으로 확인 |
| 지원 중단된 방식을 쓰는가 | 네트워크 구성, 레거시 워크스페이스 설정 | 지원 중단 항목을 목록으로 관리하고 이전 일정을 세움 |

## 4. 트레이드오프

| 점검 방식 | 장점 | 제약 |
|---|---|---|
| 시스템 테이블 쿼리 | 실제 기록 기반 판단 | 보존 기간과 갱신 지연을 고려해야 함 |
| 콘솔 수동 확인 | 설정 의도를 바로 확인 | 기록이 남지 않아 추적이 어려움 |
| 정기 점검 문서화 | 감사와 인수인계에 유리 | 문서가 실제 설정과 어긋나지 않도록 주기적으로 갱신해야 함 |

## 5. 주의사항

- **점검 결과를 기록으로 남기십시오.** 점검 날짜, 확인자, 발견 사항을 표로 남기면 다음 주기의 기준선이 됩니다.
- **네트워크 변경은 롤백 경로와 함께 하십시오.** 잠금 위험이 가장 큰 영역입니다.
- **상태 라벨 변화를 확인하십시오.** 같은 기능이 Preview에서 GA로 바뀌거나, 문서 간 표기가 충돌하는 경우가 있습니다. 이 장의 충돌 표기(컨텍스트 기반 인그레스, 사설 연결)는 실제 적용 전에 원문을 다시 확인하십시오.
- **점검 쿼리는 권한이 필요합니다.** 시스템 테이블 접근 권한은 [보안 모델 개요](security-model-overview.md)와 [감사 로그와 시스템 테이블](audit-logs-and-system-tables.md)에서 설명한 대로 부여하십시오.

## 참고 문서

- [Security and compliance](https://docs.databricks.com/aws/en/security/)
- [Administration guide](https://docs.databricks.com/aws/en/admin/)
- [Network security](https://docs.databricks.com/aws/en/security/network/)
- [System tables](https://docs.databricks.com/aws/en/admin/system-tables/)
- [Cost management](https://docs.databricks.com/aws/en/admin/usage/)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
