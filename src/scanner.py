import json
import os
import logging
from .card import Card, DBQueries
from .constants import DRAFT_PACK_STRING_PREMIER, DRAFT_START_STRING_PREMIER, DRAFT_END_STRING_PREMIER, EXPANSION_CODE_REGEX
from .utils import detect_string
from .events import DraftPackEvent, DraftStartEvent, DraftEndEvent

logger = logging.getLogger(__name__)


class ArenaScanner:
    def __init__(self, arena_file_path, ratings_db_path):
        self.arena_file_path = arena_file_path
        self.arena_file_size = os.path.getsize(self.arena_file_path)
        self.ratings_db_path = ratings_db_path
        self.ratings_db_handle = DBQueries(self.ratings_db_path)
        with open(self.arena_file_path, "r", encoding="utf-8", errors="replace") as f: # avoid processing the whole file
            f.seek(0, 2) 
            self.offset = f.tell()

        self.handlers = [
            ( [DRAFT_PACK_STRING_PREMIER], self._handle_draft_pack ),
            ( [DRAFT_START_STRING_PREMIER], self._handle_draft_start ),
            ( [DRAFT_END_STRING_PREMIER], self._handle_draft_end ),
        ]


    def check_log_rotation(self):
        current_size = os.path.getsize(self.arena_file_path)
        if current_size < self.arena_file_size: # file was truncated or rotated
            logger.info("Log file smaller than last read – resetting offset to 0")
            self.offset = 0
        self.arena_file_size = current_size


    def poll_events(self):
        self.check_log_rotation()
        events = []
        with open(self.arena_file_path, "r", encoding="utf-8", errors="replace") as log:
            log.seek(self.offset)

            while True:
                line = log.readline()
                if not line:
                    break
                logger.debug(f"{line}")
                self.offset = log.tell()

                if event := self.parse_line(line):
                    events.append(event)

        return events
    

    def parse_line(self, line):
        for search_strings, handler in self.handlers:
            if (offset := detect_string(line, search_strings)) is not None:
                return handler(line, offset)
        return None


    def _handle_draft_pack(self, line, offset):
        ratings = []
        try:
            cards = []
            draft_data = json.loads(line[offset:])
            card_ids = str(draft_data["PackCards"]).split(",")
            cards = [self.ratings_db_handle.get_card(c_id) for c_id in card_ids]
            cards.sort()
            logger.debug(f"P{draft_data['SelfPack']}-P{draft_data['SelfPick']}:\n{Card.list_to_string(cards)}\n")
            ratings = [card.rating for card in cards]
        except Exception as error:
             logger.exception(f"_handle_draft_pack: {error}")

        return DraftPackEvent(ratings=ratings)


    def _handle_draft_start(self, line, _offset):
        set_code = EXPANSION_CODE_REGEX.search(line)
        if set_code:
            return DraftStartEvent(set_code=set_code.group())
        return None
        

    def _handle_draft_end(self, _line, _offset):
        return DraftEndEvent()