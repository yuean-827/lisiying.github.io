#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_tts.py — 由 project.json 逐段合成中文旁白，输出 音频/NN.mp3 与 音频/durations.json

依赖：pip install edge-tts mutagen

用法：
    python gen_tts.py --project project.json --out ./红楼梦 --voice zh-CN-YunjianNeural
"""
import argparse
import asyncio
import json
import os

import edge_tts
from mutagen.mp3 import MP3


async def synth(text, path, voice, rate):
    await edge_tts.Communicate(text, voice, rate=rate).save(path)


async def main_async(a):
    with open(a.project, encoding="utf-8") as f:
        p = json.load(f)

    aud = os.path.join(a.out, "音频")
    os.makedirs(aud, exist_ok=True)

    durs = {}
    for s in p["shots"]:
        n = s["no"]
        out = os.path.join(aud, f"{n:02d}.mp3")
        await synth(s["narration"], out, a.voice, a.rate)
        d = round(MP3(out).info.length, 3)
        durs[f"{n:02d}"] = d
        print(f"  {n:02d}.mp3  {d:6.2f}s")

    total = round(sum(durs.values()), 2)
    with open(os.path.join(aud, "durations.json"), "w", encoding="utf-8") as f:
        json.dump({"durations": durs, "total": total,
                   "tail": p.get("tail", 0.5),
                   "segments": {k: round(v + p.get("tail", 0.5), 3)
                                for k, v in durs.items()}},
                  f, ensure_ascii=False, indent=2)
    print(f"\n旁白总长 {total}s，成片预计 {round(total + 8 * p.get('tail', 0.5), 2)}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="zh-CN-YunjianNeural")
    ap.add_argument("--rate", default="-5%")
    a = ap.parse_args()
    asyncio.run(main_async(a))


if __name__ == "__main__":
    main()
