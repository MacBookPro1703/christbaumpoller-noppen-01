"""Restliche Flächen: Rückseiten (Packungsbeilage, Aufbauanleitung), linke Seiten, Unterseiten."""
import sys
sys.path.insert(0, "/home/claude/cbp/pack")
from PIL import ImageDraw
from art import *
from dims import einzel, zehner, BLOCK
import einzel as E
import zehner as Z

HERST = "Ebbing Project GmbH · Marienthaler Str. 44a · 46348 Raesfeld · info@ebbing-project.de"
WARN = "Dekoartikel, kein Spielzeug. Enthält Kleinteile – nicht für Kinder unter 3 Jahren."


def wrap(s, fp, px, maxw, wght=None):
    f = font(fp, px, wght)
    out, line = [], ""
    for w in s.split():
        t = (line + " " + w).strip()
        if f.getlength(t) <= maxw:
            line = t
        else:
            out.append(line)
            line = w
    out.append(line)
    return "\n".join(out)


def table(f, x, y, rows, lab_w, txt_w, size, gap, k=1.0, lab_font=None):
    """Zweispaltig: Label (Gold) | Text (Creme). Gibt neue y-Position zurück."""
    for lab, txt in rows:
        w = wrap(txt, F_SANS, f.mm(size), f.mm(txt_w), 450)
        n = w.count("\n") + 1
        f.text((x, y), lab, lab_font or F_CIN, size * 0.92, fill=GOLD, anchor="la", shadow=False, tag="L:" + lab)
        f.text((x + lab_w, y), w, F_SANS, size, fill=CREME, anchor="la", wght=450, shadow=False, spacing=size * 0.18, tag="T:" + lab)
        y += n * size * 1.22 + gap
    return y


def checkbox(f, x, y, s, label, on, size):
    d = ImageDraw.Draw(f.img)
    px, py, ps = f.mm(x), f.mm(y), f.mm(s)
    d.rectangle([px, py, px + ps, py + ps], outline=CREME + (255,), width=max(1, int(f.mm(0.25))))
    if on:
        d.line([(px + ps * 0.2, py + ps * 0.2), (px + ps * 0.8, py + ps * 0.8)], fill=GOLD + (255,), width=max(2, int(f.mm(0.4))))
        d.line([(px + ps * 0.8, py + ps * 0.2), (px + ps * 0.2, py + ps * 0.8)], fill=GOLD + (255,), width=max(2, int(f.mm(0.4))))
    f.text((x + s * 1.5, y + s / 2), label, F_SANS, size, fill=CREME, anchor="lm", wght=500, shadow=False, tag="CB:" + label)


# ---------------- Einzelschachtel ----------------
def e_back(g="M", seed=21):
    d = einzel(g)
    k = d["B"] / 74
    B, H = d["B"], d["H"]
    f = Face(f"Einzel {g} hinten", B, H, E.PPM, seed=seed).bg_red(pattern=False)
    f.gold_frame(inset=1.2 * k, w=0.3 * k, double=False)
    f.text((B / 2, 5.6 * k), "Gebrauchsinformation", F_CIN, 3.4 * k, tag="Titel")
    f.text((B / 2, 9.4 * k), "Bitte aufmerksam lesen. Oder einfach aufhängen.", F_SERIF_I, 1.9 * k, fill=CREME, wght=500, shadow=False,
           tag="Unter")
    rows = [("Anwendung", "Gefühlte Gefährdungslagen im Advent, unruhige Tannenbäume, Besuch der Schwiegereltern."),
            ("Wirkung", "Hält den Weihnachtsmann nicht auf. Aber die Stimmung."),
            ("Gegenanzeigen", "Nicht anwenden bei echtem Sicherheitsbedarf."),
            ("Dosierung", "Ein Poller je Zweig. Bei erhöhter Lage: Zehnerpackung."),
            ("Nebenwirkungen", "Lächeln, Kopfschütteln, Diskussionen am Festtagstisch."),
            ("Wechselwirkung", "Mit Glühwein verstärkt sich die Wirkung."),
            ("Haltbarkeit", "Mindestens haltbar bis Ende der Gefährdungslage.")]
    y = table(f, 4.0 * k, 13.0 * k, rows, 19.5 * k, B - 27.5 * k, 2.05 * k, 1.05 * k)
    f.text((B / 2, H - 6.6 * k), wrap(WARN, F_SANS, f.mm(1.45 * k), f.mm(B - 9 * k)), F_SANS, 1.45 * k, fill=CREME, wght=500,
           shadow=False, spacing=0.2 * k, tag="Warn")
    f.text((B / 2, H - 3.2 * k), wrap(HERST, F_SANS, f.mm(1.4 * k), f.mm(B - 9 * k)), F_SANS, 1.4 * k, fill=CREME, wght=400,
           shadow=False, spacing=0.2 * k, tag="Hersteller")
    f._y_end = y
    return f


def e_left(g="M", seed=22):
    d = einzel(g)
    k = d["B"] / 74
    T, H = d["T"], d["H"]
    L, Hb, D = BLOCK[g]
    f = Face(f"Einzel {g} links", T, H, E.PPM, seed=seed).bg_red()
    glitter(f.img, density=0.06, seed=seed)
    f.gold_frame(inset=1.2 * k, w=0.3 * k, double=False)
    star(ImageDraw.Draw(f.img), T / 2 * f.ppm, 7 * k * f.ppm, 2.2 * k * f.ppm, GOLD + (255,))
    f.text((T / 2, 14 * k), "INHALT", F_CIN, 2.6 * k, tag="Inhalt")
    f.text((T / 2, 18.6 * k), "1 Christbaumpoller\nmit Öse und Satinband", F_SANS, 2.1 * k, fill=CREME, wght=500, spacing=0.3 * k,
           shadow=False, tag="Inhalt2")
    f.text((T / 2, 27 * k), "VARIANTE", F_CIN, 2.6 * k, tag="Variante")
    f.text((T / 2, 32 * k), "siehe Fenster.\nWir haben nachgesehen.", F_SERIF_I, 2.1 * k, fill=CREME, wght=500, spacing=0.3 * k,
           shadow=False, tag="Variante2")
    f.text((T / 2, 41.5 * k), "ENTSORGUNG", F_CIN, 2.6 * k, tag="Entsorgung")
    f.text((T / 2, 47 * k), "Schachtel: Altpapier\nFenster: Gelbe Tonne\nPoller: niemals", F_SANS, 1.9 * k, fill=CREME, wght=500,
           spacing=0.3 * k, shadow=False, tag="Entsorgung2")
    return f


def e_bottom(g="M", seed=23):
    d = einzel(g)
    k = d["B"] / 74
    B, T = d["B"], d["T"]
    f = Face(f"Einzel {g} unten", B, T, E.PPM, seed=seed).bg_red(pattern=False)
    f.gold_frame(inset=1.2 * k, w=0.3 * k, double=False)
    f.text((B / 2 - 10 * k, 8 * k), "Staplertaschen nach unten.", F_BRUSH, 3.8 * k, fill=CREME, tag="Stapler")
    f.text((B / 2 - 10 * k, 13.2 * k), "Bitte nicht mit dem Stapler öffnen.", F_SERIF_I, 2.0 * k, fill=CREME, wght=500, shadow=False,
           tag="Stapler2")
    dd = ImageDraw.Draw(f.img)
    x0, y0, x1, y1 = (B - 28 * k) * f.ppm, 18 * k * f.ppm, (B - 4 * k) * f.ppm, (T - 4 * k) * f.ppm
    dd.rectangle([x0, y0, x1, y1], fill=(250, 248, 242, 255))
    f.text(((B - 16 * k), 23 * k), "Etikett", F_SANS, 2.0 * k, fill=(90, 90, 90), wght=600, shadow=False, tag="Etikett")
    f.text(((B - 16 * k), 27.5 * k), "EAN + Artikelnr.\nCBP-xx-xx-xx-" + g, F_SANS, 1.5 * k, fill=(90, 90, 90), wght=400,
           shadow=False, spacing=0.2 * k, tag="Etikett2")
    f.text((4 * k + 14 * k, 26 * k), "Made in China.\nVerpackt mit Gefühl.", F_SANS, 1.7 * k, fill=CREME, wght=500, spacing=0.3 * k,
           shadow=False, tag="Made")
    return f


# ---------------- 10er ----------------
def z_back(g="M", seed=31):
    d = zehner(g)
    B, T, Hh = d["deckel"]
    k = T / 77
    P = Z.PPM
    f = Face(f"10er {g} Deckel hinten", B, Hh, P, seed=seed).bg_red(pattern=False)
    f.gold_frame(inset=2.2 * k, w=0.5 * k, double=False)
    f.text((8 * k, 9 * k), "Aufbauanleitung Zufahrtssperre (Wohnzimmer)", F_CIN, 4.4 * k, anchor="lm", tag="Titel")
    steps = ["Deckel öffnen.\nFürchtet euch nicht.", "Poller in Reihe vor den\nBaum stellen. Abstand:\neine Handbreit.",
             "Rettungsgasse zum\nPlätzchenteller\nfreihalten.", "Restliche Poller an\nden Baum hängen.\nStaplertaschen unten.",
             "Fertig. Die Lage ist\nhiermit festlich."]
    cw = 42 * k
    for i, s in enumerate(steps):
        x = 8 * k + i * (cw + 4 * k)
        dd = ImageDraw.Draw(f.img)
        cx, cy = (x + 3.2 * k) * P, 18.5 * k * P
        dd.ellipse([cx - 3 * k * P, cy - 3 * k * P, cx + 3 * k * P, cy + 3 * k * P], outline=GOLD + (255,), width=max(2, int(0.4 * k * P)))
        f.text((x + 3.2 * k, 18.5 * k), str(i + 1), F_CIN, 3.4 * k, tag=f"Nr{i}")
        f.text((x + 8 * k, 16 * k), s, F_SANS, 2.6 * k, fill=CREME, anchor="la", wght=500, spacing=0.4 * k, shadow=False, tag=f"Schritt{i}")
    # Genehmigungsvermerk
    gx = 8 * k + 5 * (cw + 4 * k)
    f.text((gx, 15 * k), "GENEHMIGUNGSVERMERK", F_CIN, 2.8 * k, anchor="la", tag="Gen")
    for j, (lab, on) in enumerate((("beantragt", False), ("in Prüfung", False), ("gefühlt", True))):
        checkbox(f, gx, 20 * k + j * 4.6 * k, 2.8 * k, lab, on, 2.6 * k)
    rows = [("Wirkung", "Hält den Weihnachtsmann nicht auf. Aber die Stimmung, und zwar zehnfach."),
            ("Gegenanzeigen", "Nicht anwenden bei echtem Sicherheitsbedarf. Ersetzt kein Sicherheitskonzept, ist aber eins."),
            ("Haltbarkeit", "Mindestens haltbar bis Ende der Gefährdungslage.")]
    table(f, 8 * k, 34.5 * k, rows, 24 * k, 150 * k, 2.4 * k, 0.6 * k)
    f.text((B - 8 * k, 36.5 * k), wrap(WARN, F_SANS, f.mm(2.2 * k), f.mm(150 * k)), F_SANS, 2.2 * k, fill=CREME, anchor="ra", wght=500,
           shadow=False, spacing=0.3 * k, tag="Warn")
    f.text((B - 8 * k, 44 * k), HERST, F_SANS, 2.1 * k, fill=CREME, anchor="ra", wght=400, shadow=False, tag="Hersteller")
    return f


def z_left(g="M", seed=32):
    d = zehner(g)
    B, T, Hh = d["deckel"]
    k = T / 77
    f = Face(f"10er {g} Deckel links", T, Hh, Z.PPM, seed=seed).bg_red()
    glitter(f.img, density=0.05, seed=seed, unit=Z.PPM * 0.09)
    f.gold_frame(inset=2.2 * k, w=0.5 * k)
    f.text((T / 2, 14 * k), "Friede auf Erden.", F_FRAK, 7.6 * k, max_w=T - 12 * k, tag="Friede")
    f.text((T / 2, 22 * k), "LUKAS 2,14", F_CIN4, 2.4 * k, fill=CREME, shadow=False, tag="Quelle")
    f.text((T / 2, 35 * k), "Bis dahin: Poller.", F_BRUSH, 6.4 * k, fill=CREME, rot=3, max_w=T - 12 * k, tag="Bisdahin")
    return f


def z_bottom(g="M", seed=33):
    d = zehner(g)
    B, T = d["B"], d["T"]
    k = T / 75
    P = Z.PPM
    f = Face(f"10er {g} Boden unten", B, T, P, seed=seed).bg_red(pattern=False)
    f.gold_frame(inset=2.2 * k, w=0.5 * k, double=False)
    f.text((B / 2 - 40 * k, 30 * k), "Bitte nicht mit dem Stapler anheben.", F_BRUSH, 8 * k, fill=CREME, tag="Stapler")
    f.text((B / 2 - 40 * k, 44 * k), "Die Taschen sitzen an den Pollern, nicht an der Schachtel.", F_SERIF_I, 3.4 * k, fill=CREME,
           wght=500, shadow=False, tag="Taschen")
    dd = ImageDraw.Draw(f.img)
    x0, y0, x1, y1 = (B - 70 * k) * P, 20 * k * P, (B - 10 * k) * P, (T - 20 * k) * P
    dd.rectangle([x0, y0, x1, y1], fill=(250, 248, 242, 255))
    f.text((B - 40 * k, 30 * k), "Etikett", F_SANS, 3.6 * k, fill=(90, 90, 90), wght=600, shadow=False, tag="Etikett")
    f.text((B - 40 * k, 38 * k), "EAN + Artikelnr. CBP-xx-xx-xx-" + g + "-10", F_SANS, 2.4 * k, fill=(90, 90, 90), wght=400, shadow=False,
           tag="Etikett2")
    f.text((B / 2 - 40 * k, 60 * k), "Made in China. Verpackt mit Gefühl. · " + HERST, F_SANS, 2.2 * k, fill=CREME, wght=400,
           shadow=False, tag="Made")
    return f


if __name__ == "__main__":
    import os
    os.makedirs("/home/claude/cbp/pack/faces", exist_ok=True)
    errs = []
    for fn in (e_back, e_left, e_bottom, z_back, z_left, z_bottom):
        fc = fn()
        errs += fc.check()
        fc.img.convert("RGB").save(f"/home/claude/cbp/pack/faces/{fn.__name__}.jpg", quality=88)
    print("Fehler gesamt:", len(errs))
