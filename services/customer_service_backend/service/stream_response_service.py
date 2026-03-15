import uuid
import asyncio
from typing import AsyncGenerator
from langchain_core.messages import AIMessageChunk

# 引入你的工厂和格式化函数 (路径请按实际项目调整)
from customer_service_backend.api.schemas.response import ContentKind
from customer_service_backend.utils.response_util import ResponseFactory
from customer_service_backend.utils.text_util import format_tool_call_html, format_agent_update_html


async def process_stream_response(app, inputs: dict, config: dict, message_id: str = None) -> AsyncGenerator:
    """
    基于 LangChain v0.1+ / LangGraph 架构重构的流式事件处理。
    统一捕获 Token、推理过程(o1/DeepSeek等)、工具调用和智能体状态切换。

    Args:
        app: 编译好的 LangGraph 实例 (workflow.compile())
        inputs: 传给图的初始输入，如 {"messages": [HumanMessage(...)]}
        config: 包含 thread_id 等配置的字典
        message_id: 全局唯一标识，用于关联同一个 SSE 流
    """
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex}"

    try:
        # 🌟 核心：使用 LangChain 官方推荐的 v2 流式事件 API
        async for event in app.astream_events(inputs, config=config, version="v2"):
            kind = event["event"]

            # ------------------------------------------------------------------
            # 1. 文本与推理生成事件 (Text & Reasoning)
            # ------------------------------------------------------------------
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]

                if isinstance(chunk, AIMessageChunk):
                    # 1.1 提取推理过程 (兼容 DeepSeek R1, QwQ, OpenAI o1 等思考模型)
                    # 现代 LangChain 支持原生 chunk.reasoning_content，部分厂商 API 放在 additional_kwargs 中
                    reasoning = getattr(chunk, "reasoning_content", None)
                    if not reasoning and "reasoning_content" in chunk.additional_kwargs:
                        reasoning = chunk.additional_kwargs["reasoning_content"]

                    if reasoning:
                        yield "data: " + ResponseFactory.build_text(
                            text=reasoning,
                            kind=ContentKind.THINKING,
                            message_id=message_id
                        ).model_dump_json() + "\n\n"

                    # 1.2 提取常规文本输出 (ANSWER)
                    if chunk.content:
                        # 确保只处理字符串内容 (有时大模型调用工具时 content 会是 list 结构)
                        if isinstance(chunk.content, str):
                            yield "data: " + ResponseFactory.build_text(
                                text=chunk.content,
                                kind=ContentKind.ANSWER,
                                message_id=message_id
                            ).model_dump_json() + "\n\n"

            # ------------------------------------------------------------------
            # 2. 工具调用事件 (Tool Call)
            # ------------------------------------------------------------------
            elif kind == "on_tool_start":
                # LangChain 触发工具时的事件名称即为工具名
                tool_name = event["name"]

                html_card = format_tool_call_html(tool_name)
                yield "data: " + ResponseFactory.build_text(
                    text=html_card + "\n",
                    kind=ContentKind.PROCESS,
                    message_id=message_id
                ).model_dump_json() + "\n\n"

            # ------------------------------------------------------------------
            # 3. 智能体状态更新 (Agent Node Transition)
            # ------------------------------------------------------------------
            elif kind == "on_chain_start":
                # 在 LangGraph 中，可以通过 event 的 metadata 捕获节点流转
                metadata = event.get("metadata", {})
                node_name = metadata.get("langgraph_node")

                # 白名单过滤：只处理真实的智能体节点，忽略系统底层路由节点 (如 __start__, ToolRouter 等)
                valid_agents = ["TechAgent", "ServiceAgent", "Supervisor"]

                if node_name and node_name in valid_agents:
                    html_card = format_agent_update_html(node_name)
                    yield "data: " + ResponseFactory.build_text(
                        text=html_card + "\n",
                        kind=ContentKind.PROCESS,
                        message_id=message_id
                    ).model_dump_json() + "\n\n"

        # ------------------------------------------------------------------
        # 4. 正常发送结束信号
        # ------------------------------------------------------------------
        yield "data: " + ResponseFactory.build_finish(message_id).model_dump_json() + "\n\n"

    except asyncio.CancelledError:
        print(f"⚠️ 流传输中止 (Message ID: {message_id})")
        raise

    except Exception as e:
        # ------------------------------------------------------------------
        # 5. 异常发送结束信号 (使用工厂的 build_error)
        # ------------------------------------------------------------------
        yield "data: " + ResponseFactory.build_error(
            error_message=f"Agent 执行崩溃: {str(e)}",
            message_id=message_id
        ).model_dump_json() + "\n\n"