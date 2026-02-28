import tkinter as tk
from .utils import blend_colors
from .constants import (
    DECK_HEIGHT, 
    DECK_WIDTH,
    FONTS
)
from .overlay import BaseOverlay


class DeckOverlay(BaseOverlay):
    def __init__(self):
        super().__init__(background="black")

        self.window.geometry("+0+90")
        
        self.deck = None
        self.card_text_refs = {}

        self.frame = tk.Frame(self.window, bg="black")
        self.frame.pack(padx=5, pady=5)

        self.window.bind("<ButtonPress-1>", self._start_move)
        self.window.bind("<B1-Motion>", self._on_move)
        self.window.bind("<ButtonRelease-1>", self._stop_move)

        self._drag_data = None

    # --------------------------------------------------

    def _start_move(self, event):
        self._drag_data = (
            event.x_root,
            event.y_root,
            self.window.winfo_x(),
            self.window.winfo_y(),
        )

    def _on_move(self, event):
        if not self._drag_data:
            return

        start_x, start_y, win_x, win_y = self._drag_data
        dx = event.x_root - start_x
        dy = event.y_root - start_y
        self.window.geometry(f"+{win_x + dx}+{win_y + dy}")

    def _stop_move(self, event):
        self._drag_data = None

    # --------------------------------------------------

    def _add_section(self, title, items):
        tk.Label(
            self.frame,
            text=title,
            bg="black",
            fg="white",
            font=FONTS["deck_label"],
            anchor="w",
        ).pack(fill="x", pady=(2, 2))

        for grp_id, name, total, left, colors in items:
            canvas = tk.Canvas(
                self.frame,
                width=DECK_WIDTH,
                height=DECK_HEIGHT,
                highlightthickness=0,
            )
            canvas.pack(fill="x", pady=2)

            self._draw_item(canvas, grp_id, name, total, left, colors)
            
            canvas.bind("<ButtonPress-1>", self._start_move)
            canvas.bind("<B1-Motion>", self._on_move)
            canvas.bind("<ButtonRelease-1>", self._stop_move)

    # --------------------------------------------------

    def load_deck(self, deck):
        self.deck = deck
        
        for widget in self.frame.winfo_children():
            widget.destroy()

        self.card_text_refs = {}
        
        if not self.deck:
            return
        
        def render():
            creatures, spells, lands = deck.grouped_for_overlay()
            self._add_section("Creatures", creatures)
            self._add_section("Spells", spells)
            self._add_section("Lands", lands)
        self.show(render)

    def card_drawn(self, grp_id):
        if grp_id in self.card_text_refs:
            dc = self.deck.get_card_by_id(grp_id)
            canvas, text_id = self.card_text_refs[grp_id]
            canvas.itemconfig(text_id, text=f"{dc.left}/{dc.total}")

    # --------------------------------------------------

    def _clear_content(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.card_text_refs = {}

    def _draw_item(self, canvas, grp_id, name, total, left, colors):
        canvas.delete("all")
        width = DECK_WIDTH
        height = DECK_HEIGHT

        if len(colors) == 1:
            canvas.create_rectangle(
                0, 0, width, height,
                fill=colors[0], outline=""
            )
        else:
            n = len(colors)
            for y in range(height):
                for x in range(width):
                    pos = ((x + y) / (width + height)) * (n - 1)
                    i = int(pos)
                    t = pos - i
                    if i >= n - 1:
                        i = n - 2
                        t = 1
                    color = blend_colors(colors[i], colors[i + 1], t)
                    canvas.create_line(x, y, x + 1, y, fill=color)

        canvas.create_text(
            4, height / 2,
            text=name,
            fill="black",
            font=FONTS["deck_card"],
            anchor="w",
        )

        text_id = canvas.create_text(
            width - 4,
            height / 2,
            text=f"{left}/{total}",
            fill="black",
            font=FONTS["deck_count"],
            anchor="e",
        )

        self.card_text_refs[grp_id] = (canvas, text_id)
