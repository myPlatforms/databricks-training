# 데이터 공유와 Clean Rooms

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 한눈에 보기

공식 문서의 현재 명칭은 **OpenSharing** 입니다(구 명칭 Delta Sharing). 공식 페이지 본문은 플랫폼을 OpenSharing으로 부르며, Delta Sharing이라는 이름은 오픈소스 프로젝트 링크와 커넥터 이름(예: OpenSharing Spark 커넥터)에 남아 있습니다. 이 장도 공식 문서 명칭을 따릅니다.

OpenSharing은 **프로바이더**(데이터를 공유하는 쪽)가 **공유**(Share)를 만들어 **리시피언트**(받는 쪽)에게 읽기 전용으로 제공하는 기능입니다. 공유에 담을 수 있는 자산은 테이블, 뷰, 볼륨, 모델, 노트북 파일입니다.

**Clean Rooms** 는 한 단계 더 나아갑니다. 여러 참여자가 **각자의 원본 데이터를 서로에게 노출하지 않고** 공동으로 분석하는 보안 환경입니다. 데이터는 중앙 Clean Room으로 옮겨져 노트북으로만 처리되고, 결과는 참여자별 임시 읽기 전용 테이블로 나옵니다.

| 목적 | 기능 | 데이터 노출 |
|---|---|---|
| 조직 간에 읽기 전용 데이터를 제공 | OpenSharing 공유 | 수신자가 공유 자산을 읽습니다. |
| 여러 조직이 서로의 원본 없이 공동 분석 | Clean Rooms | 참여자끼리 원본을 직접 보지 못합니다. |

## 1. 왜 필요한가

### 이전 방식의 한계

조직 간 데이터 공유는 흔히 다음 방식으로 이루어졌습니다.

- 파일을 내려받아 메일이나 파일 전송으로 보냅니다. 복사본이 여러 곳에 생기고 버전이 엇갈립니다.
- 공유 전용 데이터베이스를 따로 만들어 적재합니다. 원본과 사본을 같이 관리해야 합니다.
- 상대방 자격 증명을 나눠 주는 방식은 자격 증명 노출과 회수 문제가 큽니다.

OpenSharing은 **사본을 만들지 않고** 원본 테이블을 읽기 전용으로 제공합니다. 권한은 공유와 리시피언트 객체에 달리므로, 공유를 회수하면 접근도 즉시 끊깁니다.

Clean Rooms는 "데이터를 합치지 않고 분석 결과만 얻고 싶다"는 요구에서 나옵니다. 양쪽 데이터를 한곳에 복사하지 않으면서도 같은 노트북으로 계산하게 하는 구조입니다.

## 2. 어떻게 동작하는가

### 공유 모델의 객체

| 객체 | 역할 |
|---|---|
| 공유(Share) | 테이블, 뷰, 볼륨, 모델, 노트북 파일을 묶은 읽기 전용 묶음 |
| 프로바이더(Provider) | 공유를 만드는 쪽. Databricks 기반 프로바이더는 Unity Catalog가 켜진 워크스페이스가 필요합니다. |
| 리시피언트(Recipient) | 공유를 받는 쪽. 보통 Unity Catalog 보안 객체로 표현됩니다. |

리시피언트에 부여할 수 있는 권한은 `SELECT` 하나뿐입니다. 공식 문서는 "`SELECT` is the only privilege that you can grant a recipient on a share"라고 명시합니다. 리시피언트 객체 자체에는 권한을 줄 수 없습니다.

### 두 가지 공유 방식

| 방식 | 수신자 조건 | 인증 | 지원 자산 |
|---|---|---|---|
| Databricks-to-Databricks | Unity Catalog가 켜진 Databricks 워크스페이스를 쓰는 수신자 | 토큰 불필요 | 테이블, 뷰, 노트북, 볼륨, 모델 |
| Databricks-to-Open | Databricks를 쓰지 않아도 됨 | 장기 베어러 토큰 또는 OIDC 연합 | 공식 문서의 Open 공유 페이지에서 확인 |

공식 문서는 Databricks-to-Open을 "Open sharing lets you share data with any user, whether or not they have access to Databricks"라고 설명합니다. 이 외에 직접 운영하는 오픈소스 OpenSharing 서버와 SAP Business Data Cloud(BDC) 커넥터도 옵션으로 나열됩니다.

> **참고** 2026년 9월 22일 릴리즈 노트는 "Invite OpenSharing recipients by email (Beta)"을 공지했습니다. 공식 문서는 "OpenSharing by email"을 Beta로 표기하며, 계정 관리자가 계정 콘솔의 Previews 페이지에서 켜야 한다고 설명합니다.

### 공유 안의 테이블 이력

공식 문서에 따르면 공유에 테이블을 추가할 때 `WITH HISTORY`와 `WITHOUT HISTORY` 옵션이 있습니다.

- 기본값은 Databricks Runtime 16.2 이상에서 `WITH HISTORY`, 그 이전 버전에서는 `WITHOUT HISTORY`입니다.
- 삭제 벡터(deletion vectors)나 열 매핑(column mapping)이 켜진 테이블은 `WITH HISTORY`로 공유해야 합니다.
- 일부 테이블은 공유할 수 없습니다. 공식 문서는 공유할 수 없는 테이블 목록을 별도 페이지로 안내합니다.

### Clean Rooms 구조

공식 문서가 설명하는 Clean Rooms의 구성은 다음과 같습니다.

| 구성 요소 | 설명 |
|---|---|
| 중앙 Clean Room | Databricks가 관리하는 격리된 임시 환경. 참여자가 여기로 자산을 공유합니다. |
| 참여자(Collaborator) | 한 Clean Room에 최대 10명(곳)까지 참여할 수 있습니다. |
| 노트북 | 중앙 Clean Room에서 공유 데이터를 처리하는 코드. 모든 노트북은 참여자 승인을 받아야 실행됩니다. 최신 버전만 실행할 수 있습니다. |
| 출력(Output) | 노트북이 만든 출력 테이블. 각 참여자의 메타스토어에 임시 읽기 전용으로 나타납니다. |

Clean Room의 신뢰 모델은 "모든 참여자가 동등한 권한"입니다. 생성자도 특별한 권한이 없고, 노트북은 다른 참여자의 승인이 있어야 돌아갑니다. 패키지형 Clean Room은 예외로 프로바이더와 소비자 모델을 쓴다고 공식 문서가 설명합니다.

다음은 공식 문서가 밝힌 **보이는 것과 보이지 않는 것** 의 구분입니다.

| 구분 | 내용 |
|---|---|
| 다른 참여자에게 보이지 않음 | 다른 참여자의 테이블, 뷰, 볼륨 데이터. 열 이름과 타입과 공유 메타데이터만 보입니다. |
| 다른 참여자에게 공유됨 | Clean Room 이름, 중앙 Clean Room의 클라우드와 리전, 조직 이름, 공유 식별자, 공유 자산 별칭, 열 메타데이터, 노트북(읽기 전용), 출력 테이블(읽기 전용, 임시), Clean Room 이벤트 시스템 테이블, 실행 이력 |
| 중앙 Clean Room에만 공유됨 | 위 항목과 함께 읽기 전용 테이블, 볼륨, 뷰, 노트북 자체 |

Clean Room은 생성 후 참여자를 추가할 수 없도록 잠깁니다. Clean Room을 삭제하면 중앙 환경도 무효가 됩니다.

## 3. 어떻게 쓰는가

### 공유 만들기와 자산 추가

```sql
-- 공유 생성
CREATE SHARE [IF NOT EXISTS] <share-name>
[COMMENT "<comment>"];

-- 공유에 테이블 추가 (이력 옵션 명시)
ALTER SHARE <share-name> ADD TABLE <catalog-name>.<schema-name>.<table-name>
[COMMENT "<comment>"] [PARTITION(<clause>)] [AS <alias>] [WITH HISTORY | WITHOUT HISTORY];
```

공식 문서의 요구 사항입니다.

- 공유를 만들려면 메타스토어에 대한 `CREATE SHARE` 권한이 필요합니다. 메타스토어가 연결된 워크스페이스에서 실행해야 합니다.
- 테이블을 추가하려면 공유 소유자이고, 상위 카탈로그에 `USE CATALOG`, 상위 스키마에 `USE SCHEMA`, 그리고 테이블에 `SELECT`가 있어야 합니다. `SELECT`를 유지해야 수신자가 계속 읽을 수 있습니다.
- `PARTITION`과 `AS <alias>`는 스키마 전체를 추가할 때는 쓸 수 없습니다.
- 스키마 전체를 추가하려면 `ALTER SHARE ... ADD SCHEMA`를 쓰며, SQL 웨어하우스나 Databricks Runtime 13.3 LTS 이상이 필요합니다.

### 리시피언트에게 공유 열기

```sql
-- 리시피언트에게 공유 조회 권한 부여
GRANT SELECT ON SHARE <share-name> TO RECIPIENT <recipient-name>;

-- 권한 회수
REVOKE SELECT ON SHARE <share-name> FROM RECIPIENT <recipient-name>;
```

요구 사항은 다음과 같습니다.

- Unity Catalog 메타스토어가 연결된 워크스페이스를 써야 합니다.
- Unity Catalog 접근 모드를 지원하는 SQL 웨어하우스나 클러스터를 써야 합니다.
- 공유와 리시피언트가 이미 정의되어 있어야 합니다.
- 메타스토어 관리자는 항상 권한을 줄 수 있습니다. 그 밖의 사용자는 공유와 리시피언트에 대한 위임 권한이나 소유권이 필요합니다.
- 회수는 메타스토어 관리자, `USE SHARE` 권한을 가진 사용자, 또는 공유 소유자가 할 수 있습니다.

> **주의** 권한을 회수하기 전에 리시피언트가 이 공유를 이미 쓰는 파이프라인이나 대시보드가 있는지 확인하십시오. 회수하면 수신자 쪽 조회가 실패하므로, 소비자를 미리 파악하지 못하면 장애가 뒤늦게 드러납니다. 실제 조회 주체는 공유 감사 로그(Audit and monitor 페이지)에서 먼저 확인하십시오.

## 4. 트레이드오프

### 공유 방식 선택

| 상황 | 권장 방식 |
|---|---|
| 같은 조직 안의 다른 Databricks 워크스페이스 | Databricks-to-Databricks |
| 파트너가 Databricks를 쓰지 않음 | Databricks-to-Open (토큰 또는 OIDC 연합) |
| 직접 운영하는 공유 서버 필요 | 직접 운영하는 오픈소스 OpenSharing 서버 |
| 여러 기업이 원본 없이 공동 분석 | Clean Rooms |

### 한계와 비용

- 공유는 **읽기 전용** 입니다. 수신자가 공유를 편집할 수 없습니다.
- 공유와 리시피언트에는 한도가 있습니다. 메타스토어당 공유 1,000개, 카탈로그당 공유 20개, 메타스토어당 리시피언트 5,000개, 메타스토어당 프로바이더 1,000개입니다. 공식 자원 한도 페이지에서 확인한 값입니다.
- 외부 수신자가 데이터를 가져가면 이그레스(egress) 비용이 발생할 수 있습니다. 공식 문서는 이그레스 비용 관리 페이지를 따로 둡니다. 비용 수준의 수치는 이 장에서 확인하지 않았습니다.
- Clean Rooms 자체의 요금 구조는 이 장에서 확인하지 않았습니다. 서버리스 컴퓨트 비용은 Databricks 가격 페이지에서 확인하십시오.

### 상태 요약

| 기능 | 상태 | 근거 |
|---|---|---|
| 외부 Delta 테이블 공유 | GA (2026-09-15 공지) | 릴리즈 노트 |
| 외부 Iceberg 테이블 공유 | GA (2026-09-11 공지) | 릴리즈 노트 |
| 관리형 Iceberg 테이블 공유 | GA (2026-08-14 공지) | 릴리즈 노트 |
| 기본 스토리지 테이블 공유 | GA (2026-08-13 공지) | 릴리즈 노트 |
| 메트릭 뷰 공유 | GA (2026-09-24 공지) | 릴리즈 노트 |
| 공유 객체의 테이블 업데이트 트리거 | GA (2026-09-30 공지) | 릴리즈 노트 |
| SecureConnect(방화벽 뒤 공유) | GA (2026-08-13 공지) | 릴리즈 노트 |
| 이메일로 OpenSharing 수신자 초대 | Beta (2026-09-22 공지) | 공식 문서, 릴리즈 노트 |
| Clean Room: 공유 출력 | GA (2026-10-13 공지) | 릴리즈 노트 |
| Clean Room: JAR 워크로드 | GA (2026-10-13 공지) | 릴리즈 노트 |
| Clean Room: 서버리스 GPU 노트북 | GA (2026-10-28 공지) | 릴리즈 노트 |
| Clean Room: 신원 해석 프로바이더를 한 단계로 생성 | GA (2026-10-13 공지) | 릴리즈 노트 |

> **참고** Clean Rooms 페이지 자체에는 상태 라벨이 없습니다(마지막 업데이트 2026-10-08). 위 표의 GA는 개별 릴리즈 노트 항목의 표기이며, Clean Rooms 기능 전체의 상태로 읽지 마십시오.

### Clean Rooms 요구 사항과 제약

| 항목 | 내용 |
|---|---|
| 워크스페이스 | 서버리스 컴퓨트 사용 가능, Unity Catalog 사용, 메타스토어에서 OpenSharing 사용 |
| 스토리지 방화벽 | 참여자의 S3 버킷이 방화벽 뒤에 있으면 Clean Room 서버리스 컴퓨트가 기본으로는 접근할 수 없습니다. 우회 방법은 Databricks 기본 스토리지 사용, Databricks 서버리스 컴퓨트 허용, SecureConnect 사용 중 하나입니다. |
| 기본 스토리지 볼륨 | 중앙 Clean Room이 볼륨과 같은 클라우드와 리전에 있을 때만 접근할 수 있습니다. 공식 문서는 테이블이 아니라 볼륨에 적용된다고 설명합니다. |
| 런타임 | 필요한 Databricks Runtime 버전에 서비스 자격 증명 Scala 라이브러리가 포함되지 않는다고 공식 문서가 설명합니다. 세부 버전은 원문 확인이 필요합니다. |

## 5. 주의사항

> **주의** 공유는 Databricks-to-Open 방식에서 장기 베어러 토큰을 쓸 수 있습니다. 토큰이 유출되면 해당 리시피언트 접근이 공유 회수 전까지 계속됩니다. 토큰 기반 리시피언트는 정기적으로 점검하고, 가능하면 OIDC 연합을 검토하십시오.

> **주의** GRANT 정책이 걸린 모델은 OpenSharing으로 공유할 수 없습니다. 공식 문서가 명시한 제약입니다. 모델 공유를 계획하기 전에 해당 모델에 GRANT 정책이 있는지 확인하십시오(「거버넌스 태그와 ABAC 정책」 페이지 참조).

> **주의** Clean Room 노트북은 참여자 승인을 받아야 실행되고, 최신 버전만 실행된다고 공식 문서가 설명합니다. 노트북을 고친 뒤의 승인 흐름을 참여자와 미리 합의하십시오.

- 공유 자산에 열 마스크나 행 필터가 걸려 있을 때의 동작은 이 장에서 확인한 원문에 명시되지 않았습니다. 공유 설계 전에 공식 문서의 공유 페이지에서 직접 확인하십시오.
- 공유 감사와 모니터링은 공식 문서의 Audit and monitor 페이지에 있으며, 감사 로그와 시스템 테이블 세부는 12장에서 다룹니다.
- 참여자에게 돌아가는 결과는 노트북이 만든 출력 테이블입니다. 원본 데이터를 직접 내려받는 설계는 Clean Rooms 목적과 맞지 않으므로, 결과 테이블 설계를 먼저 하십시오.

## 참고 문서

- [OpenSharing overview](https://docs.databricks.com/aws/en/opensharing/)
- [Share data (Databricks-to-Databricks)](https://docs.databricks.com/aws/en/opensharing/share-data-databricks)
- [Share data (Databricks-to-Open)](https://docs.databricks.com/aws/en/opensharing/share-data-open)
- [Create shares](https://docs.databricks.com/aws/en/opensharing/create-share)
- [Grant and revoke access](https://docs.databricks.com/aws/en/opensharing/grant-access)
- [Clean Rooms](https://docs.databricks.com/aws/en/clean-rooms/)
- [Resource limits](https://docs.databricks.com/aws/en/resources/limits)
- [Databricks release notes, September 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/september)
- [Databricks release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
