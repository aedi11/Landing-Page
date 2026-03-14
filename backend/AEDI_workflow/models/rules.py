"""Pydantic models for Step 2: RuleQueryEngine"""

from pydantic import BaseModel, Field
from typing import Optional


class SeriesMapEntry(BaseModel):
    """Single chemistry-to-series mapping entry."""
    chemistry: str = Field(description="Cell chemistry, e.g. NMC, LFP, NCA")
    nominal_cell_voltage: str = Field(description="Nominal cell voltage, e.g. 3.6V or 3.2V")
    series_count: str = Field(description="Number of cells in series, e.g. 13 or 15")


class VoltageRule(BaseModel):
    """Voltage design rule for a given application."""
    application: str
    recommended_voltages: list[float] = Field(description="Recommended pack voltages in V")
    series_map: Optional[list[SeriesMapEntry]] = Field(
        default_factory=list,
        description="Chemistry-to-series-count mappings"
    )
    source: Optional[str] = None



class CurrentRule(BaseModel):
    """Current / C-rate design rule for a given application."""
    application: str
    max_continuous_c_rate: float = Field(description="Max continuous C-rate for longevity")
    max_peak_c_rate: float = Field(description="Max peak C-rate (short burst)")
    peak_duration_s: float = Field(default=5.0, description="Max duration for peak C-rate in seconds")
    ideal_continuous_c_rate: float = Field(default=1.0)
    source: Optional[str] = None


class DesignRules(BaseModel):
    """Combined design rules output from Step 2."""
    voltage_rules: list[VoltageRule]
    current_rules: list[CurrentRule]
    thermal_rules: list[dict] = Field(default_factory=list)
    safety_rules: list[dict] = Field(default_factory=list)
    bms_rules: list[dict] = Field(default_factory=list)
