# 배포 엔진: Terraform에서 직접 배포 엔진으로

> 기준일: 2026-10-28 · 근거: 공식 문서

Declarative Automation Bundles는 배포할 때 리소스 상태를 계산하고 워크스페이스에 반영하는 **배포 엔진** 을 씁니다. 이 페이지는 엔진이 어떻게 바뀌었는지, 지금 어떤 엔진이 기본인지, 기존 번들을 옮기려면 무엇을 해야 하는지 정리합니다. 엔진 변경 이력은 릴리즈 노트에 있으므로, 이 페이지의 날짜와 버전은 모두 릴리즈 노트 원문을 기준으로 합니다.

## 1. 엔진 변경 이력

릴리즈 노트에서 엔진과 관련된 항목은 다음과 같습니다.

| 날짜 | 항목 | 원문 요지 | 상태 라벨 |
|------|------|-----------|-----------|
| 2025-12-04 | "Deploy without Terraform" (CLI 0.279.0) | Terraform 의존성을 없애는 첫 단계로, 번들을 새 직접 배포 엔진으로 옮길 수 있게 함. 원문 오타 "Terrform" 포함 | 라벨 없음 |
| 2026-06-10 | "Direct deployment engine is GA" | 직접 배포 엔진이 정식 출시(GA). CLI 1.3.0 이상으로 새로 만든 번들은 Terraform 엔진 대신 직접 배포 엔진을 기본으로 사용 | GA |

2026-06-10 항목의 원문은 "New bundles created using Databricks CLI version 1.3.0 and above use the direct deployment engine by default"입니다. 같은 노트에서 Terraform 엔진과 비교해 "instead of the Terraform deployment engine"이라고 적었습니다.

> **주의** 이 기록은 두 가지를 말해 줍니다. 첫째, ** 새로 만든 번들** 은 CLI 1.3.0 이상에서 직접 엔진이 기본입니다. 둘째, ** 기존 번들** 은 마이그레이션 명령으로 옮깁니다. docs의 기능 릴리즈 노트에는 제거 시점이 없지만, **Databricks CLI v1.20.0(2026-10-07) 릴리즈 노트는 Terraform 배포 엔진을 제거했다고 명시합니다**: "Remove the Terraform deployment engine. `bundle.engine: terraform` and `DATABRICKS_BUNDLE_ENGINE=terraform` now error" … "To keep deploying with Terraform, use Databricks CLI v1.19.x." 따라서 CLI 1.20 이상에서는 Terraform 엔진을 쓸 수 없고, 기존 Terraform 상태는 직접 엔진으로 옮겨야 합니다(마이그레이션 실패는 오류로 보고됨).

## 2. 왜 바뀌었는가

릴리즈 노트는 2025-12-04 항목에서 Terraform 의존성을 없애는 것을 목표로 한 첫 단계라고 적었습니다. 직접 엔진의 내부 구현 세부는 이 장의 근거 문서에 없으므로 이 페이지에서 설명하지 않습니다.

Terraform으로 Databricks를 관리하는 팀이라면 엔진 변경이 기존 배포 흐름에 영향을 줍니다. 전환 전에 현재 번들이 어떤 엔진으로 배포되는지 확인하십시오.

## 3. 어떤 엔진을 쓰고 있는지 확인하기

설치된 CLI 버전을 먼저 확인합니다.

```bash
databricks -v
```

번들이 어떤 엔진으로 배포되는지는 CLI 버전과 번들 생성 시점에 따라 다릅니다. 기존 번들의 엔진을 어떻게 확인하는지는 이 장의 근거 문서에 명시되어 있지 않습니다. 확인하지 못했습니다. 마이그레이션 페이지의 절차를 따르면서 확인하십시오.

## 4. 기존 번들을 직접 엔진으로 옮기기

번들 명령 페이지에는 `deployment` 하위 명령 아래 `migrate`가 있습니다. 플래그는 `--noplancheck`입니다.

```bash
databricks bundle deployment migrate -t dev
```

| 단계 | 할 일 |
|------|-------|
| 1 | 개발 타깃에서 먼저 시도합니다. 운영 타깃은 개발에서 확인한 뒤 옮깁니다. |
| 2 | `databricks bundle plan -t dev`로 변경 계획을 확인합니다. |
| 3 | `migrate`를 실행합니다. `--noplancheck`은 계획 검사를 건너뛰므로 자동화에서도 기본값을 유지하는 편이 안전합니다. |
| 4 | `deploy` 후 리소스 ID와 실행 이력이 유지되는지 워크스페이스에서 확인합니다. |

> **참고** 마이그레이션의 세부 절차는 "Migrate to the direct deployment engine" 가이드가 근거 문서입니다. 이 페이지는 해당 가이드의 링크와 명령 이름까지만 확인했습니다. 실제 전환 전에 가이드 원문을 읽으십시오.

## 5. 트레이드오프

| 항목 | 직접 배포 엔진 (GA) | Terraform 엔진 (기존) |
|------|---------------------|----------------------|
| 기본값 | CLI 1.3.0 이상의 새 번들 | 기존 번들 (마이그레이션 전) |
| 외부 도구 의존 | Terraform 의존성 없음 | Terraform 필요 (CLI 1.20부터 제거, v1.19.x까지만 사용 가능) |
| 기존 상태와의 호환 | `migrate`로 전환 | 전환 전까지 그대로 사용 |
| 운영 전환 난이도 | 개발 타깃에서 먼저 검증 필요 | 이미 운영 중이라면 변화 없음 |

직접 엔진의 세부 동작 차이(예: 상태 잠금, 부분 배포 지원 범위)는 이 장의 근거 문서에서 모두 확인하지 못했습니다. 운영 전환 전에 CLI 릴리즈 노트와 마이그레이션 가이드를 함께 확인하십시오.

## 6. 주의사항

- **개발 타깃에서 먼저 옮깁니다.** 운영 번들을 바로 옮기지 않습니다.
- **계획 확인 생략 금지.** `--noplancheck`은 검사를 건너뛰는 플래그이므로 기본 흐름에서는 쓰지 않습니다.
- **기존 상태를 임의로 지우지 않습니다.** 상태 처리 방식은 마이그레이션 가이드의 절차를 따릅니다.
- **버전 고정.** 팀이 쓰는 CLI 버전을 CI에 고정하고, 엔진 기본값이 바뀌는 버전으로 올릴 때 릴리즈 노트를 확인합니다.
- **문서 명칭.** 과거 자료에 Terraform 기반 `databricks bundle` 흐름이나 Databricks Asset Bundles 명칭이 남아 있을 수 있습니다. 현재 명칭은 Declarative Automation Bundles입니다.

## 참고 문서

- [Declarative Automation Bundles 릴리즈 노트](https://docs.databricks.com/aws/en/release-notes/dev-tools/bundles)
- [What are Declarative Automation Bundles?](https://docs.databricks.com/aws/en/dev-tools/bundles/)
- [Databricks 번들 명령 (bundle-commands)](https://docs.databricks.com/aws/en/dev-tools/cli/bundle-commands)
- [Databricks CLI v1.20.0 릴리즈 노트 (GitHub)](https://github.com/databricks/cli/releases/tag/v1.20.0)
