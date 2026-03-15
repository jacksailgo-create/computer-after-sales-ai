import httpx
import logging
from typing import Tuple, List

from langchain_core.tools import tool

# 🌟 引入全局配置单例
from core.config import app_config

# 自动继承 main.py 挂载到根记录器的企业级日志配置
logger = logging.getLogger(__name__)

@tool(name_or_callable="search_knowledge")
async def search_knowledge_tool(query: str) -> Tuple[str, List[str]]:
    """
    关于技术方面的处理
    :return: (拼接好的上下文文本, 参考来源文档名列表)
    """
    base_url = app_config.kb_service.base_url
    timeout = app_config.kb_service.timeout
    url = f"{base_url}/completions"
    payload = {"query": query}

    try:
        logger.info(f"🔌 [RPC Call] 正在向知识中台发起检索, Query: '{query}'")

        # 使用 httpx 发起异步网络请求
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)

            # 检查 HTTP 层面的状态码 (如 404, 500 会直接抛出异常被 except 捕获)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 200:
                data = result.get("data", {})
                # 大模型总结后的数
                answer = data.get("answer", "")
                # 直接筛选出来的数据
                # chunks = data.get("raw_chunks", [])
                sources = data.get("sources", [])

                if not answer:
                    logger.info("📭 知识中台未检索到有效信息。")
                    return "", []

                # 将多个纯文本切片用分隔符拼接，方便喂给大模型
                # context_text = "\n\n---\n\n".join(chunks)
                logger.info(f"✅ [RPC Success] 成功拉取知识上下文。")
                return answer, sources

            else:
                # 捕获业务层面的异常 (code != 200)
                error_msg = result.get('message', '未知业务错误')
                logger.warning(f"⚠️ 知识库返回业务异常: {error_msg}")
                return "", []

    except httpx.TimeoutException:
        logger.error(f"❌ 访问知识中台超时 (已超过 {timeout}s)，请检查 8001 端口服务是否正常运行！")
        return "", []

    except httpx.RequestError as e:
        logger.error(f"❌ 访问知识中台网络拒绝连接: {e}")
        return "", []

    except Exception as e:
        logger.exception(f"❌ 跨微服务通信发生未知崩溃: {e}")
        return "", []