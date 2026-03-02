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
from .log_model import LogEntry, GREEntry, DraftEntry, ClientEntry

logger = logging.getLogger(__name__)


class MatchContext:
    def __init__(self):
        self.deck = Deck()
        self.iid_to_grpid = {}
        self.seat_id = 0
        self.initial_hand_set = False
        self.pre_mulligan_hand = None
        self.mulliganed = False
        

class ArenaScanner:
    def __init__(self, arena_file_path, ratings_db_path):
        self.arena_file_path = arena_file_path
        self.arena_file_size = os.path.getsize(self.arena_file_path)

        self.ratings_db_path = ratings_db_path
        self.ratings_db_handle = DBQueries(self.ratings_db_path)

        with open(self.arena_file_path, "r", encoding="utf-8", errors="replace") as f: # avoid processing the whole file
            f.seek(0, 2) 
            self.offset = f.tell()

        self._json_buffer = None

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

        self.context = MatchContext()
        

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

                entry = self.read_entry(line)
                if entry:
                    for handler in self.handlers:
                        if (event := handler(entry)) is not None:
                            events.append(event)
        return events
    

    def read_entry(self, line: str):
        """
        Read a single log line. Handles:
        - Plain text lines
        - JSON lines (single-line or multi-line pretty-printed)
        - Lines with a text prefix before JSON
        """

        # If we're currently accumulating a multi-line JSON, append this line
        if self._json_buffer is not None:
            self._json_buffer.append(line)
            json_text = "\n".join(self._json_buffer)
            try:
                json_obj = json.loads(json_text)
                self._json_buffer = None
                return LogEntry(json=json_obj)
            except json.JSONDecodeError:
                # JSON not complete yet
                return None

        # Not currently accumulating JSON: check if line contains JSON start
        start_idx = line.find("{") # min((i for i in (line.find("{")) if i != -1), default=-1)

        if start_idx == -1:
            # Case 0: no JSON at all
            return LogEntry(text=line)
    
        if start_idx >= 0:
            prefix = line[:start_idx].rstrip()
            json_part = line[start_idx:]
            try:
                json_obj = json.loads(json_part)
                return LogEntry(json=json_obj, text=prefix)
            except json.JSONDecodeError:
                # could be multi-line
                self._json_buffer = [line]
                return LogEntry(text=prefix)
        
        return None


    def _handle_draft_pack(self, entry: LogEntry):
        if entry.text and detect_string(entry.text, [DRAFT_PACK_STRING_PREMIER]):
            draft_entry = DraftEntry(entry.json)
            if draft_entry.pack_cards:
                cards = [self.ratings_db_handle.get_card(grp_id) 
                         for grp_id in draft_entry.pack_cards.split(",")]
                cards.sort(key=lambda c: c.sort_by_draft_criteria())
                logger.debug(f"P{draft_entry.self_pack}-P{draft_entry.self_pick}:\n{Card.list_to_string(cards)}: {entry.json}")
                return DraftPackEvent(ratings=[card.rating for card in cards])
        return None
    

    def _handle_draft_start(self, entry: LogEntry):
        if entry.text and detect_string(entry.text, [DRAFT_START_STRING_PREMIER]):
            request = entry.json.get("request")
            if request:
                set_code = EXPANSION_CODE_REGEX.search(request) # its a json with backslashes...
                if set_code:
                    return DraftStartEvent(set_code=set_code.group())
        return None
        

    def _handle_draft_end(self, entry: LogEntry):
        if entry.text and detect_string(entry.text, [DRAFT_END_STRING_PREMIER]):
            return DraftEndEvent()
        return None
    

    def _handle_decklist(self, entry: LogEntry):
        if entry.json:
            deck_list = []
            gre_entry = GREEntry(entry.json)
            for msg in gre_entry.gre_messages:
                self.update_seat_id(msg)

                if msg.connect_resp and msg.connect_resp.deck_list():   
                    deck_list = msg.connect_resp.deck_list()            
            
            # BO3
            client_entry = ClientEntry(entry.json)
            if client_entry.client_payload and client_entry.client_payload.deck_list():
                deck_list = client_entry.client_payload.deck_list()

            if deck_list:    
                counts = Counter(deck_list)
                deck_cards = [DeckCard(self.ratings_db_handle.get_card(grp_id), count) for grp_id, count in counts.items()]
                self.context.deck = Deck(deck_cards)
                logger.debug(f"Deck loaded\n {self.context.deck}: {entry.json}\n") # TODO: print deck
                return DeckListEvent(self.context.deck)
        return None
    

    def _handle_mulligan(self, entry: LogEntry):
        if entry.json:
            client_entry = ClientEntry(entry.json)
            payload = client_entry.client_payload
            if payload:
                if payload.mulligan_decision() == "MulliganOption_Mulligan":
                    self.context.mulliganed = True

                elif payload.mulligan_decision() == "MulliganOption_AcceptHand":
                    self.context.initial_hand_set = True
                    if not self.context.mulliganed:
                        logger.debug(f"Initial hand set {self.context.pre_mulligan_hand}: {entry.json}")
                        return DeckDrawEvent(self.context.pre_mulligan_hand)
            
                if self.context.mulliganed and payload.group_response():
                    hand_grpids = [self.context.iid_to_grpid.get(iid) # heres where we actually need the cache
                                    for iid in payload.group_response()
                                    if iid in self.context.iid_to_grpid]
                    logger.debug(f"Initial hand set (after mulligan) {hand_grpids}: {entry.json}")
                    return DeckDrawEvent(hand_grpids)
        return None
        

    def _handle_initial_hand(self, entry: LogEntry):
        if entry.json and not self.context.initial_hand_set:
            gre_entry = GREEntry(entry.json)

            for msg in gre_entry.gre_messages:
                self.update_seat_id(msg)

                if msg.game_state:
                    self.update_iid_cache(msg.game_state)

                    for zone in msg.game_state.zones:
                        if zone.type == "ZoneType_Hand" and zone.owner_seat_id == self.context.seat_id:
                            hand_grpids = [self.context.iid_to_grpid.get(iid) 
                                            for iid in zone.object_instance_ids
                                            if iid in self.context.iid_to_grpid]
                            if hand_grpids:
                                self.context.pre_mulligan_hand = hand_grpids 
                                # hand may be mulliganed, cannot commit yet
        return None         
    

    def _handle_card_draw(self, entry: LogEntry):
        if entry.json:
            drawn_grpids = []
            gre_entry = GREEntry(entry.json)

            for msg in gre_entry.gre_messages:
                self.update_seat_id(msg)

                if msg.game_state:
                    self.update_iid_cache(msg.game_state)

                    zone_map = {}
                    for zone in msg.game_state.zones:
                        if zone.owner_seat_id == self.context.seat_id:
                            zone_map[zone.zone_id] = zone.type

                    for annotation in msg.game_state.annotations: 
                        # Transfers from Library to Hand with category Draw or Put
                        if annotation.type == "AnnotationType_ZoneTransfer":
                            for detail in annotation.details:
                                if detail.key == "zone_src":
                                    zone_src = zone_map.get(detail.value_int32)

                                elif detail.key == "zone_dest":
                                    zone_dest = zone_map.get(detail.value_int32)

                                elif detail.key == "category":
                                    category = detail.value_string
 
                            # there could be more than one annotation with events so do not return here
                            if zone_src == "ZoneType_Library" and zone_dest == "ZoneType_Hand" and category in ("Draw", "Put"):
                                drawn_grpids.extend(self.context.iid_to_grpid.get(iid) 
                                                    for iid in annotation.affected_ids 
                                                    if iid in self.context.iid_to_grpid)
                                
                            if zone_src == "ZoneType_Library" and zone_dest == "ZoneType_Graveyard" and category in ("Mill"):
                                drawn_grpids.extend(self.context.iid_to_grpid.get(iid) 
                                                    for iid in annotation.affected_ids 
                                                    if iid in self.context.iid_to_grpid)
                               
            if drawn_grpids:
                return DeckDrawEvent(drawn_grpids)
        return None

    
    def _handle_match_end(self, entry: LogEntry):
        if entry.json:
            gre_entry = GREEntry(entry.json)
            for msg in gre_entry.gre_messages:
                if msg.result():
                    logger.debug(f"Match ended: {entry.json}")
                    self.context = MatchContext()
                    return MatchEndEvent()
        return None


    def update_seat_id(self, gre_event):
        if gre_event.type == "GREMessageType_GameStateMessage":
            new_seat_id = gre_event.my_seat_id
            if new_seat_id is not None and self.context.seat_id != new_seat_id:
                self.context.seat_id = new_seat_id
                logger.debug(f"Seat ID updated {self.context.seat_id}")


    def update_iid_cache(self, game_state):
        for obj in game_state.game_objects:
            if obj.instance_id is not None and obj.grp_id is not None:
                self.context.iid_to_grpid[obj.instance_id] = obj.grp_id