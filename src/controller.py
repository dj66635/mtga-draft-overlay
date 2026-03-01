import tkinter as tk
import logging

from .scanner import ArenaScanner
from .draft_overlay import DraftOverlay
from .deck_overlay import DeckOverlay
from .events import (
    DraftPackEvent,
    DraftStartEvent,
    DraftEndEvent,
    DeckListEvent,
    DeckDrawEvent,
    MatchEndEvent,
)
from .constants import (
    ARENA_FILE_PATH, 
    RATINGS_DB_PATH, 
    TRANSPARENT_COLOR,
    FONTS
)

logger = logging.getLogger(__name__)


class OverlayController:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # controller doesn't render anything

        self.scanner = ArenaScanner(ARENA_FILE_PATH, RATINGS_DB_PATH)

        self._create_controls()

        self.draft_overlay = DraftOverlay()
        self.deck_overlay = DeckOverlay()

        self.root.after(100, self._tick)

    # -----------------------------

    def _create_controls(self):
        self.controls = tk.Toplevel(self.root)
        self.controls.overrideredirect(True)
        self.controls.attributes("-topmost", True)
        self.controls.configure(bg=TRANSPARENT_COLOR)
        self.controls.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.controls.geometry("80x40+0+-10")

        self.toggle_btn = tk.Button(
            self.controls,
            text="👁️",
            font=FONTS["emoji"],
            command=self.toggle_overlays,
            bd=0
        )
        self.toggle_btn.pack(side="left")

        self.exit_btn = tk.Button(
            self.controls,
            text="❌",
            font=FONTS["emoji"],
            command=self.shutdown,
            bd=0
        )
        self.exit_btn.pack(side="left")


    def toggle_overlays(self):
        if self.draft_overlay:
            self.draft_overlay.toggle()

        if self.deck_overlay:
            self.deck_overlay.toggle()

    def shutdown(self):
        if self.deck_overlay:
            self.deck_overlay.destroy()

        if self.draft_overlay:
            self.draft_overlay.destroy()

        self.controls.destroy()
        self.root.destroy()

    # -----------------------------

    def _tick(self):
        for event in self.scanner.poll_events():
            self._handle_event(event)

        self.root.after(100, self._tick)

    # -----------------------------

    def _handle_event(self, event):
        if isinstance(event, DraftPackEvent):
            logger.info(f"Ratings: {event.ratings}")
            self.draft_overlay.show_ratings(event.ratings)

        elif isinstance(event, DraftStartEvent):
            logger.info(f"Draft started: {event.set_code}")

        elif isinstance(event, DraftEndEvent):
            logger.info("Draft ended")
            self.draft_overlay.clear()

        elif isinstance(event, DeckListEvent):
            logger.info("Deck loaded")
            self.deck_overlay.load_deck(event.deck)

        elif isinstance(event, DeckDrawEvent):
            logger.info(f"Drawn {event.drawn_grp_ids}")
            for grp_id in event.drawn_grp_ids:  
                self.scanner.context.deck.draw_card(grp_id)
                self.deck_overlay.card_drawn(grp_id)

        elif isinstance(event, MatchEndEvent):
            logger.info("Match ended")
            self.deck_overlay.clear()

    # -----------------------------

    def start(self):
        self.root.mainloop()


def start_overlay():
    controller = OverlayController()
    controller.start()