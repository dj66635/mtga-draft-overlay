import json
import sqlite3
import logging
from .card import Card
from .constants import DRAFT_PACK_STRING_PREMIER, DRAFT_END_STRING_PREMIER, EXPANSION_CODE_REGEX
from .utils import detect_string

logger = logging.getLogger(__name__)


class DBQueries:
    def __init__(self, db_folder):
        self.db_folder = db_folder

    def get_card(self, card_id):
        conn = sqlite3.connect(self.db_folder)
        cur = conn.cursor()

        cur.execute("SELECT * FROM Cards WHERE GrpId = ?", (card_id,))
        (grp_id, name, rarity, is_land, colors, collector_number, expansion_code, rating) = cur.fetchone()

        conn.close()
        if grp_id and name:
            return Card(grp_id, name, rarity, is_land, colors, collector_number, expansion_code, rating)
        else:
            return None


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
        # set_code = None
        try:
            with open(self.arena_file, "r", encoding="utf-8", errors="replace") as log:
                log.seek(self.start_and_pack_offset)
                while True:
                    line = log.readline()
                    if not line:
                        break
                    logger.debug(f"Waiting for draft start: {line}")
                    self.start_and_pack_offset = log.tell()

                    set_code = EXPANSION_CODE_REGEX.search(line)
                    if set_code:
                        expansion_db = f"{self.db_folder}/{set_code.group()}.sqlite"
                        self.db_handle = DBQueries(expansion_db)
                        logger.debug(f"Opening DB {expansion_db}")
                        return set_code.group() # i see no harm exiting from here, we can only find pack or end events from now on                        
                    
        except Exception as error:
            logger.exception(f"Exception draft_start_search: {error}")
        return None
    

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
                    logger.debug(f"Waiting for pack: {line}")
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
                        logger.debug(f"P{draft_data['SelfPack']}-P{draft_data['SelfPick']}:\n{Card.list_to_string(cards)}")
                        ratings = [card.Rating for card in cards]

        except Exception as error:
             logger.exception(f"Exception draft_pack_search: {error}")
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
                        logger.debug(f"Found draft end: {line}")
                        return True # return right away (?)
                    
        except Exception as error:
            logger.exception(f"Exception draft_end_search: {error}")
        return False
                    