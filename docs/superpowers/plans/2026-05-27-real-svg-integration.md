# Real SVG Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 더미 SVG를 실제 손가락 SVG 파일로 교체하고 색상 치환·flip이 정상 동작하는지 검증한다.

**Architecture:** `components/` 폴더에 실제 SVG 파일을 배치하고, `finger_svg.py`의 `BASE_HAND_COLOR`를 실제 fill 색상으로 확정한다. 기존 22개 단위 테스트를 실제 파일로 재검증한 뒤 GitHub에 푸시하면 Streamlit Cloud가 자동 재배포된다.

**Tech Stack:** Python 3.10+, xml.etree.ElementTree, pytest, Streamlit ≥ 1.28

---

## File Map

| 파일 | 변경 내용 |
|------|-----------|
| `components/hand_*.svg` | 더미 파일 → 실제 손가락 SVG로 교체 |
| `finger_svg.py` | `BASE_HAND_COLOR` 값 확정 |
| `tests/conftest.py` | `DUMMY_SVG`의 fill 색상을 실제 `BASE_HAND_COLOR`와 동기화 |

---

## Task 1: SVG 파일 명 확인 및 배치

**Files:**
- Modify: `components/` (더미 파일 교체)

- [ ] **Step 1: 실제 SVG 파일을 `components/` 폴더에 복사**

파일명 규칙: `hand_{숫자}_{변형}.svg`
```
components/
├── hand_0_a.svg
├── hand_1_a.svg
├── hand_1_b.svg   ← 변형 있을 때만
├── hand_2_a.svg
├── hand_2_b.svg
├── hand_2_c.svg
├── hand_3_a.svg
├── hand_4_a.svg
└── hand_5_a.svg
```

최소 필수: `hand_0_a.svg` ~ `hand_5_a.svg` 6개

- [ ] **Step 2: 파일 목록 확인**

```bash
ls components/
```

Expected: `hand_0_a.svg hand_1_a.svg ...` 형태로 출력

- [ ] **Step 3: SVG 파일 열어서 구조 확인**

아무 SVG 파일이나 열어서 아래 항목 체크:
- `<svg>` 태그에 `viewBox` 또는 `width`/`height` 속성 있는지
- 손 몸통(배경) fill 색상이 어떤 hex값인지 메모

```bash
# 첫 20줄만 확인
head -20 components/hand_1_a.svg
```

---

## Task 2: BASE_HAND_COLOR 확정

**Files:**
- Modify: `finger_svg.py` line 13

- [ ] **Step 1: 실제 fill 색상 확인**

Task 1 Step 3에서 메모한 hex값 확인.  
예) 손 몸통 색상이 `#F5C5B8` 이라면 그게 `BASE_HAND_COLOR`.

- [ ] **Step 2: finger_svg.py 수정**

`finger_svg.py` 13번째 줄:
```python
# 변경 전
BASE_HAND_COLOR = "#FFC6BD"  # SVG 파일 수령 후 실제 베이스 fill 색상으로 확정

# 변경 후 (실제 색상으로)
BASE_HAND_COLOR = "#실제hex값"
```

- [ ] **Step 3: 색상이 이미 #FFC6BD 이면 그대로 유지**

SVG 파일의 fill이 정확히 `#FFC6BD`(대소문자 무관)이면 수정 불필요.  
`apply_color`는 `re.IGNORECASE`로 매칭하므로 `#ffc6bd`도 정상 동작.

- [ ] **Step 4: conftest.py DUMMY_SVG fill 동기화**

`BASE_HAND_COLOR`가 `#FFC6BD`가 아니면 `tests/conftest.py`도 수정:

```python
# tests/conftest.py line 10
DUMMY_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="150" viewBox="0 0 100 150"><circle cx="50" cy="75" r="40" fill="#실제hex값"/></svg>'
```

- [ ] **Step 5: 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: `22 passed`  
(색상 관련 테스트 3개 실패 시 → `BASE_HAND_COLOR`와 `DUMMY_SVG` fill이 불일치. Step 2~4 재확인)

---

## Task 3: flip 방향 확정

**Files:**
- Modify: `finger_svg.py` line 90 (필요 시)

- [ ] **Step 1: 앱 실행**

```bash
streamlit run app.py
```

- [ ] **Step 2: 방향 기본값 확인**

숫자 `7` 입력 → 생성 클릭.  
- 1번 손(오른손)이 **엄지가 오른쪽**으로 보이면 → 정상 (flip 적용됨)
- 1번 손이 **엄지가 왼쪽**으로 보이면 → SVG가 이미 오른손 기준

- [ ] **Step 3: SVG가 오른손 기준이면 default_hand_directions 수정**

`finger_svg.py` 90번째 줄:
```python
# 변경 전 (SVG가 왼손 기준일 때 — 기본값)
return [i % 2 == 0 for i in range(count)]

# 변경 후 (SVG가 오른손 기준일 때)
return [i % 2 != 0 for i in range(count)]
```

- [ ] **Step 4: 방향 수정 후 테스트 재실행**

```bash
pytest tests/ -v
```

Expected: `22 passed`

---

## Task 4: 색상 치환 시각 확인

**Files:**
- 없음 (코드 변경 없음, 시각 확인만)

- [ ] **Step 1: 각 색상 선택 후 미리보기 확인**

앱에서 순서대로 선택:
1. **피부색** → 손이 연분홍(#FFC6BD)으로 표시되는지
2. **흰색** → 손이 흰색, 배경이 어두운 남색(#2F424E)으로 표시되는지
3. **깨다** → 손이 빨간색(#FF6666)으로 표시되는지
4. **챌리** → 손이 노란색(#FFDC0B)으로 표시되는지
5. **따미** → 손이 청록색(#26C9CB)으로 표시되는지

- [ ] **Step 2: 색상이 바뀌지 않으면 BASE_HAND_COLOR 재확인**

SVG 파일에서 실제로 사용된 색상 hex값 재확인 후 Task 2 Step 2 반복.

---

## Task 5: 변형(variant) 동작 확인

**Files:**
- 없음 (변형 파일이 있을 때만)

- [ ] **Step 1: 변형 파일이 있는 숫자 테스트**

예) `hand_2_b.svg`가 있으면 숫자 `2` 생성.  
"손 설정" 섹션에 **변형 선택** 썸네일이 나타나는지 확인.

- [ ] **Step 2: 변형 파일이 없으면 이 Task 스킵**

`hand_N_b.svg` 형태의 파일이 없으면 썸네일 섹션이 표시되지 않는 게 정상.

---

## Task 6: SVG/PNG 내보내기 확인

**Files:**
- 없음 (코드 변경 없음, 기능 확인만)

- [ ] **Step 1: SVG 다운로드 테스트**

미리보기 아래 "SVG 다운로드" 클릭 → `finger_YYYYMMDD_5-2.svg` 형태로 저장되는지 확인.

- [ ] **Step 2: SVG 파일 열어서 확인**

다운로드된 SVG를 브라우저에서 열었을 때 손가락 이미지가 정상 표시되는지 확인.

- [ ] **Step 3: PNG 다운로드 테스트**

"PNG 다운로드" 클릭 → `.png` 파일 저장되는지 확인.  
저장된 PNG를 열어서 이미지 확인 (투명 배경이 아닌 색상 배경으로 표시되어야 함).

---

## Task 7: GitHub 푸시 및 Streamlit 재배포

**Files:**
- 모든 변경된 파일

- [ ] **Step 1: 변경 파일 확인**

```bash
git status
git diff finger_svg.py
```

- [ ] **Step 2: 전체 테스트 최종 확인**

```bash
pytest tests/ -v
```

Expected: `22 passed`

- [ ] **Step 3: 커밋**

```bash
git add components/ finger_svg.py tests/conftest.py
git commit -m "feat: replace dummy SVGs with real hand SVG assets"
```

- [ ] **Step 4: GitHub 푸시**

```bash
git push origin master
```

- [ ] **Step 5: Streamlit Cloud 재배포 확인**

https://share.streamlit.io 에서 앱 상태 확인.  
"Running" → 자동 재배포 중 → "Running" 복귀 확인.  
앱 URL 접속 후 실제 SVG 이미지로 정상 작동하는지 최종 확인.
