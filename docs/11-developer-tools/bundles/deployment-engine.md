# 배포 엔진: Terraform에서 직접 배포 엔진으로

> 기준일: 2026-10-29 · 근거: 공식 문서 · 수준: 300

Declarative Automation Bundles는 배포할 때 리소스 상태를 계산하고 워크스페이스에 반영하는 **배포 엔진** 을 씁니다. 이 페이지는 엔진이 어떻게 바뀌었는지, 지금 어떤 엔진이 기본인지, 기존 번들을 옮기려면 무엇을 해야 하는지 정리합니다. 엔진 변경 이력은 릴리즈 노트에 있으므로, 이 페이지의 날짜와 버전은 모두 릴리즈 노트 원문을 기준으로 합니다.

## 1. 엔진 변경 이력

릴리즈 노트에서 엔진과 관련된 항목은 다음과 같습니다.

| 날짜 | 항목 | 원문 요지 | 상태 라벨 |
|------|------|-----------|-----------|
| 2025-12-04 | "Deploy without Terraform" (CLI 0.279.0) | Terraform 의존성을 없애는 첫 단계로, `databricks bundle migrate` 명령으로 번들을 새 직접 배포 엔진으로 옮길 수 있게 함. 원문 오타 "Terrform" 포함 | 라벨 없음 |
| 2026-06-10 | "Direct deployment engine is GA" | 직접 배포 엔진이 정식 출시(GA). CLI 1.3.0 이상으로 새로 만든 번들은 Terraform 엔진 대신 직접 배포 엔진을 기본으로 사용 | GA |
| 2026-10-07 | CLI v1.20.0 | Terraform 배포 엔진 제거 (아래 2절) | 해당 없음 |

2026-06-10 항목의 원문은 "New bundles created using Databricks CLI version 1.3.0 and above use the direct deployment engine by default"입니다. 같은 노트에서 Terraform 엔진과 비교해 "instead of the Terraform deployment engine"이라고 적었습니다.

> **주의** 이 기록은 두 가지를 말해 줍니다. 첫째, **새로 만든 번들** 은 CLI 1.3.0 이상에서 직접 엔진이 기본입니다. 둘째, **기존 번들** 은 마이그레이션으로 옮깁니다. 기능 릴리즈 노트에는 제거 시점이 없지만, **Databricks CLI v1.20.0 릴리즈 노트는 Terraform 배포 엔진 제거를 명시합니다.** 아래 2절을 확인하십시오.

## 2. CLI v1.20.0에서 바뀐 것

CLI v1.20.0 릴리즈 노트(2026-10-07)의 첫 항목은 "Remove the Terraform deployment engine."입니다. 주요 변경은 다음과 같습니다.

| 변경 | 원문 |
|---|---|
| 설정 오류화 | "`bundle.engine: terraform` and `DATABRICKS_BUNDLE_ENGINE=terraform` now error" |
| 마이그레이션 실패 처리 | "a failed migration of existing Terraform state is reported as an error instead of falling back to Terraform." |
| 폐기 경고 | "Warn that `bundle.terraform` is deprecated and has no effect since the Terraform deployment engine was removed." |
| 숨김 명령 제거 | "Remove the hidden `bundle debug terraform` command." |
| 마이그레이션 수정 | "Fix `bundle deployment migrate` failing with "no such file or directory"" (특정 Terraform 상태·설정 조합) |

Terraform 엔진을 계속 써야 하면 릴리즈 노트의 안내를 따릅니다. "To keep deploying with Terraform, use Databricks CLI v1.19.x." 따라서 CLI 1.20 이상에서는 Terraform 엔진을 쓸 수 없습니다. 기존 Terraform 상태는 직접 엔진으로 옮긴 뒤에만 배포할 수 있습니다.

## 3. 왜 바뀌었는가

릴리즈 노트는 2025-12-04 항목에서 Terraform 의존성을 없애는 것을 목표로 한 첫 단계라고 적었습니다. 직접 엔진은 Terraform 바이너리 없이 CLI가 배포를 수행합니다. 직접 엔진이 상태를 계산하고 저장하는 내부 구현은 이 장의 근거 문서에 없으므로 이 페이지에서는 설명하지 않습니다.

Terraform으로 Databricks를 관리하는 팀이라면 엔진 변경이 기존 배포 흐름에 영향을 줍니다. 전환 전에 현재 번들이 어떤 엔진으로 배포되는지 확인하십시오.

## 4. 어떻게 동작하는가

### 4.1 엔진 선택 규칙

문서가 설명하는 엔진 선택 규칙은 다음과 같습니다.

| 조건 | 사용되는 엔진 |
|---|---|
| CLI 1.3.0 이상으로 새로 만든 번들 | 직접 엔진 (기본값) |
| CLI 1.14 이상에서 Terraform 엔진 번들을 배포 | 배포 시 직접 엔진으로 자동 마이그레이션 |
| CLI 1.8 이상에서 `bundle.engine: direct` 또는 `DATABRICKS_BUNDLE_ENGINE=direct`를 명시 | 직접 엔진 (옵트인) |
| 설정 파일과 환경 변수를 둘 다 지정 | 설정 파일 값이 우선 |
| CLI 1.20 이상에서 `terraform` 지정 | 오류 |

직접 엔진 설정은 다음처럼 씁니다.

```yaml
bundle:
  engine: direct
```

```bash
DATABRICKS_BUNDLE_ENGINE=direct databricks bundle deploy -t my_target
```

### 4.2 직접 엔진의 상태

직접 엔진은 **로컬 구성만 상태 파일에 기록** 합니다. 문서는 이를 "only records local configuration in its state file"이라고 설명합니다. 원격 상태는 워크스페이스에서 리소스 ID로 추적합니다. 번들 배포는 생성한 리소스를 대상 워크스페이스에서 **리소스 ID** 로 추적한다고 명령 레퍼런스가 설명합니다.

### 4.3 직접 엔진 전용 기능

명령 레퍼런스에 따르면 다음 기능은 직접 엔진에서만 쓸 수 있습니다.

| 명령 또는 옵션 | 동작 (문서 원문 요지) |
|---|---|
| `bundle deploy --plan <파일>` | 계획 JSON 파일을 적용. 문서는 "(direct engine only)"로 표시. 파일은 `bundle plan -o json`으로 만듦 |
| `bundle deployment bind` | 명령 주석: "some resources are only available using the direct engine" (일부 리소스는 직접 엔진 전용) |

`bundle deploy --force-lock`은 배포 잠금을 강제로 얻는 옵션이며, 명령 레퍼런스에서 직접 엔진 전용으로 표시되지 않습니다.

계획을 파일로 저장한 뒤 적용하는 흐름은 다음과 같습니다.

```bash
databricks bundle plan -t dev -o json > plan.json
databricks bundle deploy -t dev --plan plan.json
```

## 5. 어떻게 쓰는가: 기존 번들 옮기기

### 5.1 설치된 CLI 버전 확인

```bash
databricks -v
```

### 5.2 마이그레이션 명령

명령 레퍼런스의 `bundle deployment migrate`는 **Public Preview** 입니다. 설명은 "Migrate the bundle from using the Terraform deployment engine to using the direct deployment engine."입니다. 문서는 "To complete the migration you must then deploy the bundle."이라고 적고, 확인 방법으로 `databricks bundle plan`을 제시합니다.

```bash
databricks bundle deployment migrate -t dev
databricks bundle plan -t dev
databricks bundle deploy -t dev
```

명령 레퍼런스 원문 기준 `--noplancheck` 플래그는 "Skip running `bundle plan` before the migration."이며, 기본 동작은 계획을 먼저 실행하고 변경 계획이 있으면 마이그레이션을 멈추는 것입니다. 이 플래그는 **"Only applicable in Databricks CLI versions 0.280.0 through 1.4.x"** 입니다. CLI 1.20 이상에서는 적용되지 않으므로 이 페이지의 절차에서 빼 둡니다.

> **주의** 직접 엔진 마이그레이션 문서는 CLI 1.14 이상에서 Terraform 번들을 배포하면 **자동으로 직접 엔진으로 옮겨진다** 고 설명합니다. 명시적 `migrate` 명령과 배포 시 자동 전환이 둘 다 문서에 있으므로, 운영 번들은 명시적 명령으로 먼저 옮기고 `plan`으로 결과를 확인하는 편이 추적하기 쉽습니다.

### 5.3 전환 순서

| 단계 | 할 일 |
|------|-------|
| 1 | 개발 타깃에서 먼저 옮깁니다. 운영 타깃은 개발에서 확인한 뒤 옮깁니다. |
| 2 | `databricks bundle plan -t dev`로 변경 계획을 확인합니다. |
| 3 | `databricks bundle deployment migrate -t dev`를 실행합니다. |
| 4 | `databricks bundle deploy -t dev`로 배포를 마칩니다. 문서가 마이그레이션 완료 조건으로 명시한 단계입니다. |
| 5 | 워크스페이스에서 잡 ID, 파이프라인 ID, 실행 이력이 유지되는지 확인합니다. |

## 6. 트레이드오프

| 항목 | 직접 배포 엔진 (GA) | Terraform 엔진 (기존) |
|------|---------------------|----------------------|
| 기본값 | CLI 1.3.0 이상의 새 번들 | 기존 번들 (마이그레이션 전) |
| 외부 도구 의존 | Terraform 의존성 없음 | Terraform 필요 (CLI 1.20부터 제거, v1.19.x까지만 사용 가능) |
| 기존 상태와의 호환 | `migrate` 또는 배포 시 자동 전환 | 전환 전까지 그대로 사용 (1.20 이상에서는 불가) |
| 직접 엔진 전용 기능 | `deploy --plan`, 일부 리소스 바인딩 | 해당 없음 |
| 운영 전환 난이도 | 개발 타깃에서 먼저 검증 필요 | 이미 운영 중이라면 버전 고정으로 버틸 수 있음 (1.19.x) |

### 6.1 직접 엔진의 알려진 동작 차이

문서가 설명하는 차이는 다음과 같습니다. 옮기기 전에 번들 설정을 이 목록과 대조하십시오.

| 항목 | 직접 엔진 동작 (문서 원문 요지) |
|---|---|
| 필드 제거 | `databricks.yml`에서 설정된 필드를 지우면 다음 배포에서 리소스 기본값으로 되돌아갑니다. Terraform은 값을 그대로 둡니다. 값을 유지하려면 명시적으로 씁니다. |
| 드리프트 | 직접 엔진이 다루지 않는 필드는 드리프트가 생길 수 있으며, 다음 `plan` 또는 `deploy`에서 갱신됩니다. |
| 직접 엔진 필수 리소스 | 클러스터 정책, Unity Catalog 카탈로그·외부 위치·시크릿, Genie 스페이스, 인스턴스 풀, 잡 실행, AI Search 엔드포인트, MCP 서비스, 모델 제공자 서비스, 모델 서비스, Postgres 스냅샷 스케줄 |
| `lifecycle.started` | 직접 엔진에서만 동작하며, `apps`, `clusters`, `sql_warehouses`에만 적용됩니다. |

## 7. 주의사항

- **개발 타깃에서 먼저 옮깁니다.** 운영 번들을 바로 옮기지 않습니다.
- **계획 확인을 기본 흐름에 둡니다.** `--noplancheck`은 계획 검사를 건너뛰는 플래그이며, CLI 1.20 이상에서는 쓸 수 없습니다.
- **기존 상태를 임의로 지우지 않습니다.** 상태 처리 방식은 마이그레이션 가이드의 절차를 따릅니다.
- **설정 필드를 명시합니다.** 직접 엔진은 필드를 지우면 기본값으로 되돌립니다. 유지해야 할 값은 번들 설정에 적습니다.
- **버전을 고정합니다.** 팀이 쓰는 CLI 버전을 CI에 고정하고, 엔진 기본값이 바뀌는 버전으로 올릴 때 릴리즈 노트를 확인합니다. Terraform 엔진이 꼭 필요하면 CLI 1.19.x에 고정합니다.
- **문서 명칭.** 과거 자료에 Terraform 기반 `databricks bundle` 흐름이나 Databricks Asset Bundles 명칭이 남아 있을 수 있습니다. 현재 명칭은 Declarative Automation Bundles입니다. 문서는 "formerly known as Databricks Asset Bundles"라고 설명합니다.
- **`bundle.terraform`은 효과가 없습니다.** CLI 1.20에서 폐기 경고가 나옵니다.

## 참고 문서

- [Declarative Automation Bundles 릴리즈 노트](https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles)
- [What are Declarative Automation Bundles?](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Migrate to the direct deployment engine](https://docs.databricks.com/aws/en/dev-tools/bundles/direct)
- [Databricks 번들 명령 (bundle-commands)](https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands)
- [Databricks CLI v1.20.0 릴리즈 노트 (GitHub)](https://github.com/databricks/cli/releases/tag/v1.20.0)
- [Databricks CLI v1.3.0 릴리즈 노트 (GitHub)](https://github.com/databricks/cli/releases/tag/v1.3.0)
- [Databricks CLI v0.279.0 릴리즈 노트 (GitHub)](https://github.com/databricks/cli/releases/tag/v0.279.0)
