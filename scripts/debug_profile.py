import sys
import traceback
import inspect
from pathlib import Path

# 把项目根目录加入 sys.path，无论从哪运行都能 import src
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hello_agents import ToolRegistry
from hello_agents.tools import Tool
from src.tools import ProfileTool

print("ROOT:", ROOT)
print("Tool.run sig       :", inspect.signature(Tool.run))
print("Tool.validate sig  :", inspect.signature(Tool.validate_parameters))
print("ProfileTool.run sig:", inspect.signature(ProfileTool.run))

t = ProfileTool()

print("\n--- get_parameters ---")
try:
    ps = t.get_parameters()
    print("params count:", len(ps))
    for p in ps:
        print("  ", p)
except Exception:
    traceback.print_exc()

params = {
    "action": "set",
    "name": "rill",
    "sex": "male",
    "age": 24,
    "height_cm": 175,
    "weight_kg": 70,
    "activity": "light",
}

print("\n--- direct run ---")
try:
    print("RESULT:", t.run(params))
except Exception:
    traceback.print_exc()

print("\n--- validate_parameters ---")
try:
    print("VALIDATED:", t.validate_parameters(params))
except Exception:
    traceback.print_exc()

print("\n--- registry.execute_tool ---")
r = ToolRegistry()
r.register_tool(t)
try:
    print("EXEC:", r.execute_tool("profile", params))
except Exception:
    traceback.print_exc()
