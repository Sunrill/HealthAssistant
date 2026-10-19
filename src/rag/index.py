"""BM25 索引：构建、保存、加载。

中文用字符二元组切词，英文数字按单词切，不依赖分词库。
"""
import json
import os
import re
from collections import Counter

from .corpus import Chunk

INDEX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "knowledge", "rag_index.json",
)


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    zh = re.sub(r"[^\u4e00-\u9fa5]", "", text)
    tokens.extend(zh[i:i + 2] for i in range(len(zh) - 1))
    return tokens


def build_index(chunks: list[Chunk]) -> dict:
    docs: list[dict] = []
    df: Counter = Counter()

    for i, c in enumerate(chunks):
        tokens = tokenize(f"{c.title} {c.section} {c.text}")
        tf = Counter(tokens)
        docs.append({
            "id": i,
            "doc_id": c.doc_id,
            "title": c.title,
            "section": c.section,
            "text": c.text,
            "len": len(tokens),
            "tf": dict(tf),
        })
        for term in tf:
            df[term] += 1

    avgdl = sum(d["len"] for d in docs) / len(docs) if docs else 0
    return {"version": 1, "n": len(docs), "avgdl": avgdl, "df": dict(df), "docs": docs}


def save_index(index: dict, path: str | None = None) -> str:
    target = path or INDEX_PATH
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    return target


def load_index(path: str | None = None) -> dict | None:
    target = path or INDEX_PATH
    if not os.path.exists(target):
        return None
    with open(target, encoding="utf-8") as f:
        return json.load(f)
