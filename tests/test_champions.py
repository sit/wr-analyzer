"""Tests for wr_analyzer.champions."""

from wr_analyzer.champions import _load_champions, fuzzy_match_champion


class TestLoadChampions:
    def test_loads_non_empty_list(self):
        champs = _load_champions()
        assert len(champs) > 100  # glossary has ~180 champions

    def test_contains_known_champions(self):
        champs = _load_champions()
        for name in ["Ahri", "Yasuo", "Jinx", "Lee Sin", "Kai'Sa"]:
            assert name in champs


class TestFuzzyMatchChampion:
    def test_exact_match(self):
        assert fuzzy_match_champion("Ahri") == "Ahri"

    def test_case_insensitive(self):
        assert fuzzy_match_champion("ahri") == "Ahri"

    def test_typo(self):
        assert fuzzy_match_champion("Yasou") == "Yasuo"

    def test_partial_match(self):
        result = fuzzy_match_champion("Lee Si")
        assert result == "Lee Sin"

    def test_no_match(self):
        assert fuzzy_match_champion("xyzxyz") is None

    def test_empty_string(self):
        assert fuzzy_match_champion("") is None
