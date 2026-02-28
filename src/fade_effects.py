from .constants import MAX_OPACITY

class FadeEffects:
    def _init_fade(self, window, max_alpha=MAX_OPACITY):
        self._fade_window = window
        self._fade_max_alpha = max_alpha
        self._fading = False


    def fade_in(self, step=0.05, delay=20):
        if self._fading:
            return
        self._fading = True
        self._fade_window.attributes("-alpha", 0.0)

        def _animate():
            alpha = self._fade_window.attributes("-alpha")
            if alpha < self._fade_max_alpha:
                alpha = min(alpha + step, self._fade_max_alpha)
                self._fade_window.attributes("-alpha", alpha)
                self._fade_window.after(delay, _animate)
            else:
                self._fading = False

        _animate()


    def fade_out(self, step=0.05, delay=20, callback=None):
        if self._fading:
            return
        self._fading = True

        def _animate():
            alpha = self._fade_window.attributes("-alpha")
            if alpha > 0.0:
                alpha = max(alpha - step, 0.0)
                self._fade_window.attributes("-alpha", alpha)
                self._fade_window.after(delay, _animate)
            else:
                self._fading = False
                if callback:
                    callback()

        _animate()