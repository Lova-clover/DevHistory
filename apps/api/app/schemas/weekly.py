"""Weekly summary related schemas."""
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeeklySummaryCreate(BaseModel):
    """Weekly summary creation request."""

    week_start: date = Field(
        ...,
        description="Week start date (Monday)",
        validation_alias="start_date",
    )
    week_end: date = Field(
        ...,
        description="Week end date (Sunday)",
        validation_alias="end_date",
    )
    regenerate: bool = Field(default=False, description="Regenerate if already exists")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("week_end")
    @classmethod
    def validate_date_range(cls, value: date, info) -> date:
        start_date = info.data.get("week_start")
        if start_date is None:
            return value

        if value <= start_date:
            raise ValueError("End date must be after start date")
        if (value - start_date).days != 6:
            raise ValueError("Week must span exactly 7 days (Monday to Sunday)")
        return value


class WeeklySummaryResponse(BaseModel):
    """Weekly summary response."""

    id: str
    user_id: str
    week_start: date
    week_end: date
    commit_count: int = Field(ge=0)
    problem_count: int = Field(ge=0)
    note_count: int = Field(ge=0)
    summary_json: dict[str, Any]
    llm_summary: Optional[str] = None
    status: str
    week: str
    created_at: datetime
    updated_at: datetime


class WeeklySummaryListResponse(BaseModel):
    """Weekly summary list response."""

    summaries: list[WeeklySummaryResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., gt=0)
    page_size: int = Field(..., gt=0)


class WeeklySummaryStats(BaseModel):
    """Weekly summary statistics."""

    total_summaries: int = Field(..., ge=0)
    total_commits: int = Field(..., ge=0)
    total_problems: int = Field(..., ge=0)
    total_blogs: int = Field(..., ge=0)
    average_commits_per_week: float = Field(..., ge=0)
    most_productive_week: Optional[str]


class WeeklyFilterRequest(BaseModel):
    """Weekly summary filter request."""

    year: Optional[int] = Field(None, ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=10, gt=0, le=50)

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, value: int) -> int:
        if value > 50:
            raise ValueError("Page size cannot exceed 50")
        return value
