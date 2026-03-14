"""
Upload design rules from JSON files to Supabase with OpenAI embeddings.
Auto-checks for the design_rules table and gives clear instructions if missing.

Usage:
    cd backend/AEDI_workflow/sql
    pip install openai supabase python-dotenv
    python upload_rules.py
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# Load env from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    print("ERROR: SUPABASE_URL, SUPABASE_KEY, and OPENAI_API_KEY must be set in backend/.env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Rule JSON files to upload
RULE_FILES = [
    ("electrical_rules.json", "Electrical"),
    ("thermal_rules.json", "Thermal"),
    ("mechanical_rules.json", "Mechanical"),
]

# Map rule_type to a category for pipeline filtering
RULE_TYPE_TO_CATEGORY = {
    "Electrical": "electrical",
    "Thermal": "thermal",
    "Mechanical": "mechanical",
    "Safety": "safety",
    "Performance": "performance",
    "Regulatory": "regulatory",
}

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 50


def check_table_exists() -> bool:
    """Check if the design_rules table exists in Supabase."""
    try:
        supabase.table("design_rules").select("id").limit(1).execute()
        return True
    except Exception as e:
        error_str = str(e)
        if "PGRST205" in error_str or "schema cache" in error_str or "does not exist" in error_str:
            return False
        # Some other error — table might exist but have a different issue
        return False


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts using OpenAI."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def build_embedding_text(rule: dict) -> str:
    """Build a rich text string for embedding that captures the rule's full context."""
    parts = []

    # Rule type and severity
    parts.append(f"[{rule.get('rule_type', 'General')}]")
    parts.append(f"[{rule.get('severity', 'Warning')}]")

    # Applies to
    if rule.get("applies_to"):
        parts.append(f"[Applies to: {rule['applies_to']}]")

    # Parameter context
    if rule.get("parameter"):
        param_str = f"Parameter: {rule['parameter']}"
        if rule.get("min_value") is not None:
            param_str += f", Min: {rule['min_value']}"
        if rule.get("max_value") is not None:
            param_str += f", Max: {rule['max_value']}"
        if rule.get("nominal_value") is not None:
            param_str += f", Nominal: {rule['nominal_value']}"
        if rule.get("unit"):
            param_str += f" {rule['unit']}"
        parts.append(param_str)

    # The actual constraint text (most important for semantic search)
    parts.append(rule.get("constraint_expr", ""))

    return " ".join(parts)


def main():
    # ── Step 0: Verify table exists ──────────────────────────────────────
    print("Checking if 'design_rules' table exists in Supabase...")
    if not check_table_exists():
        print("")
        print("=" * 70)
        print("  TABLE NOT FOUND: 'design_rules' does not exist yet")
        print("=" * 70)
        print("")
        print("  You need to create it first. Follow these steps:")
        print("")
        print("  1. Go to your Supabase Dashboard:")
        print(f"     {SUPABASE_URL.replace('.supabase.co', '.supabase.com/dashboard/project/' + SUPABASE_URL.split('//')[1].split('.')[0])}")
        print("  2. Click 'SQL Editor' in the left sidebar")
        print("  3. Click 'New Query'")
        print("  4. Paste the FULL contents of: 02_design_rules_table.sql")
        print("  5. Click 'Run'")
        print("  6. Then re-run this script: python upload_rules.py")
        print("")
        print("=" * 70)
        sys.exit(1)

    print("  Table found!\n")

    # ── Step 1: Load rules from JSON files ───────────────────────────────
    sql_dir = os.path.dirname(__file__)
    total_uploaded = 0
    total_errors = 0
    all_rules = []

    for filename, default_type in RULE_FILES:
        filepath = os.path.join(sql_dir, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: {filename} not found, skipping")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            rules = json.load(f)

        print(f"Loaded {len(rules)} rules from {filename}")

        for rule in rules:
            rule_type = rule.get("rule_type", default_type)
            category = RULE_TYPE_TO_CATEGORY.get(rule_type, rule_type.lower())

            record = {
                "rule_type": rule_type,
                "category": category,
                "constraint_expr": rule.get("constraint_expr", ""),
                "severity": rule.get("severity", "Warning"),
                "source": rule.get("source"),
                "applies_to": rule.get("applies_to"),
                "parameter": rule.get("parameter"),
                "min_value": rule.get("min_value"),
                "max_value": rule.get("max_value"),
                "nominal_value": rule.get("nominal_value"),
                "unit": rule.get("unit"),
                "raw_json": rule,
            }

            # Clean None values
            record = {k: v for k, v in record.items() if v is not None}

            # Skip rules with empty constraint text
            if not record.get("constraint_expr"):
                continue

            all_rules.append(record)

    print(f"\nTotal rules to upload: {len(all_rules)}")

    if not all_rules:
        print("No rules found. Check JSON files.")
        sys.exit(1)

    # ── Step 2: Generate embeddings in batches ───────────────────────────
    print(f"\nGenerating embeddings ({EMBEDDING_MODEL})...")
    embedding_texts = [build_embedding_text(r.get("raw_json", r)) for r in all_rules]

    all_embeddings = []
    for i in range(0, len(embedding_texts), EMBEDDING_BATCH_SIZE):
        batch_texts = embedding_texts[i:i + EMBEDDING_BATCH_SIZE]
        batch_num = i // EMBEDDING_BATCH_SIZE + 1
        total_batches = (len(embedding_texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

        print(f"  Embedding batch {batch_num}/{total_batches} ({len(batch_texts)} rules)...")

        try:
            embeddings = generate_embeddings(batch_texts)
            all_embeddings.extend(embeddings)
        except Exception as e:
            print(f"  ERROR generating embeddings: {e}")
            all_embeddings.extend([None] * len(batch_texts))

        # Rate limit: wait between batches
        if i + EMBEDDING_BATCH_SIZE < len(embedding_texts):
            time.sleep(0.5)

    embedded_count = sum(1 for e in all_embeddings if e)
    print(f"Generated {embedded_count} embeddings")

    # Attach embeddings to records
    for idx, record in enumerate(all_rules):
        if idx < len(all_embeddings) and all_embeddings[idx]:
            record["embedding"] = all_embeddings[idx]

    # ── Step 3: Upload to Supabase in batches ────────────────────────────
    print(f"\nUploading to Supabase...")
    UPLOAD_BATCH = 20  # Smaller batches due to embedding size

    for i in range(0, len(all_rules), UPLOAD_BATCH):
        batch = all_rules[i:i + UPLOAD_BATCH]
        batch_num = i // UPLOAD_BATCH + 1

        try:
            supabase.table("design_rules").insert(batch).execute()
            total_uploaded += len(batch)
            print(f"  Batch {batch_num}: uploaded {len(batch)} rules (total: {total_uploaded})")
        except Exception as e:
            print(f"  ERROR on batch {batch_num}: {e}")
            # Try one by one
            for record in batch:
                try:
                    supabase.table("design_rules").insert(record).execute()
                    total_uploaded += 1
                except Exception as e2:
                    total_errors += 1
                    constraint_preview = record.get("constraint_expr", "")[:60]
                    print(f"    SKIP: [{record.get('rule_type')}] {constraint_preview}... — {e2}")

    # ── Step 4: Verify ───────────────────────────────────────────────────
    print(f"\n{'=' * 50}")
    print(f"Upload complete! Uploaded: {total_uploaded}, Errors: {total_errors}")
    print(f"{'=' * 50}")

    try:
        count = supabase.table("design_rules").select("id", count="exact").execute()
        print(f"\nTotal rules in Supabase: {count.count}")

        # Summary by type
        for rule_type in ["Electrical", "Thermal", "Mechanical", "Safety", "Performance", "Regulatory"]:
            try:
                type_count = supabase.table("design_rules").select(
                    "id", count="exact"
                ).eq("rule_type", rule_type).execute()
                if type_count.count:
                    print(f"  {rule_type}: {type_count.count}")
            except Exception:
                pass
    except Exception as e:
        print(f"\nCould not verify counts: {e}")
        if total_uploaded > 0:
            print(f"But {total_uploaded} rules were uploaded successfully.")


if __name__ == "__main__":
    main()
