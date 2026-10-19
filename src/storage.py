"""JSON 持久化：支持多成员（家庭成员）档案。

目录约定：
    data/members.json              成员注册表
    data/members/<id>/profile.json
    data/members/<id>/records.json
    data/members/<id>/lab/...
未注册任何成员时回退到 data/ 根目录，兼容单用户旧数据。
"""
import json
import os
from typing import Optional

from .models import DailyRecord, Profile

DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MEMBERS_DIR = os.path.join(DATA_ROOT, "members")
REGISTRY_PATH = os.path.join(DATA_ROOT, "members.json")

_current_dir = DATA_ROOT
_current_id: str | None = None


def _atomic_write(path: str, payload) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ---------------- 成员管理 ----------------

def load_registry() -> list[dict]:
    if not os.path.exists(REGISTRY_PATH):
        return []
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_registry(members: list[dict]) -> None:
    _atomic_write(REGISTRY_PATH, members)


def list_members() -> list[dict]:
    return load_registry()


def register_member(name: str, relation: str = "") -> dict:
    """按姓名注册成员，已存在则直接返回。id 用 m1/m2 这类 ASCII 编号，避免路径编码问题。"""
    members = load_registry()
    for m in members:
        if m["name"] == name:
            return m
    used = {m["id"] for m in members}
    n = 1
    while f"m{n}" in used:
        n += 1
    member = {"id": f"m{n}", "name": name, "relation": relation}
    members.append(member)
    save_registry(members)
    return member


def find_member(key: str) -> dict | None:
    for m in load_registry():
        if key in (m.get("id"), m.get("name")):
            return m
    return None


def current_member() -> dict | None:
    return find_member(_current_id) if _current_id else None


def set_member(member_id: str | None) -> None:
    """切换当前成员；传 None 回退到根目录。"""
    global _current_dir, _current_id
    _current_id = member_id
    _current_dir = os.path.join(MEMBERS_DIR, member_id) if member_id else DATA_ROOT


def data_dir() -> str:
    return _current_dir


# ---------------- 档案与记录 ----------------

def _profile_path() -> str:
    return os.path.join(_current_dir, "profile.json")


def _records_path() -> str:
    return os.path.join(_current_dir, "records.json")


def save_profile(profile: Profile) -> None:
    _atomic_write(_profile_path(), profile.to_dict())


def load_profile() -> Optional[Profile]:
    path = _profile_path()
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return Profile(**json.load(f))


def load_records() -> list[DailyRecord]:
    path = _records_path()
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [DailyRecord(**item) for item in json.load(f)]


def upsert_record(record: DailyRecord) -> None:
    """同一天重复录入时覆盖而非追加。"""
    records = {r.day: r for r in load_records()}
    records[record.day] = record
    ordered = [records[d].to_dict() for d in sorted(records)]
    _atomic_write(_records_path(), ordered)
