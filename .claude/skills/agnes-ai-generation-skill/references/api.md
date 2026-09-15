# Agnes AI API Reference

Base host: `https://apihub.agnes-ai.com`

Authentication: `Authorization: Bearer YOUR_API_KEY`

Content type: `application/json`

## Text

Endpoint: `POST /v1/chat/completions`

Model: `agnes-3.0-flash`

Required:

- `model`: fixed as `agnes-3.0-flash`
- `messages`: OpenAI-compatible chat messages

Optional:

- `temperature`: number
- `top_p`: number
- `max_tokens`: number
- `stream`: boolean
- `tools`: array
- `tool_choice`: string or object

Response is OpenAI-compatible and includes `choices[].message.content` and `usage`.

## Image

Endpoint: `POST /v1/images/generations`

Model: `agnes-image-2.5-flash`

Required:

- `model`: fixed as `agnes-image-2.5-flash`
- `prompt`: text instruction for image generation or editing

Optional:

- `size`: output size such as `1024x768`
- `extra_body.image`: array of input image URLs for image-to-image
- `extra_body.response_format`: use `url` for image URLs

Prompt structure:

`[Subject] + [Scene / Environment] + [Style] + [Lighting] + [Composition] + [Quality Requirements]`

For image-to-image, state what should change and what must remain unchanged.

For non-English user prompts, translate to English before sending the request. Preserve visual specifics and constraints.

## Video

Create task endpoint: `POST /v1/videos`

Recommended result endpoint: `GET /agnesapi?video_id={video_id}`

Legacy task endpoint: `GET /v1/videos/{task_id}`

Model: `agnes-video-2.5-flash`

Live behavior confirmed by probing (2026-09-15) — treat these as authoritative over the older notes below:

- `mode` is REQUIRED. The gateway only accepts `mode="keyframe"`. All other values (`i2v`, `ti2vid`, `keyframes`, `t2v`, `video`, …) return `400 invalid mode`.
- `keyframe` mode requires `first_frame` and/or `last_frame` (image URL; data URLs likely work but use public URLs when possible). Omitting them returns `400: keyframe mode requires first_frame and/or last_frame`.
- There is no text-only video mode: anchor every video with a `first_frame` image.
- `num_frames` is a **forbidden field** (`400`). Duration and specs are server-side (create response reports e.g. `seconds: "5"`, `size: "720P"`).
- Create responses return `video_id`/`task_id` with a `task_` prefix — use that string directly with `GET /agnesapi?video_id=...`.
- Transient errors: `503 video_queue_full` (retry) and `429 rate_limit_exceeded` on the free plan (space out requests, ~40-60s).
- Generation takes ~3-5 min end-to-end (queued → in_progress → completed ~300s); poll with generous timeout.

Required:

- `model`: fixed as `agnes-video-2.5-flash`
- `prompt`: text description of the video
- `mode`: `"keyframe"`
- `first_frame`: input image URL (unless `last_frame` is the only frame supplied)

Optional:

- `last_frame`: second keyframe URL for interpolation between two keyframes
- `seed`: integer for reproducibility
- `negative_prompt`: string

Common status values:

- `queued` / `pending`
- `in_progress`
- `completed`
- `failed`

The create response may include both `task_id` and `video_id` (same `task_...` value); the completed response includes the video URL at top-level `url`.

## Error Codes

- `400`: invalid request
- `401`: unauthorized; check API key
- `404`: task not found
- `500`: server error
- `503`: service busy; retry later
