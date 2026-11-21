"""Stanzkonturen (Dielines) 1:1 für Einzelschachtel M und 10er (Deckel, Boden, Stegeinlage) + Maßtabelle S/M/L.
Schnitt = schwarz durchgezogen · Rillung = rot gestrichelt · Anschnitt 3 mm = blau punktiert · Klebefläche = grau."""
import sys, os
sys.path.insert(0, "/home/claude/cbp/pack")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Rectangle, FancyBboxPatch, Circle, Arc
from PIL import Image
from dims import einzel, zehner, BLOCK, SOCKEL, KARTON
import einzel as E, zehner as Z, rueck as R
from art import arch_poly

plt.rcParams["font.family"] = "DejaVu Sans"
INK, CUT, CRE, BLEED, DIM, GLUE, HID = "#111111", "#000000", "#d0202a", "#2a6bd1", "#1a4f9c", "#c8c8c8", "#666666"
PROBLEMS = []
GLUE_W, TUCK = 12, 15


def page(w, h):
    fig = plt.figure(figsize=(w / 25.4, h / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((8, 8), w - 16, h - 16, fill=False, lw=0.8, ec=INK))
    ax._W, ax._H = w, h
    return fig, ax


def cut(ax, pts, close=True, lw=0.9):
    ax.add_patch(Polygon(pts, closed=close, fill=False, ec=CUT, lw=lw))


def crease(ax, a, b):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=CRE, lw=0.7, ls=(0, (4, 2)))


def glue(ax, pts):
    ax.add_patch(Polygon(pts, closed=True, fc=GLUE, ec="none", alpha=0.7, hatch="////"))


def art(ax, img, x, y, w, h, rot=0, alpha=0.9):
    im = img.convert("RGB")
    if rot:
        im = im.rotate(rot, expand=True)
    im.thumbnail((1600, 1600))
    ax.imshow(np.asarray(im), extent=(x, x + w, y, y + h), alpha=alpha, zorder=0, interpolation="bilinear")


def dim(ax, a, b, txt, off=6, horiz=True, fs=6.5):
    """Maßlinie mit Text."""
    if horiz:
        y = a[1] + off
        ax.annotate("", (a[0], y), (b[0], y), arrowprops=dict(arrowstyle="<->", lw=0.5, color=DIM))
        ax.plot([a[0], a[0]], [a[1], y + (1 if off > 0 else -1)], color=DIM, lw=0.3)
        ax.plot([b[0], b[0]], [b[1], y + (1 if off > 0 else -1)], color=DIM, lw=0.3)
        ax.text((a[0] + b[0]) / 2, y + (1.2 if off > 0 else -1.2), txt, fontsize=fs, color=DIM, ha="center",
                va="bottom" if off > 0 else "top")
    else:
        x = a[0] + off
        ax.annotate("", (x, a[1]), (x, b[1]), arrowprops=dict(arrowstyle="<->", lw=0.5, color=DIM))
        ax.plot([a[0], x + (1 if off > 0 else -1)], [a[1], a[1]], color=DIM, lw=0.3)
        ax.plot([b[0], x + (1 if off > 0 else -1)], [b[1], b[1]], color=DIM, lw=0.3)
        ax.text(x + (1.2 if off > 0 else -1.2), (a[1] + b[1]) / 2, txt, fontsize=fs, color=DIM, ha="left" if off > 0 else "right",
                va="center", rotation=90)


def label(ax, x, y, s, fs=6.5, c=INK, **kw):
    ax.text(x, y, s, fontsize=fs, color=c, ha=kw.pop("ha", "center"), va=kw.pop("va", "center"), **kw)


def titleblock(ax, rows):
    w, h = ax._W, ax._H
    x0 = w - 8 - 120
    ax.add_patch(Rectangle((x0, 12), 116, 6 + 4.6 * len(rows), fill=False, ec=INK, lw=0.6))
    for i, (k, v) in enumerate(rows):
        yy = 12 + 3 + 4.6 * (len(rows) - 1 - i) + 1.5
        ax.text(x0 + 2, yy, k, fontsize=5.8, color=HID, va="center")
        ax.text(x0 + 30, yy, v, fontsize=6.2, color=INK, va="center", weight="bold" if i < 2 else "normal")


def legend(ax, x, y):
    ax.plot([x, x + 12], [y, y], color=CUT, lw=0.9); label(ax, x + 14, y, "cut / Schnitt", ha="left")
    ax.plot([x + 48, x + 60], [y, y], color=CRE, lw=0.7, ls=(0, (4, 2))); label(ax, x + 62, y, "crease / Rillung", ha="left")
    ax.plot([x + 100, x + 112], [y, y], color=BLEED, lw=0.6, ls=":"); label(ax, x + 114, y, "bleed 3 mm / Anschnitt", ha="left")
    ax.add_patch(Rectangle((x + 158, y - 2), 10, 4, fc=GLUE, ec="none", hatch="////")); label(ax, x + 170, y, "glue / Kleben", ha="left")


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
        if x0 < 8.5 or x1 > ax._W - 8.5 or y0 < 8.5 or y1 > ax._H - 8.5:
            PROBLEMS.append(f"{name}: außerhalb Rahmen: {t.get_text()[:40]!r}")
        boxes.append((x0, y0, x1, y1, t.get_text()[:30]))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 0.3 and oy > 0.3:
                PROBLEMS.append(f"{name}: Überlappung {a[4]!r} / {b[4]!r}")


# ======================================================================
def sheet_einzel(pdf, g="M"):
    d = einzel(g)
    B, T, H, K = d["B"], d["T"], d["H"], d["kopf"]
    fig, ax = page(420, 297)
    ax.text(14, 285, f"Christbaumpoller · Single box / Einzelschachtel „Die Einzelmaßnahme“ · size {g} · dieline 1:1",
            fontsize=12, weight="bold", color=INK, va="top")
    ax.text(14, 278.5, f"Inner dimensions / Innenmaß {B} × {T} × {H} mm (L × D × H) · board GC1 350 g/m² (≈ 0.5 mm) · "
            f"reverse tuck end · hang tab double layer with euro slot · PET window film 0.2 mm, glued inside, 5 mm overlap",
            fontsize=7, color=HID, va="top")
    ox, oy = 40, 70                 # Unterkante Körper
    xs = [ox, ox + GLUE_W, ox + GLUE_W + B, ox + GLUE_W + B + T, ox + GLUE_W + 2 * B + T, ox + GLUE_W + 2 * B + 2 * T]
    # Panels: [Klebe][Hinten B][Links T][Vorne B][Rechts T]
    xG, xBk, xL, xF, xR, xE = xs
    top, bot = oy + H, oy
    faces = {"back": R.e_back(g), "left": R.e_left(g), "front": E.front(g), "right": E.side_r(g), "top": E.top(g),
             "bottom": R.e_bottom(g), "kopf": E.kopf(g)}
    art(ax, faces["back"].img, xBk, bot, B, H)
    art(ax, faces["left"].img, xL, bot, T, H)
    art(ax, faces["front"].img, xF, bot, B, H)
    art(ax, faces["right"].img, xR, bot, T, H)
    # Fenster
    wx0, wy0, wx1, wy1 = E.window_rect(d)
    wp = [(xF + x, top - y) for x, y in arch_poly(wx0, wy0, wx1, wy1)]
    cut(ax, wp)
    ax.add_patch(Polygon(wp, closed=True, fc="white", ec="none", zorder=1))
    label(ax, xF + B / 2, top - (wy0 + wy1) / 2, "WINDOW\nFenster (PET)", fs=6, c=HID, zorder=2)
    # Deckel (oben, an Vorderseite) + Einstecklasche
    art(ax, faces["top"].img, xF, top, B, T)
    lid = [(xF, top), (xF, top + T), (xF + 3, top + T + TUCK), (xF + B - 3, top + T + TUCK), (xF + B, top + T), (xF + B, top)]
    # Kopfkarte doppellagig an Rückwand: Lage A (Rückseite, unbedruckt rot) + Lage B (180° gedreht)
    kA0, kA1, kB1 = top, top + K, top + 2 * K
    ax.add_patch(Rectangle((xBk, kA0), B, K, fc="#8c1420", ec="none", alpha=0.85, zorder=0))
    art(ax, faces["kopf"].img, xBk, kA1, B, K, rot=180)
    # Bodenklappe (unten, an Rückwand) + Einstecklasche
    art(ax, faces["bottom"].img, xBk, bot - T, B, T, rot=180)
    # Außenkontur
    r = 5
    outline = [(xG, bot + 4), (xBk, bot), (xBk, bot - T), (xBk + 3, bot - T - TUCK), (xBk + B - 3, bot - T - TUCK), (xBk + B, bot - T),
               (xBk + B, bot), (xL + 1, bot), (xL + 2, bot - T * 0.7), (xL + T - 4, bot - T * 0.7), (xL + T, bot), (xF, bot),
               (xF + B, bot), (xR, bot), (xR + 4, bot - T * 0.7), (xR + T - 2, bot - T * 0.7), (xR + T - 1, bot), (xE, bot), (xE, top),
               (xR + T - 1, top), (xR + T - 2, top + T * 0.7), (xR + 4, top + T * 0.7), (xR, top)] + \
              lid[::-1][:-1][::-1][::-1] + \
              [(xF, top), (xL + T, top), (xL + T - 4, top + T * 0.7), (xL + 2, top + T * 0.7), (xL + 1, top), (xBk + B, top),
               (xBk + B, kB1 - r)]
    # gerundete Ecken an der Faltkante oben der Kopfkarte (Lage B Ende = kB1)
    arc = lambda cx, cy, a0, a1: [(cx + r * np.cos(np.radians(a)), cy + r * np.sin(np.radians(a))) for a in np.linspace(a0, a1, 8)]
    outline += arc(xBk + B - r, kB1 - r, 0, 90) + arc(xBk + r, kB1 - r, 90, 180) + [(xBk, kB1 - r), (xBk, top), (xG, top - 4)]
    # Lid-Teil korrekt einsetzen: Vorderseite oben -> Deckel
    i = outline.index((xR, top))
    j = outline.index((xF, top))
    outline = outline[:i + 1] + [(xF + B, top), (xF + B, top + T), (xF + B - 3, top + T + TUCK), (xF + 3, top + T + TUCK), (xF, top + T)] + outline[j:]
    cut(ax, outline)
    # Bleed
    ax.add_patch(Polygon([(x + (3 if x > xE - 1 else (-3 if x < xG + 1 else 0)), y) for x, y in outline], closed=True, fill=False,
                         ec=BLEED, lw=0.5, ls=":"))
    glue(ax, [(xG, bot + 4), (xBk, bot), (xBk, top), (xG, top - 4)])
    for x in (xBk, xL, xF, xR):
        crease(ax, (x, bot), (x, top))
    crease(ax, (xF, top), (xF + B, top)); crease(ax, (xF, top + T), (xF + B, top + T))
    crease(ax, (xBk, bot), (xBk + B, bot)); crease(ax, (xBk, bot - T), (xBk + B, bot - T))
    crease(ax, (xL, top), (xL + T, top)); crease(ax, (xR, top), (xR + T, top))
    crease(ax, (xL, bot), (xL + T, bot)); crease(ax, (xR, bot), (xR + T, bot))
    crease(ax, (xBk, top), (xBk + B, top)); crease(ax, (xBk, kA1), (xBk + B, kA1))
    # Euroloch (beide Lagen, gespiegelt um Faltkante kB1? Faltkante ist kA1)
    for yy in (kA1 - 5.2, kA1 + 5.2):
        ax.add_patch(FancyBboxPatch((xBk + B / 2 - 13, yy - 1.6), 26, 3.2, boxstyle="round,pad=0,rounding_size=1.6", fill=False, ec=CUT, lw=0.9))
        ax.add_patch(Circle((xBk + B / 2, yy), 3.2, fill=False, ec=CUT, lw=0.9))
    glue(ax, [(xBk + 2, kA1 + 12), (xBk + B - 2, kA1 + 12), (xBk + B - 2, kB1 - 8), (xBk + 2, kB1 - 8)])
    # Labels
    label(ax, xG + GLUE_W / 2, oy + H / 2, "glue flap\nKlebelasche", fs=5, rotation=90)
    for x, w, s in ((xBk, B, "BACK / hinten"), (xL, T, "LEFT"), (xF, B, "FRONT / vorne"), (xR, T, "RIGHT")):
        label(ax, x + w / 2, bot + 2.2, s, fs=5, c=HID)
    label(ax, xF + B / 2, top + T + TUCK / 2, "tuck flap / Einstecklasche", fs=5.5, c=HID)
    label(ax, xBk + B / 2, bot - T - TUCK / 2, "tuck flap / Einstecklasche", fs=5.5, c=HID)
    label(ax, xBk + B / 2, kA0 + K * 0.5, "hang tab layer A (back)\nAufhänger Lage A", fs=5.5, c="white")
    label(ax, xL + T / 2, top + T * 0.35, "dust flap", fs=5, c=HID)
    label(ax, xR + T / 2, top + T * 0.35, "dust flap", fs=5, c=HID)
    label(ax, xL + T / 2, bot - T * 0.35, "dust flap", fs=5, c=HID)
    label(ax, xR + T / 2, bot - T * 0.35, "dust flap", fs=5, c=HID)
    # Maße
    dim(ax, (xBk, bot - T - TUCK), (xBk + B, bot - T - TUCK), f"{B}", off=-6)
    dim(ax, (xL, bot - T * 0.7), (xL + T, bot - T * 0.7), f"{T}", off=-12)
    dim(ax, (xF, bot - 2), (xF + B, bot - 2), f"{B}", off=-12)
    dim(ax, (xR, bot - T * 0.7), (xR + T, bot - T * 0.7), f"{T}", off=-12)
    dim(ax, (xG, bot - 2), (xBk, bot - 2), f"{GLUE_W}", off=-24)
    dim(ax, (xE, bot), (xE, top), f"{H}", off=8, horiz=False)
    dim(ax, (xE, top), (xE, top + T), f"{T}", off=8, horiz=False)
    dim(ax, (xF + B, top + T), (xF + B, top + T + TUCK), f"{TUCK}", off=-4, horiz=False)
    dim(ax, (xBk, kA0), (xBk, kA1), f"{K}", off=-6, horiz=False)
    dim(ax, (xBk, kA1), (xBk, kB1), f"{K}", off=-6, horiz=False)
    dim(ax, (xG, kB1 + 2), (xE, kB1 + 2), f"overall / gesamt {xE - xG} mm", off=6)
    # Sockeleinlage (U-Profil)
    sx, sy = 300, 150
    sw, sd, sh = B - 1, T - 1, SOCKEL[g]
    ins = [(sx, sy), (sx + sw, sy), (sx + sw, sy + 2 * sh + sd + 2 * 8), (sx, sy + 2 * sh + sd + 2 * 8)]
    cut(ax, ins)
    yy = sy
    for hh in (8, sh, sd, sh):
        yy += hh
        crease(ax, (sx, yy), (sx + sw, yy))
    label(ax, sx + sw / 2, sy + 8 + sh + sd / 2, f"platform / Sockel {sw} × {sd}", fs=6, c=HID)
    label(ax, sx + sw / 2, sy + 4, "foot", fs=5, c=HID)
    label(ax, sx + sw / 2, sy + 2 * sh + sd + 12, "foot", fs=5, c=HID)
    ax.text(sx, sy + 2 * sh + sd + 22, f"Insert / Sockeleinlage (U-profile, height {sh} mm)", fontsize=7, weight="bold", color=INK)
    dim(ax, (sx, sy), (sx + sw, sy), f"{sw}", off=-6)
    dim(ax, (sx + sw, sy + 8), (sx + sw, sy + 8 + sh), f"{sh}", off=5, horiz=False, fs=5.5)
    notes = ["Print / Druck: CMYK + Pantone 871 C (metallic gold) · overall aqueous varnish satin",
             "Option: partial glitter varnish (screen) on stars and bow",
             "Window film PET 0.2 mm (or cellulose), glued inside, 5 mm overlap all round",
             "Ornament stands on insert, long side with forklift pockets facing window",
             "Satin loop folded flat behind ornament · eyelet up",
             "Artwork shown for orientation only – print files will follow (vector PDF)"]
    for i, s in enumerate(notes):
        ax.text(300, 120 - i * 5.2, "• " + s, fontsize=6.2, color=INK, va="top")
    legend(ax, 14, 18)
    titleblock(ax, [("Project", "Christbaumpoller"), ("Part", f"Single box {g} – „Die Einzelmaßnahme“"),
                    ("Units / scale", "mm · 1:1 on A3"), ("Rev / date", "A · 21.11.2026"),
                    ("Customer", "Ebbing Project GmbH, 46348 Raesfeld, Germany")])
    check(fig, ax, f"Einzel {g}")
    pdf.savefig(fig); plt.close(fig)


def tray_net(ax, x0, y0, W, D, Hh, glue_corner=True):
    """Schale/Deckel mit Eck-Klebelaschen: Mittelfläche W×D, Wände Hh."""
    c = [(x0 + Hh, y0 + Hh), (x0 + Hh + W, y0 + Hh), (x0 + Hh + W, y0 + Hh + D), (x0 + Hh, y0 + Hh + D)]
    pts = [(x0 + Hh, y0), (x0 + Hh + W, y0), (x0 + Hh + W, y0 + Hh),
           (x0 + Hh + W + Hh * 0 + 0, y0 + Hh)]
    L = 15
    # Kontur: Front-/Rückwand mit Ecklaschen, Seitenwände ohne
    o = [(x0 + Hh - L, y0 + 3), (x0 + Hh, y0), (x0 + Hh + W, y0), (x0 + Hh + W + L, y0 + 3), (x0 + Hh + W + L, y0 + Hh - 1),
         (x0 + Hh + W, y0 + Hh), (x0 + 2 * Hh + W, y0 + Hh), (x0 + 2 * Hh + W, y0 + Hh + D), (x0 + Hh + W, y0 + Hh + D),
         (x0 + Hh + W + L, y0 + Hh + D + 1), (x0 + Hh + W + L, y0 + 2 * Hh + D - 3), (x0 + Hh + W, y0 + 2 * Hh + D),
         (x0 + Hh, y0 + 2 * Hh + D), (x0 + Hh - L, y0 + 2 * Hh + D - 3), (x0 + Hh - L, y0 + Hh + D + 1), (x0 + Hh, y0 + Hh + D),
         (x0, y0 + Hh + D), (x0, y0 + Hh), (x0 + Hh, y0 + Hh), (x0 + Hh - L, y0 + Hh - 1)]
    cut(ax, o)
    for a, b in ((c[0], c[1]), (c[1], c[2]), (c[2], c[3]), (c[3], c[0])):
        crease(ax, a, b)
    for xx in (x0 + Hh, x0 + Hh + W):
        crease(ax, (xx, y0), (xx, y0 + Hh)); crease(ax, (xx, y0 + Hh + D), (xx, y0 + 2 * Hh + D))
    for gx in ((x0 + Hh - L, x0 + Hh), (x0 + Hh + W, x0 + Hh + W + L)):
        glue(ax, [(gx[0], y0 + 3), (gx[1], y0 + 1), (gx[1], y0 + Hh - 1), (gx[0], y0 + Hh - 1)])
        glue(ax, [(gx[0], y0 + Hh + D + 1), (gx[1], y0 + Hh + D + 1), (gx[1], y0 + 2 * Hh + D - 1), (gx[0], y0 + 2 * Hh + D - 3)])
    return c


def sheet_zehner(pdf, g="M"):
    d = zehner(g)
    B, T, H, wand, steg_h = d["B"], d["T"], d["H"], d["wand"], d["steg_h"]
    LB, LT, LH = d["deckel"]
    fb, ft = d["fach"]
    fig, ax = page(594, 420)
    ax.text(14, 408, f"Christbaumpoller · Box of 10 / Zehnerpackung „Sicherheitskonzept für Ihr Wohnzimmer“ · size {g} · dielines 1:1",
            fontsize=13, weight="bold", color=INK, va="top")
    ax.text(14, 401, f"Lid and tray (two-piece, lid fully telescoping) · inner tray {B} × {T} mm, lid inner height {H} mm · "
            f"board GC1 400 g/m² · corner glue flaps · insert grid 2 × 5 cells {fb} × {ft} mm",
            fontsize=7.5, color=HID, va="top")
    # Deckel
    x0, y0 = 30, 190
    c = tray_net(ax, x0, y0, LB, LT, LH)
    art(ax, Z.lid_top(g).img, c[0][0], c[0][1], LB, LT)
    art(ax, Z.lid_front(g).img, c[0][0], y0, LB, LH, rot=0)
    art(ax, R.z_back(g).img, c[0][0], y0 + LH + LT, LB, LH, rot=180)
    art(ax, Z.lid_side(g).img, x0 + LH + LB, y0 + LH, LH, LT, rot=90)
    art(ax, R.z_left(g).img, x0, y0 + LH, LH, LT, rot=-90)
    label(ax, x0 + LH + LB / 2, y0 + 2 * LH + LT + 6, f"LID / Deckel  outer ≈ {LB + 1:.0f} × {LT + 1:.0f} × {LH + 1:.0f} mm", fs=8, weight="bold")
    dim(ax, (x0 + LH, y0), (x0 + LH + LB, y0), f"{LB:.0f}", off=-6)
    dim(ax, (x0 + 2 * LH + LB, y0 + LH), (x0 + 2 * LH + LB, y0 + LH + LT), f"{LT:.0f}", off=6, horiz=False)
    dim(ax, (x0 + 2 * LH + LB, y0), (x0 + 2 * LH + LB, y0 + LH), f"{LH:.0f}", off=6, horiz=False)
    dim(ax, (x0, y0 + LH + LT), (x0 + LH, y0 + LH + LT), f"{LH:.0f}", off=16)
    # Boden
    bx, by = 30, 58
    c2 = tray_net(ax, bx, by, B, T, wand)
    art(ax, R.z_bottom(g).img, c2[0][0], c2[0][1], B, T, rot=180, alpha=0.75)
    art(ax, Z.tray_tex(g, "front").img, c2[0][0], by, B, wand, rot=180)
    label(ax, bx + wand + B / 2, by + 2 * wand + T + 6, f"TRAY / Boden  inner {B} × {T} × {wand} mm (print outside)", fs=8, weight="bold")
    dim(ax, (bx + wand, by), (bx + wand + B, by), f"{B}", off=-6)
    dim(ax, (bx + 2 * wand + B, by + wand), (bx + 2 * wand + B, by + wand + T), f"{T}", off=6, horiz=False)
    dim(ax, (bx + 2 * wand + B, by), (bx + 2 * wand + B, by + wand), f"{wand}", off=6, horiz=False)
    # Stegeinlage
    sx, sy = 455, 104
    ax.text(sx, sy + 70, "Insert / Stegeinlage (cross-slotted)", fontsize=7.5, weight="bold", color=INK)
    Ls = B - 1
    cut(ax, [(sx, sy + 40), (sx + 0.25 * Ls, sy + 40), (sx + 0.25 * Ls, sy + 40 + steg_h), (sx, sy + 40 + steg_h)])
    label(ax, sx + 0.125 * Ls, sy + 40 + steg_h + 4, f"long rib 1×: {Ls} × {steg_h}\n(shown shortened, 4 slots from top, 1.2 × {steg_h / 2:.0f})", fs=5.5,
          c=HID)
    for k in range(1, 3):
        xx = sx + 0.25 * Ls * k / 3
        ax.plot([xx, xx], [sy + 40 + steg_h, sy + 40 + steg_h / 2], color=CUT, lw=0.9)
    cut(ax, [(sx, sy + 5), (sx + T - 1, sy + 5), (sx + T - 1, sy + 5 + steg_h), (sx, sy + 5 + steg_h)])
    ax.plot([sx + (T - 1) / 2] * 2, [sy + 5, sy + 5 + steg_h / 2], color=CUT, lw=0.9)
    label(ax, sx + (T - 1) / 2, sy - 1, f"cross rib 4×: {T - 1} × {steg_h}, slot from bottom", fs=5.5, c=HID)
    notes = ["Print / Druck: CMYK + Pantone 871 C (metallic gold), satin aqueous varnish",
             "Option: partial glitter varnish on bow, stars, seal",
             "Tray walls low on purpose – ornaments stand above rim (‚Zufahrtssperre‘ look)",
             "Ornaments stand in cells, long side to front, ribbons folded flat",
             "One variant per box (mockups show mixed colours for illustration only)",
             "Cheaper option: one-piece box with hinged lid (Klappdeckel), same artwork",
             "Artwork shown for orientation only – print files will follow (vector PDF)"]
    for i, s in enumerate(notes):
        ax.text(455, 96 - i * 5.0, "• " + s, fontsize=5.6, color=INK, va="top")
    legend(ax, 14, 18)
    titleblock(ax, [("Project", "Christbaumpoller"), ("Part", f"Box of 10, size {g} – lid, tray, insert"),
                    ("Units / scale", "mm · 1:1 on A2"), ("Rev / date", "A · 21.11.2026"),
                    ("Customer", "Ebbing Project GmbH, 46348 Raesfeld, Germany")])
    check(fig, ax, f"10er {g}")
    pdf.savefig(fig); plt.close(fig)


def sheet_table(pdf):
    fig, ax = page(297, 210)
    ax.text(14, 198, "Christbaumpoller · packaging dimensions S / M / L (all sizes same construction and artwork, scaled)",
            fontsize=11, weight="bold", color=INK, va="top")
    ax.text(14, 191.5, "Inner dimensions in mm. Size M dielines on the previous sheets; S and L follow the same construction.",
            fontsize=7, color=HID, va="top")
    hdr = ["Size", "Ornament L×H×D", "Single box inner L×D×H", "hang tab", "insert height",
           "10-box tray inner L×D×H", "lid inner L×D×H", "cell L×D", "rib height"]
    xs = [14, 30, 66, 110, 130, 154, 200, 240, 266]
    y = 180
    for x, h in zip(xs, hdr):
        ax.text(x, y, h, fontsize=6.4, weight="bold", color=INK, va="center")
    for g in "SML":
        y -= 9
        e, z = einzel(g), zehner(g)
        L, H, D = BLOCK[g]
        row = [g, f"{L}×{H}×{D}", f"{e['B']}×{e['T']}×{e['H']}", f"{e['kopf']}", f"{SOCKEL[g]}",
               f"{z['B']}×{z['T']}×{z['wand']}", f"{z['deckel'][0]:.0f}×{z['deckel'][1]:.0f}×{z['deckel'][2]:.0f}",
               f"{z['fach'][0]}×{z['fach'][1]}", f"{z['steg_h']}"]
        for x, v in zip(xs, row):
            ax.text(x, y, v, fontsize=7, color=INK, va="center")
        ax.plot([14, 283], [y + 4.5, y + 4.5], color="#bbbbbb", lw=0.4)
    rules = ["Single box inner = ornament + 2 mm per side (L, D); height = insert + ornament + eyelet + folded ribbon + 2 mm",
             "Eyelet above top: S 5 / M 7 / L 9 mm · folded ribbon allowance: S 6 / M 8 / L 10 mm",
             "10-box: 2 × 5 cells, cell = single-box inner L × D, ribs 1 mm, +2 mm clearance overall",
             "Tray wall ≈ 0.46 × ornament height (ornaments visible above rim) · lid fully telescoping, +1 mm",
             "Outer dimensions ≈ inner + 1 mm (board 0.45–0.5 mm)",
             "Orders of 20 / 30 / 100 pcs ship as 2 / 3 / 10 boxes of 10"]
    for i, s in enumerate(rules):
        ax.text(14, 130 - i * 6.5, "• " + s, fontsize=7, color=INK, va="top")
    titleblock(ax, [("Project", "Christbaumpoller"), ("Part", "Packaging – dimension table S / M / L"),
                    ("Units", "mm"), ("Rev / date", "A · 21.11.2026"), ("Customer", "Ebbing Project GmbH, 46348 Raesfeld, Germany")])
    check(fig, ax, "Tabelle")
    pdf.savefig(fig); plt.close(fig)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/cbp/pack/out/Christbaumpoller_Stanzkonturen.pdf"
    with PdfPages(out) as pdf:
        sheet_einzel(pdf)
        sheet_zehner(pdf)
        sheet_table(pdf)
    print("\n".join(PROBLEMS) if PROBLEMS else "keine Layoutprobleme")
    print("ok", out)
