from .utils import shorten
from .card import DBQueries
from .constants import COLOR_TO_HEX

class Deck:
    def __init__(self, name=None, cards=None):
        self.name = name
        self.cards = cards or []

    def draw_card(self, card_id, sideboard=False, amount=1):
        card = self.get_card_by_id(card_id, sideboard)
        if card:
            card.draw(amount)

    def get_card_by_id(self, card_id, sideboard):
        for dc in self.cards:
            if dc.is_my_id(card_id) and dc.sideboard == sideboard:
                return dc
        return None

    def reset_count(self):
        for card in self.cards:
            card.left = card.total


    def grouped_for_overlay(self):
        sorted_cards = sorted(self.cards, key=lambda dc: dc.card.sort_by_cost())
        creatures = [dc.printable() for dc in sorted_cards if not dc.sideboard and 2 in dc.card.types]
        spells    = [dc.printable() for dc in sorted_cards if not dc.sideboard and 2 not in dc.card.types and not dc.card.is_land]
        lands     = [dc.printable() for dc in sorted_cards if not dc.sideboard and dc.card.is_land]
        sideboard = [dc.printable() for dc in sorted_cards if dc.sideboard]
        return creatures, spells, lands, sideboard
    
    def __repr__(self):
        return (f"< {self.name or 'Deck'}: [{', '.join(f'{dc.card.name}: {dc.total}' for dc in self.cards if not dc.sideboard)}]"
                f" - Sideboard: [{', '.join(f'{dc.card.name}: {dc.total}' for dc in self.cards if dc.sideboard)}] >")

    @classmethod
    def from_text(cls, text: str):
        deck_cards = []
        section = "deck" # by default if no "Deck" label exists

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue
            if line == "Deck":
                section = "deck"
                continue
            if line == "Sideboard":
                section = "sideboard"
                continue
            if line.startswith("Name "):
                name = line.replace("Name ", "").strip()
                continue

            if section in ("deck", "sideboard"):
                parts = line.split(" ", 1)
                if len(parts) != 2:
                    continue

                count = int(parts[0])
                card_name = parts[1]

                cards = DBQueries().get_card_by_name(card_name)
                if cards:
                    deck_cards.append(DeckCard(cards[0], count, section == "sideboard", alts=cards[1:]))

        return Deck(name, deck_cards)


class DeckCard:
    def __init__(self, card, total, sideboard=False, alts=[]):
        self.card = card
        self.total = total
        self.left = total
        self.sideboard = sideboard
        self.alts = alts # handle cards with different grp_id that are essentially the same, like lands from different expansions

    def draw(self, amount=1):
        self.left = max(self.left - amount, 0)

    def is_my_id(self, grp_id):
        for card in self.alts:
            if card.grp_id == grp_id:
                return True
        return self.card.grp_id == grp_id 
    
    def printable(self):
        return (self.card.grp_id, shorten(self.card.name), self.total, self.left, [COLOR_TO_HEX[c] for c in self.card.colors()], self.sideboard)
    
    def __repr__(self):
        return f"< {self.card} - {self.left}/{self.total} {'- Sideboard ' if self.sideboard else ''}>"