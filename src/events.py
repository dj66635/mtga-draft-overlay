from dataclasses import dataclass
from .deck import Deck

@dataclass
class DraftPackEvent:
    ratings: list

@dataclass
class DraftStartEvent:
    set_code: str

@dataclass
class DraftEndEvent:
    pass

# --------

@dataclass
class DeckListEvent:
    deck: Deck

@dataclass
class DeckDrawEvent:
    drawn_grp_ids: list # (name, total, left, colors)

@dataclass
class GameEndEvent:
    pass

@dataclass
class MatchEndEvent:
    pass

# --------

@dataclass
class OppDeckSetEvent:
    deck: Deck

@dataclass
class OppDeckClearEvent:
    pass

@dataclass
class OppDeckResetEvent:
    pass

@dataclass
class OppRevealEvent:
    revealed_grp_ids: list