"""体检报告的持久化：按当前成员隔离，按报告日期分文件。"""
import json
import os

from ..storage import _atomic_write, data_dir
from .models import LabItem, LabReport


def lab_dir() -> str:
    """当前成员的体检数据目录。"""
    return os.path.join(data_dir(), "lab")


def index_path() -> str:
    return os.path.join(lab_dir(), "index.json")


def save_lab_report(report: LabReport) -> None:
    os.makedirs(lab_dir(), exist_ok=True)
    _atomic_write(os.path.join(lab_dir(), f"{report.report_date}.json"), report.to_dict())

    index = load_lab_index()
    if report.report_date not in index:
        index.append(report.report_date)
        index.sort()
        _atomic_write(index_path(), index)


def load_lab_index() -> list[str]:
    path = index_path()
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_lab_report(report_date: str) -> LabReport | None:
    path = os.path.join(lab_dir(), f"{report_date}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return LabReport(
        report_date=raw["report_date"],
        institution=raw.get("institution", ""),
        items=[LabItem(**i) for i in raw["items"]],
        conclusions=raw.get("conclusions", []),
    )


def load_all_lab_reports() -> list[LabReport]:
    return [r for r in (load_lab_report(d) for d in load_lab_index()) if r]
