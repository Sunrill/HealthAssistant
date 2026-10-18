import sys, inspect
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hello_agents.tools import Tool
from hello_agents.tools.response import ToolResponse

print("ToolResponse.__init__:", inspect.signature(ToolResponse.__init__))
print("ToolResponse fields  :", getattr(ToolResponse, "__dataclass_fields__", None) and list(ToolResponse.__dataclass_fields__.keys()))
print("ToolResponse methods :", [m for m in dir(ToolResponse) if not m.startswith("_")])

try:
    from hello_agents.tools.response import ToolStatus
    print("ToolStatus members   :", list(ToolStatus))
except Exception as e:
    print("ToolStatus import fail:", e)

print("\n--- Tool.run_with_timing source ---")
try:
    print(inspect.getsource(Tool.run_with_timing))
except Exception as e:
    print("no source:", e)
