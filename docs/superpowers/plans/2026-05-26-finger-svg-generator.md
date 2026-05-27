# Finger SVG Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 수 세기 교육 및 문제 출제용 손가락 이미지(SVG/PNG)를 생성하는 Streamlit 앱 구축

**Architecture:** `finger_svg.py`가 SVG 로딩·색상치환·반전·조합 로직을 담당하고, `app.py`가 Streamlit UI를 제공한다. 사용자가 제공한 `components/hand_{n}_{v}.svg` 파일을 조합해 최종 SVG를 생성하며, PNG 내보내기는 브라우저 Canvas API를 사용한다.

**Tech Stack:** Python 3.10+, Streamlit ≥ 1.28, xml.etree.ElementTree (stdlib), pytest

---

## File Map

| 파일 | 역할 |
|------|------|
| `finger_svg.py` | SVG 로딩·색상치환·반전·분해·조합 순수 함수 |
| `app.py` | Streamlit UI (모드 선택, 손 설정, 미리보기, 내보내기) |
| `requirements.txt` | 의존성 |
| `components/hand_{n}_{v}.svg` | 사용자 제공 SVG (Task 1에서 테스트용 더미 생성) |
| `tests/conftest.py` | pytest fixture (테스트용 SVG 파일 생성) |
| `tests/test_finger_svg.py` | finger_svg.py 단위 테스트 |

---

## Task 1: 프로젝트 셋업

**Files:**
- Create: `requirements.txt`
- Create: `tests/conftest.py`
- Create: `components/` (테스트용 더미 SVG 포함)

- [ ] **Step 1: requirements.txt 작성**

```
streamlit>=1.28.0
pytest>=7.0.0
```

- [ ] **Step 2: 테스트용 더미 SVG 생성 스크립트 실행**

`components/` 폴더에 `hand_0_a.svg` ~ `hand_5_a.svg` 6개,
추가로 `hand_1_b.svg`, `hand_2_b.svg`, `hand_2_c.svg` 생성.
아래 명령을 Python 인터프리터에서 실행:

```python
import os
os.makedirs("components", exist_ok=True)

DUMMY_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="150" viewBox="0 0 100 150">
  <circle cx="50" cy="75" r="40" fill="#FFC6BD"/>
</svg>'''

files = [f"hand_{n}_a.svg" for n in range(6)] + ["hand_1_b.svg", "hand_2_b.svg", "hand_2_c.svg"]
for f in files:
    with open(f"components/{f}", "w", encoding="utf-8") as fp:
        fp.write(DUMMY_SVG)
print("Done:", files)
```

Expected output: `Done: ['hand_0_a.svg', 'hand_1_a.svg', ..., 'hand_2_c.svg']`

- [ ] **Step 3: tests/conftest.py 작성**

```python
# tests/conftest.py
import os
import pytest

DUMMY_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="150" viewBox="0 0 100 150"><circle cx="50" cy="75" r="40" fill="#FFC6BD"/></svg>'


@pytest.fixture
def comp_dir(tmp_path):
    d = tmp_path / "components"
    d.mkdir()
    for n in range(6):
        (d / f"hand_{n}_a.svg").write_text(DUMMY_SVG, encoding="utf-8")
    (d / "hand_1_b.svg").write_text(DUMMY_SVG, encoding="utf-8")
    (d / "hand_2_b.svg").write_text(DUMMY_SVG, encoding="utf-8")
    (d / "hand_2_c.svg").write_text(DUMMY_SVG, encoding="utf-8")
    return str(d)
```

- [ ] **Step 4: 커밋**

```bash
git add requirements.txt tests/conftest.py components/
git commit -m "chore: project setup, dummy SVG fixtures"
```

---

## Task 2: SVG 로딩 & 변형 감지

**Files:**
- Create: `finger_svg.py` (일부)
- Create: `tests/test_finger_svg.py` (일부)

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_finger_svg.py
import importlib
import sys
import os
import pytest


def reload_module(comp_dir):
    """finger_svg를 새 COMPONENTS_DIR로 재로드."""
    if "finger_svg" in sys.modules:
        del sys.modules["finger_svg"]
    import finger_svg
    finger_svg.COMPONENTS_DIR = comp_dir
    finger_svg.load_svg.cache_clear()
    return finger_svg


def test_load_svg_returns_string(comp_dir):
    fsvg = reload_module(comp_dir)
    path = os.path.join(comp_dir, "hand_0_a.svg")
    result = fsvg.load_svg(path)
    assert isinstance(result, str)
    assert "<svg" in result


def test_load_svg_caches(comp_dir):
    fsvg = reload_module(comp_dir)
    path = os.path.join(comp_dir, "hand_0_a.svg")
    r1 = fsvg.load_svg(path)
    r2 = fsvg.load_svg(path)
    assert r1 is r2  # lru_cache가 동일 객체 반환


def test_get_variants_single(comp_dir):
    fsvg = reload_module(comp_dir)
    assert fsvg.get_variants(0, comp_dir) == ["a"]
    assert fsvg.get_variants(5, comp_dir) == ["a"]


def test_get_variants_multiple(comp_dir):
    fsvg = reload_module(comp_dir)
    assert fsvg.get_variants(1, comp_dir) == ["a", "b"]
    assert fsvg.get_variants(2, comp_dir) == ["a", "b", "c"]


def test_get_variants_missing_number_returns_a(comp_dir):
    fsvg = reload_module(comp_dir)
    assert fsvg.get_variants(9, comp_dir) == ["a"]
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_finger_svg.py -v
```

Expected: `ModuleNotFoundError: No module named 'finger_svg'`

- [ ] **Step 3: finger_svg.py 골격 및 load_svg / get_variants 구현**

```python
# finger_svg.py
import os
import re
import glob
import xml.etree.ElementTree as ET
from functools import lru_cache

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

SVG_NS = "http://www.w3.org/2000/svg"
COMPONENTS_DIR = "components"
BASE_HAND_COLOR = "#FFC6BD"  # SVG 파일 수령 후 실제 베이스 fill 색상으로 확정
HAND_GAP = 20  # 손 사이 간격 (px)

COLORS = {
    "피부색": "#FFC6BD",
    "흰색":   "#FFFFFF",
    "깨다":   "#FF6666",
    "챌리":   "#FFDC0B",
    "따미":   "#26C9CB",
}

BG_COLORS = {name: "#FFFFFF" for name in COLORS}
BG_COLORS["흰색"] = "#2F424E"

DEFAULT_COLOR = "피부색"


@lru_cache(maxsize=None)
def load_svg(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_variants(number: int, components_dir: str = COMPONENTS_DIR) -> list[str]:
    pattern = os.path.join(components_dir, f"hand_{number}_*.svg")
    paths = sorted(glob.glob(pattern))
    variants = []
    for p in paths:
        m = re.search(r"hand_\d+_([a-z]+)\.svg$", os.path.basename(p))
        if m:
            variants.append(m.group(1))
    return variants if variants else ["a"]
```

- [ ] **Step 4: 테스트 재실행 → 통과 확인**

```bash
pytest tests/test_finger_svg.py::test_load_svg_returns_string tests/test_finger_svg.py::test_load_svg_caches tests/test_finger_svg.py::test_get_variants_single tests/test_finger_svg.py::test_get_variants_multiple tests/test_finger_svg.py::test_get_variants_missing_number_returns_a -v
```

Expected: `5 passed`

- [ ] **Step 5: 커밋**

```bash
git add finger_svg.py tests/test_finger_svg.py
git commit -m "feat: SVG load + variant detection"
```

---

## Task 3: 색상 치환 & 치수 파싱

**Files:**
- Modify: `finger_svg.py`
- Modify: `tests/test_finger_svg.py`

- [ ] **Step 1: 실패하는 테스트 추가**

```python
# tests/test_finger_svg.py 에 추가

def test_get_svg_dimensions_from_viewbox():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300"><circle/></svg>'
    w, h = fsvg.get_svg_dimensions(svg)
    assert w == 200.0
    assert h == 300.0


def test_get_svg_dimensions_from_width_height():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="150px" height="250px"><circle/></svg>'
    w, h = fsvg.get_svg_dimensions(svg)
    assert w == 150.0
    assert h == 250.0


def test_apply_color_replaces_base(comp_dir):
    fsvg = reload_module(comp_dir)
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle fill="#FFC6BD"/></svg>'
    result = fsvg.apply_color(svg, "#FF6666")
    assert "#FF6666" in result
    assert "#FFC6BD" not in result


def test_apply_color_case_insensitive(comp_dir):
    fsvg = reload_module(comp_dir)
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle fill="#ffc6bd"/></svg>'
    result = fsvg.apply_color(svg, "#26C9CB")
    assert "#26C9CB" in result
    assert "#ffc6bd" not in result


def test_apply_color_no_change_when_no_match(comp_dir):
    fsvg = reload_module(comp_dir)
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle fill="#000000"/></svg>'
    result = fsvg.apply_color(svg, "#FF6666")
    assert "#000000" in result
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_finger_svg.py -k "dimension or apply_color" -v
```

Expected: `5 failed` (함수 없음)

- [ ] **Step 3: get_svg_dimensions, apply_color 구현 (finger_svg.py에 추가)**

```python
def get_svg_dimensions(svg_str: str) -> tuple[float, float]:
    root = ET.fromstring(svg_str)
    vb = root.get("viewBox")
    if vb:
        parts = vb.strip().split()
        return float(parts[2]), float(parts[3])
    w = re.sub(r"[^\d.]", "", root.get("width", "100"))
    h = re.sub(r"[^\d.]", "", root.get("height", "100"))
    return float(w or "100"), float(h or "100")


def apply_color(svg_str: str, target_color: str) -> str:
    pattern = re.compile(re.escape(BASE_HAND_COLOR), re.IGNORECASE)
    return pattern.sub(target_color, svg_str)
```

- [ ] **Step 4: 테스트 재실행 → 통과 확인**

```bash
pytest tests/test_finger_svg.py -k "dimension or apply_color" -v
```

Expected: `5 passed`

- [ ] **Step 5: 커밋**

```bash
git add finger_svg.py tests/test_finger_svg.py
git commit -m "feat: SVG dimension parsing + color replacement"
```

---

## Task 4: 반전(flip) & 숫자 분해

**Files:**
- Modify: `finger_svg.py`
- Modify: `tests/test_finger_svg.py`

- [ ] **Step 1: 실패하는 테스트 추가**

```python
# tests/test_finger_svg.py 에 추가

def test_apply_flip_adds_transform():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 150"><circle cx="50" cy="75" r="40" fill="#FFC6BD"/></svg>'
    result = fsvg.apply_flip(svg)
    assert "scale(-1,1)" in result
    assert "translate(" in result


def test_apply_flip_preserves_dimensions():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 150"><circle/></svg>'
    result = fsvg.apply_flip(svg)
    w, h = fsvg.get_svg_dimensions(result)
    assert w == 100.0
    assert h == 150.0


def test_decompose_zero():
    fsvg = reload_module("components")
    assert fsvg.decompose(0) == [0]


def test_decompose_single_hand():
    fsvg = reload_module("components")
    assert fsvg.decompose(3) == [3]
    assert fsvg.decompose(5) == [5]


def test_decompose_two_hands():
    fsvg = reload_module("components")
    assert fsvg.decompose(6) == [5, 1]
    assert fsvg.decompose(10) == [5, 5]


def test_decompose_three_four_hands():
    fsvg = reload_module("components")
    assert fsvg.decompose(13) == [5, 5, 3]
    assert fsvg.decompose(20) == [5, 5, 5, 5]


def test_default_hand_directions():
    fsvg = reload_module("components")
    assert fsvg.default_hand_directions(1) == [True]           # 오른손
    assert fsvg.default_hand_directions(2) == [True, False]    # 오른, 왼
    assert fsvg.default_hand_directions(4) == [True, False, True, False]
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_finger_svg.py -k "flip or decompose or directions" -v
```

Expected: `8 failed`

- [ ] **Step 3: apply_flip, decompose, default_hand_directions 구현**

```python
def apply_flip(svg_str: str) -> str:
    w, _ = get_svg_dimensions(svg_str)
    root = ET.fromstring(svg_str)
    g = ET.Element(f"{{{SVG_NS}}}g")
    g.set("transform", f"scale(-1,1) translate({-w:.4f},0)")
    for child in list(root):
        root.remove(child)
        g.append(child)
    root.append(g)
    return ET.tostring(root, encoding="unicode")


def decompose(n: int) -> list[int]:
    if n == 0:
        return [0]
    hands, remaining = [], n
    while remaining > 0:
        hands.append(min(5, remaining))
        remaining -= 5
    return hands


def default_hand_directions(count: int) -> list[bool]:
    """index 0, 2... → True(오른손/flip), index 1, 3... → False(왼손)."""
    return [i % 2 == 0 for i in range(count)]
```

- [ ] **Step 4: 테스트 재실행 → 통과 확인**

```bash
pytest tests/test_finger_svg.py -k "flip or decompose or directions" -v
```

Expected: `8 passed`

- [ ] **Step 5: 커밋**

```bash
git add finger_svg.py tests/test_finger_svg.py
git commit -m "feat: flip transform + number decomposition"
```

---

## Task 5: SVG 조립 (build_svg)

**Files:**
- Modify: `finger_svg.py`
- Modify: `tests/test_finger_svg.py`

- [ ] **Step 1: 실패하는 테스트 추가**

```python
# tests/test_finger_svg.py 에 추가

def test_build_svg_single_hand(comp_dir):
    fsvg = reload_module(comp_dir)
    config = [{"value": 3, "variant": "a", "color": "#FFC6BD", "flip": False}]
    result = fsvg.build_svg(config, bg_color="#FFFFFF", components_dir=comp_dir)
    assert "<svg" in result
    w, h = fsvg.get_svg_dimensions(result)
    assert w == 100.0  # 더미 SVG 너비
    assert h == 150.0


def test_build_svg_two_hands_width(comp_dir):
    fsvg = reload_module(comp_dir)
    config = [
        {"value": 5, "variant": "a", "color": "#FFC6BD", "flip": True},
        {"value": 2, "variant": "a", "color": "#FFC6BD", "flip": False},
    ]
    result = fsvg.build_svg(config, bg_color="#FFFFFF", components_dir=comp_dir)
    w, _ = fsvg.get_svg_dimensions(result)
    assert w == 100.0 * 2 + fsvg.HAND_GAP  # 220.0


def test_build_svg_background_color(comp_dir):
    fsvg = reload_module(comp_dir)
    config = [{"value": 0, "variant": "a", "color": "#FFFFFF", "flip": False}]
    result = fsvg.build_svg(config, bg_color="#2F424E", components_dir=comp_dir)
    assert "#2F424E" in result


def test_build_svg_color_applied(comp_dir):
    fsvg = reload_module(comp_dir)
    config = [{"value": 1, "variant": "a", "color": "#FF6666", "flip": False}]
    result = fsvg.build_svg(config, bg_color="#FFFFFF", components_dir=comp_dir)
    assert "#FF6666" in result


def test_build_svg_empty_returns_placeholder(comp_dir):
    fsvg = reload_module(comp_dir)
    result = fsvg.build_svg([], bg_color="#FFFFFF", components_dir=comp_dir)
    assert "<svg" in result
```

- [ ] **Step 2: 테스트 실행 → 실패 확인**

```bash
pytest tests/test_finger_svg.py -k "build_svg" -v
```

Expected: `5 failed`

- [ ] **Step 3: build_svg 구현**

```python
def build_svg(
    hands_config: list[dict],
    bg_color: str = "#FFFFFF",
    components_dir: str = COMPONENTS_DIR,
) -> str:
    """
    hands_config: list of {"value": int, "variant": str, "color": str, "flip": bool}
    반환: 최종 SVG 문자열
    """
    if not hands_config:
        root = ET.Element(f"{{{SVG_NS}}}svg")
        root.set("xmlns", SVG_NS)
        root.set("width", "100")
        root.set("height", "100")
        ET.SubElement(root, f"{{{SVG_NS}}}rect").attrib.update(
            {"width": "100", "height": "100", "fill": bg_color}
        )
        return ET.tostring(root, encoding="unicode")

    processed = []
    for cfg in hands_config:
        path = os.path.join(components_dir, f"hand_{cfg['value']}_{cfg['variant']}.svg")
        svg_str = load_svg(path)
        svg_str = apply_color(svg_str, cfg["color"])
        if cfg["flip"]:
            svg_str = apply_flip(svg_str)
        processed.append(svg_str)

    hand_w, hand_h = get_svg_dimensions(processed[0])
    n = len(processed)
    total_w = hand_w * n + HAND_GAP * (n - 1)

    root = ET.Element(f"{{{SVG_NS}}}svg")
    root.set("xmlns", SVG_NS)
    root.set("viewBox", f"0 0 {total_w:.2f} {hand_h:.2f}")
    root.set("width", f"{total_w:.2f}")
    root.set("height", f"{hand_h:.2f}")

    bg = ET.SubElement(root, f"{{{SVG_NS}}}rect")
    bg.set("width", f"{total_w:.2f}")
    bg.set("height", f"{hand_h:.2f}")
    bg.set("fill", bg_color)

    x_offset = 0.0
    for svg_str in processed:
        hand_elem = ET.fromstring(svg_str)
        hand_elem.set("x", f"{x_offset:.2f}")
        hand_elem.set("y", "0")
        root.append(hand_elem)
        x_offset += hand_w + HAND_GAP

    return ET.tostring(root, encoding="unicode")
```

- [ ] **Step 4: 전체 테스트 실행 → 통과 확인**

```bash
pytest tests/ -v
```

Expected: `모든 테스트 passed`

- [ ] **Step 5: 커밋**

```bash
git add finger_svg.py tests/test_finger_svg.py
git commit -m "feat: build_svg — assemble multi-hand SVG"
```

---

## Task 6: Streamlit 앱 골격 + 색상 선택

**Files:**
- Create: `app.py`

> 이 태스크부터는 UI이므로 테스트 대신 `streamlit run app.py` 로 직접 확인한다.

- [ ] **Step 1: app.py 기본 구조 작성**

```python
# app.py
import base64
import datetime
import streamlit as st
import streamlit.components.v1 as components

from finger_svg import (
    COLORS, BG_COLORS, DEFAULT_COLOR,
    get_variants, decompose, default_hand_directions, build_svg,
)
# COLORS  = {"피부색": "#FFC6BD", "흰색": "#FFFFFF", "깨다": "#FF6666", "챌리": "#FFDC0B", "따미": "#26C9CB"}
# BG_COLORS = 흰색 → "#2F424E", 나머지 → "#FFFFFF"

st.set_page_config(page_title="손가락 이미지 생성기", layout="wide")
st.title("손가락 이미지 생성기")

# ── 세션 상태 초기화 ──────────────────────────────────────────
if "mode" not in st.session_state:
    st.session_state.mode = "숫자 입력"
if "color" not in st.session_state:
    st.session_state.color = DEFAULT_COLOR
if "hands" not in st.session_state:
    # list of {"value": int, "flip": bool, "variant": str}
    st.session_state.hands = []


# ── 색상 선택 ─────────────────────────────────────────────────
st.subheader("색상")
color_cols = st.columns(len(COLORS))
for i, (name, hex_val) in enumerate(COLORS.items()):
    with color_cols[i]:
        border = "3px solid #333" if st.session_state.color == name else "1px solid #ccc"
        st.markdown(
            f'<div style="width:40px;height:40px;background:{hex_val};border:{border};border-radius:4px;cursor:pointer;margin:auto"></div>',
            unsafe_allow_html=True,
        )
        if st.button(name, key=f"color_{name}"):
            st.session_state.color = name
            st.rerun()

st.markdown("---")
```

- [ ] **Step 2: 앱 실행 → 색상 칩 표시 확인**

```bash
streamlit run app.py
```

브라우저에서 5개 색상 칩과 버튼이 표시되는지, 선택 시 테두리가 굵어지는지 확인.

- [ ] **Step 3: 커밋**

```bash
git add app.py
git commit -m "feat: Streamlit app skeleton + color picker"
```

---

## Task 7: 숫자 입력 모드

**Files:**
- Modify: `app.py`

- [ ] **Step 1: 모드 탭 및 숫자 입력 추가**

`st.markdown("---")` 아래에 추가:

```python
# ── 모드 탭 ───────────────────────────────────────────────────
tab_num, tab_manual = st.tabs(["숫자 입력", "수동 조합"])

# ── 숫자 입력 모드 ────────────────────────────────────────────
with tab_num:
    num_input = st.number_input("숫자 (0~20)", min_value=0, max_value=20, value=7, step=1)

    if st.button("생성", key="btn_generate_num"):
        values = decompose(int(num_input))
        flips  = default_hand_directions(len(values))
        variants = [get_variants(v)[0] for v in values]  # 기본 변형 = 첫 번째
        st.session_state.hands = [
            {"value": v, "flip": f, "variant": var}
            for v, f, var in zip(values, flips, variants)
        ]
        st.rerun()
```

- [ ] **Step 2: 앱 실행 → 숫자 입력 후 "생성" 클릭 시 session_state.hands 설정 확인**

```bash
streamlit run app.py
```

숫자 13 입력 → 생성 클릭 → `st.session_state.hands`에 3개 항목 확인 (브라우저 개발자 도구 또는 `st.write(st.session_state.hands)` 임시 추가).

- [ ] **Step 3: 커밋**

```bash
git add app.py
git commit -m "feat: number input mode — auto decompose to hands"
```

---

## Task 8: 수동 조합 모드

**Files:**
- Modify: `app.py`

- [ ] **Step 1: 수동 조합 탭 구현**

`with tab_manual:` 블록 추가 (tab_num 블록 바로 다음):

```python
with tab_manual:
    col_add, col_remove = st.columns([1, 1])
    with col_add:
        if st.button("＋ 손 추가", key="btn_add_hand"):
            idx = len(st.session_state.hands)
            flip = (idx % 2 == 0)
            st.session_state.hands.append({"value": 0, "flip": flip, "variant": "a"})
            st.rerun()
    with col_remove:
        if st.button("－ 손 제거", key="btn_remove_hand", disabled=len(st.session_state.hands) == 0):
            st.session_state.hands.pop()
            st.rerun()

    for i, hand in enumerate(st.session_state.hands):
        new_val = st.slider(
            f"{i+1}번 손 손가락 수",
            min_value=0, max_value=5,
            value=hand["value"],
            key=f"slider_{i}",
        )
        if new_val != hand["value"]:
            # 값이 바뀌면 변형도 해당 숫자의 첫 번째로 리셋
            variants = get_variants(new_val)
            st.session_state.hands[i]["value"] = new_val
            st.session_state.hands[i]["variant"] = variants[0]
            st.rerun()
```

- [ ] **Step 2: 앱 실행 → 손 추가/제거 + 슬라이더 동작 확인**

```bash
streamlit run app.py
```

"수동 조합" 탭에서 손 추가 3회 → 슬라이더 3개 표시 확인.  
각 슬라이더 조작 시 값 반영 확인. 손 제거 시 마지막 손 제거 확인.

- [ ] **Step 3: 커밋**

```bash
git add app.py
git commit -m "feat: manual hand combination mode"
```

---

## Task 9: 손별 설정 (방향 토글 + 변형 썸네일)

**Files:**
- Modify: `app.py`

변형 썸네일과 방향 토글은 두 모드 모두에서 공통으로 사용한다.
`tab_manual` 블록 다음, `st.markdown("---")` 위에 삽입.

- [ ] **Step 1: 손별 설정 UI 추가**

```python
# ── 손별 설정 (방향 + 변형) ───────────────────────────────────
if st.session_state.hands:
    st.subheader("손 설정")
    hand_cols = st.columns(len(st.session_state.hands))

    for i, hand in enumerate(st.session_state.hands):
        with hand_cols[i]:
            st.markdown(f"**{i+1}번 손**")

            # 방향 토글
            dir_label = "오른손" if hand["flip"] else "왼손"
            if st.button(dir_label, key=f"flip_{i}"):
                st.session_state.hands[i]["flip"] = not hand["flip"]
                st.rerun()

            # 변형 썸네일 (2개 이상일 때만 표시)
            variants = get_variants(hand["value"])
            if len(variants) > 1:
                st.caption("변형 선택")
                thumb_cols = st.columns(len(variants))
                color_hex = COLORS[st.session_state.color]
                for j, variant in enumerate(variants):
                    with thumb_cols[j]:
                        # 썸네일용 단일 손 SVG (60x90 스케일)
                        thumb_svg = build_svg(
                            [{"value": hand["value"], "variant": variant,
                              "color": color_hex, "flip": hand["flip"]}],
                            bg_color="#F5F5F5",
                        )
                        border = "2px solid #333" if variant == hand["variant"] else "1px solid #ddd"
                        st.markdown(
                            f'<div style="border:{border};border-radius:4px;padding:2px;max-width:70px;overflow:hidden">'
                            f'{thumb_svg}</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button(f"{'✓' if variant == hand['variant'] else '  '}", key=f"var_{i}_{j}"):
                            st.session_state.hands[i]["variant"] = variant
                            st.rerun()

st.markdown("---")
```

- [ ] **Step 2: 앱 실행 → 방향 토글 + 변형 썸네일 동작 확인**

```bash
streamlit run app.py
```

숫자 2 입력 → 생성. `hand_2_b.svg`, `hand_2_c.svg`가 있으면 썸네일 표시 확인.  
방향 버튼 클릭 시 "오른손" ↔ "왼손" 전환 확인.

- [ ] **Step 3: 커밋**

```bash
git add app.py
git commit -m "feat: per-hand direction toggle + variant thumbnail selector"
```

---

## Task 10: 미리보기 & 내보내기

**Files:**
- Modify: `app.py`

`st.markdown("---")` 아래에 추가.

- [ ] **Step 1: SVG 미리보기 + 다운로드 함수 작성**

```python
# ── 미리보기 & 내보내기 ───────────────────────────────────────

def make_filename(hands: list[dict]) -> str:
    today = datetime.date.today().strftime("%Y%m%d")
    values = "-".join(str(h["value"]) for h in hands)
    return f"finger_{today}_{values}"


def png_download_button(svg_str: str, filename: str, scale: int = 2) -> None:
    """브라우저 Canvas API로 PNG 변환 후 다운로드."""
    svg_b64 = base64.b64encode(svg_str.encode("utf-8")).decode()
    btn_id = f"png_{abs(hash(svg_str)) % 100000}"
    html = f"""
    <button id="{btn_id}" style="background:#fff;border:1px solid #ccc;padding:4px 12px;border-radius:4px;cursor:pointer"
      onclick="(function(){{
        var data = atob('{svg_b64}');
        var blob = new Blob([data], {{type:'image/svg+xml'}});
        var url  = URL.createObjectURL(blob);
        var img  = new Image();
        img.onload = function(){{
          var c = document.createElement('canvas');
          c.width  = img.naturalWidth  * {scale};
          c.height = img.naturalHeight * {scale};
          var ctx = c.getContext('2d');
          ctx.scale({scale},{scale});
          ctx.drawImage(img,0,0);
          var a = document.createElement('a');
          a.download = '{filename}.png';
          a.href = c.toDataURL('image/png');
          document.body.appendChild(a); a.click(); document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }};
        img.src = url;
      }})()">PNG 다운로드</button>
    """
    st.markdown(html, unsafe_allow_html=True)


if st.session_state.hands:
    color_hex = COLORS[st.session_state.color]
    bg_hex    = BG_COLORS[st.session_state.color]

    hands_config = [
        {"value": h["value"], "variant": h["variant"],
         "color": color_hex, "flip": h["flip"]}
        for h in st.session_state.hands
    ]

    svg_result = build_svg(hands_config, bg_color=bg_hex)
    filename   = make_filename(st.session_state.hands)

    st.subheader("미리보기")
    st.markdown(svg_result, unsafe_allow_html=True)

    dl_col1, dl_col2 = st.columns([1, 1])
    with dl_col1:
        st.download_button(
            "SVG 다운로드",
            data=svg_result,
            file_name=f"{filename}.svg",
            mime="image/svg+xml",
        )
    with dl_col2:
        png_download_button(svg_result, filename)
else:
    st.info("숫자를 입력하거나 손을 추가하세요.")
```

- [ ] **Step 2: 앱 실행 → 전체 흐름 확인**

```bash
streamlit run app.py
```

1. "숫자 입력" 탭에서 7 입력 → 생성 클릭
2. 손 2개 표시 확인 (오른손 5, 왼손 2)
3. 색상 "따미" 선택 → 썸네일 색상 변경 확인
4. 방향 토글 → 손 방향 변경 확인
5. SVG 미리보기 표시 확인
6. "SVG 다운로드" 클릭 → 파일 다운로드 확인
7. "PNG 다운로드" 클릭 → PNG 파일 다운로드 확인

- [ ] **Step 3: 최종 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: 모든 테스트 passed

- [ ] **Step 4: 최종 커밋**

```bash
git add app.py
git commit -m "feat: preview + SVG/PNG export — feature complete"
```

---

## SVG 파일 수령 후 체크리스트

실제 SVG 파일을 받으면 아래 두 항목 확인:

1. **BASE_HAND_COLOR 확정** (`finger_svg.py` 상단)  
   SVG 파일을 열어 손 몸통의 fill 색상 확인 → `BASE_HAND_COLOR = "#실제값"` 으로 수정

2. **flip 방향 확정** (`finger_svg.py` 상단 주석)  
   SVG가 왼손 기준이면 현재 로직 그대로 (오른손=flip).  
   SVG가 오른손 기준이면 `default_hand_directions`의 `i % 2 == 0` 을 `i % 2 != 0` 으로 변경.
