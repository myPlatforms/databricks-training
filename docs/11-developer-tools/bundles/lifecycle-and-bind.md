# 번들 수명 주기와 기존 리소스 bind

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 200

이 페이지는 번들의 명령 흐름(`validate` → `plan` → `deploy` → `run` → `destroy`), 워크스페이스에 이미 있는 리소스를 번들에 연결하는 `bind`, 그리고 기존 설정에서 번들 파일을 만드는 `generate`를 다룹니다. 번들 구조는 [번들 개요](overview.md)를 먼저 보십시오.

## 1. 왜 필요한가

번들을 처음부터 새로 만들면 문제가 없습니다. 실제 현장에서는 이미 UI에서 만든 잡이나 파이프라인이 운영 중인 경우가 많습니다. 이 리소스를 지우고 다시 배포하면 실행 이력과 리소스 ID가 바뀝니다. `bind`는 기존 리소스를 번들 정의와 연결해서 같은 리소스를 번들이 관리하게 만듭니다.

명령 흐름을 나누는 이유는 변경을 미리 보고, 실제 워크스페이스를 바꾸기 전에 멈출 수 있게 하기 위해서입니다.

## 2. 명령 흐름

| 단계 | 명령 | 하는 일 | 워크스페이스를 바꾸는가 |
|------|------|---------|------------------------|
| 검증 | `databricks bundle validate` | 설정 파일의 구문과 구조를 검사 | 아니요 |
| 미리 보기 | `databricks bundle plan` | 배포 시 수행될 작업을 실제 변경 없이 표시 | 아니요 |
| 배포 | `databricks bundle deploy` | 리소스와 파일을 원격 워크스페이스에 반영 | 예 |
| 실행 | `databricks bundle run` | 잡, 파이프라인, 앱, 스크립트 실행 | 예 (실행 자체) |
| 삭제 | `databricks bundle destroy` | 이전에 배포된 작업, 파이프라인, 아티팩트 삭제 | 예 |

표의 명령은 번들 명령 페이지에 나온 것입니다. 명령 이름은 모두 `databricks bundle` 아래에 있습니다.

```bash
databricks bundle validate -t dev
databricks bundle plan -t dev
databricks bundle deploy -t dev
databricks bundle run <job-key> -t dev
```

`<job-key>`는 `databricks.yml`에 정의한 리소스 키입니다. 실행할 리소스 이름을 명령에 넘기는 방식은 `run` 명령의 도움말에서 확인하십시오.

### 2-1. `deploy`의 주요 플래그

| 플래그 | 용도 |
|--------|------|
| `--auto-approve` | 확인 프롬프트 없이 진행. 자동화에서 쓰되 운영 타깃에서는 신중히 씀 |
| `--plan` | 계획 파일을 지정해 그 계획대로 배포 |
| `--select` | 지정한 리소스만 계획·배포 |
| `--force` | 충돌하는 변경을 강제로 덮어씀 |
| `--force-lock` | 잠금을 강제로 해제 |
| `--fail-on-active-runs` | 실행 중인 실행이 있으면 실패 |

`--select`는 2026-06-04 릴리즈 노트에 "plan or deploy only the specified resource(s)"로 소개되었고, 같은 노트에 "This option is not intended for use in production."이 적혀 있습니다. 운영 배포에서 쓰지 않습니다.

### 2-2. `run`의 주요 플래그

| 플래그 | 용도 |
|--------|------|
| `--no-wait` | 실행을 시작만 하고 완료를 기다리지 않음 |
| `--restart` | 실행 중인 실행을 재시작 |
| `--only` | 잡 안에서 지정한 태스크만 실행 |
| `--params` | 실행 파라미터 전달 |
| `--validate-only` | 실행 없이 검증만 |
| `--full-refresh`, `--refresh` 등 | 파이프라인 새로 고침 범위 지정 |

## 3. 예시: 개발 타깃 배포

처음 쓰는 개발 워크스페이스에서 흐름은 다음과 같습니다.

```bash
# 1. 구문 검증
databricks bundle validate -t dev

# 2. 변경 미리 보기 (아무것도 바꾸지 않음)
databricks bundle plan -t dev

# 3. 배포
databricks bundle deploy -t dev

# 4. 잡 실행 (리소스 키는 예시)
databricks bundle run my_job -t dev
```

`plan` 결과에서 생성, 변경, 삭제 항목을 확인한 뒤 `deploy`를 실행하는 습관이 가장 중요합니다.

## 4. 기존 리소스 bind

`bind`는 워크스페이스에 이미 있는 리소스를 번들의 리소스 정의와 연결합니다. 명령은 `databricks bundle deployment bind`이고, 번들 명령 페이지는 `--target`과 함께 쓰도록 안내합니다.

```bash
databricks bundle deployment bind --help
databricks bundle deployment bind -t <target>
```

`bind` 관련 플래그는 `--auto-approve`와 `--force-lock`입니다. 리소스 키와 리소스 ID를 어떤 인수 형식으로 넘기는지는 이 페이지 원문에 명시되어 있지 않으므로, 설치된 CLI의 `--help` 출력으로 확인하십시오. 연결을 되돌리는 `unbind`도 같은 하위 명령 아래에 있으며 `--force-lock`을 받습니다.

```bash
databricks bundle deployment unbind --help
```

> **주의** 이 페이지에서 확인한 것은 `bind`와 `unbind`의 존재, 플래그, 그리고 `--target` 사용 안내입니다. 연결 후 리소스 설정이 번들 정의로 덮어써지는지, 편집이 UI에서 막히는지 같은 동작 세부는 공식 문서 본문에 명시되어 있지 않아 확인하지 못했습니다. 실제 운영 리소스에 `bind`하기 전에 `plan`으로 차이를 먼저 확인하고, 개발 워크스페이스의 복제본에서 먼저 시험하십시오.

### 4-1. bind 전 체크리스트

| 점검 항목 | 확인 방법 |
|-----------|-----------|
| 번들 정의가 기존 리소스 설정과 같은지 | `databricks bundle plan -t <target>`로 차이 확인 |
| 스케줄·트리거가 그대로 살아 있는지 | 번들 정의와 UI 설정을 비교. 활성 스케줄이 운영 실행을 일으킬 수 있음 |
| 타깃이 맞는 워크스페이스인지 | `databricks auth profiles -o text`와 타깃 설정 확인 |
| 실행 중인 실행이 없는지 | 배포 시 `--fail-on-active-runs` 사용 검토 |

## 5. 기존 설정에서 번들 만들기 (`generate`)

이미 UI에서 만든 리소스를 번들 파일로 옮길 때 `generate`를 씁니다. 하위 명령은 다음 다섯 가지입니다.

| 하위 명령 | 생성하는 대상 |
|-----------|---------------|
| `generate job` | 잡 |
| `generate pipeline` | 파이프라인 |
| `generate app` | 앱 |
| `generate dashboard` | 대시보드 |
| `generate genie-space` | Genie 공간 (Genie Agents로 표기가 바뀜. 릴리즈 노트 2026-06-10 참고) |

```bash
databricks bundle generate job --help
```

번들 명령 페이지의 플래그 목록에는 `--bind`, `--existing-*` 계열, `--key`, `-d/--config-dir`, `-s/--source-dir`, `-f/--force`가 있습니다. `--bind`는 생성과 동시에 기존 리소스와 연결하는 플래그입니다. 각 플래그에 넘길 값의 정확한 이름은 설치된 CLI의 도움말에서 확인하십시오.

> **참고** `generate`로 만든 파일은 출발점입니다. 생성된 YAML에 워크스페이스별 값(사용자 이메일, 절대 경로)이 섞여 있을 수 있으므로 변수로 바꾸고 `validate`를 다시 돌리십시오.

## 6. 다른 명령

| 명령 | 용도 |
|------|------|
| `databricks bundle init` | 템플릿으로 새 번들 만들기. `--template-dir`, `--tag`, `--branch` 등 지정 |
| `databricks bundle summary` | 번들 식별 정보와 리소스 요약, 워크스페이스 링크 출력 |
| `databricks bundle open` | 워크스페이스에서 번들 리소스를 브라우저로 열기 |
| `databricks bundle sync` | 로컬 디렉터리를 원격으로 단방향 동기화. `--watch`로 변경 감시 |
| `databricks bundle schema` | 번들 설정의 JSON 스키마 출력. 에디터 자동 완성에 활용 가능 |

## 7. 트레이드오프

| 방식 | 장점 | 제약 |
|------|------|------|
| `plan` 후 `deploy` | 변경을 눈으로 확인 | 자동화에서는 승인 단계를 따로 설계해야 함 |
| `--auto-approve` | CI에서 무인 배포 가능 | 잘못된 계획도 그대로 적용됨 |
| `bind` | 리소스 ID와 실행 이력 유지 | 연결 후 동작 세부는 원문 확인이 필요 |
| 처음부터 새로 배포 | 깨끗한 상태에서 시작 | 기존 리소스와 ID가 바뀌고 이력이 끊김 |

## 8. 주의사항

- **`plan`을 생략하지 않습니다.** 운영 타깃에서는 `plan` 결과를 저장하고, `deploy --plan`으로 그 계획을 적용하는 방식을 고려합니다.
- **`--auto-approve`는 운영에서 신중히.** 확인 단계를 건너뜁니다.
- **`destroy`는 되돌릴 수 없습니다.** 실행 전 타깃과 프로필을 확인합니다.
- **`--select`는 임시 수단.** 릴리즈 노트가 운영 용도가 아니라고 명시합니다.
- **dev 실행이 운영 데이터를 바꾸지 않게.** 개발 타깃의 카탈로그와 스키마를 운영과 분리한 뒤 `run`을 실행합니다.

## 참고 문서

- [What are Declarative Automation Bundles?](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Databricks 번들 명령 (bundle-commands)](https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands)
- [Declarative Automation Bundles 릴리즈 노트](https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles)
