# E1 怪梦 · 逐镜视频 prompt（P01–P14）

> 竖屏 9:16；每镜 5s（81 帧 smoke test，帧率 24）；ti2vid（文生视频，暂不带图）。
> 每条 prompt 固定三段拼接：【角色段】（角色视觉设定固定词）＋【场景段】（常用场景固定词）＋【光影固定词】，再加逐镜微动作。
> 去魅铁律：狐影/人影＝虚焦一闪，绝不给清晰脸。挂坠温度＝报马在场信号。
> 台词/报马画外音不入 prompt（AI 视频不出声，配音层后期叠加；此处仅在备注列标出供配音对照）。

## 定稿规格基准（2026-09-16 E1 全片验收通过后固化，E2–E27 铺开时复用）

**视频生成走 keyframe 模式（非 ti2vid）**：
- `scripts/gen_video.py --img 首帧图 --prompt "微动作" --out PXX.mp4`
- 首帧图用 `gen_image.py` i2i 出（参考宋栀_v2/玉坠定妆照锁脸+服装），**不要直接 ti2vid 纯文生视频**（人脸/服装/物件漂移不可控）
- 网关实测：`mode="keyframe"` 可用；`ti2vid`/`i2vid` 全部 400；`num_frames` 字段被网关禁止（时长默认 5s）
- 默认输出 **704x1280 竖屏 9:16、720P**，无需裁切（实测 keyframe 输出已竖屏，非 2.5-flash 的横屏 1152x768）

**物件一致性纪律（本轮踩坑定死）**：
- **泡面桶**：全季统一"橙红条纹杯面桶"（橙杯、红色横条纹、红字杯身、筷子搭杯口），不要换成白杯/蓝杯/其他品牌；出 P03/P08/P11 等含泡面桶的镜头时，**以 P02 那张首帧做 i2i 基准**，描述里写"同款橙条纹桶"，不要每镜各造一个
- **睡衣**：宋栀南方段 E1–E21 统一"浅蓝碎花旧睡衣"（浅蓝底、小碎花、长袖长裤），全季同一套，不要每镜漂成不同花色
- **电脑**：出租屋镜头里的笔记本**屏幕朝她、背面（银色金属背）朝镜头**，不露亮屏（避免亮屏里长出手/脸/AI 脸）；需要她看屏幕时只写"屏幕朝她"
- **手机**：视频通话镜头**不给手机屏幕画面**（嵌套画面=双重人脸+手部穿帮，AI 翻车率极高），改成"她举着手机、手机背面朝观众、屏幕内容不露"，杨永川的声音走画外音
- **手部纪律**：人物镜头 i2i prompt 必须显式写「single person, exactly two hands, no duplicated person, no second phone」——多手/双人/手机叠手背是插帧最典型翻车（P08 首帧 v1/v2/v3 均触发）
- **狐影**：全程**虚焦黑影、越虚越好**，不画清晰轮廓/狐耳/狐身，最多给"一道狐狸尾巴的影子虚焦扫过墙"；绝不卡通、绝不给脸、绝不清晰

**拼接**：14 镜各 5s，`ffmpeg -f concat` 串成 E1 全片（试片拼接版 ≈72s，正式 2 分钟版需配音/字幕/配乐压进来后按分镜时间轴裁切取段）。

## 全局固定词（每条 prompt 末尾自动拼接，不逐镜重复）

STYLE: live-action realistic short drama, amateur non-celebrity faces, natural light, no makeup, film grain, low saturation, everyday texture
LIGHT-E1: cold dim room, low-saturation cool tones, single warm practical light source (laptop glow / candle), soft shadows

---

## P01 · 钩子：黑屏→睁眼（0-3s 段内取 5s）

EN: Close-up of a young Northeastern Chinese woman's eyes opening in total darkness, cold dim room, her dark old jade pendant resting against her collarbone, faint warm glow reflecting off the jade. Slow subtle camera push-in.
CHAR: 22-year-old Northeastern Chinese woman, ordinary non-influencer face, slim and plain, slightly narrow round face, single eyelids, pale cool-toned skin, clear jawline, steady calm cold eyes, shoulders level, spine straight
STYLE: live-action realistic short drama, amateur non-celebrity faces, natural light, no makeup, film grain, low saturation, everyday texture
LIGHT: pitch-black room, only faint cool light on face, single warm practical light catching the jade pendant at her collarbone
NOTE: 报马画外音「你又"接"东西了」（配音层）；挂坠微热=热（开场暗号，观众先看到温度再看到人）

---

## P02 · 深夜出租屋·泡面+招聘网站（窘迫立住）

EN: Interior of a cramped university-town rental room at night. A young Northeastern Chinese woman in rumpled old pajamas sits at a small desk, steam rising from a cheap cup of instant noodles, laptop screen casting cold blue glow showing a job-recruitment site. Static camera, slow subtle drift.
CHAR: 22-year-old Northeastern Chinese woman, ordinary face, slim, low ponytail hair, rumpled old pajamas, dark old jade pendant at collarbone, shoulders level, spine straight
STYLE: live-action realistic, amateur faces, no makeup, film grain, low saturation
LIGHT: cold dim room, only warm steam glow + cold laptop blue, hard contrast, shadows in corners
NOTE: 钱债线起手·窘迫帧；冷暗 vs 他那边亮色的对照在本集 P03 拉出

---

## P03 · 视频通话·杨永川要钱（冷暗 vs 亮色对照 + 转账 1 秒停顿）

EN: Split-feel video call scene: on screen, a slightly overweight ordinary-looking Southern Chinese man in a brightly lit neat office waves casually; off-screen, the young woman in a cold dark room with instant noodles. She pauses for one second looking at the noodles, then taps her phone to transfer 2000 yuan; close-up of phone screen showing the transfer "ding".
CHAR-HER: 22-year-old Northeastern Chinese woman, low ponytail, jade pendant at collarbone
CHAR-HIM: 30-year-old ordinary slightly-fat Southern Chinese man, not handsome, tired face, eyes darting to his phone, old business-casual shirt
STYLE: live-action realistic, amateur faces, film grain, low saturation
LIGHT: her side cold dark, his side bright warm office light, deliberate contrast
NOTE: 杨永川「你先垫我两千？」/ 她转账"叮"声放大（声音层）/ 他「谢了，别老做怪梦，信点科学」；"停一秒再转"=习惯妥协第一格，轻而快

---

## P04 · 怪梦段·床边虚焦人影（狐影首现，一闪）

EN: Dream-logic night: a young Northeastern Chinese woman lies in bed in a cold dark room; a blurry out-of-focus human figure stands at the edge of the bed, face completely obscured, no CG, just soft defocused silhouette against faint light. As she tries to approach, the figure retreats one step behind her, then fades to darkness.
CHAR: 22-year-old Northeastern Chinese woman, low ponytail, jade pendant, face half-lit in sleep
STYLE: live-action realistic, amateur face, film grain, low saturation, soft focus on the figure only
LIGHT: cold dim, single faint warm practical candle off-frame, heavy shadow
NOTE: 报马画外音不接，只有极轻「……」（声音层）；**去魅铁律：人影全程虚焦一闪，绝不出清晰脸，无 CG**

---

## P05 · 醒来·枕上发丝缠了一夜（特写）

EN: Close-up of a tangled mass of hair on a pillow after a restless night, a young woman's hand gently brushing through it, the dark old jade pendant lying near her collarbone, the room dim in early morning cold light. Slow camera drift.
CHAR: 22-year-old Northeastern Chinese woman, low ponytail now loosened, jade pendant, shoulders level
STYLE: live-action realistic, amateur face, film grain, low saturation, early-morning cool window light
LIGHT: cold blue dawn light through narrow window, single warm off-frame practical
NOTE: 去魅暗解＝她焦虑失眠非真狐（不点破）；挂坠凉着（报马退走）

---

## P06 · 挂坠特写·凉（冷手贴冷玉）

EN: Extreme close-up of the dark old jade pendant (flat round safety-knot shape, worn matte dark ink-green jade with a hole in the center, thick frayed grey-brown cloth cord) held in a cool-toned hand against a collarbone, no warmth, matte texture, film grain.
STYLE: live-action macro, natural light, no makeup, film grain, low saturation
LIGHT: cold dim, no warm light touching the jade (contrast with P01's "微热")
NOTE: 报马退场信号＝凉；全季温度线 E1 落点（热→凉对照）

---

## P07 · 她自语"又是这个梦"·摸挂坠（定心动作）

EN: A young Northeastern Chinese woman in a cold dim rental room touches her dark jade pendant at her collarbone with one hand, eyes downcast, whispering to herself; static close-up on her face and hand.
CHAR: 22-year-old Northeastern Chinese woman, low ponytail, ordinary face, jade pendant
STYLE: live-action realistic, amateur face, film grain, low saturation
LIGHT: cold dim, single warm practical off-screen
NOTE: 宋栀内心「又是这个梦」；她以为是压力（去魅暗解）；定心动作＝摸挂坠，全季反复

---

## P08 · 决定回家·手机打字（轻而快）

EN: A young Northeastern Chinese woman types a short message on her phone, face half-lit by the screen, a train ticket confirmation briefly visible; quick cut energy, no lingering.
CHAR: 22-year-old Northeastern Chinese woman, low ponytail, rumpled pajamas, jade pendant
STYLE: live-action realistic, amateur face, film grain, low saturation
LIGHT: cold screen light only, shadows
NOTE: 她跟杨永川随口说"回趟家"（台词后期）；决定寒假回东北老家

---

## P09 · 站台钩子·火车进站（她看站台）

EN: A young Northeastern Chinese woman stands at a dim railway station platform at night, watching a train pull into the station, breath faintly visible in cold air, her figure small against the dark platform lights; wide static shot, slow subtle camera drift.
CHAR: 22-year-old Northeastern Chinese woman, low ponytail, dark coat, jade pendant barely visible, shoulders level
STYLE: live-action realistic, amateur face, film grain, low saturation
LIGHT: cold station lights, sodium-lamp yellow pools, heavy shadow, one warm practical far off
NOTE: 尾钩画面（下集接 E2 东北小站接站，同机位对称）

---

## P10 · 报马尾钩·她"没听见"（幻听感）

EN: Close-up of the young woman's face at the dark station platform, her eyes still on the arriving train, lips closed, a faint unfocused warm light shimmer behind her shoulder for one beat (no clear face, no CG), as if hearing a voice only she can hear; static shot.
CHAR: 22-year-old Northeastern Chinese woman, low ponytail, jade pendant, steady cold eyes
STYLE: live-action realistic, amateur face, film grain, low saturation
LIGHT: cold station light + one defocused warm shimmer behind her (报马狐影一闪, 逆光残影, 不给脸)
NOTE: 报马画外音（第一次正经开口，御姐，带"看透"）「堂口……在等你」（配音层）；她没听见/听成幻听

---

## P11 · 出租屋空镜·泡面余温（收束节奏）

EN: Static wide shot of the cold cramped rental room, empty desk with the still-warm cup of instant noodles and the glowing job-site laptop screen, no one in frame, film grain.
STYLE: live-action realistic, film grain, low saturation
LIGHT: cold dim, warm laptop glow only
NOTE: 纯过渡镜，给节奏呼吸

---

## P12 · 挂坠微热·热（报马"来"的信号，与 P01 呼应）

EN: Extreme close-up of the dark old jade pendant at a collarbone, this time a faint warm glow catching the worn matte jade, warm skin tone on the holding hand, matte jade texture, film grain.
STYLE: live-action macro, natural light, film grain, low saturation
LIGHT: single warm practical light catching the jade (contrast with P06 的冷)
NOTE: 温度线落点：E1 内"热"是被动发热（有东西在，报马来报）；与 E2"无故微热"同型

---

## P13 · 东北小站预告帧（接 E2 对称机位）

EN: Wide static shot of a small Northeastern Chinese railway station exit at night in snow, cold blue light, a single dark silhouette of a man standing under the station lamp (out of focus, no clear face), snow falling.
STYLE: live-action realistic, film grain, low saturation, cold
LIGHT: cold station lights, heavy snow, one warm practical off-frame
NOTE: E1 尾钩的"空间预告"（观众先闻 E2 的东北冷）；对称机位留 E2 接站用

---

## P14 · 黑场帧（尾钩留白）

EN: Pure black frame, faint film grain, 1 second of near-silence (no audio, no image detail).
NOTE: 报马"堂口在等你"话音落点；黑场 1s 静默再切 E2
