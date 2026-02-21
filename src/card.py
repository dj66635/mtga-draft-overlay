
class Card:
    def __init__(self, GrpId, Name, Rarity, IsLand, Colors, CollectorNumber, ExpansionCode, Rating):
        self.GrpId = GrpId
        self.Name = Name
        self.Rarity = Rarity # 0: token, 1: land, 2: common, 3: uncommon, 4: rare, 5: mythic
        self.IsLand = bool(IsLand) # 1: land ; 0: non-land
        self.Colors = str(Colors).strip() if Colors is not None else None  # e.g. "1,3,4"; "2"; ""
        self.CollectorNumber = CollectorNumber
        self.ExpansionCode = ExpansionCode
        self.Rating = Rating

    # ----- The problem with lands ------
    # Take TDM Evolving Wilds: rarity 2. Goes after Dismal Backwater, and before Scoured Barrens. 
    # It means we could count its rarity as 1, but should we then downgrade rare lands' rarity by one as well?
    # Does not look like from other samples. So we'll actually move rarity 1 ("land rarity") up one bracket (normalized_rarity())
    # Now all regular lands are common and that could intefere with the color bucket ordering
    # So we keep track of IsLand attribute to put them at the end, and just order by CollectorNumber among them
    # Effectively, being a land can be though of as a "color class" in itself, that goes last in the bracket
    def color_class(self):
        # WUBRG (1-5), Color-less (6), Multi-color (7), Land (8)
        if self.IsLand: return 8
        if not self.Colors: return 6
        if "," in self.Colors: return 7
        try: 
            return int(self.Colors)
        except ValueError:
            return 6
    
    def normalized_rarity(self):
        if self.IsLand and self.Rarity == 1: return self.Rarity + 1
        return self.Rarity
    
    def __lt__(self, other):
        # 1. Rarity (upgrading regular lands to common)
        # 2. Color class (including "land" class last)
        # 3. Collector Number (not GrpId since that won't work cross-expansion, like bonus sheets and SPGs)
        if self.normalized_rarity() != other.normalized_rarity():
            return self.Rarity > other.Rarity
        if self.color_class() != other.color_class(): 
            # WUBRG, then color-less, then multi-color, then lands
            return self.color_class() < other.color_class() 
        return self.CollectorNumber < other.CollectorNumber
    

    def __str__(self):
        return (f"Card(GrpId='{self.GrpId}', Name='{self.Name}', Rarity='{self.Rarity}', IsLand='{self.IsLand}', Colors='{self.Colors}', "
                f"CollectorNumber='{self.CollectorNumber}', ExpansionCode='{self.ExpansionCode}', Rating='{self.Rating}')")

    def __repr__(self):
        return self.__str__()  
    
    @staticmethod
    def list_to_string(card_list): # ensures list printing looks nice
        return "\n".join(str(card) for card in card_list)