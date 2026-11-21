"""Einzelschachtel „Die Einzelmaßnahme“ – Flächen + 3D-Mockup."""
import sys, math
sys.path.insert(0, "/home/claude/cbp/render")
sys.path.insert(0, "/home/claude/cbp/pack")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import engine
from art import *
from dims import einzel, BLOCK, SOCKEL
import box3d

PPM = 26


def window_rect(d):
    B, H = d["B"], d["H"]
    k = B / 74
    return (4.2 * k, 4.0 * k, B - 4.2 * k, H - 10.0 * k)


def interior(face, d, variant, g, seed=1):
    """Inneres hinter dem Sichtfenster: Strahlenkranz, Sockel, Block mit Öse und Band."""
    W, Hp, ppm = face.W, face.Hp, face.ppm
    B, H = d["B"], d["H"]
    inn = Image.new("RGBA", (W, Hp), (0, 0, 0, 255))
    # Rückwand: Goldener Strahlenkranz auf Dunkelrot
    X, Y = np.meshgrid(np.arange(W), np.arange(Hp))
    cx, cy = W / 2, Hp * 0.42
    ang = np.arctan2(Y - cy, X - cx)
    rr = np.hypot(X - cx, Y - cy) / W
    rays = (0.5 + 0.5 * np.cos(ang * 28)) ** 3
    a = np.zeros((Hp, W, 4), np.float32)
    base = np.clip(1 - rr * 1.2, 0.25, 1)
    for c, (dc, gc) in enumerate(zip((70, 6, 12), (236, 196, 110))):
        a[..., c] = dc + (gc - dc) * rays * base * 0.55 + 18 * base
    a[..., 3] = 255
    inn = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    glow = Image.new("RGBA", (W, Hp), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - W * 0.22, cy - W * 0.22, cx + W * 0.22, cy + W * 0.22], fill=(255, 226, 150, 120))
    inn.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W * 0.08)))
    # Sockel (Einlage), sichtbare Oberkante
    L, Hb, D = BLOCK[g]
    yb = (H - SOCKEL[g]) * ppm
    dd = ImageDraw.Draw(inn)
    dd.rectangle([0, yb, W, Hp], fill=(110, 12, 22, 255))
    dd.polygon([(0, yb), (W, yb), (W * 0.93, yb - 3.5 * ppm), (W * 0.07, yb - 3.5 * ppm)], fill=(132, 18, 30, 255))
    # Block (Engine), Front ≈ 92 % der echten Breite (liegt hinter der Fensterebene)
    size = int(L * ppm * 0.70 / 0.65)
    spr = engine.block(variant, size=size, seed=seed, hang=True)
    s = size / 1000
    front_left = 90 * s
    bottom = 760 * s
    x = int(W / 2 - (L * ppm * 0.70) / 2 - front_left - 3.2 * ppm * (B / 74))
    y = int(yb - bottom - 0.6 * ppm)
    # Schatten
    sh = Image.new("RGBA", (W, Hp), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x + front_left, yb - 4.5 * ppm, x + front_left + L * ppm * 1.1, yb + 0.5 * ppm], fill=(20, 0, 0, 170))
    inn.alpha_composite(sh.filter(ImageFilter.GaussianBlur(ppm * 1.2)))
    inn.alpha_composite(spr, (x, y))
    # Innenschatten (Tiefe)
    vg = Image.new("L", (W, Hp), 0)
    x0, y0, x1, y1 = [v * ppm for v in window_rect(d)]
    ImageDraw.Draw(vg).rectangle([x0 + ppm * 2.5, y0 + ppm * 3, x1 - ppm * 2.5, y1 + ppm * 6], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(ppm * 2.6))
    dark = Image.new("RGBA", (W, Hp), (10, 0, 2, 0))
    dark.putalpha(vg.point(lambda v: int((255 - v) * 0.75)))
    inn.alpha_composite(dark)
    return inn


def front(g="M", variant="gold-glanz", seed=1, show_window=True):
    d = einzel(g)
    k = d["B"] / 74
    f = Face(f"Einzel {g} vorne", d["B"], d["H"], PPM, seed=seed).bg_red()
    wx0, wy0, wx1, wy1 = window_rect(d)
    poly = [(x * PPM, y * PPM) for x, y in arch_poly(wx0, wy0, wx1, wy1)]
    # Glitzer auf Rot
    glitter(f.img, density=0.06, seed=seed + 3)
    if show_window:
        inn = interior(f, d, variant, g, seed)
        m = Image.new("L", f.img.size, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        f.img.paste(inn, (0, 0), m)
        # Folienglanz
        gl = Image.new("L", f.img.size, 0)
        gd = ImageDraw.Draw(gl)
        gd.polygon([(wx0 * PPM, wy1 * PPM * 0.55), (wx0 * PPM + f.W * 0.18, wy0 * PPM), (wx0 * PPM + f.W * 0.28, wy0 * PPM),
                    (wx0 * PPM, wy1 * PPM * 0.85)], fill=60)
        gd.polygon([(wx1 * PPM - f.W * 0.10, wy1 * PPM), (wx1 * PPM, wy1 * PPM * 0.62), (wx1 * PPM, wy1 * PPM * 0.70),
                    (wx1 * PPM - f.W * 0.05, wy1 * PPM)], fill=40)
        gl = ImageChops.multiply(gl.filter(ImageFilter.GaussianBlur(PPM * 0.8)), m)
        wl = Image.new("RGBA", f.img.size, (255, 255, 255, 0))
        wl.putalpha(gl)
        f.img.alpha_composite(wl)
    # Goldrahmen des Fensters (Kirchenfenster, doppelt) + Maßwerk-Sterne
    fm = Image.new("L", f.img.size, 0)
    fd = ImageDraw.Draw(fm)
    fd.line(poly + [poly[0]], fill=255, width=int(PPM * 0.9 * k), joint="curve")
    outer = [(x * PPM, y * PPM) for x, y in arch_poly(wx0 - 1.0 * k, wy0 - 1.4 * k, wx1 + 1.0 * k, wy1 + 0.0, rise=min((wx1 - wx0) / 2 * 0.55, (wy1 - wy0) * 0.42) + 0.4 * k)]
    fd.line(outer[:-1], fill=255, width=int(PPM * 0.3 * k), joint="curve")
    f.img.alpha_composite(gold_layer(fm, seed))
    dr = ImageDraw.Draw(f.img)
    for sx in (wx0 + 4.0 * k, wx1 - 4.0 * k):
        star(dr, sx * PPM, (wy0 + 4.0 * k) * PPM, 1.3 * k * PPM, GOLD + (255,))
    f.gold_frame(inset=1.2 * k, w=0.3 * k)
    # Unterer Streifen: Name + Slogan (links vom Siegel)
    cxn = (d["B"] - 13 * k) / 2 + 2.5 * k
    f.text((cxn, d["H"] - 6.6 * k), "CHRISTBAUMPOLLER", F_CIN, 3.4 * k, max_w=d["B"] - 22 * k, tag="Name")
    f.text((cxn, d["H"] - 2.9 * k), "Ein Stück Sicherheitsgefühl für zu Hause", F_VIB, 2.8 * k, fill=CREME,
           max_w=d["B"] - 21 * k, tag="Slogan")
    # Siegel unten rechts, über Fensterecke
    rosette(f.img, (d["B"] - 8.0 * k) * PPM, (d["H"] - 8.6 * k) * PPM, 6.4 * k * PPM,
            [("geprüft", F_CIN, 0.30), ("nach", F_VIB, 0.30), ("Gefühl", F_CIN, 0.30)], seed=seed + 7)
    return f


def kopf(g="M", seed=1):
    d = einzel(g)
    k = d["B"] / 74
    f = Face(f"Einzel {g} Kopfkarte", d["B"], d["kopf"], PPM, seed=seed + 1).bg_red()
    glitter(f.img, density=0.07, seed=seed + 4)
    yb = (d["kopf"] - 3.0 * k) * PPM
    ribbon_band(f.img, [(-10, yb), (f.W + 10, yb)], 2.6 * k * PPM, seed)
    f.text((d["B"] / 2 + 4 * k, 15.0 * k), "Fürchtet euch nicht.", F_FRAK, 6.2 * k, max_w=d["B"] - 26 * k, tag="Spruch")
    f.text((d["B"] / 2 + 4 * k, 21.6 * k), "LUKAS 2,10", F_CIN4, 1.9 * k, fill=CREME, shadow=False, tag="Quelle")
    dr = ImageDraw.Draw(f.img)
    for sx, sy, sr in ((d["B"] - 6 * k, 6 * k, 2.0), (d["B"] - 10.5 * k, 10 * k, 0.9), (13 * k, 5.5 * k, 0.8)):
        star(dr, sx * PPM, sy * PPM, sr * k * PPM, GOLD + (255,))
    bow(f.img, 8.0 * k * PPM, yb - 1.0 * k * PPM, 5.6 * k * PPM, seed=seed + 2)
    return f


def euroloch(img, cx, cy, ppm, k=1):
    """Eurolochung ausstanzen (transparent)."""
    a = img.split()[3]
    m = Image.new("L", img.size, 255)
    d = ImageDraw.Draw(m)
    w, h, r = 13 * k * ppm, 3.2 * k * ppm, 3.2 * k * ppm
    d.rounded_rectangle([cx - w, cy - h / 2, cx + w, cy + h / 2], radius=h / 2, fill=0)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    img.putalpha(ImageChops.multiply(a, m))
    return img


def kopf_shape(f, k):
    """Obere Ecken abrunden + Eurolochung."""
    m = Image.new("L", f.img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, f.W, f.Hp + 40], radius=int(5 * k * f.ppm), fill=255)
    f.img.putalpha(ImageChops.multiply(f.img.split()[3], m))
    euroloch(f.img, f.W / 2, 5.2 * k * f.ppm, f.ppm, k)


def top(g="M", seed=1):
    d = einzel(g)
    k = d["B"] / 74
    f = Face(f"Einzel {g} oben", d["B"], d["T"], PPM, seed=seed + 2).bg_red()
    glitter(f.img, density=0.06, seed=seed + 5)
    f.gold_frame(inset=1.2 * k, w=0.3 * k, double=False)
    f.text((d["B"] / 2 + 2 * k, d["T"] * 0.40), "Hier öffnen.", F_BRUSH, 5.2 * k, fill=CREME, rot=3, tag="öffnen")
    f.text((d["B"] / 2 + 2 * k, d["T"] * 0.68), "Ohne Genehmigung.", F_BRUSH, 3.6 * k, fill=CREME, rot=3, tag="Genehmigung")
    return f


def side_r(g="M", seed=1):
    d = einzel(g)
    k = d["B"] / 74
    L, H, D = BLOCK[g]
    f = Face(f"Einzel {g} rechts", d["T"], d["H"], PPM, seed=seed + 3).bg_red()
    glitter(f.img, density=0.06, seed=seed + 6)
    f.gold_frame(inset=1.2 * k, w=0.3 * k, double=False)
    T = d["T"]
    star(ImageDraw.Draw(f.img), T / 2 * PPM, 7 * k * PPM, 2.4 * k * PPM, GOLD + (255,))
    f.text((T / 2, 15.5 * k), "DIE EINZEL-\nMASSNAHME", F_CIN, 3.3 * k, max_w=T - 6 * k, tag="Packname", spacing=0.6 * k)
    f.text((T / 2, 26.5 * k), "#wirschaffendas", F_BRUSH, 4.4 * k, fill=CREME, rot=4, max_w=T - 6 * k, tag="Hashtag")
    f.text((T / 2, 36.5 * k), "Mit Sicherheits-\nabstand verpackt.", F_SERIF_I, 2.5 * k, fill=CREME, wght=500, spacing=0.4 * k,
           max_w=T - 6 * k, tag="Abstand")
    f.text((T / 2, 48 * k), f"Größe {g}\n{L} × {H} × {D} mm", F_SANS, 2.2 * k, fill=CREME, wght=600, spacing=0.4 * k,
           max_w=T - 6 * k, tag="Größe")
    return f


def mockup(g="M", variant="gold-glanz", out=None, W=1800, H=1500, seed=1):
    d = einzel(g)
    B, T, Hh, KH = d["B"], d["T"], d["H"], d["kopf"]
    fr, kp, tp, sr = front(g, variant, seed), kopf(g, seed), top(g, seed), side_r(g, seed)
    kk = B / 74
    kopf_shape(kp, kk)
    S = 2  # Supersampling
    dist = 520
    cam = box3d.Cam(yaw=30, pitch=-16, dist=dist, f=(W * S * 0.50 / B) * dist, cx=W * S * 0.47, cy=H * S * 0.56)
    can = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    ox, oy, oz = -B / 2, -Hh / 2 - 6, -T / 2
    P = lambda x, y, z: cam.p(x + ox, y + oy, z + oz)
    # Bodenschatten
    box3d.shadow(can, [P(0, 0, 0), P(B, 0, 0), P(B + 4, 0, T + 12), P(6, 0, T + 16)], 22 * S, alpha=190)
    box3d.shadow(can, [P(-3, 0, -2), P(B + 3, 0, -2), P(B + 3, 0, T + 3), P(-3, 0, T + 3)], 5 * S, alpha=210)
    # Kopfkarte: steht an der Rückwand über der Oberseite
    box3d.put(can, kp.img, [P(0, Hh + KH, T), P(B, Hh + KH, T), P(B, Hh, T), P(0, Hh, T)], shade=0.97)
    box3d.put(can, tp.img, [P(0, Hh, T), P(B, Hh, T), P(B, Hh, 0), P(0, Hh, 0)], shade=1.08)
    box3d.put(can, sr.img, [P(B, Hh, 0), P(B, Hh, T), P(B, 0, T), P(B, 0, 0)], shade=0.72)
    box3d.put(can, fr.img, [P(0, Hh, 0), P(B, Hh, 0), P(B, 0, 0), P(0, 0, 0)], shade=1.0)
    # Kantenlicht
    dd = ImageDraw.Draw(can)
    dd.line([P(0, Hh, 0), P(B, Hh, 0)], fill=(255, 230, 200, 110), width=2 * S)
    dd.line([P(B, Hh, 0), P(B, 0, 0)], fill=(255, 220, 190, 70), width=2 * S)
    can = can.resize((W, H), Image.LANCZOS)
    if out:
        scene(can).convert("RGB").save(out, quality=92)
    return can


def scene(obj, seed=4):
    """Hintergrund: warmes Dunkel mit Lichterbokeh, Tisch."""
    W, H = obj.size
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    a = np.zeros((H, W, 4), np.float32)
    Y = np.linspace(0, 1, H)[:, None]
    X = np.linspace(0, 1, W)[None, :]
    r = np.hypot(X - 0.5, (Y - 0.45) * 1.2)
    for c, (c0, c1) in enumerate(zip((14, 15, 18), (58, 34, 26))):
        a[..., c] = c0 + (c1 - c0) * np.clip(1 - r * 1.6, 0, 1)
    a[..., 3] = 255
    bg = Image.fromarray(a.astype(np.uint8), "RGBA")
    bk = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(bk)
    rs = random.Random(seed)
    for _ in range(46):
        x, y = rs.uniform(0, W), rs.uniform(0, H * 0.62)
        rr = rs.uniform(W * 0.012, W * 0.045)
        col = rs.choice([(255, 196, 110), (255, 170, 80), (255, 225, 170), (230, 60, 50)])
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (rs.randint(26, 70),))
    bg.alpha_composite(bk.filter(ImageFilter.GaussianBlur(W * 0.006)))
    # Tischfläche
    t = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    td.rectangle([0, H * 0.70, W, H], fill=(30, 20, 16, 200))
    bg.alpha_composite(t.filter(ImageFilter.GaussianBlur(H * 0.05)))
    bg.alpha_composite(obj)
    return bg


if __name__ == "__main__":
    import time
    t = time.time()
    mockup("M", "gold-glanz", out="/home/claude/cbp/pack/probe_einzel.jpg")
    for fc in (front(), kopf(), top(), side_r()):
        fc.check()
    print(round(time.time() - t, 1), "s")
