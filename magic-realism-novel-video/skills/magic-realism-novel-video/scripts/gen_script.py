#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_script.py — 由 project.json 生成 script.md（剧本）与 分镜.md（分镜表）

用法：
    python gen_script.py --project project.json --out ./红楼梦
"""
import argparse
import json
import os


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write_script(p, out):
    L = []
    L.append(f"# {p['book']} —— 名著介绍视频剧本\n")
    L.append(f"> 书名：{p['book']}")
    L.append(f"> 画幅：{p['size']} 竖屏")
    L.append(f"> 统一风格：{p['style_suffix']}\n")
    L.append("---\n")
    L.append("## 标题\n")
    L.append(f"**《{p['title']}》**\n")
    L.append("---\n")
    L.append("## 八段情节字幕\n")
    L.append("| 序号 | 回目/阶段 | 情节 |")
    L.append("| --- | --- | --- |")
    for s in p["shots"]:
        L.append(f"| {s['no']:02d} | 【{s['act']}】 | {s['plot']} |")
    L.append("\n---\n")
    L.append("## 固定人物形象（每一段提示词都要用到，保证前后一致）\n")
    for c in p.get("characters", []):
        L.append(f"- **{c.split('：')[0]}**：{c.split('：', 1)[1]}")
    L.append("\n---\n")
    L.append("## 八段画面描述（生图提示词）\n")
    L.append("每段末尾的**风格后缀完全一致**，这是保证全片不串味的关键。\n")
    for s in p["shots"]:
        L.append(f"**{s['no']:02d}**")
        L.append(f"{s['visual']}。{p['style_suffix']}。\n")
    L.append("---\n")
    L.append("## 旁白文案（配音用，与字幕同源，略作口语化）\n")
    for s in p["shots"]:
        L.append(f"{s['no']}. {s['narration']}")
    L.append("")
    return "\n".join(L)


def write_shots(p, out):
    L = []
    L.append(f"# {p['book']} · 分镜表\n")
    L.append(f"> 画幅 {p['size']} 竖屏 ｜ {len(p['shots'])} 段 ｜ "
             f"转场：段与段之间统一叠化 {p['xfade']}s\n")
    L.append("---\n")
    L.append("## 分镜总表\n")
    L.append("| # | 字幕 | 画面要点 | 运镜 / 动态提示（生视频用） |")
    L.append("| --- | --- | --- | --- |")
    for s in p["shots"]:
        L.append(f"| {s['no']:02d} | {s['subtitle'].replace(chr(92) + 'N', '')} | "
                 f"{s['visual'].split('，')[0]} | {s['motion']} |")
    L.append("\n---\n")
    L.append("## 转场与包装\n")
    L.append("| 位置 | 处理 |")
    L.append("| --- | --- |")
    L.append(f"| 每段之间 | 叠化 {p['xfade']} 秒 |")
    L.append("| 字幕 | 底部居中，楷体，带描边保证可读 |")
    L.append(f"| 片头 | 书名《{p['book']}》+ 副标题，停 3 秒 |")
    L.append(f"| 片尾 | 「{p['closing_lines'][0]}」，停 3 秒 |")
    L.append(f"| 画面比例 | 全片 {p['size']} 竖屏，图片与视频素材统一 |")
    L.append("\n---\n")
    L.append("## 检查清单（成片前必看）\n")
    for c in [
        "8 张图的画风是否完全一致（不能一半工笔一半写实）",
        "主要人物在跨段落中的形象是否对得上",
        "8 段画面描述的风格后缀是否逐字相同",
        "字幕文字与旁白是否一致",
        "旁白总时长是否与画面总时长对齐",
        "素材自带水印是否已清除",
        "有没有漏掉转场与片头片尾",
    ]:
        L.append(f"- [ ] {c}")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    p = load(a.project)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "script.md"), "w", encoding="utf-8") as f:
        f.write(write_script(p, a.out))
    with open(os.path.join(a.out, "分镜.md"), "w", encoding="utf-8") as f:
        f.write(write_shots(p, a.out))
    print(f"OK  {a.out}/script.md  {a.out}/分镜.md")


if __name__ == "__main__":
    main()
