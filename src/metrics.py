"""健康指标计算：全部为纯函数，输入输出明确，便于单元测试。"""
from typing import Optional

ACTIVITY_FACTORS = {
    "sedentary": 1.2,     # 久坐
    "light": 1.375,       # 轻度活动（每周 1-3 次）
    "moderate": 1.55,     # 中度（每周 3-5 次）
    "active": 1.725,      # 高强度（每周 6-7 次）
    "very_active": 1.9,   # 体力劳动/一日两练
}


def bmi(weight_kg: float, height_cm: float) -> float:
    h = height_cm / 100
    return round(weight_kg / (h * h), 1)


def bmi_category(value: float) -> str:
    """中国成人标准（WS/T 428-2013）。"""
    if value < 18.5:
        return "偏瘦"
    if value < 24:
        return "正常"
    if value < 28:
        return "超重"
    return "肥胖"


def bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> int:
    """Mifflin-St Jeor 公式。"""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return round(base + 5 if sex == "male" else base - 161)


def tdee(sex: str, weight_kg: float, height_cm: float, age: int, activity: str) -> int:
    factor = ACTIVITY_FACTORS.get(activity, 1.375)
    return round(bmr(sex, weight_kg, height_cm, age) * factor)


def bp_category(systolic: int, diastolic: int) -> tuple[str, bool]:
    """返回 (分级, 是否需立即就医)。依据《中国高血压防治指南》。"""
    if systolic >= 180 or diastolic >= 110:
        return "3级高血压", True
    if systolic >= 160 or diastolic >= 100:
        return "2级高血压", False
    if systolic >= 140 or diastolic >= 90:
        return "1级高血压", False
    if systolic >= 120 or diastolic >= 80:
        return "正常高值", False
    return "正常", False


def sleep_assessment(hours: float) -> str:
    if hours < 6:
        return "睡眠不足"
    if hours < 7:
        return "略低于推荐"
    if hours <= 9:
        return "达标"
    return "睡眠偏长"


def water_target(weight_kg: float) -> int:
    """按 30 ml/kg 估算，上限 3500 ml。"""
    return min(round(weight_kg * 30), 3500)


def summarize(profile, records) -> dict:
    """汇总成结构化字典，供工具返回与报告生成使用。"""
    out = {
        "bmi": {"value": bmi(profile.weight_kg, profile.height_cm)},
        "bmr_kcal": bmr(profile.sex, profile.weight_kg, profile.height_cm, profile.age),
        "tdee_kcal": tdee(profile.sex, profile.weight_kg, profile.height_cm, profile.age, profile.activity),
        "water_target_ml": water_target(profile.weight_kg),
    }
    out["bmi"]["category"] = bmi_category(out["bmi"]["value"])

    if records:
        latest = records[-1]
        if latest.systolic and latest.diastolic:
            cat, urgent = bp_category(latest.systolic, latest.diastolic)
            out["bp"] = {"value": f"{latest.systolic}/{latest.diastolic}", "category": cat, "urgent": urgent}
        if latest.sleep_hours is not None:
            out["sleep"] = {"hours": latest.sleep_hours, "assessment": sleep_assessment(latest.sleep_hours)}
        out["latest_day"] = latest.day
        out["record_count"] = len(records)
    return out
