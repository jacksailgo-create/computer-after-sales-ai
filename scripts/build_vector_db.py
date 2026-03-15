import sys
import time
from pathlib import Path
import logging

# 1. 将项目根目录加入 sys.path，确保在任何地方运行都不会报 ModuleNotFoundError
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 2. 引入全局基建
from core.logger import setup_global_logger
from core.config import AppConfig

# 3. 引入 RAG 核心组件
from services.knowledge_platform_backend.rag import MarkdownDirectoryLoader
from services.knowledge_platform_backend.rag import QADocumentSplitter
# 直接引入我们已经实例化好的向量数据库单例
from services.knowledge_platform_backend.rag import VectorStoreManager

logger = logging.getLogger(__name__)

"""
调用数据切分，并向量化，存入向量数据库
"""

def build_knowledge_base():
    logger.info("=" * 60)
    logger.info("🚀 启动向量知识库构建流水线 (Build Vector DB Pipeline)")
    logger.info("=" * 60)

    start_time = time.time()

    # ==========================================
    # 步骤 1：提取 (Extract) - 加载清洗好的 Markdown
    # ==========================================
    logger.info("\n▶️ [步骤 1/3] 加载本地 Markdown 语料...")
    # 默认读取 data/cleaned 下的所有子目录 (faq, manuals, troubleshooting 等)
    loader = MarkdownDirectoryLoader()
    raw_documents = loader.load()

    if not raw_documents:
        logger.error("❌ 严重错误：未找到任何有效文档，请检查 data/cleaned 目录或先运行爬虫！")
        return

    logger.info(f"✅ 成功提取 {len(raw_documents)} 篇原始长文档。")

    # ==========================================
    # 步骤 2：转换 (Transform) - 智能层级切分
    # ==========================================
    logger.info("\n▶️ [步骤 2/3] 执行智能文本切分 (Chunking)...")
    # 针对售后场景，1500字一个块，重叠 100字，能在保证上下文的同时不浪费 Token
    splitter = QADocumentSplitter(chunk_size=1500, chunk_overlap=100)
    chunks = splitter.split_documents(raw_documents)

    if not chunks:
        logger.error("❌ 严重错误：文档切分失败，未能生成任何文本块！")
        return

    logger.info(f"✅ 成功将 {len(raw_documents)} 篇长文档切分为 {len(chunks)} 个原子知识块。")

    # ==========================================
    # 步骤 3：加载 (Load) - 向量化并灌入 ChromaDB
    # ==========================================
    logger.info("\n▶️ [步骤 3/3] 正在调用 Embedding 模型写入向量数据库...")
    logger.info("⚠️ 注意：这一步会调用大模型 API 将文本转为向量，可能需要一些时间，请耐心等待。")

    # 获取我们的管理器实例 (单例模式)
    vector_manager = VectorStoreManager()

    # 调用我们之前写好的分批写入方法
    # batch_size=100 意味着每发 100 个文本块给 OpenAI/本地模型，就歇 0.5 秒防封
    # 这里平台限制50
    is_success = vector_manager.batch_add_documents(
        documents=chunks,
        batch_size=50,
        sleep_time=0.5
    )

    # ==========================================
    # 构建报告
    # ==========================================
    end_time = time.time()
    cost_time = round(end_time - start_time, 2)

    logger.info("\n" + "=" * 60)
    if is_success:
        logger.info(f"🎉 知识库构建圆满完成！(总耗时: {cost_time} 秒)")
        logger.info(f"💾 数据已安全持久化到: {AppConfig.database.vector_db.persist_directory}")
        logger.info(f"🎯 现在你的 Agent 已经拥有了 {len(chunks)} 条专业售后记忆！")
    else:
        logger.error("❌ 知识库构建过程中出现部分或全部失败，请检查上方日志报错！")
    logger.info("=" * 60)


if __name__ == "__main__":
    # 初始化日志
    setup_global_logger()
    # 运行构建脚本
    build_knowledge_base()