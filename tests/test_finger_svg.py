# tests/test_finger_svg.py
import importlib
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
