import asyncio
import langchain
from langchain_core.messages import HumanMessage
from services.customer_service_backend.workflows.after_sales_graph import app


# 从你的模块中导入编译好的 app (请替换为实际的导入路径)
# from customer_service_backend.graph_app import app

# 开启全局调试模式
langchain.debug = True

async def run_simulation():
    print("\n" + "=" * 50)
    print("🚀 开始 Multi-Agent 架构多轮连贯对话测试")
    print("=" * 50)

    # 我们为这次测试设定一个唯一的会话 ID
    # LangGraph 会自动根据这个 ID 提取对应的历史记忆
    config = {"configurable": {"thread_id": "test_session_001"}}

    # 模拟真实用户的连续 3 次提问
    test_queries = [
        # 轮次 1：纯技术问题 -> 测试 Supervisor 是否路由给 TechAgent
        # "为什么win 7 删除文件后，在回收站找不到？顺便看一下今天的天气怎么样",

        # 轮次 2：售后网点查询 -> 测试 Supervisor 是否结合上下文，路由给 ServiceAgent 并调用 SQLite 测距工具
        "我在郑州二七广场附近，能帮我查一下最近的联想售后点吗？我要拿过去修。",

        # 轮次 3：结束对话 -> 测试 Supervisor 是否能判断意图，输出 FINISH 结束流转
        # "好的，太详细了，非常感谢，我下午就拿过去。没有其他问题了。"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n💬 [第 {i} 轮] 👤 用户输入: {query}")
        print("-" * 50)

        # 每次只需要传入【最新的一条消息】，不用管历史记录，MemorySaver 会搞定！
        inputs = {"messages": [HumanMessage(content=query)]}

        # 使用 astream 可以实时看到状态在哪个节点流转
        async for event in app.astream(inputs, config=config, stream_mode="updates"):
            # event 是一个字典，key 是当前执行完毕的节点名字，value 是它对 state 的更新
            for node_name, state_update in event.items():
                print(f"🔄 [流转日志] 节点 [{node_name}] 执行完毕")

                # 打印出智能体的回复（如果有的话）
                if "messages" in state_update:
                    messages = state_update["messages"]
                    if not isinstance(messages, list):
                        messages = [messages]
                    for msg in messages:
                        print(f"🤖 [{node_name} 回复]:\n{msg.content}\n")


if __name__ == "__main__":
    asyncio.run(run_simulation())