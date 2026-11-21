"""Einfache 3D-Projektion für Schachtel-Mockups: Flächenbilder per Perspektive auf Quader legen."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def coeffs(dst, src):
    """PIL PERSPECTIVE: Koeffizienten, die Ausgabepunkte dst auf Eingabepunkte src abbilden."""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()


class Cam:
    def __init__(self, yaw=-32, pitch=22, dist=900, f=1400, cx=0, cy=0):
        self.yaw, self.pitch, self.dist, self.f, self.cx, self.cy = math.radians(yaw), math.radians(pitch), dist, f, cx, cy

    def p(self, x, y, z):
        """x rechts, y oben, z nach hinten (mm) → Bildpunkt."""
        cy_, sy_ = math.cos(self.yaw), math.sin(self.yaw)
        X = x * cy_ + z * sy_
        Z = -x * sy_ + z * cy_
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        Y2 = y * cp - Z * sp
        Z2 = y * sp + Z * cp
        k = self.f / (Z2 + self.dist)
        return (self.cx + X * k, self.cy - Y2 * k)


def put(canvas, tex, quad, shade=1.0, ss=1):
    """tex (RGBA) auf Viereck quad = [TL, TR, BR, BL] legen."""
    W, H = tex.size
    src = [(0, 0), (W, 0), (W, H), (0, H)]
    xs, ys = [q[0] for q in quad], [q[1] for q in quad]
    x0, y0 = int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2
    x1, y1 = int(math.ceil(max(xs))) + 2, int(math.ceil(max(ys))) + 2
    loc = [(qx - x0, qy - y0) for qx, qy in quad]
    t = tex
    if shade != 1.0:
        a = np.array(t).astype(np.float32)
        a[..., :3] *= shade
        t = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    out = t.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, coeffs(loc, src), Image.BICUBIC)
    m = Image.new("L", out.size, 0)
    ImageDraw.Draw(m).polygon(loc, fill=255)
    out.putalpha(Image.fromarray(np.minimum(np.array(out.split()[3]), np.array(m))))
    canvas.alpha_composite(out, (x0, y0))


def shadow(canvas, pts, blur, alpha=150, off=(0, 0)):
    m = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(m).polygon([(x + off[0], y + off[1]) for x, y in pts], fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    lay = Image.new("RGBA", canvas.size, (5, 3, 2, 0))
    lay.putalpha(m)
    canvas.alpha_composite(lay)
