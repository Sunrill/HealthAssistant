"""BM25 检索。"""
import math

from .index import load_index, tokenize

K1 = 1.5
B = 0.75
MIN_SCORE = 2.0


def search(query: str, top_k: int = 3, index: dict | None = None,
           min_score: float = MIN_SCORE) -> list[dict]:
    """返回按相关度排序的片段；低于阈值的一律丢弃，避免硬凑答案。"""
    idx = index or load_index()
    if not idx or not idx.get("docs"):
        return []

    q_terms = set(tokenize(query))
    n, avgdl, df = idx["n"], idx["avgdl"], idx["df"]

    scored: list[tuple[float, dict]] = []
    for doc in idx["docs"]:
        score = 0.0
        for term in q_terms:
            f = doc["tf"].get(term, 0)
            if not f:
                continue
            d = df.get(term, 0)
            idf = math.log(1 + (n - d + 0.5) / (d + 0.5))
            score += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * doc["len"] / avgdl))
        if score >= min_score:
            scored.append((score, doc))

    scored.sort(key=lambda item: -item[0])
    return [{
        "score": round(score, 2),
        "title": doc["title"],
        "section": doc["section"],
        "text": doc["text"],
    } for score, doc in scored[:top_k]]
