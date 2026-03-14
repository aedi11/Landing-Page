"""Pydantic models for Steps 3-5: PackSizer, Validation, ExpansionManager
UPDATED to match the full AEDI Cell Database schema (Excel + Supabase).
Units: mass in kg, resistance in ohms, volume in liters."""

from pydantic import BaseModel, Field
from typing import Optional


class CellCandidate(BaseModel):
    """A cell fetched from the Supabase cells table (full schema)."""
    id: int
    manufacturer: str
    cell_name: str

    # Capacity
    capacity_ah_nom: Optional[float] = None
    capacity_ah_max: Optional[float] = None
    capacity_ah_min: Optional[float] = None

    # Voltage
    voltage_max_v: Optional[float] = None
    voltage_nom_v: Optional[float] = None
    voltage_min_v: Optional[float] = None

    # Energy & Mass
    energy_wh: Optional[float] = None
    mass_kg: Optional[float] = None

    # Format & Chemistry
    format: Optional[str] = None
    chemistry: Optional[str] = None
    chemistry_family: Optional[str] = None
    cathode: Optional[str] = None
    cathode_thickness_mm: Optional[float] = None
    anode: Optional[str] = None
    anode_thickness_mm: Optional[float] = None

    # Resistance (ohms)
    dcir_1s_ohms: Optional[float] = None
    dcir_5s_ohms: Optional[float] = None
    dcir_10s_ohms: Optional[float] = None
    dcir_30s_ohms: Optional[float] = None
    dcir_continuous_ohms: Optional[float] = None
    acir_ohms: Optional[float] = None

    # State of Power
    sop: Optional[float] = None

    # Dimensions
    length_mm: Optional[float] = None
    width_diameter_mm: Optional[float] = None
    height_mm: Optional[float] = None
    volume_l: Optional[float] = None

    # Discharge specs
    discharge_amps_max: Optional[float] = None
    discharge_amps_cont: Optional[float] = None
    discharge_w_5s: Optional[float] = None
    discharge_w_10s: Optional[float] = None
    discharge_w_30s: Optional[float] = None
    discharge_w_cont: Optional[float] = None
    discharge_temp_max_c: Optional[float] = None
    discharge_temp_min_c: Optional[float] = None

    # Charge specs
    charge_amps_max: Optional[float] = None
    charge_amps_cont: Optional[float] = None
    c_rate_max: Optional[float] = None
    c_rate_cont: Optional[float] = None
    charge_w_5s: Optional[float] = None
    charge_w_10s: Optional[float] = None
    charge_w_30s: Optional[float] = None
    charge_w_cont: Optional[float] = None
    charge_temp_max_c: Optional[float] = None
    charge_temp_min_c: Optional[float] = None

    # Life
    cycles_to_70_soh: Optional[int] = None
    cycles_to_80_soh: Optional[int] = None

    # Metrics
    wh_per_kg: Optional[float] = None
    wh_per_litre: Optional[float] = None
    w10s_per_kg: Optional[float] = None
    w_cont_per_kg: Optional[float] = None
    w10s_per_litre: Optional[float] = None
    siemens_per_wh: Optional[float] = None
    applications: Optional[str] = None


class PackCandidate(BaseModel):
    """A candidate S/P configuration (Step 3 output)."""
    cell: CellCandidate
    series_count: int = Field(description="S — number of cells in series")
    parallel_count: int = Field(description="P — number of cells in parallel")
    total_cells: int
    pack_voltage_v: float
    pack_capacity_ah: float
    pack_energy_wh: float
    estimated_weight_kg: float
    continuous_current_a: Optional[float] = None
    peak_current_a: Optional[float] = None
    continuous_c_rate: Optional[float] = None
    peak_c_rate: Optional[float] = None


class ValidatedCandidate(PackCandidate):
    """A candidate that passed voltage + current validation (Step 4 output)."""
    voltage_ok: bool = True
    current_ok: bool = True
    weight_ok: bool = True
    topology_notes: list[str] = Field(default_factory=list)


class ExpandedVariant(BaseModel):
    """An expanded variant with SOC window and cooling baseline (Step 5 output)."""
    base_candidate: ValidatedCandidate
    variant_label: str = Field(description="e.g. 'P', 'P+1', 'P+2'")
    parallel_count: int
    total_cells: int
    pack_capacity_ah: float
    pack_energy_wh: float
    estimated_weight_kg: float
    soc_window_min: float = Field(default=0.10, description="Min SOC (e.g. 0.10 = 10%)")
    soc_window_max: float = Field(default=0.90, description="Max SOC (e.g. 0.90 = 90%)")
    usable_energy_wh: float
    cooling_baseline: str = Field(default="passive", description="passive | active-air | liquid")
