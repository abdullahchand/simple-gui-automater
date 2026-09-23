from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ClickAction:
    template_path: str
    recorded_bbox: Optional[tuple] = None  # (x, y, w, h) where this was recorded
    click_type: str = "left"  # left | double | right
    threshold: float = 0.85
    search_margin: int = 250
    label: str = ""
    type: str = field(default="click", init=False)


@dataclass
class TypeAction:
    template_path: str
    text: str
    recorded_bbox: Optional[tuple] = None  # (x, y, w, h) where this was recorded
    date_format: str = "%Y-%m-%d"
    threshold: float = 0.85
    search_margin: int = 250
    label: str = ""
    type: str = field(default="type", init=False)


@dataclass
class SelectAction:
    control_template_path: str
    search_offset: tuple  # (dx, dy, w, h) relative to control match top-left
    value: str
    control_bbox: Optional[tuple] = None  # (x, y, w, h) where the control was recorded
    date_format: str = "%d"
    threshold: float = 0.85
    search_margin: int = 250
    open_delay: float = 0.6
    label: str = ""
    type: str = field(default="select", init=False)


_TYPE_MAP = {"click": ClickAction, "type": TypeAction, "select": SelectAction}


def to_dict(action) -> dict:
    return asdict(action)


def from_dict(d: dict):
    cls = _TYPE_MAP[d["type"]]
    d = {k: v for k, v in d.items() if k != "type"}
    return cls(**d)


def summary(action) -> str:
    if isinstance(action, ClickAction):
        return f"CLICK ({action.click_type}) {action.label or action.template_path}"
    if isinstance(action, TypeAction):
        return f"TYPE '{action.text}' -> {action.label or action.template_path}"
    if isinstance(action, SelectAction):
        return f"SELECT '{action.value}' in {action.label or action.control_template_path}"
    return "?"
