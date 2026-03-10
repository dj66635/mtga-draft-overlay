import sqlite3 
import re
from .constants import TOKEN_TO_COLOR, COLOR_ORDER_TO_LIST, RATINGS_DB_PATH

class Card:
    def __init__(self, grp_id, name, rarity, is_land, color_order, old_school_mana_text, types, collector_number, expansion_code, rating):
        self.grp_id = grp_id
        self.name = name
        self.rarity = rarity # 0: token, 1: land, 2: common, 3: uncommon, 4: rare, 5: mythic
        self.is_land = bool(is_land) # 1: land ; 0: non-land
        self.color_order = color_order
        self.old_school_mana_text = old_school_mana_text
        self.types = [int(t.strip()) for t in types.split(",") if t.strip()] # 1: artifact, 2: creature, 3: enchantment, 4: instant, 5: land, 8: planeswalker, 10: sorcery, 11: kindred, 14: battle
        self.collector_number = collector_number
        self.expansion_code = expansion_code
        self.rating = rating
    
    def cost(self):
        tokens = re.findall(r'o(\([^)]+\)|[^o]+)', self.old_school_mana_text)
        result = []
        for t in tokens:
            t = t.strip()
            # remove parentheses if present
            if t.startswith("(") and t.endswith(")"):
                t = t[1:-1]
            # oX treated as 0 colorless
            if t.upper() == "X":
                result.append((TOKEN_TO_COLOR['C'], 0))
            # hybrid number/color inside parentheses: 2/G -> take letter after slash
            elif "/" in t:
                color_part = t.split("/")[-1].upper()
                result.append((TOKEN_TO_COLOR[color_part], 1))
            # numeric token => colorless
            elif t.isdigit():
                result.append((TOKEN_TO_COLOR['C'], int(t)))
            # single color
            elif t.upper() in TOKEN_TO_COLOR:
                result.append((TOKEN_TO_COLOR[t.upper()], 1))
            else:
                continue
        return result

    def cmc(self):
        return sum(count for _, count in self.cost())
    
    def colors(self):
        return COLOR_ORDER_TO_LIST[self.color_order]
        
    def sort_by_draft_criteria(self):
        return (
            -self.rarity,          # higher rarity first
            self.is_land,          # False (0) before True (1)
            self.color_order,
            self.collector_number
        )
    
    def sort_by_cost(self):
        return (
            self.cmc(),
            self.color_order,
            self.collector_number
        )

    def __repr__(self):
        # Automatically include all instance attributes
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"
    
    @staticmethod
    def list_to_string(card_list): # ensures list printing looks nice
        return "\n".join(str(card) for card in card_list)


class DBQueries:
    def __init__(self):
        self.ratings_db_path = RATINGS_DB_PATH

    def get_card(self, card_id):
        conn = sqlite3.connect(self.ratings_db_path)
        cur = conn.cursor()

        cur.execute("SELECT * FROM Cards WHERE GrpId = ?", (card_id,))
        (grp_id, name, rarity, is_land, color_order, old_school_mana_text, types, collector_number, expansion_code, rating) = cur.fetchone()

        conn.close()
        if grp_id and name:
            return Card(grp_id, name, rarity, is_land, color_order, old_school_mana_text, types, collector_number, expansion_code, rating)
        else:
            return None
        
    def get_card_by_name(self, card_name):
        conn = sqlite3.connect(self.ratings_db_path)
        cur = conn.cursor()

        cur.execute("SELECT * FROM Cards WHERE Name = ?", (card_name,)) # we dont care if theres more than one...
        (grp_id, name, rarity, is_land, color_order, old_school_mana_text, types, collector_number, expansion_code, rating) = cur.fetchone()

        conn.close()
        if grp_id and name:
            return Card(grp_id, name, rarity, is_land, color_order, old_school_mana_text, types, collector_number, expansion_code, rating)
        else:
            return None
        