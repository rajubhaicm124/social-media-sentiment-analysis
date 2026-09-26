"""Pydantic request/response contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

MAX_URL_LENGTH = 2048
MAX_NAME_LENGTH = 80


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Public YouTube, Facebook or Instagram URL")
    user_name: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A URL is required.")
        if len(cleaned) > MAX_URL_LENGTH:
            raise ValueError("The URL is too long.")
        return cleaned


class DemoRequest(BaseModel):
    platform: str = Field(..., description="youtube | facebook | instagram")
    user_name: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)

    @field_validator("platform")
    @classmethod
    def _check_platform(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"youtube", "facebook", "instagram"}:
            raise ValueError("platform must be one of: youtube, facebook, instagram")
        return cleaned


class DetectRequest(BaseModel):
    url: str = Field(..., max_length=MAX_URL_LENGTH)

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A URL is required.")
        return cleaned


class ProfileRequest(BaseModel):
    user_name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    previous_name: str | None = Field(default=None, max_length=MAX_NAME_LENGTH)

    @field_validator("user_name")
    @classmethod
    def _clean(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Please enter a display name.")
        return cleaned


class RecordFilters(BaseModel):
    search: str | None = None
    sentiment: str | None = None
    platform: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    min_likes: int | None = None
    sort: str = "published_at"
    order: str = "desc"
    page: int = 1
    page_size: int = 25


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)
