# -*- coding: utf-8 -*-
"""分镜表生成器：把分镜 Markdown（每场一节）转成 Excel/CSV 表格

分镜 Markdown 约定（03_分镜/第XX集_分镜.md）：
    # 第03集 分镜
    ## 场1 · 地点 · 日/夜 · 内/外
    | 镜号 | 景别 | 画面内容 | 台词/旁白 | 音效 | 时长(秒) |
    |------|------|----------|-----------|------|-----------|
    | 1    | 全景 | …        | …         | …    | 3         |

用法：
    python scripts/storyboard_table.py 03            # 输出 05_输出/第03集_分镜表.csv
    python scripts/storyboard_table.py 03 --xlsx     # 输出 .xlsx（需 pip install openpyxl）
"""
import re
import sys
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "03_分镜"
OUT = ROOT / "05_输出"

HEADER = ["集", "场次", "镜号", "景别", "画面内容", "台词/旁白", "音效", "时长(秒)"]


def parse(md_file: Path, ep_no: str):
    rows = []
    scene = ""
    in_table = False
    for raw in md_file.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        m = re.match(r"^##\s*场?\s*(\S+)", line)
        if line.startswith("## ") and not m:
            m2 = re.match(r"^##\s+(.+)$", line)
            if m2 and "场" in m2.group(1):
                scene = m2.group(1).split("·")[0].strip()
        elif re.match(r"^\|[-\s|]+\|?$", line):
            in_table = True
            continue
        elif line.startswith("|") and in_table:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] in HEADER[2:]:  # 跳过表头行
                continue
            if len(cells) >= 6:
                rows.append([ep_no, scene, cells[0], cells[1], cells[2], cells[3],
                            cells[4], cells[5]])
        elif line.strip():
            in_table = False
    return rows


def main():
    args = [a for a in sys.argv[1:]]
    xlsx = "--xlsx" in args
    args = [a for a in args if a != "--xlsx"]
    if not args:
        sys.exit("用法：python scripts/storyboard_table.py 03 [--xlsx]")
    ep = args[0]
    files = list(SRC.glob(f"第{int(ep):02d}_*分镜*.md")) + list(SRC.glob(f"第{ep}_*分镜*.md"))
    if not files:
        sys.exit(f"未找到第{ep}集分镜文件（03_分镜/ 下）")
    rows = parse(files[0], ep.zfill(2))
    if not rows:
        sys.exit("分镜文件中没有解析到表格行，请检查格式")
    OUT.mkdir(exist_ok=True)
    if xlsx:
        try:
            import openpyxl
        except ImportError:
            sys.exit("缺少依赖 openpyxl，请先运行：pip install openpyxl")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"第{ep.zfill(2)}集分镜"
        ws.append(HEADER)
        for r in rows:
            ws.append(r)
        path = OUT / f"第{ep.zfill(2)}集_分镜表.xlsx"
        wb.save(str(path))
    else:
        path = OUT / f"第{ep.zfill(2)}集_分镜表.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(HEADER)
            w.writerows(rows)
    print(f"[完成] 共 {len(rows)} 个镜头 → {path.name}")


if __name__ == "__main__":
    main()
