"""Bilder für die Marktplatz-Listing-Vorschau: Hauptbilder je Variante (reines Weiß, Produkt ≈ 85 %),
Größenvergleich, Detail Staplertaschen, am Baum. Ausgabe: christbaumpoller/img/listing/*.webp (1500 × 1500)."""
import sys, os
sys.path.insert(0, "/home/claude/cbp/render")
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import engine

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/christbaumpoller/img/listing"
os.makedirs(OUT, exist_ok=True)
S = 1500
F = "/usr/share/fonts/truetype/google-fonts/ofl/sourcesans3/SourceSans3[wght].ttf"
KEYS = [f"{f}-{o}{s}" for f in ("gold", "silber", "rot") for o in ("glanz", "matt") for s in ("", "-schnee")]


def font(px, w=600):
    f = ImageFont.truetype(F, px)
    try:
        f.set_variation_by_axes([w])
    except Exception:
        pass
    return f


def on_white(spr, fill=0.85, shadow=True):
    bb = spr.getbbox()
    spr = spr.crop(bb)
    k = min(S * fill / spr.width, S * fill / spr.height)
    spr = spr.resize((int(spr.width * k), int(spr.height * k)), Image.LANCZOS)
    im = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    x, y = (S - spr.width) // 2, (S - spr.height) // 2
    if shadow:
        sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([x + spr.width * 0.12, y + spr.height * 0.93, x + spr.width * 0.92, y + spr.height * 1.02], fill=(0, 0, 0, 60))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(25)))
    im.alpha_composite(spr, (x, y))
    return im


# 1) Hauptbilder je Variante (mit Öse und Satinschlaufe)
for v in KEYS:
    spr = engine.block(v, size=1400, seed=3, hang=True)
    on_white(spr, 0.86).convert("RGB").save(f"{OUT}/main-{v}.webp", quality=88, method=6)

# 2) Größenvergleich S / M / L maßstäblich (50 / 70 / 90 mm)
im = Image.new("RGBA", (S, S), (255, 255, 255, 255))
d = ImageDraw.Draw(im)
base_y = 1050
sprs = [(g, L, engine.block("gold-glanz", size=int(L * 4.2 / 0.65), seed=2, hang=False)) for g, L in (("S", 50), ("M", 70), ("L", 90))]
gap = 60
x = (S - sum(sp.width for _, _, sp in sprs) - 2 * gap) // 2
for g, L, spr in sprs:
    w = L * 4.2
    im.alpha_composite(spr, (x, base_y - spr.height))
    d.text((x + spr.width * 0.45, base_y + 40), f"{g}", font=font(64, 800), fill=(30, 30, 30), anchor="mt")
    d.text((x + spr.width * 0.45, base_y + 115), f"{L} × {L // 2} mm", font=font(40, 500), fill=(90, 90, 90), anchor="mt")
    x += spr.width + gap
d.text((S // 2, 150), "Drei Größen für jeden Ast", font=font(70, 700), fill=(30, 30, 30), anchor="mm")
d.line([(110, base_y + 5), (S - 110, base_y + 5)], fill=(210, 210, 210), width=3)
im.convert("RGB").save(f"{OUT}/groessen.webp", quality=88, method=6)

# 3) Detail Staplertaschen
spr = engine.block("rot-glanz", size=2600, seed=4, hang=False)
spr = spr.crop(spr.getbbox())
crop = spr.crop((0, int(spr.height * 0.42), int(spr.width * 0.80), spr.height))
im = Image.new("RGBA", (S, S), (255, 255, 255, 255))
k = S * 0.9 / crop.width
crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
im.alpha_composite(crop, ((S - crop.width) // 2, 330))
d = ImageDraw.Draw(im)
d.text((S // 2, 150), "Mit echten Staplertaschen", font=font(72, 700), fill=(30, 30, 30), anchor="mm")
d.text((S // 2, 235), "Das Detail, an dem man ihn erkennt", font=font(44, 500), fill=(90, 90, 90), anchor="mm")
im.convert("RGB").save(f"{OUT}/staplertaschen.webp", quality=88, method=6)

# 4) Am Baum: leerer Baum + vier Poller
tree = Image.open("/home/claude/cbp/render/tree.jpg").convert("RGBA")
tw, th = tree.size
pos = [("gold-glanz", 0.36, 0.42, 150), ("rot-matt-schnee", 0.62, 0.55, 140), ("silber-glanz", 0.30, 0.68, 160), ("gold-matt-schnee", 0.66, 0.78, 165)]
for v, fx, fy, sz in pos:
    spr = engine.block(v, size=sz, seed=5, hang=True)
    tree.alpha_composite(spr, (int(tw * fx - spr.width / 2), int(th * fy - spr.height * 0.25)))
bg = Image.new("RGBA", (S, S), (13, 21, 48, 255))
k = S / th
tree = tree.resize((int(tw * k), S), Image.LANCZOS)
bg.alpha_composite(tree, ((S - tree.width) // 2, 0))
bg.convert("RGB").save(f"{OUT}/am-baum.webp", quality=86, method=6)

# 5) Verpackungsbilder übernehmen (quadratisch beschnitten)
for src, dst in (("/home/claude/cbp/pack/out/mock-einzel.jpg", "verpackung-einzel.webp"), ("/home/claude/cbp/pack/out/mock-zehner-offen.jpg", "verpackung-10er.webp")):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2 - (0 if "einzel" in src else -60), (w - s) // 2 + s, (h - s) // 2 + s - (0 if "einzel" in src else -60)))
    im.resize((S, S), Image.LANCZOS).save(f"{OUT}/{dst}", quality=86, method=6)
print("ok", len(os.listdir(OUT)), "Bilder")
