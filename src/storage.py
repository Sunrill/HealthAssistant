"""JSON 持久化：单文件存储，写入采用临时文件替换，避免中断导致文件损坏。"""
import json
import os
from typing import Optional

from .models import Profile, DailyRecord

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
RECORDS_PATH = os.path.join(DATA_DIR, "records.json")


def _atomic_write(path: str, payload) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def save_profile(profile: Profile) -> None:
    _atomic_write(PROFILE_PATH, profile.to_dict())


def load_profile() -> Optional[Profile]:
    if not os.path.exists(PROFILE_PATH):
        return None
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return Profile(**json.load(f))


def load_records() -> list[DailyRecord]:
    if not os.path.exists(RECORDS_PATH):
        return []
    with open(RECORDS_PATH, encoding="utf-8") as f:
        return [DailyRecord(**item) for item in json.load(f)]


def upsert_record(record: DailyRecord) -> None:
    """同一天重复录入时覆盖而非追加。"""
    records = {r.day: r for r in load_records()}
    records[record.day] = record
    ordered = [records[d].to_dict() for d in sorted(records)]
    _atomic_write(RECORDS_PATH, ordered)
