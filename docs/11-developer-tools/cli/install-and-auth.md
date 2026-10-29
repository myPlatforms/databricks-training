# Databricks CLI 설치와 인증

> 기준일: 2026-10-28 · 근거: 공식 문서

Databricks CLI(Command-Line Interface)는 터미널에서 워크스페이스와 계정의 리소스를 조회하고 변경하는 명령줄 도구입니다. 이 페이지는 CLI를 설치하고, 워크스페이스에 인증하고, 여러 워크스페이스를 프로필로 나누어 쓰는 방법을 다룹니다. 명령 그룹과 출력 형식은 [명령 그룹과 출력 형식](commands-and-output.md)에서 다룹니다.

## 1. 왜 필요한가

워크스페이스 UI에서 클릭으로 하던 작업은 반복하거나 자동화하기 어렵습니다. CLI를 쓰면 다음이 가능해집니다.

- 잡, 파이프라인, 앱, 클러스터 같은 리소스를 셸 스크립트와 CI 작업에서 호출합니다.
- Unity Catalog 볼륨 파일과 워크스페이스 파일을 명령으로 다룹니다.
- 번들(Declarative Automation Bundles)로 정의한 리소스를 배포하고 실행합니다. 번들은 [번들 개요](../bundles/overview.md)에서 다룹니다.
- 여러 워크스페이스(개발·운영 등)를 프로필 이름 하나로 전환합니다.

인증 정보를 스크립트마다 따로 넣으면 토큰이 여러 곳에 흩어집니다. 문서가 OAuth를 권장하는 이유도 여기에 있습니다. OAuth 토큰은 단기 토큰이며, CLI가 갱신을 관리합니다.

## 2. 상태

| 항목 | 상태 | 근거 |
|------|------|------|
| Databricks CLI 1.x | GA | [CLI 개요 페이지](https://docs.databricks.com/aws/en/dev-tools/cli/)에서 1.0.0 이상을 정식 출시(GA)로 설명 |
| 0.205 ~ 0.299 | 공개 프리뷰 | 같은 페이지 설명 |
| 0.18 이하 | 레거시 | 같은 페이지 설명. 더 이상 지원되거나 신규 기능이 추가되지 않는다고 명시 |
| OAuth U2M / M2M 인증 | 페이지에 라벨 없음 | 인증 페이지에 별도 상태 표기 없음 |

> **참고** 설치 페이지 본문에는 "v0.205 이상이면 정상 설치"라는 문장이 있습니다. CLI 개요 페이지는 1.0.0 이상을 GA로 설명하므로, 새로 설치하면 현재 1.x 라인이 설치됩니다. 설치 페이지의 버전 안내가 개요 페이지와 어긋나므로, 설치 후 `databricks -v`로 실제 버전을 확인하십시오.

## 3. 설치

설치 페이지가 안내하는 방법은 다음과 같습니다.

| OS | 방법 | 명령 |
|----|------|------|
| macOS | Homebrew | `brew tap databricks/tap` 후 `brew install databricks` |
| macOS, Linux | Homebrew 한 번에 | `brew install databricks/tap/databricks` |
| macOS, Linux | curl 설치 스크립트 | `curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh \| sh` |
| Windows | WinGet | `winget install Databricks.DatabricksCLI` |
| Windows | Chocolatey (실험적) | `choco install databricks-cli` |
| 공통 | GitHub Releases 바이너리 | OS와 아키텍처에 맞는 `.zip`을 받아 압축을 풀고 실행 파일을 사용 |

설치 후 버전을 확인합니다.

```bash
databricks -v
```

설치 페이지는 Homebrew 6.0.0부터 서드파티 tap을 `brew trust`로 신뢰 처리해야 한다고 안내합니다. 이 경우 `brew trust databricks/tap`을 먼저 실행합니다.

업데이트는 설치 방법과 같은 도구로 합니다.

```bash
brew upgrade databricks
```

curl 스크립트로 설치했다면 기존 실행 파일(`/usr/local/bin/databricks`)을 지운 뒤 설치 스크립트를 다시 실행합니다. 권한 오류가 나면 `sudo`로 실행합니다.

> **참고** 워크스페이스 안의 웹 터미널에서도 CLI를 사용할 수 있다고 설치 페이지에 나옵니다. 이 경우 별도 인증 설정 없이 쓸 수 있는지는 페이지에 명시되어 있지 않으므로 확인하지 못했습니다.

## 4. 인증 방식

인증 페이지는 CLI가 지원하는 방식을 세 가지로 나눕니다.

| 방식 | 대상 | 설명 |
|------|------|------|
| OAuth 사용자-머신(U2M) | 사람 | 대화형으로 로그인하면 CLI가 단기 토큰을 관리합니다. 페이지는 이 방식을 기본 흐름으로 안내합니다. |
| OAuth 머신-머신(M2M) | 서비스 프린시펄, 자동화 | 서비스 프린시펄의 클라이언트 ID와 시크릿으로 OAuth 클라이언트 자격 증명 흐름을 씁니다. |
| 개인 액세스 토큰(PAT) | 레거시 | 페이지에서 "legacy"로 표시되며 OAuth 사용을 권장합니다. |

### 4-1. OAuth U2M으로 로그인

워크스페이스 수준 로그인은 다음 명령입니다.

```bash
databricks auth login --host <workspace-url>
```

계정 수준 API를 쓰려면 계정 콘솔 URL과 계정 ID를 함께 지정합니다.

```bash
databricks auth login --host <account-console-url> --account-id <account-id>
```

명령을 실행하면 브라우저에서 로그인하는 흐름이 열립니다. 토큰은 OS 보안 저장소에 저장되고, 구성 파일에는 호스트와 프로필 이름 같은 비밀이 아닌 값만 남는다고 페이지가 설명합니다.

> **주의** `<workspace-url>`과 `<account-id>`는 실제 값으로 바꿔 쓰되, 공개 문서나 저장소에 실제 워크스페이스 URL과 계정 ID를 커밋하지 마십시오.

### 4-2. OAuth M2M으로 자동화

M2M은 서비스 프린시펄을 씁니다. 구성 프로필에 호스트와 자격 증명을 넣는 형태는 다음과 같습니다. 대괄호 안이 프로필 이름입니다. 값은 자리표시자입니다.

```ini
[ci-prod]
host          = https://<workspace-url>
client_id     = <service-principal-client-id>
client_secret = <service-principal-client-secret>
```

계정 수준 명령을 쓰는 프로필에는 `account_id`를 함께 넣습니다. 페이지는 `account_id`가 계정 수준 명령에만 필요하다고 설명합니다.

> **주의** `client_secret`을 `.databrickscfg`에 평문으로 두는 방식은 페이지의 예시입니다. 시크릿 값은 파일 권한을 제한하고, 저장소에는 넣지 마십시오. 저장소에 올리면 안 되는 이유는 자격 증명 노출입니다.

### 4-3. PAT (레거시)

PAT는 기존 자동화가 아직 쓰는 경우에만 씁니다. 신규 구성은 OAuth로 옮기는 것을 권장합니다. 전환 방법과 PAT 발급 절차는 인증 페이지의 "Personal access token authentication"에서 확인합니다.

## 5. 구성 프로필

프로필은 `~/.databrickscfg` 파일에 있는 이름 있는 설정 묶음입니다. 워크스페이스가 여러 개라면 프로필을 나눕니다.

프로필 목록은 다음 명령으로 봅니다.

```bash
databricks auth profiles -o text
```

특정 프로필로 명령을 실행하려면 `-p`(또는 `--profile`)를 씁니다.

```bash
databricks clusters list -p <profile-name>
```

## 6. 자격 증명 선택 순서

CLI는 실행할 때 설정 값을 다음 순서로 찾고, 필요한 값을 찾으면 그 시점에서 검색을 멈춥니다.

| 순서 | 위치 | 예시 |
|------|------|------|
| 1 | 번들 설정 파일 (번들 디렉터리에서 실행할 때) | `databricks.yml`의 워크스페이스 설정 |
| 2 | 환경 변수 | `DATABRICKS_TOKEN` 등 |
| 3 | 구성 프로필 | `~/.databrickscfg`의 프로필 |

`DATABRICKS_TOKEN` 환경 변수가 있으면 `.databrickscfg`에 토큰이 여러 개 있어도 환경 변수가 우선합니다. 예상과 다른 워크스페이스에 명령이 나가는 사고는 대부분 이 순서 때문에 생깁니다.

> **참고** 이 순서는 CLI 인증 페이지의 설명입니다. Python SDK의 자격 증명 탐색 순서는 다르므로 [Python SDK](../sdk-and-apis/python-sdk.md)에서 따로 다룹니다.

## 7. 트레이드오프

| 항목 | 장점 | 제약 |
|------|------|------|
| OAuth U2M | 단기 토큰, 사용자 본인 권한으로 실행 | 대화형 로그인이 필요해 무인 실행에는 맞지 않음 |
| OAuth M2M | 무인 자동화에 적합, 서비스 프린시펄 권한으로 실행 | 시크릿 관리 책임이 생김 |
| PAT | 설정이 단순함 | 레거시로 표시됨. 장기 토큰이라 노출 시 위험이 큼 |
| 프로필 분리 | 워크스페이스 전환이 명령 한 줄로 끝남 | 잘못된 `-p` 값이나 환경 변수 우선순위를 놓치기 쉬움 |

## 8. 주의사항

- **프로필 확인 먼저.** 운영 워크스페이스에 명령을 내기 전에 `databricks auth profiles -o text`로 프로필을 확인하고, `-p`를 명시합니다.
- **환경 변수 점검.** 셸에 `DATABRICKS_HOST`나 `DATABRICKS_TOKEN`이 남아 있으면 프로필보다 우선합니다. 작업 전에 `env | grep DATABRICKS`로 확인합니다.
- **토큰을 로그에 남기지 않기.** 디버그 로그 옵션을 켜면 요청 정보가 출력될 수 있습니다. 공유 전 로그를 점검합니다.
- **M2M 시크릿 회전.** 서비스 프린시펄 시크릿은 주기적으로 바꾸고, 바꾼 뒤 프로필을 갱신합니다.

## 참고 문서

- [Databricks CLI 개요](https://docs.databricks.com/aws/en/dev-tools/cli/)
- [CLI 설치 또는 업데이트](https://docs.databricks.com/aws/en/dev-tools/cli/install)
- [Databricks CLI 인증](https://docs.databricks.com/aws/en/dev-tools/cli/authentication)
- [Databricks 통합 인증](https://docs.databricks.com/aws/en/dev-tools/auth/unified-auth)
