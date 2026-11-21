"""Export: Mockups + Flächen (webp) für Seite und 3D-Viewer."""
import sys, os
sys.path.insert(0, "/home/claude/cbp/pack")
from PIL import Image
import einzel as E, zehner as Z, rueck as R

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/cbp/pack/out"
os.makedirs(OUT + "/3d", exist_ok=True)
errs = []


def save(face, name, ppm_out):
    errs.extend(face.check(report=False))
    im = face.img
    k = ppm_out / face.ppm
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    im.save(f"{OUT}/3d/{name}.webp", quality=86, method=6)


# Einzel (gold-glanz im Fenster)
kp = E.kopf()
E.kopf_shape(kp, 1.0)
for face, n in ((E.front(), "e-front"), (R.e_back(), "e-back"), (E.side_r(), "e-right"), (R.e_left(), "e-left"),
                (E.top(), "e-top"), (R.e_bottom(), "e-bottom"), (kp, "e-kopf")):
    save(face, n, 14)
# 10er geschlossen: Deckel + Boden unten
for face, n in ((Z.lid_top(), "z-top"), (Z.lid_front(), "z-front"), (R.z_back(), "z-back"), (Z.lid_side(), "z-right"),
                (R.z_left(), "z-left"), (R.z_bottom(), "z-bottom")):
    save(face, n, 7)
# Mockups
for fn, n in ((lambda o: E.mockup("M", "gold-glanz", out=o), "einzel"), (lambda o: Z.mockup_closed("M", out=o), "zehner-zu"),
              (lambda o: Z.mockup_open("M", out=o), "zehner-offen")):
    fn(f"{OUT}/mock-{n}.jpg")
    Image.open(f"{OUT}/mock-{n}.jpg").save(f"{OUT}/mock-{n}.webp", quality=84, method=6)
print("Layout-Fehler:", len(errs), *errs, sep="\n")
