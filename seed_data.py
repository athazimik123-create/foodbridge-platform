# ============================================================
# seed_data.py — FoodBridge Real Dataset Seeder
# ============================================================
# Usage:
#   python seed_data.py --csv your_file.csv [--dry-run] [--limit 50]
#
# Steps:
#   1. Drop your CSV into the revenue11 folder (same dir as app.py)
#   2. Run: python seed_data.py --csv your_file.csv --dry-run
#      (preview the first 5 rows without writing anything)
#   3. If it looks right, run: python seed_data.py --csv your_file.csv
# ============================================================

import os
import csv
import uuid
import argparse
from datetime import datetime, timezone, timedelta

# ── Load env before Firebase init ─────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Firebase init (reuses firebase_config logic) ──────────────
from firebase_config import _init_firebase, get_db, _MOCK_LISTINGS, create_food_listing

_init_firebase()
db = get_db()


# ════════════════════════════════════════════════════════════
# COLUMN MAP — edit this to match your CSV headers exactly
# ════════════════════════════════════════════════════════════
# Format:  "firestore_field": ["possible_csv_column_names", ...]
# The script tries each name in order and uses the first one found.
# Leave the list empty [] to always use the default value.

COLUMN_MAP = {
    "food_name":     ["food_name", "food", "item", "item_name", "food item",
                      "product", "product_name", "name", "description",
                      "Food Item", "Food_Item", "FoodItem"],

    "food_type":     ["food_type", "category", "type", "food_category",
                      "Category", "Food_Type", "FoodType"],

    "quantity_kg":   ["quantity_kg", "quantity", "qty", "weight_kg",
                      "weight", "amount_kg", "amount", "kg",
                      "Quantity", "Quantity_kg", "Qty"],

    "address":       ["address", "location", "pickup_address", "pickup_location",
                      "source_location", "Address", "Location", "pickup location"],

    "lat":           ["lat", "latitude", "Lat", "Latitude"],
    "lng":           ["lng", "lon", "longitude", "Lng", "Lon", "Longitude"],

    "expiry_hrs":    ["expiry_hrs", "expiry_hours", "shelf_life_hours",
                      "shelf_life", "hours_until_expiry", "freshness_hours",
                      "Expiry_Hours", "ShelfLife"],

    "donor_name":    ["donor_name", "donor", "organization", "source",
                      "restaurant", "supplier", "Donor", "Donor_Name"],

    "description":   ["description", "notes", "details", "remarks",
                      "Description", "Notes"],

    "tags":          ["tags", "labels", "keywords", "Tags"],

    "pickup_window": ["pickup_window", "pickup_time", "available_time",
                      "collection_time", "Pickup_Window", "PickupWindow"],
}

# ── Defaults used when a column isn't found in the CSV ────────
DEFAULTS = {
    "food_type":     "Mixed",
    "quantity_kg":   1.0,
    "address":       "India",
    "lat":           19.0760,
    "lng":           72.8777,
    "expiry_hrs":    24,
    "donor_name":    "Dataset Import",
    "description":   "",
    "tags":          [],
    "pickup_window": "Flexible (Anytime)",
}

# ── Food type normaliser ──────────────────────────────────────
VALID_TYPES = ["Bakery", "Prepared Meals", "Produce", "Dairy",
               "Seafood", "Grains", "Fruits", "Snacks", "Mixed"]

TYPE_ALIASES = {
    "bread":    "Bakery",  "pastry":   "Bakery",   "baked":    "Bakery",
    "meal":     "Prepared Meals",  "cooked":   "Prepared Meals",
    "lunch":    "Prepared Meals",  "dinner":   "Prepared Meals",
    "vegetable":"Produce", "veg":      "Produce",  "produce":  "Produce",
    "salad":    "Produce", "milk":     "Dairy",    "cheese":   "Dairy",
    "yogurt":   "Dairy",   "dairy":    "Dairy",    "fish":     "Seafood",
    "seafood":  "Seafood", "rice":     "Grains",   "grain":    "Grains",
    "wheat":    "Grains",  "cereal":   "Grains",   "fruit":    "Fruits",
    "apple":    "Fruits",  "banana":   "Fruits",   "snack":    "Snacks",
    "biscuit":  "Snacks",  "chips":    "Snacks",   "mixed":    "Mixed",
}

def normalise_food_type(raw: str) -> str:
    if not raw:
        return DEFAULTS["food_type"]
    raw_lower = raw.strip().lower()
    # Exact match
    for vt in VALID_TYPES:
        if raw_lower == vt.lower():
            return vt
    # Alias match
    for alias, canonical in TYPE_ALIASES.items():
        if alias in raw_lower:
            return canonical
    return DEFAULTS["food_type"]


def safe_float(val, default=1.0) -> float:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def safe_int(val, default=24) -> int:
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return default


def resolve(row: dict, field: str):
    """Try each candidate column name; return first non-empty value found."""
    for col in COLUMN_MAP.get(field, []):
        val = row.get(col, "").strip()
        if val and val.lower() not in ("nan", "none", "null", "n/a", "-"):
            return val
    return None


# ════════════════════════════════════════════════════════════
# MAIN SEEDER
# ════════════════════════════════════════════════════════════

def seed(csv_path: str, dry_run: bool, limit: int, donor_uid: str):
    if not os.path.exists(csv_path):
        print(f"❌  File not found: {csv_path}")
        return

    if not db and not dry_run:
        print("⚠️  No Firestore connection found — running in MOCK mode.")
        print("    (Data will be added to in-memory mock store, not saved permanently.)")
        print("    To use real Firestore, configure your .env with FIREBASE credentials.\n")

    print(f"\n{'='*60}")
    print(f"  FoodBridge Seed Script")
    print(f"  CSV : {csv_path}")
    print(f"  Mode: {'DRY RUN (no writes)' if dry_run else 'LIVE (writing to Firestore)'}")
    print(f"  Limit: {'All rows' if limit == 0 else f'First {limit} rows'}")
    print(f"{'='*60}\n")

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        print(f"📋  CSV columns detected: {headers}\n")

        # Show mapping preview
        print("🔗  Column mapping:")
        for field, candidates in COLUMN_MAP.items():
            matched = next((c for c in candidates if c in headers), None)
            status = f"✅  → '{matched}'" if matched else f"⚪  using default: {DEFAULTS.get(field, 'N/A')}"
            print(f"    {field:<18} {status}")
        print()

        rows = list(reader)
        if limit > 0:
            rows = rows[:limit]

        success, skipped = 0, 0

        for i, row in enumerate(rows, start=1):
            try:
                food_name = resolve(row, "food_name") or f"Item {i}"
                food_type = normalise_food_type(resolve(row, "food_type") or "")
                quantity  = safe_float(resolve(row, "quantity_kg"), DEFAULTS["quantity_kg"])
                address   = resolve(row, "address") or DEFAULTS["address"]
                lat       = safe_float(resolve(row, "lat"),  DEFAULTS["lat"])
                lng       = safe_float(resolve(row, "lng"),  DEFAULTS["lng"])
                expiry_h  = safe_int(resolve(row, "expiry_hrs"), DEFAULTS["expiry_hrs"])
                donor     = resolve(row, "donor_name") or DEFAULTS["donor_name"]
                desc      = resolve(row, "description") or DEFAULTS["description"]
                pickup_w  = resolve(row, "pickup_window") or DEFAULTS["pickup_window"]

                raw_tags  = resolve(row, "tags") or ""
                tags      = [t.strip() for t in raw_tags.split(",") if t.strip()] \
                            if raw_tags else ["dataset-import", food_type.lower()]

                expiry_dt = (datetime.now(timezone.utc) + timedelta(hours=expiry_h)).isoformat()

                data = {
                    "donor_id":      donor_uid,
                    "donor_name":    donor,
                    "food_name":     food_name,
                    "food_type":     food_type,
                    "quantity_kg":   quantity,
                    "servings":      int(quantity * 2.5),
                    "description":   desc,
                    "address":       address,
                    "lat":           lat,
                    "lng":           lng,
                    "expiry_dt":     expiry_dt,
                    "pickup_window": pickup_w,
                    "tags":          tags,
                    "premium_pickup": False,
                }

                if dry_run:
                    print(f"  [{i:>4}] DRY RUN → {food_name[:40]:<40}  "
                          f"{food_type:<15}  {quantity} kg  expiry:{expiry_h}h")
                    if i >= 5:
                        print(f"         ... (showing first 5 rows only in dry-run mode)\n")
                        break
                else:
                    listing_id = create_food_listing(data)
                    print(f"  [{i:>4}] ✅  {food_name[:45]:<45} → {listing_id[:8]}…")
                    success += 1

            except Exception as e:
                print(f"  [{i:>4}] ❌  Skipped row {i}: {e}")
                skipped += 1

    if not dry_run:
        print(f"\n{'='*60}")
        print(f"  ✅  Done!  Inserted: {success}  |  Skipped: {skipped}")
        print(f"{'='*60}\n")
    else:
        print("\n  ℹ️  Dry run complete. No data was written.")
        print("  Run without --dry-run to push all rows to Firestore.\n")


# ════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed FoodBridge Firestore with a real food surplus CSV dataset."
    )
    parser.add_argument(
        "--csv", required=True,
        help="Path to your CSV file. Example: --csv food_waste.csv"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview the first 5 rows without writing to Firestore."
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Max rows to insert. 0 = all rows. Example: --limit 100"
    )
    parser.add_argument(
        "--donor-uid", default="seed-import-001",
        help="UID to assign as donor_id for all seeded listings."
    )

    args = parser.parse_args()
    seed(
        csv_path=args.csv,
        dry_run=args.dry_run,
        limit=args.limit,
        donor_uid=args.donor_uid,
    )
