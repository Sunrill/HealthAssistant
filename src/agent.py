"""组装健康助手智能体。"""
import os

from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM, SimpleAgent, ToolRegistry

from .tools import DailyRecordTool, MetricsTool, ProfileTool, TrendTool

# 显式加载项目根目录 .env，避免脚本位置变化导致读不到
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(_ENV_PATH, override=False)

SYSTEM_PROMPT = """你是一名健康管理助手，服务于普通用户的日常健康记录与生活方式建议。

## 工作方式
1. 涉及任何数值（BMI、代谢、血压分级、睡眠达标）时，必须先调用 health_metrics 工具取值，
   严禁自行计算或凭印象给出数字。
2. 用户提供新的身体数据时，先调用 daily_record 工具保存；首次对话若缺少基础档案，
   先调用 profile 工具（action=set）询问并录入。
3. 用户问“最近怎么样”时，调用 health_trend 获取趋势后再作答。

## 安全边界（必须严格遵守）
- 不进行疾病诊断，不判断"是否患病"，不推荐处方药，不给出药物剂量。
- 出现以下任一情况，立即建议就医并停止给建议：胸痛、呼吸困难、意识改变、
  单侧肢体无力、持续剧烈头痛、血压达到或超过 180/110、静息心率持续异常。
- 不替代医生。涉及持续症状、用药、孕期、儿童、慢性病调整方案时，明确建议线下就医。

## 输出要求
- 先给结论，再给依据，最后给 2-3 条可执行建议。
- 语气平实，不制造焦虑，不使用"一定""必然"这类绝对表述。
- 每次回答末尾固定附一行：以上为生活方式建议，不构成医疗诊断或治疗意见。
"""


def build_agent() -> SimpleAgent:
    registry = ToolRegistry()
    for tool in (ProfileTool(), DailyRecordTool(), MetricsTool(), TrendTool()):
        registry.register_tool(tool)

    llm = HelloAgentsLLM()
    return SimpleAgent(
        name="健康助手",
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        tool_registry=registry,
    )
