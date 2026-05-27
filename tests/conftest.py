# tests/conftest.py
import sys
import os
import pytest

# Add parent directory to sys.path so finger_svg can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 100×150 circle at #FFC6BD — matches finger-svg-generator spec dimensions and base color
DUMMY_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="150" viewBox="0 0 100 150"><circle cx="50" cy="75" r="40" fill="#FFC6BD"/></svg>'


@pytest.fixture
def comp_dir(tmp_path):
    d = tmp_path / "components"
    d.mkdir()
    for n in range(6):
        (d / f"hand_{n}_a.svg").write_text(DUMMY_SVG, encoding="utf-8")
    (d / "hand_1_b.svg").write_text(DUMMY_SVG, encoding="utf-8")
    (d / "hand_2_b.svg").write_text(DUMMY_SVG, encoding="utf-8")
    (d / "hand_2_c.svg").write_text(DUMMY_SVG, encoding="utf-8")
    return str(d)
