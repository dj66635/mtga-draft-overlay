import json
import os
import logging
from collections import Counter
from .card import Card, DBQueries
from .deck import Deck, DeckCard
from .constants import (
    DRAFT_PACK_STRING_PREMIER, 
    DRAFT_START_STRING_PREMIER, 
    DRAFT_END_STRING_PREMIER, 
    EXPANSION_CODE_REGEX
)
from .utils import detect_string
from .events import DraftPackEvent, DraftStartEvent, DraftEndEvent, DeckListEvent, DeckDrawEvent, MatchEndEvent

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

        self._json_buffer = []
        self._brace_depth = 0

        self.handlers = [
            self._handle_draft_pack,
            self._handle_draft_start,
            self._handle_draft_end,
            self._handle_decklist,
            self._handle_initial_hand, 
            self._handle_mulligan,
            self._handle_card_draw,
            self._handle_match_end
        ]

        self.deck = Deck()
        self.iid_to_grpid_cache = {}
        self.seat_id = 0
        self.pre_mulligan = None
        self.waiting_for_mulligan_discards = False
        self.initial_hand_set = False
        

    def check_log_rotation(self):
        current_size = os.path.getsize(self.arena_file_path)
        if current_size < self.arena_file_size: # file was truncated or rotated
            logger.debug("Log file smaller than last read – resetting offset to 0")
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
                # logger.debug(f"{line}")
                self.offset = log.tell()

                for handler in self.handlers:
                    if (event := handler(line)) is not None:
                        events.append(event)
        return events
    

    def _handle_draft_pack(self, line):
        if (offset := detect_string(line, [DRAFT_PACK_STRING_PREMIER])) is not None:      
            ratings = []
            try:
                cards = []
                draft_data = json.loads(line[offset:])
                card_ids = str(draft_data["PackCards"]).split(",")
                cards = [self.ratings_db_handle.get_card(c_id) for c_id in card_ids]
                cards.sort(key=lambda c: c.sort_by_draft_criteria())
                logger.debug(f"P{draft_data['SelfPack']}-P{draft_data['SelfPick']}:\n{Card.list_to_string(cards)}\n")
                ratings = [card.rating for card in cards]
            except Exception as error:
                logger.exception(f"_handle_draft_pack: {error}")

            return DraftPackEvent(ratings=ratings)
        return None
    

    def _handle_draft_start(self, line):
        if detect_string(line, [DRAFT_START_STRING_PREMIER]) is not None:
            set_code = EXPANSION_CODE_REGEX.search(line)
            if set_code:
                return DraftStartEvent(set_code=set_code.group())
        return None
        

    def _handle_draft_end(self, line):
        if detect_string(line, [DRAFT_END_STRING_PREMIER]) is not None:
            return DraftEndEvent()
        return None
    
    
    def _handle_decklist(self, line):
        # TODO: BO3 EVENT
        try:
            raw_cards = None

            if (messages := self.__parse_json_game_state_msgs(line)) is None: return None

            for msg in messages:
                self.__update_seat_id(msg)

                if (connect_resp := msg.get("connectResp")):
                    raw_cards = connect_resp.get("deckMessage").get("deckCards")

            if raw_cards is None:
                return None

            counts = Counter(raw_cards)
            deck_cards = [DeckCard(self.ratings_db_handle.get_card(card_id), count) for card_id, count in counts.items()]
            self.deck = Deck(deck_cards)
            return DeckListEvent(self.deck)
        
        except Exception:
            return None
    

    def _handle_mulligan(self, line):
        try: 
            if (log_entry := self.__accumulate_json(line)) is not None:
                payload = log_entry.get("payload")

                if payload is not None:
                    mulligan_resp = payload.get("mulliganResp")
                    if mulligan_resp is not None:
                        decision = mulligan_resp.get("decision")
                        if decision is not None:
                            if decision == "MulliganOption_Mulligan":
                                self.waiting_for_mulligan_discards = True

                            if decision == "MulliganOption_AcceptHand":               
                                self.initial_hand_set = True # no need to keep updating, just (possibly) waiting to commit

                                if not self.waiting_for_mulligan_discards:
                                    logger.debug("Initial hand set\n")
                                    return DeckDrawEvent(self.pre_mulligan)
                
                    group_resp = payload.get("groupResp")
                    if group_resp is not None:
                        groups = group_resp.get("groups")
                        if groups is not None:
                            iids = groups[0].get("ids")
                            if iids is not None:
                                logger.debug("Initial hand set (after mulligan)\n")
                                hand_grp_ids = [self.iid_to_grpid_cache.get(iid) for iid in iids if iid in self.iid_to_grpid_cache]
                                return DeckDrawEvent(hand_grp_ids)
                
                return None
            
        except Exception:
            return None
        
        
    def _handle_initial_hand(self, line):
        try:
            if self.initial_hand_set: return None
            hand_grp_ids = []

            if (messages := self.__parse_json_game_state_msgs(line)) is None: return None
            
            for msg in messages:
                self.__update_seat_id(msg)
                if (game_state := msg.get("gameStateMessage")):
                    self.__update_iid_cache(game_state)
                        
                    for zone in game_state.get("zones", []):
                        if zone.get("type") == "ZoneType_Hand" and zone.get("ownerSeatId") == self.seat_id:
                            object_iids = zone.get("objectInstanceIds")
                            if object_iids:
                                hand_grp_ids = [self.iid_to_grpid_cache.get(iid) for iid in object_iids if iid in self.iid_to_grpid_cache]

            if hand_grp_ids != []:
                self.pre_mulligan = hand_grp_ids

            return None
        
        except Exception:
            return None
    

    def _handle_card_draw(self, line):
        try:
            drawn_grp_ids = []

            if (messages := self.__parse_json_game_state_msgs(line)) is None: return None

            for msg in messages:
                self.__update_seat_id(msg)
                if (game_state := msg.get("gameStateMessage")):
                    self.__update_iid_cache(game_state)

                    # zone map to decide on "Put" events
                    zone_map = {}
                    for zone in game_state.get("zones", []):
                        zone_map[zone.get("zoneId")] = zone.get("type")

                    # Scan annotations for draws or puts from library to hand
                    for annotation in game_state.get("annotations", []):
                        if "AnnotationType_ZoneTransfer" not in annotation.get("type", []):
                            continue

                        for detail in annotation.get("details", []):
                            key = detail.get("key")
                            if key == "zone_src":
                                zone_src = detail.get("valueInt32", [None])[0]
                            elif key == "zone_dest":
                                zone_dest = detail.get("valueInt32", [None])[0]
                            elif key == "category":
                                category = detail.get("valueString", [None])[0]
                        
                        src_type = zone_map.get(zone_src)
                        dest_type = zone_map.get(zone_dest)

                        if src_type == "ZoneType_Library" and dest_type == "ZoneType_Hand" and category in ("Draw", "Put"):
                            affected = annotation.get("affectedIds", [])
                            if affected:
                                grp_id = self.iid_to_grpid_cache.get(affected[0])
                                if grp_id is not None:
                                    drawn_grp_ids.append(grp_id)

            if drawn_grp_ids == []:
                return None                     
            return DeckDrawEvent(drawn_grp_ids)
        
        except Exception:
            return None
 

    def __reset_state(self):
        self.iid_to_grpid_cache = {}
        self.seat_id = 0
        self.pre_mulligan = None
        self.waiting_for_mulligan_discards = False
        self.initial_hand_set
    
    def _handle_match_end(self, line):
        try:
            if (messages := self.__parse_json_game_state_msgs(line)) is None:
                return None
            
            for msg in messages:
                if msg.get("type") == "GREMessageType_IntermissionReq":
                    intermission = msg.get("intermissionReq", {})
                    result = intermission.get("result")
                    if result:
                        logger.debug("Match ended\n")
                        self.__reset_state()
                        return MatchEndEvent()
            return None
        
        except Exception:
            return None
    

    def __parse_json_game_state_msgs(self, line):
        try:
            log_entry = json.loads(line)
            gre_event = log_entry.get("greToClientEvent")
            return gre_event.get("greToClientMessages")
        except Exception:
            return None
    
    def __update_seat_id(self, gre_event):
        if gre_event.get("type") == "GREMessageType_GameStateMessage":
            if (seat_ids := gre_event.get("systemSeatIds")):
                if self.seat_id != seat_ids[0]:
                    self.seat_id = seat_ids[0]
                    logger.debug(f"Seat ID: {self.seat_id}\n")
                    

    def __update_iid_cache(self, game_state):
        for obj in game_state.get("gameObjects", []):
            iid = obj.get("instanceId")
            grp_id = obj.get("grpId")
            if iid is not None and grp_id is not None:
                self.iid_to_grpid_cache[iid] = grp_id


    def __accumulate_json(self, line):
        stripped = line.strip()

        # If we're not currently buffering
        if self._brace_depth == 0:
            if not stripped.startswith("{"):
                return None  # Not JSON
            self._json_buffer = []
        
        # Count braces
        self._brace_depth += stripped.count("{")
        self._brace_depth -= stripped.count("}")

        self._json_buffer.append(line)

        # If balanced → complete JSON object
        if self._brace_depth == 0 and self._json_buffer:
            full_json = "".join(self._json_buffer)
            self._json_buffer = []

            try:
                return json.loads(full_json)
            except json.JSONDecodeError:
                return None

        return None