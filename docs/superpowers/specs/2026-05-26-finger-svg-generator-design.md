# Finger SVG Generator — Design Spec

> **최종 업데이트: 2026-05-29 (v1.0 기준)**
> 원본 작성일: 2026-05-26

---

## Overview

수 세기 교육 및 수학 문제 출제용 손가락 이미지 생성기.
Python + Streamlit 기반, 사용자 제공 SVG 파일을 조합하여 최종 SVG/PNG를 생성한다.

**배포:** https://finger-svg-generator-n8nqi3wtcprqmh2qvbrrrg.streamlit.app/

---

## File Structure

```
finger-svg-generator/
├── app.py                  # Streamlit UI
├── finger_svg.py           # SVG 로직
├── requirements.txt
├── components/
│   ├── hand_0_a.svg
│   ├── hand_1_a/b/c.svg
│   ├── hand_2_a/b/c.svg
│   ├── hand_3_a/b/c.svg
│   ├── hand_4_a/b.svg
│   └── hand_5_a.svg
└── tests/
    ├── conftest.py
    └── test_finger_svg.py
```

### SVG 파일 명명 규칙

- `hand_{number}_{variant}.svg`
- number: 0~5 (손가락 개수)
- variant: a, b, c (알파벳순, a가 기본값)
- 파일 추가 시 코드 수정 없이 자동 감지됨

---

## Color System

SVG 내 두 가지 베이스 색상을 아래 팔레트로 치환.

| 이름 | 손 색상 (BASE_HAND_COLOR) | 그림자 색상 (BASE_SHADOW_COLOR) | 미리보기 배경 |
|------|--------------------------|-------------------------------|-------------|
| 피부색 (기본) | `#FFC6BD` | `#f9897a` | `#FFFFFF` |
| 흰색 | `#FFFFFF` | `#b3b3b3` | `#2F424E` |
| 깨다 | `#FF6666` | `#d54141` | `#FFFFFF` |
| 챌리 | `#FFDC0B` | `#edaf00` | `#FFFFFF` |
| 따미 | `#26C9CB` | `#008f8b` | `#FFFFFF` |

- 다운로드 SVG: "흰색" 색상은 배경 `none` (투명), 나머지는 배경 `#FFFFFF`

---

## Number Decomposition

| 숫자 범위 | 손 개수 | 각 손 값 |
|----------|--------|---------|
| 0~5 | 1개 | `[N]` |
| 6~10 | 2개 | `[5, N-5]` |
| 11~15 | 3개 | `[5, 5, N-10]` |
| 16~20 | 4개 | `[5, 5, 5, N-15]` |

### 손 방향 기본값

```python
def default_hand_directions(count):
    if count == 1:
        return [True]           # 오른손
    return [i % 2 == 1 for i in range(count)]
    # 2손: [왼, 오] / 3손: [왼, 오, 왼] / 4손: [왼, 오, 왼, 오]
```

`flip=True` = 오른손 (SVG를 수평 반전), `flip=False` = 왼손 (원본 방향)

---

## Core Logic: finger_svg.py

### 상수

```python
BASE_HAND_COLOR   = "#FFC6BD"  # SVG 손 메인 색상
BASE_SHADOW_COLOR = "#f9897a"  # SVG 그림자 색상
HAND_GAP   = 40   # 손 사이 기본 간격 (px)
CANVAS_PAD = 16   # 잘림 방지 캔버스 여백 (px)
```

### 주요 함수

```python
load_svg(path: str) -> str
# SVG 파일 로드 + lru_cache 캐싱

get_variants(number: int, components_dir: str) -> list[str]
# 파일 자동 감지로 변형 목록 반환
# ex) get_variants(2) → ['a', 'b', 'c']

get_svg_dimensions(svg_str: str) -> tuple[float, float]
# viewBox 우선, 없으면 width/height 파싱

apply_color(svg_str: str, target_color: str) -> str
# BASE_HAND_COLOR → target_color (case-insensitive 치환)

apply_shadow(svg_str: str, shadow_color: str) -> str
# BASE_SHADOW_COLOR → shadow_color (case-insensitive 치환)

apply_flip(svg_str: str) -> str
# <g transform="scale(-1,1) translate(-W,0)"> 래핑

decompose(n: int) -> list[int]
# n → 손 값 리스트 (0 → [0], 7 → [5,2], 18 → [5,5,5,3])

default_hand_directions(count: int) -> list[bool]
# 손 개수 → 방향(flip) 기본값 리스트

build_svg(hands_config, bg_color, components_dir, hand_gap) -> str
# 손 목록 → 최종 SVG 문자열
```

### hands_config 구조

```python
[
    {"value": 5, "variant": "a", "color": "#FFC6BD", "shadow": "#f9897a", "flip": False},
    {"value": 2, "variant": "b", "color": "#FFC6BD", "shadow": "#f9897a", "flip": True},
]
```

### build_svg 동작 방식

각 손 SVG를 `<image href="data:image/svg+xml;base64,...">` 로 임베드.
→ CSS 클래스명 충돌 완전 차단 (중요: 여러 SVG가 `.cls-1` 등을 공유할 경우 스타일 오염 방지)

```
canvas_w = sum(widths) + hand_gap * (n-1) + CANVAS_PAD * 2
canvas_h = max(heights) + CANVAS_PAD * 2
```

---

## UI: app.py (Streamlit)

### 레이아웃

```
[색상 선택 버튼 5개]
[숫자 입력 (0~20)]
[미리보기 이미지]
[컨트롤 박스: 손별 방향 + 변형 썸네일]
[손 사이 간격 슬라이더]  ← 2손 이상일 때만 표시
[SVG 저장] [PNG 저장]
```

### 색상 선택 버튼

- `st.button`에 CSS `background-color`를 직접 주입 (`inject_css()`에서 처리)
- 선택된 색상: `border: 2px solid {shadow_color}`
- 미선택: `border: 1.5px solid #ddd`, `opacity: 0.75`

### 손별 설정

- **방향**: 왼손 / 오른손 세그먼트 버튼 (좌우 연결 스타일)
- **변형 썸네일**: `st.button`에 CSS `background-image: url(data:image/svg+xml;base64,...)` 주입
  - 버튼 자체가 64×72px 썸네일로 표시됨
  - Streamlit의 onclick sanitization을 우회하는 핵심 방식
  - 변형이 1개뿐이면 숨김

### 다운로드

- SVG: `st.download_button` — 배경색 처리 후 저장
- PNG: `<button>` + Canvas API (JavaScript) — 2× 해상도 변환
  - Streamlit이 onclick을 sanitize하지 않는 `<button>` 태그 직접 사용 (st.markdown이 아님)

### 파일명 규칙

```
finger_{YYYYMMDD}_{손값들}_{색상명}.svg
finger_{YYYYMMDD}_{손값들}_{색상명}.png
ex) finger_20260529_5-2_피부색.svg
```

---

## 기술 주의사항

### Streamlit HTML Sanitization

Streamlit은 `st.markdown(unsafe_allow_html=True)` 내의 `onclick` 속성을 제거한다.
따라서 클릭 이벤트가 필요한 요소는 반드시 `st.button` 등 Streamlit 컴포넌트를 사용해야 한다.

- **작동하는 방식**: `<style>` 태그, `background-image` CSS → 허용
- **작동 안 하는 방식**: `<div onclick="...">` → onclick 제거됨

### CSS Class 충돌

여러 SVG를 하나의 SVG 컨테이너 안에 중첩(`<svg>` 안에 `<svg>`)하면 `.cls-1`, `.cls-2` 등 전역 CSS 클래스가 충돌한다. 해결: `<image href="data:image/svg+xml;base64,...">` 임베딩으로 각 SVG를 완전 격리.

---

## Tests

```bash
pytest tests/ -v
```

`tests/conftest.py`의 더미 SVG는 실제 `BASE_HAND_COLOR(#FFC6BD)` 와 동기화되어 있어야 한다.
