"""Renderizador CPU. Cada parágrafo forma uma cena com narração e legenda."""
import hashlib
import json
import shutil
import sqlite3
import subprocess
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from . import director, parallax

ESTILOS = ("zoom", "parallax", "cartoon", "3d")

UNIVERSE = [
    "The universe began in a hot, dense state. Space itself expanded, carrying matter and light along with it.",
    "As space expanded, the universe cooled. Within the first few minutes, protons and neutrons joined to form the nuclei of light elements.",
    "Much later, electrons bound to nuclei. Light could travel freely. We still detect that ancient radiation as the cosmic microwave background.",
    "Gravity drew gas into dense pockets. Inside the first stars, pressure and heat allowed hydrogen nuclei to fuse and release energy.",
    "Groups of stars formed galaxies. By observing distant galaxies, astronomers see light that has traveled for billions of years."
]

def run(args, folder):
    with (folder / "render.log").open("ab") as log:
        result = subprocess.run(args, cwd=folder, stdout=log, stderr=log, timeout=1800)
    if result.returncode:
        raise RuntimeError((folder / "render.log").read_text(errors="replace")[-2200:])

def pipe(args, folder, gen):
    """Envia quadros RGB gerados em Python ao FFmpeg pela entrada padrão."""
    with (folder / "render.log").open("ab") as log:
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", *args], cwd=folder,
                             stdin=subprocess.PIPE, stdout=log, stderr=log)
        try:
            for frame in gen: p.stdin.write(frame)
            p.stdin.close()
        except BrokenPipeError: pass
        if p.wait(): raise RuntimeError((folder / "render.log").read_text(errors="replace")[-2200:])

def ff(args, folder):
    run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-filter_threads", "2", *args], folder)

def probe(path):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_format",
        "-show_streams", "-of", "json", str(path)], timeout=30))

def timestamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"

def artwork(path, size, seed, index):
    w, h = size
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype("float32")
    x, y = (x-w*.50)/w, (y-h*.48)/w
    r = np.sqrt(x*x + y*y)
    a = np.arctan2(y, x)
    arms = (.5 + .5*np.cos(2*a - 15*r + index))**5
    glow = np.exp(-5*r) * (.22 + .78*arms) + .85*np.exp(-24*r)
    colors = np.array([(245,129,66),(126,152,244),(173,103,211),(231,166,92),(114,164,233)])
    pixels = np.clip(np.array([6,10,24]) + glow[:,:,None]*colors[index%5], 0, 255)
    image = Image.fromarray(pixels.astype("uint8"))
    draw = ImageDraw.Draw(image)
    for _ in range(w*h//700):
        px, py = int(rng.integers(w)), int(rng.integers(h))
        radius = int(rng.choice([0,0,1,1,2]))
        lum = int(rng.integers(75,240))
        draw.ellipse((px-radius,py-radius,px+radius,py+radius), fill=(lum,lum,min(255,lum+25)))
    image.save(path)

def render(title, script, language, seconds, vertical, height, root, images=(), style="zoom", depths=(), cb=None):
    cb = cb or (lambda *a: None)
    lines = [line.strip() for line in script.splitlines() if line.strip()]
    if not lines and title.strip().lower() == "how the universe began" and language == "en":
        lines = UNIVERSE
    if not lines or len(lines)>60 or sum(map(len,lines))>20000:
        raise ValueError("Escreva de 1 a 60 parágrafos, até 20 mil caracteres, ou use o exemplo em inglês.")
    if not 3*len(lines)<=seconds<=1800 or height not in (360,720,1080) or language not in ("en","pt-br"):
        raise ValueError("Use pelo menos 3 segundos por cena, até 1800 s, e uma resolução e idioma disponíveis.")
    if images and len(images)!=len(lines):
        raise ValueError("Forneça uma imagem por cena ou deixe a lista vazia.")
    settings = dict(version=1,title=title, scenes=lines,language=language,seconds=seconds,
                    vertical=vertical,height=height, images=[hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in images])
    if style not in ESTILOS: raise ValueError("Estilo inválido: " + style)
    if style != "zoom":
        settings.update(style=style, depths=[hashlib.sha256(Path(p).read_bytes()).hexdigest() if p else "" for p in depths])
    key = hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()[:20]
    folder = Path(root).resolve()/key
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"projeto.json").write_text(json.dumps(settings,ensure_ascii=False,indent=2))
    plan = director.plan(lines)
    seed = int(key[:8], 16)
    w,h = height*16//9,height
    if vertical: w,h=h,w
    lengths = []
    for i,line in enumerate(lines):
        name = f"cena-{i+1:02}"
        wav = folder/f"{name}.wav"
        if not wav.exists():
            tmp = folder/"voz.tmp.wav"
            if shutil.which("espeak-ng"):
                run(["espeak-ng","-v",language,"-s","157","-w",str(tmp),"--",line],folder)
            elif language=="en":
                (folder/"fala.txt").write_text(line)
                ff(["-f","lavfi","-i","flite=textfile=fala.txt:voice=slt",tmp.name],folder)
            else: raise RuntimeError("Instale espeak-ng para narrar em português.")
            probe(tmp)
            tmp.replace(wav)
        lengths.append(float(probe(wav)["format"]["duration"]))
        cb("voz", (i+1)/len(lines), f"Narração {i+1}/{len(lines)}")
    weights = np.array(lengths)
    if weights.sum()>seconds*1.30:
        raise ValueError(f"A fala ocupa {weights.sum():.1f} s. Aumente a duração ou encurte o roteiro.")
    ends = [0]+np.rint(np.cumsum(weights)/weights.sum()*seconds*30).astype(int).tolist()
    subtitles=[]
    for i,line in enumerate(lines):
        name=f"cena-{i+1:02}"
        frames=ends[i+1]-ends[i]
        dur=frames/30
        segment=folder/f"{name}.mp4"
        print(f"Cena {i+1}/{len(lines)} · {dur:.1f} s",flush=True)
        cb("cenas", i/len(lines), f"Cena {i+1}/{len(lines)} · {dur:.1f} s · {style}")
        if frames<1: raise ValueError("Duração insuficiente para uma das cenas.")
        pic=folder/f"{name}.jpg"
        if not segment.exists():
            speed=max(1,lengths[i]/dur)
            enc=["-c:v","libx264","-threads","2","-preset","veryfast","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","1","parte.tmp.mp4"]
            if style=="zoom":
                if images:
                    with Image.open(images[i]) as img:
                        ImageOps.fit(ImageOps.exif_transpose(img).convert("RGB"),(w,h)).save(pic)
                else: artwork(pic,(w,h),seed+i,i)
                zoom=f"zoompan=z='1.00+0.10*on/{frames}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s={w}x{h}:fps=30"
                ff(["-i",pic.name,"-i",name+".wav","-vf",zoom,"-af",f"atempo={speed:.6f},apad","-t",f"{dur:.8f}",*enc],folder)
            else:
                img = Image.open(images[i]) if images else None
                dm = Image.open(depths[i]) if i < len(depths) and depths[i] else None
                layers = parallax.build_layers(plan[i]["humor"], w, h, seed+i, style, img, dm)
                sprite = parallax.mascote(h) if style == "cartoon" else None
                pipe(["-f","rawvideo","-pix_fmt","rgb24","-s",f"{w}x{h}","-r","30","-i","-","-i",name+".wav",
                      "-af",f"atempo={speed:.6f},apad","-t",f"{dur:.8f}",*enc], folder,
                     parallax.frames(layers, w, h, frames, plan[i]["direcao"], style, sprite))
            probe(folder/"parte.tmp.mp4")
            (folder/"parte.tmp.mp4").replace(segment)
        subtitles.append(f"{i+1}\n{timestamp(ends[i]/30)} --> {timestamp(ends[i+1]/30)}\n"+textwrap.fill(line,55)+"\n")
    (folder/"legendas.srt").write_text("\n".join(subtitles))
    cb("composicao", .5, "Montando o MP4 final")
    (folder/"lista.txt").write_text("".join(f"file 'cena-{i+1:02}.mp4'\n" for i in range(len(lines))))
    ff(["-f","concat","-safe","1","-i","lista.txt","-i","legendas.srt","-map","0:v","-map","0:a","-map","1:0",
        "-c","copy","-c:s","mov_text","-disposition:s:0","default","-movflags","+faststart","saida.tmp.mp4"],folder)
    info=probe(folder/"saida.tmp.mp4")
    codecs={s["codec_name"] for s in info["streams"]}
    if not {"h264","aac","mov_text"}<=codecs or abs(float(info["format"]["duration"])-seconds)>0.5:
        raise RuntimeError("O arquivo final falhou na conferência de duração ou faixas.")
    ff(["-xerror","-i","saida.tmp.mp4","-map","0:v","-map","0:a","-f","null","-"],folder)
    (folder/"saida.tmp.mp4").replace(folder/"video.mp4")
    if not (folder/"cena-01.jpg").exists(): ff(["-i","cena-01.mp4","-frames:v","1","cena-01.jpg"],folder)
    shutil.copyfile(folder/"cena-01.jpg",folder/"miniatura.jpg")
    (folder/"publicacao.json").write_text(json.dumps(dict(titulo=title,descricao=lines[0],estilo=style,**director.metadados(title,lines),
        capitulos=[dict(inicio=ends[i]/30,texto=l) for i,l in enumerate(lines)]),ensure_ascii=False,indent=2))
    with sqlite3.connect(folder.parent/"catalogo.sqlite") as db:
        db.execute("CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,title TEXT, path TEXT)")
        db.execute("INSERT OR REPLACE INTO projects VALUES(?,?,?)",(key,title,str(folder)))
    cb("pronto", 1, "Vídeo validado")
    return folder
