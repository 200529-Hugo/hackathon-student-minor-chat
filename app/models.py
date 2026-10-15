"""Model: data die door de controller en services wordt gedeeld."""

from dataclasses import dataclass, field

from pydantic import BaseModel, Field


class Profile(BaseModel):
    """Tijdelijk voorkeurenprofiel; bevat bewust geen identificeerbare gegevens."""

    study: str = ""
    interests: list[str] = Field(default_factory=list)
    development_goal: str = ""
    location_preferences: list[str] = Field(default_factory=list)
    study_mode_preferences: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)


@dataclass
class Session:
    """De gespreksstatus van één browser, uitsluitend bewaard in servergeheugen."""

    profile: Profile = field(default_factory=Profile)
    stage: str = "study"
    last_recommendations: list[dict] = field(default_factory=list)
    excluded_ids: set[str] = field(default_factory=set)
