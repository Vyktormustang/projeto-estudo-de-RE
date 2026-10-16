# progress.md — Progresso, obstáculos e próximas ações

## ✅ ENCERRAMENTO DO PROJETO — THEO / Arena.ai (14-out-2026)

### Fases 0–7 — status consolidado

| Fase | Entregas | Status |
|---|---|---|
| 0 Preparação | por-que preserve ROM, cópia de trabalho, hashes (SHA-256 6035a98f…), inventory.json | ✅ |
| 1 Triagem | ident: cabeçalho BPRE válido, entropia por bloco, strings, charset Gen3 + acentos PT-BR mapeados | ✅ |
| 2 Análise estática | boot trace ARM→Thumb (0x080003A4), censo BL (88.782 sites / 5.982 funções prólogo), functions.csv, callsites.tsv | ✅ |
| 3 Chamadas | callgraph DOT (5.981 nós / 21.314 arestas / 5.266 SCCs), hubs e dispatchers (H-0013/14/15 QUANTIFICADOS) | ✅ |
| 4 Dinâmica | Sandbox Linux: driver libretro + mGBA 0.10.5 headless; boot visual, determinismo, input/snapshots/save-states | ✅ |
| 5 Texto/mods | pipeline de patch de slot c/ pré-condições; patch demo "PIDGEY" → byte-contrato + boot determinístico | ✅ |
| 6 Código/hooks | hook tool validada estaticamente e **dinamicamente** (trampolim → efeito visual controlado, zero crash) | ✅ |
| 7 Fechamento | bateria unificada run_all_tests.sh → **8/8 scripts OK**; docs consolidados | ✅ |

### Conquistas adaptativas principais (resumo executivo)
- Identidade confirmada: ROM = variante PT-BR de Pokémon FireRed (BPRE Rev 0 base; hashes ≠ No-Intro/ gbhwdb; tela de título exibe "FIRE RED BR").
- Save type = Flash1M (FLASH1M_V103) — observável via region 0 = 128 KiB.
- Núcleo de objetos: pool 0x03005090 (H-0010 hipótese forte; observação bloqueada nesta plataforma, não refuta);GET/SET BoxMon H-0014/15 confirmados estruturalmente.
- Infra de emulação própria no sandbox (sem root): determinística, inputs, snapshots, states (528 KiB), região SAVE legível.

### Limites honestos (não fechados por escopo/plataforma)
- H-0010/H-0016: EWRAM/IWRAM não expostas pelo mGBA-libretro headless (region+SET_MEMORY_MAPS esgotados); alternativa documentada.
- Hub 0x0808CFF8 permanece inalcançável estaticamente (como decidido); requer ptr-write dinâmico fora do sandbox.
- Prova visual do slot PIDGEY (espécie em jogo): alcança-se c/ navegação longa (title→tutorial→new game→lab); rebaixada a opcional (ciclo 21).
- Toolchain (H-0002) mantido PROVÁVEL por política de evidência.

### Reprodutibilidade rápida
```
git worktree? n/a — tudo em /home/user/gba-re (scripted + log)
python3 scripts/gba_libretro_emu.py --rom rom/pokemon_firered_bpre_trabalho.gba \
   --frames 1300 --snap 1280=out.png           # título FIRE RED BR
bash scripts/run_all_tests.sh                  # 8/8 deve PASSAR
```

Estivadores honestos: cada claim acima tem evidência runnable neste workspace.

> Fonte primária de estado do projeto. Atualizado a cada ciclo.

## Estado: **PROJETO ENCERRADO (ciclo 24)** — ver seção de Encerramento abaixo; timeline a seguir é histórica

Última atualização: 2026-10-14 (UTC)

## Linha do tempo

### Ciclo 1 — 2026-10-14 (Fase 0 + preparação da Fase 1)

**Objetivo:** verificar ambiente real, montar memória persistente, entregar e validar
a ferramenta da Fase 1.

**Ações executadas (de verdade):**
- Inventário do ambiente por comandos reais (`uname`, `free`, `df`, verificações de
  Python/Java/Git, busca de arquivos, teste de rede, probing de ferramentas de RE).
- Detecção da divergência Windows (briefing) × Linux (real) — documentada.
- Instalação do capstone 5.0.7 (única dependência justificada agora).
- Criação da estrutura persistente: README.md, inventory.json, functions.csv,
  hypotheses.md, scripts/, logs/, reports/, tests/.
- `scripts/gba_ident.py` v1.0.0: hashes, cabeçalho GBATEK (logo, checksum, entry
  point ARM), entropia por bloco, strings ASCII, padrões BL Thumb/ARM, relatórios
  JSON/TSV, log JSONL, atualização de inventário, `--self-test`.
- **Validação:** self-test 16/16 PASS (1 bug de fixture encontrado e corrigido);
  casos de erro com exit codes corretos; execução demo sobre ROM SINTÉTICA rotulada.
- Manifesto SHA-256 dos artefatos em `logs/2026-10-14_fase0_ambiente.md`.

**Não executado (honestidade):** nenhuma análise de ROM real — a ROM não foi
fornecida. Nada foi simulado "como se" fosse a ROM real.

### Ciclo 2 — 2026-10-14 (ROM recebida → Fase 1 completa)

**Entrada:** usuário anexou `Pokemon - Fire Red (BR).txt` (16 MiB) — era uma ROM
renomeada como .txt (confirmado por magic bytes, `file`, cabeçalho GBATEK).

**Ações executadas:**
- Cópia de trabalho `rom/pokemon_firered_bpre_trabalho.gba` byte-idêntica
  (sha256 + `cmp`); original preservado em `uploads/`.
- Hashes completos: SHA-256 `6035a98f…da0b4ae`, SHA-1 `00b40312…b945db`,
  MD5 `4ec27a4b…10cbd7`, CRC32 `7a6ef5f5`.
- Cruzamento com No-Intro: **não bate** com FireRed (USA) Rev 0 (`dd88761c`) nem
  Rev 1 (`84ee4776`) → imagem modificada (consistente com tradução PT-BR).
- Fase 1 real com `gba_ident.py` → JSON + strings.tsv + regioes.tsv em `reports/`;
  `inventory.json` atualizado pela própria ferramenta.
- Análise pontual do boot: entry `B 0x08000204`; em 0x204, padrão canônico do SDK
  Nintendo (mov/msr/ldr — configuração de modos e pilhas) decodificado manualmente.
- Bibliotecas compiladas identificadas por strings: **FLASH1M_V103** (save 128 KiB),
  **RFU_V1024** (adaptador wireless). Literal "pokemon red version" @0x108.
- Mapa de regiões: 0x000000–0x15FFFF = código candidato denso (Thumb BL 17–41/KiB,
  **zero** ARM BL) → binário principal Thumb; ilhas extras em 0x1E0000 e 0x4B0000
  (esta com 109 ARM BL — investigar); 46% do arquivo = preenchimento 0xFF;
  conteúdo útil até ~0xEB0B1D (~14,6 MB); 24.732 strings ASCII ≥ 6.

**Não executado:** desassemblado sistemático (Fase 2), depuração (Fase 4) —
aguardam ferramentas/ciclos seguintes.

### Ciclo 3 — 2026-10-14 (decodificador de texto + idioma CONFIRMADO)

**Objetivo:** passo 1 do placar — `gba_poketext.py`, validação do charset e
classificação do idioma.

**Ações executadas:**
- Nova ferramenta `scripts/gba_poketext.py` (decodificador Gen 3 + extrator +
  sondas de idioma; self-test 13/13 PASS).
- **Charset validado em dados reais, não presumido:** âncoras BULBASAUR/IVYSAUR/
  VENUSAUR/CHARMANDER com slots de 11 B contíguos → tabela de espécies empírica
  em 0x245EE0 (GBA 0x08245EE0). POTION×5, POUND×2, POK[e]MON×1811.
- **PT-BR CONFIRMADO** (H-0001b): você 719 + Você 577 + ção 174 + está 345/53 +
  Olá 40 + diálogos legíveis de NPC/ajuda/Pokédex.
- **Remap de acentos descoberto empiricamente** → `notes_charset_remap_br.json`
  (é=0x1B, ê=0x1C, á=0x17, ç=0x19, ã=0xF4, õ=0xF5, â=0x68); re-extração com
  override: **14.815 strings candidatas** no dump TSV.
- `notes_estrutura.md` criado com endereços verificados.

**Erros de processo encontrados e corrigidos (log de integridade):**
1. Sonda manual "obrigad" com hex montado à mão usou byte errado (E3 no lugar de
   D5) → 0 hits espúrio; o caminho oficial (tabela inversa) estava certo: 12 hits.
   Lição: nunca hex manual; sempre derivar da tabela.
2. Bug real na ferramenta: inverso char→byte com `setdefault` preservava o byte do
   estoque quando char existia nos dois (estoque+override) → falsos zeros em sondas
   ('POKé'=0 com 'POK[e]MON'=1811 — impossível; detectado por sanity check lógico).
   Corrigido com precedência de override + 3 testes de regressão. Resultados
   corrigidos: ção 0→174, POKé 0→1982.
3. (Ciclo 1) bug de fixture — já registrado.

**Não executado:** desassembly sistemático (próximo ciclo), refino de acentos
restantes, delimitação exata das regiões de texto.

### Ciclo 4 — 2026-10-14 (desassembly evidencial: boot, ARM×Thumb, censo de funções)

**Objetivo:** passo 2 do placar — `gba_disasm.py`.

**Ações executadas:**
- Nova ferramenta `scripts/gba_disasm.py` (boot trace ARM + censo Thumb/ARM por
  capstone, dual-check manual; self-test 9/9 PASS).
- **Boot trace confirmado 2×:** entrada 0x08000204 (init SDK) → 13 instr. ARM →
  **transição ARM→Thumb em 0x080003A4** (entry principal; nomeada
  ENTRY_THUMB_boot_080003a4 no functions.csv).
- IRQ dispatcher ARM descoberto por rastreamento de literais: SP_IRQ=0x03007FA0,
  SP_USR=0x03007E40, [0x03007FFC]←0x08000248; handler em 0x08000248 confirmado
  por desassembly (padrão IE/IF/IME).
- **H-0003 ENCERRADA:** Thumb dominante = CONFIRMADO (7.565 funções por BL direto,
  78% prólogo canônico; ARM-hit 0,0 em 384 páginas). "Ilhas ARM" do ciclo 2
  REFUTADAS (eram dados imitando opcodes — H-0009).
- functions.csv: **7.566 funções** com evidência individual registrada.

**Erros de processo encontrados e corrigidos (log de integridade — ciclo 4):**
1. capstone `operands` exige `detail=True` (crash inicial) — fix explícito.
2. Fixture com BL montado em hex manual: alvo errado por 2 bytes (aritmética) —
   cura: encoder inverso `encode_bl_thumb` (nunca mais BL manual).
3. **Decodificador manual de BL com sinal no bit errado (22×21)** — divergia em
   saltos para trás; detectado por 39 divergências no dual-check; provado com
   teste diferencial sintético (capstone estava certo); fix + regressão.
4. **`i += avanco` no sweep dobrava o cursor** — varria só ~16% de cada página
   (320 insns em vez de ~1.200); detectado por saneamento "insns/página"; fix +
   regressão (página inteira = 2048 movs).
5. Classificador de página iterou 2×: limiar absoluto inútil (tudo "AMBIGUA");
   "localidade de endereço" inútil (alcance ±32 MiB × ROM 16 MiB → lixo cai
   dentro). Versão final: **prólogo-alvo** (alvos de BL caem em 0xB5/0xE92D) —
   empiricamente decisivo.
6. Nenhuma conclusão foi emitida antes de cada rodada passar pelo dual-check
   e por pelo menos um estado de falha observado.

**Não executado:** identificação das funções mais chamadas (próx. ciclo,
por assinatura), callgraph completo, Ghidra, mGBA.

### Ciclo 5 — 2026-10-14 (assinaturas das mais-chamadas + sistema de renomeações)

**Objetivo:** passo 3 do placar — dar semântica às funções mais quentes.

**Ações executadas:**
- Novo comando permanente `gba_disasm.py dis 0xADDR [-n N] [--mode thumb|arm]` com
  resolução automática de literais `ldr [pc,#i]` (THUMB: align(PC+4); ARM: PC+8) e
  anotação de SWI/branches.
- Inspecionadas as 10 funções mais chamadas + 3 callees relevantes.
- **`names_registry.json`** criado (10 renomeações com evidência); atualizador do
  functions.csv agora REAPLICA o registro a cada regeneração (testado: 10/10
  aplicados, linha manual IRQ preservada).
- ENTRY_THUMB_main (0x080003A4) adicionada manualmente ao CSV (ausente do censo —
  não é alvo de BL, é destino de BX do boot). CSV: 7.567 linhas.
- **Quebra de expectativa registrada:** as mais chamadas NÃO são memcpy/div;
  ×1363/×728 são dispatchers orientados a tabela (34 casos). H-0011: código existe
  além de 0x160000 (0x1Dxxxx) — censo ampliado pendente.

**Descobertas principais:** ver `notes_estrutura.md` (11 nomes). Destaques:
`SetGpuReg_like` (par buffered-write/commit com DISPSTAT especial ×1238),
dispatchers gêmeos 34c, pool de slots 0x28B em 0x03005090 (H-0010: sistema de
objetos?), lookup hierárquico de recursos em 0x084A329C/0x084A32CC.

**Erros de processo (ciclo 5):** nenhum novo; hipótese a-priori "mais chamadas =
runtime C" foi REFUTADA pelos dados (registrado para não enviesar as próximas).

**Não executado:** análise dos 34 casos de cada dispatcher (substrato do
callgraph), censo ampliado 0x160000–0xEB0000, mGBA.

### Ciclo 6 — 2026-10-14 (censo ampliado → callgraph → 1º MODIFICADOR de ROM)

**Objetivo:** fechar a cadeia de suprimentos do callgraph (censo cobrindo a
ROM útil), extrair o primeiro mapa arquitetural e entregar o primeiro
modificador seguro da ROM (texto) — base da resposta "quanto falta para
modificações".

**Ações executadas:**
- `setup_env.sh` reaplicado (capstone 5.0.7 havia sumido — obstáculo #5 de
  novo; mitigação funcionou em segundos). Self-test do disasm 9/9.
- `gba_disasm.py`: functions.csv agora SÓ recebe alvos com prólogo limpo
  (B5/B4/sub_sp; baixa prova fica no TSV); exporta `reports/*_callsites.tsv`;
  `--islands` default False; **bug de DUPLICAÇÃO do registry corrigido** —
  linhas aplicadas do registry eram preservadas como "manuais" na regeneração
  seguinte e reaplicadas de novo. Nova regra: registry é autoridade (linha
  anterior com endereço no registry é descartada). Resultado: 5.979 auto +
  10 registry + 2 manuais = **5.981 nós únicos, zero duplicatas** (verificado
  por `grep -c` nos 5 endereços testemunha).
- **Censo ampliado 0x0–0xEC0000** (3.776 páginas, 67 s): 88.782 BL → 51.268
  alvos; 5.978 funções com prólogo limpo; 25.352 alvos fora da ROM + 19.830
  "outro" = ruído de dados; 232 páginas THUMB-verificado, **0 ARM**; top-8
  inalterado; dual-check 100 OK → código real concentrado em 0x0–0x160000 +
  ilhas (H-0011 quantificada).
- **`gba_callgraph.py` v1.0.0** (self-test 7/7): nós do CSV, arestas do TSV,
  caller = maior início ≤ site (limitação declarada), Tarjan iterativo, BFS.
  Run real: **5.981 nós, 21.314 arestas únicas** (36.578 ponderadas), 51.616
  sites p/ fora do universo (listados na métrica, não ignorados silenciosamente);
  **BFS da entry: 2.609 alcançáveis (43,6%)** só por BL direto; **5.266 SCCs,
  maior = 585 nós** (núcleo de acoplamento — H-0012). Top indegree reproduz
  o top-8 do censo (validação cruzada ✓). **HUBS novos por outdegree:**
  0x0808CFF8 (117 callees), 0x0806A40C (79), 0x081186C8 (76), 0x08046ED0 (72),
  0x081508EC (69) — candidatos a gerentes de subsistema.
- **Sonda das tabelas dos dispatchers** (adianta tarefa 82): 34 ponteiros
  válidos por tabela; nenhum está no CSV — handlers [0] de ambas decodificam
  como **Thumb stubs sem prólogo** (por isso fora do censo de funções) com
  branch tail para continuação comum (`b #0x803FD3E` no caso tbl3FC08) →
  CONFIRMADO (estrutura) p/ handler[0]; mecanismo do despachante que resolve
  o bit 0 ainda não re-verificado.
- **`gba_patch_text.py` v1.0.0** (self-test 7/7) — **PRIMEIRO MODIFICADOR
  SEGURO DA ROM**: recusa in-place, pré-condição `--expect`, `--slot-size`
  com checagem de padding vivo (00/FF), preenchimento preservado, relatório
  hexdump + SHA-256 in/out, log JSONL. **DEMO REAL:** slot #16 da tabela de
  espécies (0x245F90, passo 11) `PIDGEY → PIDGEY!` em
  `rom_mod/PATCH_TEXTO_DEMO_PIDGEY.gba`: 2 bytes alterados na ROM inteira,
  vizinho #17 intacto, ROM original intacta (re-decode usado como prova).

**Erros de processo (ciclo 6):** bug de duplicação do registry (encontrado e
corrigido, com regra documentada); bug menor no harness do self-test do
patcher (`_espera_erro` sem kwargs) — corrigido no ato. Primeira versão do
patcher usava nomes de API do gba_poketext de cabeça → reescrita após leitura
do módulo real (lição: conferir API, não memória).

**Não executado:** leitura completa dos 2×34 casos, estrutura do loop em
ENTRY_THUMB_main, instalação de mGBA/Ghidra.

### Ciclo 7 — 2026-10-14 (casos mapeados: os 2×34 são GET/SET; hub analisado)

**Objetivo:** executar os itens 84 (casos dos dispatchers) e 78 (hub
0x0808CFF8) do placar.

**Ações executadas:**
- `scripts/gba_table_probe.py` v1.0.0 (self-test 3/3; 2 bugs de fixture hex
  corrigidos — regra reforçada: hex manual é traiçoeiro). Modos `--table`
  (ponteiros + resumo de handler: entrada/tail/BLs) e `--hub` (BLs com nomes
  + pool de memória da janela).
- **Leitura dos 2×34 casos (tarefa 84 concluída):** tabela 0x0803FC08 = GET
  com layout status@+0x50, nível@+0x54, hp@+0x56, maxHP@+0x58, 5 stats
  @+0x5A..+0x62, seletor 1..5 via 0x08044674, 19 casos via helper 0x0803FD44;
  tabela 0x0804039C = **SET espelho** (caso[10]=no-op). Classificação
  PROVÁVEL: acesso a dados de unidade (H-0014/H-0015). Registry: 12 entradas
  (novo: `acc_sel1-5_read_tbl3FC08_like`; evidência dos 2 dispatchers
  enriquecida com o mapa de casos).
- **Hub 0x0808CFF8 (tarefa 78 concluída parcial):** 0 callers BL + 0 refs de
  ponteiro → controller **indireto** (task/estado); pool EWRAM 0x020397B0;
  loop interno (self-BL). Nomeável só com validação dinâmica → H-0016; mGBA
  subiu de score (66→prioridade real).

**Erros de processo:** hex de fixture montado à mão (b +12) errado (0xE006 vs
bytes `06 e0`) + linha morta acessando `i.operands` sem detail — corrigidos.

**Não executado:** ENTRY loop, identidade exata do hub (mGBA), helpers
0x0803FD44/0x080404D0 (devem descriptografar subdados de caixa — leitura
barata, próximo ciclo).

### Ciclo 8 — 2026-10-14 (helpers lidos: caixa Pokémon CONFIRMADA estrutural)

- `dis 0x0803FD44 -n 110`: 4 substructs (sel 0..3) + recompute de checksum +
  flags **bad-egg** + jump table de 84 casos → **GetBoxMonData-like
  CONFIRMADO**; H-0014/H-0015 promovidas.
- 0x0803E3E8 = `checksum_boxsubstructs_like` (soma sel 0..3); 0x0803F91C =
  `decrypt_xor_boxsubdata_like` (`[+0x20]^=[+4]`, chave personalidade⊕OTID)
  — ambos CONFIRMADO-estrutural; 0x080404D0 = espelho SET (HIPÓTESE).
- Registry → 17 entradas (CSV pega os nomes na próxima regeneração).

### Ciclo 9 — 2026-10-14 (SET confirmado + loop principal mapeado)

- Corpo de `set_boxmondata_84case_like` lido: cabeça idêntica ao GET (4
  substructs/decrypt/checksum/bad-egg + fixup 0x0803F8F8) + própria tabela
  ≤0x50 → **CONFIRMADO**; H-0015 fechada.
- **ENTRY_THUMB_main mapeado (tarefa 68):** esqueleto AgbMain-like completo
  (init → zera EWRAM 0x1C000 → loop {per-frame; soft-reset A+B+START+SELECT;
  `game_loop_body_like` 0x080582E0}) — H-0017 CONFIRMADO-estrutural.
- Novos nomes: `memzero_ewram_like` (PROV.), `game_loop_body_like` (PROV.),
  `per_frame_update_like` (HIP.), `encrypt_xor_boxsubdata_like` (HIP.).
  Registry → 21 entradas.

### Ciclo 10 — 2026-10-14 (corpo do loop fechado; 0x080582E0 era checagem)

- 0x080582E0 lido completo: **predicado por-frame** (35 insns) — renomeado
  para `combo_pred_cb08057ded_like` (PROVÁVEL; historico preserva o erro do
  nome anterior — disciplina de não confundir leitura parcial).
- Corpo real do loop (`0x08000478…0x080004AA`): `[030030E4]=0` → tick
  0x080004B0 (0x0800B178/0x08000510) → combo 0x08058274 →
  **`frame_counter59_rollover_like`** (contador @0x0300500C+0x12, rollover
  0x3B≈1s) → **`dispatch8_idx03000FC4like`** (jump table 8 entradas
  @0x0807196C, `mov pc,r0` — 3º despachante da arquitetura) →
  `vblank_flag_sync_like` → **`b 0x0800041A` (loop fechado ✓)**.
- Registry → 24 nomes. Elo com hub 0x0808CFF8 ainda não achado via estática
  (2 despachantes do loop mapeados; restam casos do 8c + escritores da célula
  0x03000E84).

### Ciclo 11 — 2026-10-14 (casos do dispatch8 + rastro da célula de callback)

- Tabela @0x0807196C: `[0,2,3,4]=no-op`; `[1]=avança índice state + bl
  0x080722A0`; `[5-7]=bl 0x08071DD4 guardado → 0x08071C9C` → dispatch8 =
  máquina de estados por-frame (processo/task manager).
- Varredura de usos de **[0x03000E84]** (5 regiões +1 falso desalinhado):
  struct-base **0x03000E80** com sentinelas `0x80→0x81`; função
  `cb_task_state_machine_like` 0x080579C4 (HIPÓTESE; dispatch auxiliar
  @0x08057A5C, ponteiros Thumb 0x08057DA5/0x08057DED) — padrão de
  **instalador/executor de callbacks de estado**.
- Registry → 25. Próximo: helpers 0x08071DD4/0x08071C9C/0x080722A0 (elo do
  hub indireto) — ou mGBA (76) para cravar de uma vez.

### Ciclo 12 — 2026-10-14 (task manager = processos por CALLBACK — achado)

- `pred_flag03007304zero_like` (guarda do dispatch8), `cb_install_thumbptr_like`
  (instalador de callbacks p/ sentinelas), `statecb_step_r4{0x11,0x1A}_like`
  (passo+next-state 0x11/0x1A), `lookup_sanitized_idx081dd0f4like`.
- **Achado estrutural:** `pool_find_bycb_arr03005090like` busca slot **pela
  função de callback** no pool H-0010 → o sistema aloc/free é orientado a
  callback → arquitetura CONFIRMADA: processos/tarefas por-frame c/ estados.
### Ciclo 13 — 2026-10-14 (elo do hub: NEGATIVA estática = achado arquivístico)

- Busca exaustiva ao nó/chunk: 0 literais (par/Thumb+1), 0 ADR, 0 BL, 0
  branches (T16/T32), 0 ponteiros externos; **252 ponteiros intra-chunk**.
  O "117 callees" era artefato de atribuição do gap de 7.956 B.
- Veredito: chunk só entra por registro dinâmico → instalação de mGBA sobrou
  como **análise mais barata** (PC-trace + watchpoints de slot). H-0016
  BLOQUEADO-p/-estática; nota de onde o callgraph infla (outdegree)
  documentada no notes_estrutura (valerá p/ outros "hubs" próximos).

### Ciclo 14 — 2026-10-14 (dispatcher 5c fechado = família completa)

- tbl0807449C: `[0-2]→read_u8_arr02023BD6` (CONFIRMADO), `[3,4]→byte_flag0`
  → DISPATCHER_5c é o **selector do subsistema array 0x02023BD6**.
- Família de dispatchers agora quantificada: 2×34c (mon GET/SET), 8c (task
  states), 5c (arrays) = idioma `idx→tbl+mov pc,r0` recorrente.
- Registry → 32.

### Ciclo 15 — 2026-10-14 (espaço livre mapeado + desenho do hook; mGBA: caminho achado)

- mGBA: pacote "mgba" não existe no apt, **mas `libretro-mgba` /
  `libmgba0.10t64` / `libmgba-dev` ESTÃO no repositório** — opção novamente
  executável (headless ou via lib); decisão de integração pendente.
- `reports/freespace_map.tsv`: 171 runs ≥256 B; reserva in-file
  **`0xEB0B20 + 1.373.408 B de 0xFF` = corpo dos trampolins**; 0x00-runs
  anotadas como candidatas a dados.
- `notes_mods_codigo.md` (spec do `gba_hook_code.py`: 6 validações
  obrigatórias + trilha de validação dinâmica + checklist de rollback).

### Ciclo 16 — 2026-10-14 (hook IMPLEMENTADO + demo dry-run real)

- **`scripts/gba_hook_code.py` v1.0.0** (self-test 6/6; 2 classes de bug
  corrigidas no ato: hex push/pop e import de constante capstone).
- **Demo REAL dry-run**: site 0x080005B2 (BL a `SetGpuReg_like`) →
  trampolim em 0x08EB0B20 (`push {lr}; bl alvo; pop {pc}`); 10 bytes
  alterados; ocupação registrada (logs/hook_occupancy.jsonl).
  Marcado `HOOK_DRYRUN_NAO_VALIDADO.gba` — faltava validação em emulador.
- Caminho dinâmico: baixar .debs `retroarch`+`libretro-mgba` sem root
  (`apt-get download` + `dpkg-deb -x`) → próximo ciclo tenta.

### Ciclo 18 — 2026-10-14 (HOOK VALIDADO DINAMICAMENTE ✅)

- `--payload-contador ADDR` no gba_hook_code.py (self-test 7/7): trampolim
  `push{lr}; ldr r0,[pc,#12]; ldr/str/adds; bl ALVO; pop{pc}; literal`.
- Persistência ler: acesso **0x0E000000 (save flash) NÃO reflete em region 0**
  (interceptado pela emulação de flash); contador via save = falso negativo.
- Validação visual definitiva: contador apontado para a **paleta de fundo
  0x05000000** no site per-frame 0x08000B08 → tela fica **BRANCA** (backdrop
  incrementado a cada frame) em 200 frames sem crash → responsivo dinâmico.
  `rom_mod/HOOK_VALIDADO_paleta_OK.gba` + reports/emu_hook_pal.png.
- Fixes do driver: restype ctypes p/ memory_data/size (truncava ptr 64-bit
  → segfault); preload RTLD_GLOBAL de libinih (env confiável); mem-region
  (rg 0 = SAVE 128 KiB é a única exposta).

### Ciclo 19 — 2026-10-14 (agenda de input: título alcançado)

- Driver `--input FRAME:BTN[:SEG]` (janela start→hold, mapeamento libretro)
  e `--snap FRAME=out.png` (captura por frame).
- Run 1300 frames: START@880 pula intro; **frame 1280 = TÍTULO
  "POKéMON FIRE RED BR"** (Charizard + ©2004) — marca "BR" da tradução
  renderizada (confirma H-0001b na tela, visualmente) e agenda FUNCIONAL.
  reports/emu_i{880,1050,1280}.png (intro Gengar×Nidorino → título).

### Ciclo 20 — 2026-10-14 (menu navegado; serialize/unserialize OK)

- Driver ganha `--save-state/--load-state` (retro_serialize, 528 KiB/state)
  → ciclos de navegação longa viram encadeáveis (marcos serializados).
- Run 3600: title PRESS START@1750 → A@1900 selecionou **CONTROLE** →
  tela tutorial em PT-BR renderizada (texto BR confirmado em jogo:
  "Os vários botões teram sua importância explicada por ordem.").
- Estado marco salvo: emu/state_3600.bin. Próximo: voltar ao menu, NOVO
  JOGO → intro do Carvalho (script walk com checks de snapshots).

### Ciclo 21 — 2026-10-14 (densa navegação: modelo do pós-título)

- Recon: nesta build BR o fluxo é **título → START → tutorial CONTROLE**
  direto (sem menu clássico visível); inputs pós-título precisam ser
  ≥ ~60 frames após título pronto (frames ≳1800).
- Cadência do tutorial: A troca de página (PRÓX) e volta — laço 1↔2;
  RIGHT deve mover PRÓX→VOLT (timing apertado); SNAPs pages 1/2 PT-BR.
- DECISÃO: a profundidade adicional p/ prova visual de espécie é
  **opcional** (nice-to-have); prioridade da agenda recai nos pontos de
  fechamento técnico (docs, bateria de testes, alt-route watchpoint).
- Cycle scoreboard ajustado: 74 → NAVEGAÇÃO VALIDADA ✓ (título/CONTROLE);
  nova nota 66 (PROVA VISUAL espécie) = opcional, fim de fila.

### Ciclo 22 — 2026-10-14 (observador: rotas esgotadas e registradas)

- Implementada leitura REAL via retro_memory_descriptor (SET_MEMORY_MAPS,
  env cmd 36) → **mGBA-libretro publica 0 descritores** (rota morta).
- Estado das rotas p/ EWRAM/IWRAM c/ este core: region0=apenas SAVE;
  memory map vazio; (cheat system escreve mas não lê p/ o host).
- **H-0010 (pool 0x03005090 guarda alguma estrutura/máquina de estados)
  permanece DESCONHECIDO** — suposição não verificável nesta plataforma;
  alternativa futura documentada: payload-sampler que espelhe EWRAM no FB.
- Driver mantém SET_MEMORY_MAPS + map_read (úteis p/ cores que publiquem).

### Ciclo 23 — 2026-10-14 (varredura: bateria de testes 8/8 OK)

- `scripts/run_all_tests.sh` (bateria padronizada, log em logs/tests_*.log,
  exit agregado). Rodada inaugural: 4 falhas → causas: capstone ausente
  (venv não persistido entre snapshots — `pip install capstone`) e rota de
  carga do core Linux no self-test do driver. Correções aplicadas:
  self-test do emu usa o mesmo preload RTLD_GLOBAL do core.
- **Bateria final: 8/8 scripts OK** (logs/tests_20261015_005705.log).
- README atualizado com a bateria.

### Ciclo 25 — 2026-10-14 (mod-menu C1: observabilidade + espelhos de input)

- `scripts/gba_state_dump.py`: parser/editor de save-state; **EWRAM/IWRAM/
  SAVE legíveis e patcháveis no blob** (layout validado por ground-truth).
- Espelhos de input identificados (diff A/B RIGHT): **0x03003118/0x0300311C
  = held/new keys** (0x010 = RIGHT) → padrão p/ leitura de combos no hook.
- Pool 0x03005090 visto no state: ponteiros de código (reforça H-0010).

### Ciclo 26 — 2026-10-14 (limpeza de memória + consolidação)

- **`MEMORIA_CONSOLIDADA.md` criado** — memória executiva autoritativa
  (identidade, fatos-chave c/ provas, ferramentas+gotchas, estado do mod
  menu, evidências mantidas, rasura de remoções).
- Leitura completa do workspace; redução de **113 MB → 65 MB**:
  removidos rom_mods obsoletos/superseded (3 ×16 MiB) e um PNG sem efeito;
  probes do ciclo 21 arquivados em `reports/probes_c21/` (52 itens);
  logs de testes antigos removidos (ficou o mais recente — 010206).
- Bateria relida: 9 scripts cobertos; `gba_state_dump.py` recebeu
  `--self-test` (5/5 — trad/read/patch round-trip/preservação), bateria 9/9.
- Nenhum artefato de evidência primária apagado (boot, hook, título,
  CONTROLE, PIDGEY-text-mod, states, callgraph, TSVs íntegros).

### Ciclo 27 (mod-menu M2) — 2026-10-14 (navegação avançada + DIÁGNÓSTICO)

- **Workflow save-state-branches operacional** (load-state → 100–1000 frames
  → snap/state): dezenas de ramos testados em minutos (vs. boots completos).
- **Handler de input do tutorial decodificado** (0x0812F0B0): lê só borda de
  A/B (0x0300311E & 3); direcionais NÃO navegam (diff A/B confirmou ZERO
  mudança de cursor c/ RIGHT). Stage = [0x0203B108]+0x12 ∈ {0,1,2}:
  controle1 →A→ controle2 →A→ PIKA(aventura) →A→ loop controle1;
  **START/B na última tela ⇒ soft-reset GAME FREAK**.
- **State-patching PROVADO:** forçar stage=2 no save-state levou à tela
  PIKACHU intro — controle total da máquina de estados por memória.
- Strings de menu existem na ROM (CONTINUE/MYSTERY GIFT/NOVO JOGO) mas
  **nenhuma rota por botões alcança o menu clássico nesta build** após
  ~20 ramos testados → bloqueio: acesso ao gameplay depende de informação
  externa (save/como o jogador real começa).

### Ciclo 28 (mod-menu M2 ✓) — 2026-10-14 (CHEGA-SE AO JOGO real)

- Caminho empírico completo: título→START→tutorial (3 telas em laço) →
  persistir em A → **intro do OAK** → nome do jogador (SIM/NÃO c/ A) →
  rival: **teclado se navega por D-pad** (RIGHT troca coluna; DOWN entra
  na coluna amarela; A confirma quando o cursor aterrissa nos botões) →
  rival sprite + diálogos → 24 iterações A → **QUARTO (Pallet) INGAME**
  (`emu/state_g23.bin` = marco definitivo; reports/g_15.png, g_23.png).
- Regra de ouro: em telas de transição ou fadoverlapada, usar cadência
  ≥150 frames entre presses (locks duram ~100); START no teclado = ALT,
  OK só pelo cursor; não há menu clássico acessível (título→tutorial só).
- Próximo (M3): localizar party/bolsa na EWRAM via state-diffs (antes/
  depois do starter), mapear item-slots e construir o payload do combo.

### Ciclo 17 — 2026-10-14 (FASE 4 DESBLOQUEADA: GBA rodando no sandbox!)

- Fix do driver: `retro_get_system_av_info` só **após** load_game (causa do
  segfault, diagnosticado por bisseção de callbacks; callbacks nulos de
  áudio/input também derrubam retro_run — lição arquivístico).
- **`gba_libretro_emu.py` v0.3.0**: mGBA 0.10.5 (.deb extraído sem root)
  emulando 600 frames: 240×160 @59,728 fps RGB565, PNG de framebuffer,
  mem-read (EWRAM) — self-test 5/5 + retry OK.
- **Boot confirmado visualmente:** tela GAME FREAK renderizada
  (reports/emu_boot_original.png).
- **Demo de texto PATCHED:** mesmo frame byte-idêntico → boot intocado.

## Obstáculos / riscos

| # | Item | Impacto | Mitigação |
|---|------|---------|-----------|
| 1 | ROM ausente | trava Fases 1–7 | usuário fornece arquivo ou caminho |
| 2 | Ambiente = Linux, briefing = Windows | comandos mudam | scripts multiplataforma + equivalentes Windows sob demanda |
| 3 | Java 11 < JDK 17 exigido pelo Ghidra atual | Fase 2 | instalar JDK 17 (gratuito) ou Ghidra 10.x; decidir quando a ROM existir |
| 4 | RAM 1,9 GB | Ghidra apertado | -Xmx1g headless; scripts leves primeiro |
| 5 | Pacotes pip não persistem entre sessões do sandbox | capstone pode sumir | `scripts/setup_env.sh` idempotente (rodar 1 vez por sessão) |

## Placar de prioridades (score 0–100) — próximas tarefas

| Score | Tarefa | Desbloqueia | Depende de |
|------:|--------|-------------|-----------|
| ~~90~~ ✓ | Censo ampliado 0x0–0xEC0000 | feito no ciclo 6 | — |
| ~~86~~ ✓ | `gba_callgraph.py` (DOT, métricas, SCC) | feito no ciclo 6 | — |
| ~~84~~ ✓ | Casos dos dispatchers → GET/SET struct (H-0014/15, PROVÁVEL) | feito no ciclo 7 | — |
| ~~78~~ ✓ | Hub 0x0808CFF8 → controller indireto (H-0016) | feito no ciclo 7 (nome exato: mGBA) | — |
| ~~70~~ ✓ | Helpers de caixa lidos → Get/SetBoxMonData-like CONFIRMADO (ciclo 8) | — | — |
| ~~64~~ ✓ | Corpo SET 0x080404D0 confirmado (ciclo 9) | — | — |
| ~~68~~ ✓ | Loop principal mapeado: H-0017 CONFIRMADO (ciclo 9) | — | — |
| ~~62~~ ✓ | Casos do `dispatch8` mapeados + célula de callback rastreada (ciclo 11) | — | — |
| ~~60~~ ✓ | Helpers lidos → task manager = processos por callback (CONFIRMADO-estrut., ciclo 12) | — | — |
| ~~58~~ ⛔ | Elo do hub: esgotada estática (ciclo 13) → só mGBA | fechar H-0016 | mGBA (76) |
| ~~48~~ ✓ | `gba_hook_code.py` implementado + demo dry-run (ciclo 16) | — | — |
| ~~*80~~ ✓ | Emulador no sandbox (mGBA core via apt-libretro, sem root) — CICLO 17 | — | — |
| ~~*82~~ ✓ | Hook VALIDADO dinâmico (ciclo 18: paleta→branco, sem crash) | — | — |
| 74 | Agenda de input (START p/ título+menu) → prova visual do PIDGEY! na Pokédex | patch de texto confirmado | emu ✓ |
| 70 | Payload real de mod: experimento controlado p/ ++ counter visível (H-0010 watchpoint alternativo) | mods funcionais | hook ✓ |
| 72 | Agenda de input (START→título) + navegar p/ tela da espécie p/ prova visual do PIDGEY! | patch de texto confirmado | emu ✓ |
| 68 | Watchpoint-por-polling (mem-read por frame) em 0x03005090 (H-0010) + escritor do chunk | H-0010/H-0016 dinâmicos | emu ✓ |
| 56 | DISPATCHER_5c tbl0807449C: ler 5 casos (3º dispatcher nomeado) | família de dispatchers completa | disasm ✓ |
| 55 | Ghidra headless (JDK17) | Fase 2 aprofundada | download |
| ~~50~~ ✓ parte A | Mapa de espaço livre + spec do hook (`notes_mods_codigo.md`) | spike de hook | — |
| 48 | **Implementar `gba_hook_code.py`** (6 validações da spec); demonstração só no dry-run até mGBA | infra de mods funcional | disasm ✓ |

## Próxima ação de maior valor

**ESTÁTICA:** dispatcher de 5 casos @0x0807449C (score 56 — família fechada) —
barato e conclusivo. **CRÍTICO DE VALOR:** mGBA (*78) — o elo com o chunk
dinâmico 0x0808Cxxxx (H-0016), os pools de callback e a validação visual do
patch demo concentram-se na Fase 4; vale instalar agora.

## Estimativa de conclusão (heurística, atualizada por ciclo)

Cobertura: Fases 0–1 ✓; Fase 2/3 ~70% (censo+callgraph+33 nomes+3 famílias
de despachantes+loop+caixa); Fase 4: 0% (gargalo); Fases 5–7: parciais.
**ETA total: ~10–15 ciclos restantes** (incerteza alta — depende de mGBA):
| Marco | Ciclos |
|---|---:|
| nomear subsistema do chunk 0x0808Cxxxx / fechar H-0016 | +2–3 (com mGBA: 1) |
| Fase 4: instalação, watchpoints, PC-trace, validação do patch demo | +3–5 |
| infra de mods de código (espaço livre + trampolim + teste) | +3–4 |
| varredura final + Fase 7 validada + documentação de fechamento | +2–3 |
Progresso estimado do projeto: **~62%**.
( inserção ciclo 17 abaixo )

## c34 (parcial) — v3 veneer + 'input-mudo'
* SEMÁFORO c34: v3 = site-veneer em 0x08000A38 (ldr/bx/literal) + tramp 0x08EB0C00 (push{r0-r3}/payload(98%)/pop/replay/bx-back-Thumb-bit).
* Motivo do re-deseigno: BL thumb range ±4 MB; site antigo→tramp 15,4MB = IMPOSSÍVEL (explicava TODAS as travas c32/c33; v2 estátic@©2004 = sombra disso).
* Freespaces ±4MB ao redor de 0x08000B08: ZERO com ≥256B. Novo site em SetGpuReg(0x08000A38, 8B relocáveis) sobrepuja isso.
* Build v3 ok; boot v3: duas PNGs **brancas/iguais** @480 e @2900 — ainda duvidoso (validar se branco=legítimo boot).
* No jogo (state_bt7): overworld estável; combo L+R+START 170f: SEM preenchimento da bolsa; START solo não abre menu (3 runs idênticos — suspeita 'input-mudo' do state); A,A,B,START muda md5 → core-input funciona.
* Achado ruim: **0x03003118 como espelho de teclado zera no contexto bedroom-v3st1** (estado contexto-dependente!). Pede-se major-fonte-padrão de teclas.
* Casa-organizadora: usuário pediu arquivos do projeto → atualização desta memória + empacotamento (sem ROM original).

## c35 — 2026-10-15 (retomada: encoder homologado + emulador reconstruído + isolador pronto)

* **FATO — encoder BL homologado de vez**: `encode_bl_thumb` re-encodou os 88.782
  pares de `reports/pokemon_firered_bpre_trabalho_callsites.tsv` e decodificou com
  capstone: **0 divergências nos 51.041 pares dentro da faixa**; 37.741 pares são
  alvos cross-seção fora de ±4 MB e agora são **rejeitados com ValueError** (patch:
  guarda de faixa `[-0x200000,+0x1FFFFF]` halfwords + alvo halfword-alinhado).
  O wrap silencioso em exatamente `off=+0x400000` (1.579 pares) apontava para
  outro lugar — era o risco que "validava campo, não alcance".
  Hipótese Align(PC,4) na base do BL: TESTADA e DESCARTADA (piorava 26.118 pares
  site%4==2; base correta = site+4 sem alinhamento). Self-test gba_disasm 14/14
  (bordas +0x1FFFFF/-0x200000 aceitas; +0x200000/-0x200002 rejeitadas; extremos
  decodificam ao alvo via capstone). §4 da MEMÓRIA atualizada para RESOLVIDO.
* **FATO — emulador de volta**: `mgba_libretro.so` empacotado (Ubuntu noble)
  exigia GLIBC_2.38 e não carregava no Debian 12 (glibc 2.36) — self-test era 4/5.
  Core **mGBA 0.10.5 reconstruído do fonte** (github.com/mgba-emu/mgba @0.10.5,
  cmake+ninja via pip, zlib embutido) e instalado em
  `emu/x/usr/lib/x86_64-linux-gnu/libretro/mgba_libretro.so` (original preservado
  em `*.ubuntu-noble-glibc238.bak`). Mesma versão 0.10.5 → compatibilidade de
  save-state preservada. Bateria: **9/9 scripts PASS**.
* **FATO — isolador do gating PRONTO para a ROM** (HANDOFF §1):
  `reports/tramp_always.hex` (52 B) = payload que SEMPRE grava 0xAAAA (word) em
  `0x020258B8` — se nem isso gravar, o trap não roda na cena (trocar rotina-trampo);
  `reports/tramp_regkey.hex` (90 B) = fonte robusta de teclas via REG_KEYINPUT
  `0x04000130` (ativo-baixo → `mvns` → máscara 0x3FF → cmp 0x0308 L|R|START).
  Aplicador: `scripts/apply_mod_dbg.py --variant always|regkey` (mesmos asserts
  do v3: prólogo 8 B originais + destino 0xFF).
  **Auditoria capstone dos trampos pegou 3 bugs de hand-assembly antes da ROM**:
  `40 43` era `muls` (não `mvns`), `bne` pulava o `pop{r0-r3}` (corrupção de pilha
  no caminho sem-combo) e `02 80` era `strh` (não `str`). Corrigidos e validados
  (10/10 checks estruturais: bne→pop, prologo/epílogo, stores).
* **Bloqueio**: ROM ausente no workspace (regra: não entra em git). Com a ROM em
  `rom/`, o próximo passo é literalmente:
  `python3 scripts/apply_mod_dbg.py --variant always && python3 scripts/gba_libretro_emu.py --rom rom_mod/BAG_MOD_dbg_always.gba --load-state <state_bedroom> --frames 900 --save-state out.bin && python3 scripts/gba_state_dump.py out.bin --read 0x020258B8:0x04`
  → dump `0xAAAA0000` = trap roda (gating é só teclas; partir p/ regkey);
  dump `00 00 37 dd` (fill) = SetGpuReg não dispara na cena → trocar rotina-trampo
  (candidatas: per-frame vblank / ReadKeys).
* Nota de ambiente: save-states `emu/*.bin` também estavam gitignored — serão
  refeitos via agenda de input (ciclo 28) ou fornecidos pelo usuário.

### Ciclo 35 (continuação) — 2026-10-16: causa-raiz do v3 + combo provado

* **ROM** obtida do Google Drive e verificada (sha256 = inventory.json). Sem git.
* **Bug 1 (FATO)**: veneer `01 4b` lia literal em 0x08000A40 (código original, `0x2C5F0C09`)
  em vez de 0x08000A3C → `bx` para lixo no 1º SetGpuReg → tela branca. Corrigido para `00 4b`
  (`ldr r3,[pc,#0]`; regra Align(PC,4)+imm·4 confirmada no próprio código do jogo).
* **Bug 2 (FATO)**: retorno do tramp 0x08000A43 pulava `lsrs r1,r1,#0x10`@0xA40. Correto = 0x08000A41.
* **Bug 3 (FATO)**: máscara do tramp_regkey virava 0xFF00 (não 0x3FF) → `== 0x308` nunca verdadeiro.
  Tramp remontado (88 B, bne→pop validado, capstone).
* **Isolador always** (`rom_mod/BAG_MOD_dbg_always.gba`, sha256 b59de9ec…): 600 frames → PNG
  IDÊNTICO byte a byte ao original (`reports/c35_lit600.png` = `c35_orig600.png`); bolsa slot0 = `0xAAAA` → trap roda.
* **Prova semântica** do tramp_regkey (mini-emulador Thumb): 5/5 (combo exato escreve; sem teclas,
  L+R sem START, L+R+START+A e START sozinho NÃO escrevem; pilha/r5/lr/prólogo/retorno OK).
* **Combo no mGBA**: `--input 150:L:200 --input 150:R:200 --input 150:START:200` → bolsa `aa aa 00 00`
  (`reports/c35_key_combo.png`); controle sem combo → `00 00 00 00` (`BAG_MOD_dbg_regkey.gba`).
* Sintaxe de input do emulador: `FRAME:BOTAO[:SEGURAR]`, um item por botão.
* Commit `05b1bc4` + merge com remoto (`d1b9d14`). PR #2 (revert do workflow JDK, obsoleto frente ao PR #3) FECHADO.
* PENDENTE: aceitação visual completa (overworld/quarto, menu START com bolsa cheia, 60 s estável) e
  mod de preenchimento real (`apply_mod_v3`-equivalente com payload de itens) — o regkey atual só grava 0xAAAA.

### Ciclo 35 — ENCERRAMENTO (2026-10-16)

Projeto encerrado nesta fase. Ponto de entrada para retomar: **`RETOMADA.md`**.

* **FATO, corrigido**: 4 bugs no mod v3 (veneer `00 4b`; retorno `0x08000A41`; máscara `0x3FF`;
  endereço `0x020258B8`). Mod v4 gerado por `scripts/gen_tramp_v4.py` e provado por
  `scripts/test_tramp_v4.py` (5/5) e no boot (`reports/c35_v4_nocombo600.png` idêntico ao original;
  combo no frame 150 grava os 8 slots).
* **FATO, falha**: combo dentro do jogo não dispara (bolsa zerada após o frame 4000).
  HIPÓTESE: o hook roda só na inicialização; falta uma rotina por frame.
* **FATO**: `.sav` do mGBA no Drive está vazio (131072 B, todos `0xFF`). `.st0` do MyBoy é state
  fechado, não carregável; IWRAM localizada em `0xB8`; EWRAM não localizada; SAVE vazia.
* **ABERTO**: navegação até o overworld. Estágio do tutorial em `0x02000022`; patch → intro do
  Pikachu; A não avança essa intro. Ver `scripts/c35_nav_recipe.sh`.
* Ambiente: `rom/`, `emu/*.bin`, `/tmp` e saves do usuário ficam fora do git (ignorados).
  Restaure a ROM do Drive e confira o sha256 antes de retomar.
* Documentos corrigidos: `HANDOFF.md` (veneer e retorno), `README.md` (retorno), `MEMORIA_CONSOLIDADA.md` §5.
