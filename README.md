# Christbaumpoller · Noppenblock

> Variante mit 2 × 4 quadratischen Noppen oben, passenden Mulden unten (stapelbar, nicht klemmend), Ösenloch unten und Staplertaschen im echten Verhältnis. Die glatte Variante: https://macbookpro1703.github.io/christbaumpoller/

**Ein Stück Sicherheitsgefühl für zu Hause.**
Der Weihnachtsbaum-Anhänger in Form des Weihnachtsmarkt-Sperrblocks, mit Noppen und Mulden zum Stapeln, zwei Staplertaschen und Pinselschriftzug `#wirschaffendas`.
Gold · Silber · Rot – glänzend oder matt – mit oder ohne Schnee – S, M, L.

Eine Idee von **Ebbing Project**.

- Seite: https://macbookpro1703.github.io/christbaumpoller-noppen/
- Produkt- und Vertriebskonzept: [KONZEPT.md](KONZEPT.md)
- Spots: `clips/` (Web-Fassung) · Quellskripte zum Neu-Rendern: `quelle/`

Neu rendern: `cd quelle && python3 clip.py quer && python3 clip.py hoch && python3 musik.py` (Pillow, NumPy, ffmpeg).

Form umschalten: `CBP_FORM=glatt` bzw. `CBP_FORM=noppen` (Standard hier: noppen) vor `python3 clip.py …` / `listing_img.py`.
