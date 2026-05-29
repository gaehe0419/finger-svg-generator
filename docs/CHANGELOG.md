# Changelog

## v1.0 — 2026-05-29

**커밋:** `2df7443`  
**1차 완성 — 전체 기능 구현 및 Streamlit Cloud 배포**

### 구현 기능

- 숫자 입력 (0~20) → 자동 손 분해
- 색상 5종 선택 (피부색 / 흰색 / 깨다 / 챌리 / 따미) + 배경색 자동 연동
- 손별 방향 (왼손 / 오른손) 독립 설정
- 변형 썸네일 선택 (background-image CSS 방식, 실제 클릭 작동)
- 손 사이 간격 슬라이더
- SVG / PNG 저장 (PNG는 2× Canvas API 방식)
- 실시간 미리보기

### 주요 버그 수정

- **CSS class 충돌**: 여러 손 SVG를 중첩 시 `.cls-1` 등 전역 클래스 충돌 →
  `<image href="data:image/svg+xml;base64,...">` 임베딩으로 해결
- **썸네일 클릭 불작동**: `st.markdown`의 `onclick` 속성이 Streamlit에 의해 sanitize됨 →
  `st.button`에 `background-image` CSS를 직접 주입하는 방식으로 교체
- **그림자 색상 미적용**: `BASE_SHADOW_COLOR` 및 `apply_shadow()` 추가, `build_svg`에서 shadow 전달

### 알려진 제한

- PNG 저장: 브라우저 Canvas API 사용으로 일부 브라우저에서 실패 가능 (SVG로 저장 권장)
- 최대 20개 손가락 (4손) 지원
