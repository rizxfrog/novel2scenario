from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Job ---
class JobCreate(BaseModel):
    novel_text: str
    title: Optional[str] = None
    author: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    status: str
    pipeline_stage: str
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: str
    updated_at: str


# --- Character ---
class CharacterRelationship(BaseModel):
    with_: str = Field(alias="with")
    relation: str
    dynamic: str


class CharacterResponse(BaseModel):
    id: int
    job_id: int
    name: str
    role: Optional[str] = None
    traits: list[str] = []
    description: Optional[str] = None
    first_appearance: Optional[int] = None
    relationships: list[CharacterRelationship] = []


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    traits: Optional[list[str]] = None
    description: Optional[str] = None
    first_appearance: Optional[int] = None
    relationships: Optional[list[CharacterRelationship]] = None


class CharacterDelete(BaseModel):
    ids: list[int]


# --- Scene Beat ---
class SceneBeatResponse(BaseModel):
    id: int
    number: int
    type: str
    speaker: Optional[str] = None
    line: Optional[str] = None
    description: Optional[str] = None


class SceneBeatUpdate(BaseModel):
    number: Optional[int] = None
    type: Optional[str] = None
    speaker: Optional[str] = None
    line: Optional[str] = None
    description: Optional[str] = None


# --- Scene ---
class SceneSetting(BaseModel):
    location: str
    time_of_day: str
    description: str


class SceneResponse(BaseModel):
    id: int
    job_id: int
    chapter_id: int
    number: int
    heading: Optional[str] = None
    setting: Optional[SceneSetting] = None
    summary: Optional[str] = None
    characters_present: list[str] = []
    beats: list[SceneBeatResponse] = []
    chapter_title: Optional[str] = None


class SceneUpdate(BaseModel):
    heading: Optional[str] = None
    setting: Optional[SceneSetting] = None
    summary: Optional[str] = None
    characters_present: Optional[list[str]] = None
    beats: Optional[list[SceneBeatUpdate]] = None


# --- Episode ---
class EpisodeResponse(BaseModel):
    id: int
    job_id: int
    number: int
    title: Optional[str] = None
    summary: Optional[str] = None
    novel_chapters: list[int] = []
    scene_ids: list[int] = []


class EpisodeUpdate(BaseModel):
    scene_ids: list[int]


class RetryRequest(BaseModel):
    from_stage: str
    rerun_stages: list[str] = []


class AIAssistRequest(BaseModel):
    stage: str
    instruction: str
    current_data: dict


class AIAssistResponse(BaseModel):
    data: dict


# --- Script Output ---
class ScriptMeta(BaseModel):
    title: str
    author: Optional[str] = None
    total_episodes: int
    total_chapters_in_novel: int
    generated_at: str


class ScriptResponse(BaseModel):
    meta: ScriptMeta
    dramatis_personae: list[CharacterResponse]
    episodes: list[EpisodeResponse]
    adaptation_notes: list[dict]
