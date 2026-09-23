import numpy as np
import mss


def grab(bbox=None):
    """Grab the screen (or a region) as a BGR numpy array (OpenCV format).

    bbox: (x, y, w, h) or None for the whole virtual desktop.

    monitors[0] is mss's "all monitors combined" entry, spanning the same
    coordinate space pyautogui/Xlib use, which is what template-matched
    coordinates need to line up with on multi-monitor setups. monitors[1:]
    are the individual physical outputs and are NOT used here on purpose.
    """
    with mss.mss() as sct:
        if bbox is None:
            monitor = sct.monitors[0]
        else:
            x, y, w, h = bbox
            monitor = {"left": x, "top": y, "width": w, "height": h}
        shot = sct.grab(monitor)
        img = np.array(shot)  # BGRA
        return img[:, :, :3]


def screen_size():
    with mss.mss() as sct:
        m = sct.monitors[0]
        return m["width"], m["height"]
