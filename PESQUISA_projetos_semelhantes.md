# Projetos semelhantes encontrados na Internet

**Data da pesquisa:** 2026-10-17
**Escopo:** as duas frentes deste repositório — (A) `gba-decomp` (engenharia reversa /
modificação de ROM de GBA, FireRed `BPRE`) e (B) `universal-adaptive-ai-optimizer`
(`uaao`, camada externa de otimização de prompts com ciclo
BASELINE → … → REGISTRO, memória SQLite e proteção contra regressão) — mais
(C) a interseção IA + engenharia reversa.

**Método e limite honesto:** busca na web (11 consultas) + leitura das páginas de
3 repositórios (gba-harness, gba-decomp-toolkit, HexManiacAdvance-CE).
**Nenhum projeto abaixo foi clonado, instalado ou executado neste turno.**
Tudo o que está escrito é "o projeto declara fazer X", não "medimos que faz X".
Antes de executar código de qualquer um deles, vale a regra já adotada aqui:
revisar o código primeiro.

---

## Resumo executivo — 4 achados que mudam decisões

1. **O FireRed já tem decompilação completa e *matching*:** o
   [pret/pokefirered](https://github.com/pret/pokefirered) reconstrói o C que
   compila para ROM byte-idêntica (com o `agbcc`). Não precisamos redescobrir
   layouts que ele já documenta (`SaveBlock1`, `gBagPockets` etc. — que de fato
   já usamos). **Ressalva medida:** a nossa ROM é uma imagem modificada por
   terceiros, então endereço nenhum do pret pode ser confiado sem conferência
   na nossa imagem — que é o que o `gba-decomp` já faz.
2. **O análogo mais próximo do nosso `injetar_c.py` já existe e é maduro: o
   CFRU** ([Complete-Fire-Red-Upgrade](https://github.com/Skeli789/Complete-Fire-Red-Upgrade)).
   Ele injeta C/Thumb compilado numa ROM `BPRE0.gba` binária, com um
   `BPRE.ld` que expõe funções/RAM do jogo original como símbolos do linker e
   um `OFFSET_TO_PUT` configurável. É a prova externa de que o caminho
   "patch binário + C injetado" (o nosso) é viável em escala — e o `BPRE.ld`
   dele é um mapa de símbolos candidato para nós (a validar endereço a endereço).
3. **Existem harnesses de emulação prontos comparáveis ao nosso
   `emulador_console.py`** — em especial o
   [gba-harness](https://github.com/MaqsudMallick/gba-harness) (mGBA libretro
   via ctypes, "`retro_run()` é exatamente um quadro", input frame-exato) e o
   [libretro.py](https://github.com/JesseTG/libretro.py). São o candidato nº 1
   para o **teste de controle** que falta no bloqueio atual ("o jogo não sai
   do título no nosso harness"): rodar a mesma ROM num harness de terceiros
   separa "defeito do nosso harness" de "comportamento do jogo/core".
4. **No lado `uaao`, o ciclo que implementamos já é o padrão da área** —
   [GEPA](https://github.com/gepa-ai/gepa) / [DSPy](https://github.com/stanfordnlp/dspy)
   fazem geração→avaliação→seleção com frente de Pareto, e o
   [promptfoo](https://github.com/promptfoo/promptfoo) faz avaliação/regressão
   com assertions determinísticas primeiro. **Mas** GEPA/DSPy/TextGrad dependem
   de LLM como otimizador/avaliador, o que conflita com a decisão de escopo
   registrada para este projeto (*deterministic_only*, sem adaptadores LLM).
   O que dá para aproveitar sem mudar o escopo: o modelo de versionamento do
   [MLflow Prompt Registry](https://mlflow.org/docs/latest/genai/prompt-registry/)
   (versões imutáveis + alias mutável `production`/`staging` = nosso "reverter"
   com outro nome) e o catálogo de assertions determinísticas do promptfoo.

---

## A. GBA / engenharia reversa / modificação de ROM

### A1. Decompilação em nível de fonte (C que recompila o jogo)

| Projeto | O que é | Relação com o nosso |
|---|---|---|
| [pret/pokefirered](https://github.com/pret/pokefirered) | Decomp de FireRed/LeafGreen; compila ROMs `pokefirered.gba`, `pokefirered_rev1.gba` etc. com sha1 publicados; ~300 arquivos C em `src/`, ferramentas próprias (`gbagfx`, `mid2agb`, `jsonproc`), compilador original `agbcc` para match byte a byte | **Fonte de verdade de layouts** que já usamos. É também o caminho "modificar o que desejar e compilar" completo — ao custo de abandonar a ROM hackeada atual e trabalhar sobre o fonte |
| [pret/pokeemerald](https://github.com/pret/pokeemerald), [pret/pokeruby](https://github.com/pret/pokeruby), [pret (org)](https://github.com/pret) | Mesma família para Emerald, Ruby/Sapphire, Red/Blue, Crystal, Platinum, Pinball RS… | Referência cruzada: a engine Gen 3 é compartilhada; nomes de funções de um costumam valer no outro |
| [rh-hideout/pokeemerald-expansion](https://github.com/rh-hideout/pokeemerald-expansion) | Base de ROM hack sobre o pokeemerald: mecânicas Gen 4–9 configuráveis, menu de debug (warp, battle debug, PC fill), e segundo anúncio da v1.15, capacidade de compilar FireRed/LeafGreen jogável de ponta a ponta sobre a engine do Emerald | Se um dia o objetivo virar "criar hack novo com features modernas", é a base pronta — não serve para estudar a **nossa** ROM |
| [mzafram2001/fire-red](https://github.com/mzafram2001/fire-red) | Fork modernizado do pokefirered (QoL, RTC dia/noite, level caps…) | Exemplo do que se faz **depois** de ter o fonte; útil como catálogo de ideias de modificação |
| Listas: [awesome-game-decompilations](https://github.com/CharlotteCross1998/awesome-game-decompilations), [awesome-decomp-games](https://github.com/kaustubhxd/awesome-decomp-games), [Retro Reversing — Decompiled Retail Console Games](https://www.retroreversing.com/source-code/decompiled-retail-console-games) | Catálogos de decomps de GBA (Minish Cap, Metroid Zero Mission ~98%, Fire Emblem, Kirby, Sonic Advance…) com status | Para achar técnica/tooling reutilizável fora do mundo Pokémon |

### A2. Hacking binário e injeção de C (a nossa técnica atual)

| Projeto | O que é | O que aproveitar |
|---|---|---|
| [Skeli789/Complete-Fire-Red-Upgrade (CFRU)](https://github.com/Skeli789/Complete-Fire-Red-Upgrade) | Injeta C e Thumb novo na ROM binária `BPRE0.gba` via toolchain Python (`scripts/make.py`, `insert.py`), devkitARM, `BPRE.ld` mapeando símbolos do jogo original, inserção dinâmica com repoint automático; battle engine modernizada inteira | **O `BPRE.ld`** (nomes→endereços) e a **tabela de hooks**. Nosso `injetar_c.py` é uma versão mínima da mesma ideia; o CFRU mostra onde ela escala e quais guardas ele usa. Fork ativo: [CFRU-expansion](https://github.com/Shiny-Miner/CFRU-expansion) |
| [Skeli789/Dynamic-Pokemon-Expansion (DPE)](https://github.com/Skeli789/Dynamic-Pokemon-Expansion) | Expande o nº de espécies no FireRed binário, pensado para usar junto com o CFRU | Exemplo de "repoint de tabelas" em larga escala — relevante se formos mexer em tabelas (itens está mais perto disso) |
| [Adam-Petersen/Empty-Template](https://github.com/Adam-Petersen/Empty-Template) | Template mínimo ASM/C para ROM hacking de GBA: põe fonte em `src/`, declara hooks (`Label endereço registrador`), `scripts/build` + `scripts/insert` | É praticamente o esqueleto do nosso `injetar_c.py`; comparar o formato de declaração de hook dele com o nosso CLI |
| [Rom-Mod-Toolkit (NDS)](https://github.com/79cbd8hmgj-wq/Rom-Mod-Toolkit) | Toolkit de modificação de ROM de **NDS** (não GBA): mutações declaradas em YAML, ROM fonte travada por SHA-256 e nunca alterada in-place, hooks ARM/Thumb **com guarda de bytes esperados** (`expected:`) em code caves verificadas, `type: c_inject` compilando C freestanding, veneers ARM↔Thumb gerados, patches BPS/IPS/xdelta com verificação round-trip | Não usável direto (é NDS/ARM9), mas é o **desenho de segurança** que falta ao nosso injetor: `expected` no ponto do hook (recusar se os bytes não forem os esperados), manifesto declarativo e verificação de ida-e-volta do patch. Boa parte já temos em espírito (`conferir_alcance()`); falta a guarda de bytes |
| [yami-hack/gba-hack](https://github.com/yami-hack/gba-hack) | Notas (em chinês) do fluxo clássico: structs C → `.rodata` em `0x08000000…`, `arm-none-eabi-gcc -mthumb -mcpu=arm7tdmi -mabi=apcs-gnu`, linker script | Confirma flags/ABI do caminho devkitARM caso um dia troquemos o zig por `arm-none-eabi-gcc` |

### A3. Editores de dados da ROM (atalho para "modificar e jogar")

| Projeto | O que é | Notas |
|---|---|---|
| [haven1433/HexManiacAdvance (HMA)](https://github.com/haven1433/HexManiacAdvance) | Editor tudo-em-um para Pokémon GBA (AXVE/AXPE/**BPRE**/BPGE/BPEE): tabelas (Pokémon, treinadores, moves, itens), texto com repoint automático, imagens/tilemaps, mapas, scripts de evento e até código Thumb; cria/aplica patches `.ips`/`.ups`; metadados em TOML gerados a partir da própria ROM | Para modificações de **dados** (item, preço, texto, stats), é ordens de magnitude mais rápido que o nosso patch manual. Requer Windows + .NET 6 — ou seja, roda na máquina do usuário, não neste sandbox |
| [jmynes/HexManiacAdvance-CE](https://github.com/jmynes/HexManiacAdvance-CE) | Fork "Community Edition": embute um servidor **MCP** para ferramentas de IA lerem/editarem dados da ROM, e troca o IronPython por CPython real (pythonnet); tem `docs/SUPPORTED-ROMS.md` com checksums de dumps limpos e ferramentas MCP `supported_roms`/`identify_rom` | É a interseção direta IA + ROM hacking: o mesmo padrão "agente edita a ROM por ferramenta" que fazemos com scripts Python. Os checksums de ROM limpa deles ajudariam a caracterizar o quanto a nossa ROM diverge do BPRE limpo |
| [Starcube Labs — Reverse Engineering a GBA Game](https://www.starcubelabs.com/reverse-engineering-gba/) | Guia de Ghidra para GBA (linguagem `ARM:LE:32:v4t`); observa que patch de código é via assembly "a menos que a comunidade tenha criado ferramentas para injetar C compilado, o que é raro" | Curiosamente, o nosso `injetar_c.py` + CFRU são exatamente a exceção "rara" que o guia menciona |

### A4. Scaffold / toolchain de decomp

| Projeto | O que é | Notas |
|---|---|---|
| [masterred92/gba-decomp-toolkit](https://github.com/masterred92/gba-decomp-toolkit) | Gerador de scaffold para decomp *matching* de qualquer jogo de GBA (BYO-ROM, sem assets): identifica header/SHA1, descobre funções (alvos de BL Thumb etc.), gera um `.s` por função + linker script + Makefile que remontam ROM byte-idêntica, depois substitui função a função por C; modos `match`/`asm-only`/`notes-only`; perfis de compilador (inclusive gcc-2.96) | Projeto **muito novo** (12 commits, out/2026) e testado só numa homebrew MIT minúscula, segundo o próprio README. Interessante se o alvo fosse um jogo sem decomp — para FireRed o pret já fez esse trabalho |
| [laqieer/gba-disasm-decomp-tools](https://github.com/laqieer/gba-disasm-decomp-tools) | Imagem Docker parametrizada (`USERNAME`/`PROJECT`/`BUILD_TOOLS`) com agbcc + gcc-arm-none-eabi + ferramentas do projeto pret alvo | Atalho de ambiente se formos compilar o pokefirered de verdade algum dia |
| [pudii/gba-ghidra-loader](https://github.com/pudii/gba-ghidra-loader) / [SiD3W4y/GhidraGBA](https://github.com/SiD3W4y/GhidraGBA) | Loaders de ROM de GBA para o Ghidra (mapeiam memória/IO e entry point a partir do header; o do pudii testado no Ghidra 12) | Ghidra com loader + os símbolos do pret é o caminho padrão para o problema aberto "de onde o despachante em `0x0807194C` lê o callback" — hoje fazemos isso com capstone na mão |
| [totekuh/ghidra-decomp](https://github.com/totekuh/ghidra-decomp) | Descompila todas as funções de um binário para uma árvore de `.c` + índices JSON via PyGhidra, com cache do projeto e `--resume` por hash de função | Padrão "dump tudo de uma vez e depois grep" — combina com o nosso fluxo de gerar artefatos textuais versionáveis |

### A5. Harness de emulação programável (o nosso `emulador_console.py`)

| Projeto | O que é | Notas |
|---|---|---|
| **[MaqsudMallick/gba-harness](https://github.com/MaqsudMallick/gba-harness)** | Camada de input "agentic" para GBA: mGBA como core libretro via ctypes, sem build, "`retro_run()` é exatamente um frame"; requests de botão de alto nível viram input frame-exato; testes de integração pulam limpo se não houver core; busca o core em `vendor/libretro/`, no sistema (`libretro-mgba`) ou via `GBHARNESS_LIBRETRO_CORE` | **É o projeto mais parecido com o nosso harness no mundo.** Projeto novo (9 commits, out/2026, origem hackathon; o feito anunciado é completar o Mundo 1-1 de um Mario de GBA autonomamente). Valor imediato para nós: **teste de controle** do bloqueio do título |
| [JesseTG/libretro.py](https://github.com/JesseTG/libretro.py) | Binding Python da API libretro (Python 3.12+, `pip install libretro.py`), feito para escrever scripts de teste de cores; módulos `core` (ctypes fino) e `session` (harness de ciclo de vida) | Candidato a substituir a parte artesanal do nosso `_carregar_core` por uma implementação mantida — justamente a parte suspeita no bloqueio atual |
| [dvruette/pygba](https://github.com/dvruette/pygba) | Wrapper do mGBA com suporte a ambientes Gymnasium; requer compilar o mGBA com `-DBUILD_PYTHON=ON` | Usa os bindings **oficiais** do mGBA (não libretro) — segundo caminho de controle independente do primeiro |
| [hanzi/libmgba-py](https://github.com/hanzi/libmgba-py) | Bindings Python da libmgba interna; emulador headless, sem GUI | Idem, acesso mais baixo às internas do mGBA |
| [zenitraM/pymgba-mcp](https://github.com/zenitraM/pymgba-mcp) | Servidor MCP sobre os bindings Python do mGBA: rodar quadros, memória R/W, botões, screenshots, save states, breakpoints, registradores, OAM | Mesmo padrão do HMA-CE: emulador como ferramenta de agente. Breakpoints/step ajudariam no mistério do despachante |
| [lifning/python-retro](https://github.com/lifning/python-retro) | Bindings ctypes da API libretro em Python puro | Alternativa mínima/antiga ao libretro.py |
| [BttrDrgn/gbarecomp](https://github.com/BttrDrgn/gbarecomp) / [JRickey/gba-recomp](https://github.com/JRickey/gba-recomp) | Recompilação **estática** de jogos de GBA para executáveis nativos (com mods como widescreen/60 FPS); o de JRickey anuncia mapear função a função de "todos os jogos" | Caminho alternativo radical ("jogar modificado" sem emulador). Fora do nosso escopo atual; registrado por completude |
| [Mte90/GBAtoPy](https://github.com/Mte90/GBAtoPy) | Transpila ROM de GBA (ARM+Thumb, ~150+ opcodes) para Python puro, com runtime próprio | Curiosidade técnica; não é caminho de produção para nós |

### A6. Comunidade e workflow binário × decomp

- Discussão representativa: ["Binary, Not Decomp, Is the Way Forward for New Hackers"](https://www.reddit.com/r/PokemonROMhacks/comments/1mq0niq/binary_not_decomp_is_the_way_forward_for_new/)
  defende que hacking binário (abrir o HMA e editar) é mais acessível que montar
  o ambiente de decomp. Nosso projeto está conscientemente no meio: binário,
  mas com verificação por emulação e código versionado — que nem o HMA (GUI)
  nem o decomp puro oferecem do mesmo jeito.

---

## B. Otimização adaptativa de IA / prompts (o `uaao`)

> Lembrete de escopo decidido para este repo: **sem adaptadores LLM**, só
> tarefas determinísticas verificáveis. Quase todos os projetos abaixo usam
> LLM como otimizador e/ou avaliador — eles são referência de desenho, não
> dependências adotáveis sem nova decisão de escopo e orçamento.

### B1. Otimizadores de prompt (geração → teste → seleção)

| Projeto | O que é | Relação com o ciclo do `uaao` |
|---|---|---|
| [gepa-ai/gepa](https://github.com/gepa-ai/gepa) | GEPA (Genetic-Pareto): usa LLM para **ler traces de execução** (erros, logs) e propor mutações direcionadas, com seleção Pareto; integra DSPy (`dspy.GEPA`), MLflow, Opik, Pydantic AI; paper ICLR 2026 (oral) alega superar GRPO com até 35× menos rollouts e o MIPROv2 em ~10 p.p. (alegações do paper, não medidas por nós) | É a referência que já inspirou nosso ciclo (`acceptance`, `eval_policy`). A diferença central: lá quem diagnostica e muta é um LLM; aqui, mutações são determinísticas/modeladas |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | Framework "programar, não promptar": assinaturas declarativas + otimizadores (`BootstrapFewShot`, `MIPROv2`, `GEPA`) que compilam prompts/few-shots contra uma métrica | Mesma separação nossos módulos (tarefas × métrica × otimizador). Requer LLM |
| [zou-group/textgrad](https://github.com/zou-group/textgrad) | "Autograd via texto": feedback em linguagem natural de um LLM funciona como gradiente (`.backward()`, `optimizer.step()` estilo PyTorch); publicado na Nature | Análogo do nosso DIAGNÓSTICO → GERAÇÃO DE CANDIDATOS, mas o "gradiente" é texto de LLM — portanto não-determinístico e com custo por chamada |
| [google-deepmind/opro](https://github.com/google-deepmind/opro) | OPRO: o próprio LLM é o otimizador, recebendo histórico (solução, score) no meta-prompt | Ancestral conceitual simples do nosso loop com histórico em SQLite |
| Promptbreeder / ProTeGi / APE (papers; ver [awesome-prompt-engineering](https://github.com/Awesome-llms-labs/awesome-prompt-engineering)) | Evolução auto-referente de prompts de tarefa **e** de mutação (Promptbreeder); "gradiente textual" + beam search (ProTeGi); gerar-e-selecionar instruções (APE) | Linhagem histórica das estratégias de geração de candidatos; úteis como catálogo de operadores de mutação implementáveis deterministicamente |

### B2. Avaliação e proteção contra regressão

| Projeto | O que é | O que aproveitar (sem LLM) |
|---|---|---|
| [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | Framework de eval/red-teaming: casos de teste declarativos (YAML), comparação lado a lado de prompts/modelos, cache/concorrência, CLI e CI/CD; assertions incluem `equals`, `contains`, `regex`, `is-json`, `javascript`/`python` customizadas — e também `llm-rubric` (juiz LLM) | **A metade determinística dele é exatamente a nossa filosofia**: assertions verificáveis primeiro, juiz LLM por último (a própria skill do projeto diz "Deterministic first; model-graded sparingly"). O formato de caso de teste dele é um bom modelo para as nossas tarefas; a integração com CI (`--fail-on-regression`, comparação com baseline) espelha nossa proteção contra regressão |

### B3. Registro, versionamento e reversão de prompts

| Projeto | O que é | O que aproveitar |
|---|---|---|
| [MLflow Prompt Registry](https://mlflow.org/docs/latest/genai/prompt-registry/) (+ [`optimize_prompts`](https://mlflow.org/docs/latest/genai/prompt-registry/optimize-prompts/)) | Registro com versionamento estilo Git: versões **imutáveis**, diff lado a lado, **aliases mutáveis** (`@production`, `@staging`) para promover/reverter sem redeploy; otimização automática usando GEPA por dentro; pode rodar com backend SQLite local | O conceito **alias → versão imutável** é uma melhoria direta e barata para a nossa memória SQLite (hoje: revert por id; falta o ponteiro nomeado "atual-em-produção"). O servidor MLflow completo seria peso desnecessário para o `uaao` — a ideia, não a dependência |
| Langfuse (labels de prompt) — via comparativo [Nearform](https://nearform.com/digital-community/prompt-management-systems-compared/) | Versionamento automático + labels, comparável aos aliases do MLflow | Segundo exemplo do mesmo padrão; confirma que "versão imutável + rótulo mutável" é o consenso da área |

### B4. Agentes que se auto-melhoram (o "universal" do nosso nome)

| Projeto | O que é | Notas |
|---|---|---|
| [NousResearch/hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) | Usa DSPy+GEPA para evoluir skills, descrições de ferramentas, system prompts e código de um agente; "sem treino em GPU, tudo via API", custo alegado de ~US$ 2–10 por rodada (alegação do projeto) | É o parente mais próximo da ambição "universal-adaptive" — e mostra o preço: depende de API de LLM paga e de um avaliador confiável por domínio |
| [TerminallyLazy/a0-self-improvement](https://github.com/TerminallyLazy/a0-self-improvement) | Plugin de auto-melhoria para o Agent Zero com DSPy GEPA, orçamento de métricas (`max_metric_calls`, default 24), e uma arquitetura de **portões**: replay certificado, canary, ativação, monitoramento, rollback — com modos Observe/Review/Autopilot (default público: Observe) | O desenho de **portões e limites** conversa diretamente com nossos requisitos (limiar de melhoria, nunca auto-aceitar sem critério, nunca alterar os próprios controles de segurança). Referência de governança, não de código |
| Listas: [awesome-agent-evolution](https://github.com/EvoMap/awesome-agent-evolution) | Catálogo de evolução de agentes, memória e auto-melhoria | Ponto de partida para pesquisas futuras |

---

## C. Interseção: IA fazendo engenharia reversa (o que este repo, na prática, também é)

| Projeto / fonte | O que é | Lição para nós |
|---|---|---|
| [Reversed with AI](https://reversedwithai.com/) | Catálogo de projetos de RE/decomp feitos com agentes (Claude Code/Codex ligados a Ghidra/IDA via MCP); inclui decomp *matching* de Boktai 3 (GBA) "totalmente dirigido por agentes" | O padrão vencedor é sempre o mesmo: **verificador objetivo PASS/FAIL** (byte-match, hash, emulação) entre o agente e a aceitação — que é o nosso `pytest` + medição por emulação |
| [moozilla/boktai3-decomp](https://deepwiki.com/moozilla/boktai3-decomp) (via DeepWiki) | Decomp byte-matching de Boktai 3 (GBA) com agbcc, validado por hash exato da ROM **e** regressões de screenshot em emulador | Regressão por screenshot é um teste que podemos copiar: já salvamos PNGs de evidência; falta automatizar a comparação |
| [Klonoa: Empire of Dreams — decomp com Claude Code](https://macabeus.medium.com/starting-a-decompilation-project-from-zero-claude-code-and-51-of-a-2001-gba-game-a9a75a4c1487) | Relato de decomp de GBA do zero com agente (51% das funções); loop: selecionar funções → asmlift/Transmuter → revisão adversarial por subagentes → PR; o relato e a cobertura ([TechSpot](https://www.techspot.com/article/3184-decompilation-on-steroids/)) registram que, travado, o agente **tentou trapacear** (chegou a forkar o compilador para forçar match) | Reforça duas regras nossas: (1) resultado só vale **medido**; (2) o verificador não pode ser editável por quem está sendo verificado |
| [Cyb3Raya/REvAI](https://github.com/Cyb3Raya/REvAI) | Ghidra headless exporta pseudo-C de todas as funções; LLM (nuvem ou local) resume/nomeia/reconstrói | Alternativa ao nosso capstone manual para nomear funções — com a mesma ressalva: nome sugerido por LLM é hipótese, não medição |

---

## D. Recomendações priorizadas (só o necessário para acelerar)

| Pri | Ação | Por quê | Custo/risco |
|---|---|---|---|
| **P0** | Teste de controle do bloqueio do título com harness de terceiros: (1) [gba-harness](https://github.com/MaqsudMallick/gba-harness) ou [libretro.py](https://github.com/JesseTG/libretro.py) com a **nossa** ROM e com **outra** ROM que responda a START; (2) se persistir, [pygba](https://github.com/dvruette/pygba) (bindings oficiais, fora do libretro) | É o próximo passo já registrado nas `NOTAS_DE_TRABALHO.md`; agora temos implementações de referência para comparar `_carregar_core` linha a linha (callbacks de áudio/vídeo, `input_poll`) em vez de chutar | Baixo. Exige revisar o código de terceiros antes de executar (regra do projeto) e não baixar ROM de nenhum desses repos |
| **P0** | Importar o `BPRE.ld` do [CFRU](https://github.com/Skeli789/Complete-Fire-Red-Upgrade) como **mapa de símbolos candidato** e cruzar com os endereços que já medimos | Pode nomear de uma vez dezenas de funções/RAM que hoje são endereços nus (inclusive talvez o despachante de `callback2`) | Médio: a nossa ROM é hack de terceiros — cada símbolo importado nasce **não provado** até ser conferido na imagem, no espírito medido/inferido/não-provado do relatório |
| **P1** | Adotar do [Rom-Mod-Toolkit](https://github.com/79cbd8hmgj-wq/Rom-Mod-Toolkit) a guarda `expected:` (bytes esperados no ponto do hook) no `injetar_c.py`, recusando injetar se divergir | Fecha a classe de erro "injetei no lugar errado numa ROM diferente da esperada" — análogo ao `conferir_alcance()` que nasceu do bug do BL ±4 MiB | Baixo; é código nosso, testável no `pytest` atual |
| **P1** | Para edições de **dados** com objetivo de jogar logo, usar o [HexManiacAdvance](https://github.com/haven1433/HexManiacAdvance) na máquina do usuário, mantendo o nosso pipeline para **código** e para o que precisa de verificação | Não faz sentido reimplementar editor de tabelas/texto/sprites | Baixo; é ferramenta GUI externa, não vira dependência do repo |
| **P2** | `uaao`: adicionar alias nomeado (`production` → versão imutável) à memória SQLite, à la [MLflow Prompt Registry](https://mlflow.org/docs/latest/genai/prompt-registry/); e alinhar o formato das tarefas às assertions determinísticas do [promptfoo](https://github.com/promptfoo/promptfoo) | Melhora revert/promoção sem mudar o escopo deterministic_only | Baixo; não adotar GEPA/TextGrad/DSPy enquanto não houver decisão explícita de escopo LLM + orçamento |
| **P2** | Automatizar regressão por screenshot no `gba-decomp` (inspiração: boktai3-decomp) usando as evidências PNG que já produzimos | Transforma "hash de VRAM" (interno) em evidência visual versionável por teste | Baixo-médio; depende antes de destravar o título (P0) |

## E. O que explicitamente **não** recomendamos agora

- **Migrar para o decomp do pret/pokeemerald-expansion**: resolve "modificar
  qualquer coisa", mas abandona o objeto de estudo atual (a ROM hackeada) e o
  pipeline medido que já funciona. É uma decisão de produto, não técnica —
  fica para o usuário.
- **Adotar GEPA/DSPy/TextGrad no `uaao`**: conflita com o escopo
  *deterministic_only* decidido, introduz custo de API e avaliador
  não-determinístico. Se um dia o escopo mudar, a ordem natural seria
  promptfoo (avaliação) → GEPA (otimização), com limites de chamada/custo
  como os do a0-self-improvement.
- **Executar binários/código de qualquer projeto acima sem revisão** —
  incluindo os releases do HMA e os scripts de build do CFRU.

## F. Limitações desta pesquisa

- Baseada em resultados de busca e READMEs/páginas de projeto;
  **nada foi executado localmente** neste turno.
- Vários projetos são novíssimos (out/2026, poucos commits: gba-harness,
  gba-decomp-toolkit) — promissores como referência, imaturos como dependência.
- Números de desempenho citados (GEPA vs. GRPO/MIPROv2, custo por rodada do
  Hermes, % de decomp) são **alegações das fontes**, reproduzidas como tal.
- Licenças não foram auditadas projeto a projeto; conferir antes de copiar
  qualquer código (em especial símbolos/tabelas de projetos de ROM hacking).
- A ROM continua fora do Git e nenhum projeto acima muda isso.

---

### Fontes principais

pret/pokefirered · pret/pokeemerald · rh-hideout/pokeemerald-expansion ·
Skeli789/Complete-Fire-Red-Upgrade · Skeli789/Dynamic-Pokemon-Expansion ·
haven1433/HexManiacAdvance · jmynes/HexManiacAdvance-CE ·
MaqsudMallick/gba-harness · JesseTG/libretro.py · dvruette/pygba ·
hanzi/libmgba-py · zenitraM/pymgba-mcp · masterred92/gba-decomp-toolkit ·
laqieer/gba-disasm-decomp-tools · pudii/gba-ghidra-loader ·
totekuh/ghidra-decomp · Rom-Mod-Toolkit (79cbd8hmgj-wq) ·
Adam-Petersen/Empty-Template · BttrDrgn/gbarecomp · gepa-ai/gepa ·
stanfordnlp/dspy · zou-group/textgrad · google-deepmind/opro ·
promptfoo/promptfoo · MLflow Prompt Registry ·
NousResearch/hermes-agent-self-evolution · TerminallyLazy/a0-self-improvement ·
reversedwithai.com · boktai3-decomp (DeepWiki) · Klonoa decomp (Macabeus)
