from .constants import MAX_OPACITY

class FadeEffects:
    def _init_fade(self, window, step=0.05, delay=20, max_alpha=MAX_OPACITY):
        self.fade_window = window
        self.step = step
        self.delay = delay
        self.fade_max_alpha = max_alpha
        self.fading = False


    def fade_in(self):
        if self.fading:
            return
        self.fading = True
        self.fade_window.attributes("-alpha", 0.0)

        def _animate():
            alpha = self.fade_window.attributes("-alpha")
            if alpha < self.fade_max_alpha:
                alpha = min(alpha + self.step, self.fade_max_alpha)
                self.fade_window.attributes("-alpha", alpha)
                self.fade_window.after(self.delay, _animate)
            else:
                self.fading = False

        _animate()


    def fade_out(self, callback=None):
        if self.fading:
            return
        self.fading = True

        def _animate():
            alpha = self.fade_window.attributes("-alpha")
            if alpha > 0.0:
                alpha = max(alpha - self.step, 0.0)
                self.fade_window.attributes("-alpha", alpha)
                self.fade_window.after(self.delay, _animate)
            else:
                self.fading = False
                if callback:
                    callback()

        _animate()