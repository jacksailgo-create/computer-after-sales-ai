import asyncio
from langchain_core.messages import HumanMessage

from services.customer_service_backend.agents.tech_agent import tech_agent_node


async def run_test():
    print("🚀 开始独立测试 TechAgent 节点...\n")

    # 1. 伪造 LangGraph 的输入状态 (State)
    # 模拟用户遇到电脑故障，向系统发起提问
    mock_state = {
        "messages": [
            HumanMessage(content="牙痛怎么办")
        ]
    }

    print("👤 模拟输入 State:")
    print(f"   [HumanMessage]: {mock_state['messages'][0].content}\n")
    print("-" * 50)

    try:
        # 2. 执行节点逻辑
        # 这里会自动触发大模型思考，并去调用你合并好的本地知识库和 MCP 搜索工具
        new_state = await tech_agent_node(mock_state)

        # 3. 解析并验证输出
        print("\n" + "=" * 50)
        print("✅ 节点执行完成！返回的增量状态 (State Update) 如下：\n")

        # 正常情况下，new_state 应该包含一个 {"messages": [AIMessage(...)]}
        if "messages" in new_state and new_state["messages"]:
            for msg in new_state["messages"]:
                print(f"[{msg.__class__.__name__}]:")
                print(msg.content)
        else:
            print("⚠️ 警告: 节点没有返回任何消息更新！")
            print("原始返回:", new_state)

        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        # 如果报错，通常是因为工具包合并错误，或者大模型鉴权失败


if __name__ == "__main__":
    asyncio.run(run_test())