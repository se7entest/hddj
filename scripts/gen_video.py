#!/usr/bin/env python3
"""Agnes 视频生成小工具：文生视频 / 图生视频(i2v)，异步提交 + 轮询 + 下载。

用法（文生视频）：
  python scripts/gen_video.py --prompt "..." [--out 05_输出/E1/P01.mp4] [--smoke]

用法（图生视频，带首帧参考图）：
  python scripts/gen_video.py --prompt "..." --img 05_输出/定妆照/宋栀_v2.png [--out 05_输出/E1/P01.mp4]

  --smoke：用 81 帧快跑冒烟测试（默认 121 帧=5s，帧率 24）
  结果默认下载到 --out 指定路径；不传 --out 则打印 URL。

密钥读取顺序：环境变量 AGNES_API_KEY / AGNES_API_TOKEN / APIHUB_AGNES_API_KEY，
否则读项目根 .env。绝不打印密钥。
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://apihub.agnes-ai.com"
VIDEO_MODEL = "agnes-video-2.5-flash"


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
    import base64, mimetypes
    from gen_image import image_to_data_url as _i2u
    return _i2u(path)


def submit_video(key: str, prompt: str, image: str = None,
                 mode: str = "ti2vid", extra: dict = None) -> dict:
    payload = {
        "model": VIDEO_MODEL,
        "prompt": prompt,
        "mode": mode,
    }
    if image:
        # 图生视频：输入图作为首帧锚（支持 data URL 或 http URL）
        payload["extra_body"] = {"image": [image]}
    if extra:
        payload.update(extra)
    if image:
        # 图生视频：输入图作为首帧锚（支持 data URL 或 http URL）
        payload["extra_body"] = {"image": [image]}
    req = urllib.request.Request(
        f"{BASE_URL}/v1/videos",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:800]
        print(f"HTTP {e.code}: {body}")
        raise SystemExit(1)


def get_video_id(resp: dict):
    if isinstance(resp, dict):
        if "video_id" in resp:
            return resp["video_id"]
        for v in resp.values():
            if isinstance(v, str) and v.startswith("vid"):
                return v
            if isinstance(v, dict):
                r = get_video_id(v)
                if r:
                    return r
    return None


def poll_status(key: str, video_id: str, timeout: int = 600, interval: int = 10) -> dict:
    """轮询视频任务直到 completed/failed，返回最终响应。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(
            f"{BASE_URL}/agnesapi?video_id={video_id}",
            headers={"Authorization": f"Bearer {key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
            status = data.get("status", data.get("state", "unknown"))
            if status in ("completed", "finished"):
                return data
            if status in ("failed", "error"):
                print(f"任务失败: {json.dumps(data, ensure_ascii=False)[:600]}")
                raise SystemExit(1)
            print(f"  状态: {status} ... 继续等待")
        except (urllib.error.URLError, ConnectionResetError, OSError) as e:
            print(f"  轮询中断（{e}），3s 后重试")
        time.sleep(interval)
    print("轮询超时（600s），请手动用 video_id 查询")
    raise SystemExit(1)


def extract_video_url(data: dict):
    """从完成响应里挖视频 URL。"""
    if isinstance(data, dict):
        for key in ("video_url", "url"):
            v = data.get(key)
            if isinstance(v, str) and v.startswith("http"):
                return v
        for v in data.values():
            if isinstance(v, dict):
                r = extract_video_url(v)
                if r:
                    return r
            elif isinstance(v, str) and v.startswith("http") and v.lower().endswith((".mp4", ".webm")):
                return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True, help="英文视频 prompt")
    ap.add_argument("--img", help="图生视频首帧图（本地路径或 URL）")
    ap.add_argument("--out", help="结果下载到的本地路径")
    ap.add_argument("--mode", default="i2v", choices=["i2v"],
                    help="生成模式（端点只接受 i2v；纯文生视频也走 i2v，不带首帧图）")
    ap.add_argument("--width", type=int, default=None, help="输出宽（可选，端点支持时才传）")
    ap.add_argument("--frames", type=int, default=None, help="帧数（可选，端点支持时才传）")
    ap.add_argument("--timeout", type=int, default=600, help="轮询超时秒（默认 600）")
    args = ap.parse_args()

    key = load_key()
    extra = {}
    if args.width:
        extra["width"] = args.width
    if args.frames:
        extra["num_frames"] = args.frames

    image = args.img
    if image and not image.startswith("http"):
        p = Path(image)
        if p.exists():
            image = image_to_data_url(str(p))
        else:
            raise SystemExit(f"首帧图不存在: {image}")

    print(f"提交视频任务（{VIDEO_MODEL}，mode={args.mode}）...")
    resp = submit_video(key, args.prompt, image=image, mode=args.mode, extra=extra or None)
    video_id = get_video_id(resp)
    if not video_id:
        print(f"未拿到 video_id，响应: {json.dumps(resp, ensure_ascii=False)[:600]}")
        raise SystemExit(1)
    print(f"video_id: {video_id}")

    print("轮询任务状态...")
    final = poll_status(key, video_id, timeout=args.timeout)
    url = extract_video_url(final)
    if not url:
        print(f"未找到视频 URL，完整响应: {json.dumps(final, ensure_ascii=False)[:1200]}")
        raise SystemExit(1)

    print(f"URL: {url}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, args.out)
        print(f"saved: {args.out} ({os.path.getsize(args.out)//1024} KB)")
    else:
        print("（不传 --out 则不下载；需要可手动下载上面的 URL）")


if __name__ == "__main__":
    main()
