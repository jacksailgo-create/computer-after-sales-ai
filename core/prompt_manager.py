import os
import re
import logging
import threading
from pathlib import Path
from typing import Dict, List, Tuple

# 假设 PROJECT_ROOT 已经在 core.config 中定义
# 如果没有，请自行修改为你的实际路径
from core.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


class PromptManager:
    """
    🚀 终极版企业级多文件提示词加载器
    特性：智能分块解析(免反引号)、自动热更新、线程安全、LangChain 原生桥接。
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PromptManager, cls).__new__(cls)
                    cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        """初始化与目录嗅探"""
        self.prompts_dir = (PROJECT_ROOT / "services" / "customer_service_backend" / "prompts").resolve()
        logger.info(f"📁 [PromptManager] 绑定的提示词根目录: {self.prompts_dir}")

        self._prompts: Dict[str, Dict[str, dict]] = {}
        self._file_mtimes: Dict[str, float] = {}
        self._load_all_if_changed()

    def _load_all_if_changed(self):
        """扫描目录，安全地进行热更新"""
        if not self.prompts_dir.exists():
            logger.warning(f"❌ 提示词目录未找到，请检查此路径是否存在: {self.prompts_dir}")
            return

        changed = False
        for md_file in self.prompts_dir.glob("*.md"):
            try:
                current_mtime = os.path.getmtime(md_file)
                last_mtime = self._file_mtimes.get(md_file.name, 0.0)

                if current_mtime > last_mtime:
                    if last_mtime > 0:
                        logger.info(f"🔄 检测到 {md_file.name} 发生变更，正在安全热更新...")
                    else:
                        logger.info(f"📂 初次加载提示词文件: {md_file.name}")

                    self._parse_markdown_smart(md_file)
                    self._file_mtimes[md_file.name] = current_mtime
                    changed = True

            except Exception as e:
                logger.error(f"❌ 热更新 {md_file.name} 失败，错误: {e}")

        if changed:
            total_prompts = sum(len(group) for group in self._prompts.values())
            logger.info(f"✅ 提示词引擎就绪，共挂载 {total_prompts} 个 AI 角色。")

    def _parse_markdown_smart(self, file_path: Path):
        """
        🧠 智能 Markdown 解析器：
        只要遇到带有 '[标识符]' 的 '## ' 标题，下方的所有内容都是提示词，直到遇到下一个二级标题。
        完美支持如 "## 🎯 [tech_agent]角色定位" 这样的丰富写法。
        """
        content = file_path.read_text(encoding="utf-8")
        file_key = file_path.stem

        temp_namespace = {}
        current_key = None
        block_content = []

        def save_current_block():
            if current_key and block_content:
                # 1. 组合文本
                prompt_text = '\n'.join(block_content).strip()

                # 2. 兼容处理：如果用户还是习惯写 ```text，我们帮他脱掉外衣
                lines = prompt_text.split('\n')
                if lines and lines[0].strip().startswith('```'):
                    lines.pop(0)
                if lines and lines[-1].strip() == '```':
                    lines.pop(-1)
                prompt_text = '\n'.join(lines).strip()

                # 3. 变量自省：找出所有 {xxx} 的占位符
                required_vars = re.findall(r'(?<!\{)\{([a-zA-Z0-9_]+)\}(?!\})', prompt_text)

                temp_namespace[current_key] = {
                    "text": prompt_text,
                    "vars": list(set(required_vars))
                }

        for line in content.split('\n'):
            stripped_line = line.strip()

            # 匹配二级标题并提取 [] 中的标识符
            # 例如匹配: "## 🎯 [tech_agent]角色定位" -> 提取出 "tech_agent"
            if stripped_line.startswith('## ') and '[' in stripped_line and ']' in stripped_line:
                # 遇到新的标题前，先保存上一段收集的内容
                save_current_block()

                match = re.search(r'\[(.*?)\]', stripped_line)
                if match:
                    current_key = match.group(1).strip()
                    block_content = []
                else:
                    current_key = None
            elif current_key is not None:
                # 收集当前角色的提示词内容
                block_content.append(line)

        # 保存文件末尾的最后一个区块
        save_current_block()

        # 挂载到内存
        self._prompts[file_key] = temp_namespace

    # ==========================================
    # 核心 API 方法
    # ==========================================

    def get_prompt(self, file_name: str, role_key: str) -> str:
        with self._lock:
            self._load_all_if_changed()
        return self._get_role_data(file_name, role_key)["text"]

    def get_prompt_with_vars(self, file_name: str, role_key: str) -> Tuple[str, List[str]]:
        with self._lock:
            self._load_all_if_changed()
        role_data = self._get_role_data(file_name, role_key)
        return role_data["text"], role_data["vars"]

    def get_chat_template(self, file_name: str, role_key: str) -> "ChatPromptTemplate":
        """
        🏆 [LangChain 终极桥接]
        一键转换为包含系统设定和 {messages} 历史记录占位符的 ChatPromptTemplate。
        完美适配 LangGraph 的 State(messages) 机制。
        """
        from langchain_core.prompts import ChatPromptTemplate
        system_text = self.get_prompt(file_name, role_key)

        return ChatPromptTemplate.from_messages([
            ("system", system_text),
            ("placeholder", "{messages}")
        ])

    def _get_role_data(self, file_name: str, role_key: str) -> dict:
        """强化报错信息的内部寻址逻辑"""
        if file_name not in self._prompts:
            raise ValueError(f"\n❌ 找不到文件 '{file_name}.md'！\n已加载: {list(self._prompts.keys())}")

        file_namespace = self._prompts[file_name]
        if not file_namespace:
            raise ValueError(f"\n❌ '{file_name}.md' 里面没有任何提示词！请检查是否包含 '## [角色名]' 标题。")

        role_data = file_namespace.get(role_key)
        if not role_data:
            raise ValueError(
                f"\n❌ 未在 '{file_name}.md' 中找到 '[{role_key}]'！\n可用角色: {list(file_namespace.keys())}")

        return role_data


# 导出全局单例
prompt_manager = PromptManager()