"""Pydantic models for Steps 6, 9: Thermal Feasibility & Simulation"""

from pydantic import BaseModel, Field
from typing import Optional


class CoolingStrategy(BaseModel):
    """Cooling strategy assignment."""
    method: str = Field(description="passive | active-air | liquid")
    thermal_pad_conductivity_w_mk: Optional[float] = None
    fan_power_w: Optional[float] = None
    heatsink_area_cm2: Optional[float] = None
    coolant_flow_rate_lpm: Optional[float] = None


class ThermalResult(BaseModel):
    """Result of analytical thermal simulation (Step 9)."""
    variant_label: str
    cell_model: str
    heat_generation_w: float = Field(description="I^2*R total heat generation in watts")
    heat_per_cell_w: float
    cooling_capacity_w: float = Field(description="Estimated cooling capacity")
    t_ambient_c: float = Field(default=40.0)
    t_max_estimated_c: float = Field(description="Estimated max cell temperature")
    thermal_margin_c: float = Field(description="60C cutoff - T_max")
    feasible: bool = Field(description="True if T_max < 60C")
    cooling_strategy: CoolingStrategy
    recommendation: Optional[str] = None
