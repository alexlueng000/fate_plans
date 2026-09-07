# -*- coding: utf-8 -*-
"""
make_cover.py — 「镜Sir在观察」公众号封面生成器
品牌：易凡文化 / 朱砂红 #B54434 / 暖米白 #F5F0E8 / 思源宋体
规格：1800x766（微信封面 900x383 的 2x 高清版，比例 2.35:1）

换文章封面时：只改下面的 CONFIG，然后重跑
    python make_cover.py
输出：cover-*.png（高清母版）+ cover-*.jpg（公众号上传用压缩版）
依赖：Pillow
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------- 品牌常量 ----------------
W, H = 1800, 766
RED   = (181, 68, 52)      # 朱砂红 #B54434
CREAM = (245, 240, 232)    # 暖米白 #F5F0E8
INK   = (46, 36, 40)       # 深墨
GRAY  = (140, 124, 114)    # 暖灰

FDIR = "C:/Windows/Fonts/"
SERIF_VF    = FDIR + "NotoSerifSC-VF.ttf"                          # 思源宋体（品牌字体）
SERIF_HEAVY = FDIR + "Source Han Serif SC Heavy (TrueType).ttf"    # 思源宋 Heavy（大字）
KAI         = FDIR + "simkai.ttf"                                  # 楷体（印章用字）

OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- 换文章改这里 ----------------
CONFIG = {
    "slug":        "04",                          # 文章编号，用于输出文件名防覆盖
    "chip":        "观察笔记",                    # 栏目名（顶部小标签）
    "hero":        "同一类人",                    # 品牌红版的大字（标题关键词）
    "sub":         "为什么你总被同一类人吸引",
    "title_lines": ["为什么你总被", "同一类人吸引"],
    "brand":       "镜Sir在观察 · fateinsight.site",
    "bgs": {                                        # AI 底图（不含文字），缺哪张跳过哪张
        "铜镜线描": "bg-mirror.png",
        "红线隐喻": "bg-thread.png",
        "水墨":     "bg-ink.png",
    },
}

# ---------------- 字体 ----------------
_printed = False

def serif(size, weights=("Bold", "SemiBold", "Medium")):
    """思源宋体可变字体，按名称挑字重，挑不到就退回默认"""
    global _printed
    f = ImageFont.truetype(SERIF_VF, size)
    try:
        names = [n.decode() if isinstance(n, bytes) else str(n)
                 for n in f.get_variation_names()]
        if not _printed:
            _printed = True
            print("NotoSerifSC 可变字重:", names)
        for w in weights:
            if w in names:
                f.set_variation_by_name(w)
                break
    except Exception as e:
        print("可变字体退化:", e)
    return f

def sans(size, bold=False):
    return ImageFont.truetype(FDIR + ("msyhbd.ttc" if bold else "msyh.ttc"), size)

# ---------------- 基础效果 ----------------
def vignette(img, color, strength):
    """底部压一层暗红渐晕，让大色块不像纯数字色"""
    ov = Image.new("RGB", img.size, color)
    m = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(m)
    for yy in range(img.height):
        md.line([(0, yy), (img.width, yy)],
                fill=int(strength * (yy / img.height) ** 1.6))
    return Image.composite(ov, img, m)

def grain(img, amount=5):
    """轻微纸张颗粒"""
    n = Image.effect_noise(img.size, 24).convert("RGB")
    return Image.blend(img, n, amount / 255.0)

def cover_fit(path):
    """任意尺寸底图 → 等比放大铺满画布 → 居中裁切"""
    bg = Image.open(path).convert("RGB")
    s = max(W / bg.width, H / bg.height)
    nw, nh = round(bg.width * s), round(bg.height * s)
    bg = bg.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - W) // 2, (nh - H) // 2
    return bg.crop((x, y, x + W, y + H))

# ---------------- 元件 ----------------
def chip(d, xy, text, style="solid", size=34):
    """栏目小标签：solid=红底白字（米白面板上）/ outline=米白描边（红底上）"""
    x, y = xy
    f = sans(size, bold=True)
    tw = d.textlength(text, font=f)
    h = size + 24
    if style == "solid":
        d.rounded_rectangle([x, y, x + tw + 44, y + h], radius=8, fill=RED)
        d.text((x + 22, y + 12), text, font=f, fill=CREAM)
    else:
        d.rounded_rectangle([x, y, x + tw + 44, y + h], radius=8,
                            outline=CREAM, width=2)
        d.text((x + 22, y + 12), text, font=f, fill=CREAM)

def seal(d, xy, size, char, bgc, fgc):
    """印章：圆角方块 + 单字"""
    x, y = xy
    d.rounded_rectangle([x, y, x + size, y + size], radius=size // 7, fill=bgc)
    f = ImageFont.truetype(KAI, int(size * 0.62))
    d.text((x + size / 2, y + size / 2), char, font=f, fill=fgc, anchor="mm")

# ---------------- 版式一：品牌标准版（红底白字）----------------
def cover_red(cfg):
    img = Image.new("RGB", (W, H), RED)
    img = vignette(img, (120, 38, 30), 46)
    img = grain(img, 5)
    d = ImageDraw.Draw(img, "RGBA")
    # 右侧铜镜几何装饰（同心圆）
    cx, cy = 1500, H // 2
    for r, wd, a in [(320, 5, 95), (250, 3, 60), (170, 2, 38)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CREAM + (a,), width=wd)
    # 顶部栏目标签（描边版）
    chip(d, (96, 84), cfg["chip"], style="outline")
    # 大字 + 印章
    fhero = ImageFont.truetype(SERIF_HEAVY, 250)
    d.text((96, 150), cfg["hero"], font=fhero, fill=CREAM,
           stroke_width=2, stroke_fill=CREAM)
    hw = d.textlength(cfg["hero"], font=fhero)
    seal(d, (96 + hw + 48, 296), 96, "观", CREAM, RED)
    # 副标 + 底部品牌
    d.text((100, 478), cfg["sub"], font=serif(46), fill=CREAM + (228,))
    d.text((96, 662), cfg["brand"], font=sans(30), fill=CREAM + (170,))
    return img

# ---------------- 版式二：AI 底图 + 米白文字面板 ----------------
def cover_image(bg_path, cfg):
    img = cover_fit(bg_path).convert("RGBA")
    x, y, w, h = 96, 160, 1150, 470
    # 面板投影
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [x, y + 16, x + w, y + h + 16], radius=36, fill=(30, 20, 20, 80))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img, "RGBA")
    # 米白面板 + 左侧朱砂红竖条
    d.rounded_rectangle([x, y, x + w, y + h], radius=36, fill=CREAM + (242,))
    d.rounded_rectangle([x, y, x + 14, y + h], radius=7, fill=RED + (255,))
    # 栏目标签（实底版）
    chip(d, (x + 56, y + 48), cfg["chip"], style="solid")
    # 标题两行（字号按最长行自适应，避免短标题太空 / 长标题溢出）
    lines = cfg["title_lines"]
    maxlen = max(len(l) for l in lines)
    fsize = max(86, min(108, int(860 / maxlen)))  # 上限收紧，给品牌行留足空间
    ft = serif(fsize, weights=("SemiBold", "Bold", "Medium"))
    ty = y + 150
    gap = int(fsize * 0.22)
    for line in lines:
        d.text((x + 56, ty), line, font=ft, fill=INK,
               stroke_width=1, stroke_fill=INK)
        ty += fsize + gap
    # 面板底部品牌
    d.text((x + 56, y + h - 58), cfg["brand"], font=sans(30), fill=GRAY)
    return img.convert("RGB")

# ---------------- 输出 ----------------
def save(img, name):
    png = os.path.join(OUTDIR, name + ".png")
    jpg = os.path.join(OUTDIR, name + ".jpg")
    img.save(png)
    img.convert("RGB").save(jpg, quality=88, optimize=True)
    print("OK  %-24s %sx%s  png %dKB / jpg %dKB" % (
        name, img.width, img.height,
        os.path.getsize(png) // 1024, os.path.getsize(jpg) // 1024))

def main():
    cfg = CONFIG
    slug = cfg.get("slug", "*")
    save(cover_red(cfg), "cover-%s-品牌红" % slug)
    for label, bg in cfg["bgs"].items():
        p = os.path.join(OUTDIR, bg)
        if os.path.exists(p):
            save(cover_image(p, cfg), "cover-%s-%s" % (slug, label))
        else:
            print("SKIP（缺底图）", bg)

if __name__ == "__main__":
    main()
