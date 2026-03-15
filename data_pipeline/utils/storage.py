import re
import hashlib
import logging
from pathlib import Path
from typing import Optional

from core.config import AppConfig
import core.logger
# 配置基础日志
logger = logging.getLogger(__name__)


class LocalStorageHandler:
    """
    本地文件存储处理器。
    负责统一管理抓取数据的落盘、目录自动创建、文件名安全校验及防冲突。
    """

    def __init__(self, base_output_dir: str = "data/cleaned"):
        """
        初始化存储处理器。

        :param base_output_dir: 相对于项目根目录的基础输出路径，默认为 data/cleaned
        """

        # 核心改动：优先使用传入的路径，否则从 AppConfig 读取
        self.output_dir = base_output_dir or AppConfig.storage.cleaned_dir

        # 动态计算项目根目录
        # 当前文件层级: data_pipeline/utils/storage.py
        # parent.parent.parent 即为 computer-after-sales-ai 根目录
        self.project_root = Path(__file__).resolve().parent.parent.parent

        # 拼接绝对路径
        self.base_path = self.project_root / base_output_dir

    def _sanitize_filename(self, name: str, max_length: int = 50) -> str:
        """
        内部方法：清理文件名中不能包含的特殊字符，防止 Windows/Linux 报错
        并限制长度
        """
        # 替换掉所有 Windows/Linux 文件系统不支持的字符
        clean_name = re.sub(r'[\\/*?:"<>|\n\r\t]', "_", name)
        # 把多个连续的下划线或空格替换为单个下划线，让名字更紧凑
        clean_name = re.sub(r'[\s_]+', '_', clean_name)
        # 去除首尾空格，并限制最大长度，防止 FileSystemException
        return clean_name.strip('_')[:max_length]

    def _extract_title(self, content: str) -> str:
        """
        从 Markdown 内容中分别提取第一个一级标题(H1)和第一个二级标题(H2)。
        组合成 "一级标题_二级标题" 的格式返回。
        """
        # 1. 提取第一个一级标题 (# 标题)
        h1_match = re.search(r'^#\s+(.+)$', content, flags=re.MULTILINE)
        h1_text = h1_match.group(1).strip() if h1_match else ""

        # 2. 提取第一个二级标题 (## 标题)
        h2_match = re.search(r'^##\s+(.+)$', content, flags=re.MULTILINE)
        h2_text = h2_match.group(1).strip() if h2_match else ""

        # 3. 组合标题
        title_parts = []
        if h1_text:
            title_parts.append(h1_text)
        if h2_text:
            title_parts.append(h2_text)

        if title_parts:
            # 用下划线连接 H1 和 H2
            return "_".join(title_parts)

        # 4. 降级方案：如果既没有 H1 也没有 H2，提取正文前 20 个字
        text_only = re.sub(r'<[^>]+>|#|\*|-', '', content).strip()
        return text_only[:20] if text_only else "untitled"

    def save_markdown(
            self,
            content: str,
            source_name: str,
            url: str,
            category: str = "troubleshooting"
    ) -> Optional[Path]:
        """
        将纯净的 Markdown 内容安全地保存到本地。

        :param content: 准备落盘的 Markdown 文本
        :param source_name: 来源名称（如 lenovo_kb、reddit_techsupport）
        :param url: 原始 URL（用于生成哈希防重名，并在文件头备注溯源）
        :param category: 数据分类子目录（如 faq, troubleshooting, repair_cases）
        :return: 成功保存的文件路径，如果内容为空则返回 None
        """
        if not content or not content.strip():
            logger.warning(f"⚠️ 内容为空，跳过保存: {url}")
            return None

        # 1. 组装目标子目录
        target_dir = self.base_path / category / self._sanitize_filename(source_name)
        target_dir.mkdir(parents=True, exist_ok=True)

        # 2. 提取并清理标题
        raw_title = self._extract_title(content)
        safe_title = self._sanitize_filename(raw_title, max_length=40)

        # 3. 生成最终文件名：来源_标题_哈希.md
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:6]
        safe_source = self._sanitize_filename(source_name, max_length=20)

        file_name = f"{safe_source}_{safe_title}_{url_hash}.md"
        file_path = target_dir / file_name

        # 3. 写入文件(带 YAML Front Matter)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # 在文件头部注入溯源元数据（Metadata），这对后续 RAG 溯源非常有帮助
                f.write("---\n")
                f.write(f"source: {source_name}\n")
                f.write(f"url: {url}\n")
                f.write(f"category: {category}\n")
                f.write("---\n\n")

                # 写入正文
                f.write(content)

            logger.info(f"✅ 成功落盘: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"❌ 写入文件失败 {file_path}: {e}")
            return None