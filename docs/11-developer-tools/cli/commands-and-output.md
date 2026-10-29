# 명령 그룹과 출력 형식

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 Databricks CLI의 명령 구조, 자주 쓰는 명령 그룹, 출력 형식(`-o`), 그리고 스크립트에서 결과를 안전하게 쓰는 방법을 다룹니다. 설치와 인증은 [설치와 인증](install-and-auth.md)을 먼저 보십시오.

## 1. 왜 필요한가

REST API를 직접 호출하면 엔드포인트 경로, 인증 헤더, 페이지네이션을 매번 다뤄야 합니다. CLI는 이 부분을 명령으로 감쌉니다. 예를 들어 클러스터 정보 조회는 다음 한 줄입니다.

```bash
databricks clusters get 1234-567890-a12bcde3
```

같은 작업을 `curl`로 하려면 `/api/2.0/clusters/get` 엔드포인트에 GET 요청을 보내고 인증 헤더를 직접 넣어야 합니다. CLI 개요 페이지도 이 예시를 들어 두 방식을 비교합니다.

## 2. 명령 구조

CLI 명령은 `databricks <그룹> <하위 명령> [인수] [플래그]` 형태입니다.

| 그룹 예 | 역할 | 대표 명령 (문서에 나온 것) |
|---------|------|----------------------------|
| `auth` | 로그인과 프로필 관리 | `auth login`, `auth profiles` |
| `clusters` | 클러스터 조회 | `clusters list`, `clusters get` |
| `bundle` | 번들 검증·배포·실행 | `bundle validate`, `bundle deploy`, `bundle run` |
| `apps` | 앱 생성·배포 | `apps create`, `apps deploy`, `apps list-deployments` |
| `sync` | 로컬 폴더를 워크스페이스로 동기화 | `sync --watch` |

전체 명령 목록은 CLI 문서의 "Databricks CLI commands" 페이지에 있습니다. 이 페이지는 장에서 쓰는 그룹만 다룹니다. 그룹마다 하위 명령과 플래그가 많으므로 실제 목록은 `databricks <그룹> --help`로 확인합니다.

> **참고** CLI 개요 페이지는 GPU 학습 워크로드를 `databricks air` 명령으로 제출·관리한다고 설명합니다. 이 장에서는 다루지 않습니다.

### 2-1. 명령 도움말

```bash
databricks --help
databricks bundle --help
databricks bundle deploy --help
```

도움말이 가장 정확합니다. 문서의 명령 이름이 CLI 버전에 따라 바뀔 수 있으므로, 스크립트를 짜기 전에 설치된 버전에서 `--help`로 확인합니다.

## 3. 프로필과 대상 지정

전역 플래그로 어느 워크스페이스에 명령을 보낼지 지정합니다. 번들 명령 페이지가 설명하는 전역 플래그는 다음과 같습니다.

| 플래그 | 의미 |
|--------|------|
| `-p`, `--profile` | `~/.databrickscfg`의 프로필 지정 |
| `-t`, `--target` | 번들의 타깃 지정 (번들 명령에서 사용) |
| `--var` | 번들 설정의 변수 값 지정 |
| `-o`, `--output` | 출력 형식 (`text` 또는 `json`) |
| `--debug` | 디버그 로그 출력 |
| `--log-file`, `--log-format`, `--log-level` | 로그 파일과 형식·수준 지정 |
| `--progress-format` | 진행 상황 출력 형식 지정 |

예시는 다음과 같습니다.

```bash
databricks clusters list -p <profile-name>
databricks bundle validate -t dev
databricks bundle deploy -t dev --var="catalog=<catalog-name>"
```

> **주의** `-t`와 `-p`를 함께 쓸 때 두 값이 서로 다른 워크스페이스를 가리키면 번들의 타깃 설정과 프로필 설정이 충돌할 수 있습니다. 문서에 충돌 시 우선순위가 명시되어 있지 않으므로, 운영 명령에는 둘 중 하나의 의도를 분명히 하고 `bundle validate` 결과를 확인하십시오.

## 4. 출력 형식

`-o`(또는 `--output`)는 `text`와 `json` 두 값을 받습니다. 번들 명령 페이지는 이 플래그를 전역 플래그로 설명합니다. 페이지에 기본값이 명시되어 있지 않으므로 기본값은 확인하지 못했습니다. 스크립트에서는 항상 `-o`를 명시합니다.

```bash
databricks auth profiles -o text
databricks clusters list -o json
```

| 형식 | 용도 | 주의 |
|------|------|------|
| `text` | 사람이 읽기 | 열 형식이 바뀔 수 있어 파싱에 쓰지 않음 |
| `json` | 스크립트, `jq` 파이프 | 필드 이름을 실제 응답으로 한 번 확인 |

JSON 결과를 `jq`로 다루는 예는 다음과 같습니다. 필드 이름 `cluster_name`과 `cluster_id`는 응답 구조에 맞게 바꿔 쓰십시오.

```bash
databricks clusters list -o json | jq -r '.[].cluster_name'
```

> **주의** 파이프라인에서 JSON을 읽을 때 빈 결과나 에러 메시지를 같은 형식으로 받는지 먼저 확인하십시오. 에러가 텍스트로 나오면 `jq`가 실패합니다. 스크립트에서는 종료 코드(exit code)를 함께 확인합니다.

## 5. 스크립트 작성 패턴

자동화 스크립트는 세 가지를 지키면 사고가 줄어듭니다.

1. 프로필과 타깃을 명시합니다. 기본값에 기대지 않습니다.
2. `-o json`으로 결과를 받고, 종료 코드를 확인합니다.
3. 변경 명령(`deploy`, `destroy`, `run`) 전에 읽기 명령으로 대상을 확인합니다.

```bash
#!/usr/bin/env bash
set -euo pipefail

PROFILE="<profile-name>"

# 1. 대상 확인 (읽기 전용)
databricks auth profiles -o text | grep -- "$PROFILE" || { echo "프로필 없음"; exit 1; }

# 2. 번들 검증
databricks bundle validate -t dev -p "$PROFILE"

# 3. 배포
databricks bundle deploy -t dev -p "$PROFILE"
```

`set -euo pipefail`은 명령이 실패하면 스크립트를 멈춥니다. 번들 배포는 번들 장의 [배포 명령](../bundles/lifecycle-and-bind.md)에서 자세히 다룹니다.

## 6. 트레이드오프

| 방식 | 장점 | 제약 |
|------|------|------|
| CLI | 명령 한 줄, 인증 재사용, 번들·앱과 연결 | 버전마다 명령 이름과 플래그가 바뀔 수 있음 |
| REST API 직접 호출 | 모든 기능에 접근, 버전 고정이 명확 | 인증·재시도·페이지네이션을 직접 구현 |
| Python SDK | 코드에서 타입과 함께 호출 | 스크립트 환경에 Python 설치 필요 |

운영 자동화에는 CLI나 번들을 먼저 고려합니다. CLI에 없는 기능이나 세부 제어가 필요하면 [REST API와 Databricks Connect](../sdk-and-apis/rest-api-and-connect.md)를 봅니다.

## 7. 주의사항

- **`--help`로 버전 확인.** 문서 예시와 설치된 CLI 버전이 다르면 `--help` 결과를 우선합니다.
- **`text` 출력을 파싱하지 않기.** 자동화는 `json`만 씁니다.
- **변경 명령은 읽기로 먼저 확인.** `deploy`, `destroy`, `run` 전에 대상 워크스페이스와 타깃을 확인합니다.
- **디버그 로그 공유 주의.** `--debug`와 로그 파일에는 요청 정보가 들어갈 수 있으므로 외부에 공유하기 전에 점검합니다.

## 참고 문서

- [Databricks CLI 개요](https://docs.databricks.com/aws/en/dev-tools/cli/)
- [Databricks 번들 명령 (bundle-commands)](https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands)
- [Databricks CLI 인증](https://docs.databricks.com/aws/en/dev-tools/cli/authentication)
