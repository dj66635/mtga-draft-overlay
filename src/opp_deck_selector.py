import tkinter as tk
from pathlib import Path

from .overlay import BaseOverlay
from .deck import Deck
from .events import OppDeckSetEvent, OppDeckClearEvent, OppDeckResetEvent
from .utils import shorten
from .constants import DECKS_PATH, TRANSPARENT_COLOR, FONTS


class OppDeckSelector(BaseOverlay):   
    def __init__(self, x=0, y=0, callback=None):   
        super().__init__(TRANSPARENT_COLOR, x, y)
        self.opp_deck_callback = callback
        
        self.selector_frame = tk.Frame(self.window, bg=TRANSPARENT_COLOR)
        self.selector_button = tk.Button(self.selector_frame, 
                                         text = "▶ Select Deck", 
                                         bg = "lightgrey",
                                         fg = "black",
                                         font = FONTS["deck_label"],
                                         relief = "raised",
                                         width = 19,
                                         anchor = "w",
                                         bd = 2,
                                         command = self.toggle_decklist)
        self.decklist_frame = tk.Frame(self.window, bg=TRANSPARENT_COLOR)

        self.selector_frame.pack(anchor="w")
        self.selector_button.pack(anchor="w")

        self.current_deck = None
        self.decklists = []
        self.get_available_decklists()
        self.set_decklist_buttons()


    def get_available_decklists(self):
        for deck_path in Path(DECKS_PATH).glob("*.dck"):
            with open(deck_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
                deck = Deck.from_text(text)
                self.decklists.append(deck)


    def set_decklist_buttons(self):
        self.decklist_frame.pack(anchor="w")
        self.decklist_frame.pack_forget()
        # for widget in self.decklist_frame.winfo_children():
        #    widget.destroy()
        clear = tk.Button(self.decklist_frame, 
                            text = "Clear", bg = "grey", fg = "white", font = FONTS["deck_label"],
                            relief = "flat", width = 18, anchor = "w", bd = 1,
                            command = lambda: self.clear_deck())
        clear.pack(padx=5, pady=0)
        reset = tk.Button(self.decklist_frame, 
                            text = "Reset", bg = "grey", fg = "white", font = FONTS["deck_label"],
                            relief = "flat", width = 18, anchor = "w", bd = 1,
                            command = lambda: self.reset_decks())
        reset.pack(padx=5, pady=0)
        for deck in self.decklists:
            btn = tk.Button(self.decklist_frame, 
                            text = shorten(deck.name), bg = "lightgrey", fg = "black", font = FONTS["deck_label"],
                            relief = "flat", width = 18, anchor = "w", bd = 1,
                            command = lambda d=deck: self.select_deck(d))
            btn.pack(padx=5, pady=0)


    def toggle_decklist(self):
        if self.decklist_frame.winfo_ismapped():
            self.decklist_frame.pack_forget()
            self.selector_button.config(text="▶ Select Deck")
        else:
            self.decklist_frame.pack(anchor="w")
            self.selector_button.config(text="▼ Select Deck")


    def select_deck(self, deck):
        self.decklist_frame.pack_forget()
        self.selector_button.config(text=f" {shorten(deck.name)}",
                                    bg = "lightgrey",
                                    fg = "black",
                                    font = FONTS["deck_label"])
        self.opp_deck_callback(OppDeckSetEvent(deck))
    
    def clear_deck(self):
        self.opp_deck_callback(OppDeckClearEvent())

    def reset_decks(self):
        for deck in self.decklists:
            deck.reset_count()
        self.opp_deck_callback(OppDeckResetEvent())

    # --------------------------------------------------
