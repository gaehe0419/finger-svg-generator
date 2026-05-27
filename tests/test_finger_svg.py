# tests/test_finger_svg.py
import sys
import os
import pytest


def reload_module(comp_dir):
    """finger_svg를 새 COMPONENTS_DIR로 재로드."""
    if "finger_svg" in sys.modules:
        del sys.modules["finger_svg"]
    import finger_svg
    finger_svg.COMPONENTS_DIR = comp_dir
    finger_svg.load_svg.cache_clear()
    return finger_svg


def test_load_svg_returns_string(comp_dir):
    fsvg = reload_module(comp_dir)
    path = os.path.join(comp_dir, "hand_0_a.svg")
    result = fsvg.load_svg(path)
    assert isinstance(result, str)
    assert "<svg" in result


def test_load_svg_caches(comp_dir):
    fsvg = reload_module(comp_dir)
    path = os.path.join(comp_dir, "hand_0_a.svg")
    r1 = fsvg.load_svg(path)
    r2 = fsvg.load_svg(path)
    assert r1 is r2  # lru_cache가 동일 객체 반환


def test_get_variants_single(comp_dir):
    fsvg = reload_module(comp_dir)
    assert fsvg.get_variants(0, comp_dir) == ["a"]
    assert fsvg.get_variants(5, comp_dir) == ["a"]


def test_get_variants_multiple(comp_dir):
    fsvg = reload_module(comp_dir)
    assert fsvg.get_variants(1, comp_dir) == ["a", "b"]
    assert fsvg.get_variants(2, comp_dir) == ["a", "b", "c"]


def test_get_variants_missing_number_returns_a(comp_dir):
    fsvg = reload_module(comp_dir)
    assert fsvg.get_variants(9, comp_dir) == ["a"]


def test_get_svg_dimensions_from_viewbox():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 300"><circle/></svg>'
    w, h = fsvg.get_svg_dimensions(svg)
    assert w == 200.0
    assert h == 300.0


def test_get_svg_dimensions_from_width_height():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="150px" height="250px"><circle/></svg>'
    w, h = fsvg.get_svg_dimensions(svg)
    assert w == 150.0
    assert h == 250.0


def test_apply_color_replaces_base(comp_dir):
    fsvg = reload_module(comp_dir)
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle fill="#FFC6BD"/></svg>'
    result = fsvg.apply_color(svg, "#FF6666")
    assert "#FF6666" in result
    assert "#FFC6BD" not in result


def test_apply_color_case_insensitive(comp_dir):
    fsvg = reload_module(comp_dir)
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle fill="#ffc6bd"/></svg>'
    result = fsvg.apply_color(svg, "#26C9CB")
    assert "#26C9CB" in result
    assert "#ffc6bd" not in result


def test_apply_color_no_change_when_no_match(comp_dir):
    fsvg = reload_module(comp_dir)
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle fill="#000000"/></svg>'
    result = fsvg.apply_color(svg, "#FF6666")
    assert "#000000" in result


def test_apply_flip_adds_transform():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 150"><circle cx="50" cy="75" r="40" fill="#FFC6BD"/></svg>'
    result = fsvg.apply_flip(svg)
    assert "scale(-1,1)" in result
    assert "translate(" in result


def test_apply_flip_preserves_dimensions():
    fsvg = reload_module("components")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 150"><circle/></svg>'
    result = fsvg.apply_flip(svg)
    w, h = fsvg.get_svg_dimensions(result)
    assert w == 100.0
    assert h == 150.0


def test_decompose_zero():
    fsvg = reload_module("components")
    assert fsvg.decompose(0) == [0]


def test_decompose_single_hand():
    fsvg = reload_module("components")
    assert fsvg.decompose(3) == [3]
    assert fsvg.decompose(5) == [5]


def test_decompose_two_hands():
    fsvg = reload_module("components")
    assert fsvg.decompose(6) == [5, 1]
    assert fsvg.decompose(10) == [5, 5]


def test_decompose_three_four_hands():
    fsvg = reload_module("components")
    assert fsvg.decompose(13) == [5, 5, 3]
    assert fsvg.decompose(20) == [5, 5, 5, 5]


def test_default_hand_directions():
    fsvg = reload_module("components")
    assert fsvg.default_hand_directions(1) == [True]           # 오른손
    assert fsvg.default_hand_directions(2) == [True, False]    # 오른, 왼
    assert fsvg.default_hand_directions(4) == [True, False, True, False]
