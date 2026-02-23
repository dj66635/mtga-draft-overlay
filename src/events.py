from dataclasses import dataclass

@dataclass
class DraftPackEvent:
    ratings: list

@dataclass
class DraftStartEvent:
    set_code: str

@dataclass
class DraftEndEvent:
    pass