import re
import yaml
import logging
from pathlib import Path
from typing import List, Union

from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader

from core.config import app_config
from core.paths import PROJECT_ROOT

import core.logger
logger = logging.getLogger(__name__)


# ==========================================
# 1. 面向批量构建向量库的专用加载器 (Class)
# ==========================================
class MarkdownDirectoryLoader:
    """
    自定义 Markdown 目录加载器。
    专门用于读取带有 YAML Front Matter 的 Markdown 文件，
    将其解析为 LangChain 标准的 Document 对象（分离正文与元数据）。
    """

    def __init__(self, directory_path: str = None):
        """
        初始化加载器
        :param directory_path: 目标目录相对路径，如果不传则默认读取配置中的 cleaned_dir
        """
        self.target_dir_str = directory_path or app_config.storage.cleaned_dir
        self.project_root = PROJECT_ROOT
        self.base_path = self.project_root / self.target_dir_str

    def _parse_file(self, file_path: Path) -> Document:
        """内部方法：解析单个文件，分离 YAML 元数据和 Markdown 正文"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用正则匹配 YAML Front Matter
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, flags=re.DOTALL)

            metadata = {}
            if match:
                yaml_text = match.group(1)
                page_content = match.group(2).strip()
                try:
                    metadata = yaml.safe_load(yaml_text) or {}
                except yaml.YAMLError as e:
                    logger.warning(f"⚠️ 解析 YAML 元数据失败 [{file_path.name}]: {e}")
            else:
                page_content = content.strip()

            metadata['source_file'] = file_path.name
            metadata['file_path'] = str(file_path)

            return Document(page_content=page_content, metadata=metadata)

        except Exception as e:
            logger.error(f"❌ 读取文件异常 [{file_path}]: {e}")
            return None

    def load(self) -> List[Document]:
        """
        遍历目录，加载所有 Markdown 文件
        """
        if not self.base_path.exists():
            logger.error(f"🚨 目标目录不存在: {self.base_path}")
            return []

        logger.info(f"📂 正在扫描目录: {self.base_path}")
        documents = []
        md_files = list(self.base_path.rglob("*.md"))
        logger.info(f"🔎 共找到 {len(md_files)} 个 Markdown 文件，开始解析...")

        for file_path in md_files:
            doc = self._parse_file(file_path)
            if doc and doc.page_content:
                documents.append(doc)

        logger.info(f"✅ 成功加载 {len(documents)} 个有效文档。")
        return documents


# ==========================================
# 2. 面向 Web 端人工清洗的独立解析函数 (Function)
# ==========================================
def parse_single_file(file_path: Union[str, Path]) -> str:
    """
    智能文件解析器：根据文件后缀名选择合适的 LangChain Loader，
    将文件内容提取为纯文本字符串，供前端管理员预览和清洗。

    :param file_path: 文件的绝对或相对路径
    :return: 提取出的纯文本内容
    """
    # 统一使用 pathlib 进行路径操作
    target_path = Path(file_path)

    if not target_path.exists():
        logger.error(f"❌ 文件不存在: {target_path}")
        raise FileNotFoundError(f"找不到要解析的文件: {target_path}")

    # 获取文件后缀名并统一转为小写 (例如 '.pdf')
    ext = target_path.suffix.lower()

    try:
        if ext in ['.txt', '.md']:
            logger.info(f"📄 正在使用 TextLoader 解析: {target_path}")
            loader = TextLoader(str(target_path), encoding='utf-8')
            docs = loader.load()

        elif ext == '.pdf':
            logger.info(f"📑 正在使用 PyPDFLoader 解析: {target_path}")
            loader = PyPDFLoader(str(target_path))
            docs = loader.load()

        else:
            raise ValueError(f"系统暂不支持解析该格式的文件: {ext}")

        # 将多页文档的 page_content 抽取并拼接
        full_text = "\n\n".join([doc.page_content for doc in docs])

        return full_text.strip()

    except Exception as e:
        logger.exception(f"❌ 解析文件 {target_path} 时发生严重错误: {e}")
        raise RuntimeError(f"文件解析失败: {str(e)}")