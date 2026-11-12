"""Diretor por regras: planeja humor visual e câmera de cada cena e gera metadados.
Ponto de extensão: troque plan() por uma chamada a um LLM quando houver provedor."""
import re
from collections import Counter

HUMORES = {
    "espaco": ("universe","cosmos","galax","star","space","planet","big bang","universo","estrela","espaço","planeta"),
    "noite": ("night","dark","moon","dream","noite","escuro","lua","sonho"),
    "tarde": ("sunset","evening","memory","past","tarde","pôr do sol","memória","passado"),
    "dia": ("day","sun","green","forest","life","dia","sol","floresta","vida"),
}
STOP = set("the and with that this from into were which have their about para como uma mais pelo pela entre quando sobre ainda ".split())

def plan(lines):
    cenas = []
    for i, line in enumerate(lines):
        low = line.lower()
        humor = next((m for m, ks in HUMORES.items() if any(k in low for k in ks)), ("dia", "tarde", "noite")[i % 3])
        cenas.append(dict(cena=i + 1, humor=humor, direcao=1 if i % 2 == 0 else -1, texto=line))
    return cenas

def metadados(title, lines):
    words = [w for w in re.findall(r"[a-zà-ú]{5,}", " ".join(lines).lower()) if w not in STOP]
    tags = [w for w, _ in Counter(words).most_common(6)]
    return dict(tags=tags, hashtags=["#" + re.sub(r"\W", "", t.title()) for t in [title] + tags[:3]] + ["#NubiVideoAI"])
