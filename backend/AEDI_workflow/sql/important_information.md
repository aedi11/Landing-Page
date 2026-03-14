# Important Information

## Supabase Column Mapping

```
        "manufacturer": ["Manufacturer"],
        "cell_name": ["cell_name", "cell name", "model", "part"],
        "capacity_ah_nom": ["capacity_ah_nom", "ah_nom", "capacity_nom", "capacity"],
        "capacity_ah_max": ["capacity_ah_max", "ah_max", "capacity_max"],
        "capacity_ah_min": ["capacity_ah_min", "ah_min", "capacity_min"],
        "voltage_max_v": ["voltage_max_v", "v_max", "max", "voltage_max"],
        "voltage_nom_v": ["voltage_nom_v", "v_nom", "nom", "voltage_nom"],
        "voltage_min_v": ["voltage_min_v", "v_min", "min", "voltage_min"],
        "energy_wh": ["energy_wh", "energy", "wh"],
        "mass_kg": ["mass_kg", "mass", "weight_gr", "weight_g"],
        "format": ["format", "form_factor", "cell_shape"],
        "chemistry": ["chemistry", "chemistry_detail"],
        "chemistry_family": ["chemistry_family", "family"],
        "cathode": ["cathode"],
        "cathode_thickness_mm": ["cathode_thickness", "cathode_thickness_mm"],
        "anode": ["anode"],
        "anode_thickness_mm": ["anode_thickness", "anode_thickness_mm"],
        "dcir_1s_ohms": ["dcir_1s_ohms"],
        "dcir_5s_ohms": ["dcir_5s_ohms"],
        "dcir_10s_ohms": ["dcir_10s", "dcir_10s_ohms", "r_internal"],
        "dcir_30s_ohms": ["dcir_30s_ohms"],
        "dcir_continuous_ohms": ["dcir_continuous_ohms"],
        "acir_ohms": ["acir", "acir_ohms"],
        "sop": ["sop"],
        "length_mm": ["length_mm", "length"],
        "width_diameter_mm": ["width_diameter_mm", "width_mm", "width_diameter", "diameter_mm", "width/diameter"],
        "height_mm": ["height_mm", "height"],
        "volume_l": ["volume_l", "volume"],
        "discharge_amps_max": ["discharge_ampsmax", "ampsmax", "i_peak", "discharge_amps_max"],
        "discharge_amps_cont": ["discharge_ampscont", "ampscont", "i_cont", "discharge_amps_cont"],
        "discharge_w_5s": ["discharge_w5s", "w5s", "discharge_w_5s"],
        "discharge_w_10s": ["discharge_w10s", "w10s", "discharge_w_10s"],
        "discharge_w_30s": ["discharge_w30s", "w30s", "discharge_w_30s"],
        "discharge_w_cont": ["discharge_wcont", "wcont", "discharge_w_cont"],
        "discharge_temp_max_c": ["discharge_max_temperature_c", "discharge_temp_max_c", "t_max"],
        "discharge_temp_min_c": ["discharge_min_temperature_c", "discharge_temp_min_c"],
        "charge_amps_max": ["charge_ampsmax", "charge_amps_max"],
        "charge_amps_cont": ["charge_ampscont", "charge_amps_cont"],
        "c_rate_max": ["c_rate_max"],
        "c_rate_cont": ["c_rate_cont"],
        "charge_w_5s": ["charge_w5s", "charge_w_5s"],
        "charge_w_10s": ["charge_w10s", "charge_w_10s"],
        "charge_w_30s": ["charge_w30s", "charge_w_30s"],
        "charge_w_cont": ["charge_wcont", "charge_w_cont"],
        "charge_temp_max_c": ["charge_max_temperature_c", "charge_temp_max_c"],
        "charge_temp_min_c": ["charge_min_temperature_c", "charge_temp_min_c"],
        "cycles_to_70_soh": ["cycles_to_70%_soh", "cycles_70", "cycles_to_70_soh"],
        "cycles_to_80_soh": ["cycles_to_80%_soh", "cycles_80", "cycles_to_80_soh", "cycle_life"],
        "wh_per_kg": ["wh/kg", "wh_per_kg"],
        "wh_per_litre": ["wh/litre", "wh_per_litre", "wh/l"],
        "w10s_per_kg": ["w10s/kg", "w10s_per_kg"],
        "w_cont_per_kg": ["wcontinuous/kg", "w_cont_per_kg", "wcont/kg"],
        "w10s_per_litre": ["w10s/litre", "w10s_per_litre", "w10s/l"],
        "siemens_per_wh": ["siemens/wh", "siemens_per_wh"],
        "applications": ["applications"],
```

---

## Standard Units

All values stored in Supabase and used throughout the pipeline:

| Field | Unit | Notes |
|-------|------|-------|
| mass_kg | **kilograms** | NOT grams |
| dcir_*_ohms | **ohms** | NOT milliohms |
| acir_ohms | **ohms** | NOT milliohms |
| volume_l | **liters** | NOT cc/mL |
| cathode/anode_thickness_mm | **millimeters** | NOT micrometers |
| voltage_*_v | volts | |
| capacity_ah_* | amp-hours | |
| energy_wh | watt-hours | |
| length/width/height_mm | millimeters | |
| discharge/charge_amps_* | amps | |
| discharge/charge_w_* | watts | |
| *_temp_*_c | degrees Celsius | |
| cycles_to_*_soh | cycle count | integer |

---

## Fallback Defaults System

### Problem

Many cells in the database have null values for fields like mass, resistance, volume, etc. Using a single hardcoded default (e.g. 70g for all cells) is inaccurate because an NMC 21700 cell weighs ~70g but an LFP prismatic cell weighs ~500g.

### Solution: Hierarchical Fallback Lookup

When a cell value is null, the pipeline uses a **6-level hierarchy** to find the best available estimate:

```
Priority 1: manufacturer + chemistry    (e.g. Samsung SDI + NMC)     <- most accurate
Priority 2: chemistry + format           (e.g. NMC + cylindrical)
Priority 3: chemistry only               (e.g. NMC)
Priority 4: format only                  (e.g. cylindrical)
Priority 5: manufacturer only            (e.g. Samsung SDI)
Priority 6: global median               (median across ALL cells)    <- least accurate
Priority 7: emergency hardcoded          (only if JSON file missing)
```

Each level returns the **median** value computed from matching cells in the database.

### How It Works

**3 components:**

1. **`sql/generate_defaults.py`** -- One-time script that queries Supabase, groups cells by chemistry/format/manufacturer, computes medians for each group, and writes `cell_defaults.json`

2. **`cell_defaults.json`** -- Auto-generated lookup table with medians at every group level:
   ```json
   {
     "global": { "mass_kg": 0.065, "dcir_10s_ohms": 0.018 },
     "by_chemistry": {
       "NMC": { "count": 30, "medians": { "mass_kg": 0.048 } },
       "LFP": { "count": 15, "medians": { "mass_kg": 0.520 } }
     },
     "by_chemistry_format": {
       "NMC|cylindrical": { "count": 20, "medians": { "mass_kg": 0.048 } },
       "LFP|prismatic":   { "count": 10, "medians": { "mass_kg": 0.560 } }
     },
     "by_manufacturer_chemistry": {
       "Samsung SDI|NMC": { "count": 8, "medians": { "mass_kg": 0.050 } }
     }
   }
   ```

3. **`defaults.py`** -- Python module loaded at import time. Provides:
   ```python
   from ..defaults import get_fallback_for_cell

   # In pipeline code:
   mass = cell.mass_kg or get_fallback_for_cell("mass_kg", cell)
   # -> Automatically uses cell's chemistry, format, manufacturer
   #    to walk the hierarchy and return the best estimate
   ```

### Pipeline Fields Using Fallbacks

| Field | Pipeline steps | Impact if wrong |
|-------|---------------|-----------------|
| `mass_kg` | step03, step04, step05 | Pack weight estimate off |
| `dcir_10s_ohms` | step05, step06, step09 | Thermal/cooling calcs inaccurate |
| `capacity_ah_nom` | step06, step09 (1C fallback) | Heat generation estimate wrong |
| `volume_l` | step06 | Volume fit check wrong |

### When to Re-generate Defaults

Run `python sql/generate_defaults.py` whenever you:
- Add new cells to the database
- Update existing cell data
- Change the Excel file and re-upload

The more cells you have, the more accurate the group medians become.

### Example: Why Hierarchy Matters

Looking up `mass_kg` for a Samsung SDI NMC 21700 cell with null mass:

| Level | Group | Median | Cells |
|-------|-------|--------|-------|
| 1 | Samsung SDI + NMC | 0.049 kg | 8 cells |
| 2 | NMC + cylindrical | 0.048 kg | 20 cells |
| 3 | NMC (all formats) | 0.065 kg | 30 cells |
| 4 | cylindrical (all chemistries) | 0.055 kg | 25 cells |
| 5 | Samsung SDI (all chemistries) | 0.052 kg | 12 cells |
| 6 | global | 0.085 kg | 61 cells |
| 7 | emergency hardcoded | 0.070 kg | -- |

The pipeline would use **0.049 kg** (Level 1) -- much more accurate than a generic 0.070 kg.

---

## Data Upload Workflow

```
1. Run SQL schemas in Supabase SQL Editor:
   - 01_cells_table.sql        -> creates cells table
   - 02_design_rules_table.sql -> creates design_rules table + RPC functions

2. Upload cell data:
   python sql/upload_cells.py  -> reads Excel -> uploads to cells table

3. Upload design rules:
   python sql/upload_rules.py  -> reads JSON files -> generates embeddings -> uploads

4. Generate fallback defaults:
   python sql/generate_defaults.py -> queries cells -> computes medians -> writes cell_defaults.json
```

Re-run step 4 whenever cell data changes to keep estimates accurate.
