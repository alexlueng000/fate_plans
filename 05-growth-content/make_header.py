# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont

SRC = r"E:\claude_projects\chat\docs\05-growth-content\images\古风少年背影全身像_14_15岁_背对观众_半束发发髻系朱砂_2026-09-08T08-19-54.png"
OUT = r"E:\claude_projects\chat\docs\05-growth-content\images\yifan-xiaoshidi-header-final.png"

ZHU = (181, 68, 52)      # 朱砂红 #B54434
WHITE = (255, 255, 255)

img = Image.open(SRC).convert("RGB")
draw = ImageDraw.Draw(img)

def load_font(size, heavy=False):
    candidates = [
        r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf",
        r"C:\Windows\Fonts\NotoSerifSC-VF.ttf",
        r"C:\Windows\Fonts\STSONG.TTF",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def text_size(txt, f):
    bbox = draw.textbbox((0, 0), txt, font=f)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

# 主 Slogan（两行，朱砂红）
font_main = load_font(84, heavy=True)
line1 = "用东方视角"
line2 = "观察你的性格"
w1, h1 = text_size(line1, font_main)
w2, h2 = text_size(line2, font_main)

x = 100
y1 = 400
gap = 34
y2 = y1 + h1 + gap

draw.text((x, y1), line1, font=font_main, fill=ZHU)
draw.text((x, y2), line2, font=font_main, fill=ZHU)

# 品牌词印章（红底白字）
font_brand = load_font(42)
brand = "易凡小师弟"
bw, bh = text_size(brand, font_brand)
pad_x, pad_y = 30, 20
seal_w = bw + pad_x * 2
seal_h = bh + pad_y * 2
seal_x = x
seal_y = y2 + h2 + 56

draw.rounded_rectangle([seal_x, seal_y, seal_x + seal_w, seal_y + seal_h],
                       radius=16, fill=ZHU)
draw.text((seal_x + pad_x, seal_y + pad_y - 4), brand, font=font_brand, fill=WHITE)

img.save(OUT)
print("saved:", OUT)
print("size:", img.size)
print("text1:", w1, h1, "text2:", w2, h2, "seal:", seal_w, seal_h)
