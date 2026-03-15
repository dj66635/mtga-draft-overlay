import sqlite3
import csv
import re
import os
import argparse
import shutil
from dotenv import load_dotenv

# IMPORTANT: Get csv from pubhtml spreasheet by adding /pub?gid=1590876987&single=true&output=csv
# and rename it accordingly

load_dotenv()
MTGA_DB_FOLDER = os.getenv("MTGA_DB_FOLDER")

DB_PATH = "RatingsDB.sqlite"

# Includes bonus sheets. Special guests are implicitly included as well for base set (SGP-XYZ)
EXPANSION_SETS = { 
    "TMT": ["TMT"],
    "ECL": ["ECL"],
    "TLA": ["TLA"],
    "SPM": ["SPM", "MAR"], # TODO: weird card naming
    "EOE": ["EOE", "EOS"],
    "FIN": ["FIN", "FCA"],
    "TDM": ["TDM"],
    "DFT": ["DFT"],
    "FDN": ["FDN"], # TODO: alt names
    "DSK": ["DSK"],
    "BLB": ["BLB"], # missing?
    "OTJ": ["OTJ", "BIG", "OTP"],
    "MKM": ["MKM"],
}


def clean_name(name):
    # Remove any <...> tags and extra whitespace
    return re.sub(r'<.*?>', '', name).strip()


def find_mtga_file_backup(folder_path):
    # Scans folder_path for files named like Raw_CardDatabase_<hash>.mtga, back it up and return backup path
    pattern = re.compile(r'Raw_CardDatabase_[0-9a-fA-F]+\.mtga$')
    candidates = []

    # Scan folder
    for filename in os.listdir(folder_path):
        if pattern.match(filename):
            full_path = os.path.join(folder_path, filename)
            candidates.append(full_path)

    if not candidates:
        return None

    # Return the latest modified file
    latest_file = max(candidates, key=os.path.getmtime)

    # Back it up
    backup_path = os.path.join(os.getcwd(), os.path.basename(latest_file))
    shutil.copy2(latest_file, backup_path)
    return backup_path



def build_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Cards (
        GrpId INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        AltName TEXT,
        Rarity INTEGER NOT NULL,
        IsLand INTEGER NOT NULL,
        ColorOrder INTEGER NOT NULL,
        OldSchoolManaText TEXT NOT NULL,
        Types TEXT NOT NULL,
        CollectorNumber INTEGER NOT NULL,
        ExpansionCode TEXT,
        Rating TEXT
    );
    """)

    # dont put it before DROP because it'll work from here when the new db does not yet exist
    cur.execute(f"ATTACH DATABASE '{MTGA_DB_BACKUP_PATH}' AS mtgaDB;") 

    query = f"""
    SELECT c.GrpId, l.Loc, alt.Loc, c.Rarity, c.Order_LandLast, c.Order_ColorOrder, c.OldSchoolManaText, c.Types, c.CollectorNumber, c.ExpansionCode
    FROM mtgaDB.Cards c
    JOIN mtgaDB.Localizations_enUS l
        ON c.TitleId = l.LocId
        AND l.Formatted = 1
    LEFT JOIN mtgaDB.Localizations_enUS alt
        ON c.InterchangeableTitleId = alt.LocId
        AND alt.Formatted = 1
    """
    cur.execute(query)
    rows = cur.fetchall()

    cur.execute("DETACH DATABASE mtgaDB;")

    for grp_id, name, alt_name, rarity, order_land_last, order_color_order, old_school_mana_text, types, collector_number_text, expansion_code in rows:
        cleaned_name = clean_name(name)
        cleaned_alt_name = clean_name(alt_name) if alt_name else None
        is_land = order_land_last if order_land_last is not None else 0 # 1: true ; 0/None: false
        color_order = order_color_order if order_color_order is not None else 100 # will be ordered last, should not happen
        try:
            collector_number = int(collector_number_text)
        except (ValueError, TypeError):
            collector_number = 0

        cur.execute("""
            INSERT OR IGNORE INTO Cards (GrpId, Name, AltName, Rarity, IsLand, ColorOrder, OldSchoolManaText, Types, CollectorNumber, ExpansionCode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (grp_id, cleaned_name, cleaned_alt_name, rarity, is_land, color_order, old_school_mana_text, types, collector_number, expansion_code))
    
    conn.commit()
    conn.close()
    print(f"✅ Base database successfully!")


def add_expansion_ratings(expansions):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for expansion in expansions:
        csv_path = f"{expansion}TierList.csv"
        # Apply ratings
        try:
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    valid = [cell.strip() for cell in row
                            if re.match(r'^[A-Fa-f][+-]?$|^.{3,}$', cell.strip())] # A+, or +3 chars

                    if len(valid) < 3:
                        continue

                    rating = valid[0]
                    name_field = valid[2]
                    cleaned = name_field.strip().strip('"').strip()
                    names = [cleaned]

                    if '//' in cleaned:
                        parts = [part.strip() for part in cleaned.split('//')]
                        names += parts

                    for name in names:
                        cur.execute("""
                            UPDATE Cards
                            SET Rating = ?
                            WHERE lower(Name) = lower(?)
                        """, (rating, name))
        except FileNotFoundError:
            print(f"⚠️ CSV file missing for {expansion}, skipping ratings.")
    
        print(f"✅ Ratings for expansion {expansion} added successfully!")

    conn.commit()
    conn.close()


def main():
    global MTGA_DB_BACKUP_PATH
    MTGA_DB_BACKUP_PATH = find_mtga_file_backup(MTGA_DB_FOLDER)
    print(f"Working with database: {MTGA_DB_BACKUP_PATH}")

    if not MTGA_DB_BACKUP_PATH:
        print("❌ No MTGA database found.")
        return

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--build",
        action="store_true",
        help="Build database from MTGA's one"
    )

    parser.add_argument(
        "expansions",
        nargs="*",
        help="Add expansions ratings"
    )

    args = parser.parse_args()

    expansions = list(EXPANSION_SETS.keys())
    if args.expansions:
        requested = [arg.upper() for arg in args.expansions]
        invalid = [exp for exp in requested if exp not in EXPANSION_SETS]
        if invalid:
            print(f"❌ Unknown expansion(s): {invalid}")
            print(f"Available expansions: {list(EXPANSION_SETS.keys())}")
            return
        expansions = requested

    if args.build:
        print("Running build step...")
        build_database()

    print(f"Processing {expansions}...")
    add_expansion_ratings(expansions)

    if os.path.exists(MTGA_DB_BACKUP_PATH):
        os.remove(MTGA_DB_BACKUP_PATH)


if __name__ == "__main__":
    main()