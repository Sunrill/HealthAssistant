"""体检报告的数据模型。

放在 lab 包内而非 src/models.py，使拓展模块自包含，避免改动已有文件。
"""
from dataclasses import asdict, dataclass, field
from typing import Union


@dataclass
class LabItem:
    """单个检验指标。数值保存解析出的原始形态，不做加工。"""
    name: str
    value: Union[float, str]          # 数值型存 float，定性项存 "-" / "黄色" 等原值
    unit: str = ""
    ref_low: float | None = None
    ref_high: float | None = None
    flag: str = "unknown"             # normal / high / low / unknown
    panel: str = ""                   # 血常规 / 肝功能 / 肾功能 / 血脂 / 血糖 / 糖化 / 尿常规

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LabReport:
    """一次体检的全部指标与结论。"""
    report_date: str
    institution: str = ""
    items: list[LabItem] = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "report_date": self.report_date,
            "institution": self.institution,
            "items": [i.to_dict() for i in self.items],
            "conclusions": self.conclusions,
        }
