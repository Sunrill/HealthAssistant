"""体检报告相关工具，沿用 BaseHealthTool 的「_execute -> str」模式。"""
import json
from typing import Any, Dict, List

from hello_agents.tools import ToolParameter

from ..tools import BaseHealthTool
from .advice import merge_advice
from .followup import build_followups
from .knowledge import get_card
from .parser import parse_pdf
from .rules import abnormal_items, enrich
from .store import load_lab_index, load_lab_report, save_lab_report
from .trend import display_period, trend_of, trend_summary


class LabReportTool(BaseHealthTool):
    """导入与查看体检报告。"""

    def __init__(self):
        super().__init__(
            name="lab_report",
            description="导入或查看体检报告。用户提供体检 PDF 路径时说 action=import；"
                        "问“我的体检结果”“某个指标多少”时用 action=list 或 action=item。"
        )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        action = parameters.get("action", "list")

        if action == "import":
            path = parameters.get("path", "")
            date = parameters.get("report_date", "")
            if not path or not date:
                return "导入需要提供 path 与 report_date（YYYY-MM-DD）。"
            try:
                report = parse_pdf(path, date, parameters.get("institution") or "某三甲医院")
            except Exception as exc:
                return f"解析失败：{exc}"
            if not report.items:
                return "未解析出任何指标，请检查文件是否含文本层、版式是否匹配。"
            save_lab_report(report)
            abnormal = abnormal_items(report.items)
            return (f"已导入 {display_period(date)} 报告，共 {len(report.items)} 项指标，"
                    f"其中 {len(abnormal)} 项异常。")

        dates = load_lab_index()
        if not dates:
            return "尚无体检报告，请先用 action=import 导入。"

        latest = load_lab_report(dates[-1])
        if action == "item":
            keyword = parameters.get("name", "")
            if not keyword:
                return "请提供要查询的指标名，例如“尿酸”。"
            hits = [x for x in enrich(latest.items) if keyword in x["name"]]
            if not hits:
                return f"报告中未找到含“{keyword}”的指标。"
            return json.dumps(hits, ensure_ascii=False)

        overview = {
            "period": display_period(latest.report_date),
            "institution": latest.institution,
            "total": len(latest.items),
            "abnormal_count": len(abnormal_items(latest.items)),
            "conclusions": latest.conclusions,
            "all_periods": [display_period(d) for d in dates],
        }
        return json.dumps(overview, ensure_ascii=False)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="action", type="string",
                          description="import=导入, list=概览, item=查单项", required=True),
            ToolParameter(name="path", type="string", description="PDF 文件路径（import 时必填）", required=False),
            ToolParameter(name="report_date", type="string", description="体检日期 YYYY-MM-DD", required=False),
            ToolParameter(name="institution", type="string", description="体检机构，缺省为某三甲医院", required=False),
            ToolParameter(name="name", type="string", description="指标名关键词（item 时用）", required=False),
        ]


class LabAnalysisTool(BaseHealthTool):
    """异常解读、复诊建议、趋势与组合建议。"""

    def __init__(self):
        super().__init__(
            name="lab_analysis",
            description="体检报告的深度分析：action=abnormal 看异常项解读，action=followup 看复查计划，"
                        "action=trend 看某项指标跨次变化，action=advice 看合并后的生活方式建议。"
                        "回答任何涉及体检数值或异常的问题前必须先调用本工具。"
        )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        action = parameters.get("action", "abnormal")
        dates = load_lab_index()
        if not dates:
            return "尚无体检报告。"

        if action == "trend":
            name = parameters.get("name", "")
            if not name:
                return "请提供要对比的指标名，例如“尿酸”。"
            reports = [load_lab_report(d) for d in dates]
            series = trend_of([r for r in reports if r], name)
            if not series:
                return f"未找到指标“{name}”。"
            return json.dumps({"series": series, "summary": trend_summary(series)}, ensure_ascii=False)

        latest = load_lab_report(dates[-1])
        abnormal = abnormal_items(latest.items)

        if action == "followup":
            return json.dumps({"period": display_period(latest.report_date),
                               "plans": build_followups(latest)}, ensure_ascii=False)

        if action == "advice":
            names = [x["name"] for x in abnormal]
            return json.dumps(merge_advice(names), ensure_ascii=False)

        result = []
        for x in abnormal:
            card = get_card(x["name"]) or {}
            result.append({
                **x,
                "common_causes": card.get("common_causes", []),
                "lifestyle": card.get("lifestyle", []),
                "department": card.get("department", ""),
                "recheck": card.get("recheck", ""),
            })
        return json.dumps({"period": display_period(latest.report_date), "abnormal": result},
                          ensure_ascii=False)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="action", type="string",
                          description="abnormal=异常解读, followup=复查计划, trend=趋势, advice=合并建议",
                          required=True),
            ToolParameter(name="name", type="string", description="指标名（trend 时必填）", required=False),
        ]
