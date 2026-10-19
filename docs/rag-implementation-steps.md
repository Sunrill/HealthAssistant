# 为智能健康助手接入 RAG：分步实施指南

> 环境：WSL2 Ubuntu 24.04，项目 `~/projects/shoxar-HealthAssistant`
> 前置：已完成多成员改造，6 个工具正常运行，18 条测试通过

---

## 0. 先明确设计边界

接入 RAG 之前必须先回答一个问题：**检索用来解决什么？**

这个项目的数据分两类，处理方式必须不同：

| 数据类型 | 例子 | 处理方式 | 能否用 RAG |
|---|---|---|---|
| 个人结构化数据 | 我的尿酸 480、昨天睡了 6.5 小时 | 工具精确查询（`lab_report`、`health_metrics`） | **不能**。向量检索是近似匹配，可能召回别人的数据或参考区间说明 |
| 通用知识 | 为什么尿酸高要少喝啤酒、脂肪肝多久复查 | 语料检索（`knowledge_search`） | **能**，这正是 RAG 的用武之地 |

所以本方案只做一个**解释性知识检索**：用户问"为什么/原理/该怎么做"时才触发，数值查询永远走原有工具。

### 为什么用 BM25 而不是向量检索

| 方案 | 依赖 | 中文效果 | 适合场景 |
|---|---|---|---|
| BM25 + 字符二元组 | 零依赖 | 语料小时足够 | 几十到几百个片段 |
| 向量检索（bge/text-embedding） | 需 embedding 模型或 API | 语义泛化更好 | 上千片段、口语化提问 |

本项目语料目前 5 篇 19 个片段，BM25 的检索准确率已经够用（实测 5 类问题全部命中正确章节），且不引入 800 MB 的 torch。第 8 步给出向量检索的升级路径，接口保持一致。

---

## 步骤 1：准备语料

**目标**：建立可检索的本地知识库，覆盖用户最常追问的几类问题。

**输入**：健康科普知识（自撰或摘编），5 个主题各一篇。

**输出**：`data/knowledge/corpus/*.md`，每篇带 front-matter。

**文件格式**：

```markdown
---
title: 尿酸与高嘌呤饮食
tags: 尿酸, 嘌呤, 饮食
source: 公开科普摘编，非诊疗指南
---

## 尿酸是什么，为什么会升高
正文……

## 哪些食物嘌呤高
正文……
```

**约定**：一个 `##` 二级标题切一个片段（chunk）。片段是检索的最小单位，太长会稀释相关度，太短会丢上下文。经验值是每段 100–200 字。

**验证**：

```bash
ls data/knowledge/corpus/
```

预期看到 5 个文件：`uric-acid.md`、`fatty-liver.md`、`blood-pressure.md`、`aerobic-exercise.md`、`sleep.md`。

**注意**：语料是自建科普摘编，**不是临床指南**。上线前应有医学背景的人审一遍；文档里必须标注来源性质，否则模型会把它当成权威结论引用。

---

## 步骤 2：切块

**目标**：把 Markdown 解析成结构化的片段列表。

**输入**：语料目录下的 `.md` 文件。

**输出**：`list[Chunk]`，每个 Chunk 含 `doc_id / title / section / text / tags`。

**实现**：`src/rag/corpus.py`

```python
@dataclass
class Chunk:
    doc_id: str      # 文件名，如 uric-acid
    title: str       # front-matter 的 title
    section: str     # 二级标题，如 "哪些食物嘌呤高"
    text: str
    tags: list[str] = field(default_factory=list)
```

解析逻辑两段：先按 `---` 切出 front-matter（title、tags），再按行扫描，遇到 `## ` 就收束上一块、开启新块。

**验证**：

```bash
uv run python -c "
from src.rag.corpus import load_chunks
cs = load_chunks()
print('片段数:', len(cs))
for c in cs[:3]:
    print(' -', c.doc_id, '|', c.section, '|', len(c.text), '字')
"
```

预期：`片段数: 19`，前三条分别属于 `uric-acid`，每块 100–300 字。

**若不符**：片段数明显偏少，通常是二级标题用了 `###` 或没有空行分隔；片段数偏多，可能是正文里出现了 `## ` 开头的行。

---

## 步骤 3：构建索引

**目标**：把片段转成可快速打分的倒排统计（词频、文档频、平均长度）。

**输入**：`list[Chunk]`。

**输出**：`data/knowledge/rag_index.json`。

**实现**：`src/rag/index.py`

两个关键点：

**① 中文分词**——不引入 jieba，用字符二元组：

```python
def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())      # 英文/数字整词
    zh = re.sub(r"[^\u4e00-\u9fa5]", "", text)
    tokens.extend(zh[i:i + 2] for i in range(len(zh) - 1))  # 中文相邻两字
    return tokens
```

"尿酸" → `['尿酸']`，"高尿酸血症" → `['高尿','尿酸','酸血','血症']`。不依赖词典，缺点是词表偏大（19 个片段产生 1632 个词），但对小语料完全可接受。

**② 索引结构**——每块存 `tf`（词频字典）与 `len`，全局存 `df`（文档频）与 `avgdl`（平均块长）。查询时现算 IDF。

**操作**：

```bash
uv run python -m scripts.build_rag_index
```

**验证**：

```bash
cat data/knowledge/rag_index.json | head -c 200
```

预期输出：

```
语料文件: 5 个
  uric-acid: 4 块
  ...
切块总数: 19
词表大小: 1632
平均块长: 118.4 tokens
索引已写入: .../data/knowledge/rag_index.json
```

**注意**：`rag_index.json` 是派生文件，已加入 `.gitignore`。别人克隆仓库后需要先跑一次构建命令，README 里要写清楚。

---

## 步骤 4：实现检索

**目标**：给定查询，返回相关度最高的若干片段；不相关时返回空，而不是硬凑。

**输入**：查询字符串、`top_k`、阈值 `min_score`。

**输出**：`list[dict]`，每项含 `score / title / section / text`。

**实现**：`src/rag/retriever.py`，标准 BM25：

```
score = Σ idf(t) × (tf × (k1+1)) / (tf + k1 × (1 - b + b × dl/avgdl))
idf(t) = ln(1 + (N - df + 0.5) / (df + 0.5))
```

参数 `k1=1.5`、`b=0.75` 是通用默认值，语料小于千级时不需要调。

**阈值是这一步的关键**。BM25 永远会给出一个分数，哪怕完全不相关——"今天天气怎么样"也能得 1.73 分。如果不设阈值，无关问题会检索到一条"看起来相关"的健康知识，模型就会拿它硬答。设 `min_score=2.0` 后，实测分隔很清楚：

| 查询 | 最高分 | 判定 |
|---|---|---|
| 为什么尿酸高不能喝啤酒 | 6.32 | 命中《尿酸与高嘌呤饮食》 |
| 超重的人适合做什么运动 | 4.26 | 命中《有氧运动》"超重人群的注意事项" |
| 脂肪肝多久复查一次 | 7.51 | 命中《脂肪肝》"复查节奏" |
| 晚上睡不着怎么办 | 4.33 | 命中《睡眠》"改善睡眠的行为" |
| 今天天气怎么样 | 1.73 | **被阈值过滤，返回空** |

**验证**：

```bash
uv run python -c "
from src.rag.corpus import load_chunks
from src.rag.index import build_index
from src.rag.retriever import search
idx = build_index(load_chunks())
for q in ['为什么尿酸高不能喝啤酒', '今天天气怎么样']:
    hits = search(q, index=idx)
    print(q, '->', len(hits), hits[0]['section'] if hits else '（无命中）')
"
```

预期：第一条返回 3 条且首条是"尿酸是什么，为什么会升高"；第二条返回 0 条。

---

## 步骤 5：封装为工具

**目标**：让模型能主动调用检索，同时明确禁止用它查数值。

**输入**：`query`（必填）、`top_k`（默认 3）。

**输出**：JSON 字符串，含 `source` 与 `results`。

**实现**：`src/rag/tools.py`，继承项目已有的 `BaseHealthTool`（只写 `_execute` 返回字符串）。

工具描述是这个文件里最重要的部分——它决定了模型会不会调、什么时候调：

```
检索本地健康科普语料，用于回答"为什么""什么原理""该怎么做"这类解释性问题，
例如"为什么尿酸高要少喝啤酒""脂肪肝多久复查一次"。
禁止用于查询个人数值或个人报告——那类问题请用 lab_analysis、health_metrics。
```

**设计要点**：检索为空时，工具返回的是"没有找到相关内容，不要据此推断"，而不是空字符串。空字符串会让模型以为工具坏了；明确说"没有"能引导它老实承认不知道。

**验证**：

```bash
uv run python -c "
from src.rag.tools import KnowledgeSearchTool
t = KnowledgeSearchTool()
print(t.run({'query': '为什么尿酸要高'}).text[:300])
"
```

预期：返回含 `"source": "本地健康科普语料"` 的 JSON，`results` 里有标题与正文片段。

---

## 步骤 6：接入 Agent

**目标**：注册第 7 个工具，并在提示词里规定触发条件与禁止条件。

**输入**：`src/agent.py`。

**输出**：工具列表变为 7 个，提示词新增两条规则。

**操作**：

```bash
cd ~/projects/shoxar-HealthAssistant
bash apply_rag_patch.sh
```

脚本做四件事：备份原 `agent.py` 到 `.backup/`、替换为新版本、把 `rag_index.json` 加入 `.gitignore`、构建索引并跑全部测试。

**提示词新增的两条规则**：

```
8. 用户问"为什么""什么原理""该怎么做"这类解释性问题时，先调用 knowledge_search
   检索本地科普语料；检索不到就直说"本地资料没有覆盖"，不要凭常识补写。
   该类工具只用于解释原理，禁止用它查询任何个人数值或个人报告。
9. 引用语料内容时，注明来自哪一节（如"据本地资料《尿酸与高嘌呤饮食》"）。
```

第 9 条是**可追溯性要求**：让用户知道这段话来自语料而不是模型编的。

**验证**：

```bash
uv run python -c "
from src.agent import build_agent
a = build_agent()
print('工具数:', len(a.tool_registry.list_tools()))
print(a.tool_registry.list_tools())
"
```

预期：7 个工具，含 `knowledge_search`。

---

## 步骤 7：端到端验证

**目标**：确认三个方向都对——该检索时检索、不该检索时不检索、检索不到时不编造。

**操作**：

```bash
uv run python main.py
```

按下表逐条提问，观察行为：

| # | 输入 | 预期行为 | 判定依据 |
|---|---|---|---|
| 1 | 为什么尿酸高要少喝啤酒 | 调 `knowledge_search`，引用《尿酸与高嘌呤饮食》"哪些食物嘌呤高" | 回答中出现"啤酒既含嘌呤又促进尿酸生成"这类语料原文 |
| 2 | 脂肪肝要多久复查 | 调 `knowledge_search`，引用"复查节奏" | 回答提到 3–6 个月 |
| 3 | 我的尿酸是多少 | **不调** `knowledge_search`，调 `lab_report` | 数值来自报告，与语料无关 |
| 4 | 我该吃什么药降尿酸 | 不调检索，也不给药物建议 | 明确拒绝并建议就诊 |
| 5 | 跑步机坡度多少合适 | 调检索但**返回空** | 明确说"本地资料没有覆盖"，不编造 |

第 3 条和第 5 条最能说明接入是否成功：一条验证"不该用检索时没用"，一条验证"检索为空时不硬答"。

**如果第 3 条调用了 knowledge_search**：说明工具描述里的禁止条款不够强，或者提示词第 8 条被忽略。把工具描述中"禁止用于查询个人数值"提到第一句，效果会明显改善。

**如果第 5 条开始编造**：说明阈值太低，检索到了不相关片段。把 `MIN_SCORE` 从 2.0 提到 2.5，或检查语料是否覆盖过宽。

---

## 步骤 8（可选）：升级为向量检索

BM25 的短板是**词面不匹配**：用户问"尿酸能不能吃豆腐"，语料里写的是"豆制品"，二元组只能匹配到"尿酸"，"豆腐"与"豆制品"匹配不上。

升级路径，接口保持不变：

1. `uv add sentence-transformers`（或调用智谱/通义的 embedding API）；
2. 在 `src/rag/index.py` 里新增 `build_vector_index()`：把每个 `Chunk.text` 编码成向量，存为 `.npy`；
3. `src/rag/retriever.py` 增加 `search_vector()`：查询编码后算余弦相似度；
4. 在 `retriever.py` 里做**混合检索**：BM25 与向量各取 top-10，用 RRF（倒数排名融合）合并；
5. 用同一批测试问题对比两种方案的 top-1 命中率，再决定是否切换。

**建议先做 RRF 混合而不是直接替换**：BM25 对专有名词（"尿酸""ALT"）更准，向量对口语化描述更好，两者互补。

---

## 附：本次新增文件清单

| 文件 | 作用 |
|---|---|
| `data/knowledge/corpus/*.md`（5 个） | 语料，按 `##` 切块 |
| `src/rag/corpus.py` | 加载与切块 |
| `src/rag/index.py` | 分词与 BM25 索引构建 |
| `src/rag/retriever.py` | 检索与阈值过滤 |
| `src/rag/tools.py` | `knowledge_search` 工具 |
| `scripts/build_rag_index.py` | 索引构建命令 |
| `tests/test_rag.py` | 6 条测试 |
| `apply_rag_patch.sh` | 一次性接入脚本 |
| `.backup/src_agent_before_rag.py` | 自动备份的原 Agent |

改动仅 `src/agent.py` 一个文件：加 1 行 import、1 个工具、2 条提示词规则。

---

## 附：如何评估检索质量

别只看"能不能答上来"，要量化。做法是准备一份 gold set：

1. 列 20 个真实会问的问题，人工标注每条"应该命中哪一节"；
2. 跑 `search(q, top_k=3)`，统计两个指标：
   - **top-1 命中率**：第一条就是正确答案的比例；
   - **top-3 召回率**：正确答案出现在前三的比例；
3. 目标值：top-1 ≥ 80%，top-3 ≥ 95%。低于这个水平，先加语料，再调阈值。

语料规模小于 50 个片段时，BM25 通常能到 85% 以上；如果明显偏低，多半是切块粒度不对（一段太长）或语料没覆盖这个问题。

---

## 常见问题

| 症状 | 原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: src.rag` | 用了 `python scripts/...` 而非 `-m` | 改用 `uv run python -m scripts.build_rag_index` |
| 检索永远返回空 | 索引文件不存在或未构建 | 跑一次构建命令，确认 `rag_index.json` 生成 |
| 所有问题都命中同一篇 | 该篇过长、词频占优 | 拆细切块，或给 `tf` 加长度归一（`b` 调到 0.85） |
| 无关问题也有结果 | 阈值太低 | 提高 `MIN_SCORE`，或缩小语料主题范围 |
| 模型不调 knowledge_search | 工具描述不够具体 | 在 description 里补 2–3 个触发示例句 |
| 模型把语料当诊断依据 | 提示词缺少约束 | 强调"语料是科普，不是诊疗指南"，并保留免责声明 |
