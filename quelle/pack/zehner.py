"""10er-Schachtel „Sicherheitskonzept für Ihr Wohnzimmer“ – Flächen, 3D-Poller, Mockups zu/offen."""
import sys, math, random
sys.path.insert(0, "/home/claude/cbp/render")
sys.path.insert(0, "/home/claude/cbp/pack")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import engine
from art import *
from dims import zehner, BLOCK, OESE
import box3d
from einzel import scene
from engine import shade

PPM = 14
MIX = ["gold-glanz", "silber-matt-schnee", "rot-glanz", "gold-matt-schnee", "silber-glanz",
       "rot-matt", "gold-glanz-schnee", "silber-matt", "rot-glanz-schnee", "gold-matt"]


# ---------------- Poller als echter 3D-Quader (Texturen je Variante) ----------------
def block_tex(variant, g="M", ppm=14, seed=1):
    v = engine.BLOCK[variant]
    L, H, D = BLOCK[g]
    k = L / 70
    base = v["base"]
    rs = np.random.default_rng(seed)

    def surf(w, h, col, metal, hl_pos=0.35):
        Wp, Hp = int(w * ppm), int(h * ppm)
        a = np.zeros((Hp, Wp, 4), np.float32)
        Y, X = np.mgrid[0:Hp, 0:Wp]
        for c in range(3):
            a[..., c] = col[c] * (1 - 0.18 * Y / Hp)
        if metal:
            u = X / Wp * 0.8 + Y / Hp * 0.35
            band = np.exp(-((u - hl_pos) / 0.09) ** 2) * 0.75 + np.exp(-((u - hl_pos - 0.34) / 0.04) ** 2) * 0.35
            for c, hc in enumerate((255, 246, 222)):
                a[..., c] = a[..., c] * (1 - band) + hc * band
        a[..., :3] += rs.normal(0, 3 if metal else 6, (Hp, Wp))[..., None]
        if v.get("glitter"):
            sp = rs.random((Hp, Wp)) < 0.01
            a[sp, :3] += 70
        a[..., 3] = 255
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")

    metal = v.get("metal", False)
    front = surf(L, H, base, metal)
    d = ImageDraw.Draw(front)
    # Staplertaschen (M: Fuß 9 / Tasche 19, oben 17 / Mitte 14 / 19 / 9, Höhe 8)
    ph = 8 * k * ppm
    for xa in (9 * k, (9 + 19 + 14) * k):
        x0, x1 = xa * ppm, (xa + 19 * k) * ppm
        d.polygon([(x0, H * ppm), (x0 + k * ppm, H * ppm - ph), (x1 - k * ppm, H * ppm - ph), (x1, H * ppm)],
                  fill=shade(base, 0.22) + (255,))
        d.polygon([(x0 + k * ppm, H * ppm - ph), (x1 - k * ppm, H * ppm - ph), (x1 - 2 * k * ppm, H * ppm - ph + 2.2 * k * ppm),
                   (x0 + 2 * k * ppm, H * ppm - ph + 2.2 * k * ppm)], fill=shade(base, 0.42) + (255,))
    # Schriftzug
    tf = font(engine.F_SCRIPT, 9.5 * k * ppm)
    tl = Image.new("L", (int(L * ppm * 2), int(H * ppm * 2)), 0)
    ImageDraw.Draw(tl).text((L * ppm, H * ppm), "#wirschaffendas", font=tf, fill=255, anchor="mm")
    tl = tl.crop(tl.getbbox()).rotate(4, expand=True, resample=Image.BICUBIC)
    sc = L * ppm * 0.88 / tl.width
    tl = tl.resize((int(tl.width * sc), int(tl.height * sc)), Image.LANCZOS)
    lay = Image.new("RGBA", tl.size, v["textcol"] + (0,))
    lay.putalpha(tl)
    front.alpha_composite(lay, (int(L * ppm / 2 - tl.width / 2), int(H * ppm * 0.40 - tl.height / 2)))
    top = surf(L, D, shade(base, 1.14), metal, 0.5)
    side = surf(D, H, shade(base, 0.85), metal, 0.6)
    td = ImageDraw.Draw(top)
    for fx in (19 * k, 51 * k):  # Transportanker
        cx, cy = fx * ppm, D * ppm / 2
        r = 3 * k * ppm
        td.ellipse([cx - r * 1.4, cy - r, cx + r * 1.4, cy + r], fill=shade(base, 0.6) + (255,))
        td.ellipse([cx - r * 0.8, cy - r * 0.55, cx + r * 0.8, cy + r * 0.55], fill=(110, 106, 100, 255))
    if v.get("snow"):
        sw = (248, 250, 255, 255)
        top = Image.new("RGBA", top.size, sw)
        td = ImageDraw.Draw(top)
        rr = random.Random(seed)
        for _ in range(60):
            x, y = rr.uniform(0, top.width), rr.uniform(0, top.height)
            q = rr.uniform(2, 6) * ppm / 10
            td.ellipse([x - q, y - q, x + q, y + q], fill=(225, 232, 245, 255))
        d = ImageDraw.Draw(front)
        x = 0
        pts = [(0, 0)]
        while x < front.width:
            st = rr.uniform(4, 8) * ppm
            pts += [(x + st * 0.3, rr.uniform(1.5, 5) * ppm), (x + st * 0.7, rr.uniform(1, 3) * ppm), (x + st, rr.uniform(0.3, 1) * ppm)]
            x += st
        pts += [(front.width, 0)]
        d.polygon(pts, fill=sw)
        ImageDraw.Draw(side).polygon([(0, 0), (side.width, 0), (side.width, 2.5 * ppm), (side.width * 0.5, 4 * ppm), (0, 2 * ppm)], fill=sw)
    return dict(front=front, top=top, side=side)


def draw_block(can, P, x, y, z, variant, g="M", seed=1, loop=True):
    L, H, D = BLOCK[g]
    t = block_tex(variant, g, seed=seed)
    # Unterseiten-Schatten
    box3d.shadow(can, [P(x - 1, y, z - 1), P(x + L + 1, y, z - 1), P(x + L + 2, y, z + D + 3), P(x - 1, y, z + D + 3)], 6, alpha=160)
    box3d.put(can, t["top"], [P(x, y + H, z + D), P(x + L, y + H, z + D), P(x + L, y + H, z), P(x, y + H, z)])
    box3d.put(can, t["side"], [P(x + L, y + H, z), P(x + L, y + H, z + D), P(x + L, y, z + D), P(x + L, y, z)], shade=0.78)
    box3d.put(can, t["front"], [P(x, y + H, z), P(x + L, y + H, z), P(x + L, y, z), P(x, y, z)])
    dd = ImageDraw.Draw(can)
    cx, cz = x + L / 2, z + D / 2
    sc = abs(P(1, 0, 0)[0] - P(0, 0, 0)[0])
    yt = y + H + 0.3
    if loop:  # Satinband flach nach hinten auf den Block gelegt
        pts = [P(cx, yt, cz), P(cx + 1.5, yt, cz + 5), P(cx + 4, yt, cz + 9), P(cx + 6.5, yt, cz + 12), P(cx + 4.5, yt, cz + 13.5),
               P(cx + 2, yt, cz + 10), P(cx - 1, yt, cz + 5), P(cx, yt, cz)]
        dd.line(pts, fill=(222, 186, 106, 255), width=max(2, int(sc * 0.9)), joint="curve")
    # Messingöse (liegend sichtbar als Ring)
    ring = [P(cx + 2.2 * math.cos(a), yt + 0.2, cz + 2.2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 28)]
    dd.line(ring + [ring[0]], fill=(214, 182, 120, 255), width=max(2, int(sc * 0.8)))


# ---------------- Flächen ----------------
def lid_top(g="M", seed=11):
    d = zehner(g)
    B, T, Hh = d["deckel"]
    k = T / 77
    f = Face(f"10er {g} Deckel oben", B, T, PPM, seed=seed).bg_red()
    glitter(f.img, density=0.05, seed=seed, unit=PPM * 0.09)
    f.gold_frame(inset=2.2 * k, w=0.5 * k)
    xr = 66 * k  # Bandposition
    ribbon_band(f.img, [(xr * PPM, -10), (xr * PPM, f.Hp + 10)], 7 * k * PPM, seed)
    ribbon_band(f.img, [(-10, T * 0.5 * PPM), ((xr + 16 * k) * PPM, T * 0.5 * PPM)], 7 * k * PPM, seed + 1)
    bow(f.img, xr * PPM, (T * 0.5 - 4 * k) * PPM, 21 * k * PPM, seed=seed + 2)
    cx = (xr + 14 * k + B - 40 * k) / 2
    # Titelblock auf rotem Feld (Band verläuft dahinter): Feld abdunkeln
    pl = Image.new("L", f.img.size, 0)
    ImageDraw.Draw(pl).rounded_rectangle([(xr + 16 * k) * PPM, 7 * k * PPM, (B - 40 * k) * PPM, (T - 7 * k) * PPM], radius=int(5 * k * PPM),
                                         outline=255, width=max(2, int(0.45 * k * PPM)))
    f.img.alpha_composite(gold_layer(pl, seed))
    f.text((cx, 15.5 * k), "CHRISTBAUMPOLLER · DIE ZEHNERPACKUNG", F_CIN4, 3.4 * k, fill=CREME, shadow=False, tag="Kopf")
    f.text((cx, 29.5 * k), "Sicherheitskonzept", F_CIN, 12.5 * k, max_w=B - xr - 70 * k, tag="Titel1")
    f.text((cx, 46 * k), "für Ihr Wohnzimmer", F_VIB, 12 * k, max_w=B - xr - 80 * k, tag="Titel2")
    f.text((cx, 61 * k), "10-teilig · behördlich nicht abgenommen", F_SERIF_I, 4.4 * k, fill=CREME, wght=500, tag="Unter")
    rosette(f.img, (B - 21 * k) * PPM, T / 2 * PPM, 15.5 * k * PPM,
            [("geprüft", F_CIN, 0.30), ("nach", F_VIB, 0.30), ("Gefühl", F_CIN, 0.30)], seed=seed + 5)
    dr = ImageDraw.Draw(f.img)
    for sx, sy, sr in ((12 * k, 12 * k, 2.6), (24 * k, 22 * k, 1.2), (14 * k, 62 * k, 1.6), (110 * k, 66 * k, 1.0)):
        star(dr, sx * PPM, sy * PPM, sr * k * PPM, GOLD + (255,))
    return f


def lid_front(g="M", seed=12):
    d = zehner(g)
    B, T, Hh = d["deckel"]
    k = T / 77
    f = Face(f"10er {g} Deckel vorne", B, Hh, PPM, seed=seed).bg_red()
    glitter(f.img, density=0.05, seed=seed, unit=PPM * 0.09)
    f.gold_frame(inset=2.2 * k, w=0.5 * k)
    xr = 66 * k
    ribbon_band(f.img, [(xr * PPM, -10), (xr * PPM, f.Hp + 10)], 7 * k * PPM, seed)
    cx = (xr + 6 * k + B - 8 * k) / 2
    f.text((cx, 16 * k), "Macht hoch die Tür, die Tor macht weit", F_FRAK, 10 * k, max_w=B - xr - 26 * k, tag="Lied")
    f.text((cx + 40 * k, 31 * k), "… wir sperren trotzdem ab.", F_BRUSH, 8.5 * k, fill=CREME, rot=2, tag="Nachsatz")
    f.text((cx - 70 * k, 31 * k), "GEORG WEISSEL, 1623", F_CIN4, 2.6 * k, fill=CREME, shadow=False, tag="Quelle")
    f.text((cx, 44.5 * k), "Inhalt: 10 Christbaumpoller · Größe " + g + " · eine Variante je Packung", F_SANS, 3.0 * k, fill=CREME,
           wght=500, shadow=False, tag="Inhalt")
    dr = ImageDraw.Draw(f.img)
    for sx, sy, sr in ((20 * k, 14 * k, 3.0), (34 * k, 30 * k, 1.4), (16 * k, 40 * k, 1.8), (46 * k, 18 * k, 1.0)):
        star(dr, sx * PPM, sy * PPM, sr * k * PPM, GOLD + (255,))
    return f


def lid_side(g="M", seed=13):
    d = zehner(g)
    B, T, Hh = d["deckel"]
    k = T / 77
    f = Face(f"10er {g} Deckel rechts", T, Hh, PPM, seed=seed).bg_red()
    glitter(f.img, density=0.05, seed=seed, unit=PPM * 0.09)
    f.gold_frame(inset=2.2 * k, w=0.5 * k)
    ribbon_band(f.img, [(-10, Hh * 0.5 * PPM), (f.W + 10, Hh * 0.5 * PPM)], 7 * k * PPM, seed)
    f.text((T / 2, 13 * k), "10 SPERRSTELLEN", F_CIN, 4.6 * k, max_w=T - 12 * k, tag="Sperrstellen")
    f.text((T / 2, 37.5 * k), "#wirschaffendas", F_BRUSH, 7 * k, fill=CREME, rot=4, max_w=T - 12 * k, tag="Hashtag")
    f.text((T / 2, 46.5 * k), f"Größe {g}", F_SANS, 3.2 * k, fill=CREME, wght=600, shadow=False, tag="Größe")
    return f


def tray_tex(g="M", which="front", seed=14):
    """Bodenschale außen (sichtbar bei offenem Mockup): Rot mit Goldrand + Spruch."""
    d = zehner(g)
    k = d["T"] / 75
    if which == "front":
        f = Face(f"10er {g} Boden vorne", d["B"], d["wand"], PPM, seed=seed).bg_red()
        glitter(f.img, density=0.05, seed=seed, unit=PPM * 0.09)
        f.gold_frame(inset=1.6 * k, w=0.4 * k, double=False)
        f.text((d["B"] / 2, d["wand"] / 2), "Bitte Rettungsgasse zum Plätzchenteller freihalten.", F_BRUSH, 6.5 * k, fill=CREME, tag="Gasse")
    else:
        f = Face(f"10er {g} Boden rechts", d["T"], d["wand"], PPM, seed=seed).bg_red()
        glitter(f.img, density=0.05, seed=seed, unit=PPM * 0.09)
        f.gold_frame(inset=1.6 * k, w=0.4 * k, double=False)
        f.text((d["T"] / 2, d["wand"] / 2), "Sperrstelle 1–10", F_CIN4, 3.8 * k, fill=CREME, tag="Stelle")
    return f


def inner(w, h, seed=1, rays=False):
    img = Image.new("RGBA", (int(w * PPM), int(h * PPM)), (96, 10, 18, 255))
    if rays:
        W, H = img.size
        X, Y = np.meshgrid(np.arange(W), np.arange(H))
        ang = np.arctan2(Y - H * 1.1, X - W / 2)
        r = (0.5 + 0.5 * np.cos(ang * 60)) ** 4
        a = np.array(img).astype(np.float32)
        for c, gc in enumerate((236, 196, 110)):
            a[..., c] = a[..., c] * (1 - r * 0.35) + gc * r * 0.35
        img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    return img


def floor_tex(g="M"):
    """Boden mit Stegeinlage-Draufsicht: Fächer, Nummern „Sperrstelle“."""
    d = zehner(g)
    B, T = d["B"], d["T"]
    fb, ft = d["fach"]
    img = Image.new("RGBA", (int(B * PPM), int(T * PPM)), (70, 6, 12, 255))
    dr = ImageDraw.Draw(img)
    for r in range(2):
        for c in range(5):
            x0 = 1 + c * (fb + 1)
            z0 = 1 + r * (ft + 1)
            dr.rectangle([x0 * PPM, z0 * PPM, (x0 + fb) * PPM, (z0 + ft) * PPM], outline=GOLD + (255,), width=3)
    return img


def mockup_closed(g="M", out=None, W=2400, H=1350):
    d = zehner(g)
    B, T, Hh = d["deckel"]
    top, fr, sd = lid_top(g), lid_front(g), lid_side(g)
    S = 2
    dist = 1800
    cam = box3d.Cam(yaw=20, pitch=-34, dist=dist, f=(W * S * 0.80 / B) * dist, cx=W * S * 0.49, cy=H * S * 0.50)
    can = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    ox, oy, oz = -B / 2, -Hh / 2, -T / 2
    P = lambda x, y, z: cam.p(x + ox, y + oy, z + oz)
    box3d.shadow(can, [P(0, 0, 0), P(B, 0, 0), P(B + 8, 0, T + 20), P(8, 0, T + 24)], 30 * S, alpha=190)
    box3d.shadow(can, [P(-3, 0, -2), P(B + 3, 0, -2), P(B + 3, 0, T + 3), P(-3, 0, T + 3)], 6 * S, alpha=210)
    box3d.put(can, top.img, [P(0, Hh, T), P(B, Hh, T), P(B, Hh, 0), P(0, Hh, 0)], shade=1.08)
    box3d.put(can, sd.img, [P(B, Hh, 0), P(B, Hh, T), P(B, 0, T), P(B, 0, 0)], shade=0.72)
    box3d.put(can, fr.img, [P(0, Hh, 0), P(B, Hh, 0), P(B, 0, 0), P(0, 0, 0)])
    dd = ImageDraw.Draw(can)
    dd.line([P(0, Hh, 0), P(B, Hh, 0)], fill=(255, 230, 200, 110), width=2 * S)
    can = can.resize((W, H), Image.LANCZOS)
    if out:
        scene(can).convert("RGB").save(out, quality=92)
    return can


def mockup_open(g="M", out=None, W=2400, H=1500, variants=MIX):
    d = zehner(g)
    B, T, Hi, wand = d["B"], d["T"], d["H"], d["wand"]
    LB, TD, LH = d["deckel"]
    fb, ft = d["fach"]
    L, Hb, D = BLOCK[g]
    S = 2
    dist = 1700
    cam = box3d.Cam(yaw=22, pitch=-26, dist=dist, f=(W * S * 0.68 / B) * dist, cx=W * S * 0.50, cy=H * S * 0.60)
    can = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    ox, oy, oz = -B / 2, -10, -T / 2 - 20
    P = lambda x, y, z: cam.p(x + ox, y + oy, z + oz)
    # Deckel hinten angelehnt (Oberseite zur Kamera, um 72° aufgestellt)
    top = lid_top(g)
    ang = math.radians(72)
    zb = T + 10
    yb = 0
    hx = lambda u: (zb + TD * math.cos(ang) * (1 - u), yb + TD * math.sin(ang) * (1 - u))
    z_top, y_top = zb + TD * math.cos(ang) * 0 + 0, yb + TD * math.sin(ang)
    box3d.shadow(can, [P(-2, 0, zb), P(LB, 0, zb), P(LB + 6, 0, zb + 30), P(4, 0, zb + 30)], 20 * S, alpha=170)
    # Deckel: obere Kante hinten oben, untere Kante vorne am Boden (Rückseite der Schale)
    box3d.put(can, top.img, [P(-1, y_top, zb + TD * math.cos(ang)), P(LB - 1, y_top, zb + TD * math.cos(ang)), P(LB - 1, 0, zb), P(-1, 0, zb)],
              shade=1.0)
    # Schale innen
    box3d.shadow(can, [P(0, 0, 0), P(B, 0, 0), P(B + 6, 0, T + 10), P(6, 0, T + 12)], 22 * S, alpha=200)
    box3d.put(can, inner(B, wand, rays=True), [P(0, wand, T), P(B, wand, T), P(B, 0, T), P(0, 0, T)], shade=0.9)
    box3d.put(can, inner(T, wand), [P(0, wand, 0), P(0, wand, T), P(0, 0, T), P(0, 0, 0)], shade=0.75)
    box3d.put(can, floor_tex(g), [P(0, 0.2, T), P(B, 0.2, T), P(B, 0.2, 0), P(0, 0.2, 0)], shade=0.9)
    # Stegeinlage: Längssteg Mitte + Querstege (dünne Wände)
    stc = (120, 14, 24, 255)
    for c in range(1, 5):
        x = 1 + c * (fb + 1) - 1
        box3d.put(can, Image.new("RGBA", (40, 40), stc), [P(x, d["steg_h"], T), P(x, d["steg_h"], 0), P(x, 0, 0), P(x, 0, T)], shade=0.8)
    # Poller: hintere Reihe zuerst, links nach rechts
    order = []
    for r in (1, 0):
        for c in range(5):
            order.append((r, c))
    for i, (r, c) in enumerate(order):
        vi = (1 - r) * 5 + c
        x = 1 + c * (fb + 1) + (fb - L) / 2
        z = 1 + r * (ft + 1) + (ft - D) / 2
        draw_block(can, P, x, 0.3, z, variants[vi % len(variants)], g, seed=20 + vi)
    # Längssteg vorne (zwischen den Reihen) – nach hinterer Reihe gezeichnet
    # Schale außen: Vorderwand, rechte Wand
    trf, trr = tray_tex(g, "front"), tray_tex(g, "right")
    box3d.put(can, trr.img, [P(B, wand, 0), P(B, wand, T), P(B, 0, T), P(B, 0, 0)], shade=0.72)
    box3d.put(can, trf.img, [P(0, wand, 0), P(B, wand, 0), P(B, 0, 0), P(0, 0, 0)])
    dd = ImageDraw.Draw(can)
    dd.line([P(0, wand, 0), P(B, wand, 0), P(B, wand, T)], fill=(255, 225, 190, 140), width=2 * S)
    can = can.resize((W, H), Image.LANCZOS)
    if out:
        scene(can).convert("RGB").save(out, quality=92)
    return can


if __name__ == "__main__":
    import time
    t = time.time()
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("zu", "both"):
        mockup_closed("M", out="/home/claude/cbp/pack/mock_10er_zu.jpg")
    if which in ("auf", "both"):
        mockup_open("M", out="/home/claude/cbp/pack/mock_10er_offen.jpg")
    for fc in (lid_top(), lid_front(), lid_side(), tray_tex("M", "front"), tray_tex("M", "right")):
        fc.check()
    print(round(time.time() - t, 1), "s")
