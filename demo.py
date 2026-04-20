from langchain.agents import create_agent
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
SYSTEM_PROMPT = """你是一位擅长用双关语表达的专家天气预报员。

你可以使用两个工具：

- get_weather_for_location：用于获取特定地点的天气
- get_user_location：用于获取用户的位置

如果用户询问天气，请确保你知道具体位置。如果从问题中可以判断他们指的是自己所在的位置，请使用 get_user_location 工具来查找他们的位置。"""

@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"

@dataclass
class Context:
    """自定义运行时上下文模式。"""
    user_id: str

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """根据用户 ID 获取用户信息。"""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"

config = {"configurable": {"thread_id": "1"}}

agent = create_agent(
    model="deepseek-chat",
    tools=[get_user_location, get_weather_for_location],
    system_prompt=SYSTEM_PROMPT
)

response = agent.invoke(
    {
        "messages": [
            {"role": "user", "content": "我之前问了什么问题，帮我回忆一下"}
        ]
    },
    config=config,
    context=Context(user_id="1")
)

print(response)
print(response["messages"][-1].content)