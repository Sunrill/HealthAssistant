"""跨次报告的趋势对比。"""
from .knowledge import canonical_name


def display_period(iso_date: str) -> str:
    """把 ISO 日期转成只到月份的展示文本，避免暴露具体体检日。"""
    try:
        y, m, _ = iso_date.split("-")
        return f"{y} 年 {int(m)} 月"
    except (ValueError, AttributeError):
        return iso_date


def trend_of(reports: list, name: str) -> list[dict]:
    target = canonical_name(name)
    series = []
    for report in reports:
        for item in report.items:
            if canonical_name(item.name) == target:
                series.append({
                    "date": report.report_date,
                    "value": item.value,
                    "high": item.ref_high,
                })
                break
    return series


def trend_summary(series: list[dict]) -> dict:
    if len(series) < 2:
        return {"points": len(series), "note": "仅一次记录，无法算趋势"}
    first, last = series[0], series[-1]
    if not isinstance(first["value"], (int, float)) or not isinstance(last["value"], (int, float)):
        return {"points": len(series), "note": "定性指标不计算变化率"}
    delta = round(last["value"] - first["value"], 2)
    pct = round(delta / first["value"] * 100, 1) if first["value"] else None
    return {"points": len(series), "delta": delta, "change_pct": pct,
            "direction": "上升" if delta > 0 else ("下降" if delta < 0 else "持平")}
