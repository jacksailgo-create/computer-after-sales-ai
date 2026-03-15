import logging
import operator
from typing import TypedDict, Annotated, Literal

from langchain_core.messages import BaseMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage

from core.prompt_manager import prompt_manager
from core.factory import ModelFactory

logger = logging.getLogger(__name__)


# ==========================================
# 1. 定义状态 (State)
# ==========================================
class AgentState(TypedDict):
    """LangGraph 中流转的全局状态机"""
    messages: Annotated[list[BaseMessage], operator.add]
    next_agent: Literal["TechAgent", "ServiceAgent", "FINISH"]  # 👈 记录下一步要交给哪个智能体


# ==========================================
# 2. 定义路由决策模型 (Schema)
# ==========================================
class RouteDecision(BaseModel):
    """强制 LLM 输出的结构化数据字典"""
    reasoning: str = Field(
        ...,
        description="【必填】思考过程：在做出决定前，请仔细一步步分析用户的意图、当前对话上下文，以及用户的核心诉求是否已经彻底解决。"
    )
    next_agent: Literal["TechAgent", "ServiceAgent", "FINISH"] = Field(
        ...,
        description="决定下一个负责处理的智能体。技术排障选TechAgent，查网点/售后选ServiceAgent，无明确需求或问题已解决选FINISH。"
    )


# ==========================================
# 3. 主调度节点 (Node)
# ==========================================
async def supervisor_agent_node(state: AgentState) -> dict:
    """
    主调度智能体 (Supervisor)
    负责理解上下文意图，并决定下一个接手的子智能体。
    """
    logger.info("🛠️ [Node: Supervisor] 主调度开始评估任务归属...")

    # 1. 从工厂获取 LLM
    llm = ModelFactory.create_llm(role_name='supervisor_agent')

    # 2. 强制使用 function_calling 模式输出结构化数据
    # (兼容性极佳，专治各种国产大模型的 400 报错)
    router_llm = llm.with_structured_output(RouteDecision)

    # 3. 读取 System Prompt
    system_prompt_str, _ = prompt_manager.get_prompt_with_vars("supervisor_prompts_v1", "supervisor_agent")

    # 4. 🌟 组装最终的 Prompt (统一使用 LangChain 的 Message 对象，避免字典混搭引发的类型解析报错)
    # 注意：确保传入的是列表
    messages = [SystemMessage(content=system_prompt_str)] + state["messages"]

    try:
        # 5. 调用大模型进行路由决策
        decision = await router_llm.ainvoke(messages)

        # 🛡️ 核心修复：增加对 None 值的拦截
        # if decision is None or not hasattr(decision, 'reasoning'):
        #     logger.warning("⚠️ 大模型未返回标准的结构化数据，触发安全降级。")
        #     return {"next_agent": "FINISH"}

        # 6. 打印大模型的思考过程 (极其方便开发调试)
        print("\n" + "=" * 50)
        print(f"🧠 [主管思考过程]: {decision.reasoning}")
        print(f"👉 [主管派单决定]: {decision.next_agent}")
        print("=" * 50 + "\n")

        # 7. 返回增量 State (更新 next_agent)
        return {"next_agent": decision.next_agent}

    except Exception as e:
        logger.error(f"Supervisor 路由决策失败: {e}")
        # 🛑 兜底机制：如果大模型抽风报错，或者触发了安全拦截，默认结束流程，避免死循环
        return {"next_agent": "FINISH"}


async def guardrail_node(state: AgentState) -> dict:
    logger.info("🛡️ [Node: Guardrail] 执行安全与边界检查...")
    last_msg = state["messages"][-1].content

    # 简单的规则拦截 (也可以调用一个便宜的小模型专门做意图分类)
    forbidden_words = ["写代码", "翻译", "政治", "忽略之前的指令"]
    if any(word in last_msg for word in forbidden_words):
        logger.warning("🚨 触发安全护栏拦截！")
        # 伪造一个系统拒绝回复，并强制引导图走向 END
        reject_msg = AIMessage(content="抱歉，作为电脑售后客服，我无法回答与技术支持/售后服务无关的问题。")
        return {"messages": [reject_msg], "next_agent": "FINISH"}

    # 安全通过，放行给主管
    return {"next_agent": "Supervisor"}