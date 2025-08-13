# foodops/ui/results_view.py

from FoodOPS_V1.domain.types import TurnResult


# ---------- Helpers de formatage ----------


def format_to_euro(x: float) -> str:
    try:
        return f"{float(x):,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return f"{x} €"


def _pct(a: float, b: float) -> str:
    try:
        if b <= 0:
            return "—"
        v = max(0.0, min(1.0, float(a) / float(b))) * 100.0
        return f"{v:5.1f}%"
    except Exception:
        return "—"


def _bar(current: int, maxv: int, width: int = 24, fill_char: str = "█") -> str:
    if maxv <= 0:
        return " " * width
    ratio = max(0.0, min(1.0, float(current) / float(maxv)))
    n = int(round(ratio * width))
    return fill_char * n + " " * (width - n)


def _num(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0
