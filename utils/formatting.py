# utils/formatting.py
def fmt_pct(x: float, digits: int = 2) -> str:
    return f"{x*100:.{digits}f} %"

def fmt_abs(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}"