import cv2
import pytesseract
from pytesseract import Output


def find_text(region_bgr, target_text):
    """Find `target_text` inside `region_bgr` via OCR word boxes.

    Returns (x, y, w, h) of the matching word box, region-relative,
    or None if no word matches (exact match preferred, else substring).
    """
    gray = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, output_type=Output.DICT)

    target = target_text.strip().lower()
    substring_hit = None

    n = len(data["text"])
    for i in range(n):
        word = data["text"][i].strip()
        if not word:
            continue
        wl = word.lower()
        box = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
        if wl == target:
            return box
        if target in wl or wl in target:
            substring_hit = substring_hit or box

    return substring_hit
