import pytest
from src.domain.hashtag_rules import normalize_hashtag

def test_normalize_hashtag_removes_spaces():
    assert normalize_hashtag("Cine y Series") == "#CineySeries"

def test_normalize_hashtag_removes_special_chars():
    # La implementación actual no quita tildes ni traduce &
    assert normalize_hashtag("Informática & Gaming!") == "#InformáticaGaming"

def test_normalize_hashtag_already_normalized():
    assert normalize_hashtag("#Hogar") == "#Hogar"

def test_normalize_hashtag_empty():
    assert normalize_hashtag("") == ""
    assert normalize_hashtag(None) == ""
