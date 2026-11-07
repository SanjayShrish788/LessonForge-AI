from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LessonCreate(StrictModel):
    title: str = Field(min_length=3, max_length=180)
    learning_objective: str = Field(min_length=15, max_length=3000)


class Section(StrictModel):
    id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    title: str = Field(min_length=1, max_length=200)
    kind: Literal["overview", "objectives", "prerequisites", "introduction", "concepts", "examples", "applications", "activity", "knowledge_check", "summary"]
    content: str = Field(min_length=1, max_length=20000)
    minutes: int = Field(ge=1, le=45)
    source_ids: list[str] = Field(default_factory=list, max_length=30)


class LessonContent(StrictModel):
    sections: list[Section] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def valid_sections(self):
        if len({s.id for s in self.sections}) != len(self.sections):
            raise ValueError("Section IDs must be unique")
        if sum(s.minutes for s in self.sections) > 45:
            raise ValueError("The complete core lesson must fit within 45 minutes")
        return self


class LessonUpdate(LessonContent):
    expected_version: int = Field(ge=1)


class VersionRequest(StrictModel):
    expected_version: int = Field(ge=1)


class RunRequest(StrictModel):
    stage: Literal["all", "research", "generation", "qc_research", "qc_instructional", "qc_both"] = "all"


class RecommendationRequest(VersionRequest):
    action: Literal["apply", "reject"]
