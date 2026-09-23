import cv2
import numpy as np

from . import capture

# Small scale sweep absorbs minor DPI/zoom drift between recording and playback.
_SCALES = [1.0, 0.97, 1.03, 0.94, 1.06, 0.9, 1.1]


class MatchResult:
    def __init__(self, x, y, w, h, score):
        self.x, self.y, self.w, self.h, self.score = x, y, w, h, score

    @property
    def center(self):
        return self.x + self.w // 2, self.y + self.h // 2


def find_template(template_bgr, screen_bgr=None, threshold=0.85):
    """Find `template_bgr` inside `screen_bgr` (or the live screen).

    Returns the best MatchResult, or None if nothing clears `threshold`.
    """
    if screen_bgr is None:
        screen_bgr = capture.grab()

    screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    tmpl_gray_full = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

    best = None
    for scale in _SCALES:
        h0, w0 = tmpl_gray_full.shape[:2]
        w, h = int(w0 * scale), int(h0 * scale)
        if w < 4 or h < 4 or h > screen_gray.shape[0] or w > screen_gray.shape[1]:
            continue
        tmpl = cv2.resize(tmpl_gray_full, (w, h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(screen_gray, tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if best is None or max_val > best.score:
            best = MatchResult(max_loc[0], max_loc[1], w, h, max_val)

    if best is None or best.score < threshold:
        return None
    return best
