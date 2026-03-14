"""Pydantic models for Steps 7, 10, 11: Ranking & Final Output"""

from pydantic import BaseModel, Field
from typing import Optional
from .candidates import ExpandedVariant
from .thermal import ThermalResult


class RankedCandidate(BaseModel):
    """A scored and ranked candidate (Step 7 / Step 10 output)."""
    rank: int
    variant: ExpandedVariant
    thermal_result: Optional[ThermalResult] = None

    # Scoring weights
    score_energy_density: float = Field(default=0.0, description="Normalized 0-1")
    score_weight: float = Field(default=0.0)
    score_cost: float = Field(default=0.0)
    score_cycle_life: float = Field(default=0.0)
    score_thermal: float = Field(default=0.0)
    score_c_rate_margin: float = Field(default=0.0)
    total_score: float = Field(default=0.0)


class BMSRecommendation(BaseModel):
    """BMS IC recommendation for a candidate."""
    ic_manufacturer: str
    ic_part_number: str
    topology: str = Field(description="centralized | distributed | modular")
    supported_series: str
    balancing: str = Field(description="passive | active")
    communication: str = Field(description="CAN | UART | I2C | SPI")
    stacking_notes: Optional[str] = None


class CandidateReport(BaseModel):
    """Complete report for a single candidate (Step 11 output)."""
    rank: int
    variant_name: str = Field(description="e.g. 'Cost Optimized', 'Performance Optimized', 'Space Optimized'")
    summary: str
    cell_manufacturer: str
    cell_model: str
    chemistry: str
    form_factor: str
    series_count: int
    parallel_count: int
    total_cells: int
    pack_voltage_v: float
    pack_capacity_ah: float
    pack_energy_wh: float
    usable_energy_wh: float
    estimated_weight_kg: float
    continuous_c_rate: Optional[float] = None
    peak_c_rate: Optional[float] = None
    cooling_method: str
    t_max_c: Optional[float] = None
    bms: BMSRecommendation
    estimated_cost_usd: Optional[float] = None
    pros: list[str]
    cons: list[str]
    notes: list[str]


class FinalReport(BaseModel):
    """Complete pipeline output (Step 11)."""
    request_summary: str
    candidates: list[CandidateReport] = Field(description="Top 3 ranked candidates")
    recommendation: str = Field(description="Final recommendation text")
    standards_compliance: list[str] = Field(
        default_factory=list,
        description="Application-specific safety standards (set dynamically by Step 11)"
    )
