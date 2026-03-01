import sys
import os
import re
import tkinter as tk
import tkinter.font as tkfont

DEBUG = "--debug" in sys.argv
ARENA_FILE_PATH = os.getenv("ARENA_FILE_PATH")
RATINGS_DB_PATH = os.getenv("RATINGS_DB_PATH")
if not ARENA_FILE_PATH or not RATINGS_DB_PATH:
    raise ValueError("ARENA_FILE_PATH or RATINGS_DB_PATH not set. Did you forget to load .env first?" )

# ------------

TRANSPARENT_COLOR = "magenta" # pick a color not used elsewhere
MAX_OPACITY = 0.85

# ------------

DECK_HEIGHT = 20
DECK_WIDTH = 130

FONTS = {
    "rating":     ("Segoe UI",       8, "bold"),
    "emoji":      ("Segoe UI Emoji", 9        ),
    "deck_label": ("Arial",          8, "bold"),
    "deck_card":  ("Arial",          7, "bold"),
    "deck_count": ("Arial",         10, "bold"),
}

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

TOKEN_TO_COLOR = {
    'C': 'COLORLESS',
    'W': 'WHITE',
    'U': 'BLUE',
    'B': 'BLACK',
    'R': 'RED',
    'G': 'GREEN'
}

COLOR_TO_HEX = {
    'WHITE': "#FFFFFF",
    'BLUE' : "#87CEFA",
    'BLACK': "#666666",
    'RED'  : "#CD5C5C",
    'GREEN': "#66CDAA",
    'COLORLESS': "#B3B3B3"
}
NO_CARDS_LEFT = "#252525"

COLOR_ORDER_TO_LIST = [
    ["WHITE"],        
    ["BLUE"],  
    ["BLACK"],
    ["RED"],  
    ["GREEN"],

    ["WHITE", "BLUE"], # 5
    ["WHITE", "BLACK"],
    ["BLUE", "BLACK"],
    ["BLUE", "RED"],
    ["BLACK", "RED"],
    ["BLACK", "GREEN"],
    ["RED", "GREEN"],
    ["WHITE", "RED"],
    ["WHITE", "GREEN"],
    ["BLUE", "GREEN"],

    ["WHITE", "BLUE", "BLACK"], # 15
    ["BLUE", "BLACK", "RED"],
    ["BLACK", "RED", "GREEN"],
    ["WHITE", "RED", "GREEN"],
    ["WHITE", "BLUE", "GREEN"],
    ["WHITE", "BLACK", "RED"],
    ["BLUE", "RED", "GREEN"],
    ["WHITE", "BLACK", "GREEN"],
    ["WHITE", "BLUE", "RED"],
    ["BLUE", "BLACK", "GREEN"],

    ["WHITE", "BLUE", "BLACK", "RED"], # 25
    [], # ["WHITE", "BLACK", "RED", "GREEN"]
    [], # ["BLUE", "BLACK", "RED", "GREEN"]
    ["WHITE", "BLUE", "RED", "GREEN"],
    ["WHITE", "BLUE", "BLACK", "GREEN"],

    ["WHITE", "BLUE", "BLACK", "RED", "GREEN"], # 30
    ["COLORLESS"] # 31
]

# ------------

EXPANSION_CODE_REGEX = re.compile(r"(?<=PremierDraft_)[A-Z]{3}(?=_\d+)")

DRAFT_START_STRING_PREMIER = "[UnityCrossThreadLogger]==> EventJoin"
# DRAFT_PICK_STRING_PREMIER = "[UnityCrossThreadLogger]==> Event_PlayerDraftMakePick "
DRAFT_PACK_STRING_PREMIER = "[UnityCrossThreadLogger]Draft.Notify"
DRAFT_END_STRING_PREMIER = "[UnityCrossThreadLogger]==> DraftCompleteDraft"

# DRAFT_START_STRING_QUICK = "[UnityCrossThreadLogger]==> BotDraft_DraftStatus "
# DRAFT_PICK_STRING_QUICK = "[UnityCrossThreadLogger]==> BotDraft_DraftPick "

# MATCH_END_STRING = "OnSceneLoaded for MatchEndScene"