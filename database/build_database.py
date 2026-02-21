import sqlite3
import csv
import re
import os
import sys
import shutil
from dotenv import load_dotenv

# IMPORTANT: Get csv from pubhtml spreasheet by adding /pub?gid=1590876987&single=true&output=csv
# and rename it accordingly

load_dotenv()
MTGA_DB_FOLDER = os.getenv("MTGA_DB_FOLDER")

# Includes bonus sheets. Special guests are implicitly included as well for base set (SGP-XYZ)
EXPANSION_SETS = { 
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



def build_expansion_db(expansion):
    db_path = f"{expansion}.sqlite"
    csv_path = f"{expansion}TierList.csv"
    set_codes = EXPANSION_SETS[expansion]

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("DROP TABLE IF EXISTS Cards")
    cur.execute("""
    CREATE TABLE Cards (
        GrpId INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Rarity INTEGER NOT NULL,
        IsLand INTEGER NOT NULL,
        Colors TEXT NOT NULL,
        CollectorNumber INTEGER NOT NULL,
        ExpansionCode TEXT,
        Rating TEXT
    );
    """)

    # dont put it before DROP because it'll work from here when the new db does not yet exist
    cur.execute(f"ATTACH DATABASE '{MTGA_DB_BACKUP_PATH}' AS mtgaDB;") 

    placeholders = ",".join(["?"] * len(set_codes))
    spg_value = f"SPG-{expansion}"
    query = f"""
    SELECT c.GrpId, l.Loc, c.Rarity, c.Order_LandLast, c.Colors, c.CollectorNumber, c.ExpansionCode
    FROM mtgaDB.Cards c
    JOIN mtgaDB.Localizations_enUS l
        ON c.TitleId = l.LocId
       AND l.Formatted = 1
    WHERE c.ExpansionCode IN ({placeholders})
    OR c.DigitalReleaseSet = ?
    """
    cur.execute(query, set_codes + [spg_value])

    rows = cur.fetchall()

    for grp_id, name, rarity, order_land_last, colors, collector_number_text, expansion_code in rows:
        cleaned = clean_name(name)
        is_land = order_land_last if order_land_last is not None else 0 # 1: true ; 0/None: false
        try:
            collector_number = int(collector_number_text)
        except (ValueError, TypeError):
            collector_number = 0

        cur.execute("""
            INSERT OR IGNORE INTO Cards (GrpId, Name, Rarity, IsLand, Colors, CollectorNumber, ExpansionCode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (grp_id, cleaned, rarity, is_land, colors, collector_number, expansion_code))

    cur.execute("DETACH DATABASE mtgaDB;")


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

    conn.commit()
    conn.close()
    print(f"✅ Database for expansion {expansion} built successfully!")


def main():
    global MTGA_DB_BACKUP_PATH
    MTGA_DB_BACKUP_PATH = find_mtga_file_backup(MTGA_DB_FOLDER)
    print(f"Working with database: {MTGA_DB_BACKUP_PATH}")

    if not MTGA_DB_BACKUP_PATH:
        print("❌ No MTGA database found.")
        return

    # If expansions passed as arguments, use only those
    expansions_to_process = list(EXPANSION_SETS.keys())
    if len(sys.argv) > 1:
        requested = [arg.upper() for arg in sys.argv[1:]]
        invalid = [exp for exp in requested if exp not in EXPANSION_SETS]
        if invalid:
            print(f"❌ Unknown expansion(s): {invalid}")
            print(f"Available expansions: {list(EXPANSION_SETS.keys())}")
            return
        expansions_to_process = requested
        
    for expansion in expansions_to_process:
        print(f"Processing {expansion} with sets {EXPANSION_SETS[expansion]}")
        build_expansion_db(expansion)
    
    if os.path.exists(MTGA_DB_BACKUP_PATH):
        os.remove(MTGA_DB_BACKUP_PATH)


if __name__ == "__main__":
    main()