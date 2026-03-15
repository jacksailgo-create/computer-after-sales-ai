import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import app_config
import core.logger
logger = logging.getLogger(__name__)

active_db_type = app_config.database.relational_db.active
db_config = app_config.database.relational_db[active_db_type]

SQLALCHEMY_DATABASE_URL = db_config.url
POOL_RECYCLE = db_config.get("pool_recycle", 3600)
POOL_PRE_PING = db_config.get("pool_pre_ping", True)
ECHO_SQL = db_config.get("echo_sql", False)

# ==========================================
# 【关键修复】：针对 SQLite 进行绝对路径转换和防崩溃兜底
# ==========================================
if active_db_type == "sqlite":
    # 提取 YAML 中的相对路径 (例如 data/kb_management.db)
    db_path_str = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")

    # 动态计算出项目的绝对根目录
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    absolute_db_path = PROJECT_ROOT / db_path_str

    # 【最重要的一步】：强制检查并创建 data 文件夹！
    absolute_db_path.parent.mkdir(parents=True, exist_ok=True)

    # 重新组装为绝对路径的 SQLite URL
    # (Unix/Mac系统下绝对路径自带/，拼接后变成 sqlite:////Users/... 4个斜杠是合法的绝对路径)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{absolute_db_path}"

logger.info(f"🗄️ 当前激活的关系型数据库引擎: [{active_db_type.upper()}]")
logger.info(f"🔗 数据库连接 URL: {SQLALCHEMY_DATABASE_URL}")

# SQLite 兼容性处理
connect_args = {"check_same_thread": False} if active_db_type == "sqlite" else {}

engine_kwargs = {
    "pool_pre_ping": POOL_PRE_PING,
    "pool_recycle": POOL_RECYCLE,
    "echo": ECHO_SQL,
    "connect_args": connect_args
}

if active_db_type == "mysql":
    engine_kwargs["pool_size"] = db_config.get("pool_size", 5)
    engine_kwargs["max_overflow"] = db_config.get("max_overflow", 10)

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类
Base = declarative_base()


# 依赖注入函数 (DI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常: {e}")
        db.rollback()
        raise
    finally:
        db.close()