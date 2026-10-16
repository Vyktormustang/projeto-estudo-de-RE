# RETOMADA — projeto Pokémon FireRed (BR) · mod de bolsa (encerrado em 2026-10-16, ciclo 35)

> **Ponto de entrada único.** Se você está recomeçando (outra máquina, outro agente, outro dia),
> leia este arquivo primeiro. `HANDOFF.md` e `MEMORIA_CONSOLIDADA.md` são o histórico; onde
> conflitarem com este arquivo, **valem os números daqui** (corrigidos no ciclo 35).

Legenda: **FATO** = verificado por teste/captura nesta sessão · **HIPÓTESE** = inferência não
confirmada · **ABERTO** = não resolvido.

---

## 1. Objetivo
Mod-menu no FireRed BR (BPRE): combo **L+R+START** (`0x0308` em `REG_KEYINPUT` ativo-baixo) preenche
a bolsa em `0x020258B8` (8 slots `{id:u16, qty:u16}`, 4 B/slot). Aceitação: boot → logo → overworld
→ combo → menu START → tela da bolsa cheia → estável 60 s.

## 2. Estado em uma tabela

| Item | Estado | Evidência |
|---|---|---|
| Causa-raiz das falhas do v3 (3 bugs) | **FATO, corrigido** | §4 |
| Gating L+R+START (`tramp_regkey`) | **FATO** — prova semântica 5/5 | `scripts/test_tramp_v4.py` |
| Mod v4 (`BAG_MOD_v4.gba`) no boot | **FATO** — sem combo: PNG 600f idêntico ao original; com combo (frame 150): 8 slots corretos | `reports/c35_v4_nocombo600.png`, `reports/c35_v4_combo600.png` |
| Combo **dentro do jogo** (overworld) | **ABERTO / falha** — bolsa segue zerada após o frame 4000 | HIPÓTESE: o hook (`SetGpuReg`) só executa na inicialização |
| Chegar ao overworld pela emulação | **ABERTO** — preso na intro do Pikachu | §6 |
| Save do usuário (`.sav` do mGBA) | **FATO: vazio** (131072 B, todos `0xFF`) | §5 |
| Save do usuário (`.st0` do MyBoy) | **FATO: state fechado**, não carregável no core; overworld de Pallet Town na miniatura | §5 |

## 3. Como reproduzir o que está provado

Pré-requisitos: Python 3 com `capstone` (`pip install --break-system-packages capstone==5.0.7`),
core libretro em `emu/x/usr/lib/x86_64-linux-gnu/libretro/mgba_libretro.so` (já versionado;
mGBA 0.10.5 recompilado, glibc 2.36). **A ROM não vai para o git**: coloque sua cópia em
`rom/pokemon_firered_bpre_trabalho.gba` e confira o sha256 com `inventory.json`
(`6035a98f…b4ae`).

```bash
# 1) montar o mod v4 (usa só reports/*.hex já versionados)
python3 scripts/gen_tramp_v4.py          # regenera reports/tramp_v4.hex (158 B)
python3 scripts/test_tramp_v4.py         # prova semântica: esperado TODOS OS CASOS OK
python3 scripts/apply_mod_v4.py          # -> rom_mod/BAG_MOD_v4.gba (ignorado pelo git)

# 2) sem combo: deve dar PNG idêntico ao original e bolsa zerada
LD_LIBRARY_PATH=emu/x/usr/lib/x86_64-linux-gnu python3 scripts/gba_libretro_emu.py \
  --rom rom_mod/BAG_MOD_v4.gba --frames 600 --png /tmp/nocombo.png --save-state /tmp/nc.bin
python3 scripts/gba_state_dump.py /tmp/nc.bin --read 0x020258B8:0x20

# 3) com combo L+R+START no frame 150: esperado 01 00 63 00 02 00 63 00 ...
LD_LIBRARY_PATH=emu/x/usr/lib/x86_64-linux-gnu python3 scripts/gba_libretro_emu.py \
  --rom rom_mod/BAG_MOD_v4.gba --frames 600 \
  --input 150:L:200 --input 150:R:200 --input 150:START:200 --save-state /tmp/c.bin
python3 scripts/gba_state_dump.py /tmp/c.bin --read 0x020258B8:0x20
```

Sintaxe do emulador: `--input FRAME:BOTAO[:SEGURAR]` (um item por botão; combo = três itens no
mesmo frame). `--snap FRAME=arquivo.png` captura. `--mem-read` precisa de `--mem-region 2` para EWRAM.

## 4. Causas-raiz corrigidas (FATO)

1. **Veneer**: `01 4b` lia o literal em `0x08000A40` (código original, `0x2C5F0C09`) em vez de
   `0x08000A3C`. Correto: **`00 4b 18 47 01 0c eb 08`** (`ldr r3,[pc,#0]`). A regra Align(PC,4)+imm·4
   foi confirmada no próprio código do jogo.
2. **Retorno do trampolim**: `0x08000A43` pulava `lsrs r1,r1,#0x10` (`0x08000A40`). Correto:
   **`0x08000A41`** (`0xA40|1`).
3. **Máscara do combo**: o builder virava `0xFF00`, então `== 0x0308` nunca era verdadeiro. Correto:
   máscara `0x3FF`; tramp remontado.
4. **Endereço da escrita (v3)**: `movs r3,#0x20; lsls #16` produzia `0x022058B8`. Correto:
   `0x020258B8` (`movs #2`). Corrigido no gerador `scripts/gen_tramp_v4.py`.

Lição de método: **nunca montar Thumb à mão sem auditoria capstone** + teste semântico. Foram
encontrados 6 erros de montagem manual ao longo do ciclo.

## 5. Saves do usuário (dados privados — ignorados pelo git)

- `emu/states_usuario/fr_usuario.sav` (`Pokemon - Fire Red (BR).sav` no Drive, do **mGBA**):
  131072 bytes, **todos `0xFF`** → cartucho sem nenhum save gravado no jogo.
- `emu/states_usuario/fr_usuario.st0` (do **MyBoy**, pasta `MyBoy/` no Drive): state fechado de
  37 KB comprimido (gzip), cabeçalho `GBASTATE` + `POKEMON FIRE` / `BPRE`, descompactado 527.992 B.
  - Miniatura `MyBoy/Pokemon - Fire Red (BR).st0.png`: overworld de Pallet Town (FATO pela imagem).
  - **Não carrega** no core (`retro_unserialize` falha). Formato do MyBoy não documentado; estados
    não são portáveis entre emuladores (confirmado no fórum do mGBA).
  - **IWRAM localizada (FATO)**: começa em `0xB8` do arquivo. Dois ponteiros batem exatamente com o
    state do core (`0x08000248` em IWRAM+`0x3A0C`; `0x03003580` em IWRAM+`0x3A10`), e o vetor de IRQ
    em `+0x7FFC` também.
  - **Layout não é contíguo** (depois da IWRAM sobram ~3,5 KB no arquivo). **EWRAM não localizada**
    (trechos informativos do core não aparecem no `.st0`, porque os states são de momentos
    diferentes do jogo). SAVE do `.st0` também está praticamente vazia.
  - Conclusão: converter o `.st0` exige mapear o serializador do MyBoy inteiro. Não recomendado.

## 6. Navegação até o overworld (ABERTO)

Caminho empírico (ciclo 20 e 28, re-verificado no ciclo 35):
- `START@880`, `START@1750`, `A@1900` → tela **CONTROLE** do tutorial (frame 2000).
- Tutorial: **A alterna as páginas 1↔2 em laço** (verificado em 2000, 3500, 4150). Não sai sozinho.
- Variável de estágio do tutorial: ponteiro em `0x0203B108`; estágio em **`[0x0203B108] + 0x12`**
  (`0x02000022` neste boot). Valor 0 = CONTROLE 1, 1 = CONTROLE 2, 2 = aventura do Pikachu (HIPÓTESE
  pelo ciclo 27).
- Patch `0x02000022 = 0200` + A → intro "No mundo que você está prestes a entrar…" (FATO,
  `reports/c35_nav_pikaintro200.png`).
- **Bloqueio (ABERTO):** nessa intro, A não avança o texto (testado com toque de 8 e 20 frames,
  espaçamento 120–150). Sem input, o estágio fica em 2 e a tela volta à página 2 do tutorial.
- Próxima hipótese a testar: o texto da intro usa outro botão, ou o estágio precisa de um segundo
  patch. Não testado.
- Caminho que chegou ao quarto no ciclo 28 (não documentado com frames): título → tutorial →
  intro do Carvalho → nome (SIM/NÃO com A) → rival (D-pad no teclado, A confirma) → 24×A → quarto.
  Use cadência ≥150 frames entre presses em telas de transição (locks duram ~100).

## 7. Caminhos para a próxima pessoa (em ordem de custo)

1. **Save real no mGBA desktop (mais rápido).** Jogar, fazer SAVE dentro do jogo, subir o `.sav`
   gerado ao lado da ROM. Depois: (a) adicionar `--load-sram` ao harness (escrever o `.sav` no
   buffer `retro_get_memory_data(0)` antes do primeiro frame — HIPÓTESE de que funciona como no
   RetroArch); (b) "Continuar" leva ao overworld; (c) testar o combo lá.
2. **Achar a rotina por frame** para o hook (vblank ou leitura de teclas). O hook atual só roda na
   inicialização (HIPÓTESE forte, pelo teste de 4000 frames). Ferramenta: `scripts/gba_disasm.py` +
   `callgraph/` + `reports/*_callsites.tsv`. Este é o bloqueio técnico real do objetivo.
3. Mapear o `.st0` do MyBoy (§5). Só vale a pena se os caminhos 1 e 2 falharem.

## 8. Armadilhas conhecidas

- Google Drive `download_file` grava em `<repo>/google_drive/<nome>` — mova para o destino certo.
- O ambiente pode ser recriado: `/tmp` some, `rom/` e `emu/*.bin` somem. Restaure a ROM do Drive
  (`14JCEJp6LFgdkzKMOtI5-l3XvowJ1SxnC`, sha256 em `inventory.json`) antes de testar.
- Rede limitada: só `github.com`, `api.github.com`, `codeload`, `registry.npmjs.org`, `pypi.org`,
  `files.pythonhosted.org`. `pip` precisa de `--break-system-packages`.
- Nunca commitar ROM (`rom/*.gba`, `rom_mod/*.gba`), states (`emu/*.bin`, `*.st0`, `*.ss0`) nem
  `.sav` — o `.gitignore` já cobre.
- Os arquivos `MEMORIA_CONSOLIDADA.md` e `HANDOFF.md` têm trechos antigos; os valores corretos estão
  na §4 deste arquivo.
- Thumb BL: base do PC = `site+4` **não alinhado**; encoder homologado em 51.041 callsites
  (`scripts/gba_disasm.py`, `encode_bl_thumb`).

## 9. Ferramentas e arquivos
- `scripts/gen_tramp_v4.py`, `scripts/test_tramp_v4.py`, `scripts/apply_mod_v4.py` — mod v4 (novo).
- `scripts/apply_mod_dbg.py` — isoladores `always` / `regkey` (v3-era, ainda válidos).
- `scripts/gba_libretro_emu.py`, `scripts/gba_state_dump.py` — emulação e leitura/patch de state.
- `scripts/run_all_tests.sh` — bateria (9/9 no ciclo 35).
- `reports/tramp_v4.hex`, `reports/site_v3.hex` (veneer corrigido), `reports/c35_*.png` (evidências).
- `progress.md` — histórico por ciclo; `inventory.json` — hash da ROM.
