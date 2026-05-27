# app.py
import base64          # used in Task 10: PNG download via Canvas API
import datetime        # used in Task 10: auto-generated filename
import streamlit as st

from finger_svg import (
    COLORS, BG_COLORS, DEFAULT_COLOR,
    get_variants, decompose, default_hand_directions, build_svg,
)
# COLORS  = {"피부색": "#FFC6BD", "흰색": "#FFFFFF", "깨다": "#FF6666", "챌리": "#FFDC0B", "따미": "#26C9CB"}
# BG_COLORS = 흰색 → "#2F424E", 나머지 → "#FFFFFF"

st.set_page_config(page_title="손가락 이미지 생성기", layout="wide")
st.title("손가락 이미지 생성기")

# ── 세션 상태 초기화 ──────────────────────────────────────────
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

# ── 손별 설정 (방향 + 변형) ───────────────────────────────────
if st.session_state.hands:
    st.subheader("손 설정")
    hand_cols = st.columns(len(st.session_state.hands))
    color_hex = COLORS[st.session_state.color]  # global color — same for all hands

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
                for j, variant in enumerate(variants):
                    with thumb_cols[j]:
                        # 썸네일용 단일 손 SVG (60x90 스케일)
                        thumb_svg = build_svg(
                            [{"value": hand["value"], "variant": variant,
                              "color": color_hex, "flip": hand["flip"]}],
                            bg_color="#F5F5F5",
                        )
                        border = "2px solid #333" if variant == hand["variant"] else "1px solid #ddd"
                        thumb_b64 = base64.b64encode(thumb_svg.encode("utf-8")).decode()
                        st.markdown(
                            f'<div style="border:{border};border-radius:4px;padding:2px;max-width:70px;overflow:hidden">'
                            f'<img src="data:image/svg+xml;base64,{thumb_b64}" style="width:100%;height:auto"/>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button(f"{'✓' if variant == hand['variant'] else '  '}", key=f"var_{i}_{j}"):
                            st.session_state.hands[i]["variant"] = variant
                            st.rerun()

st.markdown("---")

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

    try:
        svg_result = build_svg(hands_config, bg_color=bg_hex)
    except FileNotFoundError as e:
        st.error(f"SVG 파일을 찾을 수 없습니다: {e}\ncomponents/ 폴더에 해당 파일이 있는지 확인하세요.")
        st.stop()
    filename   = make_filename(st.session_state.hands)

    st.subheader("미리보기")
    svg_b64 = base64.b64encode(svg_result.encode("utf-8")).decode()
    st.markdown(
        f'<img src="data:image/svg+xml;base64,{svg_b64}" style="max-width:100%;height:auto"/>',
        unsafe_allow_html=True,
    )

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
