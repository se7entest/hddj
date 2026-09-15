#!/usr/bin/env python3
"""Agnes 视频生成小工具：首帧图生成视频(keyframe)，异步提交 + 轮询 + 下载。

端点实测（2026-09-15）：
- /v1/videos 只接受 mode="keyframe"（i2v/ti2vid/keyframes 等全部 400 invalid mode）
- keyframe 模式必须带 first_frame（URL 或 data URL），可另带 last_frame
- num_frames 字段被网关禁止（400 forbidden），时长/规格由服务侧定（默认 5s 720P）
- 提交偶发 503 video_queue_full，自动重试；免费版另有 429 限速

用法：
  python scripts/gen_video.py --prompt "..." --img 05_输出/定妆照/宋栀_v2.png [--last 尾帧图] [--out 05_输出/E1/P01.mp4]

  结果默认下载到 --out 指定路径；不传 --out 则打印 URL。

密钥读取顺序：环境变量 AGNES_API_KEY / AGNES_API_TOKEN / APIHUB_AGNES_API_KEY，
否则读项目根 .env。绝不打印密钥。
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
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
    p = Path(path)
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def resolve_image(ref: str) -> str:
    """本地路径转 data URL；http(s) URL 原样返回。"""
    if ref.startswith("http://") or ref.startswith("https://") or ref.startswith("data:"):
        return ref
    p = Path(ref)
    if not p.exists():
        raise SystemExit(f"首帧图不存在: {ref}")
    return image_to_data_url(str(p))


def submit_video(key: str, prompt: str, first_frame: str = None,
                 last_frame: str = None, retries: int = 5) -> dict:
    payload = {
        "model": VIDEO_MODEL,
        "prompt": prompt,
        "mode": "keyframe",
    }
    if first_frame:
        payload["first_frame"] = first_frame
    if last_frame:
        payload["last_frame"] = last_frame
    body = json.dumps(payload).encode()
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            f"{BASE_URL}/v1/videos",
            data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            if e.code in (503, 429) and attempt < retries:
                wait = 30 * attempt
                print(f"HTTP {e.code}（{err_body[:160]}）→ {wait}s 后重试 ({attempt}/{retries - 1})")
                time.sleep(wait)
                continue
            print(f"HTTP {e.code}: {err_body[:600]}")
            raise SystemExit(1)
    raise SystemExit("提交重试耗尽（持续 503/429），请稍后再试")


def get_video_id(resp: dict):
    if isinstance(resp, dict):
        for k in ("video_id", "task_id", "id"):
            v = resp.get(k)
            if isinstance(v, str) and v:
                return v
    return None


def poll_status(key: str, video_id: str, timeout: int = 900, interval: int = 30) -> dict:
    """轮询 /agnesapi?video_id= 直到 completed/failed。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        req = urllib.request.Request(
            f"{BASE_URL}/agnesapi?video_id={video_id}",
            headers={"Authorization": f"Bearer {key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
            status = str(data.get("status", "unknown")).lower()
            if status in ("completed", "finished"):
                return data
            if status in ("failed", "error"):
                print(f"任务失败: {json.dumps(data, ensure_ascii=False)[:800]}")
                raise SystemExit(1)
            print(f"  状态: {status}（progress={data.get('progress', '?')}）... 继续等待", flush=True)
        except (urllib.error.URLError, ConnectionResetError, OSError) as e:
            print(f"  轮询中断（{e}），{interval}s 后重试", flush=True)
        time.sleep(interval)
    print(f"轮询超时（{timeout}s），请稍后用 video_id 手动查询: {video_id}")
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
            elif isinstance(v, str) and v.startswith("http") and v.lower().split("?")[0].endswith((".mp4", ".webm")):
                return v
    return None


def main():
    ap = argparse.ArgumentParser(description="Agnes 首帧图生成视频（keyframe 模式）")
    ap.add_argument("--prompt", required=True, help="英文视频 prompt（动作/镜头/光影描述）")
    ap.add_argument("--img", help="首帧图（本地路径或 URL，URL 建议公网可达）")
    ap.add_argument("--last", help="尾帧图（可选，用于关键帧插值）")
    ap.add_argument("--out", help="结果下载到的本地路径；不传则只打印 URL")
    ap.add_argument("--timeout", type=int, default=900, help="轮询超时秒（默认 900）")
    args = ap.parse_args()

    key = load_key()
    first = resolve_image(args.img) if args.img else None
    last = resolve_image(args.last) if args.last else None

    print(f"提交视频任务（{VIDEO_MODEL}，mode=keyframe）...", flush=True)
    resp = submit_video(key, args.prompt, first_frame=first, last_frame=last)
    video_id = get_video_id(resp)
    if not video_id:
        print(f"未拿到 video_id，响应: {json.dumps(resp, ensure_ascii=False)[:600]}")
        raise SystemExit(1)
    print(f"video_id: {video_id}（{resp.get('status', '?')}）", flush=True)

    print("轮询任务状态...", flush=True)
    final = poll_status(key, video_id, timeout=args.timeout)
    url = extract_video_url(final)
    if not url:
        print(f"未找到视频 URL，完整响应: {json.dumps(final, ensure_ascii=False)[:1200]}")
        raise SystemExit(1)

    print(f"URL: {url}")
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(out))
        print(f"saved: {out} ({out.stat().st_size // 1024} KB)")
    else:
        print("（不传 --out 则不下载；需要可手动下载上面的 URL）")


if __name__ == "__main__":
    main()
