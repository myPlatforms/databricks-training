# <img src="https://www.databricks.com/sites/default/files/2025-05/primary-icon-orange-lakehouse.svg" alt="" width="40" class="chapter-icon"> 1. 플랫폼 개요

> 기준일: 2026-10-28 · 근거: 공식 문서 · 수준: 100~200

Databricks는 데이터 엔지니어링, 분석, 머신러닝, 생성형 AI를 하나의 플랫폼에서 다루는 관리형 서비스입니다. 이 장은 Databricks를 처음 배우는 사람이 이후 장의 입구에서 필요한 큰 그림을 잡도록 돕습니다. 플랫폼이 무엇이고 왜 필요한지, 클라우드 안에서 어떤 구성 요소로 나뉘어 동작하는지, 계정·워크스페이스·메타스토어가 어떻게 연결되는지, 처음 보는 화면과 노트북을 어떻게 쓰는지, 비용이 어떤 단위로 계산되는지, 무료로 어떻게 시작하는지를 다룹니다.

이 장은 세부 기능을 깊게 파지 않습니다. 각 주제의 상세 설정과 실습은 뒤의 장에서 다루고, 이 장에서는 그 장들을 읽기 위한 용어와 구조를 정리합니다.

## 학습 목표

이 장을 마치면 다음을 할 수 있습니다.

- Databricks가 제공하는 기능 영역(저장, 컴퓨트, 거버넌스, 분석, AI, 트랜잭션)을 구분하고, 레이크하우스 개념으로 설명합니다.
- control plane과 compute plane의 역할 차이를 설명하고, 클래식(classic)과 서버리스(serverless) 컴퓨트 플레인이 어디서 실행되는지 구분합니다.
- 계정(account), 워크스페이스(workspace), Unity Catalog 메타스토어(metastore)의 포함 관계를 그릴 수 있습니다.
- 워크스페이스 사이드바와 상단바의 주요 항목을 찾고, 노트북을 만들어 셀을 실행합니다.
- 노트북의 언어 전환(`%sql` 등), 매직 명령(`%run` 등), 위젯(widget)의 기본 사용법을 익힙니다.
- DBU(Databricks Unit) 개념과 `system.billing.usage` 시스템 테이블로 사용량을 확인하는 방법을 알고, 서버리스와 클래식의 과금 구조 차이를 설명합니다.
- Free Edition과 무료 체험판(free trial)의 차이를 구분하고, 자신에게 맞는 시작 경로를 고릅니다.

## 페이지 안내

| 순서 | 페이지 | 수준 | 다루는 내용 |
|---|---|---|---|
| 1 | [플랫폼이란 무엇인가](what-is-databricks.md) | 100 | 왜 필요한가, 레이크하우스 개념, 기능 영역 지도, 이후 장 연결 |
| 2 | [플랫폼 아키텍처](architecture.md) | 100 | control plane과 compute plane, 클래식과 서버리스 컴퓨트 플레인, 워크스페이스 스토리지 |
| 3 | [계정·워크스페이스·메타스토어](account-workspace-metastore.md) | 200 | 계정 단위 관리, 워크스페이스의 역할, 메타스토어와 3단계 이름 구조 |
| 4 | [워크스페이스 UI](workspace-ui.md) | 200 | 홈 화면, 사이드바 항목, 상단바, + New 메뉴, 검색 |
| 5 | [노트북 기초](notebooks-basics.md) | 200 | 지원 언어, 셀 실행, 언어·매직 명령, `%run`, 위젯 |
| 6 | [과금 모델 기초](billing-basics.md) | 200 | DBU 개념, 서버리스와 클래식의 과금 구조, `system.billing.usage` 조회 |
| 7 | [시작하기](getting-started.md) | 100 | Free Edition, 무료 체험판, 공식 튜토리얼 순서 |
| 8 | [용어 정리](glossary.md) | 100 | 이 장과 이후 장에서 쓰는 핵심 용어 표 |
| 9 | [퀴즈와 체크리스트](quiz.md) | 100~300 | 장 내용 확인 문제 9개와 실무 체크리스트 |

권장 학습 순서는 위 표 순서입니다. 「플랫폼 아키텍처」와 「계정·워크스페이스·메타스토어」 페이지는 이후 모든 장의 전제이므로 건너뛰지 않는 것을 권장합니다. 직접 따라 해 보려면 「시작하기」 페이지를 먼저 읽고 워크스페이스를 만든 뒤 「워크스페이스 UI」와 「노트북 기초」 페이지를 따라 해도 됩니다.

## 선수 지식

- **SQL 기초**: `SELECT`, `WHERE`, `GROUP BY`를 읽을 수 있으면 충분합니다.
- **Python 기초**: 변수, 함수 호출, 리스트 정도를 알고 있으면 「노트북 기초」 페이지의 예제를 따라갈 수 있습니다.
- **클라우드 기본 개념**: 계정, 리전(region), 객체 스토리지(object storage)라는 말을 들어 본 정도면 충분합니다. 이 장에서 AWS 콘솔 조작은 요구하지 않습니다.

## 이 장의 읽는 법

이 장의 사실은 Databricks 공식 문서(AWS 기준, `docs.databricks.com/aws/en/`)에서 확인한 내용입니다. 기능 상태 라벨(GA, Public Preview, Beta)은 원문에 적힌 표기를 그대로 옮겼고, 원문에 표기가 없는 항목은 "문서에 명시 없음"으로 적었습니다.

> **참고** Azure Databricks를 쓰는 경우에도 개념(control plane, compute plane, 메타스토어, DBU)은 같습니다. 다만 리전 목록, 컴퓨트 기본값, 무료 체험 조건 등은 클라우드별로 다를 수 있으니 Azure 문서(`learn.microsoft.com/azure/databricks/`)를 따로 확인하십시오.

> **참고** 플랫폼 명칭은 공식 소개 페이지의 표기를 따랐습니다. 다른 자료에서 "Data Intelligence Platform"이라는 표현을 볼 수 있지만, 이 장이 근거로 삼은 공식 소개 페이지는 "Databricks Data + AI Platform"이라고 씁니다.

## 이후 장과의 연결

| 이 장에서 다루는 것 | 이후 장에서 깊게 다루는 것 |
|---|---|
| 저장 영역의 구분(워크스페이스 스토리지, 기본 스토리지, 외부 위치) | 02장에서 다룹니다 (스토리지) |
| 클래식과 서버리스 컴퓨트 개념 | 03장에서 다룹니다 (컴퓨트) |
| 메타스토어와 3단계 이름 구조 | 06장에서 다룹니다 (Unity Catalog) |
| 트랜잭션 워크로드의 위치 | [10장 Lakebase](../10-lakebase/README.md)에서 다룹니다 |
| 개발 도구와 AI 코딩 보조 | [11장 개발자 도구](../11-developer-tools/README.md)에서 다룹니다 |

## 참고 문서

- [What is Databricks?](https://docs.databricks.com/aws/en/introduction/)
- [Get started tutorials on Databricks](https://docs.databricks.com/aws/en/getting-started/)
- [High-level architecture](https://docs.databricks.com/aws/en/getting-started/high-level-architecture)
- [Databricks notebooks](https://docs.databricks.com/aws/en/notebooks/)
- [Compute](https://docs.databricks.com/aws/en/compute/)
