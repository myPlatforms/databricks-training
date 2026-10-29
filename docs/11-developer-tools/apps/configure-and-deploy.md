# Databricks Apps 설정과 배포

> 기준일: 2026-10-28 · 근거: 공식 문서

이 페이지는 앱의 실행 설정 파일 `app.yaml`, 환경 변수, 배포 방법(워크스페이스 폴더와 Git 저장소), 재배포와 상태 확인을 다룹니다. 앱이 쓰는 리소스와 권한은 [개요와 리소스 바인딩](overview-and-resources.md)을 먼저 보십시오.

## 1. 왜 필요한가

앱을 여러 환경에 올릴 때 실행 명령과 설정 값이 코드 곳곳에 흩어지면 배포가 깨지기 쉽습니다. 실행 명령과 환경 변수를 `app.yaml`에 모으면 다음이 쉬워집니다.

- 같은 소스를 다른 워크스페이스에 배포할 때 설정만 바꿉니다.
- 환경 변수에 웨어하우스 ID 같은 값을 넣고, 코드에서는 이름으로 읽습니다.
- 배포 명령과 실행 명령을 문서화된 형태로 고정합니다.

## 2. 앱 소스 구조

배포에 필요한 파일은 다음과 같습니다. 배포 페이지 원문 요지입니다.

| 파일 | 필수 여부 | 역할 |
|------|-----------|------|
| 진입점 스크립트 (예: `app.py`, `app.js`) | 필수 | 앱을 시작하는 코드 |
| `app.yaml` | 선택 | 실행 명령(`command`)과 환경 변수(`env`) 정의 |
| `requirements.txt` 또는 `pyproject.toml`과 `uv.lock` | Python 앱에서 의존성 | Python 패키지 목록 |
| `package.json` (pnpm이면 `pnpm-lock.yaml`) | Node.js 앱에서 의존성 | Node 패키지 목록 |

소스 폴더는 앱의 서비스 프린시펄이 접근할 수 있어야 합니다. 동기화에서 빼고 싶은 파일은 `.gitignore`에 적습니다. 원문에 따르면 배포 도구는 이 파일을 기준으로 제외 목록을 처리합니다.

> **주의** 비밀 값(토큰, 비밀번호)을 소스 폴더에 두지 마십시오. 값은 시크릿 리소스나 환경 변수로 주입합니다.

## 3. `app.yaml` 작성

### 3-1. 최상위 키

앱 실행 설정 페이지(app-runtime)가 설명하는 최상위 키는 두 가지입니다.

| 키 | 타입 | 필수 여부 | 설명 |
|----|------|-----------|------|
| `command` | sequence | 선택 | 실행 명령. 기본값은 Python 앱이면 `python <my-app.py>`, Node.js 앱이면 `npm run start` |
| `env` | list | 선택 | 앱에 추가로 전달할 환경 변수 목록 |

`env` 항목에는 `name`이 필요하고, `value`와 `valueFrom` 중 하나를 씁니다. 페이지는 "One of"로 설명하므로 둘 중 하나만 씁니다.

### 3-2. Streamlit 예시

실행 설정 페이지의 Streamlit 예시를 옮기되, 웨어하우스 ID는 자리표시자로 바꿨습니다.

```yaml
command: ['streamlit', 'run', 'app.py']
env:
  - name: 'DATABRICKS_WAREHOUSE_ID'
    value: '<sql-warehouse-id>'
  - name: 'STREAMLIT_GATHER_USAGE_STATS'
    value: 'false'
```

`STREAMLIT_GATHER_USAGE_STATS`는 Streamlit의 사용 통계 수집을 끄는 환경 변수입니다. 원문 예시에 있는 값입니다.

### 3-3. Flask 예시

같은 페이지의 Flask 예시는 `gunicorn`으로 실행합니다. 볼륨 경로를 환경 변수로 넘기는 형태입니다. 경로는 예시이므로 실제 볼륨 경로로 바꾸십시오.

```yaml
command:
  - gunicorn
  - app:app
  - -w
  - 4
env:
  - name: 'VOLUME_URI'
    value: '/Volumes/<catalog-name>/<schema-name>/<volume-name>'
```

> **참고** 이 예시는 원문의 명령 배열을 그대로 옮긴 것이며, 볼륨 경로만 자리표시자로 바꿨습니다. 원문 페이지는 줄바꿈이 평탄화되어 있어 들여쓰기는 YAML 규칙에 맞게 다시 맞췄습니다.

### 3-4. `valueFrom`

`valueFrom`은 값이 들어 있는 외부 소스를 가리키는 항목입니다. 페이지는 시크릿이나 데이터베이스 테이블을 예로 듭니다. 페이지에 `valueFrom`의 구체 문법 예시는 없고, "Use environment variables to access resources" 절을 보라고만 안내합니다. 이 페이지에서는 문법을 쓰지 않습니다. 실제로 쓰기 전에 해당 절의 원문을 확인하십시오.

## 4. 배포

배포 페이지는 세 가지 방식을 설명합니다.

| 방식 | 대상 | 특징 |
|------|------|------|
| 워크스페이스 폴더 (CLI) | 로컬에서 개발 중인 앱 | `sync`로 파일을 올리고 `apps deploy`로 배포 |
| 워크스페이스 폴더 (UI) | 이미 워크스페이스에 있는 소스 | 앱 페이지에서 Deploy 후 폴더 선택 |
| Git 저장소 | 팀 협업, 자동 배포 | 저장소 URL과 provider를 설정하고 Git 참조로 배포 |

### 4-1. 워크스페이스 폴더 배포 (CLI)

먼저 로컬 폴더를 워크스페이스로 동기화합니다. `--watch`를 쓰면 변경을 계속 올립니다.

```bash
databricks sync --watch . /Workspace/Users/<user@example.com>/my-app
```

이어서 앱을 배포합니다. 소스 경로는 동기화한 워크스페이스 경로입니다.

```bash
databricks apps deploy my-app-name --source-code-path /Workspace/Users/<user@example.com>/my-app
```

`user@example.com`은 예시 주소입니다. 실제 사용자 이메일은 공개 자료에 넣지 마십시오. 앱 생성은 배포 페이지의 흐름상 UI에서 먼저 만드는 것으로 읽힙니다. `apps create` 명령의 정확한 인수는 `databricks apps create --help`로 확인하십시오.

### 4-2. Git 저장소 배포

Git 저장소에서 바로 배포하려면 앱을 만들 때 저장소 URL과 provider를 줍니다.

```bash
databricks apps create my-app --git-url https://github.com/<org>/<repo> --git-provider gitHub
```

기존 앱은 `apps update`로 설정을 바꿉니다. 배포할 때 Git 참조를 지정합니다.

```bash
databricks apps deploy my-app --git-branch main
```

태그, 커밋, 하위 디렉터리를 지정하는 옵션도 있다고 페이지에 나옵니다. 정확한 플래그 이름은 `databricks apps deploy --help`로 확인하십시오.

> **참고** 배포 페이지는 번들 기반 배포를 Git 기반 앱 배포 방법의 하나로 언급하지만, 번들 배포 명령을 제공하지 않습니다. 번들로 앱을 정의하는 방법은 [번들 개요](../bundles/overview.md)와 `databricks bundle generate app` 도움말을 확인하십시오.

### 4-3. 재배포

| 소스 | 재배포 방법 |
|------|-------------|
| 워크스페이스 폴더 | 파일을 고친 뒤 앱 페이지에서 Deploy. 소스 경로가 바뀌었다면 "Deploy using a different source" |
| Git 저장소 | 변경을 push한 뒤 Deploy. Git 참조가 바뀌었다면 다른 소스로 배포 |
| 자동 배포 | GitHub 또는 Azure DevOps 저장소의 브랜치 push로 자동 재배포하도록 설정 가능 |

## 5. 상태와 로그 확인

| 확인 대상 | 방법 |
|-----------|------|
| 앱 상태 | 앱 개요 페이지. 상태는 Running, Stopped, Deploying, Crashed |
| 배포 이력 | Deployments 탭 또는 `databricks apps list-deployments <app-name>` |
| 실행 로그 | Logs 탭 |

배포 페이지에 상태를 조회하는 전용 CLI 명령은 없습니다. 앱 상태는 UI 개요에서 봅니다. 스크립트에서 상태를 읽어야 한다면 `databricks apps --help`에 해당 명령이 있는지 확인하십시오.

```bash
databricks apps list-deployments <app-name>
```

## 6. 트레이드오프

| 방식 | 장점 | 제약 |
|------|------|------|
| 워크스페이스 폴더 + CLI sync | 로컬 편집 후 바로 반영 | 여러 사람이 같은 폴더를 고치면 충돌 관리가 어려움 |
| Git 저장소 | 이력, 리뷰, 자동 배포 | 저장소 연결과 provider 설정이 필요 |
| 번들 기반 | 리소스와 함께 선언, 환경별 설정 | 앱 배포 명령이 번들 명령에 있는지 도움말 확인 필요 |

## 7. 주의사항

- **`app.yaml`로 설정을 모은다.** 코드에 워크스페이스 ID나 경로를 넣지 않습니다.
- **재배포 확인.** Deploy 후 Deployments 이력에 새 버전이 찍혔는지 확인합니다.
- **`Crashed` 상태는 로그부터.** Logs 탭에서 시작 오류를 확인하고, 명령(`command`)과 의존성 파일이 맞는지 봅니다.
- **동기화 제외 확인.** `.gitignore`에 비밀 파일과 로컬 가상 환경이 빠져 있지 않은지 점검합니다.
- **서비스 프린시펄 접근.** 서비스 프린시펄이 소스 코드 폴더에 접근할 수 있어야 한다는 것이 배포 페이지의 요건입니다. 권한을 먼저 확인하십시오.
- **Lakebase 연결.** 앱에 Lakebase 데이터베이스를 붙이는 절차와 주입되는 환경 변수는 [Databricks Apps와 함께 쓰기](../../10-lakebase/apps-integration.md)를 따릅니다.

## 참고 문서

- [Configure Databricks app execution with app.yaml](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime)
- [Deploy Databricks apps](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/deploy)
- [Databricks Apps 설정 (Configure apps)](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/configuration)
- [Databricks Apps 개요](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/)
- [Databricks Apps와 함께 쓰기 (Lakebase)](../../10-lakebase/apps-integration.md)
