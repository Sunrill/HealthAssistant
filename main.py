"""命令行入口：交互式健康助手。"""
import sys

from dotenv import load_dotenv

from src.agent import build_agent

load_dotenv()

MAX_HISTORY_TURNS = 6


def main() -> None:
    agent = build_agent()
    history: list[tuple[str, str]] = []

    print("健康助手已启动。输入 exit 退出。")
    print("示例：我男 24 岁，身高 175，体重 70，轻度活动")
    print("示例：今天睡了 6.5 小时，走了 8000 步，血压 128/82")
    print("示例：report（生成健康周报）\n")

    while True:
        try:
            user_input = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "q"}:
            print("已退出。")
            break

        # 生成报告分支
        if user_input.lower() == "report":
            try:
                from src.report import build_report
                advice = agent.run("请基于我的数据给出三条具体建议")
                path = build_report(advice)
                print(f"\n报告已生成：{path}\n")
            except Exception as exc:
                print(f"[错误] 报告生成失败：{exc}\n")
            continue

        context = ""
        if history:
            recent = history[-MAX_HISTORY_TURNS:]
            context = "以下是最近的对话，供参考：\n" + "\n".join(
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
