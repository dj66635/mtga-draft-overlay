import tkinter as tk
from .constants import TRANSPARENT_COLOR
from .fade_effects import FadeEffects

class BaseOverlay(FadeEffects):
    def __init__(self, background):
        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        self.window.configure(bg=background)
        self.window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

        self._init_fade(self.window)

    def show(self, render_callback):
        # Fade out current content, run render_callback, then fade in.
        self.fade_out(callback=lambda: (render_callback(), self.fade_in()))

    def toggle(self):
        if self.window.state() == "withdrawn":
            self.window.deiconify()
        else:
            self.window.withdraw()

    def clear(self):
        def _clear():
            self._clear_content()
        self.fade_out(callback=_clear)
    
    def destroy(self):
        self.window.destroy()