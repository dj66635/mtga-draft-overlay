import tkinter as tk
import ctypes

from .constants import (
    RATING_COLOR,
    DEFAULT_COLOR,
    TRANSPARENT_COLOR,
    MAX_OPACITY,
    FONTS
)
from .utils import get_contrast_color
from .overlay import BaseOverlay


class DraftOverlay(BaseOverlay):
    def __init__(self, x=0, y=0, size_x=0, size_y=0):
        super().__init__(TRANSPARENT_COLOR, x, y, size_x, size_y)
        
        self.current_items = []
        self.window.wm_attributes("-alpha", MAX_OPACITY)
        
        hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
        self._make_click_through(hwnd)

        self.canvas = tk.Canvas(self.window, bg=TRANSPARENT_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    # --------------------------------------------------

    def _make_click_through(self, hwnd):
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020

        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            style | WS_EX_LAYERED | WS_EX_TRANSPARENT,
        )
            
    # --------------------------------------------------

    def show_ratings(self, ratings):
        def render():
            self._clear_content()
            self._draw_boxes(ratings)
        self.show(render)

    # --------------------------------------------------

    def _clear_content(self):
        for item in self.current_items:
            self.canvas.delete(item)
        self.current_items = []

    def _draw_boxes(self, ratings):
        box_size = 22

        for i, rating in enumerate(ratings):
            x = 361.2 + 170.6 * (i % 8)
            y = 209 + 214 * (i // 8)

            bg_color = RATING_COLOR.get(rating, DEFAULT_COLOR)

            rect = self.canvas.create_rectangle(
                x, y, x + box_size, y + box_size,
                fill=bg_color,
            )

            text = self.canvas.create_text(
                x + box_size / 2,
                y + box_size / 2,
                text=rating,
                font=FONTS["rating"],
                fill=get_contrast_color(bg_color),
            )

            self.current_items.extend([rect, text])