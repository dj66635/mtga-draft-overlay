import sqlite3 


class Card:
    def __init__(self, grp_id, name, rarity, is_land, color_order, colors, collector_number, expansion_code, rating):
        self.grp_id = grp_id
        self.name = name
        self.rarity = rarity  # 0: token, 1: land, 2: common, 3: uncommon, 4: rare, 5: mythic
        self.is_land = bool(is_land)  # 1: land ; 0: non-land
        self.color_order = color_order
        self.colors = str(colors).strip() if colors is not None else None  # e.g. "1,3,4"; "2"; ""
        self.collector_number = collector_number
        self.expansion_code = expansion_code
        self.rating = rating
    
    def __lt__(self, other):
        if self.rarity != other.rarity:
            return self.rarity > other.rarity
        if self.is_land != other.is_land:
            return self.is_land < other.is_land
        if self.color_order != other.color_order: 
            return self.color_order < other.color_order
        return self.collector_number < other.collector_number
    

    def __str__(self):
        return (
            f"Card(grp_id='{self.grp_id}', name='{self.name}', rarity='{self.rarity}', "
            f"is_land='{self.is_land}', color_order='{self.color_order}', colors='{self.colors}', "
            f"collector_number='{self.collector_number}', expansion_code='{self.expansion_code}', "
            f"rating='{self.rating}')"
        )

    def __repr__(self):
        return self.__str__()  
    
    @staticmethod
    def list_to_string(card_list): # ensures list printing looks nice
        return "\n".join(str(card) for card in card_list)
    

class DBQueries:
    def __init__(self, ratings_db_path):
        self.ratings_db_path = ratings_db_path

    def get_card(self, card_id):
        conn = sqlite3.connect(self.ratings_db_path)
        cur = conn.cursor()

        cur.execute("SELECT * FROM Cards WHERE GrpId = ?", (card_id,))
        (grp_id, name, rarity, is_land, color_order, colors, collector_number, expansion_code, rating) = cur.fetchone()

        conn.close()
        if grp_id and name:
            return Card(grp_id, name, rarity, is_land, color_order, colors, collector_number, expansion_code, rating)
        else:
            return None