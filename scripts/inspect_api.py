import inspect
from hello_agents import HelloAgentsLLM, SimpleAgent, ToolRegistry
from hello_agents.tools import Tool, ToolParameter

print("Tool.__init__      :", inspect.signature(Tool.__init__))
print("Tool methods       :", [m for m in dir(Tool) if not m.startswith('_')])
print("ToolParameter      :", inspect.signature(ToolParameter.__init__))
print("SimpleAgent.__init__:", inspect.signature(SimpleAgent.__init__))
print("SimpleAgent methods:", [m for m in dir(SimpleAgent) if not m.startswith('_')])
print("ToolRegistry methods:", [m for m in dir(ToolRegistry) if not m.startswith('_')])
