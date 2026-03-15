import logging

from langchain.chat_models import init_chat_model
# 引入强大的 LangChain 核心组件
from langchain_core.prompts import ChatPromptTemplate

# 引入检索器
from knowledge_platform_backend.rag.hybrid_search import hybrid_retriever
from core.factory import ModelFactory

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    知识库核心业务逻辑服务层。
    负责：多路检索、上下文拼接、Prompt 构建、大模型推理。
    """

    async def generate_rag_response(self, query: str) -> dict:
        """
        根据用户提问生成 RAG 增强回答
        """
        # ==========================================
        # 1. 知识提取 (Retrieval)
        # ==========================================
        # 使用实例调用检索
        recalled_docs = hybrid_retriever.search(query)

        context_parts = []
        sources = set()

        for doc in recalled_docs:
            source_file = doc.metadata.get("source", "未知文件")
            main_title = doc.metadata.get("main_title", "未命名主题")
            sources.add(f"{source_file} ({main_title})")

            # 把每一段检索到的知识，原汁原味地拼起来
            context_parts.append(f"【来源文件: {source_file} | 对应主题: {main_title}】\n{doc.page_content}")

        context_text = "\n\n---\n\n".join(context_parts)
        if not context_text.strip():
            context_text = "当前知识库中未检索到任何相关内容。"

        # ==========================================
        # 2. 组装 Prompt
        # ==========================================
        prompt_template = """你是一个专业的企业级电脑售后技术专家。
请严格根据以下【参考知识】来回答用户的【提问】。

回答要求：
1. 态度专业、礼貌，步骤条理清晰（可使用 Markdown 列表）。
2. 只要【参考知识】里有提及解决方案，请详细给出排查步骤。
3. 如果【参考知识】中完全没有相关记录，请直接回答：“抱歉，当前的售后知识库中未找到关于该问题的记录。”，绝对不能编造（幻觉）。

【参考知识】：
{context}

【用户提问】：
{question}
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # ==========================================
        # 3. 核心交接：把数据正式交给大模型
        # ==========================================
        logger.info(f"🧠 检索完毕 (共 {len(recalled_docs)} 段上下文)，准备请求大模型...")

        llm = ModelFactory.create_llm("knowledge_rag")

        chain = prompt | llm

        # 触发大模型推理
        response = chain.invoke({
            "context": context_text,
            "question": query
        })

        logger.info("✅ 大模型回答生成完毕！")

        # 返回业务处理结果，不包含任何 HTTP 状态码
        return {
            "answer": response.content,
            "sources": list(sources),
            # "chunks": recalled_docs
        }


# 导出一个单例服务供路由层使用
knowledge_service = KnowledgeService()