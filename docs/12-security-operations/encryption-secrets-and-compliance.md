# 암호화·시크릿·컴플라이언스

> 기준일: 2026-10-28 · 근거: 공식 문서

## 한눈에 보기

이 페이지는 세 가지를 다룹니다. **고객 관리 키**(Customer-managed keys, CMK)는 플랫폼이 쓰는 암호화 키를 고객이 소유한 키로 바꾸는 기능입니다. **시크릿 스코프**(Secret scope)는 노트북과 잡이 쓰는 자격증명을 코드 밖에 두는 저장소입니다. **컴플라이언스 보안 프로필**(Compliance security profile)은 규제 대상 데이터를 처리하는 워크스페이스에 강화된 설정을 한꺼번에 켜는 기능입니다.

## 1. 왜 필요한가

### 이전 방식의 한계

- 플랫폼 기본 키만 쓰면 키 회전과 폐기를 고객이 직접 통제할 수 없습니다.
- 노트북에 비밀번호를 넣으면 공유할 때마다 노출됩니다.
- 규제 산업에서는 강화된 OS 이미지, FIPS 검증 암호 모듈, 모니터링을 워크스페이스마다 따로 구성하기 어렵습니다.

## 2. 어떻게 동작하는가

### 고객 관리 키 (Customer-managed keys)

문서 기준 Enterprise 요금제가 필요합니다. 클라우드 키 관리 서비스(KMS)에 있는 키를 쓰며, 세 가지 적용 범위가 있습니다.

| 적용 범위 | 대상 데이터 | 메모 |
|---|---|---|
| 관리형 서비스 (Managed services) | 컨트롤 플레인 데이터. 노트북 소스, 시크릿, Databricks SQL 쿼리와 쿼리 기록, AI/BI 대시보드, Genie Agents, AI Search 인덱스, Lakebase Autoscaling 프로젝트 데이터, Git 자격증명 | 서버리스 워크스페이스에서는 워크스페이스 스토리지와 루트 스토리지도 포함 |
| 워크스페이스 스토리지 (Workspace storage) | 워크스페이스 스토리지 버킷. DBFS 루트(FileStore, MLflow 모델, DBFS 루트의 Lakeflow pipelines 데이터), 잡 결과 같은 시스템 데이터, 선택 시 클래식 컴퓨트의 EBS 볼륨 | 기본 스토리지(default storage)에는 적용 안 됨 |
| Unity Catalog | 기본 스토리지로 뒷받침되는 카탈로그의 데이터 | 카탈로그마다 다른 키 사용 가능. KMS로 암호화된 S3 버킷을 읽고 쓸 수 있음 |

서버리스 워크스페이스는 관리형 서비스 키만 있으면 되며, 워크스페이스 스토리지와 루트 스토리지를 포함합니다. Model Serving 아티팩트는 워크스페이스 루트 스토리지(고객이 암호화 가능)와 Databricks 관리 레지스트리(관리형 서비스 키로 암호화)로 나뉩니다.

문서가 명시한 제약은 다음과 같습니다.

| 제약 | 내용 |
|---|---|
| 쿼리 기록 | 관리형 서비스 키를 설정한 뒤에도 `system` 카탈로그에 키를 설정하기 전까지 쿼리 기록 테이블의 `statement_text` 같은 필드가 비어 보입니다. 릴리즈 노트에 따르면 `system` 카탈로그의 키로 쿼리 기록을 복호화하는 기능이 2026년 10월 2일 GA입니다 |
| 대시보드 | 2024년 11월 1일 이후에 만든 AI/BI 대시보드만 암호화되고 CMK와 호환됨 |
| DBFS 마운트 | 워크스페이스 스토리지 키는 추가 DBFS 마운트를 암호화하지 않음. 마운트는 레거시 패턴이며 Unity Catalog 사용을 권장 |
| 서버리스 EBS | 서버리스 컴퓨트에는 원격 EBS 볼륨 암호화가 적용되지 않음. 서버리스 디스크는 수명이 짧다고 문서가 설명 |

> **참고** 문서는 키 유형을 별도로 정의하지 않습니다. 클라우드 KMS의 고객 키를 쓴다는 설명만 있습니다. 설정 절차는 "Configure customer-managed keys for encryption" 페이지를 따르십시오.

### 시크릿 스코프 (Secret scopes)

시크릿은 이름이 붙은 키-값 묶음이며, 그 묶음을 **스코프** 라고 부릅니다. 문서가 설명하는 스코프는 Databricks가 관리하는 암호화 데이터베이스에 저장되는 유형입니다.

| 항목 | 문서 기준 규칙 |
|---|---|
| 스코프 이름 | 워크스페이스 안에서 유일. 영숫자, 대시(`-`), 밑줄(`_`), `@`, 마침표 사용 가능. 128자 이하. 대소문자 구분 없음 |
| 키 이름 | 대소문자 구분 없음 |
| 스코프 이름 가시성 | 워크스페이스의 모든 사용자가 스코프 이름은 볼 수 있음 |
| 스코프 삭제 | 스코프의 모든 시크릿과 ACL이 함께 삭제됨 |
| 권장 단위 | 개인이 아니라 역할이나 애플리케이션 단위로 스코프를 맞춤 |

스코프 생성자는 기본으로 **MANAGE** 권한을 받습니다. 문서는 MANAGE가 시크릿 읽기, 시크릿 쓰기, 스코프 권한 부여를 허용한다고 설명합니다. UI에서 스코프를 만들 때 MANAGE 대상을 "Creator" 또는 "All workspace users"로 고를 수 있으며, "Creator" 선택은 Premium 플랜 이상이 필요합니다.

### 자격증명 편집 (Redaction)

노트북 출력에서 시크릿 값은 `[REDACTED]`로 가려집니다. 대상은 `dbutils.secrets.get()`으로 읽은 literal 값과 Spark 설정 속성에서 참조한 시크릿입니다.

> **주의** 편집은 우회를 막지 못합니다. 문서는 시크릿을 가공(변환)하면 편집이 적용되지 않는다고 명시합니다. 따라서 접근 제어가 실질적인 1차 방어선입니다.

SQL에서는 DQL 명령이 시크릿 함수를 호출할 때 편집이 적용됩니다. DML 명령은 `sha()`나 `aes_encrypt()` 같은 함수로 감싼 경우에만 시크릿을 읽을 수 있고, 쿼리 분석기는 암호화되지 않은 시크릿을 테이블에 저장하는 DML을 차단합니다.

## 3. 어떻게 쓰는가

### 스코프 만들고 시크릿 넣기

```bash
# 스코프를 만듭니다. CLI 0.205 이상이 필요합니다.
databricks secrets create-scope my-scope

# 시크릿을 넣습니다. 값은 JSON 본문의 string_value로 전달하며, 명령 이력에 남지 않도록 파일이나 표준 입력을 씁니다.
databricks secrets put-secret --json '{"scope": "my-scope", "key": "api-key", "string_value": "<value>"}'
```

> **주의** 위 예시의 `<value>`는 자리표시자입니다. 실제 값을 명령 줄에 직접 쓰면 셸 이력에 남습니다. 문서가 권장하는 것처럼 파일이나 표준 입력으로 넘기십시오.

### 노트북에서 읽기

```python
# 시크릿 값은 노트북 출력에서 [REDACTED]로 가려집니다.
api_key = dbutils.secrets.get(scope="my-scope", key="api-key")
```

시크릿 키 목록만 보려면 `dbutils.secrets.list("my-scope")`를 씁니다.

### 스코프 권한 부여

스코프 ACL은 `put-acl`로 설정합니다. 같은 주체에 대해 기존 권한을 덮어씁니다. 주체는 사용자(이메일), 서비스 프린시펄(애플리케이션 ID), 그룹(이름)으로 지정합니다.

스코프 권한은 CLI의 `put-acl`로 부여합니다. 명령 이름과 주체 지정 방식은 문서에 있지만, 이 장에서는 권한 수준 값을 예시로 쓰지 않습니다. 권한 수준의 전체 목록과 정확한 옵션은 Secret ACL 참고 페이지에서 확인하십시오. 현재 권한은 `list-acls`, `get-acl`로 보고, `delete-acl`로 제거합니다.

### 컴플라이언스 보안 프로필 확인

컴플라이언스 보안 프로필은 워크스페이스 설정에서 켭니다. 문서가 나열한 적용 대상 표준은 다음과 같습니다.

| 구분 | 표준 |
|---|---|
| 정부·공공 | CCCS Medium (Protected B), DoD IL5, FedRAMP High, FedRAMP Moderate, IRAP, ISMAP |
| 산업·보안 인증 | C5, HIPAA, HITRUST, K-FSI, PCI-DSS, TISAX, UK Cyber Essentials Plus |

> **참고** 위 구분 열은 이 장에서 나눈 것이며 문서의 분류가 아닙니다.

문서는 표준을 준수하지 않더라도 보안 기능만 쓰려고 프로필을 켤 수 있다고 설명합니다.

프로필을 켜면 다음 설정이 함께 적용됩니다(문서 기준).

- CIS Level 1 강화 OS 이미지와 FIPS 140 검증 암호 모듈
- 설정한 유지보수 기간 중 자동 클러스터 업데이트. 이 설정은 해당 워크스페이스에서 영구적으로 켜짐
- 리뷰 가능한 로그를 만드는 향상된 보안 모니터링 에이전트
- 클러스터와 SQL 웨어하우스에 AWS Nitro 인스턴스 유형 강제
- 모든 송신(egress) 트래픽에 TLS 1.2 이상. 메타스토어 통신 포함

릴리즈 노트에 따르면 2026년 10월 16일부터 컴플라이언스 보안 프로필 워크스페이스는 모든 표준을 지원하는 `READ METADATA` 권한이 기본으로 켜집니다. 같은 달 5일부터 Genie Code 예약 작업도 이 워크스페이스에서 기본으로 켜집니다.

> **주의** 프로필을 켜면 Enhanced Security and Compliance 추가 기능 요금이 부과된다고 문서가 명시합니다. 단가는 이 장에 쓰지 않습니다. 가격 페이지에서 확인하십시오.

### 향상된 보안 모니터링

컴플라이언스 프로필과 별도로 켤 수 있는 기능입니다. 문서 기준으로는 워크스페이스가 Enterprise 요금제여야 합니다. 워크스페이스 단위로 켜거나, 계정 수준 기본값으로 새 워크스페이스에 적용할 수 있습니다.

| 모니터링 대상 | 내용 |
|---|---|
| 강화 OS 이미지 | Ubuntu Advantage 기반, CIS Level 1 강화, FIPS 140 검증 암호 모듈 |
| 파일 무결성 | 클러스터 워커 VM의 파일 무결성과 보안 경계 위반 탐지 |
| 악성코드 | 호스트 OS와 Databricks Runtime 컨테이너 파일 시스템을 매일 검사 |
| 취약점 스캔 | 컨테이너 호스트 VM의 특정 CVE를 스캔 |

적용 대상은 클래식 컴퓨트 플레인의 리소스(클러스터, 서버리스가 아닌 SQL 웨어하우스)입니다. 서버리스 컴퓨트에는 추가 모니터링이 없습니다.

파일 무결성과 악성코드 검사 결과는 감사 로그 시스템 테이블에 기록되며, 취약점 스캔 보고서는 워크스페이스 관리자에게 이메일로 발송됩니다. Databricks는 보고서와 로그를 최소 1년 보관합니다. 감사 로그 전달을 구성했다면 보존, 수집, 분석은 고객 책임입니다. 문서는 "이 로그를 검토하는 것은 고객의 책임"이라고 명시합니다.

## 4. 트레이드오프

| 선택 | 장점 | 제약 |
|---|---|---|
| 고객 관리 키 | 키 통제권을 고객이 가짐 | Enterprise 요금제, 쿼리 기록·DBFS 마운트 등 적용 범위 제약 |
| 시크릿 스코프 (Databricks 관리) | 코드에서 자격증명 분리 | 스코프 이름은 모든 사용자에게 보임. 편집은 우회를 막지 못함 |
| 컴플라이언스 프로필 | 규제 요건에 맞는 설정을 한꺼번에 적용 | 추가 요금, 자동 클러스터 업데이트 강제, Nitro 인스턴스 제한 |
| 향상된 보안 모니터링 | 악성코드와 무결성 검사를 자동 수행 | 클래식 컴퓨트에만 적용, 로그 검토 책임은 고객 |

## 5. 주의사항

- **시크릿 값은 명령 줄 인자로 넘기지 마십시오.** 셸 이력과 프로세스 목록에 남을 수 있습니다.
- **스코프 ACL은 관리자와 생성자도 읽을 수 있다는 점을 전제로 설계하십시오.** 문서가 관리자, 생성자, 권한을 받은 사용자 모두 읽을 수 있다고 경고합니다.
- **고객 관리 키를 설정한 뒤 쿼리 기록을 확인하십시오.** `system` 카탈로그 키가 없으면 `statement_text`가 비어 보입니다.
- **컴플라이언스 프로필 적용 전 클러스터 업데이트 정책을 점검하십시오.** 자동 업데이트가 유지보수 기간에 실행됩니다.
- **컴플라이언스 프로필 워크스페이스에서 식별 정보를 자유 입력 필드에 넣지 마십시오.** 문서가 이름과 태그 같은 고객 정의 필드는 규제 경계 밖에서 처리될 수 있다고 경고합니다.
- **Genie One은 컴플라이언스 프로필 워크스페이스의 데이터를 계정 수준에서 집계하지 않는다고 문서가 명시합니다.** 계정 수준 현황 조회를 기대한다면 이 제약을 먼저 확인하십시오.

## 참고 문서

- [Data security and encryption overview](https://docs.databricks.com/aws/en/security/keys/)
- [Customer-managed keys for encryption](https://docs.databricks.com/aws/en/security/keys/customer-managed-keys)
- [Secret management overview](https://docs.databricks.com/aws/en/security/secrets/)
- [Use a secret in a Spark configuration property or environment variable](https://docs.databricks.com/aws/en/security/secrets/secrets-spark-conf-env-var)
- [Compliance security profile](https://docs.databricks.com/aws/en/security/privacy/security-profile)
- [Enhanced security monitoring](https://docs.databricks.com/aws/en/security/privacy/enhanced-security-monitoring)
- [Release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
