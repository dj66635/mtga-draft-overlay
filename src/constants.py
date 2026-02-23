import sys
import os
import re

DEBUG = "--debug" in sys.argv
ARENA_FILE_PATH = os.getenv("ARENA_FILE_PATH")
RATINGS_DB_PATH = os.getenv("RATINGS_DB_PATH")
if not ARENA_FILE_PATH or not RATINGS_DB_PATH:
    raise ValueError("ARENA_FILE_PATH or RATINGS_DB_PATH not set. Did you forget to load .env first?" )

# ------------

TRANSPARENT_COLOR = "magenta" # pick a color not used elsewhere
MAX_OPACITY = 0.85

# ------------

RATING_COLOR = {
    "A+": "#00FF00", 
    "A":  "#33FF00",
    "A-": "#66FF00",
    "B+": "#99FF00",
    "B":  "#CCFF00",
    "B-": "#FFFF00",
    "C+": "#FFCC00",
    "C":  "#FF9900",
    "C-": "#FF6600",
    "D+": "#FF3300",
    "D":  "#FF0000",
    "D-": "#CC0000",
    "F":  "#800000",
}
DEFAULT_COLOR = "#888888"

# ------------

EXPANSION_CODE_REGEX = re.compile(r"(?<=PremierDraft_)[A-Z]{3}(?=_\d+)")

DRAFT_START_STRING_PREMIER = "[UnityCrossThreadLogger]==> EventJoin "
# DRAFT_PICK_STRING_PREMIER = "[UnityCrossThreadLogger]==> Event_PlayerDraftMakePick "
DRAFT_PACK_STRING_PREMIER = "[UnityCrossThreadLogger]Draft.Notify "
DRAFT_END_STRING_PREMIER = "[UnityCrossThreadLogger]==> DraftCompleteDraft"

# DRAFT_START_STRING_QUICK = "[UnityCrossThreadLogger]==> BotDraft_DraftStatus "
# DRAFT_PICK_STRING_QUICK = "[UnityCrossThreadLogger]==> BotDraft_DraftPick "