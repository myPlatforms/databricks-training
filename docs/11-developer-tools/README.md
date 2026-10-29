# 11. 개발자 도구

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~300

이 장은 Databricks 워크스페이스에서 코드를 작성하고, 배포를 자동화하고, 외부 도구와 연결하는 **개발자 도구** 를 다룹니다. Genie Code 외에 CLI, Declarative Automation Bundles, SDK와 REST API, Databricks Apps, Git 폴더와 CI/CD를 함께 수록합니다.

| 주제 | 상태 | 위치 |
|------|------|------|
| Genie Code | 수록됨 | [genie-code/README.md](genie-code/README.md) |
| Databricks CLI | 수록됨 | [설치와 인증](cli/install-and-auth.md), [명령 그룹과 출력 형식](cli/commands-and-output.md) |
| Declarative Automation Bundles | 수록됨 | [개요](bundles/overview.md), [수명 주기와 bind](bundles/lifecycle-and-bind.md), [배포 엔진](bundles/deployment-engine.md) |
| Python SDK, REST API, Databricks Connect | 수록됨 | [Python SDK](sdk-and-apis/python-sdk.md), [REST API와 Databricks Connect](sdk-and-apis/rest-api-and-connect.md) |
| Databricks Apps | 수록됨 | [개요와 리소스 바인딩](apps/overview-and-resources.md), [설정과 배포](apps/configure-and-deploy.md) |
| Git 폴더와 CI/CD | 수록됨 | [Git 폴더와 CI/CD 패턴](git-and-cicd/git-folders-and-cicd.md) |

Apps와 Lakebase를 함께 쓰는 연동은 [Databricks Apps와 함께 쓰기](../10-lakebase/apps-integration.md)에서 다룹니다. Lakeflow Jobs와 파이프라인, Unity Catalog의 권한 관리는 각각 04장과 06장에서 다룹니다.

## 이 장의 범위

- **Genie Code**: 워크스페이스 안에서 노트북·SQL·파이프라인 작업을 돕는 AI 코딩·데이터 어시스턴트입니다. 채팅 패널, 전체 화면 모드, 예약 작업, Lakeflow Jobs 태스크, 터미널용 CLI까지 한 제품군으로 묶어 다룹니다.
- **다른 Genie 제품과의 구분**: 문서에서 Genie One은 비즈니스 사용자가 데이터 질문을 하는 용도, Genie Agents는 데이터 팀이 신뢰할 수 있는 데이터와 비즈니스 규칙을 구성하는 용도로 설명합니다. 이 장은 Genie Code만 다룹니다.

## 학습 목표

이 장을 마치면 다음을 설명하고 수행할 수 있어야 합니다.

1. Genie Code가 어디에서 열리고 무엇을 할 수 있는지 구분합니다.
2. 인스트럭션, 스킬, MCP 서버로 Genie Code의 동작을 조정합니다.
3. Lakeflow Jobs의 Genie Code 태스크와 예약 작업의 차이를 설명하고 설계에 맞게 고릅니다.
4. 자동 승인(auto-approve)의 의미와 운영 환경에서의 위험을 이해합니다.
5. 예산, 사용량 테이블, 파트너 AI 설정으로 사용량과 데이터 처리 범위를 관리합니다.
6. Databricks CLI를 설치하고, OAuth 프로필로 워크스페이스를 전환하며, 출력 형식을 맞춰 스크립트에 씁니다.
7. Declarative Automation Bundles로 리소스를 선언하고 `validate`, `plan`, `deploy`, `run`, `destroy` 흐름으로 배포합니다. 기존 리소스를 `bind`로 연결하는 전후 확인 절차를 설명합니다.
8. Python SDK의 인증 체인과 `WorkspaceClient`, `AccountClient`의 차이를 설명하고, 상황에 맞게 REST API나 Databricks Connect를 고릅니다.
9. Databricks Apps의 리소스 바인딩, 앱 권한과 사용자 권한의 차이, `app.yaml` 설정을 이해하고 앱을 배포합니다.
10. Git 폴더로 협업하고, 운영 폴더를 자동화로 갱신하는 CI/CD 패턴을 설계합니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|------|--------|------|-------------|
| 1 | [모드·기능과 데이터 접근 권한](genie-code/features-and-permissions.md) | 100 | 진입점, 기능 목록, 승인(자동 승인), 세션 간 메모리, 권한 모델 |
| 2 | [인스트럭션과 스킬](genie-code/instructions-and-skills.md) | 200 | 인스트럭션 경로와 우선순위, AGENTS.md·CLAUDE.md 자동 로드, SKILL.md 작성 |
| 3 | [MCP 서버 연결](genie-code/mcp.md) | 200 | 기본 제공 커넥터, UC MCP Service·사용자 정의 서버 연결, 인증과 거버넌스 |
| 4 | [예약 작업](genie-code/scheduled-tasks.md) | 200 | 반복 실행 프롬프트 생성과 관리, 실행 기록, Lakeflow Jobs 태스크와의 선택 기준 |
| 5 | [Lakeflow Jobs의 Genie Code 태스크](genie-code/lakeflow-jobs-task.md) | 200 | 태스크 설정, 프롬프트 파라미터, 응답 참조, 설계 패턴 |
| 6 | [Genie Code CLI](genie-code/cli.md) | 200 | 설치, 명령, MCP 추가, 워크스페이스와의 차이 (Beta) |
| 7 | [거버넌스와 비용](genie-code/governance-and-cost.md) | 300 | 과금 구조, 예산과 차단, 사용량 확인, 파트너 AI 설정, 데이터 처리 지역 |
| 8 | [Databricks CLI 설치와 인증](cli/install-and-auth.md) | 200 | 설치, OAuth 로그인, 구성 프로필, 자격 증명 선택 순서 |
| 9 | [명령 그룹과 출력 형식](cli/commands-and-output.md) | 200 | 명령 구조, 전역 플래그, JSON 출력, 스크립트 작성 패턴 |
| 10 | [Declarative Automation Bundles 개요](bundles/overview.md) | 100 | 번들의 구성 요소, databricks.yml 구조, 타깃과 변수 |
| 11 | [번들 수명 주기와 기존 리소스 bind](bundles/lifecycle-and-bind.md) | 200 | validate·plan·deploy·run·destroy 흐름, bind와 generate |
| 12 | [배포 엔진: Terraform에서 직접 배포 엔진으로](bundles/deployment-engine.md) | 300 | 엔진 변화, 기존 번들 마이그레이션, 직접 엔진의 동작 차이 |
| 13 | [Python SDK: WorkspaceClient와 AccountClient](sdk-and-apis/python-sdk.md) | 200 | 설치, 두 클라이언트, 인증 체인, 노트북 기본 인증 |
| 14 | [REST API와 Databricks Connect](sdk-and-apis/rest-api-and-connect.md) | 200 | REST API 호출 요소, Databricks Connect 설정, 방식 선택 기준 |
| 15 | [Databricks Apps 개요와 리소스 바인딩](apps/overview-and-resources.md) | 100 | 앱 구성 요소, 리소스 종류, 앱 권한과 사용자 권한, 상태 데이터 위치 |
| 16 | [Databricks Apps 설정과 배포](apps/configure-and-deploy.md) | 200 | app.yaml, 환경 변수, 워크스페이스 폴더와 Git 배포, 상태 확인 |
| 17 | [Git 폴더와 CI/CD 패턴](git-and-cicd/git-folders-and-cicd.md) | 300 | 협업 흐름, 운영 Git 폴더 자동 갱신 패턴, 권한 설계 |
| 18 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 10개와 실무 체크리스트 |

## 작성 원칙

- 본문은 공식 문서 원문으로 확인한 내용만 씁니다. 문서에 없는 내용은 "문서에 명시 없음"으로 표기합니다.
- 기능마다 상태(GA, Public Preview, Beta)를 표기합니다. 문서 페이지에 라벨이 없으면 릴리즈 노트의 라벨을 근거로 하고 출처를 밝힙니다.
- 이 장의 문서는 AWS 문서(`docs.databricks.com/aws/en/`)를 기준으로 합니다. Azure와 GCP 문서는 별도로 존재하며, 이 장에서는 확인하지 않았습니다.
