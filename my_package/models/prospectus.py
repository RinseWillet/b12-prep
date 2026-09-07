"""Pydantic schema for structured Eurobond prospectus extraction output."""
import re
from datetime import date as date_type
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

T = TypeVar("T")

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


class ExtractedField(GenericModel, Generic[T]):
    """A single extracted value with provenance, used for confidence/sentinel handling."""

    value: Optional[T] = None
    confidence: float = 0.0
    source_page: Optional[int] = None
    extraction_method: str = "stub"  # one of: llm, stub, manual

    @validator("confidence")
    def _clamp_confidence_to_unit_range(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class ProspectusFields(BaseModel):
    isin: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    issuer_name: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    currency: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    aggregate_nominal_amount: ExtractedField[float] = Field(default_factory=ExtractedField[float])
    coupon_rate: ExtractedField[float] = Field(default_factory=ExtractedField[float])
    maturity_date: ExtractedField[date_type] = Field(default_factory=ExtractedField[date_type])
    issue_date: ExtractedField[date_type] = Field(default_factory=ExtractedField[date_type])
    governing_law: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    listing: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    document_type: ExtractedField[str] = Field(default_factory=ExtractedField[str])

    @validator("isin")
    def _downgrade_confidence_on_bad_isin_format(cls, v: ExtractedField) -> ExtractedField:
        if v.value is not None and not ISIN_PATTERN.match(v.value):
            v.confidence = min(v.confidence, 0.2)
        return v

    @validator("currency")
    def _downgrade_confidence_on_bad_currency_format(cls, v: ExtractedField) -> ExtractedField:
        if v.value is not None and not CURRENCY_PATTERN.match(v.value):
            v.confidence = min(v.confidence, 0.2)
        return v
