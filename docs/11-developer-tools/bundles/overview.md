# Declarative Automation Bundles 개요

> 기준일: 2026-10-28 · 근거: 공식 문서

Declarative Automation Bundles(구 Databricks Asset Bundles)는 잡, 파이프라인, 앱 같은 Databricks 리소스와 소스 코드를 **YAML 파일로 선언** 하고, 그 선언을 여러 워크스페이스와 환경에 배포하는 도구입니다. 이 페이지는 번들이 해결하는 문제, `databricks.yml`의 구조, 타깃과 변수의 역할을 다룹니다. 명령 실행과 기존 리소스 연결은 [수명 주기와 bind](lifecycle-and-bind.md)에서, 배포 엔진은 [배포 엔진](deployment-engine.md)에서 다룹니다.

## 1. 명칭과 상태

공식 문서 페이지 제목은 "What are Declarative Automation Bundles?"입니다. 본문은 이 제품을 "Declarative Automation Bundles (formerly known as Databricks Asset Bundles)"라고 설명합니다. 2026-03-16 릴리즈 노트는 "Databricks Asset Bundles has been renamed to Declarative Automation Bundles."라고 기록합니다. 이 페이지와 다른 페이지는 현재 표기인 Declarative Automation Bundles를 씁니다. 구 명칭은 이 문단에서만 병기합니다.

| 항목 | 상태 | 근거 |
|------|------|------|
| Declarative Automation Bundles (번들 본체) | GA | 릴리즈 노트 2024-04-23 "Declarative Automation Bundles is generally available" (당시 명칭 Databricks Asset Bundles) |
| Python으로 번들 정의 | GA | 릴리즈 노트 2025-10-27 "Python for Declarative Automation Bundles is GA" |
| 워크스페이스 안에서 번들 작업 | GA | 릴리즈 노트 2025-10-15 "Bundles in the workspace is GA" |
| 직접 배포 엔진 (direct deployment engine) | GA | 릴리즈 노트 2026-06-10 "Direct deployment engine is GA" |

> **참고** 페이지 자체에는 상태 라벨이 없습니다. 위 상태는 릴리즈 노트의 라벨을 근거로 한 것입니다.

## 2. 왜 필요한가

워크스페이스 UI에서 잡을 만들고 고치는 방식은 다음 문제를 만듭니다.

- **변경 이력이 없다.** 누가 언제 무엇을 바꿨는지 Git에 남지 않습니다.
- **환경 복제가 수작업이다.** 개발 환경의 잡을 운영에 똑같이 만들려면 설정을 손으로 옮깁니다.
- **검토가 어렵다.** 리뷰어가 UI 설정을 diff로 볼 수 없습니다.

번들은 리소스 정의와 소스 코드를 같은 저장소에 두고, Git 리뷰와 CI/CD를 거쳐 배포합니다. 환경별 차이는 타깃(target)과 변수(variable)로 표현합니다.

## 3. 구성 요소

번들 문서는 번들을 다음 요소로 구성한다고 설명합니다. 페이지 원문은 "artifacts, resources, and configuration"이라고 표현합니다.

| 요소 | 역할 |
|------|------|
| `databricks.yml` | 번들의 진입점. 최상위 설정을 담습니다. |
| 리소스 설정 파일 | 잡, 파이프라인 등 리소스를 정의합니다. `include`로 불러옵니다. |
| 소스 파일 | 노트북, Python 파일, SQL 같은 실제 코드입니다. |
| 테스트 | 단위·통합 테스트는 번들 구성의 일부로 둘 수 있습니다. |

## 4. `databricks.yml` 최상위 구조

설정 명세 페이지는 `databricks.yml`의 최상위 키를 다음과 같이 나열합니다.

| 키 | 역할 (명세 주석 요지) |
|----|----------------------|
| `bundle` | 기본 번들 설정 (이름 등) |
| `include` | 추가 설정 파일 포함 |
| `scripts` | 실행 가능한 스크립트 |
| `sync` | 워크스페이스로 동기화할 파일·경로의 포함·제외 |
| `artifacts` | 기본 아티팩트 설정 |
| `variables` | 번들 전역에서 쓰는 사용자 정의 변수 |
| `workspace` | 워크스페이스 설정 |
| `permissions` | `resources`에 정의한 리소스에 적용할 권한 |
| `resources` | 리소스 정의 (잡, 파이프라인, 앱, 대시보드 등) |
| `targets` | 배포와 워크플로 실행의 대상. 기본 타깃은 하나만 `default: true`로 지정합니다. |

가장 단순한 파일은 다음과 같습니다.

```yaml
bundle:
  name: my_bundle

targets:
  dev:
    default: true
```

`include`로 다른 파일을 불러오는 예는 다음과 같습니다. 페이지의 예시 그대로입니다.

```yaml
include:
  - '*.yml'
```

### 4-1. 잡 리소스 예시

설정 예시 페이지의 서버리스 잡 예시입니다. 클러스터 정의가 없고 노트북 태스크를 실행합니다.

```yaml
resources:
  jobs:
    serverless_job_no_cluster:
      name: serverless_job_no_cluster
      email_notifications:
        on_failure:
          - someone@example.com
      tasks:
        - task_key: notebook_task
          notebook_task:
            notebook_path: ../src/notebook.ipynb
```

`someone@example.com`은 예시 주소입니다. 실제 알림 주소로 바꾸되 공개 저장소에는 실제 주소를 두지 마십시오.

### 4-2. 파이프라인 리소스 예시

설정 예시 페이지에 있는 가장 짧은 파이프라인 정의입니다. 서버리스 컴퓨트로 실행됩니다.

```yaml
resources:
  pipelines:
    my_pipeline:
      name: my_pipeline
      target: ${bundle.environment}
      serverless: true
```

`${bundle.environment}`은 번들 변수 참조 문법입니다. 이 참조가 어떤 값으로 해석되는지는 타깃 설정과 함께 확인해야 합니다.

## 5. 타깃과 변수

타깃은 같은 번들을 여러 환경에 배포하는 단위입니다. `dev`와 `prod` 타깃이 같은 리소스 정의를 쓰되 워크스페이스나 변수 값이 다른 구조가 대표적입니다. `targets`는 기본 타깃을 하나 지정해야 하며(`default: true`), 명령의 `-t`(`--target`)로 대상을 고릅니다.

> **참고** 이 페이지는 타깃 안에서 워크스페이스·변수를 지정하는 세부 키를 옮기지 않았습니다. 타깃별 워크스페이스 지정 키, `variables` 블록의 `default` 형식, 변수 치환 문법은 [설정 명세 페이지](https://docs.databricks.com/aws/en/dev-tools/bundles/settings)에서 원문을 확인한 뒤 작성하십시오.

명령줄에서 변수 값을 바꾸려면 `--var`을 씁니다.

```bash
databricks bundle deploy -t prod --var="catalog=<catalog-name>"
```

## 6. 트레이드오프

| 항목 | 장점 | 제약 |
|------|------|------|
| 선언형 YAML | 리뷰, 이력, 환경 복제가 쉬움 | UI에서 바로 고치는 편의성은 줄어듦 |
| 타깃·변수 | 한 정의로 여러 환경 | 환경 간 차이가 많아지면 파일이 복잡해짐 |
| 기존 리소스 연결 | UI로 만든 리소스도 번들로 옮길 수 있음 | 연결 전 설정 차이를 확인해야 함 (다음 페이지) |
| 워크스페이스 안 번들 | UI에서 번들 작업 가능 (GA) | 로컬 Git 워크플로와 병행 시 기준을 정해야 함 |

## 7. 주의사항

- **타깃을 나눠도 데이터는 같을 수 있습니다.** `dev` 타깃이 운영과 같은 카탈로그나 테이블을 가리키면 개발 실행이 운영 데이터를 바꿉니다. 타깃마다 카탈로그와 스키마 변수를 분리합니다.
- **기본 타깃은 하나.** 여러 타깃에 `default: true`를 두면 검증 단계에서 실패합니다. 문서는 "One and only one" 기본 타깃을 요구합니다.
- **경로는 번들 기준.** 노트북 경로는 `databricks.yml` 기준 상대 경로로 씁니다. 절대 경로를 하드코딩하면 다른 워크스페이스에서 깨집니다.
- **변수 치환 확인.** 배포 전 `databricks bundle validate`로 치환 결과를 확인합니다.

## 참고 문서

- [What are Declarative Automation Bundles?](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Declarative Automation Bundles configuration](https://docs.databricks.com/aws/en/dev-tools/bundles/settings)
- [Bundle configuration examples](https://docs.databricks.com/aws/en/dev-tools/bundles/examples)
- [Declarative Automation Bundles 릴리즈 노트](https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles)
