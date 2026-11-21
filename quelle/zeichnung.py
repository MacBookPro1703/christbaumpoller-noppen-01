"""Technische Zeichnungen Christbaumpoller S/M/L – A4 quer, Maßstab 1:1 in mm, Erstwinkel-Projektion."""
import sys, os, io
sys.path.insert(0, os.path.dirname(__file__))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Circle, Rectangle, FancyBboxPatch
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D
import numpy as np
from engine import block, BLOCK
from PIL import Image

plt.rcParams["font.family"] = "DejaVu Sans"
SCRIPT = FontProperties(fname=os.path.join(os.path.dirname(__file__), "fonts", "CaveatBrush.ttf"))
INK, DIM, RED, GOLD, HID = "#1b1e22", "#1a4f9c", "#b81c26", "#c9a24a", "#777777"

# Maße in mm – Summen der Längsteilung geprüft (Fuß + Tasche + Mittelfuß + Tasche + Fuß = L)
SIZES = {
    "S": dict(L=50, H=25, D=23, a=6.5, w=13.5, wt=12, m=10, h=5.5, ax=(13.5, 36.5), ad=4.5, adep=1.0,
              eo=5, ewire=0.8, eh=5.5, tw=43, th=7, tc=10, wt_g=12, ch=0.3),
    "M": dict(L=70, H=35, D=32, a=9, w=19, wt=17, m=14, h=8, ax=(19, 51), ad=6, adep=1.5,
              eo=6, ewire=0.8, eh=7, tw=60, th=10, tc=14, wt_g=30, ch=0.5),
    "L": dict(L=90, H=45, D=41, a=11.5, w=24.5, wt=22, m=18, h=10.5, ax=(24.5, 65.5), ad=7.5, adep=2.0,
              eo=7, ewire=1.0, eh=8.5, tw=77, th=13, tc=18, wt_g=55, ch=0.5),
}
for k, s in SIZES.items():
    assert abs(2 * s["a"] + 2 * s["w"] + s["m"] - s["L"]) < 1e-6, k
RIBBON = "gold satin ribbon, width 3 mm, closed loop\n120 mm (240 mm cut length), knotted,\npre-attached to the eyelet"


def dim_h(ax, x1, x2, y, yref, txt, above=True, fs=7):
    ax.plot([x1, x1], [yref, y + (1.2 if above else -1.2)], color=DIM, lw=0.4)
    ax.plot([x2, x2], [yref, y + (1.2 if above else -1.2)], color=DIM, lw=0.4)
    ax.annotate("", xy=(x1, y), xytext=(x2, y), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.6, shrinkA=0, shrinkB=0, mutation_scale=6))
    ax.text((x1 + x2) / 2, y + (0.8 if above else -0.8), txt, ha="center", va="bottom" if above else "top", fontsize=fs, color=DIM)


def dim_v(ax, y1, y2, x, xref, txt, left=True, fs=7):
    ax.plot([xref, x + (-1.2 if left else 1.2)], [y1, y1], color=DIM, lw=0.4)
    ax.plot([xref, x + (-1.2 if left else 1.2)], [y2, y2], color=DIM, lw=0.4)
    ax.annotate("", xy=(x, y1), xytext=(x, y2), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.6, shrinkA=0, shrinkB=0, mutation_scale=6))
    ax.text(x + (-0.8 if left else 0.8), (y1 + y2) / 2, txt, ha="right" if left else "left", va="center", fontsize=fs, color=DIM, rotation=90, rotation_mode="anchor") if False else \
        ax.text(x + (-0.8 if left else 0.8), (y1 + y2) / 2, txt, ha="right" if left else "left", va="center", fontsize=fs, color=DIM)


def front_poly(s, x0, y0):
    L, H, a, w, wt, m, h = s["L"], s["H"], s["a"], s["w"], s["wt"], s["m"], s["h"]
    d = (w - wt) / 2
    p1a, p1b = x0 + a, x0 + a + w
    p2a, p2b = p1b + m, p1b + m + w
    return [(x0, y0), (p1a, y0), (p1a + d, y0 + h), (p1b - d, y0 + h), (p1b, y0), (p2a, y0), (p2a + d, y0 + h), (p2b - d, y0 + h),
            (p2b, y0), (x0 + L, y0), (x0 + L, y0 + H), (x0, y0 + H)]


def script_text(ax, s, x0, y0, txt="#wirschaffendas"):
    tp = TextPath((0, 0), txt, size=10, prop=SCRIPT)
    bb = tp.get_extents()
    sc = s["tw"] / bb.width
    cx, cy = x0 + s["L"] / 2, y0 + s["H"] - s["tc"]
    tr = Affine2D().translate(-bb.x0 - bb.width / 2, -bb.y0 - bb.height / 2).scale(sc).rotate_deg(4).translate(cx, cy)
    ax.add_patch(PathPatch(tr.transform_path(tp), color=RED, lw=0))
    # Druckfeld
    ax.add_patch(Rectangle((cx - s["tw"] / 2, cy - s["th"] / 2), s["tw"], s["th"], fill=False, ls=(0, (2, 1.5)), lw=0.4, ec=HID))
    return cx, cy


def sheet(pdf, size):
    s = SIZES[size]
    L, H, D = s["L"], s["H"], s["D"]
    fig = plt.figure(figsize=(297 / 25.4, 210 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((8, 8), 281, 194, fill=False, lw=0.8, ec=INK))
    ax.text(14, 196, f"CHRISTBAUMPOLLER – size {size}  ·  {L} × {H} × {D} mm", fontsize=13, weight="bold", color=INK, va="top")
    ax.text(14, 189, "Christmas tree ornament · scale 1:1 when printed on A4 at 100 % · all dimensions in mm · first-angle projection",
            fontsize=7.5, color=HID, va="top")

    # ---------- Vorderansicht ----------
    fx, fy = 30, 98
    ax.add_patch(Polygon(front_poly(s, fx, fy), closed=True, fc="#f3ead6", ec=INK, lw=0.9))
    script_text(ax, s, fx, fy)
    # Transportanker (verdeckt) in der Vorderansicht
    for axx in s["ax"]:
        ax.add_patch(Rectangle((fx + axx - s["ad"] / 2, fy + H - s["adep"]), s["ad"], s["adep"], fill=False, ls="--", lw=0.4, ec=HID))
    # Öse + Band
    ex, ey = fx + L / 2, fy + H
    stem = 2.0
    ax.add_patch(Rectangle((ex - 0.6, ey), 1.2, stem, fc=GOLD, ec=INK, lw=0.4))
    ax.add_patch(Circle((ex, ey + stem + s["eo"] / 2), s["eo"] / 2, fill=False, ec=GOLD, lw=2.2))
    ax.add_patch(Circle((ex, ey + stem + s["eo"] / 2), s["eo"] / 2, fill=False, ec=INK, lw=0.3))
    rt = ey + stem + s["eo"] - 1
    top = ey + 34
    ax.plot([ex - 0.9, ex - 0.4], [rt, top], color=GOLD, lw=2.0)
    ax.plot([ex + 0.9, ex + 0.4], [rt, top], color=GOLD, lw=2.0)
    ax.plot([ex - 4, ex - 1, ex + 1, ex + 4], [top + 1, top + 2.5, top - 0.5, top + 1], color=INK, lw=0.5)  # Bruchlinie
    ax.text(ex + 4, top - 6, "ribbon loop\n120 mm (shortened)", fontsize=6.5, color=INK, va="center")
    ax.text(fx, fy + H + 2, "FRONT VIEW", fontsize=7.5, weight="bold", color=INK, va="bottom")
    # Maße Front
    dim_h(ax, fx, fx + L, fy - 9, fy, f"{L}", above=False)
    xs = [fx, fx + s["a"], fx + s["a"] + s["w"], fx + s["a"] + s["w"] + s["m"], fx + L - s["a"], fx + L]
    labels = [s["a"], s["w"], s["m"], s["w"], s["a"]]
    for i in range(5):
        dim_h(ax, xs[i], xs[i + 1], fy - 4, fy, f"{labels[i]:g}", above=False, fs=6)
    dim_v(ax, fy, fy + H, fx - 5, fx, f"{H}")
    dim_v(ax, fy, fy + s["h"], fx + L + 4, fx + L, f"{s['h']:g}", left=False, fs=6)
    ax.text(fx + s["a"] + s["w"] / 2, fy + s["h"] + 1.2, f"top {s['wt']:g}", fontsize=5.5, color=DIM, ha="center")
    dim_v(ax, ey, ey + stem + s["eo"], ex + s["eo"] / 2 + 6, ex, f"{stem + s['eo']:g}", left=False, fs=6)
    ax.text(ex - s["eo"] / 2 - 1, ey + stem + s["eo"] + 0.6, f"Ø{s['eo']:g}", fontsize=6, color=DIM, ha="right", va="bottom")
    dim_v(ax, fy + H - s["tc"], fy + H, fx + L + 12, fx + L, f"{s['tc']:g}", left=False, fs=6)

    # ---------- Seitenansicht (links, Erstwinkel rechts daneben) ----------
    sx, sy = fx + L + 26, fy
    ax.add_patch(Rectangle((sx, sy), D, H, fc="#e9dfc6", ec=INK, lw=0.9))
    ax.plot([sx, sx + D], [sy + s["h"], sy + s["h"]], ls="--", lw=0.5, color=HID)
    ax.text(sx + D / 2, sy + s["h"] / 2, "pocket through", fontsize=5.5, color=HID, ha="center", va="center")
    ax.add_patch(Rectangle((sx + D / 2 - 0.6, sy + H), 1.2, stem, fc=GOLD, ec=INK, lw=0.4))
    ax.add_patch(Circle((sx + D / 2, sy + H + stem + s["eo"] / 2), s["eo"] / 2, fill=False, ec=GOLD, lw=2.2))
    dim_h(ax, sx, sx + D, sy - 9, sy, f"{D}", above=False)
    ax.text(sx, sy + H + stem + s["eo"] + 2.5, "SIDE VIEW", fontsize=7.5, weight="bold", color=INK, va="bottom")
    ax.text(sx + D / 2, sy - 16, "forklift pockets run through\nthe full depth", fontsize=6, color=INK, ha="center", va="top")

    # ---------- Draufsicht (unter der Vorderansicht) ----------
    tx, ty = fx, fy - 30 - D
    ax.add_patch(Rectangle((tx, ty), L, D, fc="#f6efe0", ec=INK, lw=0.9))
    for axx in s["ax"]:
        ax.add_patch(Circle((tx + axx, ty + D / 2), s["ad"] / 2, fc="#cfc7b6", ec=INK, lw=0.5))
        ax.add_patch(Circle((tx + axx, ty + D / 2), s["ad"] / 4, fc="#8a857c", ec=INK, lw=0.3))
    ax.add_patch(Circle((tx + L / 2, ty + D / 2), 1.6, fc=GOLD, ec=INK, lw=0.4))
    ax.text(tx, ty + D + 2, "TOP VIEW", fontsize=7.5, weight="bold", color=INK, va="bottom")
    dim_h(ax, tx, tx + s["ax"][0], ty - 4, ty, f"{s['ax'][0]:g}", above=False, fs=6)
    dim_h(ax, tx, tx + L / 2, ty - 9, ty, f"{L / 2:g}", above=False, fs=6)
    dim_h(ax, tx, tx + s["ax"][1], ty - 14, ty, f"{s['ax'][1]:g}", above=False, fs=6)
    dim_v(ax, ty, ty + D / 2, tx - 5, tx, f"{D / 2:g}", fs=6)
    dim_v(ax, ty, ty + D, tx - 11, tx, f"{D}")
    ax.annotate(f"2× lifting anchor recess\nØ{s['ad']:g}, depth {s['adep']:g}", xy=(tx + s["ax"][1] + s["ad"] / 2, ty + D / 2),
                xytext=(tx + L + 4, ty + D * 0.75), fontsize=5.8, color=DIM, va="center",
                arrowprops=dict(arrowstyle="-", color=DIM, lw=0.4))
    ax.annotate("eyelet, centred", xy=(tx + L / 2, ty + D / 2 - 1.6), xytext=(tx + L + 4, ty + D * 0.25), fontsize=5.8, color=DIM, va="center",
                arrowprops=dict(arrowstyle="-", color=DIM, lw=0.4))

    # ---------- Render ----------
    img = block("gold-glanz", size=900, seed=3)
    img = img.crop(img.getbbox())
    bw, bh = 62, 50
    iw = min(bw, bh * img.width / img.height); ih = iw * img.height / img.width
    x0r = 245 - iw / 2
    ax.imshow(np.array(img), extent=(x0r, x0r + iw, 184 - ih, 184), zorder=3)
    ax.text(245, 131, f"reference render (size {size}, gold glossy)", fontsize=6, color=HID, ha="center", va="top")

    # ---------- Spezifikation ----------
    spec = [
        ("Body", f"{L} × {H} × {D} mm, edges\nchamfered/rounded {s['ch']:g} mm"),
        ("Forklift pockets", f"2×, through the full depth;\nwidth {s['w']:g} (bottom) / {s['wt']:g} (top),\nheight {s['h']:g}"),
        ("Feet", f"outer {s['a']:g} mm, middle {s['m']:g} mm"),
        ("Lifting anchors", f"2× round recess Ø{s['ad']:g}, depth {s['adep']:g},\nat {s['ax'][0]:g} and {s['ax'][1]:g} mm, centred in depth"),
        ("Eyelet", f"brass colour, ring Ø{s['eo']:g} outer, wire Ø{s['ewire']:g},\nheight {stem + s['eo']:g} above top, fixed min. 3 mm\ndeep, pull test ≥ 2 kg"),
        ("Ribbon", RIBBON),
        ("Print", f"\"#wirschaffendas\", brush script (font Caveat\nBrush, vector file supplied), print field\n{s['tw']:g} × {s['th']:g} mm, centre {s['tc']:g} mm below top\nedge, rotated +4°, pad print"),
        ("Weight", f"max. {s['wt_g']} g incl. eyelet and ribbon"),
        ("Tolerance", "general ± 0.3 mm (S, M), ± 0.5 mm (L);\ntext position ± 1 mm"),
    ]
    yy = 117
    ax.text(204, yy + 3, "SPECIFICATION", fontsize=8, weight="bold", color=INK, va="bottom")
    for k, v in spec:
        ax.text(204, yy, k, fontsize=5.9, weight="bold", color=INK, va="top")
        ax.text(230, yy, v, fontsize=5.9, color=INK, va="top")
        yy -= 4.0 + 2.9 * v.count("\n")

    # ---------- Schriftfeld ----------
    tb = [("Project", "Christbaumpoller"), ("Part", f"Ornament size {size}"), ("Material", "polyresin / rigid PU foam / ABS-PS"),
          ("Units / scale", "mm · 1:1 on A4"), ("Rev / date", "A · 20.11.2026"), ("Customer", "Ebbing Project GmbH, 46348 Raesfeld, Germany")]
    ax.add_patch(Rectangle((204, 12), 81, 27, fill=False, ec=INK, lw=0.6))
    for i, (k, v) in enumerate(tb):
        y = 36 - i * 4.2
        ax.text(206, y, k, fontsize=5.8, color=HID, va="center")
        ax.text(225, y, v, fontsize=6.2, color=INK, va="center", weight="bold" if i < 2 else "normal")
    # 1:1-Prüfmaß
    ax.plot([140, 190], [14, 14], color=INK, lw=0.8)
    for x in range(140, 191, 10):
        ax.plot([x, x], [13, 15], color=INK, lw=0.6)
    ax.text(140, 16.5, "check scale: 50 mm", fontsize=6, color=INK)
    check(fig, ax, f"sheet {size}")
    pdf.savefig(fig)
    plt.close(fig)


PROBLEMS = []
def check(fig, ax, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    boxes = []
    for t in ax.texts:
        if not t.get_text().strip():
            continue
        bb = t.get_window_extent(r)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        if x0 < 8.5 or x1 > 288.5 or y0 < 8.5 or y1 > 201.5:
            PROBLEMS.append(f"{name}: outside frame: {t.get_text()[:40]!r} x {x0:.1f}-{x1:.1f} y {y0:.1f}-{y1:.1f}")
        boxes.append((x0, y0, x1, y1, t.get_text()[:30]))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 0.3 and oy > 0.3:
                PROBLEMS.append(f"{name}: overlap {a[4]!r} / {b[4]!r}")


def overview(pdf):
    fig = plt.figure(figsize=(297 / 25.4, 210 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((8, 8), 281, 194, fill=False, lw=0.8, ec=INK))
    ax.text(14, 196, "CHRISTBAUMPOLLER – technical drawings · overview of sizes and variants", fontsize=13, weight="bold", color=INK, va="top")
    ax.text(14, 189, "Front views at scale 1:1 (A4, 100 %) with eyelet and pre-attached ribbon (shortened). Detail sheets per size follow. Dimensions in mm.", fontsize=7.5, color=HID, va="top")
    x = 20
    for size in ("S", "M", "L"):
        s = SIZES[size]
        ax.add_patch(Polygon(front_poly(s, x, 130), closed=True, fc="#f3ead6", ec=INK, lw=0.9))
        script_text(ax, s, x, 130)
        ex, ey = x + s["L"] / 2, 130 + s["H"]
        ax.add_patch(Rectangle((ex - 0.6, ey), 1.2, 2, fc=GOLD, ec=INK, lw=0.3))
        ax.add_patch(Circle((ex, ey + 2 + s["eo"] / 2), s["eo"] / 2, fill=False, ec=GOLD, lw=2))
        rt = ey + 2 + s["eo"] - 1
        ax.plot([ex - 0.9, ex - 0.3], [rt, 186], color=GOLD, lw=1.6)
        ax.plot([ex + 0.9, ex + 0.3], [rt, 186], color=GOLD, lw=1.6)
        ax.text(x + s["L"] / 2, 124, f"{size}: {s['L']} × {s['H']} × {s['D']} mm · max. {s['wt_g']} g", fontsize=7.5, ha="center", va="top", weight="bold")
        x += s["L"] + 28
    # Variantenbilder
    keys = ["gold-glanz", "gold-glanz-schnee", "gold-matt", "gold-matt-schnee", "silber-glanz", "silber-glanz-schnee",
            "silber-matt", "silber-matt-schnee", "rot-glanz", "rot-glanz-schnee", "rot-matt", "rot-matt-schnee"]
    names = {"gold": "GOLD", "silber": "SILVER", "rot": "RED", "glanz": "glossy", "matt": "matte"}
    for i, k in enumerate(keys):
        im = block(k, size=420, seed=i, hang=False)
        w = 40; h = w * im.height / im.width
        cx = 20 + (i % 6) * 45
        cy = 108 - (i // 6) * 40
        ax.imshow(np.array(im), extent=(cx, cx + w, cy - h, cy), zorder=3)
        p = k.split("-")
        ax.text(cx + w / 2, cy - h - 1.5, f"{names[p[0]]} {names[p[1]]}" + (" + snow" if len(p) > 2 else ""), fontsize=5.8, ha="center", va="top")
    notes = ("Colours (approval by physical colour sample): gold metallic ≈ Pantone 871 C · silver metallic ≈ Pantone 877 C · red ≈ Pantone 186 C.\n"
             "Text colour: red ≈ Pantone 186 C on gold and silver; cream white ≈ RAL 9001 on red.  Glossy = high-gloss metallic clear coat; matte = soft-touch matte clear coat.\n"
             "Snow cap: white texture paste with fine glitter on the full top surface, thickness 1.5–3 mm, irregular drips over the front edge 1–5 mm; anchors may be covered.\n"
             "Each piece: polybag + kraft box + hang tag with importer info (GPSR) and warning \"Decoration, not a toy. Not suitable for children under 3 years.\"")
    ax.text(14, 13, notes, fontsize=6.2, color=INK, va="bottom", linespacing=1.5)
    check(fig, ax, "overview")
    pdf.savefig(fig)
    plt.close(fig)


def foam_sheet(pdf):
    s = SIZES["M"]; L, H, D = s["L"], s["H"], s["D"]
    fig = plt.figure(figsize=(297 / 25.4, 210 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((8, 8), 281, 194, fill=False, lw=0.8, ec=INK))
    ax.text(14, 196, "CHRISTBAUMPOLLER – Option C: rigid PU foam, coated · manufacturing requirements", fontsize=12.5, weight="bold", color=INK, va="top")
    ax.text(14, 189, "Applies to sizes S, M and L (size M shown, scale 1:1). Outer dimensions on sheets S/M/L are FINISHED dimensions incl. coating.",
            fontsize=7.3, color=HID, va="top")
    # Schnitt A-A durch die Öse
    fx, fy = 22, 112
    poly = front_poly(s, fx, fy)
    ax.add_patch(Polygon(poly, closed=True, fc="#efe3c8", ec=INK, lw=0.9, hatch="....", zorder=1))
    ax.add_patch(Polygon(poly, closed=True, fill=False, ec="#b84a2a", lw=2.2, zorder=2))   # Beschichtung (überhöht)
    ex = fx + L / 2
    # Einsatz mit Widerhaken
    ax.add_patch(Rectangle((ex - 1.5, fy + H - 10), 3, 10, fc="#c9a24a", ec=INK, lw=0.5, zorder=3))
    for yb in (fy + H - 8.5, fy + H - 5.5, fy + H - 2.5):
        ax.plot([ex - 1.5, ex - 2.6, ex - 1.5], [yb, yb - 0.8, yb - 1.6], color=INK, lw=0.5, zorder=4)
        ax.plot([ex + 1.5, ex + 2.6, ex + 1.5], [yb, yb - 0.8, yb - 1.6], color=INK, lw=0.5, zorder=4)
    ax.add_patch(Rectangle((ex - 0.6, fy + H), 1.2, 2, fc=GOLD, ec=INK, lw=0.4, zorder=3))
    ax.add_patch(Circle((ex, fy + H + 2 + s["eo"] / 2), s["eo"] / 2, fill=False, ec=GOLD, lw=2.2, zorder=3))
    # Trennebene + Anguss/Entlüftung
    ax.plot([fx - 6, fx + L + 6], [fy, fy], ls=(0, (6, 2, 1, 2)), color="#7a3fa0", lw=0.9)
    ax.text(fx + L + 7, fy, "parting line\n(underside)", fontsize=6, color="#7a3fa0", va="center")
    mx = fx + s["a"] + s["w"] + s["m"] / 2
    ax.annotate("pour hole Ø3 in underside\nof middle foot (hidden)", xy=(mx, fy), xytext=(mx + 14, fy - 14), fontsize=6, color=DIM, ha="center",
                arrowprops=dict(arrowstyle="->", color=DIM, lw=0.5))
    ax.annotate("2 vents Ø1 in underside\nof outer feet", xy=(fx + s["a"] / 2, fy), xytext=(fx - 4, fy - 22), fontsize=6, color=DIM, ha="left",
                arrowprops=dict(arrowstyle="->", color=DIM, lw=0.5))
    ax.annotate("brass eyelet insert, barbed shank\nØ3 × 10 mm, placed in mould\nbefore pouring (moulded-in)", xy=(ex + 1.6, fy + H - 6),
                xytext=(fx + L + 7, fy + H - 4), fontsize=6, color=DIM, va="center", arrowprops=dict(arrowstyle="->", color=DIM, lw=0.5))
    ax.annotate("coating (shown thicker)", xy=(fx + L, fy + H * 0.55), xytext=(fx + L + 7, fy + H * 0.55 - 7), fontsize=6, color="#b84a2a", va="center",
                arrowprops=dict(arrowstyle="->", color="#b84a2a", lw=0.5))
    ax.text(fx, fy + H + 12, "SECTION A–A through eyelet (size M)", fontsize=7.5, weight="bold", color=INK)
    ax.text(fx + 3, fy + H / 2 + 1, "rigid PU foam core\n250–350 kg/m³", fontsize=6.5, color=INK, va="center", zorder=5,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="none", alpha=0.9))
    dim_h(ax, fx, fx + L, fy - 34, fy, f"{L} finished", above=False)
    # Schichtaufbau
    lx, ly = 22, 34
    ax.text(lx, ly + 30, "COATING BUILD-UP (dry film)", fontsize=7.5, weight="bold", color=INK)
    layers = [("rigid PU foam core, closed skin", "#efe3c8", 10), ("sealer + filler primer, 2 coats, 40–60 µm", "#d9d4c7", 6),
              ("base coat gold / silver / red, 20–40 µm", "#c9a24a", 5), ("pad print \"#wirschaffendas\"", RED, 2.5),
              ("clear coat matte or gloss, 20–40 µm", "#f4f4f4", 4)]
    y = ly
    for name, col, h in layers:
        ax.add_patch(Rectangle((lx, y), 40, h, fc=col, ec=INK, lw=0.4))
        ax.text(lx + 43, y + h / 2, name, fontsize=6.2, va="center", color=INK)
        y += h
    ax.text(lx, ly - 4, "Total coating 80–150 µm. Foam part = finished dimension − 0.1 mm per side.", fontsize=6.2, color=HID, va="top")
    # Prozess
    px = 168
    ax.text(px, 172, "PROCESS STEPS", fontsize=8, weight="bold", color=INK)
    steps = [
        "Master model from our STEP file (CNC or 3D print), approval by photo",
        "2-part silicone mould, parting line on underside; pour hole + vents hidden in feet",
        "Insert brass eyelet (barbed shank) into mould before pouring",
        "Pour 2K rigid PU foam, density 250–350 kg/m³; demould after full cure",
        "Trim flash, sand parting line; reject parts with voids > 1 mm",
        "Seal + filler primer, 2 coats; sand between coats for gloss version",
        "Base coat: gold / silver / red metallic, or matte version",
        "Pad print \"#wirschaffendas\" (red on gold/silver, cream white on red)",
        "Clear coat matte or gloss; snow variant: white texture paste + glitter on top",
        "Tie gold cord / ribbon loop, final QC, polybag + header card",
    ]
    y = 165
    for i, t in enumerate(steps):
        ax.add_patch(Circle((px + 2.2, y - 1.3), 2.2, fc="#B08D57", ec="none"))
        ax.text(px + 2.2, y - 1.3, str(i + 1), fontsize=6, color="white", ha="center", va="center", weight="bold")
        ax.text(px + 6.5, y, t, fontsize=6.1, color=INK, va="top")
        y -= 7.2
    # Prüfungen
    qy = 88
    ax.text(px, qy, "QUALITY CHECKS (per batch, results with each shipment)", fontsize=8, weight="bold", color=INK)
    qc = [("Weight", "finished M 8–12 g (S 4–6 g, L 15–22 g), ± 1 g"),
          ("Eyelet pull test", "≥ 1 kg for 10 s, no movement (5 pcs / batch)"),
          ("Coating adhesion", "cross-cut test ISO 2409, class ≤ 1"),
          ("Drop test", "1.2 m onto hard floor: no chipping, no cracks"),
          ("Dimensions", "± 0.5 mm, forklift pockets ± 0.3 mm"),
          ("Surface", "no visible pinholes > 0.5 mm, no sink marks"),
          ("Colour", "vs. approved physical sample"),
          ("Materials", "lead-free paint, REACH; MDI-based PU fully cured,\nno odour on delivery")]
    y = qy - 6
    for k, v in qc:
        ax.text(px, y, k, fontsize=6.1, weight="bold", color=INK, va="top")
        ax.text(px + 30, y, v, fontsize=6.1, color=INK, va="top")
        y -= 5.6 + 3.0 * v.count("\n")
    # Schriftfeld
    tb = [("Project", "Christbaumpoller"), ("Part", "Option C – rigid PU foam"), ("Units / scale", "mm · 1:1 on A4"),
          ("Rev / date", "A · 20.11.2026"), ("Customer", "Ebbing Project GmbH, 46348 Raesfeld, Germany")]
    ax.add_patch(Rectangle((204, 12), 81, 23, fill=False, ec=INK, lw=0.6))
    for i, (k, v) in enumerate(tb):
        yy = 32 - i * 4.2
        ax.text(206, yy, k, fontsize=5.8, color=HID, va="center")
        ax.text(225, yy, v, fontsize=6.2, color=INK, va="center", weight="bold" if i < 2 else "normal")
    check(fig, ax, "foam")
    pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/cbp/save/Christbaumpoller_Technische-Zeichnungen.pdf"
    with PdfPages(out) as pdf:
        overview(pdf)
        for sz in ("S", "M", "L"):
            sheet(pdf, sz)
        foam_sheet(pdf)
    print("\n".join(PROBLEMS) if PROBLEMS else "no layout problems")
    print("ok", out)
