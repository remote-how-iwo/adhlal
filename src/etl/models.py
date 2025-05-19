"""Pydantic schema – one row per conversation."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class Likert(int, Enum):
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5


class Education(BaseModel):
    institution: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None


class ContactInfo(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    @validator("phone", pre=True, always=True)
    def _clean_phone(cls, v: str | None):  # noqa: N805 – pydantic rule
        if v:
            digits = "".join(filter(str.isdigit, v))
            return digits or None
        return None


class StudentProfile(BaseModel):
    chat_id: int
    user_email: EmailStr
    consent: bool | None = None

    education: Education = Field(default_factory=Education)

    motivation: Optional[str] = None
    experience: Optional[str] = None
    program_choice_reason: Optional[str] = None

    satisfaction_rating: Optional[Likert] = None
    satisfaction_reason: Optional[str] = None

    skills_development: Optional[str] = None

    industry_alignment_rating: Optional[Likert] = None
    industry_alignment_details: Optional[str] = None

    contact_info: ContactInfo = Field(default_factory=ContactInfo)

    orientation_interest: Optional[bool] = None

    extracted_at: datetime = Field(default_factory=datetime.utcnow) 