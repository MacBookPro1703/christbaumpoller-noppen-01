"""Christbaumpoller – Zeichen-Engine (PIL). Anhänger, Baum, Markt, Schnee, Text."""
import math, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

F_BLACK = "/usr/share/fonts/truetype/google-fonts/ofl/archivoblack/ArchivoBlack-Regular.ttf"
F_SANS = "/usr/share/fonts/truetype/google-fonts/ofl/sourcesans3/SourceSans3[wght].ttf"
F_SERIF_I = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
F_SERIF = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"

BG = (27, 30, 34)
BRONZE = (176, 141, 87)
CREAM = (232, 230, 225)

VARIANTS = {
    "klassik":   dict(name="Klassik Rot", base=(178, 30, 40)),
    "schnee":    dict(name="Schneeweiß", base=(236, 233, 226)),
    "tanne":     dict(name="Tannengrün", base=(30, 92, 58)),
    "gelb":      dict(name="Stadtgelb", base=(240, 196, 30)),
    "beton":     dict(name="Echtbeton", base=(150, 150, 146), concrete=True),
    "bescherung": dict(name="Bescherung", base=(238, 235, 228), ribbon=(185, 28, 38)),
}
FARBEN = {"gold": ("Gold", (200, 160, 74)), "silber": ("Silber", (178, 182, 190)), "rot": ("Rot", (182, 28, 38))}
for fk, (fn, fc) in FARBEN.items():
    for fin in ("glanz", "matt"):
        for sn in (False, True):
            key = f"{fk}-{fin}" + ("-schnee" if sn else "")
            VARIANTS[key] = dict(name=f"{fn} {'glänzend' if fin == 'glanz' else 'matt'}" + (" mit Schnee" if sn else ""),
                                 base=fc if fin == "glanz" else tuple(int(c * 0.9 + 12) for c in fc),
                                 metal=(fin == "glanz"), matt=(fin == "matt"), glitter=(fin == "glanz" and fk == "gold"),
                                 snow=sn, text="#WIRSCHAFFENDAS")
VARIANTS["gold"] = VARIANTS["gold-glanz"]


def font(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def shade(c, k):
    if k >= 1:
        return tuple(int(v + (255 - v) * (k - 1)) for v in c)
    return tuple(int(v * k) for v in c)


def ornament(variant="klassik", size=420, string_len=0.55, seed=1, hang=True):
    """Gibt RGBA-Sprite zurück; Pivot (Aufhängepunkt) = (w/2, 0). Der Sprite ist so breit/hoch,
    dass beim Rotieren um den Pivot nichts abgeschnitten wird (Höhe*2)."""
    v = VARIANTS[variant]
    S = 4  # Supersampling
    W = 1000
    x0, y0 = 120, 0
    BW, BH = 640, 300          # Front
    ox, oy = 150, -120         # Tiefe
    top_y = 420                 # y der Front-Oberkante
    y0 = top_y
    canvas_h = top_y + BH + 40
    im = Image.new("RGBA", (W, canvas_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = v["base"]
    top_c, front_c, side_c = shade(base, 1.18), base, shade(base, 0.68)
    # Körper
    d.polygon([(x0, y0), (x0 + BW, y0), (x0 + BW + ox, y0 + oy), (x0 + ox, y0 + oy)], fill=top_c)
    d.polygon([(x0 + BW, y0), (x0 + BW + ox, y0 + oy), (x0 + BW + ox, y0 + BH + oy), (x0 + BW, y0 + BH)], fill=side_c)
    d.rectangle([x0, y0, x0 + BW, y0 + BH], fill=front_c)
    # Front-Verlauf (Glanz oben, dunkler unten)
    grad = Image.new("L", (1, BH))
    for yy in range(BH):
        grad.putpixel((0, yy), int(60 * (yy / BH) ** 1.3))
    grad = grad.resize((BW, BH))
    dark = Image.new("RGBA", (BW, BH), (0, 0, 0, 255)); dark.putalpha(grad)
    im.alpha_composite(dark, (x0, y0))
    if v.get("metal"):
        band = np.zeros((BH, BW), np.float32)
        yy, xx = np.mgrid[0:BH, 0:BW]
        u = (xx / BW) * 0.8 + (yy / BH) * 0.35
        band = np.exp(-((u - 0.38) / 0.09) ** 2) * 0.75 + np.exp(-((u - 0.72) / 0.04) ** 2) * 0.35
        sheen = Image.new("RGBA", (BW, BH), (255, 240, 200, 255))
        sheen.putalpha(Image.fromarray((band * 255).astype(np.uint8)))
        im.alpha_composite(sheen, (x0, y0))
        dk = Image.new("RGBA", (BW, BH), (60, 40, 10, 255))
        dk.putalpha(Image.fromarray((np.clip(0.5 - band, 0, 1) * 120 * (yy / BH)).astype(np.uint8)))
        im.alpha_composite(dk, (x0, y0))
    if v.get("text"):
        tf = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/ofl/archivoblack/ArchivoBlack-Regular.ttf", 66)
        tf = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/ofl/archivoblack/ArchivoBlack-Regular.ttf", 90)
        tl = Image.new("RGBA", (BW * 3, BH), (0, 0, 0, 0))
        td = ImageDraw.Draw(tl)
        tx, ty = BW * 1.5, BH / 2
        hi = (255, 255, 255, 150) if v.get("metal") else shade(base, 1.35) + (170,)
        lo = shade(base, 0.42) + (255,)
        td.text((tx + 3, ty + 4), v["text"], font=tf, fill=hi, anchor="mm")
        td.text((tx, ty), v["text"], font=tf, fill=lo, anchor="mm")
        tl = tl.crop(tl.getbbox())
        k = BW * 0.86 / tl.width
        tl = tl.resize((int(tl.width * k), int(tl.height * k)), Image.LANCZOS)
        im.alpha_composite(tl, (int(x0 + (BW - tl.width) / 2), int(y0 + BH * 0.55 - tl.height / 2)))
    # Fase / Kantenlicht
    d.line([(x0, y0), (x0 + BW, y0)], fill=shade(base, 1.45), width=6)
    d.line([(x0 + BW, y0), (x0 + BW + ox, y0 + oy)], fill=shade(base, 1.3), width=4)
    d.line([(x0 + BW, y0), (x0 + BW, y0 + BH)], fill=shade(base, 0.85), width=4)
    # Schleifenband (Bescherung)
    rib = v.get("ribbon")
    if rib:
        rw = 70
        cx = x0 + BW / 2
        d.rectangle([cx - rw / 2, y0, cx + rw / 2, y0 + BH], fill=rib)
        d.polygon([(cx - rw / 2, y0), (cx + rw / 2, y0), (cx + rw / 2 + ox, y0 + oy), (cx - rw / 2 + ox, y0 + oy)], fill=shade(rib, 1.15))
        # Querband auf der Seite
        sy = y0 + BH * 0.45
        d.polygon([(x0 + BW, sy - rw / 2), (x0 + BW + ox, sy - rw / 2 + oy), (x0 + BW + ox, sy + rw / 2 + oy), (x0 + BW, sy + rw / 2)], fill=shade(rib, 0.7))
        d.rectangle([x0, sy - rw / 2, x0 + BW, sy + rw / 2], fill=rib)
        d.line([(x0, sy - rw / 2), (x0 + BW, sy - rw / 2)], fill=shade(rib, 1.3), width=4)
    # Noppen: hintere Reihe zuerst
    r, ry, h = 54, 24, 46
    for j in (1, 0):
        for i in range(4):
            fx = (i + 0.5) / 4
            fz = (j + 0.5) / 2
            cx = x0 + fx * BW + fz * ox
            cy = y0 + fz * oy
            d.ellipse([cx - r, cy - ry, cx + r, cy + ry], fill=side_c)
            d.rectangle([cx - r, cy - h, cx + r, cy], fill=front_c)
            # zylindrische Schattierung
            for k in range(8):
                xx = cx - r + (2 * r) * (k / 8)
                d.rectangle([xx, cy - h, xx + 2 * r / 8 + 1, cy], fill=shade(base, 1.08 - 0.06 * k))
            d.ellipse([cx - r, cy - h - ry, cx + r, cy - h + ry], fill=shade(base, 1.25))
            if not v.get("matt"):
                d.ellipse([cx - r * .55, cy - h - ry * .6, cx - r * .05, cy - h - ry * .1], fill=shade(base, 1.6 if v.get("metal") else 1.45))
    if v.get("snow"):
        sw = (250, 252, 255)
        rs = random.Random(seed)
        # Decke auf der Oberseite, leicht über die Vorderkante
        top_pts = [(x0 - 6, y0 + 4), (x0 + ox - 6, y0 + oy - 4), (x0 + BW + ox + 6, y0 + oy - 4), (x0 + BW + 8, y0 + 4)]
        d.polygon(top_pts, fill=(236, 240, 248))
        # Tropfnasen an der Vorderkante
        xx = x0 - 6
        pts = [(x0 - 6, y0 - 4)]
        while xx < x0 + BW + 8:
            step = rs.randint(40, 80)
            dep = rs.randint(10, 46)
            pts += [(xx + step * 0.3, y0 + dep), (xx + step * 0.6, y0 + dep * 0.7), (xx + step, y0 + rs.randint(4, 14))]
            xx += step
        pts += [(x0 + BW + 8, y0 - 4)]
        d.polygon(pts, fill=sw)
        # Hauben auf den Noppen
        for j in (1, 0):
            for i in range(4):
                fx, fz = (i + 0.5) / 4, (j + 0.5) / 2
                cx, cy = x0 + fx * BW + fz * ox, y0 + fz * oy
                d.ellipse([cx - r - 6, cy - h - ry - 18, cx + r + 6, cy - h + ry + 4], fill=sw)
                d.ellipse([cx - r * 0.6, cy - h - ry - 26, cx + r * 0.5, cy - h - ry + 2], fill=sw)
                d.ellipse([cx - r - 6, cy - h + ry - 10, cx + r + 6, cy - h + ry + 6], fill=(214, 222, 236))
        # Seitenkante
        d.polygon([(x0 + BW + 6, y0 - 2), (x0 + BW + ox + 6, y0 + oy - 4), (x0 + BW + ox + 4, y0 + oy + 22), (x0 + BW + 4, y0 + 30)], fill=(222, 228, 240))
    # Schleife oben (Bescherung)
    if rib:
        bx, by = x0 + BW / 2 + ox * 0.5, y0 + oy * 0.5 - 70
        for sgn in (-1, 1):
            d.ellipse([bx + sgn * 95 - 70, by - 50, bx + sgn * 95 + 70, by + 45], fill=rib, outline=shade(rib, 0.7), width=6)
            d.ellipse([bx + sgn * 95 - 35, by - 20, bx + sgn * 95 + 35, by + 20], fill=shade(rib, 0.6))
        d.polygon([(bx - 20, by + 10), (bx - 90, by + 120), (bx - 50, by + 120), (bx - 5, by + 30)], fill=shade(rib, 0.9))
        d.polygon([(bx + 20, by + 10), (bx + 90, by + 120), (bx + 50, by + 120), (bx + 5, by + 30)], fill=shade(rib, 0.8))
        d.ellipse([bx - 32, by - 30, bx + 32, by + 30], fill=shade(rib, 1.15))
    # Textur Beton / Glitzer
    rng = np.random.default_rng(seed)
    a = np.array(im)
    mask = a[..., 3] > 0
    if v.get("concrete"):
        n = rng.normal(0, 12, a.shape[:2])
        n = n + (rng.random(a.shape[:2]) < 0.004) * -60  # Lunker
        for c in range(3):
            a[..., c] = np.clip(a[..., c] + n * mask, 0, 255)
    if v.get("snow"):
        wm = (a[..., 0] > 230) & (a[..., 2] > 240) & mask
        sp = (rng.random(a.shape[:2]) < 0.01) & wm
        a[sp, :3] = (190, 215, 255)
    if v.get("matt"):
        n = rng.normal(0, 5, a.shape[:2])
        for c in range(3):
            a[..., c] = np.clip(a[..., c].astype(int) + n * mask, 0, 255)
    if v.get("glitter"):
        sp = (rng.random(a.shape[:2]) < 0.012) & mask
        a[sp, :3] = np.clip(a[sp, :3].astype(int) + 90, 0, 255)
        n = rng.normal(0, 7, a.shape[:2])
        for c in range(3):
            a[..., c] = np.clip(a[..., c] + n * mask, 0, 255)
    im = Image.fromarray(a.astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Aufhänger: Messingkappe + Öse in der Mitte der Oberseite
    hx, hy = x0 + BW / 2 + ox * 0.5, y0 + oy * 0.5 - nh - 40
    if not hang:
        pass
    elif not rib:
        d.rectangle([hx - 28, hy - 10, hx + 28, hy + 30], fill=(150, 118, 62))
        d.rectangle([hx - 28, hy - 10, hx - 8, hy + 30], fill=(205, 172, 110))
        d.ellipse([hx - 28, hy - 22, hx + 28, hy + 2], fill=(214, 182, 120))
        ring_y = hy - 22
    else:
        ring_y = hy - 60
    if not hang:
        ring_y = hy - 60
    if hang:
        d.ellipse([hx - 26, ring_y - 58, hx + 26, ring_y + 4], outline=(214, 182, 120), width=10)
    # Faden
    pivot_y = 0
    full = Image.new("RGBA", (W, canvas_h), (0, 0, 0, 0))
    # String vom oberen Rand zur Öse
    sd = ImageDraw.Draw(full)
    if hang:
        sd.line([(hx, 0), (hx, ring_y - 54)], fill=(215, 190, 140, 255), width=7)
    full.alpha_composite(im)
    # Zuschneiden: Pivot horizontal mittig setzen
    left = int(hx - W / 2)
    out = Image.new("RGBA", (W, canvas_h), (0, 0, 0, 0))
    out.alpha_composite(full, (-left, 0))
    # String-Länge: obere Leerfläche skalieren
    scale = size / W
    out = out.resize((size, int(canvas_h * scale)), Image.LANCZOS)
    # weicher Schatten/Glanz nicht nötig – Sprite fertig
    return out


def pad_for_rotation(sprite):
    """Pivot oben mittig → Sprite auf Quadrat 2*h legen, Pivot in die Mitte."""
    w, h = sprite.size
    s = max(w, h) * 2
    c = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    c.alpha_composite(sprite, (s // 2 - w // 2, s // 2))
    return c


def place_swing(frame, padded, px, py, angle):
    rot = padded.rotate(angle, resample=Image.BICUBIC, center=(padded.width / 2, padded.height / 2))
    frame.alpha_composite(rot, (int(px - padded.width / 2), int(py - padded.height / 2)))


def glow_sprite(radius, color, core=0.25):
    s = radius * 2
    y, x = np.mgrid[0:s, 0:s]
    dd = np.sqrt((x - radius) ** 2 + (y - radius) ** 2) / radius
    a = np.clip(1 - dd, 0, 1) ** 2.2
    a = a + np.clip(1 - dd / core, 0, 1) * 0.8
    a = np.clip(a, 0, 1)
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr)


def vgrad(W, H, top, bottom):
    t = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - t) + np.array(bottom)[None, None, :] * t)
    arr = np.repeat(arr, W, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB").convert("RGBA")


def tree(W, H, seed=3, scale=1.0):
    """Tannenbaum als RGBA in Größe W×H, mit Lichterpositionen."""
    rng = random.Random(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = W / 2
    tiers = 7
    lights = []
    trunk_w = W * 0.07
    d.rectangle([cx - trunk_w / 2, H * 0.9, cx + trunk_w / 2, H], fill=(62, 40, 26))
    for t in range(tiers):
        f = t / (tiers - 1)
        top = H * (0.02 + 0.115 * t)
        bot = top + H * 0.2
        half = W * (0.1 + 0.4 * f)
        col = (18 + int(10 * f), 58 + int(20 * f), 36 + int(8 * f))
        pts = [(cx, top)]
        n = 9
        for k in range(n + 1):
            x = cx + half - (2 * half) * k / n
            y = bot + (rng.random() * 0.03 - 0.01) * H - (k % 2) * H * 0.025
            pts.append((x, y))
        pts.append((cx, top))
        d.polygon([(cx, top)] + pts[1:-1], fill=col)
        # Unterseite dunkler
        d.polygon([(cx - half * 0.98, bot - H * 0.012), (cx + half * 0.98, bot - H * 0.012), (cx + half * 0.7, bot - H * 0.05), (cx - half * 0.7, bot - H * 0.05)], fill=(16, 50, 32))
        for _ in range(9 + t * 3):
            yy = top + (bot - top) * (0.35 + 0.6 * rng.random())
            span = half * (yy - top) / (bot - top) * 0.92
            xx = cx + (rng.random() * 2 - 1) * span
            lights.append((xx, yy, rng.random() * 6.28, rng.choice([(255, 196, 110), (255, 220, 160), (255, 170, 90)])))
    # Nadeltextur
    a = np.array(im).astype(np.int16)
    m = a[..., 3] > 0
    n = np.random.default_rng(seed).normal(0, 9, a.shape[:2])
    for c in range(3):
        a[..., c] = np.clip(a[..., c] + n * m, 0, 255)
    xs = np.linspace(-1, 1, W)[None, :]
    sh = 1 - 0.45 * np.clip(np.abs(xs + 0.25), 0, 1) ** 1.5
    for c in range(3):
        a[..., c] = (a[..., c] * sh).astype(np.int16)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # Stern
    sd = ImageDraw.Draw(im)
    R = W * 0.05
    sx, sy = cx, H * 0.03
    star = []
    for k in range(10):
        rr = R if k % 2 == 0 else R * 0.42
        an = -math.pi / 2 + k * math.pi / 5
        star.append((sx + rr * math.cos(an), sy + rr * math.sin(an)))
    sd.polygon(star, fill=(222, 186, 112))
    return im, lights, (sx, sy)


class Snow:
    def __init__(self, W, H, n=220, seed=5, big=1.0):
        r = random.Random(seed)
        self.W, self.H = W, H
        self.p = [[r.random() * W, r.random() * H, (0.6 + r.random() * 2.6) * big * min(W, H) / 1080,
                   0.4 + r.random() * 1.2, r.random() * 6.28] for _ in range(n)]

    def draw(self, frame, t):
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for x, y, s, sp, ph in self.p:
            yy = (y + t * 60 * sp * self.H / 1080) % (self.H + 20) - 10
            xx = x + math.sin(t * 0.8 + ph) * 18 * sp
            a = int(120 + 120 * min(1, s / 3))
            d.ellipse([xx - s, yy - s, xx + s, yy + s], fill=(255, 255, 255, a))
        frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.6)))


def text_layer(size, lines, center, alpha=1.0, align="center", shadow=True):
    """lines: [(text, fontobj, color)] untereinander, zentriert um center."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    heights = []
    for txt, f, col in lines:
        bb = d.textbbox((0, 0), txt, font=f)
        heights.append((bb[2] - bb[0], bb[3] - bb[1], bb[1]))
    gap = int(lines[0][1].size * 0.35)
    total = sum(h for _, h, _ in heights) + gap * (len(lines) - 1)
    y = center[1] - total / 2
    for (txt, f, col), (w, h, off) in zip(lines, heights):
        x = center[0] - w / 2 if align == "center" else center[0]
        d.text((x, y - off), txt, font=f, fill=col + (255,))
        y += h + gap
    if shadow:
        sh = Image.new("RGBA", size, (0, 0, 0, 0))
        a = layer.split()[3].filter(ImageFilter.GaussianBlur(max(6, lines[0][1].size // 6)))
        sh.putalpha(a.point(lambda v: int(v * 0.85)))
        sh = Image.composite(sh, sh, sh)
        base = Image.new("RGBA", size, (0, 0, 0, 0))
        base.alpha_composite(sh)
        base.alpha_composite(layer)
        layer = base
    if alpha < 1:
        layer.putalpha(layer.split()[3].point(lambda v: int(v * max(0, alpha))))
    return layer


def fade(t, a, b, inn=0.6, out=0.6):
    if t < a or t > b:
        return 0.0
    return max(0.0, min(1.0, (t - a) / inn, (b - t) / out))


def ease(x):
    x = max(0, min(1, x))
    return x * x * (3 - 2 * x)


# ======================================================================
# Sperrblock-Form nach Jörgs Foto (Dortmund, 20.11.2026): glatter Quader,
# Staplertasche unten an der Längsseite, zwei Transportanker oben, Pinselschrift.
# ======================================================================
F_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "caveat-brush-latin-400-normal.woff")

def _variants_block():
    V = {}
    farben = {"gold": ("Gold", (206, 164, 70)), "silber": ("Silber", (184, 188, 196)), "rot": ("Rot", (184, 30, 40))}
    for fk, (fn, fc) in farben.items():
        for fin in ("glanz", "matt"):
            for sn in (False, True):
                key = f"{fk}-{fin}" + ("-schnee" if sn else "")
                V[key] = dict(name=f"{fn} {'glänzend' if fin == 'glanz' else 'matt'}" + (" · mit Schnee" if sn else ""),
                              base=fc if fin == "glanz" else tuple(int(c * 0.88 + 14) for c in fc),
                              metal=(fin == "glanz"), matt=(fin == "matt"), glitter=(fin == "glanz" and fk == "gold"),
                              snow=sn, text="#wirschaffendas",
                              textcol=(250, 244, 232) if fk == "rot" else (178, 26, 34))
    V["gelb"] = dict(name="Stadtgelb", base=(232, 184, 30), matt=True, weathered=True)
    V["gelb-text"] = dict(name="Stadtgelb", base=(232, 184, 30), matt=True, weathered=True, text="#wirschaffendas", textcol=(178, 26, 34))
    V["weiss"] = dict(name="Weiß", base=(232, 230, 224), matt=True, weathered=True)
    V["rot"] = dict(name="Rot", base=(184, 30, 40), matt=True, weathered=True)
    V["bescherung"] = dict(name="Bescherung", base=(236, 233, 226), matt=True, ribbon=(185, 28, 38))
    return V

BLOCK = _variants_block()


FORM = os.environ.get("CBP_FORM", "noppen")   # "glatt" (Original) | "noppen" (2 x 4 flache Noppen wie Beton-Noppenblock), 21.11.2026


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def _noppen(d, x0, y0, BW, BH, ox, oy, base, metal, snow):
    """2 x 4 flache Kegelstumpf-Noppen auf die Oberseite (Schrägbild). Maße wie Blender-Modell M: L70 D32 H35."""
    L_, D_, H_ = 70.0, 32.0, 35.0
    pl, pd = L_ / 4, D_ / 2
    r1 = 0.31 * min(pl, pd); r2 = r1 * 0.80; nh = 0.09 * H_ * BH / H_   # halbe Kantenlänge: quadratisch, oben flach, Seiten leicht schräg
    def P(X, Y, z=0.0):
        return (x0 + X / L_ * BW + Y / D_ * ox, y0 + Y / D_ * oy - z)
    def ring(cx, cy, r, z):
        return [P(cx + a * r, cy + b * r, z) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for iy in (1, 0):                 # hintere Reihe zuerst
        for ix in range(4):
            cx, cy = pl * (ix + 0.5), pd * (iy + 0.5)
            lo, hi = ring(cx, cy, r1, 0), ring(cx, cy, r2, nh)
            d.polygon(_hull([(round(a, 2), round(b, 2)) for a, b in lo + hi]), fill=shade(base, 0.78))
            # Glanzkante vorne links am Mantel
            if metal:
                d.polygon([P(cx - r1, cy - r1, 0), P(cx + r1, cy - r1, 0), P(cx + r2, cy - r2, nh), P(cx - r2, cy - r2, nh)], fill=shade(base, 0.95))
                d.line([P(cx - r1, cy - r1, 0), P(cx - r2, cy - r2, nh)], fill=shade(base, 1.45), width=4)
            d.polygon(hi, fill=(244, 247, 252) if snow else shade(base, 1.22))
            if snow:
                d.polygon(ring(cx, cy, r2 * 0.85, nh + 4), fill=(252, 253, 255))
            elif metal:
                d.polygon([P(cx - r2, cy - r2, nh), P(cx - r2 * 0.4, cy - r2, nh), P(cx - r2, cy + r2 * 0.2, nh)], fill=shade(base, 1.38))
    return nh


def block(variant="gold-glanz", size=420, seed=1, hang=True, text=None, form=None):
    """Sperrblock-Anhänger als RGBA. Pivot = (w/2, 0) bei hang=True."""
    v = dict(BLOCK[variant])
    form = form or FORM
    nh = 0.0
    if text is not None:
        v["text"] = text
    rng = np.random.default_rng(seed)
    rs = random.Random(seed)
    W = 1000
    x0 = 110
    BW, BH = 650, 330
    ox, oy = 170, -125
    y0 = 430
    CH = y0 + BH + 30
    im = Image.new("RGBA", (W, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = v["base"]
    top_c, side_c = shade(base, 1.16), shade(base, 0.66)
    fw, rh = BW * 0.17, BH * (0.22 if form == "glatt" else 0.126)   # Taschenhöhe (noppen: echtes Verhältnis)
    # Oberseite, Seite
    d.polygon([(x0, y0), (x0 + BW, y0), (x0 + BW + ox, y0 + oy), (x0 + ox, y0 + oy)], fill=top_c)
    d.polygon([(x0 + BW, y0), (x0 + BW + ox, y0 + oy), (x0 + BW + ox, y0 + BH + oy), (x0 + BW, y0 + BH)], fill=side_c)
    # Tasche durch den Block: dunkle Innenfläche sichtbar
    pockets = [(0.13, 0.40), (0.60, 0.87)] if form == "glatt" else [(0.25 - 0.0465, 0.25 + 0.0465), (0.75 - 0.0465, 0.75 + 0.0465)]   # zwei Staplertaschen (Anteil der Länge)
    tp = 8 if form == "glatt" else 4   # Schräge der Taschenwand
    for pa, pb in pockets:
        xa, xb = x0 + pa * BW, x0 + pb * BW
        d.polygon([(xa, y0 + BH - rh), (xb, y0 + BH - rh), (xb + ox * 0.35, y0 + BH - rh + oy * 0.35),
                   (xa + ox * 0.35, y0 + BH - rh + oy * 0.35)], fill=shade(base, 0.30))
        d.polygon([(xa, y0 + BH), (xa, y0 + BH - rh), (xa + ox * 0.35, y0 + BH - rh + oy * 0.35), (xa + ox * 0.35, y0 + BH + oy * 0.35)], fill=shade(base, 0.45))
    # Front als Maske (mit Tasche)
    front_poly = [(x0, y0), (x0 + BW, y0), (x0 + BW, y0 + BH)]
    for pa, pb in reversed(pockets):
        xa, xb = x0 + pa * BW, x0 + pb * BW
        front_poly += [(xb, y0 + BH), (xb - tp, y0 + BH - rh), (xa + tp, y0 + BH - rh), (xa, y0 + BH)]
    front_poly += [(x0, y0 + BH)]
    fm = Image.new("L", (W, CH), 0)
    ImageDraw.Draw(fm).polygon(front_poly, fill=255)
    # Front-Füllung mit Verlauf
    yy = np.linspace(0, 1, CH)[:, None]
    fr = np.zeros((CH, W, 4), np.float32)
    for c in range(3):
        fr[..., c] = base[c] * (1 - 0.22 * np.clip((yy - y0 / CH) / (BH / CH), 0, 1))
    fr[..., 3] = 255
    if v.get("metal"):
        X, Y = np.meshgrid(np.arange(W), np.arange(CH))
        u = ((X - x0) / BW) * 0.8 + ((Y - y0) / BH) * 0.35
        band = np.exp(-((u - 0.36) / 0.08) ** 2) * 0.8 + np.exp(-((u - 0.70) / 0.035) ** 2) * 0.4
        for c, hc in enumerate((255, 244, 214)):
            fr[..., c] = fr[..., c] * (1 - band) + hc * band
        dk = np.clip(0.45 - band, 0, 1) * ((Y - y0) / BH).clip(0, 1) * 0.35
        for c in range(3):
            fr[..., c] *= (1 - dk)
    front = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8), "RGBA")
    im.paste(front, (0, 0), fm)
    d = ImageDraw.Draw(im)
    # Fasen / Kantenlicht
    d.line([(x0, y0), (x0 + BW, y0)], fill=shade(base, 1.5 if v.get("metal") else 1.3), width=7)
    d.line([(x0 + BW, y0), (x0 + BW + ox, y0 + oy)], fill=shade(base, 1.3), width=5)
    d.line([(x0 + BW, y0), (x0 + BW, y0 + BH)], fill=shade(base, 0.82), width=5)
    # Schleifenband (Bescherung)
    rib = v.get("ribbon")
    if rib:
        rw = 64
        cx = x0 + BW * 0.5
        d.rectangle([cx - rw / 2, y0, cx + rw / 2, y0 + BH], fill=rib)
        d.polygon([(cx - rw / 2, y0), (cx + rw / 2, y0), (cx + rw / 2 + ox, y0 + oy), (cx - rw / 2 + ox, y0 + oy)], fill=shade(rib, 1.15))
        sy = y0 + BH * 0.38
        d.rectangle([x0, sy - rw / 2, x0 + BW, sy + rw / 2], fill=rib)
        d.polygon([(x0 + BW, sy - rw / 2), (x0 + BW + ox, sy - rw / 2 + oy), (x0 + BW + ox, sy + rw / 2 + oy), (x0 + BW, sy + rw / 2)], fill=shade(rib, 0.7))
        d.polygon([(x0 + BW * 0.25 + ox * 0.5 - rw / 2, y0 + oy * 0.5), (x0 + BW * 0.25 + ox * 0.5 + rw / 2, y0 + oy * 0.5),
                   (x0 + BW * 0.75 + ox * 0.5 + rw / 2, y0 + oy * 0.5), (x0 + BW * 0.75 + ox * 0.5 - rw / 2, y0 + oy * 0.5)], fill=rib)
    # Transportanker oben (nur glatt) bzw. Noppen (ohne Schnee hier, mit Schnee nach dem Schnee)
    if form == "noppen" and not v.get("snow"):
        nh = _noppen(d, x0, y0, BW, BH, ox, oy, base, v.get("metal"), False)
    for fx in ((0.27, 0.73) if form == "glatt" else ()):
        ax, ay = x0 + fx * BW + 0.5 * ox, y0 + 0.5 * oy
        d.ellipse([ax - 34, ay - 13, ax + 34, ay + 13], fill=shade(base, 0.55))
        d.ellipse([ax - 20, ay - 7, ax + 20, ay + 7], fill=(120, 116, 110))
        d.ellipse([ax - 9, ay - 4, ax + 9, ay + 3], fill=(70, 66, 62))
    # Schriftzug (Pinsel), auf die Front geklippt
    if v.get("text"):
        tf = ImageFont.truetype(F_SCRIPT, 170)
        tl = Image.new("RGBA", (BW * 2, BH * 2), (0, 0, 0, 0))
        td = ImageDraw.Draw(tl)
        td.text((BW, BH), v["text"], font=tf, fill=v["textcol"] + (255,), anchor="mm")
        tl = tl.crop(tl.getbbox()).rotate(4, expand=True, resample=Image.BICUBIC)
        k = BW * 0.92 / tl.width
        tl = tl.resize((int(tl.width * k), int(tl.height * k)), Image.LANCZOS)
        if v.get("matt"):
            a = np.array(tl).astype(np.int16)
            a[..., 3] = (a[..., 3] * (0.85 + 0.15 * rng.random(a.shape[:2]))).astype(np.int16)
            tl = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        layer = Image.new("RGBA", (W, CH), (0, 0, 0, 0))
        layer.alpha_composite(tl, (int(x0 + BW * 0.5 - tl.width / 2), int(y0 + BH * 0.40 - tl.height / 2)))
        la = ImageChops.multiply(layer.split()[3], fm)
        layer.putalpha(la)
        if v.get("metal"):  # Glanz über die Schrift
            pass
        im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    # Schnee
    if v.get("snow"):
        sw = (250, 252, 255)
        d.polygon([(x0 - 6, y0 + 4), (x0 + ox - 6, y0 + oy - 6), (x0 + BW + ox + 6, y0 + oy - 6), (x0 + BW + 8, y0 + 4)], fill=(238, 242, 250))
        # Polster-Wölbung
        d.polygon([(x0 + 30, y0 - 8), (x0 + ox, y0 + oy - 22), (x0 + BW + ox - 20, y0 + oy - 22), (x0 + BW - 10, y0 - 10)], fill=sw)
        xx = x0 - 6
        pts = [(x0 - 6, y0 - 6)]
        while xx < x0 + BW + 8:
            step = rs.randint(40, 80)
            dep = rs.randint(10, 48)
            pts += [(xx + step * 0.3, y0 + dep), (xx + step * 0.6, y0 + dep * 0.7), (xx + step, y0 + rs.randint(4, 14))]
            xx += step
        pts += [(x0 + BW + 8, y0 - 6)]
        d.polygon(pts, fill=sw)
        d.polygon([(x0 + BW + 6, y0 - 4), (x0 + BW + ox + 6, y0 + oy - 6), (x0 + BW + ox + 4, y0 + oy + 24), (x0 + BW + 4, y0 + 30)], fill=(222, 228, 240))
        if form == "noppen":
            nh = _noppen(d, x0, y0 - 10, BW, BH, ox, oy, base, v.get("metal"), True)
    # Textur: Betonporen / Verwitterung / Glitzer
    a = np.array(im).astype(np.int16)
    mask = a[..., 3] > 0
    n = rng.normal(0, 4 if v.get("metal") else 8, a.shape[:2])
    pores = (rng.random(a.shape[:2]) < (0.002 if v.get("metal") else 0.006)) & mask
    for c in range(3):
        a[..., c] = a[..., c] + n * mask
    a[pores, :3] -= 45
    if v.get("weathered"):
        # Abplatzungen: graue Betonflecken
        blot = Image.new("L", (W, CH), 0)
        bd = ImageDraw.Draw(blot)
        for _ in range(14):
            bx, by = rs.uniform(x0, x0 + BW + ox), rs.uniform(y0 + oy, y0 + BH)
            r = rs.uniform(3, 12)
            bd.ellipse([bx - r, by - r * 0.6, bx + r, by + r * 0.6], fill=255)
        bm = (np.array(blot.filter(ImageFilter.GaussianBlur(2))) > 120) & mask
        a[bm, 0], a[bm, 1], a[bm, 2] = 140, 136, 126
    if v.get("snow"):
        wm = (a[..., 0] > 230) & (a[..., 2] > 240) & mask
        sp = (rng.random(a.shape[:2]) < 0.01) & wm
        a[sp, 0], a[sp, 1], a[sp, 2] = 190, 215, 255
    if v.get("glitter"):
        sp = (rng.random(a.shape[:2]) < 0.012) & mask & ~((a[..., 0] > 235) & (a[..., 2] > 235))
        a[sp, :3] += 80
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # Schleife oben
    if rib:
        bx, by = x0 + BW / 2 + ox * 0.5, y0 + oy * 0.5 - 50
        for sgn in (-1, 1):
            d.ellipse([bx + sgn * 95 - 70, by - 50, bx + sgn * 95 + 70, by + 45], fill=rib, outline=shade(rib, 0.7), width=6)
            d.ellipse([bx + sgn * 95 - 35, by - 20, bx + sgn * 95 + 35, by + 20], fill=shade(rib, 0.6))
        d.polygon([(bx - 20, by + 10), (bx - 90, by + 120), (bx - 50, by + 120), (bx - 5, by + 30)], fill=shade(rib, 0.9))
        d.polygon([(bx + 20, by + 10), (bx + 90, by + 120), (bx + 50, by + 120), (bx + 5, by + 30)], fill=shade(rib, 0.8))
        d.ellipse([bx - 32, by - 30, bx + 32, by + 30], fill=shade(rib, 1.15))
    # Aufhänger: Messingöse mittig
    hx, hy = x0 + BW / 2 + ox * 0.5, y0 + oy * 0.5
    ring_y = hy - 22
    if hang:
        if not rib:
            d.ellipse([hx - 22, hy - 9, hx + 22, hy + 9], fill=(150, 118, 62))
            d.rectangle([hx - 9, hy - 26, hx + 9, hy], fill=(196, 160, 96))
        else:
            ring_y = hy - 80
        d.ellipse([hx - 24, ring_y - 54, hx + 24, ring_y + 4], outline=(214, 182, 120), width=10)
    out = Image.new("RGBA", (W, CH), (0, 0, 0, 0))
    if hang:
        od = ImageDraw.Draw(out)
        # Satinband als Schlaufe: zwei Stränge von der Öse nach oben, oben verknotet
        for dx, col in ((-11, (196, 158, 78, 255)), (11, (226, 192, 116, 255))):
            od.polygon([(W / 2 + dx - 6, ring_y - 48), (W / 2 + dx + 6, ring_y - 48), (W / 2 + 5, 10), (W / 2 - 5, 10)], fill=col)
        od.ellipse([W / 2 - 13, 0, W / 2 + 13, 24], fill=(200, 162, 82, 255))
    out.alpha_composite(im, (int(W / 2 - hx), 0))
    if not hang:
        out = out.crop(out.getbbox())
        sc = size / out.width
        return out.resize((size, int(out.height * sc)), Image.LANCZOS)
    sc = size / W
    return out.resize((size, int(CH * sc)), Image.LANCZOS)
