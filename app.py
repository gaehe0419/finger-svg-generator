# app.py
import base64
import datetime
import streamlit as st

from finger_svg import (
    COLORS, SHADOW_COLORS, BG_COLORS, DEFAULT_COLOR, HAND_GAP,
    get_variants, decompose, default_hand_directions, build_svg,
)


@st.cache_data(show_spinner=False)
def cached_thumb_svg(value: int, variant: str, color: str, shadow: str,
                     flip: bool, bg_color: str = "#ffffff") -> str:
    """썸네일용 SVG를 캐싱하여 매 rerun 마다 재생성을 방지한다."""
    return build_svg(
        [{"value": value, "variant": variant,
          "color": color, "shadow": shadow, "flip": flip}],
        bg_color=bg_color,
    )

st.set_page_config(page_title="손가락 이미지 생성기", page_icon="✌️", layout="wide")
st.title("✌️ 손가락 이미지 생성기")

# ── 세션 상태 초기화 ──────────────────────────────────────────
if "color" not in st.session_state:
    st.session_state.color = DEFAULT_COLOR
if "hands" not in st.session_state:
    _init_vals = decompose(7)
    _init_flips = default_hand_directions(len(_init_vals))
    st.session_state.hands = [
        {"value": v, "flip": f, "variant": get_variants(v)[0]}
        for v, f in zip(_init_vals, _init_flips)
    ]
if "last_num" not in st.session_state:
    st.session_state.last_num = 7
if "hand_gap_slider" not in st.session_state:
    st.session_state["hand_gap_slider"] = HAND_GAP

# ── CSS 전체 주입 ─────────────────────────────────────────────
def inject_css():
    css = "<style>"

    # 전체 최대 너비 960px + 가운데 정렬
    css += (
        "[data-testid='stMainBlockContainer'] {"
        "  max-width:960px!important;"
        "  margin-left:auto!important;"
        "  margin-right:auto!important;"
        "}"
    )

    # 최상위 섹션 간격 40px
    css += (
        "[data-testid='stMainBlockContainer'] > [data-testid='stVerticalBlock'] {"
        "  gap:40px!important; }"
    )

    # 숫자 입력 크게
    css += (
        "[data-testid='stNumberInput'] input {"
        "  font-size:22px!important; height:52px!important;"
        "  text-align:center!important; }"
    )

    # 색상 버튼 행
    css += (
        ".stHorizontalBlock:has(.st-key-color_0) {"
        "  gap:8px!important; flex-wrap:wrap!important; }"
        ".stHorizontalBlock:has(.st-key-color_0) > [data-testid='stColumn'] {"
        "  flex:0 0 auto!important; width:auto!important; min-width:0!important; }"
        ".stHorizontalBlock:has(.st-key-color_0) button { width:80px!important; }"
    )

    # 색상 버튼 개별 스타일
    _TEXT_COLOR = {
        "피부색": "#555555", "흰색": "#2F424E",
        "깨다":   "#ffffff", "챌리": "#555555", "따미": "#ffffff",
    }
    for _i, (_name, _hex) in enumerate(COLORS.items()):
        _sel     = st.session_state.color == _name
        _shadow  = SHADOW_COLORS[_name]
        _border  = f"2px solid {_shadow}" if _sel else "1.5px solid #dddddd"
        _tc      = _TEXT_COLOR[_name]
        _opacity = "1" if _sel else "0.75"
        css += (
            f".st-key-color_{_i} button {{"
            f"background-color:{_hex}!important;border:{_border}!important;"
            f"color:{_tc}!important;font-weight:700!important;"
            f"opacity:{_opacity}!important;"
            f"min-height:44px!important;padding:8px 0!important;border-radius:50px!important;}}"
        )

    # 방향 세그먼트 버튼 — 형태 (최대 4손)
    for i in range(4):
        css += (
            f".st-key-dir_{i}_L button {{"
            f"border-radius:6px 0 0 6px!important; border-right:none!important;"
            f"padding:5px 14px!important; font-size:13px!important;}}"
        )
        css += (
            f".st-key-dir_{i}_R button {{"
            f"border-radius:0 6px 6px 0!important;"
            f"padding:5px 14px!important; font-size:13px!important;}}"
        )
    # 방향 버튼 활성 상태 + 비활성 (흰 배경 유지, 글자색만 흐리게)
    css += (
        "[class*='st-key-dir_'] [data-testid='stBaseButton-primary'] {"
        "background:#222!important; border-color:#222!important; color:#fff!important;}"
        "[class*='st-key-dir_'] [data-testid='stBaseButton-secondary'] {"
        "background:#fff!important; border-color:#ddd!important;"
        "color:rgba(85,85,85,0.3)!important;}"
    )
    # 방향 버튼 행: gap 0, 직접 부모 컬럼 패딩 제거 (direct-child 셀렉터로 정밀 타깃)
    for i in range(4):
        css += (
            f"[data-testid='stHorizontalBlock']:has(>[data-testid='stColumn']"
            f">[data-testid='stVerticalBlock']>.st-key-dir_{i}_L){{gap:0!important;}}"
            f"[data-testid='stColumn']:has(>[data-testid='stVerticalBlock']>.st-key-dir_{i}_L),"
            f"[data-testid='stColumn']:has(>[data-testid='stVerticalBlock']>.st-key-dir_{i}_R){{"
            f"padding:0!important;flex:0 0 auto!important;width:auto!important;}}"
        )

    # 변형 썸네일 컬럼 간격 16px
    css += (
        "[data-testid='stHorizontalBlock']:has([class*='st-key-var_'])"
        ":not(:has(.st-key-dir_0_L)){"
        "gap:16px!important;}"
    )

    # 컨트롤 영역 (outer hand_cols) — 회색 박스 + 왼쪽 정렬
    # :not(...)으로 inner direction-button 행을 제외하고 outer 만 타깃
    css += (
        "[data-testid='stHorizontalBlock']:has(.st-key-dir_0_L)"
        ":not([data-testid='stHorizontalBlock']:has(>[data-testid='stColumn']"
        ">[data-testid='stVerticalBlock']>.st-key-dir_0_L)){"
        "background:#f0f2f6!important;border-radius:12px!important;"
        "padding:20px 20px 40px 20px!important;gap:24px!important;"
        "justify-content:flex-start!important;align-items:flex-start!important;}"
        # 각 손 컬럼: 자동 너비, 왼쪽 정렬
        "[data-testid='stHorizontalBlock']:has(.st-key-dir_0_L)"
        ":not([data-testid='stHorizontalBlock']:has(>[data-testid='stColumn']"
        ">[data-testid='stVerticalBlock']>.st-key-dir_0_L))"
        ">[data-testid='stColumn']{"
        "flex:0 0 auto!important;width:auto!important;min-width:150px!important;}"
    )

    # 저장 버튼: 높이·텍스트 크게
    css += (
        ".st-key-dl_svg [data-testid='stBaseButton-primary'] {"
        "  min-height:56px!important; font-size:18px!important; }"
    )

    # 호버 이펙트
    css += (
        # 색상 버튼 hover
        ".stHorizontalBlock:has(.st-key-color_0) button{"
        "transition:opacity 0.15s,filter 0.15s!important;}"
        ".stHorizontalBlock:has(.st-key-color_0) button:hover{"
        "opacity:1!important;filter:brightness(0.93)!important;}"
        # 방향 버튼 transition
        "[class*='st-key-dir_'] button{"
        "transition:color 0.15s,background 0.15s,border-color 0.15s!important;}"
        "[class*='st-key-dir_'] [data-testid='stBaseButton-secondary']:hover{"
        "color:rgba(85,85,85,0.65)!important;border-color:#bbb!important;}"
        "[class*='st-key-dir_'] [data-testid='stBaseButton-primary']:hover{"
        "background:#3a3a3a!important;}"
        # SVG 다운로드 버튼 hover
        ".st-key-dl_svg button{"
        "transition:filter 0.15s!important;}"
        ".st-key-dl_svg button:hover{"
        "filter:brightness(1.15)!important;}"
        # PNG 다운로드 버튼 hover
        "button.dl-png-btn{"
        "transition:background 0.15s!important;}"
        "button.dl-png-btn:hover{"
        "background:#f5f5f5!important;}"
        # 변형 버튼 hover (background-image 썸네일 버튼)
        "[class*='st-key-var_'] button{"
        "transition:opacity 0.15s!important;}"
        "[class*='st-key-var_'] button:hover{opacity:0.75!important;}"
    )

    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)


inject_css()


# ── 색상 버튼 ─────────────────────────────────────────────────
color_cols = st.columns(len(COLORS))
for i, (name, _) in enumerate(COLORS.items()):
    with color_cols[i]:
        if st.button(name, key=f"color_{i}"):
            st.session_state.color = name
            st.rerun()

# ── 숫자 입력 ─────────────────────────────────────────────────
_n = int(st.number_input(
    "총 손가락 수", min_value=0, max_value=20,
    value=st.session_state.last_num, step=1,
    key="num_input_widget",
    help="최대 20개까지 입력할 수 있습니다.",
))
if _n != st.session_state.last_num:
    st.session_state.last_num = _n
    _vals   = decompose(_n)
    _flips  = default_hand_directions(len(_vals))
    _prev   = st.session_state.hands  # 기존 손 설정 보존
    st.session_state.hands = [
        {
            "value":   v,
            "flip":    _prev[idx]["flip"]    if idx < len(_prev) else f,
            "variant": _prev[idx]["variant"] if idx < len(_prev)
                       and _prev[idx]["value"] == v else get_variants(v)[0],
        }
        for idx, (v, f) in enumerate(zip(_vals, _flips))
    ]
    st.rerun()


# ── 미리보기 + 컨트롤 ─────────────────────────────────────────
def make_filename(hands: list[dict], color: str) -> str:
    today  = datetime.date.today().strftime("%Y%m%d")
    values = "-".join(str(h["value"]) for h in hands)
    return f"finger_{today}_{values}_{color}"


if st.session_state.hands:
    color_hex  = COLORS[st.session_state.color]
    bg_hex     = BG_COLORS[st.session_state.color]
    shadow_hex = SHADOW_COLORS[st.session_state.color]
    hand_gap   = int(st.session_state.get("hand_gap_slider", HAND_GAP))

    hands_config = [
        {"value": h["value"], "variant": h["variant"],
         "color": color_hex, "shadow": shadow_hex, "flip": h["flip"]}
        for h in st.session_state.hands
    ]

    try:
        svg_result = build_svg(hands_config, bg_color=bg_hex, hand_gap=hand_gap)
    except FileNotFoundError as e:
        st.error(f"SVG 파일을 찾을 수 없습니다: {e}")
        st.stop()

    filename = make_filename(st.session_state.hands, st.session_state.color)
    svg_b64   = base64.b64encode(svg_result.encode()).decode()

    # 다운로드용 SVG: 흰색 손은 배경 투명, 나머지는 흰색
    _dl_bg     = "none" if st.session_state.color == "흰색" else "#FFFFFF"
    svg_download = build_svg(hands_config, bg_color=_dl_bg, hand_gap=hand_gap)
    dl_b64     = base64.b64encode(svg_download.encode()).decode()

    # ── 이미지 영역 ─────────────────────────────────────────
    _preview_border = (
        f"1.5px solid {SHADOW_COLORS[st.session_state.color]}"
        if bg_hex != "#FFFFFF" else "1.5px solid #d0d0d0"
    )
    st.markdown(
        f'<div style="border:{_preview_border};border-radius:12px;'
        f'padding:24px;background:{bg_hex};height:300px;'
        f'display:flex;align-items:center;justify-content:center;'
        f'width:100%;box-sizing:border-box;">'
        f'<img src="data:image/svg+xml;base64,{svg_b64}"'
        f' style="max-width:100%;max-height:100%;height:auto;" />'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── 컨트롤 영역 ─────────────────────────────────────────
    hand_cols = st.columns(len(st.session_state.hands))
    for i, hand in enumerate(st.session_state.hands):
        with hand_cols[i]:
            st.markdown(
                f"<p style='font-size:11px;font-weight:700;color:#999;"
                f"letter-spacing:.5px;text-transform:uppercase;margin:0 0 8px 0;'>"
                f"{i+1}번손</p>",
                unsafe_allow_html=True,
            )
            # 방향 세그먼트 버튼
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("왼손", key=f"dir_{i}_L",
                             type="primary" if not hand["flip"] else "secondary"):
                    st.session_state.hands[i]["flip"] = False
                    st.rerun()
            with dc2:
                if st.button("오른손", key=f"dir_{i}_R",
                             type="primary" if hand["flip"] else "secondary"):
                    st.session_state.hands[i]["flip"] = True
                    st.rerun()

            # 변형 썸네일 — 버튼 자체를 썸네일로 표시 (background-image CSS)
            variants = get_variants(hand["value"])
            if len(variants) > 1:
                thumb_cols = st.columns(len(variants))
                for j, variant in enumerate(variants):
                    with thumb_cols[j]:
                        thumb_svg = cached_thumb_svg(
                            hand["value"], variant,
                            color_hex, shadow_hex, hand["flip"],
                            bg_color=bg_hex,
                        )
                        tb64        = base64.b64encode(thumb_svg.encode()).decode()
                        _sel_border = "2px solid #ff4444" if bg_hex != "#FFFFFF" else "2px solid #333"
                        _def_border = "1px solid #4a5f6e" if bg_hex != "#FFFFFF" else "1px solid #ddd"
                        border      = _sel_border if variant == hand["variant"] else _def_border
                        # 버튼을 썸네일로 변환: background-image로 SVG 표시
                        st.markdown(
                            f'<style>'
                            f'.st-key-var_{i}_{j} button{{'
                            f'background-image:url("data:image/svg+xml;base64,{tb64}")!important;'
                            f'background-size:80% auto!important;'
                            f'background-repeat:no-repeat!important;'
                            f'background-position:center!important;'
                            f'background-color:{bg_hex}!important;'
                            f'width:64px!important;height:72px!important;min-height:72px!important;'
                            f'border:{border}!important;border-radius:6px!important;'
                            f'padding:0!important;font-size:0!important;color:transparent!important;'
                            f'cursor:pointer!important;display:block!important;margin:0 auto!important;}}'
                            f'</style>',
                            unsafe_allow_html=True,
                        )
                        if st.button(
                            "●",
                            key=f"var_{i}_{j}",
                            type="primary" if variant == hand["variant"] else "secondary",
                        ):
                            st.session_state.hands[i]["variant"] = variant
                            st.rerun()

    # ── 손 사이 간격 슬라이더 ────────────────────────────────
    if len(st.session_state.hands) > 1:
        st.slider(
            "손 사이 간격", min_value=0, max_value=120, step=4,
            key="hand_gap_slider",
        )

    # ── 다운로드 ─────────────────────────────────────────────
    _png_id = "dl_png_btn"
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "↓ SVG 저장",
            data=svg_download,
            file_name=f"{filename}.svg",
            mime="image/svg+xml",
            type="primary",
            use_container_width=True,
            key="dl_svg",
        )
    with dl_col2:
        st.markdown(
            f'<button id="{_png_id}" class="dl-png-btn"'
            f' style="width:100%;background:#fff;'
            f' border:1px solid rgba(49,51,63,.2);'
            f' padding:0.45rem 1rem;border-radius:0.5rem;cursor:pointer;'
            f' font-size:1.125rem;font-weight:400;color:#262730;line-height:1.6;'
            f' display:inline-flex;align-items:center;justify-content:center;'
            f' min-height:3.5rem;"'
            f' onclick="(function(){{'
            f'var img=new Image();'
            f'img.onload=function(){{'
            f'var c=document.createElement(\'canvas\');'
            f'var w=img.naturalWidth||img.width||300;'
            f'var h=img.naturalHeight||img.height||300;'
            f'c.width=w*2;c.height=h*2;'
            f'var ctx=c.getContext(\'2d\');ctx.scale(2,2);ctx.drawImage(img,0,0);'
            f'var a=document.createElement(\'a\');'
            f'a.download=\'{filename}.png\';'
            f'a.href=c.toDataURL(\'image/png\');'
            f'a.style.display=\'none\';'
            f'document.body.appendChild(a);a.click();'
            f'setTimeout(function(){{document.body.removeChild(a);}},100);}};'
            f'img.onerror=function(){{alert(\'PNG 저장 실패.\\nSVG로 저장해 주세요.\');}};'
            f'img.src=\'data:image/svg+xml;base64,{dl_b64}\';}})()">↓ PNG 저장</button>',
            unsafe_allow_html=True,
        )
