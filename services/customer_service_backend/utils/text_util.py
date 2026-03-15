from typing import Dict

# --------------------------------------------------------------------------
# 语义化映射表：将后端的节点名/工具名映射为面向用户的友好词汇
# --------------------------------------------------------------------------
DISPLAY_NAME_MAPPING: Dict[str, str] = {
    # --- 外部 MCP 工具 ---
    "bailian_web_search": "联网搜索",
    "search_mcp": "联网搜索",
    "map_geocode": "地址解析",
    "map_ip_location": "IP定位",
    "map_search_places": "地点搜索",
    "map_uri": "生成导航链接",
    "baidu_map_mcp": "百度地图查询",

    # --- 本地自建工具 ---
    "search_knowledge_tool": "查询知识库",
    "get_user_coordinates": "位置解析",
    "find_nearest_stations": "查询附近服务站",
    "geocode_address": "地址转坐标",

    # --- 智能体节点 (Agents) ---
    "tech_agent_node": "技术支持专家",
    "service_agent_node": "售后服务专家",
    # 💡 补充 LangGraph 中常用的首字母大写节点名，防止映射遗漏
    "TechAgent": "技术支持专家",
    "ServiceAgent": "售后服务专家",
    "Supervisor": "主调度中心"
}


def get_display_name(raw_name: str) -> str:
    """
    获取友好的显示名称。如果字典中未定义，则优雅降级返回原名。
    """
    return DISPLAY_NAME_MAPPING.get(raw_name, raw_name)


def format_tool_call_html(tool_name: str) -> str:
    """
    生成工具调用的 UI 卡片
    """
    display_name = get_display_name(tool_name)

    # 使用 .strip() 剔除多余的换行符，保证输出纯净的 HTML 节点
    return f"""
<div class="tech-process-card tool-call">
    <div class="tech-process-header">
        <span class="tech-icon">🔄</span>
        <span class="tech-label">正在调用工具</span>
    </div>
    <div class="tech-process-flow">
        <span class="tech-node source">调度中心</span>
        <span class="tech-arrow">➔</span>
        <span class="tech-node target">{display_name}</span>
    </div>
</div>
""".strip()


def format_agent_update_html(agent_name: str) -> str:
    """
    生成智能体切换的 UI 卡片
    """
    # 🔧 修复：智能体的名字也必须经过映射，否则页面会暴漏底层节点英文名
    display_name = get_display_name(agent_name)

    return f"""
<div class="tech-process-card agent-update">
    <div class="tech-process-header">
        <span class="tech-icon">🤖</span>
        <span class="tech-label">智能体切换</span>
    </div>
    <div class="tech-process-body">
        <span class="tech-text">当前接管: <strong class="highlight">{display_name}</strong></span>
    </div>
</div>
""".strip()