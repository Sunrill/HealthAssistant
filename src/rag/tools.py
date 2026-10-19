"""知识检索工具：把本地语料检索暴露给 Agent。"""
import json
from typing import Any, Dict, List

from hello_agents.tools import ToolParameter

from ..tools import BaseHealthTool
from .retriever import search


class KnowledgeSearchTool(BaseHealthTool):
    """本地健康科普语料检索。"""

    def __init__(self):
        super().__init__(
            name="knowledge_search",
            description="检索本地健康科普语料，用于回答“为什么”“什么原理”“该怎么做”这类解释性问题，"
                        "例如“为什么尿酸高要少喝啤酒”“脂肪肝多久复查一次”。"
                        "禁止用于查询个人数值或个人报告——那类问题请用 lab_analysis、health_metrics。"
        )

    def _execute(self, parameters: Dict[str, Any]) -> str:
        query = (parameters.get("query") or "").strip()
        if not query:
            return "请提供要检索的问题或关键词。"
        top_k = int(parameters.get("top_k", 3))
        hits = search(query, top_k=top_k)
        if not hits:
            return "本地语料中没有找到相关内容。不要据此推断，请建议用户咨询医生或查阅权威资料。"
        return json.dumps({
            "source": "本地健康科普语料（自建，非诊疗指南）",
            "results": hits,
        }, ensure_ascii=False)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="query", type="string", description="要检索的问题或关键词", required=True),
            ToolParameter(name="top_k", type="integer", description="返回条数，默认 3", required=False),
        ]
