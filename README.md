# Nubi — projeto pessoal

Extraída do **Archive Studio AI** em 01/11/2026. Roda **sozinha**, só com CPU (Python 3.10+, `numpy` e `httpx`). O **cérebro já treinado vai junto**, na pasta `cerebro/`: é só descompactar e rodar (para usar outra pasta: `--home` ou `NUBI_HOME`).

```bash
pip install -r requirements.txt
python -m nubi                      # conversa no terminal
python -m nubi --say "oi"           # uma frase e sai
python -m nubi --study PASTA        # estuda o código/README de uma pasta
python -m nubi --home ~/Drive/nubi  # cérebro numa pasta sua (ex.: Drive sincronizado)
python -m nubi --export cerebro.zip # / --import cerebro.zip: leva o cérebro para outro computador
python -m nubi --force              # aprendizado FORÇADO: treina até acertar tudo que ela já foi ensinada
python -m nubi --lang [ARQUIVO|PASTA]  # treina a linguagem neural (opcional: com mais texto .txt/.md seu)
python -m nubi --write "rede neural"   # ela escreve frases sobre o tema com a linguagem neural
pytest                              # 25 testes
```

No chat: «force o aprendizado» · «treine a linguagem» · «fale sobre …» · «continue: …».

## Aprendizado forçado e linguagem neural (novo)

**Aprendizado forçado** (`nubi/force.py`). O ensino normal mostra cada exemplo poucas vezes; com muita coisa ensinada um exemplo corrigido estraga outro.
O modo forçado monta o **currículo** (tudo que foi ensinado, agora salvo em `mind.json` como `examples`, mais as intenções de fábrica e os cartões estudados) e
**paráfrases** de cada exemplo, prova a rede **só com os picos** (sem a memória de padrões) e repete a regra de erro com margem sobre todos os exemplos, em lotes,
por centenas de épocas. Se a saída esparsa não consegue separar tudo, a rede **cresce** (`SpikingNet.grow_readout`, sinaptogênese: de 20 % a 100 % de conectividade
oculta→saída). Depois um polimento reforça o que a prova real ainda erra e guarda a melhor versão. O humor (reforço) não é tocado e é conferido no fim.
A generalização é medida com paráfrases que **nunca** entram no treino.

Medido neste projeto (800 neurônios, 186 exemplos): acerto só com a rede de picos **33 % → 96 %**; paráfrases inéditas **36 % → 79 %**; humor 86 % → 86 %; ~30 s.
Ela ainda erra frases de 2 palavras muito parecidas com outras (ex.: «boa noite») e paráfrases muito diferentes: o forçado não faz milagre sobre o que a codificação não separa.

**Linguagem neural** (`nubi/lang.py`). Um modelo de linguagem em palavras, só numpy: 3 palavras de contexto → embeddings → camada oculta tanh → softmax (Adam, parada
antecipada na validação), misturado na geração com um trigrama contado no mesmo texto; gera vários candidatos e fica com o mais provável. O corpus é o que ela
estudou, os fatos e as respostas que você ensinou, mais qualquer texto seu (`--lang ARQUIVO`). **Limite honesto:** com o corpus de um projeto pequeno (~2 mil palavras)
ela escreve frases que lembram o material, às vezes truncadas ou sem sentido; não responde com fatos confiáveis (para isso há a busca nos cartões e o provedor).
Quanto mais texto em português você der, melhor. Salvo em `lm.npz`, incluído no `--export`/`--import`.

Launchers: `tools/iniciar_nubi_windows.bat` e `tools/iniciar_nubi_mac_linux.sh`. Provedor de IA opcional (OmniRoute, LM Studio, Ollama, OpenRouter…):
`NUBI_PROVIDER_URL`, `NUBI_PROVIDER_MODEL`, `NUBI_PROVIDER_KEY`, `NUBI_PROVIDER_MODE` (`off` | `auto` | `sempre`).

## O que mudou ao tirá-la do Archive Studio

* `nubi/_compat.py` substitui o que ela pegava emprestado do sistema (pasta de dados, configurações por variável de ambiente, `Criteria`, `similarity`).
* **Sem painel web** (aba 🧠 Nubi) e **sem as ações que mexiam no sistema** («criar vídeo», «descobrir vídeos»): essas dependiam do Archive Studio. O código das ações continua em `nubi/actions.py`
  e responde que precisa do painel quando ele não existe. As frases de treino embutidas ainda falam do Archive Studio; troque os rótulos em `nubi/actions.py` (`INTENTS`) pelos do seu projeto.
* O estudo (`source.py`) lê qualquer pasta: `README.md`, módulos `.py` e, se existir, a estrutura `archive_studio/`.

## Como foi feita (documentação original)

## 🧠 Nubi — a IA do sistema (rede neural de picos)

A **Nubi** é uma rede neural de picos (**SNN**, *spiking neural network*) que mora dentro do sistema e funciona só com **CPU**, no seu PC e no Colab
(`python -m archive_studio nubi` conversa com ela no terminal, sem painel). Fica na aba **🧠 Nubi** do painel.

* **Fica atualizada sozinha:** se o código/README mudou desde o último estudo, a Nubi **reestuda o sistema em segundo plano** quando é aberta (só se ela já tinha estudado antes; `NUBI_AUTOSTUDY=0` desliga). Assim ela conhece os recursos novos (formatos, cartum, animação…) sem você clicar em «Estudar».
* **Neurônios e sinapses:** de **250 a 1000 neurônios** (padrão 800; `NUBI_NEURONS` muda na criação) e **mais de 7000 sinapses** (o padrão tem ~33 mil).
  Camadas: entrada (palavras da frase + 8 sensores do sistema) → camada oculta recorrente (80 % excitatória, 20 % inibitória) → saída (uma população por rótulo).
  Cada neurônio é do tipo *integra-e-dispara com vazamento*: **acumula carga elétrica, a carga vaza com o tempo e ele DISPARA quando atinge o limiar**,
  volta ao repouso e fica um instante refratário; o limiar se adapta (homeostase).
* **Aprende a qualquer momento**, de quatro jeitos: **(1) ensino** — «aprenda: frase => resposta», «quando eu disser X faça status», «aprenda que …»
  (regra local de erro nas sinapses oculta→saída, poucas apresentações); **(2) reforço** — “certo/errado/👍/👎”, confirmar ou cancelar uma ação: o
  sinal de recompensa vira mudança de peso por **STDP modulado por recompensa** (traço de elegibilidade) e por gradiente de política; **(3) STDP** a cada frase;
  **(4) estudar o código-fonte** — o botão **📚 Estudar o código-fonte** (ou «estude o código») lê módulos, funções, rotas da API, o README e as telas,
  cria ~700 trechos de conhecimento e treina a rede para saber de que assunto cada pergunta trata. Reestudar é incremental.
* **Memória associativa de padrões de picos:** cada exemplo aprendido guarda a “assinatura” de picos que ele provocou na camada oculta; a decisão final
  soma a saída da rede com a semelhança a essas assinaturas (aprende de 1 exemplo só e esquece o exemplo que levou a um erro).
* **O que ela faz:** responde sobre o sistema com trechos reais do código/README («como funciona a miniatura?»), diz o estado do Maestro e das produções,
  lista projetos, dá ideias de miniatura, **cria vídeos** («crie um vídeo sobre …» → ela pede confirmação), estuda o código e responde o que você ensinou.
  O **humor** (ALERTA / COMEMORAR / OBSERVAR / DESCANSAR) vem dos sensores (erro, sucesso, produção rodando, silêncio…) e foi aprendido **por reforço**.
  O painel desenha o “cérebro” ao vivo: os neurônios que dispararam na última frase, quadro a quadro.
* **Provedores (OmniRoute e outros):** em **🔌 Provedores de IA** aponte a Nubi para qualquer endpoint compatível com OpenAI — o **OmniRoute** (que junta
  muitos provedores num endereço só; porta e chave conforme a sua instalação), LM Studio, Ollama, OpenRouter… Modo **Automático** consulta quando a rede não
  sabe; **Sempre** consulta em toda pergunta de assunto. Se você disser «certo», ela **aprende a resposta** e passa a responder sozinha sem consultar de novo.
  Vai para o provedor só a sua pergunta e trechos do código/README (nunca a chave nem arquivos de projeto); a chave fica só no servidor. No Colab o
  provedor precisa de um endereço acessível de lá (`localhost` seria o próprio Colab). O mesmo endereço serve para o LLM de roteiros em **Sistema → LLM
  compatível com OpenAI**.
* **Limites honestos:** é uma rede pequena que **associa padrões e escolhe ações** — não é um modelo de linguagem e não escreve textos livres (para isso existe o
  provedor). Acerta quase tudo que foi ensinado e a maioria das paráfrases, mas pode errar frases novas; por isso o reforço. O humor aprendido acerta cerca de
  70–85 % das situações de teste e melhora com o uso. Tudo é salvo em disco (`nubi/` na pasta de dados; no Drive se o painel usa o Drive). A criação inicial
  (treino das intenções e do humor) leva cerca de 30–40 s na primeira vez.

## Pesquisa de vídeos (parte que ficou no Archive Studio)

A habilidade de pesquisa (`nubi/search.py`: critérios, gostos e estratégias por reforço) continua aqui, mas a **chamada à API do YouTube** (`youtube/discover.py`) ficou no Archive Studio.
No Archive Studio a aba «Descobrir» segue funcionando, guardando as preferências num arquivo próprio.

## Voltar a ligar no Archive Studio

O Archive Studio guarda tudo no histórico do git. O último commit COM a Nubi integrada foi `0c47649` (branch `claude/optimistic-heisenberg-oivnmm`):

```bash
git show 0c47649:archive_studio/nubi/brain.py   # ver
git checkout 0c47649 -- archive_studio/nubi tools/nubi_pc archive_studio/server/static/nubi.js tests/test_nubi.py tests/test_nubi_pc.py
```
