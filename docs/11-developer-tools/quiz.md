# 퀴즈와 체크리스트

> 기준일: 2026-10-29 · 근거: 이 장 본문 · 수준: 100~300

이 장에서 다룬 내용을 확인하는 문제입니다. 정답을 펼치면 해설과 근거 페이지로 가는 링크가 있습니다.

## 퀴즈

### 1. Genie Code의 자동 승인(Auto-approve)을 설명한 내용으로 본문에 맞는 것은? (수준 100)

- A. 자동 승인은 보안 경계이므로, 운영 환경에서 기본으로 켜 두는 것이 권장된다.
- B. 자동 승인은 생산성 기능이며 보안 경계가 아니다. 운영, 민감 데이터, 공유 리소스에서는 끄는 것이 권장된다.
- C. 자동 승인이 켜지면 `DROP`에 `CASCADE`를 붙인 삭제도 요청 범위와 상관없이 허용된다.
- D. Lakeflow Jobs의 Genie Code 태스크에서는 태스크마다 자동 승인을 끌 수 있다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 자동 승인을 "a productivity feature, not a security boundary"라고 명시하고, 운영·민감·공유 리소스에서는 끄기를 권장합니다. C는 자동 승인이 차단하는 동작 목록에 `DROP`의 `CASCADE` 추가가 들어 있으므로 틀립니다. D는 본문이 Job 태스크에서는 자동 승인을 끌 수 없다고 명시하므로 틀립니다. A는 권장 방향이 반대입니다.

근거: [모드·기능과 데이터 접근 권한 — 승인 (Approve tool actions)](genie-code/features-and-permissions.md#승인-approve-tool-actions)

</details>

### 2. 로컬 IDE에서 Python으로 Spark 코드를 작성하고, 실행은 Databricks 컴퓨트에서 하려 한다. 본문 기준으로 맞는 도구는? (수준 100)

- A. Python SDK의 `WorkspaceClient`로 로컬 IDE에 Spark 세션을 연다.
- B. Databricks Connect를 쓴다.
- C. `databricks bundle deploy`로 로컬 Spark 세션을 연다.
- D. `AccountClient`로 계정 수준 Spark 세션을 연다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 두 방식을 고르는 기준 표는 "로컬 IDE에서 Spark 코드를 디버깅하고 싶은가"의 답으로 Databricks Connect를 제시합니다. 본문은 Connect가 로컬 Python·Scala·R 프로세스에서 Spark 코드를 실행하되 컴퓨트는 Databricks를 쓰는 도구라고 설명합니다. SDK는 애플리케이션 코드에서 워크스페이스 API를 호출하는 용도, `bundle deploy`는 리소스를 배포하는 명령, `AccountClient`는 계정 수준 API용이므로 모두 틀립니다.

근거: [REST API와 Databricks Connect — 4. 두 방식을 고르는 기준](sdk-and-apis/rest-api-and-connect.md#4-두-방식을-고르는-기준), [REST API와 Databricks Connect — 3. Databricks Connect](sdk-and-apis/rest-api-and-connect.md#3-databricks-connect)

</details>

### 3. 사용자마다 다른 Unity Catalog 권한으로 데이터를 보여 줘야 하는 Databricks App을 만든다. 맞는 권한 모델은? (수준 100)

- A. 앱 권한: 모든 사용자가 같은 앱 권한을 쓰므로 사용자마다 다른 행과 테이블 권한이 자동으로 적용된다.
- B. 사용자 권한: 로그인한 사용자의 자격 증명으로 Unity Catalog의 세밀한 권한이 그대로 적용된다.
- C. 앱 권한: 앱을 만든 개발자 본인의 계정 권한을 그대로 빌려 쓴다.
- D. 사용자 권한: 앱이 실행 때마다 새 리소스를 만들어 사용자별로 권한을 분리한다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 사용자 권한은 SSO로 로그인한 사용자의 자격 증명을 쓰고, Unity Catalog의 세밀한 권한이 그대로 적용됩니다. 앱 권한의 신원은 앱별로 자동 생성되는 서비스 프린시펄이며, 모든 사용자가 같은 권한을 공유합니다. 따라서 A는 틀립니다. C도 신원이 개발자 계정이 아니므로 틀립니다. 본문은 앱이 기존 리소스만 쓸 수 있고 새로 만들 수 없다고 명시하므로 D도 틀립니다.

근거: [Databricks Apps 개요와 리소스 바인딩 — 7. 두 가지 권한 모델](apps/overview-and-resources.md#7-두-가지-권한-모델)

</details>

### 4. `-p`를 지정하지 않고 `databricks clusters list`를 실행했더니 기대한 워크스페이스가 아닌 곳의 결과가 나왔다. 본문이 지목하는 원인은? (수준 200)

- A. 출력 형식을 `text`로 두어 요청이 다른 워크스페이스로 나갔다.
- B. 셸에 `DATABRICKS_TOKEN` 환경 변수가 설정되어 있어, `.databrickscfg`의 프로필보다 먼저 쓰였다.
- C. `databricks -v`로 확인한 CLI 버전이 낮아 프로필 파일을 건너뛰었다.
- D. 번들 설정 파일의 워크스페이스 설정이 환경 변수보다 항상 나중에 적용된다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 자격 증명을 번들 설정 파일, 환경 변수, 구성 프로필 순서로 찾고 값을 찾으면 멈춘다고 설명합니다. `DATABRICKS_TOKEN`이 있으면 `.databrickscfg`에 토큰이 여러 개 있어도 환경 변수가 우선합니다. 본문은 이 순서 때문에 예상과 다른 워크스페이스로 명령이 나가는 사고가 생긴다고 주의를 줍니다. 출력 형식은 워크스페이스 선택과 무관하고, 번들 설정 파일은 환경 변수보다 먼저 확인되므로 A, C, D는 틀립니다.

근거: [Databricks CLI 설치와 인증 — 6. 자격 증명 선택 순서](cli/install-and-auth.md#6-자격-증명-선택-순서)

</details>

### 5. 매일 아침 Genie Code로 전일 데이터를 점검한다. 판단 결과(마지막 줄 OK 또는 CHECK)를 같은 Job의 다음 태스크가 읽어 분기하고, 실패 시에는 Job의 재시도 체계를 쓰려 한다. 가장 적합한 구성은? (수준 200)

- A. 예약 작업(Scheduled tasks)으로 프롬프트를 등록하고, 실행마다 생기는 채팅을 사람이 읽는다.
- B. Lakeflow Jobs에 Genie Code 태스크를 추가하고, 다음 태스크에서 `{{tasks.<task_name>.output.response}}`를 참조한다.
- C. Genie Code 채팅을 노트북에서 열어 매번 수동으로 프롬프트를 실행한다.
- D. Genie Code 태스크의 자동 승인을 끄고, 실행마다 사람이 승인한 뒤 다음 태스크를 돌린다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 예약 작업은 대화형 채팅을 반복 실행해 결과를 채팅으로 남기는 기능이며, 다음 단계로 연결하는 방법은 문서에 없습니다. Lakeflow Jobs의 Genie Code 태스크는 Job 실행 안의 한 태스크로 돌고, 응답을 `{{tasks.<task_name>.output.response}}`로 다음 태스크에 넘기며, 재시도와 알림은 Advanced 설정에서 정합니다. D는 본문이 Job 태스크의 자동 승인을 끌 수 없다고 명시하므로 틀립니다. C는 반복 실행 자동화의 목적과 맞지 않습니다.

근거: [예약 작업 — 예약 작업과 Lakeflow Jobs 태스크](genie-code/scheduled-tasks.md#예약-작업과-lakeflow-jobs-태스크), [Lakeflow Jobs의 Genie Code 태스크 — 다음 태스크에서 응답 쓰기](genie-code/lakeflow-jobs-task.md#다음-태스크에서-응답-쓰기)

</details>

### 6. Databricks 노트북에서 `WorkspaceClient()`를 인수 없이 만들었다. 본문이 설명하는 인증 동작으로 맞는 것은? (수준 200)

- A. 사용자가 `.databrickscfg`에 저장해 둔 구성 프로필이 자동으로 우선 적용된다.
- B. 노트북 실행 동안 Databricks가 자동으로 만든 임시 개인 액세스 토큰을 쓰고, 실행이 끝나면 토큰이 삭제된다.
- C. 드라이버 노드뿐 아니라 워커 노드에서도 같은 방식으로 동작한다.
- D. 토큰을 노트북 셀에 직접 적어야 동작한다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 노트북에서 인수 없이 만든 클라이언트가 실행 동안만 유효한 임시 토큰을 쓰고, 실행이 끝나면 토큰이 삭제된다고 설명합니다. 이 인증은 드라이버 노드에서만 동작하고 구성 프로필과 함께 쓸 수 없으므로 A와 C는 틀립니다. 토큰을 셀에 적을 필요가 없으므로 D도 틀립니다. 토큰을 코드에 넣는 방식은 본문이 권장하지 않습니다.

근거: [Python SDK — 6-3. 노트북 기본 인증](sdk-and-apis/python-sdk.md#6-3-노트북-기본-인증)

</details>

### 7. 개발 타깃에 번들을 배포하기 전, 워크스페이스를 바꾸지 않고 변경 내용만 미리 보려 한다. 적합한 명령은? (수준 200)

- A. `databricks bundle deploy -t dev`
- B. `databricks bundle plan -t dev`
- C. `databricks bundle run my_job -t dev`
- D. `databricks bundle destroy -t dev`

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 명령 흐름 표에서 `plan`은 배포 시 수행될 작업을 실제 변경 없이 표시하며 워크스페이스를 바꾸지 않습니다. `deploy`는 리소스와 파일을 원격 워크스페이스에 반영하고, `run`은 잡을 실행하며, `destroy`는 배포된 리소스를 삭제합니다. 세 명령은 모두 워크스페이스를 바꾸므로 A, C, D는 틀립니다. 본문은 `plan` 결과를 확인한 뒤 `deploy`를 실행하는 습관을 강조합니다.

근거: [번들 수명 주기와 기존 리소스 bind — 2. 명령 흐름](bundles/lifecycle-and-bind.md#2-명령-흐름)

</details>

### 8. 직접 배포 엔진을 쓰는 번들에서 `databricks.yml`의 설정 필드 한 줄을 지우고 배포했다. 본문이 설명하는 결과는? (수준 300)

- A. 필드가 지워진 것을 감지해 배포가 중단된다.
- B. 워크스페이스의 리소스는 마지막 값을 그대로 유지한다.
- C. 리소스가 그 필드의 기본값으로 되돌아간다. Terraform 엔진이 값을 그대로 두던 것과 다르다.
- D. 필드가 무시되고 다른 타깃의 값이 자동으로 복사된다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: C** — 본문의 직접 엔진 동작 차이 표는 설정된 필드를 지우면 다음 배포에서 리소스 기본값으로 되돌아가며, Terraform은 값을 그대로 둔다고 설명합니다. 값을 유지하려면 번들 설정에 명시적으로 씁니다. B는 Terraform 방식에 가깝고 직접 엔진의 동작이 아닙니다. A와 D는 본문에 없는 동작입니다.

근거: [배포 엔진 — 6.1 직접 엔진의 알려진 동작 차이](bundles/deployment-engine.md#61-직접-엔진의-알려진-동작-차이)

</details>

### 9. 팀이 Genie Code 사용량에 예산을 걸고 "Block usage" 임계값을 설정했다. 본문이 명시하는 내용으로 맞는 것은? (수준 300)

- A. 청구 금액의 절대 상한이므로, 상한을 넘는 청구는 발생하지 않는다.
- B. 사용량 추적은 거의 실시간 추정이므로, 임계값에 도달하기 전에 차단되거나 차단이 적용되기 전에 한도를 넘을 수 있다.
- C. 예산 설정으로 사용자의 월 무료 사용량을 없앨 수 있다.
- D. 태그는 여러 개를 함께 붙일수록 추적이 정확해진다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문의 정확도 한계 절은 사용량 추적이 거의 실시간 추정이라 차단과 알림이 대략적으로 동작하며, 청구 금액의 상한으로 쓰면 안 된다고 경고합니다. C는 본문이 예산 설정으로 무료 사용량을 없앨 수 없다고 명시하므로 틀립니다. D는 본문이 태그 `databricks-product=genie` 하나만 쓰라고 하고 다른 태그를 붙이면 추적되지 않는다고 하므로 틀립니다.

근거: [거버넌스와 비용 — 정확도 한계](genie-code/governance-and-cost.md#정확도-한계), [거버넌스와 비용 — 과금 구조](genie-code/governance-and-cost.md#과금-구조)

</details>

### 10. 팀이 운영 Git 폴더를 두고, PR이 병합되면 자동화가 최신 커밋으로 갱신하는 구조를 설계한다. 본문의 설계 원칙에 맞는 것은? (수준 300)

- A. 운영 Git 폴더는 누구나 편집할 수 있게 열어 두고, 편집 이력은 Git 커밋으로 추적한다.
- B. 운영 폴더는 자동화만 갱신하고 편집은 관리자와 서비스 프린시펄로 제한한다. 워크플로 실행자와 자동화 서비스 프린시펄에는 Can Run을 주고, 필요하면 전체 사용자에게 Can View를 준다.
- C. 개발자가 운영 폴더의 배포 브랜치에 직접 커밋한 뒤 자동화가 나중에 맞추도록 한다.
- D. 자동화 서비스 프린시펄에 워크스페이스 관리자 권한을 주면 권한 관리가 단순해진다.

<details markdown="1">
<summary>정답과 해설</summary>

**정답: B** — 본문은 운영 Git 폴더를 자동화만 갱신하고, 편집은 관리자와 서비스 프린시펄로 제한하도록 권장합니다. 권한 설정 단계에서도 워크플로 실행 사용자와 자동화 서비스 프린시펄에 Can Run, 필요하면 전체 사용자에게 Can View를 주라고 설명합니다. A와 C는 사람이 운영 폴더를 고치면 저장소와 어긋난다는 본문의 주의와 반대입니다. D는 권한 최소화 원칙에 어긋납니다.

근거: [Git 폴더와 CI/CD 패턴 — 7. 운영 Git 폴더 만들기](git-and-cicd/git-folders-and-cicd.md#7-운영-git-폴더-만들기)

</details>

## 실무 체크리스트

이 장의 내용을 실제 환경에 적용할 때 확인할 항목입니다.

- [ ] Genie Code 패널의 승인 설정을 확인하고, 운영이나 민감 데이터가 있는 워크스페이스에서는 자동 승인을 끈다 — [모드·기능과 데이터 접근 권한](genie-code/features-and-permissions.md#승인-approve-tool-actions)
- [ ] 파트너 AI 기능의 계정·워크스페이스 설정 상태와 설정 제거 예정 일정을 확인한다 — [거버넌스와 비용](genie-code/governance-and-cost.md#모델과-데이터-처리-범위)
- [ ] 예산은 청구 상한이 아니므로, 실제 비용은 `system.billing.usage`로 확인하고 임계값에만 기대지 않는다 — [거버넌스와 비용](genie-code/governance-and-cost.md#정확도-한계)
- [ ] 예약 작업의 실행 권한은 생성자의 Unity Catalog 권한이므로, 생성자가 바뀌기 전에 작업을 점검하는 절차를 둔다 — [예약 작업](genie-code/scheduled-tasks.md#주의사항)
- [ ] 연결된 MCP 서버의 인증 만료와 권한 변경을 담당자가 주기적으로 확인한다 (권한이 바뀌면 예약 작업은 재인증 전까지 실패한다) — [MCP 서버 연결](genie-code/mcp.md#트레이드오프)
- [ ] 번들을 배포하기 전에 `validate`와 `plan`을 실행하고 결과를 검토한다 — [번들 수명 주기와 기존 리소스 bind](bundles/lifecycle-and-bind.md#2-명령-흐름)
- [ ] 개발 타깃의 카탈로그와 스키마를 운영과 분리한다 — [Declarative Automation Bundles 개요](bundles/overview.md#7-주의사항)
- [ ] 직접 배포 엔진으로 옮기기 전에 개발 타깃에서 먼저 시험하고, 유지해야 할 설정 필드는 번들 설정에 명시한다 — [배포 엔진](bundles/deployment-engine.md#53-전환-순서)
- [ ] 운영 Git 폴더는 자동화만 갱신하고, 자동화의 Git 자격 증명은 서비스 프린시펄에 연결해 주기적으로 회전한다 — [Git 폴더와 CI/CD 패턴](git-and-cicd/git-folders-and-cicd.md#10-주의사항)

## 참고 문서

이 페이지는 이 장 본문을 근거로 합니다. 공식 문서 링크는 각 본문 페이지의 참고 문서를 보세요.

- [모드·기능과 데이터 접근 권한](genie-code/features-and-permissions.md)
- [인스트럭션과 스킬](genie-code/instructions-and-skills.md)
- [MCP 서버 연결](genie-code/mcp.md)
- [예약 작업](genie-code/scheduled-tasks.md)
- [Lakeflow Jobs의 Genie Code 태스크](genie-code/lakeflow-jobs-task.md)
- [Genie Code CLI](genie-code/cli.md)
- [거버넌스와 비용](genie-code/governance-and-cost.md)
- [Databricks CLI 설치와 인증](cli/install-and-auth.md)
- [명령 그룹과 출력 형식](cli/commands-and-output.md)
- [Declarative Automation Bundles 개요](bundles/overview.md)
- [번들 수명 주기와 기존 리소스 bind](bundles/lifecycle-and-bind.md)
- [배포 엔진: Terraform에서 직접 배포 엔진으로](bundles/deployment-engine.md)
- [Python SDK: WorkspaceClient와 AccountClient](sdk-and-apis/python-sdk.md)
- [REST API와 Databricks Connect](sdk-and-apis/rest-api-and-connect.md)
- [Databricks Apps 개요와 리소스 바인딩](apps/overview-and-resources.md)
- [Databricks Apps 설정과 배포](apps/configure-and-deploy.md)
- [Git 폴더와 CI/CD 패턴](git-and-cicd/git-folders-and-cicd.md)
