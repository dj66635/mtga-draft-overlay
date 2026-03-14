import tkinter as tk
from .constants import TRANSPARENT_COLOR, MAX_OPACITY
from .fade_effects import FadeEffects

class BaseOverlay(FadeEffects):
    def __init__(self, background, x=0, y=0, size_x=0, size_y=0, fade_step=0.05, fade_delay=20):
        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        self.window.configure(bg=background)
        self.window.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.window.wm_attributes("-alpha", MAX_OPACITY)

        if size_x == 0 and size_y == 0:
            self.window.geometry(f"+{x}+{y}")
        else:
            self.window.geometry(f"{size_x}x{size_y}+{x}+{y}")

        self._init_fade(self.window, fade_step, fade_delay)

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