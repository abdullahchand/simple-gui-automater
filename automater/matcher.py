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


def _find_peaks(corr, threshold, min_dist):
    """Return every local maximum in `corr` at or above `threshold`, at least
    `min_dist` apart, as (x, y, score). Needed because near-identical UI
    elements (e.g. the same icon repeated in every row of a table) each
    produce their own peak in the correlation map."""
    peaks = []
    work = corr.copy()
    for _ in range(25):  # safety cap
        _, max_val, _, max_loc = cv2.minMaxLoc(work)
        if max_val < threshold:
            break
        x, y = max_loc
        peaks.append((x, y, max_val))
        x0, x1 = max(0, x - min_dist), min(work.shape[1], x + min_dist)
        y0, y1 = max(0, y - min_dist), min(work.shape[0], y + min_dist)
        work[y0:y1, x0:x1] = -1.0
    return peaks


def find_all_matches(template_bgr, screen_bgr, threshold=0.85):
    """Every place `template_bgr` matches in `screen_bgr` at or above
    `threshold`, across a small scale sweep."""
    screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    tmpl_gray_full = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    h0, w0 = tmpl_gray_full.shape[:2]
    min_dist = max(10, min(w0, h0) // 2)

    matches = []
    for scale in _SCALES:
        w, h = int(w0 * scale), int(h0 * scale)
        if w < 4 or h < 4 or h > screen_gray.shape[0] or w > screen_gray.shape[1]:
            continue
        tmpl = cv2.resize(tmpl_gray_full, (w, h), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(screen_gray, tmpl, cv2.TM_CCOEFF_NORMED)
        for x, y, score in _find_peaks(res, threshold, min_dist):
            matches.append(MatchResult(x, y, w, h, score))
    return matches


def find_template(template_bgr, screen_bgr=None, threshold=0.85):
    """Find `template_bgr` inside `screen_bgr` (or the live screen).

    Returns the single best-scoring MatchResult, or None if nothing clears
    `threshold`.
    """
    if screen_bgr is None:
        screen_bgr = capture.grab()
    matches = find_all_matches(template_bgr, screen_bgr, threshold)
    if not matches:
        return None
    return max(matches, key=lambda m: m.score)


def find_template_near(template_bgr, recorded_bbox=None, threshold=0.85, margin=250):
    """Search near `recorded_bbox` first, falling back to the full screen.

    When several near-identical elements exist close together (e.g. the same
    "..." icon repeated in every row of a table), the highest-scoring match
    isn't necessarily the right one - they can all score ~equally. So instead
    of just taking the best score, every match above `threshold` is found and
    the one CLOSEST to where this template was originally recorded is picked.
    """
    if recorded_bbox is not None:
        sw, sh = capture.screen_size()
        rx, ry, rw, rh = recorded_bbox
        x0 = max(0, rx - margin)
        y0 = max(0, ry - margin)
        x1 = min(sw, rx + rw + margin)
        y1 = min(sh, ry + rh + margin)
        region_bbox = (x0, y0, x1 - x0, y1 - y0)

        local_screen = capture.grab(region_bbox)
        matches = find_all_matches(template_bgr, local_screen, threshold)
        if matches:
            ref_x, ref_y = rx - x0, ry - y0
            best = min(matches, key=lambda m: (m.x - ref_x) ** 2 + (m.y - ref_y) ** 2)
            return MatchResult(best.x + x0, best.y + y0, best.w, best.h, best.score)

        # Not found nearby (window moved/scrolled) - fall back to a full scan,
        # still preferring whichever match is closest to the recorded spot.
        matches = find_all_matches(template_bgr, capture.grab(), threshold)
        if not matches:
            return None
        return min(matches, key=lambda m: (m.x - rx) ** 2 + (m.y - ry) ** 2)

    return find_template(template_bgr, threshold=threshold)
