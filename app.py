# app.py
import base64          # used in Task 10: PNG download via Canvas API
import datetime        # used in Task 10: auto-generated filename
import streamlit as st
import streamlit.components.v1 as components  # used in Task 10: inject PNG download JS

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
# 선택된 색상은 전체 손에 일괄 적용. 흰색 선택 시 미리보기 배경 → BG_COLORS["흰색"] = "#2F424E"
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

with tab_manual:
    col_add, col_remove = st.columns([1, 1])
    with col_add:
        if st.button("＋ 손 추가", key="btn_add_hand"):
            idx = len(st.session_state.hands)
            flip = (idx % 2 == 0)
            st.session_state.hands.append({"value": 0, "flip": flip, "variant": get_variants(0)[0]})
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
            key=f"manual_slider_{i}",
        )
        if new_val != hand["value"]:
            # 값이 바뀌면 변형도 해당 숫자의 첫 번째로 리셋
            variants = get_variants(new_val)
            st.session_state.hands[i]["value"] = new_val
            st.session_state.hands[i]["variant"] = variants[0]
            st.rerun()

st.markdown("---")
