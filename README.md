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

## Escopo e próximas etapas do projeto

A entrega implementa composição 2D, renderização, narração, exportação, catálogo, retomada por cena e verificação por decodificação de áudio e vídeo. A interface atual é o notebook. O roteiro do exemplo é pré-escrito, a narração é sintética e os fundos são ilustrações procedurais. A seleção de legendas depende do player.

O briefing completo inclui um editor web com timeline, direção e roteiro por IA, ComfyUI, Remotion, modelos de vídeo, Blender e parallax por profundidade. Essas integrações ficam para etapas posteriores. A sequência proposta é expor o renderizador como serviço de tarefas, implementar a interface do editor, adicionar provedores opcionais e então validar os modos 2.5D e 3D.
