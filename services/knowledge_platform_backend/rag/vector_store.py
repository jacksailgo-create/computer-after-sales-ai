import logging
import time
from pathlib import Path
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from tqdm import tqdm
from core.paths import PROJECT_ROOT
# 引入我们的全局配置
from core.config import app_config
from core.factory import ModelFactory
import core.logger
logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    向量数据库管理器 (单例模式/工厂模式)
    负责初始化 Embedding 模型并连接本地 ChromaDB。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreManager, cls).__new__(cls)
            cls._instance._init_store()
        return cls._instance

    def _init_store(self):
        """内部初始化方法"""
        db_config = app_config.database.vector_db
        logger.info(f"正在初始化向量数据库，Provider: {db_config.provider}")

        # 1. 动态获取持久化目录绝对路径
        project_root = PROJECT_ROOT
        persist_dir = str(project_root / db_config.persist_directory)

        # 3. 初始化并连接 Chroma 数据库
        if db_config.provider == "chroma":
            self.vector_store = Chroma(
                collection_name=db_config.collection_name,
                embedding_function=ModelFactory.create_embeddings(),
                persist_directory=persist_dir
            )
            logger.info(f"✅ ChromaDB 连接成功！当前集合包含文档数: {self.vector_store._collection.count()}")
        else:
            raise ValueError(f"暂不支持的 Vector DB Provider: {db_config.provider}")

    def get_store(self) -> Chroma:
        """对外暴露底层的 VectorStore 对象，供检索和写入使用"""
        return self.vector_store

    def batch_add_documents(
            self,
            documents: List[Document],
            batch_size: int = 100,
            sleep_time: float = 0.5
    ) -> bool:
        """
        分批将文档切块（Chunks）写入 ChromaDB。

        :param documents: 切分好的 LangChain Document 对象列表
        :param batch_size: 每批提交的数量 (建议 100-500，取决于 Embedding API 的限制)
        :param sleep_time: 每批写入后的暂停时间(秒)，防止触发大模型 API 的并发限流
        :return: 全部成功返回 True，否则返回 False
        """
        total_docs = len(documents)
        if total_docs == 0:
            logger.warning("没有需要写入的文档！")
            return False

        total_batches = (total_docs + batch_size - 1) // batch_size
        logger.info(f"📦 准备将 {total_docs} 个文本块分 {total_batches} 批写入向量库...")

        success_count = 0

        # 使用 tqdm 包装循环，设置总数和前缀描述
        with tqdm(total=total_batches, desc="向量化入库", unit="批") as pbar:
            for i in range(0, total_docs, batch_size):
                batch_docs = documents[i: i + batch_size]
                current_batch_num = (i // batch_size) + 1

                try:
                    # 动态更新进度条右侧的提示信息，替代原先的 logger.info
                    pbar.set_postfix({"当前处理": f"{len(batch_docs)}个块"})

                    # 核心写入操作
                    self.vector_store.add_documents(batch_docs)
                    success_count += len(batch_docs)

                    if current_batch_num < total_batches:
                        time.sleep(sleep_time)

                except Exception as e:
                    # 关键点：在 tqdm 运行期间如果要打印报错日志，必须用 tqdm.write！
                    # 这样错误信息会平滑地打印在进度条上方，不会把进度条冲断
                    tqdm.write(f"❌ 第 {current_batch_num} 批写入失败: {e}")
                    # 后台依然用 logger 记录完整的异常堆栈到文件里
                    logger.exception(f"第 {current_batch_num} 批写入异常")
                    continue

                # 每跑完一个批次，推动进度条前进 1 格
                pbar.update(1)

        logger.info("=" * 40)
        logger.info(f"🎉 向量化写入任务结束！预期写入: {total_docs} 个块，实际成功: {success_count} 个块。")
        logger.info("=" * 40)

        return success_count == total_docs

# 实例化导出，其他模块直接 from backend.rag.vector_store import vector_db 即可使用
vector_db = VectorStoreManager().get_store()