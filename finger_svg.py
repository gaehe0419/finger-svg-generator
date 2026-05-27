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
BASE_HAND_COLOR   = "#FFC6BD"  # 손 메인 색상 (cls-1)
BASE_SHADOW_COLOR = "#f9897a"  # 손 그림자 색상 (cls-2)
HAND_GAP = 20  # 손 사이 간격 (px)
PADDING = 20  # 이미지 주변 여유 공간 (px)

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
    """Generate default hand directions: even indices → True (right/flip), odd → False (left)."""
    return [i % 2 == 0 for i in range(count)]


def build_svg(
    hands_config: list[dict],
    bg_color: str = "#FFFFFF",
    components_dir: str = COMPONENTS_DIR,
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

    # Compute per-hand widths to support mixed-dimension SVG files
    widths = [get_svg_dimensions(s)[0] for s in processed]
    hand_h = get_svg_dimensions(processed[0])[1]
    total_w = sum(widths) + HAND_GAP * (len(processed) - 1)

    # Add padding around all hands
    bg_w = total_w + 2 * PADDING
    bg_h = hand_h + 2 * PADDING

    root = ET.Element(f"{{{SVG_NS}}}svg")
    root.set("viewBox", f"0 0 {bg_w:.2f} {bg_h:.2f}")
    root.set("width", f"{bg_w:.2f}")
    root.set("height", f"{bg_h:.2f}")

    bg = ET.SubElement(root, f"{{{SVG_NS}}}rect")
    bg.set("width", f"{bg_w:.2f}")
    bg.set("height", f"{bg_h:.2f}")
    bg.set("fill", bg_color)

    x_offset = PADDING
    for svg_str, w in zip(processed, widths):
        hand_elem = ET.fromstring(svg_str)
        hand_elem.set("x", f"{x_offset:.2f}")
        hand_elem.set("y", f"{PADDING:.2f}")
        root.append(hand_elem)
        x_offset += w + HAND_GAP

    return ET.tostring(root, encoding="unicode")
