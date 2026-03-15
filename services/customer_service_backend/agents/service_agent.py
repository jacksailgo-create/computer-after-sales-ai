import logging
from langchain_core.messages import AIMessage

# ✅ 只引入我们在 MCP 测试中跑通的 create_agent
from langchain.agents import create_agent

from core.prompt_manager import prompt_manager
from core.factory import ModelFactory

from clients.local.service_stations_client import get_user_coordinates, find_nearest_stations
# ✅ 注意这里导入的是刚才修改的工具加载器函数
from clients.mcp.mcp_client import load_mcp_map_tools

logger = logging.getLogger(__name__)


async def service_agent_node(state: dict) -> dict:
    """
    全能业务智能体
    """
    logger.info("🛠️ [Node: ServiceAgent] 全能业务智能体介入...")

    # 1. 从工厂获取 LLM
    llm = ModelFactory.create_llm(role_name='service_agent')

    # 2. 读取 System Prompt
    system_prompt_str, _ = prompt_manager.get_prompt_with_vars("service_prompts", "service_agent")

    # 补充上下文要求
    full_system_prompt = (
        f"{system_prompt_str}"
    )

    # 3. 准备本地工具
    local_tools = [get_user_coordinates, find_nearest_stations]

    # 4. 动态拉取远程 MCP 工具（地图服务）
    try:
        mcp_tools = await load_mcp_map_tools()
    except Exception as e:
        logger.error(f"拉取 MCP 工具失败，将降级仅使用本地知识库: {e}")
        mcp_tools = []

    # 5. 合并所有可用工具
    all_tools = mcp_tools + local_tools

    # 6. 🚀 使用现代模式创建 Agent (内部会自动编译为一个支持工具调用的 LangGraph)
    agent = create_agent(
        model=llm,
        tools=all_tools,
        system_prompt=full_system_prompt  # 直接传入 String，它会自动作为 System Message 注入
    )

    # 从 State 中获取对话历史
    messages = state.get("messages", [])

    try:
        logger.info("开始业务逻辑分析...")

        # 7. 异步执行 Agent
        response = await agent.ainvoke({"messages": messages})

        # 8. 提取最终的自然语言回复 (response["messages"] 的最后一条)
        final_message = response["messages"][-1]

        # 9. 返回增量 State
        return {"messages": [final_message]}

    except Exception as e:
        logger.error(f"ServiceAgent 执行异常: {e}")
        # 如果大模型调用出错，给出一个优雅的降级回复
        error_msg = AIMessage(content=f"抱歉，全能服务系统暂时遇到网络波动，请稍后再试。({str(e)})")
        return {"messages": [error_msg]}