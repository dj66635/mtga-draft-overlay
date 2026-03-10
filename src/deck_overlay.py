import tkinter as tk
from .utils import blend_colors, hex_to_rgb
from .constants import (
    DECK_HEIGHT, 
    DECK_WIDTH,
    FONTS,
    NO_CARDS_LEFT
)
from .overlay import BaseOverlay


class DeckOverlay(BaseOverlay):
    def __init__(self, x=0, y=0, fade_step=0.05, fade_delay=20, manual_mode=False):
        super().__init__("black", x, y, fade_step=fade_step, fade_delay=fade_delay)
        
        self.deck = None
        self.card_obj_refs = {}
        self.sideboard_card_obj_refs = {}
        self.manual_mode = manual_mode

        self.frame = tk.Frame(self.window, bg="black")
        self.frame.pack(padx=5, pady=5)

        self.window.bind("<ButtonPress-1>", self._start_move)
        self.window.bind("<B1-Motion>", self._on_move)
        self.window.bind("<ButtonRelease-1>", self._stop_move)

        self._drag_data = None

        self.clear() # removes the freaking black box

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

        for grp_id, name, total, left, colors, sideboard in items:
            canvas = tk.Canvas(
                self.frame,
                width=DECK_WIDTH,
                height=DECK_HEIGHT,
                highlightthickness=0,
            )
            canvas.pack(fill="x", pady=2)
            
            self._draw_item(canvas, grp_id, name, total, left, colors, sideboard)
            
            canvas.bind("<ButtonPress-1>", self._start_move)
            canvas.bind("<B1-Motion>", self._on_move)
            canvas.bind("<ButtonRelease-1>", self._stop_move)
            if self.manual_mode:
                canvas.bind("<ButtonPress-1>", lambda e, g=grp_id, s=sideboard: self._decrease_count(g, s), add="+")
                canvas.bind("<ButtonPress-3>", lambda e, g=grp_id, s=sideboard: self._increase_count(g, s), add="+")

    def _decrease_count(self, grp_id, sideboard):
        self.deck.draw_card(grp_id, sideboard)
        self.refresh_card_count(grp_id, sideboard)
    
    def _increase_count(self, grp_id, sideboard):
        self.deck.draw_card(grp_id, sideboard, -1) # little hack
        self.refresh_card_count(grp_id, sideboard)

    # --------------------------------------------------

    def load_deck(self, deck):
        self.deck = deck
        
        for widget in self.frame.winfo_children():
            widget.destroy()        

        self.card_obj_refs = {}
        
        if not self.deck:
            return
        
        def render():
            creatures, spells, lands, sideboard = deck.grouped_for_overlay()
            self._add_section("Creatures", creatures)
            self._add_section("Spells", spells)
            self._add_section("Lands", lands)
            if sideboard: self._add_section("Sideboard", sideboard)
        self.show(render)


    def refresh_card_count(self, grp_id, sideboard=False):
        refs = self.card_obj_refs if not sideboard else self.sideboard_card_obj_refs
        if grp_id in refs:
            dc = self.deck.get_card_by_id(grp_id, sideboard)
            canvas, text_id, count_id, box_id, old_color = refs[grp_id]
            canvas.itemconfig(count_id, text=f"{dc.left}/{dc.total}")

            if dc.left == 0:
                canvas.itemconfig(text_id, fill="grey")
                canvas.itemconfig(count_id, fill="grey")
                if isinstance(box_id, tk.PhotoImage):
                    for y in range(box_id.height()):
                        for x in range(box_id.width()):
                            box_id.put(NO_CARDS_LEFT, (x, y))
                else:
                    canvas.itemconfig(box_id, fill=NO_CARDS_LEFT)
            else:
                if isinstance(old_color, str):
                    if old_color == canvas.itemcget(box_id, "fill"):
                        return # only if changed
                
                elif isinstance(old_color, list):
                    for y in range(box_id.height()):
                        for x in range(box_id.width()):
                            if box_id.get(x, y) == hex_to_rgb(old_color[y * box_id.width() + x]):
                                return

                canvas.itemconfig(text_id, fill="black")
                canvas.itemconfig(count_id, fill="black")
                if isinstance(box_id, tk.PhotoImage):
                    for y in range(box_id.height()):
                        for x in range(box_id.width()):
                            box_id.put(old_color[y * box_id.width() + x], (x, y))
                else:
                    canvas.itemconfig(box_id, fill=old_color)


    def refresh_card_counts(self):
        for grp_id in self.card_obj_refs:
            self.refresh_card_count(grp_id)
        for grp_id in self.sideboard_card_obj_refs:
            self.refresh_card_count(grp_id, True)
                
    # --------------------------------------------------

    def _clear_content(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.card_obj_refs = {}
        self.sideboard_card_obj_refs = {}

    def _draw_item(self, canvas, grp_id, name, total, left, colors, sideboard):
        canvas.delete("all")
        width = DECK_WIDTH
        height = DECK_HEIGHT
       
        box_id = None
        old_color = []
        if len(colors) == 1:
            rect = canvas.create_rectangle(
                0, 0, width, height,
                fill=colors[0] if left != 0 else NO_CARDS_LEFT, 
                outline=""
            )
            old_color = canvas.itemcget(rect, "fill")
            box_id = rect
        else:
            n = len(colors)
            img = tk.PhotoImage(width=width, height=height)
            for y in range(height):
                for x in range(width):
                    pos = ((x + y) / (width + height)) * (n - 1)
                    i = int(pos)
                    t = pos - i
                    color = blend_colors(colors[i], colors[i + 1], t) if left != 0 else NO_CARDS_LEFT
                    img.put(color, (x, y))
                    old_color.append(color)
            canvas.create_image(0, 0, anchor="nw", image=img)
            canvas.image = img  # keep a reference!
            box_id = img

        text_id = canvas.create_text(
            4, height / 2,
            text=name,
            fill="black" if left != 0 else "grey",
            font=FONTS["deck_card"],
            anchor="w",
        )

        count_id = canvas.create_text(
            width - 4,
            height / 2,
            text=f"{left}/{total}",
            fill="black" if left != 0 else "grey",
            font=FONTS["deck_count"],
            anchor="e",
        )

        if not sideboard:
            self.card_obj_refs[grp_id] = (canvas, text_id, count_id, box_id, old_color)
        else: 
            self.sideboard_card_obj_refs[grp_id] = (canvas, text_id, count_id, box_id, old_color)
