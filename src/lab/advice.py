"""把多个异常项的约束合并成一份不冲突的建议。"""
from .knowledge import get_card

CONSTRAINTS = {
    "尿酸": ["限嘌呤", "限酒", "限果糖", "足量饮水"],
    "脂肪肝": ["限酒", "控精制碳水", "控总热量"],
    "甘油三酯": ["限酒", "控精制碳水"],
    "超重": ["控总热量"],
}


def merge_advice(abnormal_names: list[str]) -> dict:
    merged: list[str] = []
    sources: dict[str, list[str]] = {}
    for name in abnormal_names:
        for c in CONSTRAINTS.get(name, []):
            sources.setdefault(c, []).append(name)
            if c not in merged:
                merged.append(c)

    lifestyle: list[str] = []
    for name in abnormal_names:
        card = get_card(name) or {}
        for tip in card.get("lifestyle", []):
            if tip not in lifestyle:
                lifestyle.append(tip)

    return {
        "constraints": merged,
        "constraint_sources": sources,
        "lifestyle": lifestyle,
        "note": "以上约束已合并去重，执行时以最严格的一条为准。",
    }
