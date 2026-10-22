# Importar a ROM de GBA no Ghidra (ARMv4T) — guia e evidências

> **Escopo.** Como importar a ROM no Ghidra com a arquitetura **certa** (ARMv4T,
> não ARMv7), com o mapa de memória do GBA já montado, o cabeçalho do cartucho
> rotulado e as entradas ARM/Thumb semeadas — tudo em um comando, com
> evidências em JSON e verificação cruzada independente.
>
> A ROM **não** entra no repositório. Projeto Ghidra e evidências ficam fora do
> git (`~/.local/opt/re-tools/ghidra-projects` e `reports/ghidra/`).

---

## 1. TL;DR

```bash
source scripts/re_env.sh              # JAVA_HOME + GHIDRA_INSTALL_DIR
bash scripts/ghidra_import_gba.sh rom/sua_rom.gba
```

Saída esperada (resumo):

```
[ghidra-import] rom:      /…/rom/sua_rom.gba (16777216 bytes, sha256 …)
[compare] OK  Python e Ghidra concordam em 11 campos do cabeçalho
[ghidra-import] funções: 12 000+ | símbolos: … | referências: …
[ghidra-import] âncoras encontradas: gba_cart_header@0x08000000, gba_game_title@…, REG_KEYINPUT@…, gBagSlots_slot0@0x020258B8, SetGpuReg@0x08000A38
[ghidra-import] IMPORT CONCLUÍDO
```

Sem ROM à mão? `bash scripts/ghidra_import_gba.sh --self-test` gera uma ROM
**sintética de 32 KB com cabeçalho válido** e roda o pipeline completo.

---

## 2. Por que ARM:LE:32:v4t (e não a lane do REA)

| Caminho | Linguagem | Serve para o GBA? |
|---|---|---|
| REA `--target-format raw-binary --architecture arm` | `ARM:LE:32:v7` (fixa, não configurável) | **Parcial.** O GBA é ARMv4T: não há `TMode` alternável pela lane raw, então código Thumb (a maior parte do jogo) não é seguido corretamente |
| **Ghidra direto com este importador** | `ARM:LE:32:v4t` | **Sim.** ARMv4T + Thumb, com `TMode` no contexto |

Confirmado na instalação: a linguagem existe em
`Ghidra/Processors/ARM/data/languages/ARM.ldefs` (`id="ARM:LE:32:v4t"`), e o
importador **valida isso antes** de rodar.

---

## 3. O comando que o script executa

```bash
analyzeHeadless "$GHIDRA_PROJECTS_DIR" gba_<sha8> \
  -import rom/sua_rom.gba \
  -processor ARM:LE:32:v4t \
  -loader BinaryLoader -loader-baseAddr 0x08000000 -loader-blockName GBA_ROM \
  -scriptPath scripts/ghidra_scripts \
  -preScript  GbaPrepareProgram.java pre  reports/ghidra \
  -postScript GbaPrepareProgram.java post reports/ghidra \
  -overwrite -analysisTimeoutPerFile 1800 -max-cpu <nproc> \
  -log reports/ghidra/analyzeHeadless.log -scriptlog reports/ghidra/ghidra_scripts.log
```

Todas as opções acima foram conferidas em duas fontes locais/versionadas:

- `support/analyzeHeadlessREADME.md` da própria instalação (opções `-import`,
  `-processor`, `-loader`/`-loader-baseAddr`, `-scriptPath`, `-preScript`,
  `-postScript`, `-analysisTimeoutPerFile`, `-max-cpu`, `-log`, `-scriptlog`,
  `-overwrite`) — inclui o **Exemplo 18** com `BinaryLoader` + `-loader-baseAddr 0x1000`;
- código-fonte oficial da tag `Ghidra_12.1.4_build`
  (`BinaryLoader.java`: opção `Base Address`, parse em hexadecimal).

**Pré-script vs post-script importa:** o mapa de memória (EWRAM/IWRAM/IO/…)
precisa existir **antes** da auto-análise, senão referências como
`ldr r0, =0x020258B8` não resolvem. Por isso `GbaPrepareProgram.java` roda duas
vezes: `pre` (antes da análise) e `post` (depois, só para evidências).

---

## 4. O que o pre-script faz (`GbaPrepareProgram.java`, modo `pre`)

### 4.1 Blocos de memória criados (se ainda não existirem)

| Bloco | Endereço | Tamanho | Permissões | Fonte |
|---|---|---|---|---|
| `GBA_ROM` (do loader) | `0x08000000` | tamanho do arquivo | R‑X | import |
| `GBA_EWRAM_256K` | `0x02000000` | 256 KB | RW | GBATEK |
| `GBA_IWRAM_32K` | `0x03000000` | 32 KB | RW | GBATEK |
| `GBA_IO_REGISTERS` | `0x04000000` | 1 KB | RW | GBATEK |
| `GBA_PALETTE_RAM` | `0x05000000` | 1 KB | RW | GBATEK |
| `GBA_VRAM_96K` | `0x06000000` | 96 KB | RW | GBATEK |
| `GBA_OAM` | `0x07000000` | 1 KB | RW | GBATEK |
| `GBA_ROM_MIRROR_0A/0C/0E` | `0x0A000000`… | 32 MB cada | R‑X | **opcional** (`--mirrors`), GBATEK |

Os mirrors ficam **desligados por padrão**: são decode de barramento, não
memória física, e só ajudam se você for seguir ponteiros que usem essas cópias.

### 4.2 Cabeçalho do cartucho (GBATEK §9.2)

Lido direto da memória e validado no programa:

- título (12 bytes em `0xA0`), código do jogo (`0xAC`), código do fabricante (`0xB0`);
- byte fixo `0x96` em `0xB2`;
- versão de software (`0xBC`) e **complemento** (`0xBD`) conferido contra
  `-(0x19 + sum(0xA0..0xBC)) & 0xFF`;
- palavra de entrada em `0x08000000` (deve ser `B` ARM) e alvo decodificado;
- palavra em `0x080000C0` (reportada crua, **sem** interpretação).

### 4.3 Rótulos criados (com nível de confiança)

| Endereço | Nome | Nível | Origem |
|---|---|---|---|
| `0x08000000` | `gba_cart_header` | CONFIRMADO | GBATEK |
| `0x080000A0` | `gba_game_title` | CONFIRMADO | GBATEK |
| `0x080000AC` | `gba_game_code` | CONFIRMADO | GBATEK |
| `0x080000B0` | `gba_maker_code` | CONFIRMADO | GBATEK |
| `0x080000BD` | `gba_header_complement` | CONFIRMADO | GBATEK |
| `0x080000C0` | `gba_word_at_0xC0` | OBSERVADO | sem interpretação |
| `0x04000000` | `REG_DISPCNT` | CONFIRMADO | GBATEK |
| `0x04000004` | `REG_DISPSTAT` | CONFIRMADO | GBATEK |
| `0x04000006` | `REG_VCOUNT` | CONFIRMADO | GBATEK |
| `0x04000130` | `REG_KEYINPUT` | CONFIRMADO | GBATEK (ativo-baixo) |
| `0x04000200/02/08` | `REG_IE` / `REG_IF` / `REG_IME` | CONFIRMADO | GBATEK |
| `0x020258B8` | `gBagSlots_slot0` | CONFIRMADO no projeto | README (slot 0 da mochila) |
| `0x08000A38` | `SetGpuReg` | CONFIRMADO no projeto | README (site do hook v3) |
| `0x03003118` | `gKeysMirror_HIPOTESE` | **HIPÓTESE** | HANDOFF (bug aberto) |

### 4.4 Seeds de entrada

1. **ARM (CONFIRMADO):** decodifica o `B` em `0x08000000` e cria função no alvo.
2. **Thumb (HIPÓTESE):** se no alvo houver `ldr rX, [pc, #imm]` e o literal for um
   ponteiro **ímpar** dentro da ROM, marca `TMode` no contexto, desmonta e cria
   `gba_entry_thumb_guess`. É heurística — o relatório grava
   `"confidence": "HIPOTESE"` e o método usado.

---

## 5. Evidências geradas (`reports/ghidra/`)

| Arquivo | Conteúdo |
|---|---|
| `rom_header.json` | cabeçalho lido **em Python** (independente do Ghidra) + sha256 da ROM |
| `gba_prepare_pre.json` | blocos criados, cabeçalho lido **pelo Ghidra**, rótulos, seeds, avisos |
| `gba_prepare_post.json` | contagem de funções/símbolos/referências, funções na ROM, âncoras encontradas |
| `analyzeHeadless.log` / `ghidra_scripts.log` | logs oficiais do headless e dos scripts |
| `analyzeHeadless.console.log` | stdout/stderr do processo |

**Cross-check automático:** `gba_rom_header.py <rom> --compare gba_prepare_pre.json`
compara 11 campos do cabeçalho entre as duas implementações (Python e Java) e
exige `language_id` contendo `v4t`. Se as duas discordarem, o import falha —
é o teste que pega erro de extensão de sinal, soma de complemento ou offset.

---

## 6. Opções do importador

| Opção | Para quê |
|---|---|
| `--no-analysis` | importa e roda scripts sem auto-análise (segundos, útil para fumaça) |
| `--mirrors` | adiciona os blocos `0x0A/0x0C/0x0E` |
| `--reuse` | reabre o programa existente (`-process`) sem reimportar |
| `--timeout SEG` | `-analysisTimeoutPerFile` (padrão 1800) |
| `--max-runtime SEG` | mata o processo inteiro depois de SEG |
| `--project-dir` / `--project-name` | onde e com que nome criar o projeto |
| `--evidence DIR` | onde gravar JSONs/logs |
| `--allow-invalid-header` | segue mesmo com cabeçalho inválido (ROM hack/trim) |
| `--dry-run` | mostra o comando exato, não executa |
| `--self-test` | valida ferramentas e roda o pipeline na ROM sintética |
| `--keep-temp` | mantém o projeto temporário do self-test |

Códigos de saída: `0` ok · `1` falhou · `2` uso · `3` pré-requisitos ausentes.

---

## 7. Depois do import (uso prático)

1. **GUI:** `"$GHIDRA_INSTALL_DIR/ghidraRun"` → abra o projeto
   `gba_<sha8>` (o script imprime o caminho).
2. **Navegue pelas âncoras:** `gBagSlots_slot0`, `SetGpuReg`,
   `gba_entry_arm`, `gba_entry_thumb_guess`.
3. **REFs para EWRAM:** com os blocos criados, `ldr r0, =0x020258B8` aparece
   como referência para `gBagSlots_slot0` (antes ficaria “sem bloco”).
4. **Scripts úteis já inclusos no Ghidra:** `FindPotentialDecompilerProblems`,
   `CreateStructure`, `CompareFunctionSizes`.
5. **Volte ao REA** para perguntas pontuais depois de ter o programa:
   a CLI do REA trabalha sobre o binário (lane raw), não sobre o projeto Ghidra.

---

## 8. Limites conhecidos e honestidade

- **Thumb na ROM inteira não sai "de graça".** O seed cobre a entrada; o resto
  aparece quando a auto-análise segue `bx`/`blx` — em jogos grandes, parte do
  código Thumb pode continuar como dados até você marcar manualmente.
- **Auto-análise de 16 MB é pesada** (RAM/tempo). Se estourar memória, aumente
  `-Xmx` no `analyzeHeadless` ou rode com `--no-analysis` e analise funções
  específicas.
- **`0x03003118` é hipótese** — o próprio HANDOFF registra que esse espelho de
  teclas zera em certas cenas. O rótulo diz isso no nome.
- **`--mirrors` não é memória física**; use só se precisar seguir ponteiros
  espelhados.
- **Este pipeline não foi executado neste sandbox** por falta de JDK (ver
  `docs/REA_GHIDRA.md` §7). A validação aqui foi: sintaxe (tree-sitter/`bash -n`/
  shellcheck), APIs conferidas no código-fonte oficial da tag 12.1.4 e opções
  conferidas no README da própria instalação. A execução real roda no CI
  (`.github/workflows/re-tools.yml`) e na sua máquina.

---

## 9. Troubleshooting

| Sintoma | Causa | Correção |
|---|---|---|
| `pré-requisito ausente: JDK completo` | `JAVA_HOME` aponta para JRE ou está vazio | `bash scripts/setup_re_tools.sh` |
| `linguagem ARM:LE:32:v4t não existe` | instalação Ghidra sem o módulo ARM | reinstale o Ghidra oficial |
| `cabeçalho inválido` | ROM aparada, hack, ou arquivo errado | confira `reports/ghidra/rom_header.json`; use `--allow-invalid-header` se intencional |
| `ERROR: Unable to prompt user for JDK path` | headless chamado sem TTY e sem JDK | instale o JDK 21 |
| `program already exists` | rodou sem `--overwrite`/`--reuse` | use `--reuse` ou apague o projeto |
| análise não termina | ROM grande + pouca RAM | `--timeout`, `--no-analysis`, ou `-Xmx` maior |
| `cross-check` divergiu | implementações Python/Java discordam | abra issue: é bug real, não ruído |

---

## 10. Arquivos

| Arquivo | Papel |
|---|---|
| `scripts/ghidra_import_gba.sh` | orquestrador (pré-checagem, comando, verificações) |
| `scripts/ghidra_scripts/GbaPrepareProgram.java` | pre/post-script: mapa, cabeçalho, rótulos, seeds |
| `scripts/gba_rom_header.py` | leitor de cabeçalho independente + `--compare` + `--self-test` |
| `scripts/make_synthetic_arm_image.py` | blob ARM e **ROM GBA sintética** (`--gba-rom`) para testes |
| `docs/REA_GHIDRA.md` | instalação do stack (REA + Ghidra + JDK) |
