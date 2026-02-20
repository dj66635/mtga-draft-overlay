
import json
import re
import sqlite3
from .constants import DRAFT_START_STRING_PREMIER, DRAFT_START_STRING_QUICK, DRAFT_PACK_STRING_PREMIER, DRAFT_END_STRING_PREMIER, EXPANSION_CODE_REGEX
from .utils import detect_string, json_find, process_json, debug_print

class DBQueries:
    def __init__(self, db_folder):
        self.db_folder = db_folder

    def get_card(self, card_id):
        conn = sqlite3.connect(self.db_folder)
        cur = conn.cursor()

        cur.execute("SELECT GrpId, Name, Rarity, Rating FROM Cards WHERE GrpId = ?", (card_id,))
        (grpId, name, rarity, rating) = cur.fetchone()

        conn.close()
        if grpId and name:
            return Card(grpId, name, rarity, rating)
        else:
            return None

class Card:
    def __init__(self, GrpId, Name, Rarity, Rating):
        self.GrpId = GrpId
        self.Name = Name
        self.Rarity = Rarity # 0: token, 1: land, 2: common, 3: uncommon, 4: rare, 5: mythic
        self.Rating = Rating

    def __lt__(self, other):
        if self.Rarity != other.Rarity:
            return self.Rarity > other.Rarity # more rare first
        return self.GrpId < other.GrpId
    
    def __str__(self):
        return f"Card(Name='{self.Name}', GrpId={self.GrpId}, Rarity={self.Rarity}, Rating={self.Rating})"
    
    def __repr__(self):
        return self.__str__()  # ensures list printing looks nice
    

class ArenaScanner:
    def __init__(
        self,
        filename,
        db_folder
    ):
        self.arena_file = filename
        self.db_handle = ""
        self.db_folder = db_folder
        self.in_draft = False
        with open(self.arena_file, "r", encoding="utf-8", errors="replace") as f: # avoid processing the whole file
            f.seek(0, 2) 
            self.start_and_pack_offset = f.tell()
            self.end_offset = f.tell()

    def draft_start_search(self):
        """Search for the string that represents the start of a draft"""
        event_name = None
        try:
            with open(self.arena_file, "r", encoding="utf-8", errors="replace") as log:
                log.seek(self.start_and_pack_offset)
                while True:
                    line = log.readline()
                    if not line:
                        break
                    debug_print(f"Waiting for draft start: {line}")
                    self.start_and_pack_offset = log.tell()
                    start_offset = detect_string(line, [DRAFT_START_STRING_PREMIER, DRAFT_START_STRING_QUICK])
                    if start_offset != -1:
                        entry_string = line[start_offset:]
                        event_data = process_json(entry_string)
                        event_name = json_find("EventName", event_data)
                        set_code = re.search(EXPANSION_CODE_REGEX, event_name) # extract 3 letter code expansion
                        self.db_handle = DBQueries(f"{self.db_folder}/{set_code.group()}.sqlite")
                        debug_print(f"Opening DB {self.db_folder}/{set_code.group()}.sqlite")
                        return event_name # i see no harm exiting from here, we can only find pack or end events from now on
        except Exception as error:
            print(f"Exception draft_start_search: {error}")
        return event_name
    

    def draft_pack_search(self):
        """Parse the premier draft string that contains the non-P1P1 pack data"""
        ratings = None
        # Identify and print out the log lines that contain the draft packs
        try:
            with open(self.arena_file, "r", encoding="utf-8", errors="replace") as log:
                log.seek(self.start_and_pack_offset)
                while True:
                    line = log.readline()
                    if not line:
                        break
                    debug_print(f"Waiting for pack: {line}")
                    self.start_and_pack_offset = log.tell()
                    string_offset = detect_string(line, [DRAFT_PACK_STRING_PREMIER])
                    if string_offset != -1:
                        cards = []
                        # Identify the pack
                        draft_data = json.loads(line[string_offset:])
                        cardIds = str(draft_data["PackCards"]).split(",")
                        for cardId in cardIds:
                            cards.append(self.db_handle.get_card(cardId))
                        cards.sort()
                        debug_print(f"P{draft_data['SelfPack']}-P{draft_data['SelfPick']}: {cards}")
                        ratings = [card.Rating for card in cards]
        except Exception as error:
             print(f"Exception draft_pack_search: {error}")
             return [] # return empty in order to trigger a clear_boxes
        return ratings


    def draft_end_search(self):
        try:
            with open(self.arena_file, "r", encoding="utf-8", errors="replace") as log:
                log.seek(self.end_offset)
                while True:
                    line = log.readline()
                    if not line:
                        break
                    self.end_offset = log.tell()
                    end_offset = detect_string(line, [DRAFT_END_STRING_PREMIER])
                    if end_offset != -1:
                        debug_print(f"Found draft end: {line}")
                        return True # return right away (?)
        except Exception as error:
            print(f"Exception draft_end_search: {error}")
        return False
                    