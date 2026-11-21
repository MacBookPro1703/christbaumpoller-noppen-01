"""Christbaumpoller – Verpackungs-Grafik (PIL). Flächen als Bilder in px/mm, mit Text-Layoutprüfung."""
import math, random, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

FD = "/home/claude/cbp/render/fonts/"
F_FRAK = FD + "unifrakturmaguntia-latin-400-normal.woff"
F_CIN = FD + "cinzel-latin-700-normal.woff"
F_CIN4 = FD + "cinzel-latin-400-normal.woff"
F_CIND = FD + "cinzel-decorative-latin-700-normal.woff"
F_VIB = FD + "great-vibes-latin-400-normal.woff"
F_BRUSH = FD + "CaveatBrush.ttf"
F_SANS = "/usr/share/fonts/truetype/google-fonts/ofl/sourcesans3/SourceSans3[wght].ttf"
F_SERIF = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
F_SERIF_I = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"

ROT = (150, 16, 28)
ROT_D = (88, 8, 16)
CREME = (250, 244, 228)
GOLD = (212, 175, 90)       # ≈ Pantone 871 C (Metallic-Gold) – Bildschirmnäherung
GOLD_D = (128, 92, 34)
GOLD_H = (255, 238, 176)
TANNE = (18, 64, 44)


def font(path, px, wght=None):
    f = ImageFont.truetype(path, max(6, int(px)))
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def gold_layer(mask, seed=1, glitter=0.0):
    """mask: L-Bild. Gibt RGBA mit Metallgold-Verlauf zurück."""
    W, H = mask.size
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    u = (y * 0.8 + x * 0.25)
    k = 0.5 + 0.5 * np.sin(u * math.pi * 5.0)
    k = k ** 1.6
    a = np.zeros((H, W, 4), np.float32)
    for c in range(3):
        a[..., c] = GOLD_D[c] + (GOLD_H[c] - GOLD_D[c]) * (0.25 + 0.75 * k)
    rng = np.random.default_rng(seed)
    a[..., :3] += rng.normal(0, 6, (H, W))[..., None]
    if glitter:
        sp = rng.random((H, W)) < glitter
        a[sp, :3] = 255
    a[..., 3] = np.array(mask, np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def glitter(img, density=0.0025, seed=3, col=(255, 248, 225), area=None, big=0.04, unit=None):
    """Glitzer als Druckeffekt: kleine Punkte + vereinzelte Sternfunkeln."""
    W, H = img.size
    rs = random.Random(seed)
    d = ImageDraw.Draw(img)
    u = unit if unit else W / 900
    n = int(W * H * density / 100 * (W / 900 / u) ** 2 * 0.5) if unit else int(W * H * density / 100)
    for _ in range(n):
        x, y = rs.uniform(0, W), rs.uniform(0, H)
        if area and not area(x, y):
            continue
        r = rs.choice((0.6, 0.8, 1.0, 1.3)) * u
        a = rs.randint(120, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
        if rs.random() < big:
            L = rs.uniform(4, 9) * u
            d.line([(x - L, y), (x + L, y)], fill=col + (200,), width=max(1, int(u)))
            d.line([(x, y - L), (x, y + L)], fill=col + (200,), width=max(1, int(u)))
    return img


def star(d, cx, cy, r, fill, n=5, inner=0.45, rot=-90):
    pts = []
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def snowflake(d, cx, cy, r, fill, w=1):
    for i in range(6):
        a = math.radians(i * 60)
        x2, y2 = cx + r * math.cos(a), cy + r * math.sin(a)
        d.line([(cx, cy), (x2, y2)], fill=fill, width=w)
        for t in (0.5, 0.75):
            bx, by = cx + r * t * math.cos(a), cy + r * t * math.sin(a)
            for s in (-1, 1):
                b = a + s * math.radians(40)
                d.line([(bx, by), (bx + r * 0.22 * math.cos(b), by + r * 0.22 * math.sin(b))], fill=fill, width=w)


class Face:
    """Eine Packungsfläche: B×H mm, px/mm. Text wird mit Box protokolliert (für check())."""

    def __init__(self, name, B, H, ppm=16, bg=ROT, seed=1):
        self.name, self.B, self.H, self.ppm = name, B, H, ppm
        self.W, self.Hp = int(round(B * ppm)), int(round(H * ppm))
        self.img = Image.new("RGBA", (self.W, self.Hp), bg + (255,))
        self.boxes = []
        self.seed = seed

    def mm(self, v):
        return v * self.ppm

    def bg_red(self, pattern=True):
        W, H = self.W, self.Hp
        X, Y = np.meshgrid(np.linspace(-1, 1, W), np.linspace(-1, 1, H))
        r = np.sqrt((X * 0.8) ** 2 + (Y * 0.9) ** 2)
        k = np.clip(1 - r * 0.55, 0, 1)
        a = np.zeros((H, W, 4), np.float32)
        for c in range(3):
            a[..., c] = ROT_D[c] + (ROT[c] + 22 - ROT_D[c]) * k
        a[..., 3] = 255
        self.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        if pattern:  # Damast aus Schneeflocken und Sternen, Ton in Ton
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            step = self.mm(9)
            rs = random.Random(self.seed)
            j = 0
            yy = -step
            while yy < H + step:
                xx = -step + (step / 2 if j % 2 else 0)
                while xx < W + step:
                    if (int(xx / step) + j) % 2:
                        snowflake(d, xx, yy, self.mm(1.8), (255, 210, 200, 34), w=max(1, int(self.mm(0.18))))
                    else:
                        star(d, xx, yy, self.mm(1.0), (255, 220, 160, 30))
                    xx += step
                yy += step * 0.866
                j += 1
            self.img.alpha_composite(lay)
        return self

    def gold_frame(self, inset=2.0, w=0.45, double=True):
        m = Image.new("L", self.img.size, 0)
        d = ImageDraw.Draw(m)
        i, ww = self.mm(inset), max(1, int(self.mm(w)))
        d.rectangle([i, i, self.W - i, self.Hp - i], outline=255, width=ww)
        if double:
            i2 = i + self.mm(0.9)
            d.rectangle([i2, i2, self.W - i2, self.Hp - i2], outline=255, width=max(1, ww // 2))
        for cx, cy in ((i, i), (self.W - i, i), (i, self.Hp - i), (self.W - i, self.Hp - i)):
            star(d, cx, cy, self.mm(1.6), 255, n=4, inner=0.3, rot=-90)
        self.img.alpha_composite(gold_layer(m, self.seed))
        return self

    # ---------------- Text ----------------
    def text(self, xy_mm, s, fpath, size_mm, fill="gold", anchor="mm", wght=None, max_w=None, shadow=True,
             rot=0, tag=None, spacing=0.0):
        px = self.mm(size_mm)
        f = font(fpath, px, wght)
        if max_w:
            while f.getbbox(s)[2] - f.getbbox(s)[0] > self.mm(max_w) and px > 6:
                px *= 0.96
                f = font(fpath, px, wght)
        tmp = Image.new("L", (self.W * 2, self.Hp * 2), 0)
        td = ImageDraw.Draw(tmp)
        if "\n" in s:
            td.multiline_text((self.W, self.Hp), s, font=f, fill=255, anchor=anchor, align=anchor[0] == "l" and "left" or "center",
                              spacing=self.mm(spacing))
        else:
            td.text((self.W, self.Hp), s, font=f, fill=255, anchor=anchor)
        bb = tmp.getbbox()
        if bb is None:
            return None
        g = tmp.crop(bb)
        ox, oy = bb[0] - self.W, bb[1] - self.Hp
        if rot:
            g = g.rotate(rot, expand=True, resample=Image.BICUBIC)
        x, y = self.mm(xy_mm[0]) + ox, self.mm(xy_mm[1]) + oy
        if rot:
            x -= (g.width - (bb[2] - bb[0])) / 2
            y -= (g.height - (bb[3] - bb[1])) / 2
        x, y = int(x), int(y)
        if fill == "gold":
            lay = gold_layer(g, self.seed + len(self.boxes))
        else:
            lay = Image.new("RGBA", g.size, fill + (0,))
            lay.putalpha(g)
        if shadow:
            sh = Image.new("RGBA", g.size, (40, 0, 4, 0))
            sh.putalpha(g.point(lambda v: int(v * 0.55)))
            sh = sh.filter(ImageFilter.GaussianBlur(max(1, self.mm(0.15))))
            self.img.alpha_composite(sh, (x + int(self.mm(0.15)), y + int(self.mm(0.2))))
        self.img.alpha_composite(lay, (x, y))
        box = (x / self.ppm, y / self.ppm, (x + g.width) / self.ppm, (y + g.height) / self.ppm)
        self.boxes.append((tag or s[:24], box))
        return box

    def check(self, margin=1.2, report=True):
        errs = []
        for t, (x0, y0, x1, y1) in self.boxes:
            if x0 < margin or y0 < margin or x1 > self.B - margin or y1 > self.H - margin:
                errs.append(f"{self.name}: '{t}' außerhalb Rand ({x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}) in {self.B}×{self.H}")
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                a, b = self.boxes[i][1], self.boxes[j][1]
                if a[0] < b[2] - 0.05 and b[0] < a[2] - 0.05 and a[1] < b[3] - 0.05 and b[1] < a[3] - 0.05:
                    errs.append(f"{self.name}: '{self.boxes[i][0]}' überlappt '{self.boxes[j][0]}'")
        if report:
            print(("OK  " if not errs else "FEHLER ") + f"{self.name}: {len(self.boxes)} Texte", *errs, sep="\n   ")
        return errs


# ---------------- Schmuckelemente ----------------
def ribbon_band(img, pts, width_px, seed=1):
    """Aufgedrucktes Satinband entlang Polylinie (Druck, kein echtes Band)."""
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).line(pts, fill=255, width=int(width_px), joint="curve")
    g = gold_layer(m, seed)
    # Satinrillen
    d = ImageDraw.Draw(g)
    for t in (-0.28, 0.28):
        p2 = [(x, y) for x, y in pts]
    img.alpha_composite(g)
    # Kanten
    e = Image.new("L", img.size, 0)
    ImageDraw.Draw(e).line(pts, fill=255, width=int(width_px))
    edge = ImageChops.subtract(e, e.filter(ImageFilter.MinFilter(5)))
    lay = Image.new("RGBA", img.size, GOLD_D + (0,))
    lay.putalpha(edge.point(lambda v: int(v * 0.8)))
    img.alpha_composite(lay)


def bow(img, cx, cy, s, seed=2, tails=True):
    """Gedruckte Schleife, Größe s px (Spannweite ≈ 2.2 s)."""
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    hi = Image.new("L", img.size, 0)
    dh = ImageDraw.Draw(hi)
    sh = Image.new("L", img.size, 0)
    ds = ImageDraw.Draw(sh)
    if tails:
        for sgn in (-1, 1):
            poly = [(cx + sgn * 0.08 * s, cy + 0.1 * s), (cx + sgn * 0.55 * s, cy + 1.05 * s), (cx + sgn * 0.42 * s, cy + 0.92 * s),
                    (cx + sgn * 0.30 * s, cy + 1.12 * s), (cx - sgn * 0.08 * s, cy + 0.15 * s)]
            d.polygon(poly, fill=255)
            ds.line(poly[:2], fill=255, width=max(1, int(s * 0.03)))
    for sgn in (-1, 1):
        lp = [(cx, cy)]
        for i in range(0, 361, 10):
            a = math.radians(i)
            lp.append((cx + sgn * (0.58 * s + 0.52 * s * math.cos(a)) * 1.0 - sgn * 0.0, cy - 0.06 * s + 0.36 * s * math.sin(a)))
        lp = [(cx, cy - 0.1 * s), (cx + sgn * 0.5 * s, cy - 0.55 * s), (cx + sgn * 1.08 * s, cy - 0.42 * s),
              (cx + sgn * 1.12 * s, cy - 0.05 * s), (cx + sgn * 0.85 * s, cy + 0.22 * s), (cx + sgn * 0.3 * s, cy + 0.12 * s)]
        d.polygon(lp, fill=255)
        ds.polygon([(cx + sgn * 0.18 * s, cy - 0.05 * s), (cx + sgn * 0.62 * s, cy - 0.30 * s), (cx + sgn * 0.85 * s, cy - 0.12 * s),
                    (cx + sgn * 0.45 * s, cy + 0.02 * s)], fill=255)
        dh.line([(cx + sgn * 0.45 * s, cy - 0.45 * s), (cx + sgn * 0.98 * s, cy - 0.36 * s)], fill=255, width=max(1, int(s * 0.07)))
    d.ellipse([cx - 0.2 * s, cy - 0.24 * s, cx + 0.2 * s, cy + 0.18 * s], fill=255)
    dh.ellipse([cx - 0.1 * s, cy - 0.17 * s, cx + 0.04 * s, cy - 0.06 * s], fill=255)
    # Schatten unter der Schleife
    shadow = Image.new("RGBA", img.size, (30, 0, 0, 0))
    shadow.putalpha(m.filter(ImageFilter.GaussianBlur(s * 0.05)).point(lambda v: int(v * 0.6)))
    img.alpha_composite(shadow, (int(s * 0.04), int(s * 0.07)))
    img.alpha_composite(gold_layer(m, seed))
    dk = Image.new("RGBA", img.size, GOLD_D + (0,))
    dk.putalpha(ImageChops.multiply(sh.filter(ImageFilter.GaussianBlur(s * 0.03)), m).point(lambda v: int(v * 0.75)))
    img.alpha_composite(dk)
    hl = Image.new("RGBA", img.size, GOLD_H + (0,))
    hl.putalpha(hi.filter(ImageFilter.GaussianBlur(s * 0.02)).point(lambda v: int(v * 0.8)))
    img.alpha_composite(hl)


def rosette(img, cx, cy, r, lines, seed=5, ring_text=None):
    """Siegel mit Zackenrand, rotem Innenkreis, Gold-Text."""
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    n = 36
    pts = []
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * 0.9
        a = math.pi * i / n
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=255)
    sh = Image.new("RGBA", img.size, (20, 0, 0, 0))
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(r * 0.08)).point(lambda v: int(v * 0.6)))
    img.alpha_composite(sh, (int(r * 0.05), int(r * 0.08)))
    img.alpha_composite(gold_layer(m, seed))
    d2 = ImageDraw.Draw(img)
    d2.ellipse([cx - r * 0.74, cy - r * 0.74, cx + r * 0.74, cy + r * 0.74], fill=ROT_D + (255,))
    d2.ellipse([cx - r * 0.68, cy - r * 0.68, cx + r * 0.68, cy + r * 0.68], outline=GOLD + (255,), width=max(1, int(r * 0.03)))
    # Ringtext
    if ring_text:
        f = font(F_CIN, r * 0.17)
        L = len(ring_text)
        span = 300
        for i, ch in enumerate(ring_text):
            a = math.radians(-90 - span / 2 + span * (i + 0.5) / L)
            x, y = cx + r * 0.83 * math.cos(a), cy + r * 0.83 * math.sin(a)
            g = Image.new("L", (int(r), int(r)), 0)
            ImageDraw.Draw(g).text((r / 2, r / 2), ch, font=f, fill=255, anchor="mm")
            g = g.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
            lay = Image.new("RGBA", g.size, ROT_D + (0,))
            lay.putalpha(g)
            img.alpha_composite(lay, (int(x - r / 2), int(y - r / 2)))
    # Innentext
    tot = sum(sz for _, _, sz in lines)
    y = cy - tot * r / 2
    for s, fp, sz in lines:
        f = font(fp, sz * r * 0.92)
        g = Image.new("L", (int(r * 3), int(sz * r * 2.2)), 0)
        ImageDraw.Draw(g).text((r * 1.5, sz * r * 1.1), s, font=f, fill=255, anchor="mm")
        bb = g.getbbox()
        if bb:
            g = g.crop(bb)
            k = min(1.0, r * 1.15 / g.width)
            if k < 1:
                g = g.resize((max(1, int(g.width * k)), max(1, int(g.height * k))), Image.LANCZOS)
            img.alpha_composite(gold_layer(g, seed + 1), (int(cx - g.width / 2), int(y + sz * r / 2 - g.height / 2)))
        y += sz * r
    star(ImageDraw.Draw(img), cx, cy + r * 0.52, r * 0.07, GOLD + (255,))


def arch_poly(x0, y0, x1, y1, rise=None, n=60):
    """Kirchenfenster (Tudorbogen mit leichter Spitze): Seiten gerade, oben Bogen mit Scheitel bei y0."""
    a = (x1 - x0) / 2
    xc = x0 + a
    rise = rise if rise else min(a * 0.55, (y1 - y0) * 0.42)
    spring = y0 + rise
    pts = [(x0, y1), (x0, spring)]
    for i in range(1, n):
        t = 1 - i / n            # 1 → 0 (links außen → Mitte)
        f = math.sqrt(max(0.0, 1 - t * t)) * (1 - 0.22 * t) / 1.0
        f = f / (1.0)
        pts.append((xc - a * t, spring - rise * f))
    pts.append((xc, y0))
    for i in range(1, n):
        t = i / n
        f = math.sqrt(max(0.0, 1 - t * t)) * (1 - 0.22 * t)
        pts.append((xc + a * t, spring - rise * f))
    pts += [(x1, spring), (x1, y1)]
    return pts
