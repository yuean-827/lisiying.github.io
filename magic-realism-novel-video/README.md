# 名著介绍视频生成 Skill（魔幻现实主义版）

**《新媒体交互设计》作业 1**

给一个书名，自动产出一支 9:16 竖屏的名著介绍讲解视频。

- 在线预览：`index.html`（GitHub Pages）
- 技能包：`skills/magic-realism-novel-video/`
- 验证作品：《百年孤独：马孔多的一场大雨》（155.5 秒 / 1080×1920 / 9 段）

## 这个作业交的不是视频，是一套能力

视频只是这套能力的验证结果。真正的交付物是 `skills/magic-realism-novel-video/` 这个技能包——
它能把「给一个书名 → 出一支讲解视频」这件事稳定地重复做出来。

技能包含六个要素：

| 要素 | 内容 |
| --- | --- |
| 标题和描述 | 一句话说清用途 |
| When to Use | 什么场景触发、什么场景不该触发 |
| Capabilities | 能做什么、边界在哪 |
| Process | 八个阶段，每步都有明确产出文件 |
| Output Format | 交付物清单与路径 |
| Examples | 《百年孤独》与《老人与海》两个例子 |

## 目录结构

```
.
├── index.html                              作品展示页
├── assets/
│   ├── video/bainiangudu.mp4               成片（网页版 720×1280）
│   ├── poster.jpg                          封面
│   └── stills/01-09.jpg                    九段剧照
└── skills/magic-realism-novel-video/
    ├── SKILL.md                            主说明文件
    ├── reference.md                        参数细节与踩坑记录
    ├── scripts/
    │   ├── gen_script.py                   剧本 → script.md / 分镜.md
    │   ├── gen_tts.py                      旁白 → 音频/*.mp3
    │   └── build_video.py                  合成 → 成片/*.mp4
    └── templates/
        └── project.example.json            项目配置示例（百年孤独）
```

## 快速开始

```bash
pip install edge-tts mutagen pillow imageio-ffmpeg

# 1. 生成剧本
python skills/magic-realism-novel-video/scripts/gen_script.py \
  --project skills/magic-realism-novel-video/templates/project.example.json \
  --out ./百年孤独

# 2. 合成旁白
python skills/magic-realism-novel-video/scripts/gen_tts.py \
  --project skills/magic-realism-novel-video/templates/project.example.json \
  --out ./百年孤独

# 3. 生成配图与动态素材后，合成成片
python skills/magic-realism-novel-video/scripts/build_video.py \
  --project skills/magic-realism-novel-video/templates/project.example.json \
  --out ./百年孤独
```

在 Agent 里也可以直接触发：

```
/magic-realism-novel-video 百年孤独
```

## 制作流程

```
书名
 └─ ① 剧本      script.md / 分镜.md        ← 停下确认
     └─ ② 语音  音频/NN.mp3（决定全片时长）
         └─ ③ 配图  图片/NN.png（统一风格后缀）
             └─ ④ 去水印  图片916/
                 └─ ⑤ 生视频  视频/NN.mp4（先试 1 段再批量）
                     └─ ⑥ 合成  慢放对齐 + 烧字幕 + 叠化串联
                         └─ ⑦ 自检  抽帧九宫格 + 检查清单
```

## 技术栈

- **剧本**：大模型生成，输出结构化 `project.json`
- **旁白**：`edge-tts`（`zh-CN-YunjianNeural`，语速 −5%），免费
- **配图**：生成式图像（内置 ImageGen，或火山方舟豆包 Seedream）
- **动态素材**：图像转视频（内置 VideoGen，或火山方舟 Seedance）
- **合成**：`ffmpeg`（libass 字幕 + xfade 叠化 + libx264）

## 部署 GitHub Pages

仓库根目录已含 `.nojekyll`。把本目录全部内容推送到 GitHub 仓库，
在 Settings → Pages 选择 `main` 分支根目录即可上线。
