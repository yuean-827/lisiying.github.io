# reference.md — 详细参数与踩坑记录

本文件是 `SKILL.md` 的补充资料。SKILL.md 只保留核心流程，这里放具体参数、API 细节和踩过的坑。

## 1. 目录约定

```
<书名>/
├── script.md          剧本
├── 分镜.md            分镜表
├── 图片/              原始配图（生成尺寸，如水印未清）
├── 图片916/           清理水印并裁成 9:16 的成品图（合成时读这里）
├── 音频/01-08.mp3     旁白
├── 视频/01-08.mp4     动态素材
├── _tmp/              逐段渲染中间产物（可删）
└── 成片/
    ├── <书名>_名著介绍_9x16.mp4    高质量母版（CRF 19）
    └── <书名>_网页版.mp4           网页发布版（CRF 26）
```

## 2. 生图

**内置 ImageGen**

- `size` 传 `1024x1536`（2:3，接近 9:16），`quality` 传 `high`
- 产物右下角带「AI生成 WORKBUDDY>」水印

**火山方舟 Seedream**

```
POST https://ark.cn-beijing.volces.com/api/v3/images/generations
model: doubao-seedream-4-0-250828
Authorization: Bearer <ark- 开头的 key>
```

## 3. 生视频

**内置 VideoGen**

- 传 `image` 即图生视频（首帧）；同时传 `last_image` 可做首尾帧
- `resolution`：`720P` / `1080P`
- 5 秒一段，约 50-100 积分
- **产物右下角带「视频由AI生成」水印**

**火山方舟 Seedance**

```
POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
model: doubao-seedance-1-0-pro-fast-251015   （或 doubao-seedance-1-0-lite-i2v-250428）
```

## 4. 水印处理

### 4.1 图片水印

在 1024x1536 图上，水印位置约为 `x 770-1000, y 1420-1534`。

处理方式：**从水印正上方克隆一块等大纹理覆盖，再按中心裁剪成 9:16**。
换模型或换生成尺寸后必须重新定位，不要沿用旧坐标。

### 4.2 视频水印

在 1080x1920 上，「视频由AI生成」位于 `x 850-1055, y 1865-1910`。

**不要用 `delogo`**——它是从四周边界插值，在这种有笔触纹理的画面上会留下明显竖向拖影。

正确做法：**裁掉底部 110px，再放大回原尺寸**。

```
crop=1080:1920:0:0, crop=1080:1810:0:0, scale=1080:1920
```

等效放大 6%，肉眼几乎无感，且完全无伪影。

## 5. 时长对齐

旁白是**时长的主宰**，不要先定 5 秒再硬塞音频。

- 每段渲染时长 `S = 旁白时长 + 0.5s 留白`
- 素材只有 5.04s，用 `setpts=N*PTS` 慢放填满：`N = S / 5.04`（实测落在 1.58~2.02 之间，观感自然）
- 若 `N > 2.8`，慢放会显得拖沓，改为循环素材

留白 0.5s 与 `xfade=0.5` 相等，叠化正好吃掉留白，旁白不会互相压。

## 6. ASS 字幕

- **必须手动 `\N` 换行**：libass 对连续中文不会自动断行（`WrapStyle: 0` 也不行），
  只有写死断点才能保证换行位置可控
- 字体 `KaiTi`（Windows 自带 `simkai.ttf`），字号 46，白字 + 深色描边
- `PlayResX/Y` 必须等于输出分辨率，否则字幕缩放会错
- `MarginV 180`：字幕落在底部安全区内，不会被手机端的进度条遮住
- ASS 文件路径是**相对 ffmpeg 工作目录**解析的，脚本里要把 `cwd` 切到 `_tmp/`

## 7. ffmpeg 获取（Windows）

- 系统若无 ffmpeg，`pip install imageio-ffmpeg` 会附带静态 ffmpeg
- **注意**：该包在安装时会去 GitHub 拉二进制，国内常见卡死。可靠做法是
  从清华 PyPI 镜像**直接下载 wheel 文件再本地安装**：

  ```python
  # 1. 取 https://pypi.tuna.tsinghua.edu.cn/simple/imageio-ffmpeg/ 的索引
  # 2. 挑 win_amd64 的 wheel，urllib 下载到本地
  # 3. pip install --no-deps <本地 wheel>
  ```

- 剪映自带的 `ffmpeg.exe` 是精简版（无 libass、无 libx264），**不能**用于合成
- 需要 `libass`（字幕）、`libx264`、`xfade`、`acrossfade`；gyan essentials 构建全都带

## 8. 成本与止损

- 生图：约 5-10 积分/张，8 张 = 几十积分
- 生视频：约 50-100 积分/段，8 段 = 400-800 积分
- **先只做第 1 段**，确认风格、人物、运镜都对了再批量，否则 8 段全废
- 旁白（edge-tts）和成片合成（ffmpeg）都是免费且本地的

## 9. 已知边界

- 本流程只保证「同一支片子内部风格一致」，不保证跨次生成的风格可复现
- 人物形象靠提示词文字锚定，不是真正的角色一致性模型，跨段仍可能有细微漂移
- 叠化转场对硬切场景（如打斗）不合适，此类段落可改为直接硬切
