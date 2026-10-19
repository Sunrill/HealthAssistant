"""体检报告解析。

策略：先把 PDF 抽成纯文本，再按行流识别「名 → 值 → 标志 → 区间 → 单位」五元组。
面板标题只在「其后紧跟 检查者/检查项目」时才算标题，避免与同名指标（如糖化血红蛋白）冲突。
pymupdf 采用惰性导入：未安装时其余功能仍可正常使用。
当前规则针对单一机构版式校准，换机构需重新调规则。
"""
import re

from .models import LabItem, LabReport

DEFAULT_INSTITUTION = "某三甲医院"

NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")
RANGE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*[-–~]\s*(\d+(?:\.\d+)?)$")
GT_RE = re.compile(r"^>\s*(\d+(?:\.\d+)?)$")
LT_RE = re.compile(r"^<\s*(\d+(?:\.\d+)?)$")
UNIT_HINT = re.compile(r"(10\^|/L|/dL|g/L|%|μmol|mmol|U/L|fL|fl|ml/L|pg|mmHg|×)")

FLAGS = {"↑": "high", "↓": "low", "H": "high", "L": "low"}
TEXT_VALUES = {"-", "+-", "±", "+", "++", "+++"}

PANEL_MAP = {
    "血常规": "血常规",
    "肝功能11 项": "肝功能", "肝功能11项": "肝功能",
    "肾功能3 项": "肾功能", "肾功能3项": "肾功能",
    "血脂四项": "血脂",
    "血糖": "血糖",
    "糖化血红蛋白": "糖化",
    "尿常规": "尿常规",
}

SKIP = {
    "", "检查项目", "检查结果", "标志", "参考值", "单位",
    "检验检查结果：", "检验小结：", "常规检查结果：",
}

# 页眉噪声前缀；若你的报告页眉含机构全名，可在此补充对应前缀
NOISE_PREFIX = (
    "第 ", "姓名：", "报告生成时间", "录入者", "检查者",
    "审核", "小结", "=====", "检验检查结果", "检验小结",
)


def _clean(line: str) -> str:
    return line.replace("\u3000", " ").strip()


def _is_noise(line: str) -> bool:
    return any(line.startswith(p) for p in NOISE_PREFIX)


def _is_panel_header(lines: list[str], i: int) -> bool:
    """只有紧跟着「检查者/检查项目」的同名行才算面板标题。"""
    if lines[i] not in PANEL_MAP:
        return False
    if i + 1 >= len(lines):
        return False
    nxt = lines[i + 1]
    return nxt == "检查项目" or nxt.startswith("检查者")


def _parse_range(token: str):
    """返回 (low, high)；无法解析返回 (None, None)。"""
    token = token.strip()
    m = RANGE_RE.match(token)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = GT_RE.match(token)
    if m:
        return float(m.group(1)), None
    m = LT_RE.match(token)
    if m:
        return None, float(m.group(1))
    return None, None


def _is_name(line: str) -> bool:
    if not line or line in SKIP:
        return False
    if _is_noise(line) or line.startswith("·"):
        return False
    if NUM_RE.match(line) or RANGE_RE.match(line) or line in FLAGS:
        return False
    if len(line) > 40:
        return False
    # 单位行不能当指标名：短、含单位特征、几乎不含中文
    if len(line) <= 12 and UNIT_HINT.search(line) and not re.search(r"[\u4e00-\u9fa5]{2,}", line):
        return False
    return True


def parse_text(text: str, report_date: str, institution: str = DEFAULT_INSTITUTION) -> LabReport:
    lines = [_clean(x) for x in text.splitlines()]
    items: list[LabItem] = []
    conclusions: list[str] = []
    panel = ""

    i = 0
    while i < len(lines):
        line = lines[i]

        if _is_panel_header(lines, i):
            panel = PANEL_MAP[line]
            i += 1
            continue

        if line.startswith("·"):
            conclusions.append(line.lstrip("·").strip())
            i += 1
            continue

        if not _is_name(line):
            i += 1
            continue

        if i + 1 >= len(lines):
            break
        value_token = lines[i + 1]
        if not (NUM_RE.match(value_token) or value_token in TEXT_VALUES):
            i += 1
            continue

        name = line
        value = float(value_token) if NUM_RE.match(value_token) else value_token
        j = i + 2

        flag = "unknown"
        if j < len(lines) and lines[j] in FLAGS:
            flag = FLAGS[lines[j]]
            j += 1

        ref_low = ref_high = None
        if j < len(lines):
            low, high = _parse_range(lines[j])
            if low is not None or high is not None:
                ref_low, ref_high = low, high
                j += 1
            elif lines[j] in ("-", "+-"):
                j += 1

        unit = ""
        if j < len(lines) and UNIT_HINT.search(lines[j]) and not _is_name(lines[j]):
            unit = lines[j]
            j += 1

        items.append(LabItem(
            name=name.lstrip("*").strip(),
            value=value,
            unit=unit,
            ref_low=ref_low,
            ref_high=ref_high,
            flag=flag,
            panel=panel,
        ))
        i = j

    return LabReport(report_date=report_date, institution=institution,
                     items=items, conclusions=conclusions)


def parse_pdf(path: str, report_date: str, institution: str = DEFAULT_INSTITUTION) -> LabReport:
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("解析 PDF 需要 pymupdf，请先执行 uv add pymupdf") from exc

    doc = pymupdf.open(path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return parse_text(text, report_date, institution)
