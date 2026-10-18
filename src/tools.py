"""HelloAgents 工具封装。工具只做确定性操作，不含任何生成式逻辑。"""
import json
from datetime import date
from typing import Any, Dict, List

from hello_agents.tools import Tool, ToolParameter
from hello_agents.tools.response import ToolResponse, ToolStatus

from . import storage
from .metrics import summarize
from .models import DailyRecord, Profile


class BaseHealthTool(Tool):
    """兼容 hello-agents 1.x 的基类。

    1.x 的 Tool.run 必须返回 ToolResponse（框架会读取 .stats/.context），
    而教程基于旧版允许直接返回 str。这里统一包装：
    子类只实现 _execute() -> str，由 run() 负责转成 ToolResponse。
    """

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        try:
            text = self._execute(parameters)
            return ToolResponse(
                status=ToolStatus.SUCCESS,
                text=str(text),
                data={},
                context={"tool_name": self.name, "input": parameters},
            )
        except Exception as exc:
            return ToolResponse(
                status=ToolStatus.ERROR,
                text=f"执行失败：{exc}",
                data={},
                error_info={"code": "EXECUTION_ERROR", "message": str(exc)},
                context={"tool_name": self.name, "input": parameters},
            )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        raise NotImplementedError


class ProfileTool(BaseHealthTool):
    """录入/查看用户基础档案。"""

    def __init__(self):
        super().__init__(
            name="profile",
            description="录入或查看用户基础档案（性别、年龄、身高、体重、活动量）。"
                        "首次使用必须先调用 action=set 录入档案，否则无法计算任何指标。"
        )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        action = parameters.get("action", "get")

        if action == "set":
            profile = Profile(
                name=parameters.get("name", "用户"),
                sex=parameters["sex"],
                age=int(parameters["age"]),
                height_cm=float(parameters["height_cm"]),
                weight_kg=float(parameters["weight_kg"]),
                activity=parameters.get("activity", "light"),
            )
            storage.save_profile(profile)
            return f"档案已保存：{profile.name}，{profile.sex}，{profile.age}岁，{profile.height_cm}cm，{profile.weight_kg}kg"

        profile = storage.load_profile()
        if not profile:
            return "尚未录入档案，请先调用 action=set 提供性别、年龄、身高、体重。"
        return json.dumps(profile.to_dict(), ensure_ascii=False)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="action", type="string", description="set=录入，get=查看", required=True),
            ToolParameter(name="sex", type="string", description="male 或 female", required=False),
            ToolParameter(name="age", type="integer", description="年龄（岁），纯数字", required=False),
            ToolParameter(name="height_cm", type="number", description="身高（厘米），纯数字", required=False),
            ToolParameter(name="weight_kg", type="number", description="体重（千克），纯数字", required=False),
            ToolParameter(name="activity", type="string",
                          description="sedentary/light/moderate/active/very_active", required=False),
            ToolParameter(name="name", type="string", description="称呼", required=False),
        ]


class DailyRecordTool(BaseHealthTool):
    """录入当日健康数据。"""

    def __init__(self):
        super().__init__(
            name="daily_record",
            description="录入某一天的健康数据：体重、睡眠时长、步数、血压、饮水量。"
                        "用户说“今天睡了7小时”“血压130/85”时调用本工具。未提供的字段留空即可。"
        )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        day = parameters.get("day") or date.today().isoformat()

        def opt(key, cast):
            v = parameters.get(key)
            return cast(v) if v not in (None, "", "null") else None

        record = DailyRecord(
            day=day,
            weight_kg=opt("weight_kg", float),
            sleep_hours=opt("sleep_hours", float),
            steps=opt("steps", int),
            systolic=opt("systolic", int),
            diastolic=opt("diastolic", int),
            water_ml=opt("water_ml", int),
            note=parameters.get("note", "") or "",
        )
        storage.upsert_record(record)

        filled = {k: v for k, v in record.to_dict().items() if v not in (None, "", day)}
        return f"{day} 数据已保存：" + "，".join(f"{k}={v}" for k, v in filled.items())

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="day", type="string", description="日期 YYYY-MM-DD，缺省为今天", required=False),
            ToolParameter(name="weight_kg", type="number", description="体重（千克），纯数字", required=False),
            ToolParameter(name="sleep_hours", type="number", description="睡眠时长（小时），纯数字", required=False),
            ToolParameter(name="steps", type="integer", description="步数，纯数字", required=False),
            ToolParameter(name="systolic", type="integer", description="收缩压（高压），纯数字", required=False),
            ToolParameter(name="diastolic", type="integer", description="舒张压（低压），纯数字", required=False),
            ToolParameter(name="water_ml", type="integer", description="饮水量（毫升），纯数字", required=False),
            ToolParameter(name="note", type="string", description="备注", required=False),
        ]


class MetricsTool(BaseHealthTool):
    """计算健康指标。"""

    def __init__(self):
        super().__init__(
            name="health_metrics",
            description="计算 BMI、基础代谢率、每日能量消耗、血压分级、睡眠评估、饮水目标。"
                        "任何涉及具体数值或分级的回答都必须先调用本工具，不得自行估算。"
        )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        profile = storage.load_profile()
        if not profile:
            return "缺少用户档案，请先调用 profile 工具（action=set）录入性别、年龄、身高、体重。"
        records = storage.load_records()
        return json.dumps(summarize(profile, records), ensure_ascii=False)

    def get_parameters(self) -> List[ToolParameter]:
        return []


class TrendTool(BaseHealthTool):
    """查看最近若干天的数据趋势。"""

    def __init__(self):
        super().__init__(
            name="health_trend",
            description="查看最近 N 天的体重、睡眠、步数、血压变化，用于回答“最近怎么样”这类问题。"
        )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        days = int(parameters.get("days", 7))
        records = storage.load_records()[-days:]
        if not records:
            return "暂无历史记录。"

        rows = []
        for r in records:
            rows.append({
                "day": r.day,
                "weight_kg": r.weight_kg,
                "sleep_hours": r.sleep_hours,
                "steps": r.steps,
                "bp": f"{r.systolic}/{r.diastolic}" if r.systolic and r.diastolic else None,
            })

        weights = [r.weight_kg for r in records if r.weight_kg is not None]
        summary = {"days": len(records)}
        if len(weights) >= 2:
            summary["weight_change_kg"] = round(weights[-1] - weights[0], 1)

        return json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="days", type="integer", description="回溯天数，默认 7", required=False),
        ]
