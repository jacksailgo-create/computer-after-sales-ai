import os
import logging
from omegaconf import OmegaConf, DictConfig
from core.paths import PROJECT_ROOT

# ==========================================
# 1. 独立的安全启动日志 (拒绝污染 Root Logger)
# ==========================================
# 专门为配置加载阶段创建一个不向上传播的 Logger
init_logger = logging.getLogger("config_loader")
init_logger.propagate = False
if not init_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[Config Loader] %(levelname)s - %(message)s"))
    init_logger.addHandler(handler)
    init_logger.setLevel(logging.INFO)

# ==========================================
# 2. 精准定位项目根目录
# ==========================================
# __file__ 是 core/config.py
# parent 是 core/
# parent.parent 是项目根目录
PROJECT_ROOT = PROJECT_ROOT


class GlobalConfigManager:
    """
    企业级多模块配置中心 (单例)。
    支持多目录自动扫描、环境变量覆盖、默认值兜底与运行时锁定。
    """
    _instance = None
    _config: DictConfig = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalConfigManager, cls).__new__(cls)
            cls._instance._load_all_configs()
        return cls._instance

    def _load_all_configs(self):
        # ------------------------------------------------
        # 1. 基础兜底配置 (Base Fallback)
        # 防止物理 YAML 文件丢失导致整个系统在启动时崩溃
        # ------------------------------------------------
        merged_config = OmegaConf.create({
            "logging": {"log_dir": "logs", "console_level": "INFO"},
            "llm": {"model": "gpt-3.5-turbo", "temperature": 0.1},
            "kb_service": {"base_url": "http://127.0.0.1:8001/api/v1/chat", "timeout": 15.0}
        })

        # ------------------------------------------------
        # 2. 动态扫描配置目录 (Dynamic Discovery)
        # ------------------------------------------------
        # 核心基建的配置目录肯定要扫
        target_conf_dirs = [PROJECT_ROOT / "core" / "conf"]

        # 自动遍历 services/ 目录下所有微服务的 conf 或 config 文件夹
        services_dir = PROJECT_ROOT / "services"
        if services_dir.exists():
            for service_path in services_dir.iterdir():
                if service_path.is_dir():
                    # 同时兼容命名为 conf 或 config 的文件夹
                    for folder_name in ("conf", "config"):
                        potential_dir = service_path / folder_name
                        if potential_dir.exists():
                            target_conf_dirs.append(potential_dir)

        # ------------------------------------------------
        # 3. 遍历加载并合并所有 YAML
        # ------------------------------------------------
        for conf_dir in target_conf_dirs:
            init_logger.info(f"🔍 扫描配置目录: {conf_dir.relative_to(PROJECT_ROOT)}")
            for ext in ("*.yaml", "*.yml"):
                for yaml_file in conf_dir.glob(ext):
                    try:
                        file_config = OmegaConf.load(yaml_file)
                        # 将当前文件的配置合并到总字典中 (相同 Key 会被覆盖)
                        merged_config = OmegaConf.merge(merged_config, file_config)
                        init_logger.info(f"  └── ✅ 加载成功: {yaml_file.name}")
                    except Exception as e:
                        init_logger.error(f"  └── ❌ 加载失败 {yaml_file.name}: {e}")

        # ------------------------------------------------
        # 4. 环境级配置覆盖 (Environment Override)
        # 例如通过 export APP_ENV=prod 加载 config-prod.yaml
        # ------------------------------------------------
        env = os.getenv("APP_ENV", "dev").lower()
        env_override_file = PROJECT_ROOT / f"config-{env}.yaml"

        if env_override_file.exists():
            try:
                env_config = OmegaConf.load(env_override_file)
                merged_config = OmegaConf.merge(merged_config, env_config)
                init_logger.info(f"🌍 应用环境级覆盖配置: {env_override_file.name}")
            except Exception as e:
                init_logger.error(f"❌ 环境配置加载失败 {env_override_file.name}: {e}")

        # ------------------------------------------------
        # 5. 锁定配置为只读 (Thread-safe Security)
        # ------------------------------------------------
        OmegaConf.set_readonly(merged_config, True)
        self._config = merged_config

    @property
    def settings(self) -> DictConfig:
        return self._config


# ==========================================
# 3. 暴露全局单例与通用常量
# ==========================================
# 外部统一使用 from core.config import app_config, PROJECT_ROOT
app_config = GlobalConfigManager().settings

__all__ = ["app_config", "PROJECT_ROOT"]