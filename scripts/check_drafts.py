# -*- coding: utf-8 -*-
"""草稿体检：统计 02_剧本/ 与 01_大纲/ 的字数、场次、集数

用法：
    python scripts/check_drafts.py

输出示例：
    01_大纲/世界观设定.md  字数 12034  场景头 0
    02_剧本/第01集_开门.md  字数 856  场景 3  台词行 42
    合计 2 个剧本文件，平均单集 856 字（目标 400–700 字/集？请对照大纲）
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def count_chinese(text: str) -> int:
    return sum(1 for c in text if "一" <= c <= "鿿")


def main():
    total = 0
    n_scripts = 0
    for d in ("01_大纲", "02_剧本", "03_分镜"):
        folder = ROOT / d
        if not folder.exists():
            continue
        files = sorted(folder.glob("*.md"))
        for f in files:
            text = f.read_text(encoding="utf-8")
            words = count_chinese(text)
            total += words
            line_count = text.count("\n## ")
            extra = ""
            if d == "02_剧本":
                n_scripts += 1
                # 台词行：角色名：台词
                import re
                dialogue = len(re.findall(r"^\S{1,12}（[^）]*）：.+$", text, re.M))
                extra = f" 场景 {line_count}  台词 {dialogue}"
            elif line_count:
                extra = f" 小节 {line_count}"
            print(f"{f.name:30s} 字数 {words:>7}{extra}")
    if n_scripts:
        print(f"\n剧本 {n_scripts} 集，平均 {total // n_scripts} 字/集")


if __name__ == "__main__":
    main()
