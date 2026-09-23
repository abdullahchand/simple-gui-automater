import time

import cv2
import pyautogui

from . import actions as A
from . import capture, matcher, ocr, dynamic

pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True  # move mouse to a screen corner to abort


class PlaybackError(Exception):
    def __init__(self, step_index, action, message):
        self.step_index = step_index
        self.action = action
        super().__init__(f"Step {step_index + 1} ({A.summary(action)}): {message}")


def _click_at(x, y, click_type):
    pyautogui.moveTo(x, y, duration=0.15)
    if click_type == "double":
        pyautogui.doubleClick()
    elif click_type == "right":
        pyautogui.click(button="right")
    else:
        pyautogui.click()


def _run_click(index, act: A.ClickAction):
    template = cv2.imread(act.template_path)
    m = matcher.find_template(template, threshold=act.threshold)
    if m is None:
        raise PlaybackError(index, act, "template not found on screen")
    x, y = m.center
    _click_at(x, y, act.click_type)


def _run_type(index, act: A.TypeAction):
    template = cv2.imread(act.template_path)
    m = matcher.find_template(template, threshold=act.threshold)
    if m is None:
        raise PlaybackError(index, act, "template not found on screen")
    x, y = m.center
    _click_at(x, y, "left")
    text = dynamic.resolve_value(act.text, act.date_format)
    pyautogui.typewrite(text, interval=0.02)


def _run_select(index, act: A.SelectAction):
    control_tmpl = cv2.imread(act.control_template_path)
    m = matcher.find_template(control_tmpl, threshold=act.threshold)
    if m is None:
        raise PlaybackError(index, act, "control template not found on screen")
    cx, cy = m.center
    _click_at(cx, cy, "left")
    time.sleep(act.open_delay)

    dx, dy, w, h = act.search_offset
    region_x, region_y = m.x + dx, m.y + dy
    region = capture.grab((region_x, region_y, w, h))

    target = dynamic.resolve_value(act.value, act.date_format)
    box = ocr.find_text(region, target)
    if box is None:
        raise PlaybackError(index, act, f"could not find '{target}' via OCR in options area")
    bx, by, bw, bh = box
    click_x = region_x + bx + bw // 2
    click_y = region_y + by + bh // 2
    _click_at(click_x, click_y, "left")


_RUNNERS = {A.ClickAction: _run_click, A.TypeAction: _run_type, A.SelectAction: _run_select}


def run_sequence(steps, delay_between=0.4, on_step=None):
    """Run all `steps` in order. Raises PlaybackError on first failure.

    on_step(index, action): optional callback fired before each step runs.
    """
    for i, act in enumerate(steps):
        if on_step:
            on_step(i, act)
        _RUNNERS[type(act)](i, act)
        time.sleep(delay_between)
