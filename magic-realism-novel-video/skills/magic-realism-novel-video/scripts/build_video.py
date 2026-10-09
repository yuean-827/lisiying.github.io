#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_video.py — 把「配图 + 旁白 + 动态素材」合成 9:16 成片

流程：
  1. 逐段渲染：素材慢放对齐旁白时长 → 裁除底部水印 → 烧录 ASS 字幕
  2. 片头 / 片尾：静态图 + 压暗 + 标题字幕
  3. xfade 叠化串联全部段落，acrossfade 串联音轨

依赖：pip install imageio-ffmpeg mutagen
      ffmpeg 需带 libass（字幕）、libx264、xfade

用法：
    python build_video.py --project project.json --out ./红楼梦
"""
import argparse
import json
import os
import subprocess
import sys

import imageio_ffmpeg
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

FF = imageio_ffmpeg.get_ffmpeg_exe()

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,KaiTi,46,&H00FFFFFF,&H000000FF,&HCC1A1208,&H80000000,0,0,0,0,100,100,1.5,0,1,2.2,1.2,2,70,70,180,134
Style: Big,KaiTi,104,&H00F5E6C8,&H000000FF,&HCC1A1208,&H80000000,0,0,0,0,100,100,4,0,1,3,2,5,60,60,60,134
Style: Mid,KaiTi,54,&H00F5E6C8,&H000000FF,&HCC1A1208,&H80000000,0,0,0,0,100,100,3,0,1,2.4,1.5,5,60,60,60,134
Style: Small,KaiTi,36,&H00DCCBA8,&H000000FF,&HCC1A1208,&H80000000,0,0,0,0,100,100,2,0,1,1.6,1,5,60,60,60,134

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

ENCF = ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", "-movflags", "+faststart"]


def ts(s):
    h = int(s // 3600)
    m = int(s % 3600 // 60)
    return f"{h:d}:{m:02d}:{s % 60:05.2f}"


def dur(path):
    return float(MP3(path).info.length) if path.endswith(".mp3") \
        else float(MP4(path).info.length)


def run(args, tmp, desc=""):
    p = subprocess.run(args, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=tmp)
    if p.returncode != 0:
        print(f"!! FAIL {desc}\nCMD: {' '.join(args)[:1200]}")
        print((p.stderr or "")[-2500:])
        sys.exit(1)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True, help="项目目录（含 图片916/ 音频/ 视频/）")
    ap.add_argument("--crf", type=int, default=19)
    a = ap.parse_args()

    with open(a.project, encoding="utf-8") as f:
        P = json.load(f)

    W, H = P["resolution"]
    FPS = P["fps"]
    XF = P["xfade"]
    TAIL = P["tail"]
    CUT = P["watermark_cut_px"]
    shots = P["shots"]

    IMG = os.path.join(a.out, "图片916")
    AUD = os.path.join(a.out, "音频")
    VID = os.path.join(a.out, "视频")
    TMP = os.path.join(a.out, "_tmp")
    OUTD = os.path.join(a.out, "成片")
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUTD, exist_ok=True)

    # ---------- 字幕 ----------
    for s in shots:
        n = s["no"]
        seg = dur(os.path.join(AUD, f"{n:02d}.mp3")) + TAIL
        body = (ASS_HEAD.format(W=W, H=H)
                + f"Dialogue: 0,{ts(0.15)},{ts(seg - 0.10)},Sub,,0,0,0,,{s['subtitle']}\n")
        with open(os.path.join(TMP, f"sub{n:02d}.ass"), "w", encoding="utf-8") as f:
            f.write(body)

    parts = []

    # ---------- 片头 ----------
    def card(name, png, lines, d):
        body = ASS_HEAD.format(W=W, H=H) + "\n".join(lines) + "\n"
        with open(os.path.join(TMP, f"{name}.ass"), "w", encoding="utf-8") as f:
            f.write(body)
        vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},eq=brightness=-0.28:saturation=0.72,fps={FPS},setsar=1,"
              f"subtitles={name}.ass,format=yuv420p[v]")
        outp = os.path.join(TMP, f"{name}.mp4")
        run([FF, "-y", "-loop", "1", "-t", f"{d}", "-i", os.path.join(IMG, png),
             "-f", "lavfi", "-t", f"{d}", "-i", "anullsrc=r=48000:cl=stereo",
             "-filter_complex",
             vf + ";[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a]",
             "-map", "[v]", "-map", "[a]", "-t", f"{d}", "-r", str(FPS)] + ENCF + [outp],
            TMP, name)
        return outp, d

    intro, idur = card("intro", "01_916.png", [
        f"Dialogue: 0,0:00:00.00,0:00:03.00,Small,,0,0,0,,{{\\fad(400,300)}}{P.get('opening_kicker','名著导读')}",
        f"Dialogue: 0,0:00:00.35,0:00:03.00,Big,,0,0,0,,{{\\fad(500,300)}}{P['book']}",
        f"Dialogue: 0,0:00:01.05,0:00:03.00,Mid,,0,0,0,,{{\\fad(600,300)\\fs42}}{P.get('subtitle','')}",
    ], 3.0)
    parts.append((intro, idur))

    # ---------- 八段正文 ----------
    for s in shots:
        n = s["no"]
        mp3 = os.path.join(AUD, f"{n:02d}.mp3")
        clip = os.path.join(VID, f"{n:02d}.mp4")
        S = dur(mp3) + TAIL
        factor = S / dur(clip)
        pre = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
               f"crop={W}:{H - CUT}:0:0,scale={W}:{H},setsar=1")
        if factor <= 2.8:
            pre = pre.replace(",setsar=1", f",setpts={factor:.5f}*PTS,fps={FPS},setsar=1")
        else:
            pre = pre.replace(",setsar=1", f",fps={FPS},setsar=1")
        vf = pre + f",subtitles=sub{n:02d}.ass,format=yuv420p[v]"
        af = (f"[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
              f"apad=pad_dur={S:.3f},atrim=0:{S:.3f},afade=t=in:st=0:d=0.25,"
              f"afade=t=out:st={S - 0.35:.3f}:d=0.35,asetpts=PTS-STARTPTS[a]")
        outp = os.path.join(TMP, f"part{n:02d}.mp4")
        run([FF, "-y", "-stream_loop", "-1", "-i", clip, "-i", mp3,
             "-filter_complex", f"{vf};{af}",
             "-map", "[v]", "-map", "[a]", "-t", f"{S:.3f}", "-r", str(FPS)]
            + ENCF + [outp], TMP, f"段{n:02d}")
        parts.append((outp, S))
        print(f"  -> part{n:02d}  {S:.2f}s  (slowmo x{factor:.2f})")

    # ---------- 片尾 ----------
    cl = P.get("closing_lines", [])
    outro, odur = card("outro", "08_916.png", [
        f"Dialogue: 0,0:00:00.20,0:00:03.20,Mid,,0,0,0,,{{\\fad(600,400)}}{cl[0] if cl else ''}",
        f"Dialogue: 0,0:00:01.10,0:00:03.20,Small,,0,0,0,,{{\\fad(700,400)}}{cl[1] if len(cl) > 1 else ''}",
    ], 3.2)
    parts.append((outro, odur))

    # ---------- 串联 ----------
    inputs = []
    for p, _ in parts:
        inputs += ["-i", p]
    fc = []
    for i in range(len(parts)):
        fc.append(f"[{i}:v]setsar=1,format=yuv420p[pv{i}]")
        fc.append(f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[pa{i}]")
    acc = parts[0][1]
    vp, ap_ = "pv0", "pa0"
    for i in range(1, len(parts)):
        off = acc - XF
        fc.append(f"[{vp}][pv{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[vx{i}]")
        fc.append(f"[{ap_}][pa{i}]acrossfade=d={XF}:c1=tri:c2=tri[ax{i}]")
        vp, ap_ = f"vx{i}", f"ax{i}"
        acc = off + parts[i][1]

    final = os.path.join(OUTD, f"{P['book']}_名著介绍_{P['size'].replace(':', 'x')}.mp4")
    args = ([FF, "-y"] + inputs + ["-filter_complex", ";".join(fc),
            "-map", f"[{vp}]", "-map", f"[{ap_}]", "-r", str(FPS),
            "-movflags", "+faststart",
            "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", final])
    run(args, TMP, "final")
    print(f"\n成片总时长 {acc - XF:.2f}s\nOUTPUT: {final}")


if __name__ == "__main__":
    main()
