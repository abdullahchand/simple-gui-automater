import re
from datetime import datetime, timedelta

_TOKEN_RE = re.compile(r"\{(today|now)([+-]\d+)?\}")


def resolve_value(expr: str, fmt: str = "%Y-%m-%d") -> str:
    """Expand {today}, {today+3}, {today-2}, {now} tokens using `fmt`.

    Plain strings with no tokens are returned unchanged, so this is safe
    to call on literal click/type/select values too.
    """
    if not expr:
        return expr

    def _sub(match: "re.Match[str]") -> str:
        base, offset = match.group(1), match.group(2)
        now = datetime.now()
        if base == "today":
            now = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if offset:
            now += timedelta(days=int(offset))
        return now.strftime(fmt)

    return _TOKEN_RE.sub(_sub, expr)


def has_tokens(expr: str) -> bool:
    return bool(expr) and bool(_TOKEN_RE.search(expr))
