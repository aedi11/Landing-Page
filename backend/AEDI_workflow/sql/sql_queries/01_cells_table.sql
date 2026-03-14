-- ============================================================================
-- AEDI Battery Pack Pipeline — Supabase Schema: cells table
-- UPDATED to match the full AEDI Cell Database Excel schema
-- Units: mass in kg, resistance in ohms, volume in liters, thickness in mm
-- Execute this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- ============================================================================

-- Drop old table if exists (only run on first setup)
DROP TABLE IF EXISTS cells CASCADE;

CREATE TABLE cells (
    id                      SERIAL PRIMARY KEY,

    -- Identity
    manufacturer            TEXT NOT NULL,
    cell_name               TEXT NOT NULL,

    -- Capacity
    capacity_ah_nom         FLOAT,
    capacity_ah_max         FLOAT,
    capacity_ah_min         FLOAT,

    -- Voltage
    voltage_max_v           FLOAT,
    voltage_nom_v           FLOAT,
    voltage_min_v           FLOAT,

    -- Energy
    energy_wh               FLOAT,

    -- Mass (kg)
    mass_kg                 FLOAT,

    -- Format & Chemistry
    format                  TEXT,            -- cylindrical, prismatic, pouch
    chemistry               TEXT,            -- NMC, NCA, LFP, LTO, etc.
    chemistry_family        TEXT,            -- e.g. NMC811, NMC622
    cathode                 TEXT,
    cathode_thickness_mm    FLOAT,
    anode                   TEXT,
    anode_thickness_mm      FLOAT,

    -- Resistance (ohms)
    dcir_1s_ohms            FLOAT,
    dcir_5s_ohms            FLOAT,
    dcir_10s_ohms           FLOAT,           -- DC internal resistance at 10s pulse
    dcir_30s_ohms           FLOAT,
    dcir_continuous_ohms    FLOAT,
    acir_ohms               FLOAT,           -- AC internal resistance

    -- State of Power
    sop                     FLOAT,

    -- Dimensions (mm)
    length_mm               FLOAT,
    width_diameter_mm       FLOAT,           -- width for prismatic/pouch, diameter for cylindrical
    height_mm               FLOAT,

    -- Volume (liters)
    volume_l                FLOAT,

    -- Discharge specs
    discharge_amps_max      FLOAT,
    discharge_amps_cont     FLOAT,
    discharge_w_5s          FLOAT,
    discharge_w_10s         FLOAT,
    discharge_w_30s         FLOAT,
    discharge_w_cont        FLOAT,
    discharge_temp_max_c    FLOAT,
    discharge_temp_min_c    FLOAT,

    -- Charge specs
    charge_amps_max         FLOAT,
    charge_amps_cont        FLOAT,
    c_rate_max              FLOAT,
    c_rate_cont             FLOAT,
    charge_w_5s             FLOAT,
    charge_w_10s            FLOAT,
    charge_w_30s            FLOAT,
    charge_w_cont           FLOAT,
    charge_temp_max_c       FLOAT,
    charge_temp_min_c       FLOAT,

    -- Calendar Life
    cycles_to_70_soh        INT,
    cycles_to_80_soh        INT,

    -- Performance Metrics (computed or from sheet)
    wh_per_kg               FLOAT,
    wh_per_litre            FLOAT,
    w10s_per_kg             FLOAT,
    w_cont_per_kg           FLOAT,
    w10s_per_litre          FLOAT,
    siemens_per_wh          FLOAT,

    -- Applications
    applications            TEXT,

    -- Metadata
    created_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(manufacturer, cell_name)
);

-- Indexes for common pipeline queries
CREATE INDEX idx_cells_chemistry ON cells(chemistry);
CREATE INDEX idx_cells_format ON cells(format);
CREATE INDEX idx_cells_capacity ON cells(capacity_ah_nom);
CREATE INDEX idx_cells_voltage ON cells(voltage_nom_v);
CREATE INDEX idx_cells_manufacturer ON cells(manufacturer);
CREATE INDEX idx_cells_energy ON cells(energy_wh);
CREATE INDEX idx_cells_wh_per_kg ON cells(wh_per_kg);
