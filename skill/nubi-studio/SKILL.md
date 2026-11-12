---
name: nubi-studio
description: Explica como o NUBI Video AI Studio funciona (renderizador em CPU, estilos cartoon/parallax/2.5D, diretor por regras, dashboard e notebook Colab) e registra onde o desenvolvimento parou. Use ao continuar, depurar ou estender o projeto NUBI_ORCHESTRATOR, ou quando o usuário pedir o estado atual, próximos passos ou como rodar o sistema.
---

# NUBI Video AI Studio: como funciona e onde parou

## Objetivo
Transformar uma ideia (tema, roteiro, idioma, duração) em um vídeo final: MP4 + miniatura + título + descrição + tags + hashtags + legendas SRT. Fluxo alvo: **ideia → diretor → imagens / narração / animação / composição → vídeo final**.

## Estrutura do repositório
| Arquivo | Função |
|---|---|
| `nubi/render.py` | Orquestra tudo: valida entradas, narra, anima cada cena, concatena, verifica e registra. Função `render(title, script, language, seconds, vertical, height, root, images, style, depths, cb)`. |
| `nubi/parallax.py` | Motor de camadas. `build_layers()` cria céu, astro, nuvens e colinas (ou usa imagem + profundidade); `frames()` gera quadros RGB; `mascote()` desenha a nuvem do modo cartoon. |
| `nubi/director.py` | Diretor por regras: `plan()` define humor e sentido da câmera por cena; `metadados()` gera tags e hashtags. |
| `nubi/dashboard.py` + `nubi/static/dashboard.html` | Servidor HTTP (biblioteca padrão) e interface. API: `/api/status`, `/api/plano`, `/api/render`, `/api/jobs`, `/api/projetos`, `/files/<id>/<arquivo>`. |
| `nubi/__main__.py` | CLI: `--estilo`, `--profundidade`, `--painel`. |
| `NUBI_Colab.ipynb` | Clona o GitHub, instala FFmpeg/espeak-ng, abre o dashboard por `serve_kernel_port_as_iframe` ou renderiza manualmente. |
| `test_nubi.py` | Testes: vídeo vertical, retomada por cena, 3 estilos, diretor. |

## Como o render funciona
1. Cada linha do roteiro vira uma cena. A chave do projeto é um hash das entradas (inclui estilo e profundidades), então repetir a chamada retoma o trabalho.
2. Voz: `espeak-ng` (en, pt-br); sem ele, filtro `flite` do FFmpeg (só inglês).
3. A duração de cada cena é proporcional à duração medida da fala, escalada para `seconds`.
4. Animação: `zoom` usa `zoompan` do FFmpeg; `parallax`, `cartoon` e `3d` geram quadros em Python e os enviam ao FFmpeg por stdin (`pipe()`). Cena pronta = `cena-NN.mp4` existente; só é refeita se o arquivo for apagado.
5. Concatenação com legendas `mov_text`, conferência de codecs e duração, decodificação completa, `video.mp4`, `miniatura.jpg`, `publicacao.json` e registro em `catalogo.sqlite`.
6. `cb(etapa, pct, msg)` informa progresso (etapas: voz, cenas, composicao, pronto). O dashboard usa isso.

## Estilos
- `cartoon`: 2D com contorno, nuvens, colinas, árvores e mascote.
- `parallax`: camadas com fatores de profundidade 0,05 / 0,25 / 0,4 / 0,7 / 1,0. Com imagem + mapa de profundidade (branco = perto), separa fundo, meio e frente.
- `3d`: 2.5D. Escala por camada cresce com a profundidade (câmera avançando) e há órbita lateral e leve oscilação vertical.
- `zoom`: modo original.

## Como rodar
- Colab: publicar o conteúdo no GitHub (raiz com `NUBI_Colab.ipynb`, `requirements.txt`, `nubi/`), abrir o notebook, Executar tudo, usar a seção 3 (dashboard).
- Terminal: `python -m nubi --painel` (http://127.0.0.1:8765) ou `python -m nubi --titulo ... --estilo cartoon`. Testes: `python -m unittest -v`.
- Dependências: Python 3.10+, numpy, Pillow, FFmpeg (libx264, AAC), espeak-ng.

## Onde parou (estado atual)
**Pronto e testado:** renderizador CPU com retomada; estilos cartoon, parallax e 2.5D; Diretor por regras; dashboard (status do sistema, formulário, direção, progresso, player, metadados, log, lista de projetos); notebook com dashboard embutido; testes passando (vídeo vertical, 3 estilos, diretor); API do dashboard testada de ponta a ponta com um job real.

**Não feito:**
1. Diretor com LLM (roteiro, narrativa e plano visual). `director.plan()` é o ponto de troca.
2. Imagens por IA (ComfyUI). Hoje só ilustrações procedurais ou imagens do usuário. O indicador "ComfyUI" do painel é fixo em "não conectado".
3. Vozes neurais (Piper/Kokoro). A voz atual é sintética básica.
4. 3D real (Blender/Three.js). O modo `3d` é 2.5D com camadas.
5. Estimativa automática de profundidade. O parallax por imagem exige mapa de profundidade fornecido; o painel ainda não tem campo para ele (só a CLI com `--profundidade`).
6. Remotion, editor com timeline, trilha sonora/efeitos (Audio Engine) e publicação automática. Itens "em breve" da barra lateral.
7. Não testado: execução real no Colab (o ambiente de desenvolvimento não tinha acesso ao Colab), 1080p longo, GPU e espeak-ng em português (o ambiente de teste usou flite).
8. Dashboard: uma renderização por vez, sem fila persistente nem cancelamento; jobs somem ao reiniciar o servidor (os arquivos ficam).

## Próximos passos sugeridos (ordem)
1. Testar no Colab e corrigir o que aparecer.
2. Campo de mapa de profundidade e upload de imagens no painel; depois profundidade automática (modelo MiDaS/Depth Anything).
3. Diretor com LLM gerando roteiro e plano por cena (mesmo formato de `plan()`).
4. Provedor de imagens ComfyUI por API, com fallback para o procedural.
5. Piper/Kokoro como motor de voz opcional.
6. Fila de jobs com cancelamento; editor de timeline; Blender/Three.js; publicação.

## Cuidados ao editar
- Mudar qualquer entrada altera a chave do projeto (nova pasta). Mudar o código de uma cena não invalida cenas já salvas: apague o `cena-NN.mp4` afetado.
- Nunca rodar duas renderizações do mesmo projeto ao mesmo tempo.
- O dashboard serve só arquivos de uma lista fixa em pastas com id hexadecimal de 20 caracteres; mantenha essa validação.
