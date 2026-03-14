"""
Generate cell_defaults.json from Supabase cell data.
Computes median values grouped by chemistry, format, and chemistry+format.

Run this after uploading cells to Supabase:
    cd backend/AEDI_workflow/sql
    python generate_defaults.py

Re-run whenever you add new cells to keep estimates accurate.
"""

import os
import sys
import json
import statistics
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fields we want fallback estimates for (only numeric fields used in pipeline)
FALLBACK_FIELDS = [
    "capacity_ah_nom",
    "voltage_nom_v",
    "voltage_max_v",
    "voltage_min_v",
    "energy_wh",
    "mass_kg",
    "dcir_10s_ohms",
    "acir_ohms",
    "length_mm",
    "width_diameter_mm",
    "height_mm",
    "volume_l",
    "discharge_amps_max",
    "discharge_amps_cont",
    "discharge_temp_max_c",
    "discharge_temp_min_c",
    "charge_amps_max",
    "charge_amps_cont",
    "charge_temp_max_c",
    "charge_temp_min_c",
    "cycles_to_80_soh",
    "cycles_to_70_soh",
    "wh_per_kg",
    "wh_per_litre",
]


def safe_median(values: list) -> float | None:
    """Compute median from a list, filtering out None/non-numeric."""
    clean = [v for v in values if v is not None and isinstance(v, (int, float))]
    if not clean:
        return None
    return round(statistics.median(clean), 6)


def compute_group_medians(cells: list[dict], group_key: str) -> dict:
    """Group cells by a key and compute median for each fallback field."""
    groups: dict[str, list[dict]] = {}
    for cell in cells:
        key_val = cell.get(group_key)
        if not key_val:
            continue
        key_val = str(key_val).strip()
        if key_val not in groups:
            groups[key_val] = []
        groups[key_val].append(cell)

    result = {}
    for key_val, group_cells in groups.items():
        medians = {}
        for field in FALLBACK_FIELDS:
            med = safe_median([c.get(field) for c in group_cells])
            if med is not None:
                medians[field] = med
        if medians:
            result[key_val] = {
                "count": len(group_cells),
                "medians": medians,
            }
    return result


def compute_combo_medians(cells: list[dict]) -> dict:
    """Group cells by chemistry+format combo and compute medians."""
    groups: dict[str, list[dict]] = {}
    for cell in cells:
        chem = cell.get("chemistry")
        fmt = cell.get("format")
        if not chem or not fmt:
            continue
        key = f"{chem.strip()}|{fmt.strip()}"
        if key not in groups:
            groups[key] = []
        groups[key].append(cell)

    result = {}
    for key, group_cells in groups.items():
        medians = {}
        for field in FALLBACK_FIELDS:
            med = safe_median([c.get(field) for c in group_cells])
            if med is not None:
                medians[field] = med
        if medians:
            result[key] = {
                "count": len(group_cells),
                "medians": medians,
            }
    return result


def compute_manufacturer_chemistry_medians(cells: list[dict]) -> dict:
    """Group cells by manufacturer+chemistry and compute medians."""
    groups: dict[str, list[dict]] = {}
    for cell in cells:
        mfr = cell.get("manufacturer")
        chem = cell.get("chemistry")
        if not mfr or not chem:
            continue
        key = f"{mfr.strip()}|{chem.strip()}"
        if key not in groups:
            groups[key] = []
        groups[key].append(cell)

    result = {}
    for key, group_cells in groups.items():
        medians = {}
        for field in FALLBACK_FIELDS:
            med = safe_median([c.get(field) for c in group_cells])
            if med is not None:
                medians[field] = med
        if medians:
            result[key] = {
                "count": len(group_cells),
                "medians": medians,
            }
    return result


def main():
    print("Fetching all cells from Supabase...")
    result = supabase.table("cells").select("*").execute()
    cells = result.data or []
    print(f"Found {len(cells)} cells")

    if not cells:
        print("No cells in database. Run upload_cells.py first.")
        sys.exit(1)

    # 1. Global medians (last resort fallback)
    print("\nComputing global medians...")
    global_medians = {}
    for field in FALLBACK_FIELDS:
        med = safe_median([c.get(field) for c in cells])
        if med is not None:
            global_medians[field] = med
    print(f"  {len(global_medians)} fields with global medians")

    # 2. By chemistry (e.g. NMC, LFP, NCA)
    print("Computing chemistry group medians...")
    by_chemistry = compute_group_medians(cells, "chemistry")
    print(f"  {len(by_chemistry)} chemistry groups: {list(by_chemistry.keys())}")

    # 3. By format (e.g. cylindrical, prismatic, pouch)
    print("Computing format group medians...")
    by_format = compute_group_medians(cells, "format")
    print(f"  {len(by_format)} format groups: {list(by_format.keys())}")

    # 4. By chemistry + format combo (e.g. NMC|cylindrical)
    print("Computing chemistry+format combo medians...")
    by_chem_format = compute_combo_medians(cells)
    print(f"  {len(by_chem_format)} combo groups: {list(by_chem_format.keys())}")

    # 5. By manufacturer + chemistry (e.g. Samsung|NMC)
    print("Computing manufacturer+chemistry medians...")
    by_mfr_chem = compute_manufacturer_chemistry_medians(cells)
    print(f"  {len(by_mfr_chem)} manufacturer+chemistry groups")

    # 6. By manufacturer
    print("Computing manufacturer group medians...")
    by_manufacturer = compute_group_medians(cells, "manufacturer")
    print(f"  {len(by_manufacturer)} manufacturer groups: {list(by_manufacturer.keys())}")

    # Build the defaults JSON
    defaults = {
        "_meta": {
            "generated_from": f"{len(cells)} cells",
            "fields": FALLBACK_FIELDS,
            "hierarchy": [
                "1. manufacturer+chemistry (most specific)",
                "2. chemistry+format",
                "3. chemistry",
                "4. format",
                "5. manufacturer",
                "6. global median (least specific)",
            ],
        },
        "global": global_medians,
        "by_chemistry": by_chemistry,
        "by_format": by_format,
        "by_chemistry_format": by_chem_format,
        "by_manufacturer_chemistry": by_mfr_chem,
        "by_manufacturer": by_manufacturer,
    }

    # Write to JSON
    output_path = os.path.join(os.path.dirname(__file__), "..", "cell_defaults.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=2)

    print(f"\nWritten to: {os.path.abspath(output_path)}")

    # Print summary table
    print(f"\n{'='*70}")
    print("FALLBACK DEFAULTS SUMMARY")
    print(f"{'='*70}")
    print(f"{'Field':<25s} {'Global':>10s}", end="")
    for chem in list(by_chemistry.keys())[:5]:
        print(f" {chem:>10s}", end="")
    print()
    print("-" * 70)
    for field in FALLBACK_FIELDS:
        val = global_medians.get(field)
        print(f"{field:<25s} {str(val or '-'):>10s}", end="")
        for chem in list(by_chemistry.keys())[:5]:
            cval = by_chemistry.get(chem, {}).get("medians", {}).get(field)
            print(f" {str(cval or '-'):>10s}", end="")
        print()
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
