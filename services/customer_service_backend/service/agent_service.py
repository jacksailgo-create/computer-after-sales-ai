import json
import re
import uuid
import asyncio
from langchain_core.messages import HumanMessage, AIMessage

# 引入你的响应工厂和枚举
from customer_service_backend.api.schemas.response import ContentKind
from customer_service_backend.utils.response_util import ResponseFactory

# 引入 UI 卡片生成器
from customer_service_backend.utils.text_util import format_tool_call_html, format_agent_update_html

# 引入会话管理服务
from customer_service_backend.service.session_service import session_service

# 引入编译好的 LangGraph app
from customer_service_backend.workflows.after_sales_graph import app


class MultiAgentService:
    """
    智能体核心业务服务：负责与 LangGraph 交互、管理上下文记忆，并将状态实时转化为 SSE 流。
    """

    @staticmethod
    async def process_task(request_context, flag: bool = True):
        user_id = request_context.context.user_id
        session_id = request_context.context.session_id
        query = request_context.query

        message_id = f"msg_{uuid.uuid4().hex}"

        # 📂 记忆加载阶段
        chat_history = session_service.prepare_history(
            user_id=user_id,
            session_id=session_id,
            user_input=query,
            max_turn=5
        )

        inputs = {"messages": chat_history}
        config = {"configurable": {"thread_id": session_id}}

        # 🛡️ 状态追踪变量
        announced_nodes = set()
        final_state_messages = None
        supervisor_raw_output = ""

        try:
            init_packet = ResponseFactory.build_text("正在建立安全连接...\n", ContentKind.THINKING, message_id)
            yield f"data: {init_packet.model_dump_json()}\n\n"

            # 🌟 核心监听：使用 astream_events
            async for event in app.astream_events(inputs, config=config, version="v2"):
                kind = event["event"]
                event_name = event["name"]

                # 🎯 拦截 A: 真实的 Token 级流式输出
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    node_name = event.get("metadata", {}).get("langgraph_node")

                    # 拦截主调度中心 (Supervisor) 的内部输出
                    if node_name == "Supervisor":
                        if chunk.content and isinstance(chunk.content, str):
                            supervisor_raw_output += chunk.content
                        continue

                    # 提取思考过程 (o1 / DeepSeek 等推理模型)
                    reasoning = getattr(chunk, "reasoning_content", None) or chunk.additional_kwargs.get(
                        "reasoning_content")
                    if reasoning:
                        yield f"data: {ResponseFactory.build_text(reasoning, ContentKind.THINKING, message_id).model_dump_json()}\n\n"

                    # 提取正式文本
                    if chunk.content and isinstance(chunk.content, str):
                        yield f"data: {ResponseFactory.build_text(chunk.content, ContentKind.ANSWER, message_id).model_dump_json()}\n\n"

                # 🎯 拦截 B: 工具调用 (Tool Call)
                elif kind == "on_tool_start":
                    html_card = format_tool_call_html(event_name)
                    # 移除了多余的 \n，保证 UI 紧凑
                    yield f"data: {ResponseFactory.build_text(html_card, ContentKind.PROCESS, message_id).model_dump_json()}\n\n"

                # 🎯 拦截 C: 智能体节点切换 (包含 snake_case 命名)
                elif kind == "on_chain_start":
                    # 🚨 修复：加入了 service_agent_node 和 tech_agent_node
                    valid_agent_nodes = ["Supervisor", "TechAgent", "ServiceAgent", "tech_agent_node",
                                         "service_agent_node"]

                    if event_name in valid_agent_nodes:
                        if event_name not in announced_nodes:
                            announced_nodes.add(event_name)
                            html_card = format_agent_update_html(event_name)
                            # 移除了多余的 \n
                            yield f"data: {ResponseFactory.build_text(html_card, ContentKind.PROCESS, message_id).model_dump_json()}\n\n"

                # 🎯 拦截 D: 捕获最终执行状态
                elif kind == "on_chain_end":

                    # 🚨 修复：处理 Supervisor 理由，替换中文字段并去除 \n
                    if event_name == "Supervisor" and supervisor_raw_output:
                        reasoning_text = ""
                        try:
                            clean_json = re.sub(r"```json|```", "", supervisor_raw_output).strip()
                            parsed_data = json.loads(clean_json)
                            reasoning_text = parsed_data.get("reasoning", "")
                        except Exception:
                            # 降级处理：如果不是标准 JSON，直接拿原话
                            reasoning_text = supervisor_raw_output.strip()

                        if reasoning_text:
                            # 1. 强制清理所有的换行符，用空格代替避免字词粘连
                            reasoning_text = reasoning_text.replace("\n", " ").replace("\r", "")
                            # 2. 将底层英文节点名翻译为友好的中文
                            reasoning_text = reasoning_text.replace("service_agent_node", "售后服务专家")
                            reasoning_text = reasoning_text.replace("ServiceAgent", "售后服务专家")
                            reasoning_text = reasoning_text.replace("tech_agent_node", "技术支持专家")
                            reasoning_text = reasoning_text.replace("TechAgent", "技术支持专家")

                            yield f"data: {ResponseFactory.build_text(f'调度分析：{reasoning_text}', ContentKind.THINKING, message_id).model_dump_json()}\n\n"

                        # 清空 buffer
                        supervisor_raw_output = ""

                    # 捕获整个主图执行完毕，提取包含完整流转的 messages
                    elif event_name == app.name:
                        output_data = event["data"].get("output")
                        if output_data and isinstance(output_data, dict) and "messages" in output_data:
                            final_state_messages = output_data["messages"]

            # 💾 记忆落库阶段
            if final_state_messages:
                session_service.save_history(
                    user_id=user_id,
                    session_id=session_id,
                    chat_history=final_state_messages
                )

            # 图执行完毕，发送结束信号
            finish_packet = ResponseFactory.build_finish(message_id)
            yield f"data: {finish_packet.model_dump_json()}\n\n"

        except asyncio.CancelledError:
            print(f"⚠️ 流传输中止 (Session: {session_id})")
            raise

        except Exception as e:
            error_packet = ResponseFactory.build_error(f"智能体执行异常: {str(e)}", message_id)
            yield f"data: {error_packet.model_dump_json()}\n\n"