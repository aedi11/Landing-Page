import pandas as pd
from neo4j import GraphDatabase
from datetime import datetime

# ---------------- CONFIG ----------------
NEO4J_URI="neo4j+s://9c43a27c.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="0teKZBDYeePZBS1g9WvThZgagSDdCZA9hHHVERg2YrQ"
NEO4J_DATABASE="neo4j"

EXCEL_PATH = "cell_database.xlsx"
SOURCE_NAME = "excel_cells_v1"

# ---------------- LOAD EXCEL ----------------
df = pd.read_excel(EXCEL_PATH)
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

# ================= CONNECT =================
driver = GraphDatabase.driver(
    NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

# ================= INGEST FUNCTION =================
def ingest_cell(tx, row):

    cell_id = str(row["id"])

    # -------- Cell --------
    tx.run("""
    MERGE (c:Cell {id: $cell_id})
    SET c.format = $format,
        c.energy_density_wh_l = $energy_density,
        c.source = $source,
        c.updated_at = $updated_at
    """, {
        "cell_id": cell_id,
        "format": row.get("format"),
        "energy_density": row.get("vol.energy_density(wh/l)"),
        "source": SOURCE_NAME,
        "updated_at": datetime.utcnow().isoformat()
    })

    # -------- Manufacturer --------
    tx.run("""
    MERGE (m:Manufacturer {name: $name})
    WITH m
    MATCH (c:Cell {id: $cell_id})
    MERGE (c)-[:MADE_BY]->(m)
    """, {
        "name": row.get("company_name"),
        "cell_id": cell_id
    })

    # -------- Chemistry --------
    tx.run("""
    MERGE (ch:Chemistry {type: $type, detail: $detail})
    WITH ch
    MATCH (c:Cell {id: $cell_id})
    MERGE (c)-[:HAS_CHEMISTRY]->(ch)
    """, {
        "type": row.get("chemistry"),
        "detail": row.get("chemistry_detail"),
        "cell_id": cell_id
    })

    # -------- Electrical Spec (1:1) --------
    tx.run("""
    MERGE (e:ElectricalSpec {cell_id: $cell_id})
    SET e.capacity_ah = $capacity,
        e.v_min = $v_min,
        e.v_nom = $v_nom,
        e.v_max = $v_max,
        e.i_cont = $i_cont,
        e.i_peak = $i_peak,
        e.i_charge_max = $i_charge_max,
        e.i_charge_standard = $i_charge_std,
        e.charging_voltage_v = $charging_voltage,
        e.cutoff_current_a = $cutoff_current,
        e.r_internal = $r_internal
    WITH e
    MATCH (c:Cell {id: $cell_id})
    MERGE (c)-[:HAS_ELECTRICAL_SPEC]->(e)
    """, {
        "cell_id": cell_id,
        "capacity": row.get("capacity_nom"),
        "v_min": row.get("v_min"),
        "v_nom": row.get("v_nom"),
        "v_max": row.get("v_max"),
        "i_cont": row.get("i_cont"),
        "i_peak": row.get("i_peak"),
        "i_charge_max": row.get("i_charge_max"),
        "i_charge_std": row.get("standard_charge_current_(a)"),
        "charging_voltage": row.get("charging_voltage_v"),
        "cutoff_current": row.get("charge_cutoff_current_a"),
        "r_internal": row.get("r_internal")
    })

    # -------- Thermal Limit (1:1) --------
    tx.run("""
    MERGE (t:ThermalLimit {cell_id: $cell_id})
    SET t.discharge_min_c = $dis_min,
        t.charge_min_c = $chg_min,
        t.temp_max_c = $t_max,
        t.storage_max_c = $storage_max
    WITH t
    MATCH (c:Cell {id: $cell_id})
    MERGE (c)-[:HAS_THERMAL_LIMIT]->(t)
    """, {
        "cell_id": cell_id,
        "dis_min": row.get("op_temp_discharge_min_c"),
        "chg_min": row.get("t_charge_min"),
        "t_max": row.get("t_max"),
        "storage_max": row.get("storage_temp_max_c")
    })

    # -------- Aging Spec (1:1) --------
    tx.run("""
    MERGE (a:AgingSpec {cell_id: $cell_id})
    SET a.cycle_life = $cycle_life,
        a.calendar_life_years = $calendar_life,
        a.capacity_fade_eol = $capacity_fade,
        a.resistance_growth_eol = $res_growth,
        a.crate_discharge = $crate_dis,
        a.crate_charge = $crate_chg,
        a.cycle_dod = $dod,
        a.rest_time_h = $rest
    WITH a
    MATCH (c:Cell {id: $cell_id})
    MERGE (c)-[:HAS_AGING_SPEC]->(a)
    """, {
        "cell_id": cell_id,
        "cycle_life": row.get("cycle_life"),
        "calendar_life": row.get("calendar_life_years"),
        "capacity_fade": row.get("capacity_fade_eol"),
        "res_growth": row.get("resistance_growth_eol"),
        "crate_dis": row.get("crate_discharge_cyclelife"),
        "crate_chg": row.get("crate_charge_cyclelife"),
        "dod": row.get("t_cycle_dod"),
        "rest": row.get("t_rest_h")
    })

    # -------- Physical Spec (1:1) --------
    tx.run("""
    MERGE (p:PhysicalSpec {cell_id: $cell_id})
    SET p.weight_g = $weight,
        p.length_mm = $length,
        p.height_mm = $height,
        p.width_mm = $width,
        p.diameter_mm = $diameter
    WITH p
    MATCH (c:Cell {id: $cell_id})
    MERGE (c)-[:HAS_PHYSICAL_SPEC]->(p)
    """, {
        "cell_id": cell_id,
        "weight": row.get("weight_(gr)"),
        "length": row.get("length_(mm)"),
        "height": row.get("height_(mm)"),
        "width": row.get("width_(mm)"),
        "diameter": row.get("diameter_(mm)")
    })




# ================= RUN =================
with driver.session() as session:
    for i, row in df.iterrows():
        session.execute_write(ingest_cell, row)

driver.close()
print("✅ Neo4j ingestion completed successfully")