import tkinter as tk
import tkinter.font as tkfont
import ctypes
import logging
from .scanner import ArenaScanner
from .constants import DB_FOLDER, ARENA_LOGS, RATING_COLOR, DEFAULT_COLOR, TRANSPARENT_COLOR, MAX_OPACITY
from .utils import get_contrast_color

logger = logging.getLogger(__name__)

class Overlay:
    def __init__(self, log_scanner):
        self.current_items = []
        self.log_scanner = log_scanner
        self.visible = True

        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill="both", expand=True)

        self.rating_font = tkfont.Font(family="Segoe UI", size=8, weight="bold")
        self.emoji_font = tkfont.Font(family="Segoe UI Emoji", size=9)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.root.overrideredirect(True) # removes title bar
        self.root.wm_attributes("-alpha", MAX_OPACITY)

        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        
        self._set_see_through()
        self._set_click_through(hwnd)
        self._set_always_on_top(hwnd)
        self._set_buttons()

        # Logo
        self.logo = self.canvas.create_text(70, 3, text="🚀", anchor="ne", font=self.emoji_font, fill="white")

    # ---------------------------------
    # METHODS 
    # ---------------------------------
    def _set_buttons(self):
        # --- Controls Window (no fade) ---
        self.controls = tk.Toplevel(self.root)
        self.controls.overrideredirect(True)
        self.controls.attributes("-topmost", True)
        self.controls.configure(bg=TRANSPARENT_COLOR)
        self.controls.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.controls.geometry("80x40+0+-10")

        # Toggle Button
        self.toggle_btn = tk.Button(self.controls, text="👁️", font=self.emoji_font, command=self.toggle_overlay, bd=0)
        self.toggle_btn.pack(side="left", padx=0, pady=0)

        # Exit Button
        self.exit_btn = tk.Button(self.controls, text="❌", font=self.emoji_font, command=self.root.destroy, bd=0)
        self.exit_btn.pack(side="left", padx=0, pady=0)

    def _set_see_through(self):
        self.root.configure(bg=TRANSPARENT_COLOR)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.canvas.config(bg=TRANSPARENT_COLOR, highlightthickness=0)

    def _set_click_through(self, hwnd):
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

    def _set_always_on_top(self, hwnd):
        self.root.attributes("-topmost", True) # does nothing?
        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def start(self):
        self.update_on_tick()
        self.root.mainloop()


    def toggle_overlay(self):
        if self.visible:
            self.canvas.pack_forget()
            self.visible = False
        else:
            self.canvas.pack(fill="both", expand=True)
            self.visible = True

    def fade_in(self, step=0.05, delay=20):
        # Ensure alpha exists
        try:
            alpha = self.root.attributes("-alpha")
        except:
            alpha = 0.0
            self.root.attributes("-alpha", alpha)
        if alpha < MAX_OPACITY:
            alpha = min(alpha + step, MAX_OPACITY)
            self.root.attributes("-alpha", alpha)
            self.root.after(delay, lambda: self.fade_in(step, delay))

    def fade_out_wait(self, step=0.05, delay=20, callback=None):
        try:
            alpha = self.root.attributes("-alpha")
        except:
            alpha = MAX_OPACITY
            self.root.attributes("-alpha", alpha)
        if alpha > 0.0:
            alpha = max(alpha - step, 0.0)
            self.root.attributes("-alpha", alpha)
            self.root.after(delay, lambda: self.fade_out_wait(step, delay, callback))
        else: 
            if callback: callback()

    def clear_boxes(self):
        self.fade_out_wait() # when called through draw_boxes its already faded out, thus no issue
        for item_id in self.current_items:
            self.canvas.delete(item_id)
        self.current_items = []

    def box_positions(self, i):
        base_h = 361.2
        base_v = 209
        card_width = 170.6
        card_length = 214
        # (base_v, base_h) <- card_width -> ... <- card_width -> 8 cards long...
        return (base_h + card_width * (i % 8), base_v + card_length * (i // 8))
    
    def draw_boxes(self, texts):
        # fade_out_wait at the end
        def _draw_boxes():
            self.clear_boxes()
            box_size = 22

            # Create boxes
            for i, rating in enumerate(texts):
                (x, y) = self.box_positions(i)
                bg_color = RATING_COLOR.get(rating, DEFAULT_COLOR)

                rect = self.canvas.create_rectangle(
                    x, y, x + box_size, y + box_size,
                    fill = bg_color
                )
                text = self.canvas.create_text(
                    x + box_size / 2, y + box_size / 2,
                    text = rating,
                    font = self.rating_font,
                    fill = get_contrast_color(bg_color)
                )
                self.current_items.extend([rect, text])
            self.fade_in()
        self.fade_out_wait(callback=_draw_boxes)
        
    def update_on_tick(self):	  
        # not in draft, search for the start. we need to load the db     
        if not self.log_scanner.in_draft: 
            set_code = self.log_scanner.draft_start_search()
            if set_code is not None:
                logger.info(f"New draft: {set_code}")
                self.log_scanner.in_draft = True

        else: # in draft, we search for cards and the end
            ratings = self.log_scanner.draft_pack_search() 
            if ratings is not None:
                logger.info(f"Ratings: {ratings}")
                self.draw_boxes(ratings)

            ended = self.log_scanner.draft_end_search()
            if ended:
                logger.info(f"Draft ended. GL!")
                self.log_scanner.in_draft = False
                self.clear_boxes()

        self.root.after(100, self.update_on_tick)


def start_overlay():
    log_scanner = ArenaScanner(ARENA_LOGS, DB_FOLDER)
    overlay = Overlay(log_scanner)
    overlay.start()
