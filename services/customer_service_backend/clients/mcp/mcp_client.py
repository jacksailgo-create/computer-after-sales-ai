import os
import asyncio
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from openai import timeout, api_key

from core.config import app_config


async def load_mcp_search_tools():
    """负责实时咨询查询"""
    api_key = app_config.search_service.api_key
    if not api_key:
        raise ValueError("缺少 DASHSCOPE_API_KEY")

    client = MultiServerMCPClient({
        "bailian_web_search": {
            "transport": "sse",
            "url": app_config.search_service.base_url,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            },
        }
    })
    # 获取真正的工具列表 (比如里面包含一个名叫 'amap-maps' 的工具)
    tools = await client.get_tools()
    return tools

async def load_mcp_map_tools():
    """负责地图定位工作"""
    api_key = app_config.map_service.api_key
    if not api_key:
        raise ValueError("缺少 DASHSCOPE_API_KEY")
    client = MultiServerMCPClient({
        "baidu_map_mcp": {
            "transport": "sse",
            "url": app_config.map_service.base_url + api_key,
        }
    })
    tools = await client.get_tools()
    return tools