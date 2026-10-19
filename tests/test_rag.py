from src.rag.corpus import load_chunks
from src.rag.index import build_index, tokenize
from src.rag.retriever import search


def test_tokenize_mixes_zh_and_en():
    tokens = tokenize("尿酸480 μmol/L")
    assert "480" in tokens
    assert "尿酸" in tokens


def test_chunk_count():
    chunks = load_chunks()
    assert len(chunks) >= 15          # 5 篇 × 至少 3 节


def test_search_hits_uric_acid():
    index = build_index(load_chunks())
    hits = search("为什么尿酸高不能喝啤酒", index=index)
    assert hits, "应至少命中一条"
    assert "尿酸" in hits[0]["title"]


def test_search_hits_exercise():
    index = build_index(load_chunks())
    hits = search("超重的人适合做什么运动", index=index)
    assert hits
    assert any("运动" in h["title"] for h in hits[:2])


def test_search_rejects_unrelated():
    index = build_index(load_chunks())
    assert search("今天天气怎么样", index=index) == []


def test_empty_query():
    index = build_index(load_chunks())
    assert search("", index=index) == []
