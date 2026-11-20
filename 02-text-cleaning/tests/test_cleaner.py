import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cleaner import normalize_whitespace


def test_collapses_blank_lines():
    assert normalize_whitespace("a\n\n\n\nb") == "a\n\nb"


def test_collapses_spaces():
    assert normalize_whitespace("hello     world") == "hello world"
