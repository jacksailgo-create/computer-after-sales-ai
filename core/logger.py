import sys
import logging
from logging.handlers import TimedRotatingFileHandler

# 🌟 修复 1：引入我们的 OmegaConf 全局配置单例实例
from core.config import app_config
# 假设你有一个统一定义根目录的地方
from core.paths import PROJECT_ROOT

# ==========================================
# 1. 定义 ANSI 颜色转义码常量 (控制台专用)
# ==========================================
class LogColors:
    RESET = "\033[0m"
    GREY = "\033[38;20m"
    GREEN = "\033[32;20m"
    YELLOW = "\033[33;20m"
    RED = "\033[31;20m"
    BOLD_RED = "\033[31;1m"

# ==========================================
# 2. 自定义彩色 Formatter
# ==========================================
class ColoredFormatter(logging.Formatter):
    """动态根据日志级别给控制台输出上色"""
    def __init__(self, fmt, datefmt):
        super().__init__()
        self.fmt = fmt
        self.datefmt = datefmt
        self.FORMATS = {
            logging.DEBUG: LogColors.GREY + self.fmt + LogColors.RESET,
            logging.INFO: LogColors.GREEN + self.fmt + LogColors.RESET,
            logging.WARNING: LogColors.YELLOW + self.fmt + LogColors.RESET,
            logging.ERROR: LogColors.RED + self.fmt + LogColors.RESET,
            logging.CRITICAL: LogColors.BOLD_RED + self.fmt + LogColors.RESET
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.fmt)
        formatter = logging.Formatter(log_fmt, self.datefmt)
        return formatter.format(record)

# ==========================================
# 3. 核心初始化函数 (微服务专属工厂)
# ==========================================
def setup_logger(service_name: str) -> logging.Logger:
    """
    初始化企业级日志配置工厂
    :param service_name: 服务名，用于隔离日志文件 (例如 'customer_service')
    """
    # ------------------------------------------------
    # 1. 获取 OmegaConf 配置对象
    # ------------------------------------------------
    log_cfg = app_config.logging

    # ------------------------------------------------
    # 2. 准备服务专属目录 (按服务名隔离，拒绝文件踩踏)
    # ------------------------------------------------
    # 路径形如: /项目根目录/logs/customer_service/
    service_log_dir = PROJECT_ROOT / log_cfg.log_dir / service_name
    service_log_dir.mkdir(parents=True, exist_ok=True)

    debug_log_path = service_log_dir / "debug.log"
    info_log_path = service_log_dir / "info.log"
    error_log_path = service_log_dir / "error.log"

    # ------------------------------------------------
    # 3. 定义输出格式 (读取 YAML 配置)
    # ------------------------------------------------
    base_fmt = log_cfg.format
    date_fmt = "%Y-%m-%d %H:%M:%S"

    console_formatter = ColoredFormatter(fmt=base_fmt, datefmt=date_fmt)
    file_formatter = logging.Formatter(fmt=base_fmt, datefmt=date_fmt)

    # ------------------------------------------------
    # 4. 配置各类处理器 (Handlers)
    # ------------------------------------------------
    handlers = []

    # 4.1 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_cfg.console_level, logging.INFO))
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # 4.2 DEBUG 文件 (全量流水账，短期保留)
    debug_handler = TimedRotatingFileHandler(
        filename=debug_log_path, when="midnight", interval=1,
        backupCount=log_cfg.retention.debug_days, encoding="utf-8"
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(file_formatter)
    handlers.append(debug_handler)

    # 4.3 INFO 文件 (核心业务轨迹，中期保留)
    info_handler = TimedRotatingFileHandler(
        filename=info_log_path, when="midnight", interval=1,
        backupCount=log_cfg.retention.info_days, encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(file_formatter)
    handlers.append(info_handler)

    # 4.4 ERROR 文件 (纯净报错本，长期保留)
    error_handler = TimedRotatingFileHandler(
        filename=error_log_path, when="midnight", interval=1,
        backupCount=log_cfg.retention.error_days, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    handlers.append(error_handler)

    # ------------------------------------------------
    # 5. 挂载到根记录器 (Root Logger)
    # ------------------------------------------------
    # 🌟 修复 2：直接配置 Root Logger，让整个微服务生态（包括第三方库和你的所有模块）都吃这个配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 总阀门全开，具体拦截靠上面的各个 Handler

    # 清除可能存在的默认处理器，防止重复打印两次
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 将组装好的彩色控制台和三个日志文件处理器挂载上去
    for h in handlers:
        root_logger.addHandler(h)

    # ------------------------------------------------
    # 6. 一键屏蔽第三方吵闹库 (读取 YAML 列表)
    # ------------------------------------------------
    if hasattr(log_cfg, "mute_libraries"):
        for lib in log_cfg.mute_libraries:
            logging.getLogger(lib).setLevel(logging.WARNING)

    return root_logger