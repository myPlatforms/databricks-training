# CLAUDE.md — databricks-training

Databricks 한국어 교육 자료. 공개 리포 `myPlatforms/databricks-training`, GitHub Pages(MkDocs Material) 게시.
본문은 `docs/` 아래, 목차는 `docs/SUMMARY.md` 하나로 관리한다 (MkDocs `literate-nav`와 GitBook이 같은 파일을 읽는다).

## 공개 리포 규칙 (최우선)

- **공개 자료만 근거로 쓴다**: docs.databricks.com, learn.microsoft.com/azure/databricks, databricks.com 블로그·릴리즈 노트, 공개 GitHub.
- 쓰지 않는 것: 고객사명·고객 사례, 사내 링크·사내 자료(go/ 링크, 사내 검색·메신저 링크, 내부 문서), 워크스페이스 URL·ID·계정 ID·토큰, 비공개 로드맵.
  (공식 문서에 나오는 제품·커넥터 이름 자체 — 예: Slack, Glean 커넥터 — 는 써도 된다.)

## 품질 기준

각 기능 페이지는 아래 5가지를 담는다. 개요 수준에서 멈추지 않는다.

1. **왜 필요한가** — 이전 방식의 한계, 해결하는 문제
2. **어떻게 동작하는가** — 구성 요소, 동작 원리
3. **어떻게 쓰는가** — 설정·코드·SQL 예시 (실행 가능한 형태)
4. **트레이드오프** — 제약, 대안과의 비교, 비용 구조, 언제 쓰지 않는가
5. **주의사항** — 흔한 실수, 권장 설정

## 최신성 규칙

- 페이지 맨 위 메타 줄: `> 기준일: YYYY-MM-DD · 근거: 공식 문서 · 수준: 200` 형식 (수준은 아래 "수준과 퀴즈").
- 기능마다 **상태(GA / Public Preview / Beta / Private Preview)** 를 표기한다. 클라우드별로 다르면 나눠 쓴다.
- 날짜·한도·수치는 문서 원문에서 확인한 것만 쓴다. 확인 못 한 것은 쓰지 않거나 "문서에 명시 없음"이라고 쓴다.
- **제품명은 학습 지식으로 고치지 않는다.** 리브랜딩이 잦으므로 현재 문서 표기를 따른다. 구 명칭은 처음 한 번 괄호로 병기(예: "Lakeflow pipelines(구 DLT)" — docs 제목은 "Spark Declarative Pipelines on Lakeflow", 본문 표기는 "Lakeflow pipelines").
- 각 페이지 끝에 `## 참고 문서` — 근거로 쓴 공식 문서 링크 목록.
- 페이지를 고치면 기준일을 갱신하고 `docs/updates.md`에 한 줄 추가한다.

## 문체·서식

- 합니다체. 기술 용어는 첫 등장 때 영문 병기(예: "동기화 테이블(Synced Table)").
- 볼드 뒤에 한글 조사가 바로 오면 렌더링이 깨질 수 있다 → `**용어** 는`처럼 닫는 `**` 뒤에 공백.
  일괄 보정은 **정규식으로 `**…**`를 짝짓지 말고** `python3 -I tools/fix_bold.py docs`를 쓴다 (한 줄에 굵은 글씨가 둘이면 정규식이 '닫는 ** ~ 여는 **'를 짝지어 `** 텍스트**`로 깨뜨린다. 2026-10-29 98줄 손상 사례).
- 다이어그램: Mermaid·ASCII 아트 금지. 표로 표현하거나 공식 문서 이미지를 링크.
- 주의·참고 박스는 MkDocs/GitBook 양쪽에서 읽히도록 인용문으로 쓴다: `> **주의** ...`, `> **참고** ...` (`!!!` admonition, `{% hint %}` 금지).
- 코드 블록에는 언어 지정(```python, ```sql, ```bash, ```yaml).

## 수준과 퀴즈

- 페이지마다 수준 하나: **100** 개념(무엇·왜, 코드 없이 이해, 누구나) · **200** 실무(설정·UI 절차·SQL·코드) · **300** 심화(설계 판단·내부 동작·한도·운영·비용·보안). 장 README 메타 줄은 범위(`100~300`), `## 페이지 안내` 표에 `수준` 열.
- 수준만 바꿀 때는 기준일을 갱신하지 않는다 (기준일은 사실을 원문으로 확인한 날).
- 장마다 `quiz.md`(퀴즈와 체크리스트): 8~10문항, 본문 근거만, 정답은 `<details markdown="1">`로 접고 근거 섹션 링크. 정답이 날짜·버전·상태 라벨·한도 숫자 자체인 문항은 만들지 않는다.
- **본문 사실을 고치면 같은 장 `quiz.md`의 해당 문항·체크리스트도 확인한다.**

## 아이콘·이미지

- 장 아이콘은 www.databricks.com에 **공개로 게시된** `primary-icon-orange-*.svg`를 원격 URL로 참조한다 (홈 커리큘럼 표, 장 README 제목). 경로에 CMS 업로드 날짜가 들어가 사이트 개편 때 바뀔 수 있으므로 깨지면 같은 이름의 새 경로로 교체한다.
- **Brandfolder 등 사내 브랜드 자산 파일은 리포에 넣지 않는다** (사내 전용).
- 화면 캡처는 이름·이메일·워크스페이스 URL·카탈로그 이름 같은 식별 정보를 가린 뒤 `docs/assets/shots/`에 둔다.

## 파일 구성

- 폴더: 두 자리 번호 prefix + 영문 kebab-case (`10-lakebase/`). 각 폴더에 `README.md`(장 개요·학습 목표·페이지 안내).
- 파일명 영문 kebab-case. 한 페이지가 약 250줄을 넘으면 하위 페이지로 나눈다.
- 새 페이지는 반드시 `docs/SUMMARY.md`에 등록한다 (미등록 페이지는 사이트에 안 보인다).
- 내부 링크는 상대 경로 `.md` 링크.
- 실습: 노트북은 `labs/<NN-폴더>/*.py`(Databricks 노트북 소스 형식, 워크스페이스 고유 값은 위젯 자리표시자), 사이트 페이지는 `docs/<NN-폴더>/lab.md`. **워크스페이스에서 실제로 실행해 확인한 코드만** 넣고, 만든 리소스는 정리 단계에서 지운다. 사내 실습 자료(외부 공개 금지)는 흐름만 참고하고 문장·코드를 옮기지 않는다.

## 빌드·검증

```bash
uv run --frozen mkdocs build --strict   # 깨진 링크·미등록 페이지 검사
uv run --frozen mkdocs serve            # 로컬 미리보기 http://127.0.0.1:8000
```

- `uv.lock`은 공개 PyPI URL(`files.pythonhosted.org`)로 기록한다. 사내 프록시로 `uv lock`을 다시 돌리면 프록시 URL이 들어가 CI가 실패하므로, 재생성 후 URL을 공개 주소로 치환하고 `--frozen`으로 실행한다.

PR은 CI에서 `mkdocs build --strict`가 통과해야 병합한다. `main` 병합 시 GitHub Pages로 자동 배포된다.

## 최신화 파이프라인

Databricks Job `training-content-refresh`가 릴리즈 노트·블로그를 수집해 Delta(`<catalog>.training.*`)에 적재하고,
Genie Code 태스크가 영향받는 페이지의 수정안을 만든 뒤, PR을 자동으로 연다. 자동 PR도 사람이 검토 후 병합한다.
