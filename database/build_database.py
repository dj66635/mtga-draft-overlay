import sqlite3
import csv
import re
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: Get csv from pubhtml spreasheet by adding /pub?gid=1590876987&single=true&output=csv
# and rename it accordingly

# Configuration
EXPANSION = sys.argv[1] # TODO: FDN SPM??
DB_PATH = f"{EXPANSION}.sqlite"
CSV_PATH = f"{EXPANSION}TierList.csv"
MTGA_DB_FOLDER = os.getenv("MTGA_DB_FOLDER")

def clean_name(name):
    """Remove any <...> tags and extra whitespace."""
    return re.sub(r'<.*?>', '', name).strip()


def find_latest_mtga_file(folder_path):
    """
    Scans folder_path for files named like Raw_CardDatabase_<hash>.mtga
    and returns the full path to the most recently modified one.
    """
    pattern = re.compile(r'Raw_CardDatabase_[0-9a-fA-F]+\.mtga$')
    candidates = []

    # Scan folder
    for filename in os.listdir(folder_path):
        if pattern.match(filename):
            full_path = os.path.join(folder_path, filename)
            candidates.append(full_path)

    if not candidates:
        return None  # no matching files found

    # Return the latest modified file
    latest_file = max(candidates, key=os.path.getmtime)
    return latest_file


MTGA_DB_PATH = find_latest_mtga_file(MTGA_DB_FOLDER)


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute(f"ATTACH DATABASE '{MTGA_DB_PATH}' AS mtgaDB;")


# Create Cards table
cur.execute("DROP TABLE IF EXISTS Cards")
cur.execute("""
CREATE TABLE Cards (
    GrpId INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    Rarity INTEGER,
    Rating TEXT
);
""")


# Copy GrpId + Name from old DB
cur.execute("""
SELECT c.GrpId, l.Loc, c.Rarity
FROM mtgaDB.Cards c
JOIN mtgaDB.Localizations_enUS l
    ON c.TitleId = l.LocId
   AND l.Formatted = 1
WHERE c.ExpansionCode = ?
""", (EXPANSION,))

rows = cur.fetchall()
print(rows)
for grp_id, name, rarity in rows:
    cleaned = clean_name(name)
    cur.execute("""
        INSERT OR IGNORE INTO Cards (GrpId, Name, Rarity)
        VALUES (?, ?, ?)
    """, (grp_id, cleaned, rarity))


cur.execute("DETACH DATABASE mtgaDB;")


# Process ratings CSV
with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        
        valid = [cell.strip() for cell in row if re.match(r'^[A-Fa-f][+-]?$|^.{3,}$', cell.strip())] # A+, or +3 chars
        if len(valid) < 3:
            continue
        print(valid)
        rating = valid[0]
        name_field = valid[2]

        # If "//"" present, we add the rating of each side as well
        cleaned = name_field.strip().strip('"').strip()
        names = [cleaned]
        if '//' in cleaned:
            parts = [part.strip() for part in cleaned.split('//')]
            names += parts

        for name in names:
            # Update the database by matching cleaned Name
            cur.execute("""
                UPDATE Cards
                SET Rating = ?
                WHERE lower(Name) = lower(?)
            """, (rating, name))


# Commit & close
conn.commit()
conn.close()
print(f"✅ Database for expansion {EXPANSION} populated and ratings applied successfully!")
