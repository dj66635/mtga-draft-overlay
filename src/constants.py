import sys
import os

DEBUG = "--debug" in sys.argv
ARENA_LOGS = os.getenv("ARENA_LOGS")
DB_FOLDER = os.getenv("DB_FOLDER")
if not ARENA_LOGS or not DB_FOLDER:
    raise ValueError("ARENA_LOGS or DB_FOLDER not set. Did you forget to load .env first?" )

# ------------

EXPANSION_CODE_REGEX = r"(?<=PremierDraft_)[A-Z]{3}(?=_\d+)"

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

DRAFT_START_STRING_PREMIER = "[UnityCrossThreadLogger]==> EventJoin "
DRAFT_START_STRING_QUICK = "[UnityCrossThreadLogger]==> BotDraft_DraftStatus "

# DRAFT_PICK_STRING_PREMIER = "[UnityCrossThreadLogger]==> Event_PlayerDraftMakePick "
# DRAFT_PICK_STRING_QUICK = "[UnityCrossThreadLogger]==> BotDraft_DraftPick "

DRAFT_PACK_STRING_PREMIER = "[UnityCrossThreadLogger]Draft.Notify "

DRAFT_END_STRING_PREMIER = "[UnityCrossThreadLogger]==> DraftCompleteDraft"


