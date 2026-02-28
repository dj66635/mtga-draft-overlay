from .utils import shorten
from .constants import COLOR_TO_HEX

class Deck:
    def __init__(self, cards=None):
        self.cards = cards or []

    def draw_card(self, card_id, amount=1):
        card = self.get_card_by_id(card_id)
        if card:
            card.draw(amount)

    def get_card_by_id(self, card_id):
        for dc in self.cards:
            if dc.card.grp_id == card_id:
                return dc
        return None

    def grouped_for_overlay(self):
        sorted_cards = sorted(self.cards, key=lambda dc: dc.card.sort_by_cost())
        creatures = [dc.printable() for dc in sorted_cards if 2 in dc.card.types]
        spells = [dc.printable() for dc in sorted_cards if 2 not in dc.card.types and not dc.card.is_land]
        lands = [dc.printable() for dc in sorted_cards if dc.card.is_land]
        return creatures, spells, lands


class DeckCard:
    def __init__(self, card, total):
        self.card = card
        self.total = total
        self.left = total

    def draw(self, amount=1):
        self.left = max(self.left - amount, 0)
    
    def printable(self):
        return (self.card.grp_id, shorten(self.card.name), self.total, self.left, [COLOR_TO_HEX[c] for c in self.card.colors()])