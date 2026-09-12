#!/usr/bin/env python3
"""Agnes 图像生成小工具：文生图 / 图生图(i2i)，可下载结果到本地。

用法：
  python scripts/gen_image.py --prompt "..." [--ref 宋栀_玉坠] [--size 736x1312] [--out 05_输出/定妆照/xxx.png]

--ref 两种写法：
  1. 定妆照简写名（推荐）：宋栀 / 宋栀_玉坠 / 吴依依_红绳银铃 / 杨永川 / 周野 /
     刘桂兰 / 报马_光影 / 马半仙_手 —— 自动解析到 05_输出/定妆照/<名>.png
  2. 任意本地图片路径

密钥读取顺序：环境变量 AGNES_API_KEY / AGNES_API_TOKEN / APIHUB_AGNES_API_KEY，
否则读项目根 .env。绝不打印密钥。
"""
import argparse
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://apihub.agnes-ai.com"
IMAGE_MODEL = "agnes-image-2.5-flash"


def load_key() -> str:
    for var in ("AGNES_API_KEY", "AGNES_API_TOKEN", "APIHUB_AGNES_API_KEY"):
        val = os.environ.get(var)
        if val:
            return val
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            for var in ("AGNES_API_KEY=", "AGNES_API_TOKEN=", "APIHUB_AGNES_API_KEY="):
                if line.startswith(var):
                    return line[len(var):].strip()
    raise SystemExit("未找到 Agnes API key（设置 AGNES_API_KEY 或写入 .env）")


def image_to_data_url(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/png"
    data = Path(path).read_bytes()
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def extract_urls(x):
    urls = []
    if isinstance(x, dict):
        for v in x.values():
            if isinstance(v, str) and v.startswith("http"):
                urls.append(v)
            else:
                urls += extract_urls(v)
    elif isinstance(x, list):
        for v in x:
            urls += extract_urls(v)
    return urls


REF_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def resolve_ref(name: str) -> str:
    p = Path(name)
    if p.exists():
        return str(p)
    ref_dir = Path(__file__).resolve().parent.parent / "05_输出" / "定妆照"
    base = name if p.suffix.lower() in REF_EXTS else name
    for ext in REF_EXTS:
        alt = ref_dir / f"{base}{ext}"
        if alt.exists():
            return str(alt)
    found = sorted(x.name for x in ref_dir.iterdir() if x.suffix.lower() in REF_EXTS)
    raise SystemExit(f"参考图未找到：{name}（定妆照目录现有：{'、'.join(found) or '空'}）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True, help="英文生成 prompt")
    ap.add_argument("--ref", help="i2i 参考图：定妆照简写名（如 宋栀_玉坠）或本地路径（可多次传：重复 --ref）")
    ap.add_argument("--size", default="736x1312")
    ap.add_argument("--out", help="结果下载到的本地路径")
    args = ap.parse_args()

    key = load_key()
    payload = {
        "model": IMAGE_MODEL,
        "prompt": args.prompt,
        "size": args.size,
        "extra_body": {"response_format": "url"},
    }
    if args.ref:
        payload["extra_body"]["image"] = [image_to_data_url(resolve_ref(args.ref))]

    req = urllib.request.Request(
        f"{BASE_URL}/v1/images/generations",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:800]}")
        raise SystemExit(1)

    url = extract_urls(data)[0]
    print(f"URL: {url}")
    if args.out:
        urllib.request.urlretrieve(url, args.out)
        print(f"saved: {args.out} ({os.path.getsize(args.out)//1024} KB)")


if __name__ == "__main__":
    main()
