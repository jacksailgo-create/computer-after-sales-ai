# crawlers/html_parser.py
import logging
import re
from typing import Dict, Any

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter
import core.logger
# 配置基础日志
logger = logging.getLogger(__name__)

class HtmlToMarkdownTool:
    """
    完整的 HTML 转 Markdown 工具类。
    集成了标签移除、特定 Class 清洗、恶意引流链接过滤以及 Markdown 格式化转换与碎片修复。
    """

    def __init__(
            self,
            strip_tags=None,
            strip_classes=None,
            strip_images=True,
            bad_link_patterns=None
    ):
        # 1. 定义需要物理移除的 HTML 标签（全局噪音标签）
        self.strip_tags = strip_tags or [
            'script', 'style', 'nav', 'footer', 'header',
            'iframe', 'noscript', 'aside', 'form', 'meta', 'link'
        ]

        # 2. 定义需要移除的特定 CSS 类的节点（针对大厂售后页面的定制化屏蔽）
        self.strip_classes = strip_classes or [
            'mceNonEditable', 'ad-banner', 'recommend-links', 'share-box'
        ]

        # 3. 定义需要彻底清除的垃圾链接特征（如联想的重装系统广告）
        self.bad_link_patterns = bad_link_patterns or [
            'item.lenovo.com.cn/product',
            'support.example.com/premium'  # 示例：其他需要屏蔽的付费服务链接
        ]

        # 4. 是否在最终的 Markdown 中剥离图片（纯文本 QA 通常不需要图片）
        self.strip_images = strip_images

    def _clean_html(self, html_content: str) -> str:
        """内部方法：在 HTML DOM 层面进行深度清洗（剪枝）"""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Step 1: 移除指定的噪音标签
        for tag in self.strip_tags:
            for element in soup.find_all(tag):
                element.decompose()  # 从 DOM 树中彻底物理销毁

        # Step 2: 根据特定的 Class 移除节点（直接端掉整个牛皮癣容器）
        for class_name in self.strip_classes:
            for element in soup.find_all(class_=class_name):
                element.decompose()

        # Step 3: 针对特定的引流链接进行精确打击
        for pattern in self.bad_link_patterns:
            for a_tag in soup.find_all('a', href=True):
                if pattern in a_tag['href']:
                    # 很多时候广告是一个 <li> 或 <p> 包裹着 <a>，尝试向上寻找父节点并一起连根拔起
                    parent = a_tag.parent
                    if parent and parent.name in ['li', 'p', 'div', 'span']:
                        parent.decompose()
                    else:
                        a_tag.decompose()

        return str(soup)

    def convert(self, html_content: str) -> str:
        """
        核心暴露方法：执行完整的 HTML 到 Markdown 转换流水线
        """
        if not html_content:
            return ""

        # 1. 净化 HTML DOM
        cleaned_html = self._clean_html(html_content)

        # 2. 配置 Markdown 转换器
        strip_list = ['img'] if self.strip_images else []

        converter = MarkdownConverter(
            heading_style="ATX",  # 使用标准的 # 表示标题
            bullets="-",  # 无序列表使用 -
            strip=strip_list,  # 剥离配置好的特定标签（如 img）
            escape_asterisks=False,  # 防止把正常文本里的星号转义
            escape_underscores=False
        )

        # 3. 执行初步转换
        md_text = converter.convert(cleaned_html)

        # 4. 后处理清洗：格式化与碎片修复
        # 将 3 个以上的连续换行压缩为 2 个换行（保留标准的 Markdown 段落间距）
        md_text = re.sub(r'\n{3,}', '\n\n', md_text)

        # 清除每一行末尾的冗余空格
        md_text = re.sub(r'[ \t]+$', '', md_text, flags=re.MULTILINE)

        # 【核心修复】：缝合碎片化的加粗标签，将 "**解决方案****：**" 变为 "**解决方案：**"
        # 匹配两个相连的加粗闭合与开启标签（中间允许有空格），将其直接剔除
        md_text = re.sub(r'\*\*\s*\*\*', '', md_text)

        return md_text.strip()

    def parser_html(self, knowledge_no: str, html_data: Dict[str, Any]) -> str:
        """
        解析 HTML 数据，返回 Markdown 格式
        包括标题等
        :param knowledge_no: 知识编号
        :param html_data: HTML 数据
        :return: Markdown 格式
        """

        # 1. 判断是否有内容
        if not html_data['content']:
            raise ValueError('HTML 数据为空')

        items = []
        # 2. 获取 HTML 内容
        # 2.1 提取知识库编号
        items.append(f'# 知识库 {knowledge_no}\n')
        # 2.2 提取标题
        title = html_data.get('title', '暂无标题')
        items.append(f'## {title.strip()}\n')
        # 2.3 提取摘要 digest
        digest = html_data.get('digest')
        if digest and digest.strip():
            items.append(f'## 问题描述\n{digest.strip()}\n')
        # 2.4 提取分类
        # a.firstTopicName(主分类) b.subTopicName（子分类） c.questionCategoryName（早起遗留的分类名，问题对应的分类）
        first_topic_name = html_data.get('firstTopicName', '')
        sub_topic_name = html_data.get('subTopicName', '')
        question_category_name = html_data.get('questionCategoryName', '')

        categories = []
        if first_topic_name and first_topic_name.strip():
            categories.append(f'主类别: {first_topic_name.strip()}')
        if sub_topic_name and sub_topic_name.strip():
            categories.append(f'子类别: {sub_topic_name.strip()}')
        if question_category_name and question_category_name.strip():
            categories.append(f'问题类别: {question_category_name.strip()}')
        if categories:
            items.append(f'## 分类\n{"\n".join(categories)}\n')

        # 2.5 提取关键字
        keywords = html_data.get('keywords')
        key_words_list = [keyword.strip() for keyword in keywords.split(',')] if keywords else []
        if key_words_list:
            items.append(f'## 关键字\n{"\n".join(key_words_list)}\n')
        # 2.6 构建元数据（时效性、版本）
        metadata = []
        create_time = html_data.get('createTime')
        version_no = html_data.get('versionNo')
        if create_time and create_time.strip():
            metadata.append(f'创建时间: {create_time.strip()}')
        if version_no and version_no.strip():
            metadata.append(f'版本: {version_no.strip()}')
        if metadata:
            items.append(f'## 元数据\n{"|".join(metadata)}\n')

        # 2.7 构建内容
        content = html_data.get('content')
        if content:
            clean_markdown = self.convert(content)
            items.append(f'## 解决方案\n{clean_markdown}\n')

        # # 2.8 构建标题 作为知识库的注释（防止切块后文档上下文丢失）
        # items.append(f'<!-- 文档主题: {title.strip()} （知识库编号: {knowledge_no}） -->')

        return '\n'.join(items)