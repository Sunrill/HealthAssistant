from dotenv import load_dotenv

load_dotenv()

from hello_agents import HelloAgentsLLM

llm = HelloAgentsLLM()
print("MODEL:", llm.model)

resp = llm.invoke([{"role": "user", "content": "用一句话说明你是谁。"}])
print("RESPONSE:", resp.content)
print("TOKENS:", resp.usage.get("total_tokens"))
