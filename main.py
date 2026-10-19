"""命令行入口：多成员健康助手。"""
import sys

from dotenv import load_dotenv

from src import storage
from src.agent import build_agent

load_dotenv()

MAX_HISTORY_TURNS = 6

HELP_TEXT = """可用命令
  /members            列出家庭成员
  /add 姓名 [关系]     新增成员并切换为当前
  /use 姓名或编号      切换当前成员
  report              生成当前成员的健康周报
  exit                退出
"""


def _show_members() -> None:
    members = storage.list_members()
    if not members:
        print("尚未建立成员，先执行：/add 姓名 [关系]")
        return
    current = storage.current_member()
    current_id = current["id"] if current else None
    for m in members:
        mark = "*" if m["id"] == current_id else " "
        relation = f"（{m['relation']}）" if m.get("relation") else ""
        print(f"  {mark} {m['id']}  {m['name']}{relation}")


def _switch(key: str) -> None:
    member = storage.find_member(key)
    if not member:
        print(f"未找到成员“{key}”，用 /members 查看已有成员。")
        return
    storage.set_member(member["id"])
    print(f"已切换到：{member['name']}")


def main() -> None:
    members = storage.list_members()
    if members:
        storage.set_member(members[0]["id"])

    agent = build_agent()
    history: list[tuple[str, str]] = []

    print("健康助手已启动。输入 /help 查看命令，exit 退出。")
    current = storage.current_member()
    print(f"当前成员：{current['name'] if current else '（未指定）'}")
    if not members:
        print("提示：先用 /add 姓名 [关系] 建立成员档案。")
    print()

    while True:
        try:
            user_input = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break

        if not user_input:
            continue
        lowered = user_input.lower()

        if lowered in {"exit", "quit", "q"}:
            print("已退出。")
            break

        if user_input in {"/help", "help"}:
            print(HELP_TEXT)
            continue

        if user_input == "/members":
            _show_members()
            continue

        if lowered.startswith("/add "):
            parts = user_input[5:].split(maxsplit=1)
            name = parts[0]
            relation = parts[1] if len(parts) > 1 else ""
            member = storage.register_member(name, relation)
            storage.set_member(member["id"])
            history.clear()
            print(f"已建立并切换到：{member['name']}{('（' + relation + '）') if relation else ''}")
            continue

        if lowered.startswith("/use "):
            _switch(user_input[5:].strip())
            history.clear()
            continue

        current = storage.current_member()
        if current is None:
            print("还没有选定成员，先执行：/add 姓名 [关系]")
            continue

        if lowered == "report":
            try:
                from src.report import build_report
                advice = agent.run("请基于我的数据给出三条具体建议")
                path = build_report(advice)
                print(f"\n报告已生成：{path}\n")
            except Exception as exc:
                print(f"[错误] 报告生成失败：{exc}\n")
            continue

        context = f"当前档案成员：{current['name']}。\n"
        if history:
            recent = history[-MAX_HISTORY_TURNS:]
            context += "以下是最近的对话，供参考：\n" + "\n".join(
                f"用户：{u}\n助手：{a}" for u, a in recent
            ) + "\n\n当前问题："

        try:
            answer = agent.run(context + user_input)
        except Exception as exc:
            print(f"[错误] 本轮处理失败：{exc}\n")
            continue

        print(f"\n助手 > {answer}\n")
        history.append((user_input, answer))


if __name__ == "__main__":
    sys.exit(main())
