这个目录是 **数据采集模块（Web Crawling Layer）**，专门负责从互联网抓取知识数据，为你的电脑售后知识库提供原始数据。每个文件职责应该明确，否则爬虫系统很容易混乱。

结构：

```text
crawlers/
│
├── forum_crawler.py
├── manual_crawler.py
├── faq_crawler.py
└── site_configs.yaml
```

下面逐个解释。

---

# 1 `forum_crawler.py`

**作用：爬取技术论坛数据**

技术论坛是电脑售后最有价值的数据来源，因为里面包含：

* 用户问题
* 技术人员回答
* 真实维修案例

典型数据格式：

```json
{
  "title": "Laptop screen black after update",
  "question": "My laptop screen is black after Windows update",
  "answers": [
    "Try booting in safe mode",
    "Update your graphics driver"
  ],
  "source": "forum"
}
```

保存位置通常是：

```
data/raw/forums/
```

常见可爬论坛（示例）：

* Stack Overflow
* Reddit 技术版块
* 厂商社区论坛

典型流程：

```
论坛列表页
   ↓
帖子URL
   ↓
帖子详情
   ↓
解析问题 + 回复
   ↓
存JSON
```

---

# 2 `manual_crawler.py`

**作用：爬取官方技术文档 / 产品手册**

这些数据通常来自厂商技术支持页面，例如：

* BIOS说明
* 维修手册
* 用户指南

典型数据：

```
BIOS update instructions
Hardware replacement guide
Troubleshooting manual
```

保存目录：

```
data/raw/manuals/
```

例如抓到的内容：

```
Dell XPS 13 Service Manual
Section: Removing the battery
Step 1: Remove the back cover
Step 2: Disconnect the battery cable
```

这类数据 **专业性最高**。

---

# 3 `faq_crawler.py`

**作用：抓取 FAQ 网站**

很多公司官方支持页面都有 FAQ，例如：

```
How to fix WiFi not working
How to reset BIOS
How to recover Windows
```

数据结构：

```json
{
  "question": "Why is my laptop overheating?",
  "answer": "Clean the cooling fan and check airflow"
}
```

保存位置：

```
data/raw/web_pages/
```

FAQ数据特点：

* 简洁
* 结构清晰
* 适合直接进入知识库

---

# 4 `site_configs.yaml`

**作用：配置爬虫网站**

把所有目标网站集中管理，而不是写死在代码里。

示例：

```yaml
forums:
  - name: stackoverflow
    base_url: https://stackoverflow.com/questions
    type: forum

  - name: reddit_techsupport
    base_url: https://www.reddit.com/r/techsupport
    type: forum

manuals:
  - name: dell_support
    base_url: https://www.dell.com/support

  - name: hp_support
    base_url: https://support.hp.com

faq_sites:
  - name: microsoft_support
    base_url: https://support.microsoft.com
```

爬虫程序读取这个配置：

```
site_configs.yaml
     ↓
读取网站列表
     ↓
选择对应crawler
     ↓
开始抓取
```

这样做的好处：

* 新增网站只需要改配置
* 不用改代码
* 管理方便

---

# 推荐再加两个文件（实际项目必备）

建议把 `crawlers/` 扩展成这样：

```text
crawlers/
│
├── base_crawler.py
├── forum_crawler.py
├── manual_crawler.py
├── faq_crawler.py
│
├── site_configs.yaml
│
├── parsers/
│   ├── forum_parser.py
│   ├── manual_parser.py
│   └── faq_parser.py
│
└── utils/
    ├── request_utils.py
    └── url_manager.py
```

原因：

爬虫通常需要：

* 请求管理
* HTML解析
* URL去重
* 重试机制

如果全部写在一个文件里，代码会很难维护。

---

# 完整数据流

你的项目数据流程应该是：

```
crawlers
   ↓
data/raw
   ↓
processing
   ↓
data/cleaned
   ↓
data/chunks
   ↓
vector database
   ↓
AI Agent
```

---

如果这个项目是 **电脑售后 AI 系统**，下一步其实有一个更重要的设计：

**爬虫应该按“电脑故障类型”采集数据，而不是按网站。**

例如：

```
boot_issue
wifi_issue
blue_screen
battery_issue
keyboard_issue
```

这样知识库质量会高很多。

如果你需要，我可以帮你设计 **一套完整的电脑维修知识爬虫体系（20+数据源 + 自动分类）**，这一步其实决定了整个 AI 系统的能力上限。
