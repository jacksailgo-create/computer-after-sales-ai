# test_kb_client.py
import sys
import os
import asyncio

# 1. 确保 Python 能找到我们的 core 和 services 包
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

# 2. 初始化我们炫酷的企业级彩色日志
from core.logger import setup_logger

setup_logger("test_client")

# 3. 引入写好的单例客户端
from clients.local.kb_client import kb_client
import logging

logger = logging.getLogger(__name__)


async def main():
    logger.info("🚀 开始单独测试 KnowledgeBaseClient...")

    # 模拟用户提问
    test_query = "联想 ThinkPad 连不上 WiFi 怎么排查？"

    logger.info(f"发送测试 Query: '{test_query}'")

    # 发起跨微服务请求
    context_text, sources = await kb_client.search_knowledge(test_query)

    logger.info("==========================================")
    logger.info("🎯 最终获取到的拼接上下文 (Context):")
    if context_text:
        print(f"\n{context_text}\n")
    else:
        print("\n[上下文为空]\n")

    logger.info("🏷️ 最终获取到的参考来源 (Sources):")
    print(f"\n{sources}\n")
    logger.info("==========================================")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())