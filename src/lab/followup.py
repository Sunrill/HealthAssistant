"""从异常项生成复查待办。"""
from datetime import date, timedelta

from .knowledge import get_card
from .rules import abnormal_items

PERIOD_DAYS = {
    "2–4 周": 21,
    "1 个月": 30,
    "3 个月": 90,
    "3–6 个月": 135,
    "6 个月": 180,
    "随下次血常规": 365,
}


def build_followups(report) -> list[dict]:
    plans = []
    for x in abnormal_items(report.items):
        card = get_card(x["name"]) or {}
        recheck = card.get("recheck", "遵医嘱")
        days = PERIOD_DAYS.get(recheck, 90)
        due = date.fromisoformat(report.report_date) + timedelta(days=days)
        plans.append({
            "item": x["name"],
            "severity": x["severity"],
            "department": card.get("department", "相应专科"),
            "recheck": recheck,
            "due_date": due.isoformat(),
            "critical": x["critical"],
        })
    plans.sort(key=lambda p: (not p["critical"], p["due_date"]))
    return plans
