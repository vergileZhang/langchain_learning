from dataclasses import dataclass
from typing import List, Dict, Any

from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver


SYSTEM_PROMPT = """
你是一名电商平台的个性化客服助手。

你的职责：
1. 优先帮助用户处理订单、退款、物流、会员权益等问题
2. 回答时要结合用户身份信息和订单信息
3. 如果用户的问题涉及“我的订单”“我的会员”“帮我查一下”，优先使用工具查询
4. 如果用户没有明确说订单号，但问题明显在问“最近订单”，可以先查用户订单
5. 语气专业、简洁、清楚，不要编造不存在的信息
6. 如果工具已经返回了结果，就基于结果回答，不要重复要求用户提供已经知道的信息
"""


# 模拟用户数据库
USER_DB = {
    "u1001": {
        "name": "张三",
        "vip_level": "Gold",
        "city": "Shanghai",
        "language": "zh",
    },
    "u1002": {
        "name": "李四",
        "vip_level": "Normal",
        "city": "Shenzhen",
        "language": "zh",
    },
}

# 模拟订单数据库
ORDER_DB = {
    "u1001": [
        {
            "order_id": "A001",
            "item": "机械键盘",
            "status": "已发货",
            "tracking_no": "SF123456",
            "refund_available": False,
        },
        {
            "order_id": "A002",
            "item": "无线鼠标",
            "status": "已签收",
            "tracking_no": "SF888888",
            "refund_available": True,
        },
    ],
    "u1002": [
        {
            "order_id": "B001",
            "item": "显示器",
            "status": "处理中",
            "tracking_no": None,
            "refund_available": False,
        }
    ],
}


@dataclass
class CustomerContext:
    user_id: str


@tool
def get_current_user_profile(runtime: ToolRuntime[CustomerContext]) -> str:
    """获取当前登录用户的资料信息。"""
    user_id = runtime.context.user_id
    user = USER_DB.get(user_id)

    if not user:
        return "未找到该用户信息"

    return (
        f"用户ID: {user_id}, "
        f"姓名: {user['name']}, "
        f"会员等级: {user['vip_level']}, "
        f"城市: {user['city']}, "
        f"语言: {user['language']}"
    )


@tool
def get_my_orders(runtime: ToolRuntime[CustomerContext]) -> str:
    """获取当前登录用户的订单列表。"""
    user_id = runtime.context.user_id
    orders = ORDER_DB.get(user_id, [])

    if not orders:
        return "当前用户没有订单记录"

    lines = []
    for order in orders:
        lines.append(
            f"订单号: {order['order_id']}, "
            f"商品: {order['item']}, "
            f"状态: {order['status']}, "
            f"物流单号: {order['tracking_no']}, "
            f"是否可退款: {order['refund_available']}"
        )
    return "\n".join(lines)


@tool
def get_order_by_id(order_id: str, runtime: ToolRuntime[CustomerContext]) -> str:
    """根据订单号查询当前登录用户的订单详情。"""
    user_id = runtime.context.user_id
    orders = ORDER_DB.get(user_id, [])

    for order in orders:
        if order["order_id"] == order_id:
            return (
                f"订单号: {order['order_id']}, "
                f"商品: {order['item']}, "
                f"状态: {order['status']}, "
                f"物流单号: {order['tracking_no']}, "
                f"是否可退款: {order['refund_available']}"
            )

    return f"未找到订单号 {order_id} 对应的订单"


@tool
def apply_refund(order_id: str, runtime: ToolRuntime[CustomerContext]) -> str:
    """为当前登录用户的指定订单申请退款。仅做演示，不会真的调用外部系统。"""
    user_id = runtime.context.user_id
    orders = ORDER_DB.get(user_id, [])

    for order in orders:
        if order["order_id"] == order_id:
            if order["refund_available"]:
                return f"订单 {order_id} 已提交退款申请，预计 1-3 个工作日处理完成"
            return f"订单 {order_id} 当前不满足退款条件"

    return f"未找到订单号 {order_id}，无法申请退款"


checkpointer = InMemorySaver()

agent = create_agent(
    model="deepseek-chat",
    tools=[
        get_current_user_profile,
        get_my_orders,
        get_order_by_id,
        apply_refund,
    ],
    system_prompt=SYSTEM_PROMPT,
    context_schema=CustomerContext,
    checkpointer=checkpointer,
)

config = {"configurable": {"thread_id": "customer-thread-001"}}
context = CustomerContext(user_id="u1001")


# 第一轮
response1 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "我想看看我的订单，顺便告诉我我是什么会员",
            }
        ]
    },
    config=config,
    context=context,
)

print("第一轮回复:")
print(response1["messages"][-1].content)
print("-" * 50)

# 第二轮：测试记忆
response2 = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "那我最近这个已经签收的订单可以退款吗？帮我直接申请一下",
            }
        ]
    },
    config=config,
    context=context,
)

print("第二轮回复:")
print(response2["messages"][-1].content)
