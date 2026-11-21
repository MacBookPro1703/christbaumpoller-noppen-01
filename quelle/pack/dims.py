"""Christbaumpoller – Verpackungsmaße (mm). Quelle Blockmaße: render/zeichnung.py (S/M/L L×H×D)."""
BLOCK = {"S": (50, 25, 23), "M": (70, 35, 32), "L": (90, 45, 41)}
# Öse über Oberkante, Bandbogen (Satinband 3 mm, 120-mm-Schlaufe flach nach hinten gelegt), Sockel (Einlage)
OESE = {"S": 5, "M": 7, "L": 9}
BAND = {"S": 6, "M": 8, "L": 10}
SOCKEL = {"S": 6, "M": 8, "L": 10}
LUFT_SEITE = 2      # je Seite in Länge und Tiefe
LUFT_OBEN = 2
STEG = 1            # Kartonsteg zwischen den Fächern (10er)
KARTON = 0.5        # Kartondicke (GC1 350–400 g/m²)
KOPF = {"S": 24, "M": 30, "L": 34}  # Aufhängelasche (Kopfkarte) Einzelschachtel


def einzel(g):
    L, H, D = BLOCK[g]
    B = L + 2 * LUFT_SEITE
    T = D + 2 * LUFT_SEITE
    Hi = SOCKEL[g] + H + OESE[g] + BAND[g] + LUFT_OBEN
    return dict(B=B, T=T, H=Hi, kopf=KOPF[g])


def zehner(g):
    """Deckel-Boden-Schachtel: Boden (Schale) mit Stegeinlage 2×5, Deckel voll übergreifend."""
    L, H, D = BLOCK[g]
    fb, ft = L + 2 * LUFT_SEITE, D + 2 * LUFT_SEITE
    B = 5 * fb + 4 * STEG + 2
    T = 2 * ft + STEG + 2
    Hi = H + OESE[g] + BAND[g] + LUFT_OBEN          # Innenhöhe Deckel (Poller steht direkt auf dem Boden)
    wand = round(H * 0.46)                            # Bodenschale niedrig: Schriftzug und Taschen bleiben sichtbar
    steg_h = round(H * 0.40)                          # Höhe der Stegeinlage
    return dict(B=B, T=T, H=Hi, fach=(fb, ft), wand=wand, steg_h=steg_h,
                deckel=(B + 2 * KARTON + 1, T + 2 * KARTON + 1, Hi + 1))


if __name__ == "__main__":
    for g in "SML":
        print(g, "einzel", einzel(g), "zehner", zehner(g))
