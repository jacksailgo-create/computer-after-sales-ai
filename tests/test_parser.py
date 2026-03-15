from data_pipeline.processing.html_parser import HtmlToMarkdownTool


def run_example():
    # 模拟爬虫抓取到的原始网页 HTML (包含各种噪音)
    raw_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>笔记本蓝屏 0x0000007B 怎么解决？- 电脑售后论坛</title>
        <style>.ad-banner { display: none; }</style>
        <script>console.log("tracker loaded");</script>
    </head>
    <body>
        <nav>
            <ul><li>首页</li><li>论坛</li><li>登录</li></ul>
        </nav>

        <aside>
            <p>这里是侧边栏广告：买新电脑选我们！</p>
            <img src="ad.jpg" alt="广告图">
        </aside>

        <main>
            <h1>笔记本蓝屏 0x0000007B 怎么解决？</h1>
            <div class="post-content">
                <p>各位大神，我的电脑重装系统后一开机就蓝屏，代码是 <strong>0x0000007B</strong>，求救！</p>
            </div>

            <div class="reply">
                <h2>最佳回复专家：Hardware Master</h2>
                <p>这个报错通常是硬盘模式（SATA Controller Mode）设置不对导致的。请按照以下步骤排查：</p>
                <ul>
                    <li>重启电脑，疯狂按 <code>F2</code> 或 <code>Del</code> 键进入 BIOS。</li>
                    <li>找到 <strong>Configuration</strong> 或 <strong>Advanced</strong> 菜单。</li>
                    <li>将 <strong>SATA Controller Mode</strong> 从 <em>AHCI</em> 改为 <em>IDE</em>，或者反过来试试。</li>
                    <li>按 <code>F10</code> 保存并退出。</li>
                </ul>
            </div>
        </main>

        <footer>
            <p>Copyright © 2026 电脑售后论坛. All rights reserved.</p>
        </footer>
    </body>
    </html>
    """

    # 1. 初始化工具
    # 重点：配置需要物理移除的噪音标签。对于论坛，aside 和 nav 是绝对不能进向量库的。
    parser = HtmlToMarkdownTool(
        strip_tags=['script', 'style', 'nav', 'footer', 'head', 'aside'],
        strip_images=True
    )

    # 2. 执行转换
    clean_markdown = parser.convert(raw_html)

    # 3. 打印结果对比
    print("====== 转换后的 Markdown 结果 ======\n")
    print(clean_markdown)


if __name__ == "__main__":
    run_example()