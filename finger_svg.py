# finger_svg.py
import base64
import os
import re
import glob
import xml.etree.ElementTree as ET
from functools import lru_cache

ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

SVG_NS = "http://www.w3.org/2000/svg"
COMPONENTS_DIR = "components"
BASE_HAND_COLOR   = "#FFC6BD"  # 손 메인 색상 (cls-1)
BASE_SHADOW_COLOR = "#f9897a"  # 손 그림자 색상 (cls-2)
HAND_GAP   = 40  # 손 사이 간격 (px)
CANVAS_PAD = 16  # 잘림 방지용 캔버스 여백 (px)

COLORS = {
    "피부색": "#FFC6BD",
    "흰색":   "#FFFFFF",
    "깨다":   "#FF6666",
    "챌리":   "#FFDC0B",
    "따미":   "#26C9CB",
}

SHADOW_COLORS = {
    "피부색": "#f9897a",
    "흰색":   "#b3b3b3",
    "깨다":   "#d54141",
    "챌리":   "#edaf00",
    "따미":   "#008f8b",
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


def apply_shadow(svg_str: str, shadow_color: str) -> str:
    pattern = re.compile(re.escape(BASE_SHADOW_COLOR), re.IGNORECASE)
    return pattern.sub(shadow_color, svg_str)


def apply_flip(svg_str: str) -> str:
    """Flip SVG horizontally by wrapping children in a <g> with scale(-1,1) and translate."""
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
    """Decompose a number into hands (max 5 fingers per hand). n must be >= 0."""
    if n < 0:
        raise ValueError(f"decompose expects n >= 0, got {n}")
    if n == 0:
        return [0]
    hands, remaining = [], n
    while remaining > 0:
        hands.append(min(5, remaining))
        remaining -= 5
    return hands


def default_hand_directions(count: int) -> list[bool]:
    """Generate default hand directions.
    1손  → [True]           (오른손)
    2손+ → [False, True, False, True, ...]  (왼→오른→왼→오른...)
    """
    if count == 1:
        return [True]
    return [i % 2 == 1 for i in range(count)]


def build_svg(
    hands_config: list[dict],
    bg_color: str = "#FFFFFF",
    components_dir: str = COMPONENTS_DIR,
    hand_gap: int = HAND_GAP,
) -> str:
    """
    Assemble a single SVG from one or more hand configs placed side by side.
    hands_config: list of {"value": int, "variant": str, "color": str, "flip": bool}
    Returns SVG string.
    """
    if not hands_config:
        root = ET.Element(f"{{{SVG_NS}}}svg")
        root.set("width", "100")
        root.set("height", "150")
        bg = ET.SubElement(root, f"{{{SVG_NS}}}rect")
        bg.set("width", "100")
        bg.set("height", "150")
        bg.set("fill", bg_color)
        return ET.tostring(root, encoding="unicode")

    processed = []
    for cfg in hands_config:
        path = os.path.join(components_dir, f"hand_{cfg['value']}_{cfg['variant']}.svg")
        try:
            svg_str = load_svg(path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Hand SVG not found: value={cfg['value']}, variant={cfg['variant']} "
                f"(expected {path})"
            ) from None
        svg_str = apply_color(svg_str, cfg.get("color", COLORS[DEFAULT_COLOR]))
        if cfg.get("shadow"):
            svg_str = apply_shadow(svg_str, cfg["shadow"])
        if cfg.get("flip", False):
            svg_str = apply_flip(svg_str)
        processed.append(svg_str)

    # Compute per-hand dimensions (width + height for every hand)
    dims = [get_svg_dimensions(s) for s in processed]
    widths  = [d[0] for d in dims]
    heights = [d[1] for d in dims]
    total_w = sum(widths) + hand_gap * (len(processed) - 1)
    max_h   = max(heights)

    # 잘림 방지 패딩 포함 캔버스
    canvas_w = total_w + CANVAS_PAD * 2
    canvas_h = max_h  + CANVAS_PAD * 2

    root = ET.Element(f"{{{SVG_NS}}}svg")
    root.set("viewBox", f"0 0 {canvas_w:.2f} {canvas_h:.2f}")
    root.set("width",   f"{canvas_w:.2f}")
    root.set("height",  f"{canvas_h:.2f}")

    bg = ET.SubElement(root, f"{{{SVG_NS}}}rect")
    bg.set("width",  f"{canvas_w:.2f}")
    bg.set("height", f"{canvas_h:.2f}")
    bg.set("fill", bg_color)

    # 각 손 SVG를 <image> 요소로 임베드 — CSS 클래스명 충돌 완전 차단
    x_offset = float(CANVAS_PAD)
    for svg_str, w, h in zip(processed, widths, heights):
        b64 = base64.b64encode(svg_str.encode("utf-8")).decode("ascii")
        img_elem = ET.SubElement(root, f"{{{SVG_NS}}}image")
        img_elem.set("x",      f"{x_offset:.2f}")
        img_elem.set("y",      f"{CANVAS_PAD + max_h - h:.2f}")  # 여백 + 아래 정렬
        img_elem.set("width",  f"{w:.2f}")
        img_elem.set("height", f"{h:.2f}")
        img_elem.set("href",   f"data:image/svg+xml;base64,{b64}")
        x_offset += w + hand_gap

    return ET.tostring(root, encoding="unicode")
