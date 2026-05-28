# app.py
import base64
import datetime
import streamlit as st

from finger_svg import (
    COLORS, SHADOW_COLORS, BG_COLORS, DEFAULT_COLOR,
    get_variants, decompose, default_hand_directions, build_svg,
)

st.set_page_config(page_title="손가락 이미지 생성기", layout="wide")
st.title("손가락 이미지 생성기")

# ── 세션 상태 초기화 ──────────────────────────────────────────
if "color" not in st.session_state:
    st.session_state.color = DEFAULT_COLOR
if "hands" not in st.session_state:
    # list of {"value": int, "flip": bool, "variant": str}
    st.session_state.hands = []


# ── 좌측 / 우측 분할 ──────────────────────────────────────────
col_left, col_right = st.columns([1, 2], gap="medium")

# ── [좌측] 색상 선택 ──────────────────────────────────────────
with col_left:
    st.subheader("색상")

    # 색상 버튼 CSS
    # 버튼 키를 color_0 ~ color_4 (인덱스)로 지정해야 st-key-color_0 등 고유 클래스가 생성됨.
    _TEXT_COLOR = {
        "피부색": "#555555",
        "흰색":   "#2F424E",
        "깨다":   "#ffffff",
        "챌리":   "#555555",
        "따미":   "#ffffff",
    }
    _css = "<style>"
    # 버튼 행: gap 8px, 컬럼이 flex:1 균등분할되지 않도록 auto로 override
    _css += (
        ".stHorizontalBlock:has(.st-key-color_0) {"
        "  gap: 8px !important; flex-wrap: wrap !important; }"
        ".stHorizontalBlock:has(.st-key-color_0) > [data-testid='stColumn'] {"
        "  flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }"
        # 모든 색상 버튼 공통 크기 — 가장 긴 텍스트(피부색 3자)에 맞춰 고정
        ".stHorizontalBlock:has(.st-key-color_0) button {"
        "  width: 80px !important; }"
    )
    for _i, (_name, _hex) in enumerate(COLORS.items()):
        _sel    = st.session_state.color == _name
        _shadow = SHADOW_COLORS[_name]                          # 활성 테두리 = shadow color
        _border = f"2px solid {_shadow}" if _sel else "1.5px solid #dddddd"
        _tc     = _TEXT_COLOR[_name]
        _css += (
            f'.st-key-color_{_i} button {{'
            f'background-color:{_hex}!important;border:{_border}!important;'
            f'color:{_tc}!important;font-weight:700!important;'
            f'min-height:44px!important;'
            f'padding:8px 0!important;border-radius:50px!important;}}'  # padding 좌우 0 (width 고정이므로)
        )
    _css += "</style>"
    st.markdown(_css, unsafe_allow_html=True)

    color_cols = st.columns(len(COLORS))
    for i, (name, hex_val) in enumerate(COLORS.items()):
        with color_cols[i]:
            if st.button(name, key=f"color_{i}"):               # use_container_width 제거
                st.session_state.color = name
                st.rerun()

    st.divider()

    # ── [좌측] 입력 방식 탭 ───────────────────────────────────
    st.subheader("입력 방식")
    tab_num, tab_manual = st.tabs(["숫자 입력", "수동 조합"])

    # ── 숫자 입력 모드 ────────────────────────────────────────
    with tab_num:
        num_input = st.number_input("숫자 (0~20)", min_value=0, max_value=20, value=7, step=1)

        if st.button("생성", key="btn_generate_num"):
            values = decompose(int(num_input))
            flips = default_hand_directions(len(values))
            variants = [get_variants(v)[0] for v in values]
            st.session_state.hands = [
                {"value": v, "flip": f, "variant": var}
                for v, f, var in zip(values, flips, variants)
            ]
            st.rerun()

    # ── 수동 조합 모드 ────────────────────────────────────────
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
                variants = get_variants(new_val)
                st.session_state.hands[i]["value"] = new_val
                st.session_state.hands[i]["variant"] = variants[0]
                st.rerun()

    # ── [좌측] 손별 설정 (방향 + 변형) ────────────────────────
    if st.session_state.hands:
        st.divider()
        st.subheader("손 설정")
        color_hex = COLORS[st.session_state.color]

        for i, hand in enumerate(st.session_state.hands):
            st.markdown(f"**{i+1}번 손**")

            # 방향 토글 (ON = 오른손, OFF = 왼손)
            new_flip = st.toggle("오른손", value=hand["flip"], key=f"flip_{i}")
            if new_flip != hand["flip"]:
                st.session_state.hands[i]["flip"] = new_flip
                st.rerun()

            # 변형 썸네일 (2개 이상일 때만 표시)
            variants = get_variants(hand["value"])
            if len(variants) > 1:
                st.caption("변형 선택")
                thumb_cols = st.columns(len(variants))
                for j, variant in enumerate(variants):
                    with thumb_cols[j]:
                        thumb_svg = build_svg(
                            [{"value": hand["value"], "variant": variant,
                              "color": color_hex,
                              "shadow": SHADOW_COLORS[st.session_state.color],
                              "flip": hand["flip"]}],
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

            st.divider()


# ── [우측] 미리보기 & 내보내기 ──────────────────────────────
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


with col_right:
    if st.session_state.hands:
        color_hex = COLORS[st.session_state.color]
        bg_hex = BG_COLORS[st.session_state.color]

        shadow_hex = SHADOW_COLORS[st.session_state.color]
        hands_config = [
            {"value": h["value"], "variant": h["variant"],
             "color": color_hex, "shadow": shadow_hex, "flip": h["flip"]}
            for h in st.session_state.hands
        ]

        try:
            svg_result = build_svg(hands_config, bg_color=bg_hex)
        except FileNotFoundError as e:
            st.error(f"SVG 파일을 찾을 수 없습니다: {e}\ncomponents/ 폴더에 해당 파일이 있는지 확인하세요.")
            st.stop()
        filename = make_filename(st.session_state.hands)

        st.subheader("미리보기")
        svg_b64 = base64.b64encode(svg_result.encode("utf-8")).decode()
        st.markdown(
            f'<div style="border:1.5px solid #d0d0d0;border-radius:12px;padding:24px;'
            f'background:#ffffff;display:inline-block;width:100%;box-sizing:border-box">'
            f'<img src="data:image/svg+xml;base64,{svg_b64}" style="max-width:100%;height:auto;display:block"/>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.subheader("다운로드")
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
        st.info("좌측에서 숫자를 입력하거나 손을 추가하세요.")
