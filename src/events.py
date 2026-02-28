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

@dataclass
class DeckListEvent:
    deck: Deck
    # creatures: list  # (name, total, left, colors)
    # spells: list
    # lands: list

@dataclass
class DeckDrawEvent:
    drawn_grp_ids: list # (name, total, left, colors)

@dataclass
class MatchEndEvent:
    pass