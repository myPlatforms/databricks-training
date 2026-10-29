# 볼륨과 외부 스토리지

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

## 한눈에 보기

테이블은 행과 열로 된 데이터를 거버넌스하고, **볼륨**(Volume)은 **파일** 을 거버넌스합니다. 공식 문서는 볼륨을 "비정형 데이터셋에 대한 거버넌스를 가능하게 하는 Unity Catalog 객체"로 설명합니다. CSV, 이미지, 모델 가중치, 로그처럼 테이블로 담기 어려운 파일을 카탈로그 안에 두고 권한을 줄 수 있습니다.

외부 스토리지에 접근하는 경로는 두 층입니다.

| 층 | 객체 | 역할 |
|---|---|---|
| 자산 층 | 볼륨 (관리형, 외부) | 파일 묶음을 객체로 만들고 권한을 줍니다. |
| 연결 층 | 스토리지 자격 증명, 외부 위치 | 클라우드 스토리지 경로에 접근하는 인증 정보와 경로를 묶습니다. |

볼륨은 관리형과 외부로 나뉩니다. 관리형 볼륨은 UC가 저장 위치를 정하고, 외부 볼륨은 이미 있는 클라우드 스토리지 경로를 가리킵니다.

## 1. 왜 필요한가

### 이전 방식의 한계

파일 기반 데이터는 흔히 스토리지 경로를 직접 노트북에 적고 접근했습니다. 이 방식에서는 다음 문제가 생깁니다.

- 스토리지 키나 역할이 노트북 코드에 노출되거나 여러 곳에 복사됩니다.
- 누가 어떤 파일을 읽었는지 Databricks 쪽에서 추적하기 어렵습니다.
- 경로가 바뀌면 여러 노트북과 잡을 같이 고쳐야 합니다.
- 같은 경로를 다른 워크스페이스에서 쓸 때 권한이 맞지 않는 경우가 생깁니다.

볼륨은 파일 경로를 `/Volumes/<카탈로그>/<스키마>/<볼륨>/...` 형태로 통일하고, 권한을 볼륨 객체에 붙입니다. 외부 스토리지 자격 증명은 스토리지 자격 증명 객체로 분리해 노트북 밖으로 뺍니다.

## 2. 어떻게 동작하는가

### 관리형 볼륨과 외부 볼륨

| 항목 | 관리형 볼륨 (Managed) | 외부 볼륨 (External) |
|---|---|---|
| 저장 위치 | 스키마에 연결된 UC 관리 스토리지 안 | 이미 있는 클라우드 객체 스토리지 경로 |
| 데이터 수명 | UC가 배치와 삭제를 관리합니다. 삭제 시 7일 보존이 적용된다고 공식 문서가 설명합니다. | 볼륨을 삭제해도 데이터는 클라우드 스토리지에 남습니다. |
| 접근 통제 | 모든 접근이 UC를 거칩니다. | UC가 권한을 관리하지만, 외부 도구는 직접 URI로 접근할 수 있습니다. |
| 대표 용도 | Databricks 안에서만 쓰는 워크로드 | 기존 스토리지를 Databricks와 외부 시스템이 함께 쓰는 경우 |

> **참고** 공식 문서는 관리형 볼륨을 Databricks 전용 워크로드의 가장 단순한 선택으로 설명합니다. 외부 볼륨은 데이터를 복사하지 않고 기존 스토리지에 거버넌스를 더하는 방식입니다.

> **주의** 외부 볼륨에 대해 외부 시스템이 클라우드 URI로 직접 읽고 쓰면 UC 권한이 적용되지 않습니다. 공식 문서는 이런 경우 자격 증명 벤딩(credential vending)이나 클라우드 네이티브 접근 제어를 쓰라고 권장합니다.

### 파일 경로

볼륨의 파일은 다음 형식으로 접근합니다.

```
/Volumes/<catalog>/<schema>/<volume>/<path>/<file-name>
```

Apache Spark에서는 `dbfs:/` 접두사도 쓸 수 있습니다.

```
dbfs:/Volumes/<catalog>/<schema>/<volume>/<path>/<file-name>
```

카탈로그, 스키마, 볼륨 디렉터리는 UC가 관리하며 읽기 전용입니다. 그 아래 `<path>` 부분만 파일을 추가하거나 지울 수 있습니다.

### 요구 사항

| 항목 | 내용 |
|---|---|
| 지원 범위 | Unity Catalog 전용 기능 |
| 최소 런타임 | Databricks Runtime 13.3 LTS 이상 |
| 필요한 권한 | `READ VOLUME`(읽기), `WRITE VOLUME`(쓰기), `CREATE VOLUME`(생성), `MANAGE`, `APPLY TAG` |

공식 문서의 볼륨 페이지는 필요한 권한의 세부 목록을 싣지 않고 별도 문서로 안내합니다. 위 표의 권한 이름은 권한 참조 페이지의 정의입니다.

## 3. 어떻게 쓰는가

### 볼륨 만들기

```sql
-- 관리형 볼륨 (LOCATION 없이 생성)
CREATE VOLUME myManagedVolume
COMMENT 'This is my example managed volume';

-- 외부 볼륨 (LOCATION으로 기존 스토리지 경로 지정)
CREATE EXTERNAL VOLUME IF NOT EXISTS myCatalog.mySchema.myExternalVolume
COMMENT 'This is my example external volume'
LOCATION 's3://my-bucket/my-location/my-path';
```

> **참고** 관리형 볼륨은 `LOCATION`을 지정하지 않습니다. 공식 문서는 "You do not need to specify a location when creating a managed volume"이라고 설명합니다.

### 파일 읽고 쓰기

노트북이나 잡에서 볼륨 경로를 그대로 씁니다.

```python
# 볼륨 디렉터리 목록 조회 (공식 문서 예제)
dbutils.fs.ls("/Volumes/MyCatalog/MySchema/MyVolume")
```

볼륨의 파일을 SQL 테이블 값으로 참조하는 `FILE` 타입은 Beta입니다. 사용자별 개인 볼륨인 My Files도 Beta입니다.

### 권한 부여

볼륨 권한은 `GRANT`로 줍니다. 볼륨 권한 구문은 권한 참조 페이지의 정의를 따르며, 아래 예는 같은 형식을 쓴 것입니다.

```sql
-- 분석팀에 볼륨 읽기 권한 부여
GRANT READ VOLUME ON VOLUME mycatalog.myschema.myvolume TO `analytics-team`;

-- 적재 팀에 볼륨 쓰기 권한 부여
GRANT WRITE VOLUME ON VOLUME mycatalog.myschema.myvolume TO `ingest-team`;
```

### 스토리지 자격 증명과 외부 위치

외부 볼륨이나 외부 테이블이 클라우드 경로에 접근하려면 두 객체가 필요합니다.

| 객체 | 설명 | 예 (AWS) |
|---|---|---|
| 스토리지 자격 증명 | 장기 클라우드 자격 증명(IAM 역할 등)을 담는 UC 객체 | S3 버킷에 접근하는 IAM 역할 |
| 외부 위치 | 스토리지 경로와 스토리지 자격 증명을 짝지은 객체 | `s3://my-bucket/my-path/`와 위 IAM 역할의 짝 |

공식 문서가 설명하는 순서는 다음과 같습니다.

1. 장기 클라우드 자격 증명(예: IAM 역할)을 담은 스토리지 자격 증명 객체를 만듭니다.
2. 스토리지 경로와 그 자격 증명 객체를 참조하는 외부 위치 객체를 만듭니다.
3. 외부 테이블이나 외부 볼륨을 만들 때 외부 위치 안의 경로를 씁니다.

> **참고** 이 장에서는 `CREATE STORAGE CREDENTIAL`과 `CREATE EXTERNAL LOCATION`의 SQL 문법을 확인하지 못했습니다. 공식 문서 페이지는 개요만 싣고, 세부 절차는 "Connect to an AWS S3 external location", "Manage storage credentials", "Manage external locations" 페이지로 안내합니다. 실제 문법과 옵션은 그 페이지에서 확인하십시오.

공식 문서는 권한도 나눠서 주라고 설명합니다.

- 스토리지 자격 증명을 만들고 쓰는 권한은 외부 위치를 만들어야 하는 사용자에게만 줍니다.
- 외부 위치를 만들고 쓰는 권한은 외부 테이블, 외부 볼륨, 관리형 스토리지 위치를 만들어야 하는 사용자에게만 줍니다.

## 4. 트레이드오프

### 한도

공식 문서의 자원 한도 페이지에 있는 항목입니다.

| 항목 | 한도 | 범위 | 고정 여부 |
|---|---|---|---|
| 볼륨 | 10,000 | 스키마 | 아님 |
| 볼륨 | 100,000 | 메타스토어 | 아님 |
| 스토리지 자격 증명과 서비스 자격 증명 합계 | 1,000 | 메타스토어 | 아님 |
| 외부 위치 | 10,000 | 메타스토어 | 아님 |
| 연결(Connection) | 1,000 | 메타스토어 | 아님 |

> **참고** 공식 문서는 스토리지 자격 증명과 서비스 자격 증명의 한도를 **합산** 해서 1,000으로 설명합니다. "스토리지 자격 증명 1,000개"로 따로 있는 것이 아닙니다.

### 관리형과 외부 선택

| 상황 | 권장 |
|---|---|
| Databricks 안에서만 파일을 쓰고 접근 통제를 한곳에서 하고 싶음 | 관리형 볼륨 |
| 이미 클라우드 스토리지에 있는 파일을 복사하지 않고 거버넌스를 붙이고 싶음 | 외부 볼륨 |
| 외부 시스템이 같은 경로를 직접 읽고 씀 | 외부 볼륨 + 클라우드 측 접근 제어(UC 권한만으로는 부족) |

### 언제 쓰지 않는가

- 파일 수집 방식(전송 도구, 적재 파이프라인)의 비교는 이 장의 범위가 아닙니다. 적재 방법은 해당 장과 공식 문서의 수집 가이드를 참고하십시오.
- 파일 하나를 SQL로 자주 조회해야 하면 테이블로 적재하는 편이 낫습니다. 볼륨의 `FILE` 타입은 Beta입니다.

## 5. 주의사항

> **주의** 공식 문서는 관리형 볼륨의 삭제에 7일 보존이 적용된다고 설명합니다. 복구 절차와 보존 기간이 지난 뒤의 동작은 이 장에서 확인한 원문에 없으므로, 삭제 전에 공식 문서에서 직접 확인하십시오.

> **주의** 외부 볼륨을 삭제해도 클라우드 스토리지의 데이터는 남습니다. 반대로 남은 데이터는 UC 권한의 대상이 아니므로, 외부 경로를 직접 접근할 수 있는 주체를 따로 관리해야 합니다.

> **주의** Files API 3.0은 2026년 10월 23일 릴리즈 노트에서 Beta로 공지되었습니다. 다중 파트 업로드(5000 MiB 초과 파일)와 조건부 작업(현재 버전 기준의 업로드, 다운로드, 삭제)을 지원한다고 설명합니다. Beta이므로 운영 코드에 넣기 전에 상태를 확인하십시오.

- 2026년 10월 27일 릴리즈 노트는 **볼륨 파일 편집** 을 GA로 공지했습니다. 워크스페이스의 파일 편집기에서 볼륨 파일을 직접 편집할 수 있습니다. 편집 권한 요구 사항은 릴리즈 노트에 명시되어 있지 않으므로 권한 설계 전에 원문을 확인하십시오.
- 볼륨 경로에서 쓰기 전에 `WRITE VOLUME` 권한과 상위 카탈로그·스키마의 진입 권한(`USE CATALOG`, `USE SCHEMA`)이 함께 있어야 합니다. 진입 권한은 [권한 모델과 소유권](privileges-and-ownership.md)에서 설명했습니다.
- 볼륨 태그(`APPLY TAG`)와 정책 연계는 「거버넌스 태그와 ABAC 정책」 페이지의 거버넌스 태그 체계를 따르십시오.

## 참고 문서

- [Unity Catalog volumes](https://docs.databricks.com/aws/en/volumes/)
- [CREATE VOLUME (SQL reference)](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-volumes)
- [Storage credentials](https://docs.databricks.com/aws/en/connect/unity-catalog/cloud-storage/storage-credentials)
- [External locations](https://docs.databricks.com/aws/en/connect/unity-catalog/cloud-storage/external-locations)
- [Unity Catalog resource limits](https://docs.databricks.com/aws/en/resources/limits)
- [Databricks release notes, October 2026](https://docs.databricks.com/aws/en/release-notes/product/2026/october)
