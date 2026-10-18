import inspect
from typing import Any, Dict, List
from hello_agents import ToolRegistry
from hello_agents.tools import Tool, ToolParameter

print("Tool.run signature     :", inspect.signature(Tool.run))
print("Tool.get_parameters sig:", inspect.signature(Tool.get_parameters))
print("execute_tool signature :", inspect.signature(ToolRegistry.execute_tool))

# 1) ToolParameter 字段实测
try:
    p = ToolParameter(name="action", type="string", description="test", required=True)
    print("ToolParameter ok      :", p)
    print("  fields              :", list(p.model_fields.keys()) if hasattr(p, "model_fields") else dir(p))
except Exception as e:
    print("ToolParameter FAILED  :", type(e).__name__, e)

# 2) 最小 Tool 子类（完全照教程风格）
class EchoTool(Tool):
    def __init__(self):
        super().__init__(name="echo", description="回显输入")
    def run(self, parameters: Dict[str, Any]) -> str:
        return f"echo: {parameters.get('text', '')}"
    def get_parameters(self) -> List[ToolParameter]:
        return [ToolParameter(name="text", type="string", description="要回显的文本", required=True)]

t = EchoTool()
print("to_dict               :", t.to_dict())
print("to_openai_schema      :", t.to_openai_schema())

# 3) 注册 + 执行
r = ToolRegistry()
r.register_tool(t)
print("list_tools            :", r.list_tools())
try:
    print("execute_tool          :", r.execute_tool("echo", {"text": "hello"}))
except Exception as e:
    print("execute_tool FAILED   :", type(e).__name__, e)
