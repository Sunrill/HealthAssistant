"""生成 Markdown 健康周报。"""
import os
from datetime import datetime

from . import storage
from .metrics import summarize

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")


def build_report(advice: str) -> str:
    profile = storage.load_profile()
    if not profile:
        raise ValueError("缺少用户档案，无法生成报告")

    records = storage.load_records()
    data = summarize(profile, records)

    lines = [
        "# 健康周报",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"记录天数：{data.get('record_count', 0)}",
        "",
        "## 基础指标",
        "",
        f"- BMI：{data['bmi']['value']}（{data['bmi']['category']}）",
        f"- 基础代谢率：{data['bmr_kcal']} kcal/日",
        f"- 每日能量消耗：{data['tdee_kcal']} kcal/日",
        f"- 建议饮水量：{data['water_target_ml']} ml/日",
    ]

    if "bp" in data:
        lines.append(f"- 最近血压：{data['bp']['value']}（{data['bp']['category']}）")
    if "sleep" in data:
        lines.append(f"- 最近睡眠：{data['sleep']['hours']} 小时（{data['sleep']['assessment']}）")

    lines += ["", "## 建议", "", advice.strip(), "", "---", "",
              "以上为生活方式建议，不构成医疗诊断或治疗意见。"]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "health_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
