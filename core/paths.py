from pathlib import Path


def get_project_root(marker_file: str = "pyproject.toml") -> Path:
    """
    向上寻找包含 marker_file 的目录，作为微服务的根目录。
    """
    # __file__ 是当前文件 (paths.py) 的绝对路径
    # resolve() 用来消除软链接等影响，获取真实路径
    current_dir = Path(__file__).resolve().parent

    # 逐级向上遍历 (包括当前目录)
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / marker_file).exists():
            return parent

    # 如果找到了操作系统的根目录还没找到，抛出明确异常
    raise FileNotFoundError(
        f"🚨 找不到项目根目录！请确保 '{marker_file}' 文件存在于 knowledge_platform_backend 目录下。"
    )


# 1. 初始化出全局的 PROJECT_ROOT
PROJECT_ROOT = get_project_root()

# 2. 你还可以顺便把常用的子目录也在这里定义好，全项目复用！
# 例如：定义好数据文件夹、日志文件夹、临时文件文件夹
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
PROMPTS_DIR = PROJECT_ROOT / "core" / "prompts"
SESSION_DIR = DATA_DIR / "sessions"

# 确保这些文件夹在运行时存在 (如果不存在自动创建)
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)