# NUBI Video AI Studio

Esta edição oferece um fluxo de produção em CPU dentro do notebook ou pelo terminal. O exemplo “How the Universe Began” traz cinco cenas com roteiro editorial em inglês. Para outros temas, escreva o roteiro e forneça imagens próprias ou utilize os fundos espaciais procedurais. O movimento usa zoom 2D. As legendas ficam em uma faixa selecionável no MP4 e também em arquivo SRT.

## Publicar e abrir no Colab

1. Extraia o ZIP no computador. No repositório público FelipeGomes070898/NUBI-ORCHESTRATOR, use **Add file → Upload files**. Arraste o conteúdo extraído, incluindo a pasta nubi. A raiz do repositório deve mostrar NUBI_Colab.ipynb, requirements.txt e a pasta nubi.
2. Confirme o envio em **Commit changes**. Se a branch for main, abra https://colab.research.google.com/github/FelipeGomes070898/NUBI-ORCHESTRATOR/blob/main/NUBI_Colab.ipynb . Para outra branch, substitua main no link.
3. Conecte uma sessão Python e escolha **Ambiente de execução → Executar tudo**. Acesso à internet é necessário para baixar código e dependências. A renderização e a voz usam o ambiente de execução.
4. Para outro vídeo, altere título, idioma, duração, formato, texto e caminhos das imagens na terceira célula e execute dela até o fim. Aceita imagens locais que o Pillow consiga abrir, como JPG, PNG e WebP. Cada linha de texto não vazia representa uma cena.
5. Baixe o MP4 ou escolha ZIP na última célula. Para manter os arquivos entre sessões, marque SALVAR_NO_DRIVE antes de renderizar. A pasta local /content é temporária.

## Usar no terminal Linux

Use Python 3.10 ou posterior, FFmpeg com libx264 e AAC, FFprobe e espeak-ng. No Ubuntu, instale os binários com `sudo apt-get install ffmpeg espeak-ng`. Em um ambiente virtual Python, rode `python -m pip install -r requirements.txt`. Na raiz, rode `python -m nubi`. Para testar, use `python -m unittest -v`.

Exemplo com texto próprio em português:

    python -m nubi --titulo "Minha história" --roteiro cenas.txt --idioma pt-br --vertical --duracao 30

Saída em producoes/<id>/video.mp4. Adicione um argumento --imagem por cena para substituir a arte procedural. Os arquivos projeto.json e publicacao.json descrevem as configurações e os capítulos. O catálogo SQLite registra os projetos concluídos.

## Diagnóstico

- Falha ao clonar: confirme que o repositório é público e contém os arquivos extraídos na raiz. Para atualizar o código do GitHub, abra uma sessão nova.
- Roteiro longo: ajuste a duração sugerida pelo erro ou encurte a fala. A distribuição de tempo entre cenas considera a duração medida das vozes.
- Interrupção: repita a renderização com as mesmas entradas e destino. Se uma cena armazenada estiver danificada, remova apenas o MP4 da cena afetada e execute novamente. Consulte render.log para erros do FFmpeg. Execute apenas uma renderização do mesmo projeto por vez.
- Sem espaço: exporte seus resultados e libere espaço. As cenas intermediárias são mantidas para a retomada.
- Vozes: espeak-ng atende inglês e português brasileiro. Se faltar espeak-ng, a instalação local pode usar o filtro flite do FFmpeg para o exemplo em inglês.

## Estilos de animação

| Estilo | O que faz |
|---|---|
| `cartoon` | 2D com contornos grossos: céu, astro, nuvens, colinas, árvores e o mascote nuvem sorridente. |
| `parallax` | Camadas (céu, nuvens, colinas) movidas em velocidades diferentes. Com imagem própria e mapa de profundidade (`--profundidade`, branco = perto), a imagem é separada em fundo, meio e frente. |
| `3d` | 2.5D: a câmera avança em perspectiva e orbita levemente; camadas próximas crescem mais rápido. Não é 3D real. |
| `zoom` | Modo original (zoom lento sobre uma imagem). |

O Diretor (`nubi/director.py`) escolhe humor (dia, tarde, noite, espaço) e sentido da câmera por cena e gera tags e hashtags. Hoje é por regras, não um LLM.

    python -m nubi --titulo "Minha história" --roteiro cenas.txt --idioma pt-br --estilo cartoon --duracao 30

## Dashboard

No Colab, execute a seção 3 do notebook. No terminal: `python -m nubi --painel` e abra http://127.0.0.1:8765. O painel mostra o estado do sistema, o formulário de ideia, a direção por cena, o progresso de narração, camadas e composição, o player do MP4 com miniatura, título, descrição, tags e hashtags, e o log. Só roda uma renderização por vez. Itens "em breve" na barra lateral ainda não têm função.

Desempenho: os estilos por camadas geram cada quadro em Python. Use 720p para testes. Em 1080p, 60 s levam alguns minutos em CPU.

## Estado do projeto

Implementado: composição 2D, estilos cartoon, parallax e 2.5D, narração sintética, legendas, exportação, catálogo, retomada por cena, verificação do MP4, Diretor por regras, dashboard web com API local e integração com Colab.

Pendente: Diretor com LLM, geração de imagens (ComfyUI), vozes neurais (Piper/Kokoro), 3D real (Blender/Three.js), estimativa automática de profundidade, Remotion, editor com timeline e publicação automática. Detalhes em `skill/nubi-studio/SKILL.md`.
