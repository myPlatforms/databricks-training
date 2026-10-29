# REST API와 Databricks Connect

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 두 가지 접근 방식을 다룹니다. 하나는 모든 기능에 접근할 수 있는 **REST API** 이고, 다른 하나는 로컬 IDE나 Python 프로세스에서 Databricks 컴퓨트에 Spark 코드를 실행하는 **Databricks Connect** 입니다. SDK와 CLI로 충분하지 않을 때 어떤 방식을 고를지 판단하는 기준도 함께 정리합니다.

## 1. 세 방식의 위치

개발자 도구 개요 페이지는 SDK가 없는 언어나 고급 시나리오에서 REST API를 쓰라고 안내합니다. 같은 개요 페이지에 Databricks Connect는 로컬 IDE에서 대화형 개발과 디버깅을 하는 용도로 나옵니다.

| 방식 | 용도 | 이 장에서 다루는 페이지 |
|------|------|-------------------------|
| CLI | 셸 명령, 스크립트, 번들 | [설치와 인증](../cli/install-and-auth.md) |
| Python SDK | 애플리케이션 코드에서 API 호출 | [Python SDK](python-sdk.md) |
| REST API | SDK가 없는 언어, 고급 자동화, 세부 제어 | 이 페이지 |
| Databricks Connect | 로컬 Python·Scala·R에서 Spark 코드 실행 | 이 페이지 |

## 2. REST API

### 2-1. 호출 구성 요소

REST API 레퍼런스 소개 페이지는 호출에 필요한 요소를 다음처럼 나열합니다. 페이지에 기본 URL 형식은 명시되어 있지 않습니다.

| 요소 | 내용 |
|------|------|
| 워크스페이스 인스턴스 | 호출 대상 워크스페이스 주소 |
| HTTP 메서드 | `GET`, `POST` 등 작업 유형 |
| 경로 | 예: `/api/2.0/clusters/get` |
| 인증 정보 | 아래 인증 설명 참고 |
| 요청 페이로드 또는 쿼리 파라미터 | 작업에 따라 다름 |

클러스터 조회를 `curl`로 호출하면 이 요소를 모두 직접 넣어야 합니다. 명령 한 줄로 끝나는 CLI와 비교하면 차이가 분명합니다([명령 그룹과 출력 형식](../cli/commands-and-output.md)에서 같은 작업을 CLI로 보여 줍니다).

### 2-2. 인증

소개 페이지는 사용자와 서비스 프린시펄 모두 OAuth 사용을 강하게 권장하고, OAuth를 쓸 수 없을 때 개인 액세스 토큰(PAT)을 쓸 수 있다고 설명합니다. 클라우드별로 다음 방식도 언급합니다.

| 클라우드 | 페이지가 언급하는 방식 |
|----------|------------------------|
| 공통 | OAuth 권장, PAT 대체 |
| Azure | 관리 ID(managed identity), Microsoft Entra ID 토큰 |
| GCP | Google ID 토큰 |

헤더 형식이나 `curl` 예시는 이 페이지에 없습니다. 헤더를 넣는 방법은 인증 관련 문서를 확인하십시오. 자격 증명을 자동으로 찾아 헤더를 만드는 일은 SDK가 해 주므로, 가능하면 SDK를 쓰는 편이 안전합니다.

### 2-3. API 버전 표기

소개 페이지에서 확인된 버전 표기는 경로의 `2.0`입니다. 이 페이지는 Jobs API의 최신 버전 번호를 확인하지 못했습니다. 따라서 이 장에서는 버전 번호를 특정하지 않습니다. 호출하려는 엔드포인트의 레퍼런스 페이지에서 경로를 확인하십시오.

> **주의** "7.6.x-gpu-ml-scala2.12"처럼 점이 들어간 문자열은 API 버전이 아니라 Databricks Runtime 버전 표기입니다. 두 개념을 혼동하지 마십시오.

### 2-4. 언제 REST API를 쓰는가

| 상황 | 권장 |
|------|------|
| Python으로 애플리케이션을 짠다 | Python SDK |
| 셸 스크립트에서 한 번 조회하거나 변경한다 | CLI |
| 쓰려는 언어에 SDK가 없다 | REST API |
| SDK에 아직 없는 엔드포인트를 쓴다 | REST API |
| 응답 원본을 그대로 로깅·검증한다 | REST API (원본 JSON 확인) |

> **참고** 개발자 도구 개요 페이지는 JavaScript, Java, Go, R용 SDK 페이지도 나열합니다. 이 페이지에서는 각 SDK의 세부 사항을 확인하지 않았습니다.

## 3. Databricks Connect

### 3-1. 개념

Databricks Connect는 로컬 Python, Scala, R 프로세스에서 Spark 코드를 작성하고, 실행은 Databricks 컴퓨트에서 하도록 해 주는 도구입니다. 개요 페이지는 이 도구가 Spark Connect를 확장해 Databricks 컴퓨트 모드와 Unity Catalog를 지원한다고 설명합니다. 개요 페이지는 Databricks Runtime 13.3 LTS 이상을 기준으로 다룬다고 명시합니다.

| 언어 | 개요 페이지 | 튜토리얼 |
|------|-------------|----------|
| Python | 있음 | 클래식 컴퓨트, 서버리스 컴퓨트 |
| Scala | 있음 | 클래식 컴퓨트, 서버리스 컴퓨트 (JAR 빌드) |
| R | 있음 | 튜토리얼 섹션 |

개요 페이지와 서버리스 튜토리얼 페이지에는 상태 라벨이 없습니다.

### 3-2. 서버리스 Python 튜토리얼 요약

서버리스 튜토리얼은 다음 조건을 씁니다.

- Python 3.12
- Databricks Connect 17.3 LTS
- 설치 명령: `pip install "databricks-connect==17.3.*"`

> **주의** 튜토리얼이 쓰는 버전은 17.3 계열입니다. 튜토리얼은 다른 Python 버전도 호환되면 쓸 수 있다고 설명합니다. 실제로 쓰는 워크스페이스 DBR 또는 서버리스 환경 버전과 맞는지 확인하십시오.

인증은 CLI 로그인 후 프로필을 씁니다.

```bash
databricks auth login --host <workspace-url>
```

프로필의 `DEFAULT` 항목에 `serverless_compute_id = auto`를 넣거나, 환경 변수로 설정합니다.

```bash
export DATABRICKS_SERVERLESS_COMPUTE_ID=auto
```

세션 생성 코드는 다음과 같습니다. 튜토리얼 원문에서는 `DatabricksSession` 임포트 행이 추출 텍스트에 없었습니다. 임포트 경로는 튜토리얼 원문에서 확인하십시오.

```python
spark = DatabricksSession.builder.serverless().profile("<profile-name>").getOrCreate()

df = spark.range(10)
df.show()
```

환경 변수를 설정했다면 프로필 인수 없이도 쓸 수 있는 형태가 튜토리얼에 나옵니다.

```python
spark = DatabricksSession.builder.getOrCreate()
```

### 3-3. 클래식 컴퓨트

클래식 컴퓨트 연결은 Python과 Scala 튜토리얼에 각각 있습니다. 개요 페이지는 서버리스와 클래식 각각의 튜토리얼이 있다고만 적습니다. 클래식 연결에 필요한 클러스터 ID나 설정 값은 이 페이지에서 옮기지 않았습니다. 클래식 튜토리얼을 직접 확인하십시오.

## 4. 두 방식을 고르는 기준

| 질문 | 답이 "예"라면 |
|------|----------------|
| 내 로컬 IDE에서 Spark 코드를 디버깅하고 싶은가 | Databricks Connect |
| 워크스페이스 리소스(잡, 볼륨, 권한)를 호출하고 싶은가 | Python SDK 또는 CLI |
| SDK가 없는 언어인가 | REST API |
| 스크립트에서 한 번 실행하는 조회인가 | CLI |

Spark DataFrame을 다루는 로직은 Databricks Connect로, 리소스 관리는 SDK나 CLI로 나누는 구성이 흔합니다.

## 5. 트레이드오프

| 방식 | 장점 | 제약 |
|------|------|------|
| REST API | 모든 엔드포인트에 접근 | 인증·요청 구성을 직접 관리 |
| Python SDK | 인증과 대기 로직 내장 | Beta 라벨, 버전 고정 필요 |
| Databricks Connect | 로컬 IDE에서 Spark 실행 | 로컬 Python 버전과 클라이언트 버전을 맞춰야 함 |

## 6. 주의사항

- **버전 짝을 맞춥니다.** Databricks Connect 클라이언트 버전과 대상 컴퓨트 버전이 맞아야 합니다. 튜토리얼의 17.3 계열을 기준으로 시작하고, 다른 버전은 호환성을 확인합니다.
- **임시 토큰을 소스에 두지 않습니다.** 인증은 프로필이나 환경 변수로 합니다.
- **REST 호출은 재시도를 설계합니다.** 페이지네이션과 일시 오류 처리는 직접 구현해야 합니다.
- **문서 버전 확인.** 개요 페이지의 13.3 LTS 기준과 튜토리얼의 17.3 기준이 다르므로, 워크스페이스에서 쓰는 버전의 문서를 봅니다.

## 참고 문서

- [Databricks REST API reference](https://docs.databricks.com/api/workspace/introduction)
- [Databricks 개발자 도구 개요](https://docs.databricks.com/aws/en/dev-tools/)
- [Databricks Connect](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/)
- [Tutorial: Run Python code on serverless compute](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/tutorial-serverless)
