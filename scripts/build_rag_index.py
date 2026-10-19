"""构建 RAG 索引。

用法：
    uv run python -m scripts.build_rag_index
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag.corpus import load_chunks  # noqa: E402
from src.rag.index import build_index, save_index  # noqa: E402


def main() -> int:
    chunks = load_chunks()
    if not chunks:
        print("语料为空，请检查 data/knowledge/corpus/ 下是否有 .md 文件")
        return 1

    index = build_index(chunks)
    path = save_index(index)

    per_doc = Counter(c.doc_id for c in chunks)
    print(f"语料文件: {len(per_doc)} 个")
    for doc_id, count in per_doc.items():
        print(f"  {doc_id}: {count} 块")
    print(f"切块总数: {index['n']}")
    print(f"词表大小: {len(index['df'])}")
    print(f"平均块长: {index['avgdl']:.1f} tokens")
    print(f"索引已写入: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
