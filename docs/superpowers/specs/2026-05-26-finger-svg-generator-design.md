# Finger SVG Generator — Design Spec
Date: 2026-05-26

## Overview

수 세기 교육 및 수학 문제 출제용 손가락 이미지 생성기.
egg-svg-generator와 동일한 기술 스택(Python + Streamlit)을 사용하며,
사용자가 제공한 SVG 파일을 조합하여 최종 SVG/PNG를 생성한다.

## File Structure

```
finger-svg-generator/
├── components/
│   ├── hand_0_a.svg          # 주먹 (변형 1개)
│   ├── hand_1_a.svg          # 변형 최대 3개
│   ├── hand_1_b.svg
│   ├── hand_1_c.svg
│   ├── hand_2_a.svg
│   ├── hand_2_b.svg
│   ├── hand_2_c.svg
│   ├── hand_3_a.svg
│   ├── hand_3_b.svg
│   ├── hand_3_c.svg
│   ├── hand_4_a.svg
│   ├── hand_4_b.svg
│   ├── hand_4_c.svg
│   └── hand_5_a.svg          # 전부 펼침 (변형 1개)
├── finger_svg.py
├── app.py
└── requirements.txt
```

### SVG 파일 명명 규칙

- `hand_{number}_{variant}.svg`
- number: 0~5 (손가락 개수)
- variant: a, b, c (알파벳 순, a가 기본값)
- 변형이 1개인 숫자는 `_a`만 존재
- 새 파일을 추가하면 코드 수정 없이 자동 감지됨

### SVG 방향 처리

- 모든 SVG는 단일 방향으로 제작 (제공 파일 기준 방향을 베이스로 사용)
- 반전이 필요한 손에는 SVG 내부 `<g transform="scale(-1,1) translate(-W,0)">` 래핑
- CSS 반전 대신 SVG transform 사용 → PNG 내보내기 시 안전
- 베이스 SVG가 왼손인 경우: 오른손에 flip 적용 / 오른손인 경우: 왼손에 flip 적용
  (SVG 파일 수령 후 확정)

## Color System

SVG 내 베이스 fill 색상을 아래 팔레트로 치환.

| 이름 | 손 색상 | 미리보기 배경 |
|------|--------|-------------|
| 피부색 (기본) | `#FFC6BD` | `#FFFFFF` |
| 흰색 | `#FFFFFF` | `#2F424E` |
| 깨다 | `#FF6666` | `#FFFFFF` |
| 챌리 | `#FFDC0B` | `#FFFFFF` |
| 따미 | `#26C9CB` | `#FFFFFF` |

- 기본 색상: 피부색
- 흰색 선택 시 미리보기 배경을 `#2F424E`로 전환

## Number Decomposition

숫자 → 손별 분해 규칙:

| 숫자 범위 | 손 개수 | 각 손 값 예시 |
|----------|--------|-------------|
| 0~5 | 1개 | [N] |
| 6~10 | 2개 | [5, N-5] |
| 11~15 | 3개 | [5, 5, N-10] |
| 16~20 | 4개 | [5, 5, 5, N-15] |

### 손 방향 기본값 (자동 배정)

| 손 번호 | 기본 방향 |
|--------|---------|
| 1번 | 오른손 |
| 2번 | 왼손 |
| 3번 | 오른손 |
| 4번 | 왼손 |

사용자가 각 손의 방향을 개별 변경 가능.

## Core Logic: finger_svg.py

### 주요 함수

```python
load_svg(path)
# SVG 파일 로드 및 캐싱. ElementTree로 파싱.

get_variants(number)
# number에 해당하는 SVG 변형 목록 반환 (파일 자동 감지)
# 예: get_variants(1) → ['a', 'b', 'c']

apply_color(svg_tree, hand_color)
# SVG 내 베이스 fill 색상을 hand_color로 치환

apply_flip(svg_tree, width)
# 오른손 방향일 때 <g transform="scale(-1,1) translate(-{width},0)"> 래핑

make_hand(number, variant, color, flip)
# 단일 손 SVG 요소 생성 (색상 치환 + 방향 적용)

decompose(n)
# 숫자 n → 손별 값 리스트 반환
# decompose(13) → [5, 5, 3]

build_svg(hands_config, bg_color)
# hands_config: [{"value": int, "variant": str, "color": str, "flip": bool}, ...]
# 손들을 가로로 배치하여 최종 SVG 문서 반환
```

### hands_config 구조

```python
[
    {"value": 5, "variant": "a", "color": "#FFC6BD", "flip": True},   # 오른손
    {"value": 3, "variant": "b", "color": "#FFC6BD", "flip": False},  # 왼손
]
```

## UI: app.py (Streamlit)

### 입력 모드

**모드 A — 숫자 입력:**
- 숫자(0~20) 입력
- 자동으로 손 개수 결정 및 방향 기본값 배정
- 각 손의 방향/변형은 사후 개별 조정 가능

**모드 B — 수동 조합:**
- [+ 손 추가] / [- 손 제거] 버튼
- 각 손: 슬라이더로 0~5 설정
- 방향 기본값은 추가 순서에 따라 자동 배정 (R, L, R, L...)

### 공통 설정

- **색상**: 전체 일괄 적용. 피부색 / 흰색 / 깨다 / 챌리 / 따미 (컬러 칩 선택)
  - 기본값: 피부색

### 손별 독립 설정 (각 손마다)

- **방향**: 오른손 / 왼손 토글 (기본값은 순서에 따라 자동 배정)
- **변형**: 해당 숫자의 변형 SVG를 썸네일로 나열, 클릭 선택, 선택된 항목 강조 테두리
  - 변형이 1개뿐이면 썸네일 UI 숨김

### 미리보기 & 내보내기

- 실시간 SVG 미리보기
- 배경: 색상 선택에 따라 자동 전환 (흰색 선택 시 `#2F424E`)
- [SVG 다운로드] [PNG 다운로드] (egg-svg-generator와 동일한 Canvas API 방식)
- 파일명: 날짜 + 숫자 기반 자동 생성

## Reference

- egg-svg-generator: https://github.com/gaehe0419/egg-svg-generator
- 동일 패턴: ElementTree SVG 조작, Streamlit UI, Base64 PNG 변환
