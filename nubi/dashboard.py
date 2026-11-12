"""Dashboard web do NUBI Video AI Studio (somente biblioteca padrão). Roda local ou dentro do Colab."""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import director
from .render import render

HTML = Path(__file__).with_name("static") / "dashboard.html"
ARQUIVOS = {"video.mp4": "video/mp4", "miniatura.jpg": "image/jpeg", "legendas.srt": "text/plain; charset=utf-8",
            "publicacao.json": "application/json", "render.log": "text/plain; charset=utf-8"}
JOBS, LOCK = {}, threading.Lock()
DESTINO = Path("producoes")

def sistema():
    mem = dict(l.split(":", 1) for l in Path("/proc/meminfo").read_text().splitlines()) if Path("/proc/meminfo").exists() else {}
    kb = lambda k: int(mem[k].split()[0]) if k in mem else 0
    total, livre = kb("MemTotal"), kb("MemAvailable")
    gpu = None
    if shutil.which("nvidia-smi"):
        try: gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], text=True, timeout=5).strip()
        except Exception: pass
    cpus = os.cpu_count() or 1
    return dict(cpu=f"{cpus} núcleos ({min(100, round(os.getloadavg()[0] / cpus * 100))}%)" if hasattr(os, "getloadavg") else f"{cpus} núcleos",
                ram=f"{total/1048576:.1f} GB ({round(100*(total-livre)/total) if total else 0}%)",
                gpu=gpu or "sem GPU (modo CPU)", python=sys.version.split()[0],
                ffmpeg=bool(shutil.which("ffmpeg")), espeak=bool(shutil.which("espeak-ng")), blender=bool(shutil.which("blender")),
                comfyui=False)

def projetos():
    db = DESTINO / "catalogo.sqlite"
    if not db.exists(): return []
    with sqlite3.connect(db) as c:
        return [dict(id=i, titulo=t) for i, t, _ in c.execute("SELECT * FROM projects")][::-1]

def iniciar(d):
    with LOCK:
        if any(j["estado"] == "rodando" for j in JOBS.values()): raise RuntimeError("Já existe uma renderização em andamento.")
        jid = uuid.uuid4().hex[:8]
        job = JOBS[jid] = dict(id=jid, estado="rodando", etapa="diretor", pct=0, log=[], titulo=d["titulo"], projeto=None, erro=None,
                               etapas=dict(voz=0, cenas=0, composicao=0))
    def cb(etapa, pct, msg):
        job["etapa"] = etapa
        if etapa in job["etapas"]: job["etapas"][etapa] = pct
        job["log"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    def run():
        try:
            lines = [l for l in d["roteiro"].splitlines() if l.strip()]
            cb("diretor", 1, f"Diretor planejou {len(lines) or 5} cenas · estilo {d['estilo']}")
            imgs = [x.strip() for x in d.get("imagens", "").splitlines() if x.strip()]
            pasta = render(d["titulo"], d["roteiro"], d["idioma"], int(d["duracao"]), d["formato"] == "9:16",
                           int(d["resolucao"]), DESTINO, imgs, d["estilo"], (), cb)
            job.update(estado="pronto", projeto=pasta.name, publicacao=json.loads((pasta / "publicacao.json").read_text()))
        except Exception as e:
            job.update(estado="erro", erro=str(e)[-600:]); job["log"].append("ERRO: " + str(e)[-300:])
    threading.Thread(target=run, daemon=True).start()
    return jid

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send_json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/": b = HTML.read_bytes(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); return self.wfile.write(b)
        if path == "/api/status": return self.send_json(sistema())
        if path == "/api/projetos": return self.send_json(projetos())
        if path == "/api/jobs": return self.send_json(list(JOBS.values())[::-1][:20])
        m = re.fullmatch(r"/files/([0-9a-f]{20})/([\w.]+)", path)
        if m and m[2] in ARQUIVOS and (DESTINO / m[1] / m[2]).is_file(): return self.arquivo(DESTINO / m[1] / m[2], ARQUIVOS[m[2]])
        self.send_json({"erro": "não encontrado"}, 404)
    def arquivo(self, f, tipo):
        size, start, end = f.stat().st_size, 0, f.stat().st_size - 1
        r = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if r: start = int(r[1] or 0); end = int(r[2]) if r[2] else end
        self.send_response(206 if r else 200); self.send_header("Content-Type", tipo); self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if r: self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        with f.open("rb") as fh:
            fh.seek(start); left = end - start + 1
            while left > 0 and (chunk := fh.read(min(65536, left))): self.wfile.write(chunk); left -= len(chunk)
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        try:
            if self.path == "/api/plano":
                lines = [l for l in d.get("roteiro", "").splitlines() if l.strip()]
                return self.send_json(dict(cenas=director.plan(lines), **director.metadados(d.get("titulo", ""), lines)))
            if self.path == "/api/render": return self.send_json(dict(id=iniciar(d)))
        except Exception as e: return self.send_json({"erro": str(e)}, 400)
        self.send_json({"erro": "não encontrado"}, 404)

def serve(port=8765, destino="producoes", bloquear=False):
    global DESTINO
    DESTINO = Path(destino); DESTINO.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    if bloquear: print(f"NUBI Dashboard em http://127.0.0.1:{port}"); srv.serve_forever()
    else: threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
