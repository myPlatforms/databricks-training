# Git 폴더와 CI/CD 패턴

> 기준일: 2026-10-28 · 근거: 공식 문서

Databricks Git folders(구 Repos)는 워크스페이스 안에서 Git 저장소를 연결하는 시각적 Git 클라이언트이자 API입니다. 노트북과 파일에 버전 관리, 협업, CI/CD를 적용할 때 씁니다. 이 페이지는 Git 폴더의 역할, 협업 흐름, 그리고 운영 폴더를 자동화로 갱신하는 CI/CD 패턴을 다룹니다.

## 1. 왜 필요한가

워크스페이스에서 노트북을 직접 고치면 다음 문제가 생깁니다.

- 누가 어떤 변경을 했는지 이력이 워크스페이스 밖에 남지 않습니다.
- 여러 명이 같은 노트북을 고치면 덮어쓰기가 생깁니다.
- 개발 코드를 운영에 옮길 때 사람이 수동으로 복사하면 실수가 생깁니다.

Git 폴더는 워크스페이스 파일을 Git 저장소와 연결합니다. 개발자는 개인 브랜치에서 작업하고, 리뷰를 거쳐 병합하고, 병합 이후 운영 폴더를 자동으로 갱신하는 흐름을 만들 수 있습니다.

## 2. 상태와 명칭

| 항목 | 상태 | 근거 |
|------|------|------|
| Databricks Git folders | 페이지에 라벨 없음 | 페이지 H1 "Databricks Git folders", 최종 수정일 2026-09-11 |
| 구 명칭 Repos | 명칭 변경 | 하위 페이지 "What happened to Repos?"에서 설명 |

> **참고** 이 페이지는 상태 라벨을 표기하지 않습니다. 기능 단위 상태는 릴리즈 노트에서 확인하십시오.

## 3. 지원 범위와 기능

Git 폴더 개념 페이지의 요약에 따르면 다음을 할 수 있습니다.

- 저장소를 클론해 Git 폴더를 만듭니다.
- 브랜치를 만들고 전환합니다.
- 변경 사항을 커밋하고 원격에 push합니다.
- 병합 충돌을 해결합니다.
- Git CLI 명령을 씁니다.

지원하는 Git 제공자 목록은 이 페이지 본문에 없습니다. 개념 페이지의 "supported providers" 항목을 확인하십시오. 지원 자산 유형은 별도 페이지("Supported asset types")에 있습니다. 이 페이지에서는 확인하지 못했습니다.

### 3-1. 하위 페이지

| 주제 | 내용 |
|------|------|
| Git folders concepts | 개념 |
| Configure Git integration | Git 연동 설정 |
| Create and manage Git folders | 생성과 관리 |
| Supported asset types | 지원 자산 유형 |
| CI/CD with Git folders | CI/CD 패턴 (4절 이후 내용의 원문) |
| Automate with a service principal | 서비스 프린시펄로 자동화 |
| Automate with Terraform | Terraform 자동화 |
| Set up private Git connectivity | 사설 Git 연결 |
| Serverless Private Git | 서버리스 사설 Git |
| Limitations and FAQ | 제한과 FAQ |
| Errors and troubleshooting | 오류와 문제 해결 |

## 4. 세 가지 흐름

CI/CD 페이지는 Git 폴더의 흐름을 세 가지로 나눕니다.

| 흐름 | 누가 | 하는 일 |
|------|------|---------|
| 관리자 흐름 | 관리자 | 운영용 상위 폴더를 만들고, 각 폴더에 저장소와 브랜치를 클론 (예: Production, Test, Staging) |
| 사용자 흐름 | 개발자 | `/Workspace/Users/<user>/` 아래에 자기 Git 폴더를 만들고 개인 브랜치에서 작업 후 push |
| 병합 흐름 | 자동화 | PR이 병합되면 Databricks Repos API로 운영 Git 폴더를 최신 커밋으로 갱신 |

## 5. 협업 절차

페이지가 안내하는 기능 브랜치 기준 절차입니다.

1. 기존 저장소를 워크스페이스에 클론합니다.
2. `main` 브랜치에서 기능 브랜치를 만듭니다.
3. 노트북과 파일을 편집합니다.
4. 변경을 커밋하고 원격에 push합니다.
5. 다른 기여자도 자기 사용자 폴더에 클론해서 같은 방식으로 작업합니다.
6. Git 제공자에서 PR을 만들고 팀 리뷰를 거쳐 배포 브랜치에 병합합니다.

페이지는 개발자마다 개인 브랜치를 쓰라고 권장합니다. 충돌 해결 방법은 이 페이지에서 설명하지 않고 별도 문서를 보라고 안내합니다.

## 6. CI/CD 방식 선택

페이지는 두 가지 방식을 제시하고 번들 방식을 권장합니다.

| 방식 | 대상 | 설명 |
|------|------|------|
| 번들 방식 (권장) | 잡, 파이프라인 등 리소스 | 리소스와 소스를 저장소에 정의하고 Declarative Automation Bundles로 배포 |
| 운영 Git 폴더 방식 | 코드만 워크스페이스에 두는 경우 | 운영 Git 폴더를 두고 최신 커밋으로 갱신 |

번들로 정의한 리소스를 워크스페이스 Git 폴더에서 생성하고 배포하고 관리할 수도 있다고 페이지는 설명합니다. 번들 개념은 [번들 개요](../bundles/overview.md)를 보십시오.

## 7. 운영 Git 폴더 만들기

페이지의 절차 요약입니다.

| 단계 | 할 일 |
|------|-------|
| 1 | 배포할 저장소와 브랜치를 정합니다. |
| 2 | 서비스 프린시펄을 만들거나 고르고, 저장소에 접근할 Git 자격 증명을 설정합니다. |
| 3 | 워크스페이스 하위 폴더(프로젝트, 팀, 단계별)에 해당 저장소와 브랜치의 Git 폴더를 만듭니다. |
| 4 | 폴더를 선택하고 공유(Share) 설정을 엽니다. |
| 5 | 권한을 줍니다. 워크플로를 실행하는 사용자와 자동화 서비스 프린시펄에는 **Can Run**, 필요하면 전체 사용자에게 **Can View** 를 줍니다. |
| 6 | Add를 클릭합니다. |
| 7 | 원격 브랜치와 동기화합니다. 아래 8절 중 하나를 씁니다. |

운영 폴더는 자동화만 갱신하고, 대부분의 사용자에게는 실행 권한만 주고 편집은 관리자와 서비스 프린시펄로 제한하는 것을 권장합니다.

## 8. 원격 동기화 방법

### 8-1. 외부 CI/CD

GitHub Actions 같은 외부 도구가 배포 브랜치에 PR이 병합될 때 최신 커밋을 pull하도록 합니다. 페이지는 이 방식의 예시 본문을 싣지 않고 관련 문서 링크만 둡니다. 실제 워크플로 파일은 CI/CD 도구의 문서를 따릅니다.

### 8-2. 예약 작업 노트북

외부 CI/CD를 쓸 수 없다면 Git 폴더를 갱신하는 노트북을 예약 실행합니다. 페이지의 예시는 다음과 같습니다.

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.repos.update(
    w.workspace.get_status(path="<git-folder-workspace-full-path>").object_id,
    branch="<branch-name>",
)
```

`<git-folder-workspace-full-path>`는 운영 Git 폴더의 워크스페이스 전체 경로입니다. 경로를 하드코딩하지 말고 환경 설정에서 읽도록 설계하십시오.

> **주의** 이 코드는 Python SDK의 `repos.update`를 씁니다. SDK 사용법과 인증 체인은 [Python SDK](../sdk-and-apis/python-sdk.md)를 보십시오.

## 9. 트레이드오프

| 방식 | 장점 | 제약 |
|------|------|------|
| 개인 Git 폴더 + PR | 이력과 리뷰가 Git에 남음 | 협업 규칙과 브랜치 정책을 팀이 정해야 함 |
| 운영 Git 폴더 자동 갱신 | 운영 코드가 저장소와 일치 | 갱신 실패를 감지하는 장치가 필요 |
| 번들 방식 | 리소스와 코드를 함께 배포 | 번들 구조를 익혀야 함 |
| 예약 노트북 갱신 | 외부 CI 없이 가능 | 예약 실행 실패를 따로 모니터링해야 함 |

## 10. 주의사항

- **운영 폴더 직접 편집 금지.** 운영 Git 폴더는 자동화만 갱신합니다. 사람이 고치면 저장소와 어긋납니다.
- **서비스 프린시펄 자격 증명 관리.** Git 접근 자격 증명은 서비스 프린시펄에 연결하고 주기적으로 회전합니다.
- **권한 최소화.** 대부분의 사용자는 Can Run만 받습니다.
- **경로 하드코딩 금지.** 운영 폴더 경로와 브랜치 이름은 설정으로 분리합니다.
- **지원 자산 확인.** 노트북과 파일 외에 어떤 자산이 Git 폴더에서 버전 관리되는지는 지원 자산 페이지로 확인합니다.

## 참고 문서

- [Databricks Git folders](https://docs.databricks.com/aws/en/repos/)
- [CI/CD with Databricks Git folders](https://docs.databricks.com/aws/en/repos/ci-cd)
- [Declarative Automation Bundles 개요](https://docs.databricks.com/aws/en/dev-tools/bundles/)
