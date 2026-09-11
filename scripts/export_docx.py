# -*- coding: utf-8 -*-
"""剧本 Markdown 批量导出 Word (.docx)

用法：
    python scripts/export_docx.py          # 导出 02_剧本/ 下全部
    python scripts/export_docx.py 03       # 只导出第03集
    python scripts/export_docx.py 01 03    # 导出第01、03集

依赖：pip install python-docx
输出：05_输出/第XX集_集名.docx
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "02_剧本"
OUT = ROOT / "05_输出"


def pick_files(argv):
    if not argv:
        return sorted(SRC.glob("第*.md"))
    picked = []
    for num in argv:
        m = list(SRC.glob(f"第{int(num):02d}_*.md")) + list(SRC.glob(f"第{num}_*.md"))
        if not m:
            print(f"[警告] 未找到第{num}集剧本")
        picked += m
    return sorted(picked)


def md_to_docx(md_path: Path, docx_path: Path):
    """轻量 Markdown → docx：识别 标题/场景头/动作行/角色台词行"""
    try:
        from docx import Document
        from docx.shared import Pt
        from docx.oxml.ns import qn
    except ImportError:
        sys.exit("缺少依赖 python-docx，请先运行：pip install python-docx")

    doc = Document()
    # 正文中文字体
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    lines = md_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        s = line.rstrip()
        if not s.strip():
            continue
        if s.startswith("# "):
            doc.add_heading(s[2:].strip(), level=0)
        elif s.startswith("## "):
            # 场景头：场1 · 地点 · 日/夜 · 内/外
            doc.add_heading(s[3:].strip(), level=1)
            doc.paragraphs[-1].runs[0].font.size = Pt(14)
        elif s.startswith("### "):
            doc.add_heading(s[4:].strip(), level=2)
        else:
            p = doc.add_paragraph()
            # 角色台词行：角色名（提示）：台词 → 加粗角色名
            m = re.match(r"^(?!\()(\S{1,12})(?:（[^）]*）)?：(.*)$", s.strip())
            if m:
                r1 = p.add_run(m.group(1))
                r1.bold = True
                r2 = p.add_run("：")
                r2.bold = True
                p.add_run(m.group(3))
            else:
                p.add_run(s.strip())
    doc.save(str(docx_path))
    print(f"[完成] {md_path.name} → {docx_path.name}")


def main():
    files = pick_files(sys.argv[1:])
    if not files:
        sys.exit("没有可导出的剧本（02_剧本/ 为空？）")
    OUT.mkdir(exist_ok=True)
    for f in files:
        docx_path = OUT / f.name.replace(".md", ".docx")
        md_to_docx(f, docx_path)
    print(f"共导出 {len(files)} 集 → {OUT}/")


if __name__ == "__main__":
    main()
