import argparse
from pathlib import Path
from .render import render

parser = argparse.ArgumentParser(description="Produção de vídeo em CPU")
parser.add_argument("--titulo", default="How the Universe Began")
parser.add_argument("--roteiro", type=Path, help="TXT UTF-8, uma cena por linha")
parser.add_argument("--idioma", choices=["en","pt-br"], default="en")
parser.add_argument("--duracao", type=int, default=60)
parser.add_argument("--resolucao", type=int, choices=[360,720,1080], default=1080)
parser.add_argument("--vertical", action="store_true")
parser.add_argument("--imagem", action="append", default=[])
parser.add_argument("--saida", default="producoes")
args = parser.parse_args()
folder = render(args.titulo, args.roteiro.read_text(encoding="utf-8") if args.roteiro else "",
                args.idioma,args.duracao,args.vertical,args.resolucao,args.saida,args.imagem)
print(folder/"video.mp4")
