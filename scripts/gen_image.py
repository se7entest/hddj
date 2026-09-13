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
import sys
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
    data = _shrink(data)
    return f"data:image/jpeg;base64," + base64.b64encode(data).decode()


def _shrink(data: bytes, max_side: int = 1024, quality: int = 85) -> bytes:
    """参考图超限会让请求体过大、服务端频繁断连；先压到 1024 边 JPEG 再传。"""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        if max(w, h) > max_side:
            scale = max_side / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=quality)
        return buf.getvalue()
    except Exception:
        return data


def find_i2i(x):
    """i2i 结果优先取大图 output_image（i2i 返回会附带 thumbnail_url，旧逻辑会误取）。"""
    if isinstance(x, dict):
        big = x.get("output_image")
        if isinstance(big, dict) and big.get("url"):
            return big["url"]
        for v in x.values():
            if isinstance(v, dict):
                r = find_i2i(v)
                if r:
                    return r
    elif isinstance(x, list):
        for v in x:
            r = find_i2i(v)
            if r:
                return r
    return None


def extract_t2i(x, k: int = 0):
    """文生图：按输出顺序取第 k 张（默认 0=第一张），取不到则退回大图/data。"""
    if isinstance(x, dict):
        found = []
        for key in ("url", "b64_json"):
            v = x.get(key)
            if v:
                found.append(v)
        if k < len(found):
            return found[k]
        for v in x.values():
            if isinstance(v, str) and (v.startswith("http") or v.startswith("data:")):
                return v
            if isinstance(v, (dict, list)):
                r = extract_t2i(v, k)
                if r:
                    found.append(r)
        if k < len(found):
            return found[k]
    elif isinstance(x, list):
        found = []
        for v in x:
            r = extract_t2i(v, k)
            if r:
                found.append(r)
        if k < len(found):
            return found[k]
    return None


def data_url_to_file(data: str, out: str) -> int:
    header, b64 = data.split(",", 1)
    Path(out).write_bytes(base64.b64decode(b64))
    return os.path.getsize(out)


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
    ap.add_argument("--ref", action="append", help="i2i 参考图：定妆照简写名（如 宋栀_玉坠）或本地路径，可多次传")
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
        payload["extra_body"]["image"] = [image_to_data_url(resolve_ref(r)) for r in args.ref]

    import time
    last_err = None
    for attempt in range(1, 4):
        req = urllib.request.Request(
            f"{BASE_URL}/v1/images/generations",
            data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read().decode())
            last_err = None
            break
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code}: {e.read().decode()[:800]}")
            raise SystemExit(1)
        except (urllib.error.URLError, ConnectionResetError, OSError) as e:
            last_err = e
            if attempt < 3:
                wait = 10 * attempt
                print(f"连接中断（{e}），{wait}s 后第 {attempt+1} 次重试...")
                time.sleep(wait)
    if last_err:
        print(f"重试后仍失败: {last_err}")
        raise SystemExit(1)

    if args.ref:
        # i2i：优先取大图，避免拿到 i2i 附带的第一张缩略图
        url = find_i2i(data)
        if url:
            print(f"URL: {url}")
            if args.out:
                urllib.request.urlretrieve(url, args.out)
                print(f"saved: {args.out} ({os.path.getsize(args.out)//1024} KB)")
            return

    # 文生图：默认取第一张；如需取其他序号图请改用 i2i 流程或改 prompt 重新生成
    url = extract_t2i(data, 0)
    if not url:
        print("未找到输出图 URL", file=sys.stderr)
        raise SystemExit(1)
    if url.startswith("data:"):
        if not args.out:
            print(url)
            return
        size = data_url_to_file(url, args.out)
        print(f"saved: {args.out} ({size//1024} KB)")
    else:
        print(f"URL: {url}")
        if args.out:
            urllib.request.urlretrieve(url, args.out)
            print(f"saved: {args.out} ({os.path.getsize(args.out)//1024} KB)")


if __name__ == "__main__":
    main()
