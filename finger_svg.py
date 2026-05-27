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
