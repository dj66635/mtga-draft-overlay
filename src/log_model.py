class LogEntry:
    def __init__(self, text=None, json=None):
        self.text = text
        self.json = json


class ArenaEntry: # TODO: should be splitted into three classes
    def __init__(self, raw: dict):
        self.raw = raw

    # ---------- Top-level fields ----------
    # @property
    # def transaction_id(self):
    #     return self.raw.get("transactionId")

    # @property
    # def request_id(self):
    #     return self.raw.get("requestId")

    # @property
    # def timestamp(self):
    #     return self.raw.get("timestamp")

    # ---------- GRE messages ----------
    @property
    def gre_messages(self):
        event = self.raw.get("greToClientEvent")
        if not event:
            return []

        messages = event.get("greToClientMessages", [])
        return [GREMessage(m) for m in messages]
    
    # -------- Client messages --------
    @property
    def client_payload(self):
        payload = self.raw.get("payload")
        if payload:
            return ClientPayload(payload)
        return None
    
    # -------- Draft messages ---------
    @property
    def self_pick(self):
        return self.raw.get("SelfPick")
    
    @property
    def self_pack(self):
        return self.raw.get("SelfPack")

    @property
    def pack_cards(self):
        return self.raw.get("PackCards")


# ArenaEntry.ClientPayload
class ClientPayload:
    def __init__(self, raw: dict):
        self.raw = raw
    
    def mulligan_decision(self):
        mulligan_resp = self.raw.get("mulliganResp")
        if mulligan_resp:
            return mulligan_resp.get("decision")
        return None
        
    def group_response(self):
        group_resp = self.raw.get("groupResp")
        if group_resp:
            groups = group_resp.get("groups", [])
            for group in groups:
                if group.get("zoneType") == "ZoneType_Hand":
                    return group.get("ids", [])
        return None

    def deck_list(self):
        submit_deck_resp = self.raw.get("submitDeckResp")
        if submit_deck_resp:
            deck = submit_deck_resp.get("deck")
            if deck:
                return deck.get("deckCards", [])
        return None
                

# ArenaEntry.GREMessage
class GREMessage:
    def __init__(self, raw: dict):
        self.raw = raw

    @property
    def type(self):
        return self.raw.get("type")

    @property
    def system_seat_ids(self):
        return self.raw.get("systemSeatIds", [])
    
    @property
    def my_seat_id(self):
        seats = self.system_seat_ids
        return seats[0] if seats else None
    
    # @property
    # def msg_id(self):
    #     return self.raw.get("msgId")

    # @property
    # def game_state_id(self):
    #     return self.raw.get("gameStateId")

    # ---------- GameStateMessage ----------
    @property
    def game_state(self):
        gsm = self.raw.get("gameStateMessage")
        if gsm:
            return GameStateMessage(gsm)
        return None

    # ---------- ConnectResponse ----------
    @property
    def connect_resp(self):
        connect_resp = self.raw.get("connectResp")
        if connect_resp:
            return ConnectResponse(connect_resp)
        return None
    
    # Just for game end: intermissionReq -> result
    def result(self):
        intermission_req = self.raw.get("intermissionReq")
        if intermission_req:
            return intermission_req.get("result")
        return None
    

# GREMessage.ConnectResponse
class ConnectResponse:
    def __init__(self, raw: dict):
        self.raw = raw

    def deck_list(self):
        deck_message = self.raw.get("deckMessage")
        if deck_message:
            return deck_message.get("deckCards")
        return None


# GREMessage.GameStateMessage
class GameStateMessage:
    def __init__(self, raw: dict):
        self.raw = raw

    @property
    def type(self):
        return self.raw.get("type")

    @property
    def zones(self):
        zones = self.raw.get("zones", [])
        return [Zone(z) for z in zones]

    @property
    def game_objects(self):
        return self.raw.get("gameObjects", [])

    @property
    def annotations(self):
        annotations = self.raw.get("annotations", [])
        return [Annotation(a) for a in annotations]

    # @property
    # def turn_info(self):
    #     return self.raw.get("turnInfo")

    # @property
    # def players(self):
    #     return self.raw.get("players", [])

    # @property
    # def actions(self):
    #     return self.raw.get("actions", [])
    

# GREMessage.GameStateMessage.Zone
class Zone:
    def __init__(self, raw: dict):
        self.raw = raw

    @property
    def zone_id(self):
        return self.raw.get("zoneId")
    
    @property
    def type(self):
        return self.raw.get("type")
    
    @property
    def owner_seat_id(self):
        return self.raw.get("ownerSeatId")
    
    @property
    def object_instance_ids(self):
        return self.raw.get("objectInstanceIds", [])


# GREMessage.GameStateMessage.Annotation
class Annotation:
    def __init__(self, raw: dict):
        self.raw = raw
    
    @property
    def affected_ids(self):
        return self.raw.get("affectedIds", [])

    @property
    def type(self):
        type = self.raw.get("type", [])
        return type[0] if type else None
    
    @property
    def details(self):
        details = self.raw.get("details", [])
        return [AnnotationDetails(d) for d in details]


# GREMessage.GameStateMessage.Annotation.Detail
class AnnotationDetails:
    def __init__(self, raw: dict):
        self.raw = raw
    
    @property
    def key(self):
        return self.raw.get("key")
    
    @property
    def type(self):
        return self.raw.get("type")
    
    @property
    def value_int32(self):
        value_int32 = self.raw.get("valueInt32", [])
        return value_int32[0] if value_int32 else None
    
    @property
    def value_string(self):
        value_string = self.raw.get("valueString", [])
        return value_string[0] if value_string else None