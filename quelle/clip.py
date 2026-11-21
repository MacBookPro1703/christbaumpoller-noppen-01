"""Rendert den Spot. Aufruf: python3 clip.py quer|hoch [frame_sekunden für Testbild]"""
import sys, subprocess, os, math, random
sys.path.insert(0, os.path.dirname(__file__))
from engine import *

MODE = sys.argv[1]
W, H = (1920, 1080) if MODE == "quer" else (1080, 1920)
FPS = 30
DUR = 23.0
U = min(W, H) / 1080  # Basiseinheit
VERT = H > W
rng = random.Random(7)

# ---------- Fonts ----------
f_cap = font(F_SERIF_I, int(64 * U), 500)
f_cap2 = font(F_SERIF_I, int(54 * U), 450)
f_title = font(F_BLACK, int((118 if not VERT else 84) * U))
f_slog = font(F_SERIF_I, int(50 * U), 500)
f_small = font(F_SANS, int(30 * U), 500)
f_brand = font(F_SANS, int(34 * U), 650)

# ---------- Szene A: Weihnachtsmarkt ----------
def build_market():
    ww = W + int(200 * U)
    bg = vgrad(ww, H, (8, 12, 32), (46, 30, 36))
    d = ImageDraw.Draw(bg)
    ground = int(H * (0.80 if not VERT else 0.70))
    # Buden
    lights = []
    x = -40
    while x < ww:
        bw = rng.randint(int(230 * U), int(330 * U))
        bh = rng.randint(int(150 * U), int(210 * U))
        top = ground - bh - int(40 * U)
        col = (34, 24, 26)
        d.rectangle([x, top, x + bw, ground], fill=col)
        d.polygon([(x - 18 * U, top), (x + bw / 2, top - 90 * U), (x + bw + 18 * U, top)], fill=(48, 30, 30))
        # Schnee auf dem Dach
        d.polygon([(x - 18 * U, top), (x + bw / 2, top - 90 * U), (x + bw + 18 * U, top), (x + bw / 2, top - 74 * U)], fill=(210, 214, 226))
        # Theke leuchtet
        d.rectangle([x + 16 * U, top + 40 * U, x + bw - 16 * U, top + bh * 0.62], fill=(232, 150, 70))
        d.rectangle([x + 16 * U, top + 40 * U, x + bw - 16 * U, top + 56 * U], fill=(250, 200, 120))
        for k in range(9):
            lx = x + bw / 2 + (k - 4) / 4 * (bw / 2 + 18 * U)
            ly = top - 90 * U * (1 - abs(k - 4) / 4) + 6 * U
            lights.append((lx, ly, rng.random() * 6.28, (255, 205, 130)))
        x += bw + rng.randint(int(30 * U), int(90 * U))
    glowlayer = bg.filter(ImageFilter.GaussianBlur(int(26 * U)))
    bg = ImageChops.screen(bg, glowlayer)
    d = ImageDraw.Draw(bg)
    # Boden (Schnee)
    g = vgrad(ww, H - ground, (196, 200, 214), (120, 118, 132))
    bg.alpha_composite(g, (0, ground))
    # Unschärfe für Tiefe
    bg = bg.filter(ImageFilter.GaussianBlur(2.2 * U))
    # große Poller im Vordergrund
    blocks = []
    order = ["gelb", "bescherung", "rot", "gelb", "weiss", "bescherung", "gelb", "rot"]
    n = 5 if not VERT else 3
    bwid = int((ww * 0.95) / n)
    for i in range(n + 1):
        spr = block(order[i % len(order)], size=int(bwid * 0.92), hang=False, seed=i)
        bx = int(i * bwid * 1.02 - bwid * 0.15)
        by = int(H * (0.93 if not VERT else 0.86)) - spr.height
        # Schatten
        sh = Image.new("RGBA", (spr.width, int(40 * U)), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([spr.width * 0.08, 0, spr.width * 0.9, 40 * U], fill=(20, 16, 30, 140))
        bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), (bx, by + spr.height - int(26 * U)))
        bg.alpha_composite(spr, (bx, by))
    return bg, lights

# ---------- Szene B: Wohnzimmer mit Baum ----------
def build_room():
    bg = vgrad(W, H, (34, 20, 18), (14, 10, 12))
    # Bokeh im Hintergrund
    bok = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for _ in range(26):
        r = int(rng.uniform(40, 110) * U)
        sp = glow_sprite(r, rng.choice([(255, 170, 80), (255, 210, 140), (200, 120, 60)]), core=0.9)
        sp.putalpha(sp.split()[3].point(lambda v: int(v * 0.35)))
        bok.alpha_composite(sp, (rng.randint(-r, W - r), rng.randint(-r, int(H * 0.8))))
    bg.alpha_composite(bok.filter(ImageFilter.GaussianBlur(6 * U)))
    # Fenster mit Nacht
    if not VERT:
        wx, wy, wwid, whei = int(W * 0.07), int(H * 0.12), int(W * 0.24), int(H * 0.56)
    else:
        wx, wy, wwid, whei = int(W * 0.06), int(H * 0.17), int(W * 0.30), int(H * 0.20)
    win = vgrad(wwid, whei, (10, 18, 46), (34, 44, 82))
    wd = ImageDraw.Draw(win)
    for _ in range(70):
        sx, sy, sr = rng.random() * wwid, rng.random() * whei, rng.uniform(1, 3.2) * U
        wd.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(230, 236, 255, 220))
    wd.rectangle([0, whei * 0.86, wwid, whei], fill=(170, 180, 205))
    bg.alpha_composite(win, (wx, wy))
    d = ImageDraw.Draw(bg)
    fr = int(14 * U)
    d.rectangle([wx, wy, wx + wwid, wy + whei], outline=(70, 46, 34), width=fr)
    d.line([(wx + wwid / 2, wy), (wx + wwid / 2, wy + whei)], fill=(70, 46, 34), width=fr)
    d.line([(wx, wy + whei * 0.45), (wx + wwid, wy + whei * 0.45)], fill=(70, 46, 34), width=fr)
    # Boden
    fl = int(H * 0.86)
    bg.alpha_composite(vgrad(W, H - fl, (58, 34, 24), (30, 18, 14)), (0, fl))
    # Baum
    if not VERT:
        tw, th = int(W * 0.40), int(H * 0.98)
        tx = int(W * 0.56)
    else:
        tw, th = int(W * 0.92), int(H * 0.68)
        tx = int(W * 0.04)
    tr, tl, star = tree(tw, th, seed=11)
    ty = fl - th + int(20 * U)
    bg.alpha_composite(tr, (tx, ty))
    lights = [(tx + x, ty + y, ph, c) for x, y, ph, c in tl]
    # Geschenke unter dem Baum
    for k, (vk, s) in enumerate([("bescherung", 0.15), ("rot-glanz", 0.11), ("gold-glanz-schnee", 0.10)]):
        spr = block(vk, size=int(W * s if not VERT else W * s * 1.6), hang=False, seed=20 + k)
        gx = tx + int(tw * (0.12 + 0.3 * k))
        bg.alpha_composite(spr, (gx, fl + int(30 * U) - spr.height + k * int(12 * U)))
    # Anhänger-Positionen auf dem Baum
    hangers = []
    spots = [(0.50, 0.30, "gold-glanz"), (0.33, 0.49, "rot-glanz-schnee"), (0.67, 0.46, "silber-glanz"), (0.24, 0.69, "gold-matt-schnee"),
             (0.55, 0.63, "rot-matt"), (0.77, 0.71, "silber-glanz-schnee"), (0.44, 0.82, "rot-glanz")]
    for i, (fx, fy, vk) in enumerate(spots):
        size = int(tw * (0.24 if i else 0.30))
        hangers.append((tx + fx * tw, ty + fy * th, pad_for_rotation(block(vk, size=size, seed=30 + i)), rng.random() * 6.28))
    star_xy = (tx + star[0], ty + star[1])
    return bg, lights, hangers, star_xy

# ---------- Szene C: Endkarte ----------
def build_end():
    bg = Image.new("RGBA", (W, H), BG + (255,))
    rg = glow_sprite(int(max(W, H) * 0.55), (120, 92, 52), core=0.01)
    rg.putalpha(rg.split()[3].point(lambda v: int(v * 0.55)))
    bg.alpha_composite(rg, (W // 2 - rg.width // 2, int(H * (0.30 if not VERT else 0.30)) - rg.height // 2))
    logo = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img", "ep.png")).convert("RGBA").resize((int(84 * U), int(84 * U)), Image.LANCZOS)
    hangs = []
    keys = ["rot-glanz", "gold-glanz-schnee", "silber-glanz"]
    for i, k in enumerate(keys):
        size = int((W * 0.17) if not VERT else W * 0.30)
        fx = [0.30, 0.50, 0.70][i] if not VERT else [0.2, 0.5, 0.8][i]
        top = H * (0.10 if not VERT else 0.22) + [30, 0, 50][i] * U
        hangs.append((W * fx, top, pad_for_rotation(block(k, size=size, seed=40 + i)), i * 1.7))
    return bg, logo, hangs

def draw_lights(frame, lights, t, scale=1.0, sprites={}):
    for x, y, ph, c in lights:
        b = 0.55 + 0.45 * math.sin(t * 2.2 + ph)
        lvl = int(b * 3.99)
        key = (c, lvl)
        if key not in sprites:
            sp = glow_sprite(int(16 * U * scale), c)
            sp.putalpha(sp.split()[3].point(lambda v, l=lvl: int(v * (0.35 + 0.65 * l / 3))))
            sprites[key] = sp
        sp = sprites[key]
        frame.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))

print("baue Kulissen …", flush=True)
MKT, MKT_L = build_market()
ROOM, ROOM_L, HANG, STAR = build_room()
END, LOGO, ENDH = build_end()
snow = Snow(W, H, n=int(260 if not VERT else 300), big=1.0)
snow2 = Snow(W, H, n=90, seed=9, big=0.7)

A_END, B_START, B_END, C_START = 8.0, 7.2, 15.8, 15.0

def scene_a(t):
    shift = int(ease(t / 8.0) * 160 * U)
    f = MKT.crop((shift, 0, shift + W, H))
    lt = [(x - shift, y, ph, c) for x, y, ph, c in MKT_L]
    draw_lights(f, lt, t, 0.8)
    snow.draw(f, t)
    cy = H * (0.30 if not VERT else 0.27)
    a1 = fade(t, 0.5, 3.6)
    if a1: f.alpha_composite(text_layer((W, H), [("Alle Jahre wieder.", f_cap, CREAM)], (W / 2, cy), a1))
    a2 = fade(t, 3.9, 7.8)
    if a2:
        if not VERT:
            lines = [("Glühwein. Lichterglanz.", f_cap, CREAM), ("Und an jeder Zufahrt: ein Poller.", f_cap, (238, 205, 150))]
        else:
            lines = [("Glühwein.", f_cap, CREAM), ("Lichterglanz.", f_cap, CREAM), ("Und an jeder Zufahrt:", f_cap, (238, 205, 150)), ("ein Poller.", f_cap, (238, 205, 150))]
        f.alpha_composite(text_layer((W, H), lines, (W / 2, cy), a2))
    return f

def scene_b(t):
    lt = t - B_START
    f = ROOM.copy()
    draw_lights(f, ROOM_L, t, 1.0)
    # Sternglanz
    sg = glow_sprite(int(70 * U), (255, 214, 140), core=0.15)
    sg.putalpha(sg.split()[3].point(lambda v: int(v * (0.55 + 0.25 * math.sin(t * 1.5)))))
    f.alpha_composite(sg, (int(STAR[0] - sg.width / 2), int(STAR[1] - sg.height / 2)))
    for i, (x, y, pad, ph) in enumerate(HANG):
        ang = math.sin(t * 1.6 + ph) * (7 if i else 9) * math.exp(-max(0, lt - 6) * 0.1)
        place_swing(f, pad, x, y, ang)
    snow2.draw(f, t) if False else None
    # langsamer Zoom auf den Hauptanhänger
    z = 1 + 0.10 * ease(lt / 8.6)
    fx, fy = HANG[0][0], HANG[0][1] + 80 * U
    nw, nh = W / z, H / z
    l = min(max(fx - nw / 2, 0), W - nw); tt = min(max(fy - nh / 2, 0), H - nh)
    f = f.crop((int(l), int(tt), int(l + nw), int(tt + nh))).resize((W, H), Image.BILINEAR)
    if not VERT:
        cx, cy = W * 0.28, H * 0.80
    else:
        cx, cy = W / 2, H * 0.10
    a1 = fade(lt, 0.9, 4.4)
    if a1:
        lines = [("Was uns draußen schützt,", f_cap2, CREAM), ("ist längst Tradition.", f_cap2, CREAM)]
        f.alpha_composite(text_layer((W, H), lines, (cx, cy), a1))
    a2 = fade(lt, 4.7, 8.5)
    if a2:
        lines = [("Jetzt auch", f_cap2, (238, 205, 150)), ("für Ihren Baum.", f_cap2, (238, 205, 150))]
        f.alpha_composite(text_layer((W, H), lines, (cx, cy), a2))
    return f

def scene_c(t):
    lt = t - C_START
    f = END.copy()
    for i, (x, y, pad, ph) in enumerate(ENDH):
        ang = math.sin(t * 1.4 + ph) * 6
        ImageDraw.Draw(f).line([(x, 0), (x, y)], fill=(215, 190, 140, 255), width=max(2, int(3 * U)))
        place_swing(f, pad, x, y, ang)
    snow2.draw(f, t)
    ty = H * (0.66 if not VERT else 0.64)
    a = ease((lt - 0.6) / 1.0)
    if a > 0:
        f.alpha_composite(text_layer((W, H), [("CHRISTBAUMPOLLER", f_title, CREAM)], (W / 2, ty), a))
    a = ease((lt - 1.5) / 1.0)
    if a > 0:
        f.alpha_composite(text_layer((W, H), [("Ein Stück Sicherheitsgefühl für zu Hause.", f_slog if not VERT else f_cap2, BRONZE)], (W / 2, ty + 120 * U), a))
    a = ease((lt - 3.0) / 1.0)
    if a > 0:
        f.alpha_composite(text_layer((W, H), [("Wir schaffen das. Mit Sicherheitsabstand.", f_small, (159, 170, 176))], (W / 2, ty + 195 * U), a, shadow=False))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        by = int(H * (0.94 if not VERT else 0.92))
        lay.alpha_composite(LOGO, (int(W / 2 - 150 * U), by - LOGO.height // 2))
        ImageDraw.Draw(lay).text((W / 2 - 150 * U + LOGO.width + 22 * U, by), "Ebbing Project", font=f_brand, fill=CREAM + (255,), anchor="lm")
        lay.putalpha(lay.split()[3].point(lambda v: int(v * a)))
        f.alpha_composite(lay)
    # Ausblenden am Ende
    if t > DUR - 0.8:
        k = (DUR - t) / 0.8
        f = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), f, max(0, k))
    return f

def frame_at(t):
    if t < B_START:
        f = scene_a(t)
    elif t < A_END:
        k = ease((t - B_START) / (A_END - B_START))
        f = Image.blend(scene_a(t), scene_b(t), k)
    elif t < C_START:
        f = scene_b(t)
    elif t < B_END:
        k = ease((t - C_START) / (B_END - C_START))
        f = Image.blend(scene_b(t), scene_c(t), k)
    else:
        f = scene_c(t)
    if t < 0.6:
        f = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), f, t / 0.6)
    return f.convert("RGB")

if len(sys.argv) > 2:
    for s in sys.argv[2].split(","):
        frame_at(float(s)).save(f"./test_{MODE}_{s}.jpg", quality=85)
    sys.exit()

out_tmp = f"./_{MODE}_tmp.mp4"
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out_tmp], stdin=subprocess.PIPE)
N = int(DUR * FPS)
for i in range(N):
    p.stdin.write(frame_at(i / FPS).tobytes())
    if i % 90 == 0:
        print(f"{MODE}: {i}/{N}", flush=True)
p.stdin.close()
if p.wait() == 0:
    os.rename(out_tmp, f"./{MODE}_stumm.mp4")
    print("fertig", flush=True)
