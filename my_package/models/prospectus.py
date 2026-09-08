"""Pydantic schema for structured Eurobond prospectus extraction output."""
import re
from datetime import date as date_type
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field, validator
from pydantic.generics import GenericModel

T = TypeVar("T")

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
COMMON_CODE_PATTERN = re.compile(r"^\d{9}$")
LEI_PATTERN = re.compile(r"^[A-Z0-9]{20}$")
COUPON_TYPES = {"fixed", "floating", "zero"}


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
    common_code: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    clearing_systems: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    specified_denomination: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    form_of_notes: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    coupon_type: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    interest_payment_frequency: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    issue_price: ExtractedField[float] = Field(default_factory=ExtractedField[float])
    seniority: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    issuer_lei: ExtractedField[str] = Field(default_factory=ExtractedField[str])
    guarantor_name: ExtractedField[str] = Field(default_factory=ExtractedField[str])

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

    @validator("common_code")
    def _downgrade_confidence_on_bad_common_code_format(cls, v: ExtractedField) -> ExtractedField:
        if v.value is not None and not COMMON_CODE_PATTERN.match(v.value):
            v.confidence = min(v.confidence, 0.2)
        return v

    @validator("issuer_lei")
    def _downgrade_confidence_on_bad_lei_format(cls, v: ExtractedField) -> ExtractedField:
        if v.value is not None and not LEI_PATTERN.match(v.value):
            v.confidence = min(v.confidence, 0.2)
        return v

    @validator("coupon_type")
    def _downgrade_confidence_on_unknown_coupon_type(cls, v: ExtractedField) -> ExtractedField:
        if v.value is not None and v.value not in COUPON_TYPES:
            v.confidence = min(v.confidence, 0.2)
        return v

    @validator("issue_price")
    def _downgrade_confidence_on_implausible_issue_price(cls, v: ExtractedField) -> ExtractedField:
        # Issue price is a percentage of par; anything outside 0-200% is suspect.
        if v.value is not None and not (0.0 < v.value <= 200.0):
            v.confidence = min(v.confidence, 0.2)
        return v
