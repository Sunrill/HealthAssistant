"""检验指标的判定规则：全部为纯函数。"""
from .models import LabItem

SEVERITY_LIGHT = "轻度"
SEVERITY_MODERATE = "中度"
SEVERITY_MARKED = "显著"

# 危急值区间：(下限, 上限)，None 表示该侧不设限
CRITICAL = {
    "葡萄糖": (3.0, 13.9),
    "尿酸": (None, 700),
    "白细胞计数": (1.5, 30),
    "血红蛋白": (70, 200),
    "血小板计数": (50, 600),
}


def judge_flag(value, ref_low, ref_high) -> str:
    """依据参考区间判定标志位。定性项（非数值）返回 unknown。"""
    if not isinstance(value, (int, float)):
        return "unknown"
    if ref_low is None and ref_high is None:
        return "unknown"
    if ref_high is not None and value > ref_high:
        return "high"
    if ref_low is not None and value < ref_low:
        return "low"
    return "normal"


def deviation_pct(value, ref_low, ref_high) -> float | None:
    """偏离百分比。正数表示偏高，负数表示偏低。"""
    if not isinstance(value, (int, float)):
        return None
    if ref_high is not None and value > ref_high:
        return round((value - ref_high) / ref_high * 100, 1)
    if ref_low is not None and value < ref_low:
        return round((value - ref_low) / ref_low * 100, 1)
    return None


def severity(deviation: float | None) -> str:
    """按偏离幅度分级。经验阈值，可按指标定制。"""
    if deviation is None:
        return "正常"
    pct = abs(deviation)
    if pct < 10:
        return SEVERITY_LIGHT
    if pct < 30:
        return SEVERITY_MODERATE
    return SEVERITY_MARKED


def is_critical(name: str, value) -> bool:
    """危急值提示。仅覆盖少量高频项，其余交医生判断。"""
    if not isinstance(value, (int, float)):
        return False
    bounds = CRITICAL.get(name)
    if not bounds:
        return False
    low, high = bounds
    if low is not None and value < low:
        return True
    if high is not None and value > high:
        return True
    return False


def _ref_text(ref_low, ref_high) -> str:
    if ref_low is not None and ref_high is not None:
        return f"{ref_low}–{ref_high}"
    if ref_low is not None:
        return f">{ref_low}"
    if ref_high is not None:
        return f"<{ref_high}"
    return "-"


def enrich(items: list[LabItem]) -> list[dict]:
    """把判定结果补齐成可直接展示的结构。"""
    out = []
    for item in items:
        flag = item.flag if item.flag != "unknown" else judge_flag(
            item.value, item.ref_low, item.ref_high)
        dev = deviation_pct(item.value, item.ref_low, item.ref_high)
        out.append({
            "name": item.name,
            "value": item.value,
            "unit": item.unit,
            "ref": _ref_text(item.ref_low, item.ref_high),
            "panel": item.panel,
            "flag": flag,
            "deviation_pct": dev,
            "severity": severity(dev),
            "critical": is_critical(item.name, item.value),
        })
    return out


def abnormal_items(items: list[LabItem]) -> list[dict]:
    return [x for x in enrich(items) if x["flag"] in ("high", "low")]
