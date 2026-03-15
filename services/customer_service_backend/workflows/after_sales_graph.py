from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langgraph.types import RetryPolicy

from customer_service_backend.agents.supervisor_agent import AgentState
from customer_service_backend.agents.supervisor_agent import supervisor_agent_node, guardrail_node
from customer_service_backend.agents.tech_agent import tech_agent_node
from customer_service_backend.agents.service_agent import service_agent_node

# 1. 初始化图 (Graph)
# StateGraph 是 LangGraph 的核心。AgentState 是一个 TypedDict，
# 它定义了在这些智能体之间流转的“共享内存”（比如对话历史 messages、下一步去哪 next_agent）。
workflow = StateGraph(AgentState)

# 为节点配置重试策略：最多重试 3 次，初始等待 2 秒，指数退避
robust_retry = RetryPolicy(max_attempts=3, initial_interval=2.0, backoff_factor=2.0)

# 2. 添加所有智能体节点 (Nodes)
# 节点是图中的“执行单元”。把我们写好的异步函数（或大模型调用链）注册进图中。
# 这里的 "Supervisor" 等字符串是节点的 ID，后面连线时全靠这个 ID 识别。
workflow.add_node("Guardrail", guardrail_node)
workflow.add_node("Supervisor", supervisor_agent_node, retry=robust_retry) # 大脑：负责分发任务
workflow.add_node("TechAgent", tech_agent_node, retry=robust_retry)        # 专员A：负责技术排障
workflow.add_node("ServiceAgent", service_agent_node, retry=robust_retry)  # 专员B：负责售后与网点查询


# 入口先走护栏
workflow.set_entry_point("Guardrail")
# 护栏根据结果，决定是去主管，还是直接滚蛋(FINISH)
workflow.add_conditional_edges(
    "Guardrail",
    lambda state: "Supervisor" if state["next_agent"] == "Supervisor" else "FINISH",
    {"Supervisor": "Supervisor", "FINISH": END}
)

# 3. 制定路由规则（核心的注入与分发逻辑）
# 条件边 (Conditional Edges) 决定了图的动态走向。
workflow.add_conditional_edges(
    "Supervisor",                          # 起点：每次从 Supervisor 出来后触发
    lambda state: state["next_agent"],     # 路由条件函数：读取 Supervisor 写入 state 的决策结果
    {
        # 路由映射表：如果上一行的 lambda 返回 "TechAgent"，就走到对应的 "TechAgent" 节点
        "TechAgent": "TechAgent",
        "ServiceAgent": "ServiceAgent",
        "FINISH": END                      # END 是 LangGraph 的内置节点，代表整个流程完美结束
    }
)

# 4. 子智能体汇报机制（形成执行闭环）
# 普通的无条件边 (Normal Edges)。
# 规定了 TechAgent 和 ServiceAgent 只要执行完毕，无论结果如何，
# 都必须无条件地把最新的 state 交回给 Supervisor。
# 由 Supervisor 来决定是继续派发下一个任务，还是结束服务。
workflow.add_edge("TechAgent", "Supervisor")
workflow.add_edge("ServiceAgent", "Supervisor")

# 6. 创建 MemorySaver
memory = MemorySaver()

# compile() 会将定义好的节点和边冻结，编译成一个可执行的 Runnable 应用 (app)。
# 你后续只需要调用 app.ainvoke({"messages": [...]}) 即可启动整个 Multi-Agent 流程。
app = workflow.compile()

# ==========================================
# 📊 LangGraph 可视化调试工具
# ==========================================

def visualize_graph(compiled_app):
    print("\n" + "=" * 50)
    print("🚀 正在生成 Agent 架构可视化图...")
    print("=" * 50 + "\n")

    # 【方式一】终端字符画 (ASCII) - 最快，零依赖，直接在控制台看
    print("【1】终端 ASCII 流程图：")
    try:
        print(compiled_app.get_graph().print_ascii())
    except Exception as e:
        print(f"生成 ASCII 图失败: {e}")

    print("\n" + "-" * 50 + "\n")

    # 【方式二】保存为高清 PNG 图片 - 适合做文档和复杂架构排查
    print("【2】正在尝试生成高清 PNG 图片 (graph_visualization.png)...")
    try:
        # draw_mermaid_png() 底层会调用 Mermaid 的 API 生成图片字节流
        png_bytes = compiled_app.get_graph().draw_mermaid_png()

        # 将字节流写入本地文件
        with open("graph_visualization.png", "wb") as f:
            f.write(png_bytes)
        print("✅ 成功！流程图已保存至当前目录下的 'graph_visualization.png'")

    except Exception as e:
        print(f"❌ 生成图片失败 (可能是网络原因或缺少依赖): {e}")

    print("\n" + "=" * 50)

