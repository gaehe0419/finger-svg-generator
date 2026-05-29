# 손가락 이미지 생성기

수 세기 교육 및 수학 문제 출제용 손가락 SVG/PNG 이미지 생성 도구.

**배포 URL:** https://finger-svg-generator-n8nqi3wtcprqmh2qvbrrrg.streamlit.app/

---

## 기능

| 기능 | 설명 |
|------|------|
| 숫자 입력 | 0~20 입력 시 손 자동 분해 (손당 최대 5개) |
| 색상 선택 | 피부색 / 흰색 / 깨다 / 챌리 / 따미 — 배경색 자동 연동 |
| 손 방향 | 손별 왼손 / 오른손 독립 설정 |
| 변형 선택 | 같은 손가락 수의 다른 모양을 썸네일로 선택 |
| 손 사이 간격 | 슬라이더로 0~120px 조정 |
| SVG 저장 | 색상 배경 제외한 투명/흰색 배경으로 저장 |
| PNG 저장 | 2× 해상도 (Canvas API 변환) |

---

## 파일 구조

```
finger-svg-generator/
├── app.py                  # Streamlit UI
├── finger_svg.py           # SVG 로직 (색상·flip·조립)
├── requirements.txt
├── components/
│   ├── hand_0_a.svg        # 주먹 (변형 없음)
│   ├── hand_1_a/b/c.svg    # 1개 — 변형 3종
│   ├── hand_2_a/b/c.svg    # 2개 — 변형 3종
│   ├── hand_3_a/b/c.svg    # 3개 — 변형 3종
│   ├── hand_4_a/b.svg      # 4개 — 변형 2종
│   └── hand_5_a.svg        # 전부 펼침 (변형 없음)
└── tests/
    ├── conftest.py
    └── test_finger_svg.py
```

### SVG 파일 명명 규칙

- `hand_{손가락수}_{변형}.svg`
- 손가락수: 0~5
- 변형: `a`, `b`, `c` (알파벳순, `a`가 기본값)
- 파일을 추가하면 코드 수정 없이 자동 감지됨

---

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 색상 시스템

| 이름 | 손 색상 | 그림자 색상 | 미리보기 배경 |
|------|--------|-----------|-------------|
| 피부색 | `#FFC6BD` | `#f9897a` | `#FFFFFF` |
| 흰색   | `#FFFFFF` | `#b3b3b3` | `#2F424E` |
| 깨다   | `#FF6666` | `#d54141` | `#FFFFFF` |
| 챌리   | `#FFDC0B` | `#edaf00` | `#FFFFFF` |
| 따미   | `#26C9CB` | `#008f8b` | `#FFFFFF` |

---

## 숫자 분해 규칙

| 입력값 | 손 | 각 손 값 예시 |
|-------|---|-------------|
| 0~5   | 1개 | `[N]` |
| 6~10  | 2개 | `[5, N-5]` |
| 11~15 | 3개 | `[5, 5, N-10]` |
| 16~20 | 4개 | `[5, 5, 5, N-15]` |

### 손 방향 기본값

| 손 번호 | 기본 방향 |
|--------|---------|
| 1번 (1손만 있을 때) | 오른손 |
| 1번 (2손 이상) | 왼손 |
| 2번 | 오른손 |
| 3번 | 왼손 |
| 4번 | 오른손 |

---

## 핵심 로직 (finger_svg.py)

```python
decompose(n)          # 숫자 → 손 값 리스트   ex) decompose(13) → [5,5,3]
get_variants(n)       # 파일 자동 감지 변형 목록  ex) get_variants(2) → ['a','b','c']
apply_color(svg, c)   # BASE_HAND_COLOR → c 치환 (case-insensitive)
apply_shadow(svg, c)  # BASE_SHADOW_COLOR → c 치환
apply_flip(svg)       # scale(-1,1) + translate 래핑
build_svg(configs, bg_color, hand_gap)  # 손 목록 → 최종 SVG
```

`build_svg`는 각 손 SVG를 `<image href="data:image/svg+xml;base64,...">` 로 임베드하여 CSS 클래스 충돌을 완전 차단한다.

---

## 버전

| 버전 | 날짜 | 커밋 | 내용 |
|------|------|------|------|
| v1.0 | 2026-05-29 | `2df7443` | 1차 완성 — 전체 기능 구현 및 배포 |
