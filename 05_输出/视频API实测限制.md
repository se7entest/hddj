# 《狐渡》视频生成 API 实测限制记录（2026-09-15）

> 目的：Agnes 视频 API 端到端验证卡在两处，记录实测结果 + 规避方案，明天接着测。

## 已完成的工具与资产
- `scripts/gen_video.py`：异步提交→轮询→下载全链路，密钥复用 `.env`，不打印
- `05_输出/E1_prompt.md`：E1 怪梦 14 个逐镜英文 prompt（P01–P14），角色段+场景段+光影固定词+逐镜微动作拼接，去魅铁律已写进狐影帧
- 全季 27 集分镜已读完

## 卡点一：`mode` 字段枚举值不确定（最关键）

### 实测结论
`POST /v1/videos` **强制要求 `mode` 字段**（不传报 "mode is required"），但网关对取值做枚举校验，传错值报 400 "invalid mode"。

| 模型 | 测过的 mode 值 | 结果 |
|---|---|---|
| `agnes-video-2.5-flash` | ti2vid / keyframes / i2v / i2vid / t2v / text2video / image2video / first_last / auto / default / image / video | **全部 400 invalid mode**（2.5 网关枚举与文档不符） |
| `agnes-video-v2.0` | i2v / keyframes / video | 报 `fail_to_fetch_task`（非 invalid mode）；完整错误体暴露真实枚举：**`ti2vid` / `keyframes` / `multi_reference`** |

**关键发现**：v2.0 的错误体里写着 `Input should be 'ti2vid', 'keyframes' or 'multi_reference'`——这是上游 litellm 的真实枚举。但 2.5-flash 网关上连 `ti2vid`/`keyframes` 都报 invalid，说明 2.5-flash 网关的 mode 枚举校验规则和 v2.0 不一致（可能是 2.5-flash 只接受某个子集，或字段名/取值都不同）。

### 待明天验证
1. 用 `agnes-video-v2.0` + `mode=ti2vid` 或 `mode=keyframes` 提交，确认是否能真正拿到 video_id（跑通端到端）
2. 若 v2.0 通了，2.5-flash 的合法 mode 值仍需再探（可能得找网关侧文档或问 API 提供方）
3. 确认 v2.0 和 2.5-flash 出片质量差异，决定全季用哪个模型

## 卡点二：免费版限速（429）频繁

- 每次探测 mode 值都会烧掉一次配额，反复撞 429（"Upgrade to a Token Plan to unlock higher limits"）
- **规避**：明天测试前先 `time.sleep(90~120)` 让限速窗口完全恢复，再**只发一个请求**确认，避免批量探测把窗口磨空
- 免费版限速恢复周期实测约 60–120 秒

## 其他 API 行为记录
- `height`、`frame_rate`、`width`、`num_frames` 等字段在 2.5-flash 网关上全部 "forbidden field"——端点只接受 `model` + `prompt` + `mode`（+ 可选 image），时长/尺寸走默认值，**不能自定义竖屏 9:16 的 720x1280**，得用默认 1152x768 横屏再裁切/或接受默认
- 轮询端点 `GET /agnesapi?video_id={id}` 状态值：queued / in_progress / completed / failed
- 提交成功返回 `video_id`（推荐）或 `task_id`（旧版）；完成响应含 `video_url`/`url`

## 下一步（明天）
1. 限速恢复后，先试 `agnes-video-v2.0` + `mode=ti2vid`（不带图）跑 P01 端到端
2. 再试 `agnes-video-v2.0` + `mode=keyframes` + 首帧图（定妆照 `宋栀_v2.png`）跑 P01 图生视频
3. 确认输出尺寸/时长是否满足竖屏 9:16；若不满足，记录裁切方案
4. 2.5-flash 的合法 mode 值单独再探（或向 API 方确认）
