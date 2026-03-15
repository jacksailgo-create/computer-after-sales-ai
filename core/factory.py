import os
import logging

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_openai import OpenAIEmbeddings
from core.config import app_config

logger = logging.getLogger(__name__)


class ModelFactory:
    """
    企业级通用模型工厂
    支持配置驱动的 LLM 和 Embedding 实例化，兼容所有 OpenAI 协议厂商
    """

    @staticmethod
    def _get_provider_credentials(provider_name: str):
        """内部工具：获取 Provider 的基础配置和 API Key"""
        provider_cfg = app_config.llm.providers.get(provider_name)
        if not provider_cfg:
            raise ValueError(f"❌ 配置文件中未定义 Provider: {provider_name}")

        # 优先级：环境变量 (如 SILICONFLOW_API_KEY) > YAML 中的 api_key
        env_key = f"{provider_name.upper()}_API_KEY"
        api_key = os.getenv(env_key) or provider_cfg.get("api_key")

        if not api_key:
            logger.warning(f"⚠️ 未找到 {provider_name} 的 API Key (环境变量 {env_key} 或 YAML)")

        return provider_cfg.base_url, api_key

    @classmethod
    def create_llm(cls, role_name: str) -> BaseChatModel:
        """
        根据路由名称创建 LLM (例如: 'supervisor', 'tech_agent')
        """
        route_cfg = app_config.llm.routing.get(role_name)
        if not route_cfg:
            raise ValueError(f"❌ 路由表节点缺失: llm.routing.{role_name}")

        base_url, api_key = cls._get_provider_credentials(route_cfg.provider)

        print(f"🚀 使用 LLM: {"openai" if route_cfg.provider == "siliconflow" or "qwen" else route_cfg.provider} - {route_cfg.model}")

        return init_chat_model(
            model_provider= "openai" if route_cfg.provider == "siliconflow" or "qwen" else route_cfg.provider,
            model=route_cfg.model,
            temperature=route_cfg.temperature,
            openai_api_base=base_url,
            openai_api_key=api_key,
            # 可根据需要增加 max_tokens 等通用参数
            timeout=app_config.llm.get("timeout", 60)
        )

    @classmethod
    def create_embeddings(cls) -> OpenAIEmbeddings:
        """
        根据路由表中的 embedding 节点创建向量模型
        """
        # 对应你 YAML 中的 llm.routing.embedding
        route_cfg = app_config.llm.routing.embedding
        if not route_cfg:
            raise ValueError("❌ 路由表节点缺失: llm.routing.embedding")

        base_url, api_key = cls._get_provider_credentials(route_cfg.provider)

        return OpenAIEmbeddings(
            model=route_cfg.model,
            openai_api_base=base_url,
            openai_api_key=api_key,
            # 针对 Embedding 的特殊配置，如维度等
            check_embedding_ctx_length=False
        )