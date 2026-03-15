import sqlite3
import queue
import logging
from contextlib import contextmanager
from typing import Generator

from customer_service_backend.utils.geo_utils import calculate_distance

logger = logging.getLogger(__name__)


class SQLiteConnectionPool:
    """
    轻量级 SQLite 线程安全连接池
    专为 LangGraph/FastAPI 等高并发异步场景设计
    """

    def __init__(self, db_path: str, max_connections: int = 5, timeout: float = 10.0):
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool: queue.Queue = queue.Queue(maxsize=max_connections)
        self._init_pool()

    def _init_pool(self):
        """初始化时建立指定数量的连接，填满队列"""
        for _ in range(self.max_connections):
            conn = self._create_connection()
            self._pool.put(conn)
        logger.info(f"✅ SQLite 连接池初始化完成，最大连接数: {self.max_connections}")

    def _create_connection(self) -> sqlite3.Connection:
        """创建一个底层的 SQLite 连接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=self.timeout
        )
        conn.row_factory = sqlite3.Row

        # 🌟 唯一的新增点：在这个底层连接创建时，注入自定义的测距函数
        # 这样池子里的每一个连接都能听懂 SQL 里的 haversine_dist 指令了！
        conn.create_function("haversine_dist", 4, calculate_distance)

        return conn

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """以获取/释放的上下文管理器模式暴露连接"""
        conn = self._pool.get()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ 数据库操作异常，已回滚: {e}")
            raise
        finally:
            self._pool.put(conn)

    def close_all(self):
        """优雅关闭所有连接"""
        while not self._pool.empty():
            conn = self._pool.get()
            conn.close()
        logger.info("🛑 SQLite 连接池已全部关闭")