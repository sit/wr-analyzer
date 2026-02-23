"""Tests for wr_analyzer.models."""

from datetime import datetime

from wr_analyzer.models import (
    Champion,
    EventType,
    Game,
    Result,
    Runes,
    StreamAnalysis,
    TimelineEvent,
)


def test_champion_required_fields():
    champ = Champion(name="Ahri", player="Player1", role="Mid")
    assert champ.name == "Ahri"
    assert champ.runes is None
    assert champ.build == []


def test_champion_with_runes_and_build():
    runes = Runes(keystone="Electrocute", secondary="Brutal")
    champ = Champion(
        name="Zed",
        player="Player2",
        role="Mid",
        runes=runes,
        build=["Youmuu's Ghostblade", "Duskblade of Draktharr"],
    )
    assert champ.runes.keystone == "Electrocute"
    assert len(champ.build) == 2


def test_timeline_event_defaults():
    event = TimelineEvent(timestamp="00:05:30", event_type=EventType.KILL)
    assert event.player == ""
    assert event.target == ""
    assert event.assists == []


def test_game_defaults():
    game = Game(
        start_time=datetime(2025, 1, 1, 12, 0),
        end_time=datetime(2025, 1, 1, 12, 20),
        result=Result.WIN,
    )
    assert game.champions == []
    assert game.timeline == []


def test_stream_analysis_to_dict():
    now = datetime(2025, 6, 15, 10, 30)
    analysis = StreamAnalysis(
        source="test_video.mp4",
        analysis_date=now,
        games=[
            Game(
                start_time=now,
                end_time=now,
                result=Result.WIN,
                champions=[
                    Champion(name="Ahri", player="P1", role="Mid"),
                ],
                timeline=[
                    TimelineEvent(
                        timestamp="00:03:00",
                        event_type=EventType.KILL,
                        player="P1",
                        target="P2",
                        assists=["P3"],
                    ),
                ],
            )
        ],
    )
    d = analysis.to_dict()
    assert "stream_metadata" in d
    meta = d["stream_metadata"]
    assert meta["source"] == "test_video.mp4"
    assert len(meta["games"]) == 1
    game = meta["games"][0]
    assert game["result"] == "Win"
    assert game["champions"][0]["name"] == "Ahri"
    assert game["timeline"][0]["event_type"] == "Kill"
    assert game["timeline"][0]["assists"] == ["P3"]


def test_build_lists_are_independent():
    """Verify default mutable field doesn't share state across instances."""
    c1 = Champion(name="A", player="P", role="R")
    c2 = Champion(name="B", player="P", role="R")
    c1.build.append("item")
    assert c2.build == []
