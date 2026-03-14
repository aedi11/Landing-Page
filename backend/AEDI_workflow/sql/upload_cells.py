"""
Upload cell database from Excel to Supabase.
Run this AFTER executing 01_cells_table.sql in Supabase SQL Editor.

Usage:
    cd backend/AEDI_workflow/sql
    pip install openpyxl pandas supabase python-dotenv
    python upload_cells.py
"""

import os
import sys
import math
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Load env from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Path to the Excel file
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "cell-database-23-02-2026.xlsx")

if not os.path.exists(EXCEL_PATH):
    print(f"ERROR: Excel file not found at {EXCEL_PATH}")
    sys.exit(1)


def safe_float(val):
    """Convert to float, return None if not a valid number."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    """Convert to int, return None if not a valid number."""
    f = safe_float(val)
    return int(f) if f is not None else None


def safe_str(val):
    """Convert to string, return None if empty/NaN."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip()
    return s if s else None


def main():
    print(f"Reading Excel file: {EXCEL_PATH}")

    # Try to read all sheets and find the one with data
    xl_file = pd.ExcelFile(EXCEL_PATH)
    print(f"Available sheets: {xl_file.sheet_names}")

    # Try each sheet and different header rows
    df = None
    used_sheet = None
    used_header_row = None

    for sheet_name in xl_file.sheet_names:
        print(f"\nTrying sheet: '{sheet_name}'")

        # Try header at row 0, 1, 2 (in case there are title rows)
        for header_row in [0, 1, 2]:
            try:
                temp_df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name, header=header_row)

                # Check if this looks like valid data
                if len(temp_df.columns) > 5 and not all('Unnamed' in str(col) for col in temp_df.columns[:5]):
                    df = temp_df
                    used_sheet = sheet_name
                    used_header_row = header_row
                    print(f"  ✓ Found data at header row {header_row}! {len(df)} rows, {len(df.columns)} columns")
                    break
            except Exception as e:
                continue

        if df is not None:
            break

    if df is None or len(df.columns) <= 2:
        print("\nERROR: Could not find valid data in any sheet.")
        print("The Excel file may have:")
        print("  - Data starting at a different row (beyond row 3)")
        print("  - All data in merged cells")
        print("  - A completely different structure")
        print("\nTrying to read first 10 rows of first sheet for debugging:")
        try:
            debug_df = pd.read_excel(EXCEL_PATH, sheet_name=0, nrows=10, header=None)
            print(debug_df.to_string())
        except Exception as e:
            print(f"  Could not read: {e}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Using sheet: '{used_sheet or xl_file.sheet_names[0]}' (header row: {used_header_row or 0})")
    print(f"Data: {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    print(f"{'='*60}")

    # Normalize column names: lowercase, strip whitespace, replace spaces with underscores
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]
    print(f"\nNormalized columns: {list(df.columns)}")

    # Map Excel columns to Supabase table columns
    # This mapping may need adjustment based on your actual column names
    COLUMN_MAP = {
        # Try multiple possible column name variants for each field
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
        "discharge_temp_max_c": ["discharge_max_temperature_°c", "discharge_temp_max_c", "t_max"],
        "discharge_temp_min_c": ["discharge_min_temperature_°c", "discharge_temp_min_c"],
        "charge_amps_max": ["charge_ampsmax", "charge_amps_max"],
        "charge_amps_cont": ["charge_ampscont", "charge_amps_cont"],
        "c_rate_max": ["c_rate_max"],
        "c_rate_cont": ["c_rate_cont"],
        "charge_w_5s": ["charge_w5s", "charge_w_5s"],
        "charge_w_10s": ["charge_w10s", "charge_w_10s"],
        "charge_w_30s": ["charge_w30s", "charge_w_30s"],
        "charge_w_cont": ["charge_wcont", "charge_w_cont"],
        "charge_temp_max_c": ["charge_max_temperature_°c", "charge_temp_max_c"],
        "charge_temp_min_c": ["charge_min_temperature_°c", "charge_temp_min_c"],
        "cycles_to_70_soh": ["cycles_to_70%_soh", "cycles_70", "cycles_to_70_soh"],
        "cycles_to_80_soh": ["cycles_to_80%_soh", "cycles_80", "cycles_to_80_soh", "cycle_life"],
        "wh_per_kg": ["wh/kg", "wh_per_kg"],
        "wh_per_litre": ["wh/litre", "wh_per_litre", "wh/l"],
        "w10s_per_kg": ["w10s/kg", "w10s_per_kg"],
        "w_cont_per_kg": ["wcontinuous/kg", "w_cont_per_kg", "wcont/kg"],
        "w10s_per_litre": ["w10s/litre", "w10s_per_litre", "w10s/l"],
        "siemens_per_wh": ["siemens/wh", "siemens_per_wh"],
        "applications": ["applications"],
    }

    def find_col(df_cols, variants):
        """Find the first matching column name from variants."""
        df_cols_lower = [c.lower() for c in df_cols]
        for v in variants:
            v_lower = v.lower().replace(" ", "_")
            for i, c in enumerate(df_cols_lower):
                if v_lower in c or c in v_lower:
                    return df.columns[i]
        return None

    # Build the mapping from Supabase column → actual Excel column
    col_mapping = {}
    for supa_col, variants in COLUMN_MAP.items():
        excel_col = find_col(df.columns, variants)
        if excel_col:
            col_mapping[supa_col] = excel_col
        else:
            col_mapping[supa_col] = None

    print(f"\nColumn mapping (Supabase → Excel):")
    for k, v in col_mapping.items():
        status = "✓" if v else "✗ NOT FOUND"
        print(f"  {k:25s} → {v or status}")

    # Check required columns
    if not col_mapping.get("manufacturer") or not col_mapping.get("cell_name"):
        print("\nERROR: Could not find 'manufacturer' or 'cell_name' columns.")
        print("Available columns:", list(df.columns))
        print("\nPlease update the COLUMN_MAP in this script to match your Excel headers.")
        sys.exit(1)

    # Build rows for Supabase
    # IMPORTANT: these must match the keys in COLUMN_MAP above
    float_cols = [
        "capacity_ah_nom", "capacity_ah_max", "capacity_ah_min",
        "voltage_max_v", "voltage_nom_v", "voltage_min_v",
        "energy_wh", "mass_kg",
        "cathode_thickness_mm", "anode_thickness_mm",
        "dcir_1s_ohms", "dcir_5s_ohms", "dcir_10s_ohms", "dcir_30s_ohms", "dcir_continuous_ohms",
        "acir_ohms", "sop",
        "length_mm", "width_diameter_mm", "height_mm", "volume_l",
        "discharge_amps_max", "discharge_amps_cont",
        "discharge_w_5s", "discharge_w_10s", "discharge_w_30s", "discharge_w_cont",
        "discharge_temp_max_c", "discharge_temp_min_c",
        "charge_amps_max", "charge_amps_cont",
        "c_rate_max", "c_rate_cont",
        "charge_w_5s", "charge_w_10s", "charge_w_30s", "charge_w_cont",
        "charge_temp_max_c", "charge_temp_min_c",
        "wh_per_kg", "wh_per_litre", "w10s_per_kg", "w_cont_per_kg", "w10s_per_litre", "siemens_per_wh",
    ]
    int_cols = ["cycles_to_70_soh", "cycles_to_80_soh"]
    str_cols = [
        "manufacturer", "cell_name", "format", "chemistry", "chemistry_family",
        "cathode", "anode", "applications",
    ]

    rows = []
    skipped = 0

    for idx, row in df.iterrows():
        record = {}

        for supa_col in str_cols:
            excel_col = col_mapping.get(supa_col)
            record[supa_col] = safe_str(row[excel_col]) if excel_col else None

        for supa_col in float_cols:
            excel_col = col_mapping.get(supa_col)
            record[supa_col] = safe_float(row[excel_col]) if excel_col else None

        for supa_col in int_cols:
            excel_col = col_mapping.get(supa_col)
            record[supa_col] = safe_int(row[excel_col]) if excel_col else None

        # Skip rows without manufacturer or cell name
        if not record.get("manufacturer") or not record.get("cell_name"):
            skipped += 1
            continue

        # Clean None values — Supabase handles NULL
        record = {k: v for k, v in record.items() if v is not None}

        rows.append(record)

    print(f"\nPrepared {len(rows)} valid rows ({skipped} skipped)")

    if not rows:
        print("No rows to upload. Check column mapping above.")
        sys.exit(1)

    # Upload in batches of 50
    BATCH_SIZE = 50
    uploaded = 0
    errors = 0

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        try:
            result = supabase.table("cells").upsert(
                batch, on_conflict="manufacturer,cell_name"
            ).execute()
            uploaded += len(batch)
            print(f"  Uploaded batch {i // BATCH_SIZE + 1}: {len(batch)} rows (total: {uploaded})")
        except Exception as e:
            errors += len(batch)
            print(f"  ERROR on batch {i // BATCH_SIZE + 1}: {e}")
            # Try inserting one by one to find the problematic row
            for row in batch:
                try:
                    supabase.table("cells").upsert(
                        row, on_conflict="manufacturer,cell_name"
                    ).execute()
                    uploaded += 1
                except Exception as e2:
                    errors += 1
                    print(f"    SKIP: {row.get('manufacturer')} {row.get('cell_name')} — {e2}")

    print(f"\nDone! Uploaded: {uploaded}, Errors: {errors}")

    # Verify
    count = supabase.table("cells").select("id", count="exact").execute()
    print(f"Total cells in Supabase: {count.count}")


if __name__ == "__main__":
    main()
