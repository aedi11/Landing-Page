"""Pydantic models for Step 1: RequirementsParser"""

from pydantic import BaseModel, Field
from typing import Optional


class UserRequirements(BaseModel):
    """Raw user input — natural language query."""
    query: str = Field(description="User's natural language design requirements")


class ParsedRequirements(BaseModel):
    """Structured requirements extracted by LLM (Step 1 output)."""
    application_type: str = Field(
        description="Identified application: e-scooter, e-bike, e-motorcycle, e-rickshaw, "
        "telecom-backup, solar-ess, ups, industrial-ess, etc."
    )
    target_voltage_v: float = Field(description="Target nominal pack voltage in volts")
    target_energy_wh: float = Field(description="Target pack energy in Wh")
    target_capacity_ah: Optional[float] = Field(
        default=None, description="Target pack capacity in Ah (derived if not given)"
    )
    nominal_power_w: Optional[float] = Field(
        default=None, description="Nominal continuous power in watts"
    )
    peak_power_w: Optional[float] = Field(
        default=None, description="Peak power in watts"
    )
    max_weight_kg: Optional[float] = Field(
        default=None, description="Maximum allowed pack weight in kg"
    )
    max_volume_l: Optional[float] = Field(
        default=None, description="Maximum allowed pack volume in liters"
    )
    preferred_chemistry: Optional[str] = Field(
        default=None, description="User-preferred chemistry: NMC, LFP, NCA, LTO, or None"
    )
    preferred_form_factor: Optional[str] = Field(
        default=None, description="User-preferred form factor: cylindrical, prismatic, pouch, blade, or None"
    )
    target_series_count: Optional[int] = Field(
        default=None, description="User-specified series count (e.g. 16 for 16S). None if not specified."
    )
    target_parallel_count: Optional[int] = Field(
        default=None, description="User-specified parallel count (e.g. 1 for 1P). None if not specified."
    )
    target_discharge_current_a: Optional[float] = Field(
        default=None, description="Target continuous discharge current in amps (e.g. 100A)"
    )
    target_peak_current_a: Optional[float] = Field(
        default=None, description="Target peak discharge current in amps"
    )
    protection_features: list[str] = Field(
        default_factory=list,
        description="Protection features: MCB, fuse, contactor, precharge, etc. with ratings if given"
    )
    monitoring_features: list[str] = Field(
        default_factory=list,
        description="Monitoring/communication features: WiFi, Bluetooth, RS485, CAN, MODBUS, LCD, LED, etc."
    )
    enclosure_type: Optional[str] = Field(
        default=None,
        description="Enclosure type: 19-inch-rack, wall-mount, IP65-outdoor, custom, etc."
    )
    swappable: bool = Field(default=False, description="Whether the pack needs to be swappable")
    cooling_preference: Optional[str] = Field(
        default=None, description="Cooling preference: passive, active-air, liquid, or None"
    )
    budget_usd: Optional[float] = Field(
        default=None, description="Budget constraint in USD"
    )
    special_requirements: list[str] = Field(
        default_factory=list, description="Any additional special requirements"
    )
    confidence: float = Field(
        default=1.0, description="Confidence score 0-1 that all critical fields were extracted"
    )
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Questions to ask user if confidence < 0.8"
    )
