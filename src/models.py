"""数据模型：用户档案与每日记录。"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Profile:
    name: str
    sex: str                 # "male" | "female"
    age: int
    height_cm: float
    weight_kg: float
    activity: str = "light"  # sedentary|light|moderate|active|very_active
    conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DailyRecord:
    day: str                          # YYYY-MM-DD
    weight_kg: Optional[float] = None
    sleep_hours: Optional[float] = None
    steps: Optional[int] = None
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    water_ml: Optional[int] = None
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
