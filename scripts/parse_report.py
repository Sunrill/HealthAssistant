"""解析体检报告 PDF 并落库（支持指定成员）。

用法：
    uv run python -m scripts.parse_report <pdf路径> <YYYY-MM-DD> [机构名] [--member m2]
"""
import sys
from pathlib import Path

# 允许直接以脚本方式运行：把项目根目录加入 sys.path（pytest 由 pytest.ini 负责）
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import storage  # noqa: E402
from src.lab.parser import parse_pdf  # noqa: E402
from src.lab.rules import abnormal_items  # noqa: E402
from src.lab.store import save_lab_report  # noqa: E402
from src.lab.trend import display_period  # noqa: E402


def main() -> int:
    argv = sys.argv[1:]
    member_key = None
    if "--member" in argv:
        idx = argv.index("--member")
        if idx + 1 >= len(argv):
            print("--member 后面需要跟成员编号或姓名")
            return 1
        member_key = argv[idx + 1]
        del argv[idx:idx + 2]

    if len(argv) < 2:
        print("用法: uv run python -m scripts.parse_report <pdf路径> <YYYY-MM-DD> [机构名] [--member m2]")
        return 1

    path, date = argv[0], argv[1]
    institution = argv[2] if len(argv) > 2 else "某三甲医院"

    if not Path(path).exists():
        print(f"找不到文件: {path}")
        print("请先把体检报告放到 data/reports/ 下，例如：")
        print("  mkdir -p data/reports && cp <你的PDF> data/reports/checkup.pdf")
        return 1

    if member_key:
        member = storage.find_member(member_key)
        if not member:
            print(f"未找到成员“{member_key}”，现有成员：")
            for m in storage.list_members():
                print(f"  {m['id']}  {m['name']}")
            return 1
        storage.set_member(member["id"])
        print(f"当前成员: {member['name']}")
    else:
        members = storage.list_members()
        if members:
            print("提示: 未指定 --member，将写入根目录而非任何成员。")
            print("      可用成员: " + "、".join(f"{m['id']}({m['name']})" for m in members))

    report = parse_pdf(path, date, institution)

    print(f"报告期间: {display_period(date)}")
    print(f"指标总数: {len(report.items)}")
    by_panel: dict[str, int] = {}
    for item in report.items:
        by_panel[item.panel] = by_panel.get(item.panel, 0) + 1
    for panel, count in by_panel.items():
        print(f"  {panel or '(未分组)'}: {count}")

    abnormal = abnormal_items(report.items)
    print(f"异常项: {len(abnormal)}")
    for x in abnormal:
        print(f"  {x['name']} = {x['value']} {x['unit']} "
              f"(参考 {x['ref']}，偏离 {x['deviation_pct']}%，{x['severity']})")

    print(f"结论条数: {len(report.conclusions)}")
    for c in report.conclusions:
        print(f"  · {c}")

    save_lab_report(report)
    print(f"已保存到 {storage.data_dir()}/lab/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
