"""语料加载与切块：每个 Markdown 文件按二级标题切块。"""
import os
from dataclasses import dataclass, field

CORPUS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "knowledge", "corpus",
)


@dataclass
class Chunk:
    doc_id: str          # 文件名（不含扩展名）
    title: str           # front-matter 的 title
    section: str         # 二级标题
    text: str
    tags: list[str] = field(default_factory=list)


def _parse_front_matter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, parts[2].lstrip("\n")


def load_chunks(corpus_dir: str | None = None) -> list[Chunk]:
    root = corpus_dir or CORPUS_DIR
    chunks: list[Chunk] = []
    if not os.path.isdir(root):
        return chunks

    for name in sorted(os.listdir(root)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(root, name), encoding="utf-8") as f:
            meta, body = _parse_front_matter(f.read())

        title = meta.get("title", name[:-3])
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]

        section, buf = None, []
        for line in body.splitlines():
            if line.startswith("## "):
                if section and buf:
                    chunks.append(Chunk(name[:-3], title, section, "\n".join(buf).strip(), tags))
                section, buf = line[3:].strip(), []
            elif section is not None:
                buf.append(line)
        if section and buf:
            chunks.append(Chunk(name[:-3], title, section, "\n".join(buf).strip(), tags))

    return chunks
