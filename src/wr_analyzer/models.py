"""Dataclasses matching the analysis schema (docs/schema.json)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Result(str, Enum):
    WIN = "Win"
    LOSE = "Lose"


class EventType(str, Enum):
    KILL = "Kill"
    TURRET_DESTROYED = "TurretDestroyed"


@dataclass
class Runes:
    keystone: str
    secondary: str


@dataclass
class Champion:
    name: str
    player: str
    role: str
    runes: Optional[Runes] = None
    build: list[str] = field(default_factory=list)


@dataclass
class TimelineEvent:
    timestamp: str  # "HH:MM:SS"
    event_type: EventType
    player: str = ""
    target: str = ""
    assists: list[str] = field(default_factory=list)


@dataclass
class Game:
    start_time: datetime
    end_time: datetime
    result: Result
    champions: list[Champion] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)


@dataclass
class StreamAnalysis:
    source: str
    analysis_date: datetime
    games: list[Game] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict matching the JSON schema structure."""
        return {"stream_metadata": asdict(self)}
