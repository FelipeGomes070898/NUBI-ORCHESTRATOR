"""Motor de camadas em CPU: parallax, cartoon 2D e 3D simulado (2.5D, câmera em perspectiva)."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

# céu topo, céu base, astro, colinas (longe, meio, perto), contorno
PALETAS = {
    "dia": ((90,180,250),(200,240,255),(255,226,90),((130,200,170),(86,176,110),(52,140,80)),(30,50,70)),
    "tarde": ((90,60,140),(255,160,110),(255,236,170),((190,110,140),(130,80,130),(70,50,100)),(40,25,60)),
    "noite": ((8,12,40),(40,50,110),(240,240,255),((40,50,110),(30,36,86),(18,22,56)),(5,8,25)),
    "espaco": ((4,4,16),(30,14,60),(255,170,90),((60,30,90),(40,20,70),(22,12,44)),(0,0,0)),
}

def _grad(w, h, top, bot):
    t = np.linspace(0, 1, h, dtype="float32")[:, None, None]
    a = np.array(top, "float32") * (1 - t) + np.array(bot, "float32") * t
    return Image.fromarray(np.repeat(a, w, 1).astype("uint8")).convert("RGBA")

def _blob(d, ells, fill, line, k):
    for x0, y0, x1, y1 in ells: d.ellipse((x0-k, y0-k, x1+k, y1+k), fill=line)
    for e in ells: d.ellipse(e, fill=fill)

def _hills(w, h, base, amp, color, line, rng, u, trees):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    ph, f = rng.uniform(0, 6.28), rng.uniform(2.5, 4.5) * 2 * math.pi / w
    y_at = lambda x: base + amp * math.sin(x*f + ph) + amp * .4 * math.sin(x*f*2.3 + ph*1.7)
    pts = [(x, y_at(x)) for x in range(0, w + 20, 20)]
    d.polygon(pts + [(w, h), (0, h)], fill=color)
    d.line(pts, fill=line, width=int(6*u), joint="curve")
    if trees:
        leaf = tuple(min(255, c + 30) for c in color)
        for x in range(int(rng.integers(40, 160)*u), w, int(rng.integers(170, 280)*u)):
            y = y_at(x)
            d.rectangle((x-5*u, y-48*u, x+5*u, y+8*u), fill=tuple(c//2 for c in color), outline=line, width=int(3*u))
            _blob(d, [(x-30*u, y-92*u, x+30*u, y-40*u), (x-44*u, y-72*u, x+4*u, y-30*u), (x-4*u, y-72*u, x+44*u, y-30*u)], leaf, line, int(3*u))
    return img

def _clouds(w, h, rng, u, line, white=(255, 255, 255)):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for _ in range(max(4, w // int(380*u))):
        cx, cy, s = rng.uniform(0, w), rng.uniform(.06, .3) * h, rng.uniform(.8, 1.5) * u
        _blob(d, [(cx-70*s, cy-25*s, cx+10*s, cy+25*s), (cx-30*s, cy-50*s, cx+50*s, cy+20*s), (cx, cy-20*s, cx+85*s, cy+25*s)], white, line, int(3*u))
    return img

def _sky(w, h, mood, rng, u):
    top, bot, astro, _, line = PALETAS[mood]
    img = _grad(w, h, top, bot); d = ImageDraw.Draw(img)
    if mood in ("noite", "espaco"):
        for _ in range(w * h // 2500):
            x, y, r = rng.integers(w), rng.integers(int(h*.8)), rng.choice([1, 1, 2]) * u
            d.ellipse((x-r, y-r, x+r, y+r), fill=(235, 235, 255))
    cx, cy, r = w * rng.uniform(.3, .7), h * .26, h * .09
    if mood == "espaco":
        d.ellipse((cx-r*2.2, cy-r*.45, cx+r*2.2, cy+r*.45), outline=(255, 210, 140), width=int(8*u))
        _blob(d, [(cx-r, cy-r, cx+r, cy+r)], astro, (120, 60, 30), int(5*u))
        d.arc((cx-r*2.2, cy-r*.45, cx+r*2.2, cy+r*.45), 0, 180, fill=(255, 210, 140), width=int(8*u))
    else:
        _blob(d, [(cx-r, cy-r, cx+r, cy+r)], astro, line, int(5*u))
    return img

def _fit(img, size):
    return ImageOps.fit(ImageOps.exif_transpose(img).convert("RGB"), size).convert("RGBA")

def build_layers(mood, w, h, seed, style, image=None, depth=None):
    """Retorna [(camada RGBA, fator de profundidade)] do fundo para a frente."""
    rng = np.random.default_rng(seed)
    W2 = int(w * 1.5) // 2 * 2
    ss = 2 if w * h <= 1280 * 720 else 1
    u = h / 540 * ss
    top, bot, astro, hills, line = PALETAS[mood]
    down = lambda im: im.resize((W2, h), Image.LANCZOS) if ss > 1 else im
    sil = lambda base, amp, col, tr, sc=1: down(_hills(W2*ss, h*ss, base*h*ss, amp*h*ss, col, line, rng, u*sc, tr))
    if image is not None:
        bg = _fit(image, (W2, h))
        layers = [(bg.filter(ImageFilter.GaussianBlur(1.2)), .1)]
        if depth is not None:  # mapa de profundidade: branco = perto
            m = np.asarray(ImageOps.fit(depth.convert("L"), (W2, h)), "float32") / 255
            for lo, hi, dep in ((.35, .65, .55), (.6, 1.01, 1.0)):
                a = np.clip((m - lo) / .08, 0, 1) * (m < hi if hi < 1 else 1)
                lay = bg.copy(); lay.putalpha(Image.fromarray((a * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(2)))
                layers.append((lay, dep))
        else:
            layers += [(sil(.8, .04, hills[1], True), .6), (sil(.92, .03, hills[2], True, 1.5), 1.0)]
        return layers
    sky = _sky(W2*ss, h*ss, mood, rng, u); sky = down(sky)
    layers = [(sky, .05)]
    if mood != "espaco": layers.append((down(_clouds(W2*ss, h*ss, rng, u, line)), .25))
    layers += [(sil(.62, .06, hills[0], False), .4), (sil(.74, .05, hills[1], True), .7), (sil(.9, .03, hills[2], True, 1.6), 1.0)]
    return layers

def mascote(h):
    """Nuvem sorridente (mascote NUBI) para o modo cartoon."""
    s = int(h * .24); u = s / 200
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    _blob(d, [(20*u, 60*u, 120*u, 170*u), (60*u, 20*u, 160*u, 150*u), (90*u, 70*u, 185*u, 170*u), (40*u, 100*u, 170*u, 180*u)], (255, 255, 255), (40, 60, 90), int(5*u))
    for ex in (80, 120): d.ellipse(((ex-7)*u, 95*u, (ex+7)*u, 117*u), fill=(30, 40, 60))
    d.arc((82*u, 105*u, 118*u, 140*u), 20, 160, fill=(30, 40, 60), width=int(4*u))
    for ex in (66, 134): d.ellipse(((ex-9)*u, 120*u, (ex+9)*u, 132*u), fill=(255, 150, 160))
    return img

def frames(layers, w, h, n, direcao=1, modo="parallax", sprite=None):
    """Gera n quadros RGB. parallax/cartoon: câmera lateral. 3d: câmera avança em perspectiva + órbita leve."""
    for i in range(n):
        t = i / max(1, n - 1); e = t * t * (3 - 2 * t)
        cam = direcao * (-1 + 2 * e) * (.55 if modo == "3d" else 1)
        canvas = None
        for img, dep in layers:
            s = 1.02 + (.30 * e * dep + .02 * e if modo == "3d" else .02 * e)
            cx = img.width / 2 + cam * dep * (img.width - w) / 2
            dy = math.sin(t * 9.4) * h * .006 * dep if modo == "3d" else 0
            lay = img.transform((w, h), Image.AFFINE, (1/s, 0, cx - w/(2*s), 0, 1/s, h/2 - h/(2*s) + dy), Image.BILINEAR)
            if canvas is None: canvas = lay
            else: canvas.alpha_composite(lay)
        if sprite is not None:
            canvas.alpha_composite(sprite, (int(w*.5 - sprite.width/2), int(h*.58 + math.sin(t * 25) * h * .02)))
        yield canvas.convert("RGB").tobytes()
