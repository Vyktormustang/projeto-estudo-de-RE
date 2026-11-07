# gba-re — Engenharia Reversa Automatizada de ROM de Game Boy Advance

Projeto de reconstrução técnica verificável do código e da lógica interna de um
jogo de GBA (título a identificar), seguindo o plano em 7 fases + protocolos de
validação e priorização definidos no briefing do projeto.

## Estado atual

- **ROM:** `IDENTIFICADA` — cópia de trabalho em `rom/pokemon_firered_bpre_trabalho.gba`.
  Família: **Pokémon FireRed (BPRE, USA, Rev 0 de cabeçalho)**, imagem **modificada**
  (não bate com dumps limpos No-Intro) — nome do arquivo sugere tradução PT-BR
  (H-0001b, PROVÁVEL, a confirmar via texto decodificado). O original do usuário
  permanece intacto em `uploads/`; ROM nunca entra em repositórios públicos.
- **Ambiente de execução deste assistente:** sandbox **Linux Debian 13 x86_64**
  (o briefing cita Windows — tudo aqui é multiplataforma; equivalentes Windows
  são fornecidos sob demanda). Ver `logs/2026-10-14_fase0_ambiente.md`.
- **Toolchain:** Python 3.13 + capstone instalado; Git 2.47; OpenJDK 11
  (atenção: Ghidra ≥ 11 exige JDK 17 — pendente decisão na Fase 2).

## Estrutura (memória persistente)

```
gba-re/
├── README.md            ← este arquivo
├── inventory.json       ← inventário da ROM + manifesto de artefatos (hashes)
├── functions.csv        ← funções: endereço, nome, classificação, confiança
├── hypotheses.md        ← hipóteses, evidências, testes pendentes
├── progress.md          ← progresso, obstáculos, próximas ações (fonte primária)
├── callgraph/           ← grafo de chamadas (Fase 3, quando disponível)
├── scripts/             ← automação (veja abaixo)
├── logs/                ← registros reproduzíveis de cada execução
├── reports/             ← relatórios gerados pelos scripts
└── tests/               ← fixtures sintéticas rotuladas (NUNCA confundir com a ROM real)
```

## Scripts

| Script | Fase | Objetivo |
|---|---|---|
| `scripts/setup_env.sh` | 0 | Instala dependências mínimas (capstone). Idempotente. |
| `scripts/gba_ident.py` | 1 | Identificação/triagem da ROM: hashes, cabeçalho GBATEK, entropia por bloco, strings, padrões de código (Thumb BL / ARM BL). Tem `--self-test`. |
| `scripts/gba_poketext.py` | 1/5 | Decodificador do charset Pokémon Gen 3 (com validação por âncoras), dump de texto e sondas de idioma. `--self-test`. Suporta `--charset-override` (remap PT-BR: `notes_charset_remap_br.json`). |
| `scripts/gba_disasm.py` | 2/3 | Boot trace ARM (segue branches/literais até a transição Thumb), censo de funções por BL direto (capstone) com prova de prólogo-alvo por página, dual-check manual de BL. `--self-test`. Popula `functions.csv` (só prólogo limpo; reaplica `names_registry.json`) e exporta `reports/*_callsites.tsv`. Inclui `dis 0xADDR` (desassembly sob demanda com literais resolvidos). |
| `scripts/gba_callgraph.py` | 3 | Grafo de chamadas (BL direto) a partir de functions.csv + callsites: DOT, edges.tsv, métricas (top in/out-degree, BFS da entry, SCCs/Tarjan). `--self-test`. |
| `scripts/gba_table_probe.py` | 3 | Sonda de tabelas de salto (`--table`) e hubs (`--hub`): resumo de handlers (entrada/tail/BLs), BLs com nomes, pool de memória da janela. `--self-test`. |
| `scripts/gba_patch_text.py` | 6 | **Primeiro modificador seguro da ROM**: patch de slot de texto (0xFF), `--expect` pré-condição, `--slot-size` p/ passo fixo, anti-in-place, relatório hexdump+SHA-256. `--self-test`. |
| `scripts/gba_hook_code.py` | 6 | Instalador de trampolim de código: troca `bl #ALVO` em site por `bl #TRAMP` (payload Thumb + chamada original) em run 0xFF de `freespace_map.tsv`; 6 validações; DRY-RUN até validação em emulador. `--self-test`. |
| `scripts/gba_libretro_emu.py` | 4 | Driver libretro headless (mGBA core .deb, sem root): roda N frames, PNG 240×160, agenda de input `--input`, snapshots `--snap`, save-state `--save-state/--load-state`, mem-read SAVE (rg0), preload RTLD de libinih. `--self-test`. |
| `scripts/run_all_tests.sh` | 7 | **Bateria única**: roda `--self-test` dos 8 scripts, log em `logs/tests_*.log`, exit agregado (0 = tudo OK). |

Registro de renomeações (sobrevive a regenerações): `names_registry.json`.
Notas verificadas sobre a estrutura da ROM: `notes_estrutura.md`.

## Regras operacionais (resumo do briefing)

1. ROM original preservada; trabalhar sempre em cópia.
2. Nada de inventar funções, endereços ou resultados. Fatos ≠ inferências ≠ hipóteses.
3. Níveis de confiança: **CONFIRMADO / PROVÁVEL / HIPÓTESE / DESCONHECIDO**.
4. Cabeçalho da ROM não prova identidade do jogo; é só um indício.
5. Não redistribuir a ROM nem recursos protegidos.
6. Classificação código/dados por heurística gera hipóteses, não fatos — validação
   definitiva acontece na análise estática (Fase 2 · Ghidra) e dinâmica (Fase 4 · mGBA).

## Referências técnicas confiáveis

- **GBATEK** (Martin Korth): https://problemkaputt.de/gbatek.htm — formato do
  cabeçalho, mapa de memória, registradores de hardware do GBA.
- Capstone Engine: https://www.capstone-engine.org — desassemblador ARM/Thumb.
- Ghidra: https://ghidra-sre.org (Fase 2) · mGBA: https://mgba.io (Fase 4).

## Uso rápido (Linux/macOS; Windows entre parênteses)

```bash
# 0) setup mínimo
bash gba-re/scripts/setup_env.sh          # (Win: python -m pip install capstone)

# 1) identificação — apontar a COPIA da ROM
python3 gba-re/scripts/gba_ident.py rom/jogo.gba -o gba-re/reports \
    --update-inventory gba-re/inventory.json
# (Win: py gba-re\scripts\gba_ident.py rom\jogo.gba -o gba-re\reports)

# validar a ferramenta sem ROM (fixture sintética rotulada)
python3 gba-re/scripts/gba_ident.py --self-test
```
