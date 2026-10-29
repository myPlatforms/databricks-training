# Python SDK: WorkspaceClient와 AccountClient

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

Databricks SDK for Python(`databricks-sdk`)은 Python 코드에서 워크스페이스와 계정의 REST API를 타입이 있는 객체로 호출하게 해 주는 라이브러리입니다. 이 페이지는 설치, 두 클라이언트(`WorkspaceClient`, `AccountClient`), 인증 체인, 그리고 운영 코드에서 주의할 점을 다룹니다. REST API 직접 호출과 Databricks Connect는 [REST API와 Databricks Connect](rest-api-and-connect.md)에서 다룹니다.

## 1. 왜 필요한가

REST API를 `requests`로 직접 부르면 다음을 매번 구현해야 합니다.

- 인증 헤더와 토큰 갱신
- 엔드포인트 경로와 요청·응답 JSON 구조
- 장기 실행 작업(예: 클러스터 기동, 잡 완료)을 기다리는 로직
- 페이지네이션

SDK는 이 부분을 감쌉니다. SDK 문서는 장기 실행 작업 대기와 페이지네이션도 별도 페이지로 안내합니다. 기존 배포 시스템에 Python 코드를 붙이거나, 웹 서비스 안에서 Databricks 리소스를 다루는 경우에 특히 유용합니다.

## 2. 상태

| 항목 | 상태 | 근거 |
|------|------|------|
| Databricks SDK for Python | Beta | SDK 페이지 원문: "The Databricks SDK for Python is in Beta and is okay to use in production." |

> **참고** 페이지 원문은 Beta 기간 동안 특정 마이너 버전에 의존성을 고정(pin)하라고 권장합니다. 운영 코드에서는 버전을 고정하고, 업그레이드 시 변경 로그를 확인하십시오.

## 3. 설치

문서가 안내하는 설치 명령은 다음과 같습니다.

```bash
pip3 install databricks-sdk
```

특정 버전을 고정할 때는 다음처럼 씁니다. 버전 값은 예시이므로 실제로 쓸 버전을 PyPI에서 확인하십시오.

```bash
pip3 install "databricks-sdk==<version>"
```

Poetry를 쓴다면 `poetry add databricks-sdk`를 씁니다. 업그레이드는 `pip3 install --upgrade databricks-sdk`입니다.

## 4. 기본 사용법

워크스페이스 안의 클러스터 이름을 출력하는 예시입니다. 페이지 원문 예시와 같습니다.

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

for c in w.clusters.list():
    print(c.cluster_name)
```

`WorkspaceClient()`는 인수 없이 만듭니다. 호스트와 자격 증명은 아래 인증 체인에서 찾습니다.

Git 폴더를 갱신하는 예시도 같은 패턴입니다. 이 코드는 [Git 폴더와 CI/CD](../git-and-cicd/git-folders-and-cicd.md)에서 씁니다.

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.repos.update(
    w.workspace.get_status(path="<git-folder-workspace-full-path>").object_id,
    branch="<branch-name>",
)
```

## 5. 두 클라이언트

| 클라이언트 | 범위 | 예시 용도 |
|------------|------|-----------|
| `WorkspaceClient` | 워크스페이스 수준 API | 클러스터, 잡, Unity Catalog 볼륨 파일, `dbutils` |
| `AccountClient` | 계정 수준 API | 계정 그룹 목록 조회 |

`AccountClient`는 계정 콘솔 호스트와 계정 ID가 필요합니다. 페이지는 노트북 내장 인증을 `AccountClient`에서 쓸 수 없다고 설명하므로, 노트북에서 실행한다면 생성자에 자격 증명을 명시해야 합니다.

```python
from databricks.sdk import AccountClient

a = AccountClient(
    host="<account-console-url>",
    account_id="<account-id>",
)

for g in a.groups.list():
    print(g.display_name)
```

`host`에는 계정 콘솔 URL을 넣습니다. 이 장의 근거 문서에서 실제 주소 형식은 확인하지 못했으므로 자리표시자로 두었습니다. 계정 ID도 공개 저장소에 넣지 마십시오.

> **참고** 이 장의 근거 문서는 `AccountClient`의 `host` 기본값을 명시하지 않습니다. 계정 콘솔 URL은 `databricks auth login --host <account-console-url> --account-id <account-id>`에서 쓰는 값과 같은 것입니다([설치와 인증](../cli/install-and-auth.md)).

## 6. 인증 체인

### 6-1. 방식 선택 순서

공식 인증 페이지는 도구와 SDK가 다음 순서로 방식을 시도하고, 처음 성공하는 방식에서 멈춘다고 설명합니다.

| 순서 | 방식 | 대상 |
|------|------|------|
| 1 | 개인 액세스 토큰 (PAT, 레거시) | 기존 자동화 |
| 2 | OAuth 머신-투-머신 (M2M) | 서비스 프린시펄 |
| 3 | OAuth 사용자-투-머신 (U2M) | 사람 |

특정 방식을 강제하려면 `Config` API에서 Databricks 인증 유형 필드를 설정합니다. 이 페이지는 필드의 정확한 이름을 옮기지 않았으므로, SDK의 인증 문서에서 확인하십시오.

### 6-2. 자격 증명 찾는 순서

각 방식 안에서 자격 증명은 다음 순서로 찾습니다.

| 순서 | 위치 | 설명 |
|------|------|------|
| 1 | SDK 설정 필드 | 코드에서 직접 준 값 (SDK만 해당) |
| 2 | 환경 변수 | 플랫폼별 변수 |
| 3 | 구성 프로필 | `.databrickscfg`의 `DEFAULT` 프로필 |

특정 프로필을 기본으로 쓰려면 환경 변수 `DATABRICKS_CONFIG_PROFILE`에 프로필 이름을 넣습니다. 이식성을 높이는 권장 방법으로 페이지가 안내합니다.

```bash
export DATABRICKS_CONFIG_PROFILE=<profile-name>
```

이렇게 설정한 뒤 `WorkspaceClient()`를 인수 없이 만들면 됩니다.

> **주의** 이 순서는 SDK 인증 페이지의 설명입니다. CLI는 번들 설정 파일, 환경 변수, 프로필 순서이므로([설치와 인증](../cli/install-and-auth.md)) 두 도구의 결과가 다를 수 있습니다.

### 6-3. 노트북 기본 인증

SDK 페이지는 노트북에서 `WorkspaceClient()`를 인수 없이 쓰면 노트북 실행 동안 Databricks가 자동으로 만드는 임시 개인 액세스 토큰을 쓴다고 설명합니다. 실행이 끝나면 토큰은 삭제됩니다. 이 인증에는 다음 제약이 있습니다.

- 드라이버 노드에서만 동작합니다.
- 구성 프로필과 함께 쓸 수 없습니다.
- Databricks Container Services와 호환되지 않습니다.

### 6-4. 지원되는 인증 방식

SDK 페이지는 OAuth M2M, OAuth U2M(0.1.9 이상), 개인 액세스 토큰 인증을 지원한다고 적습니다. 자격 증명을 코드에 직접 넣는 방식도 지원되지만, 페이지는 노출 위험 때문에 권장하지 않는다고 명시합니다.

```python
# 권장하지 않음: 코드에 호스트와 토큰을 직접 넣는 방식
from databricks.sdk import WorkspaceClient

w = WorkspaceClient(host="https://<workspace-url>", token="<token>")
```

위 예시는 "이렇게 쓰면 안 된다"는 반례입니다. 토큰을 소스 코드에 두지 마십시오.

## 7. 트레이드오프

| 방식 | 장점 | 제약 |
|------|------|------|
| SDK | 타입, 인증 재사용, 대기·페이지네이션 내장 | Beta 라벨, 버전 고정 관리 필요 |
| CLI | 셸에서 한 줄 실행 | 복잡한 로직은 스크립트로 길어짐 |
| REST API 직접 호출 | 언어 제약 없음, 버전 고정이 명확 | 인증·대기·재시도를 직접 구현 |

## 8. 주의사항

- **버전 고정.** Beta 기간 동안 `databricks-sdk` 버전을 고정하고, 업그레이드는 테스트 후 반영합니다.
- **노트북 인증 범위 확인.** 노트북의 임시 토큰은 `AccountClient`나 프로필과 함께 쓸 수 없습니다. 계정 API를 노트북에서 호출한다면 자격 증명을 명시합니다.
- **토큰 하드코딩 금지.** 소스 코드, 노트북 셀, 공개 저장소 어디에도 토큰과 시크릿을 두지 않습니다.
- **테스트.** 페이지는 `pytest`와 `unittest.mock`으로 SDK 호출을 모킹하는 예시를 제공합니다. 운영 로직은 모킹 테스트로 감쌉니다.

## 참고 문서

- [Databricks SDK for Python](https://docs.databricks.com/aws/en/dev-tools/sdk-python)
- [Databricks 통합 인증](https://docs.databricks.com/aws/en/dev-tools/auth/unified-auth)
- [Databricks SDK for Python API 참조 (외부)](https://databricks-sdk-py.readthedocs.io)
