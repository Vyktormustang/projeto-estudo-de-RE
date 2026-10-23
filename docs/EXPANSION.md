# Todos os Pokémon até a geração atual — como isso é feito

> **Resposta curta:** não é um patch na sua ROM. É um **jogo novo compilado a
> partir do código-fonte** (decomp) usando a **pokeemerald-expansion**. Ela já
> contém Gen 1–9 e todas as mecânicas modernas; o que falta é compilar.
>
> **Status em 2026-10-22:** a expansão foi baixada e analisada aqui; o build
> **não terminou** neste ambiente (falta o toolchain ARM oficial — o sandbox só
> tem acesso a GitHub/PyPI/npm). O passo a passo do Windows abaixo é o caminho
> confiável e leva ~20 min.

---

## 1. O que a expansion já entrega (verificado no código, v1.17.2)

| Recurso | Onde está | Valor |
|---|---|---|
| Pokémon Gen 1–9 (1025) | `include/config/species_enabled.h` | `P_GEN_1..9_POKEMON` = **TRUE** |
| Tipo Fada | tabela de tipos do decomp | nativo |
| Split físico/especial | `include/config/battle.h` | `B_PHYSICAL_SPECIAL_SPLIT` |
| Mega Evolução | `include/config/battle.h` | `B_MEGA_EVO_*` |
| Z-Moves | `include/config/battle.h` | `B_SHOW_USELESS_Z_MOVE_INFO` |
| Dynamax/Gigantamax | `include/config/battle.h` | `B_FLAG_DYNAMAX_BATTLE` |
| Terastallization | `include/config/battle.h` | `B_FLAG_TERA_ORB_*` |
| Habilidades, itens, natures, golpes | `src/data/*` | até Gen 9 |

O repositório é **`rh-hideout/pokeemerald-expansion`** (≈ 47 MB de código, build
gera um `.gba` de 32 MB).

---

## 2. O que se perde

| Item | Situação |
|---|---|
| Tradução PT-BR do FireRed | **perdida** (a expansion é Emerald, em inglês) |
| Mapa/história de Kanto | **perdida** (é Hoenn) |
| O mod da mochila v4 | fica no FireRed PT-BR, intacto (projeto separado) |

A tradução é a **fase 2** (seção 5).

---

## 3. Build no Windows (caminho recomendado)

### 3.1 Instalar as ferramentas (uma vez)

1. **devkitPro** — instalador oficial: <https://github.com/devkitPro/installer/releases>
   (escolha *GBA Development*).
2. **MSYS2** (vem com o devkitPro) — abra o terminal **MSYS2 MinGW 64-bit** e rode:

```bash
pacman -Syu
pacman -S git make python gcc
```

3. Confirme:

```bash
arm-none-eabi-gcc --version
make --version
```

### 3.2 Baixar e compilar

```bash
git clone --depth 1 https://github.com/rh-hideout/pokeemerald-expansion.git
cd pokeemerald-expansion
make modern -j$(nproc)
```

Saída: `pokeemerald.gba` (32 MB) na raiz do repositório.

> `make modern` usa o `arm-none-eabi-gcc` do devkitPro. **Não** use `make`
> sozinho: ele exige o `agbcc` (compilador antigo, só para builds "matching").

### 3.3 Primeira execução

1. Abra `pokeemerald.gba` no **mGBA**.
2. Novo jogo → escolha o inicial → o jogo roda Hoenn normalmente, mas com os
   1025 Pokémon, golpes e mecânicas novas.
3. Para **encher a mochila / pegar qualquer Pokémon**, use o menu de debug
   (seção 3.4).

### 3.4 Menu de debug (pegar qualquer Pokémon/item)

O menu de debug é compilado junto quando o build é feito com `DEBUG=1`:

```bash
make modern -j$(nproc) DEBUG=1
```

No jogo: abra o menu inicial e pressione **SELECT** → *Debug Menu* → você pode
dar qualquer Pokémon (Gen 1–9), item, golpe, dinheiro, etc.

Para deixar isso permanente no código-fonte, edite
`include/config/debug.h` e ponha `DEBUG_OVERWORLD_MENU` como `TRUE`.

---

## 4. Build no Linux/sandbox (o que foi tentado aqui)

Sem acesso à internet além de GitHub/PyPI/npm, o toolchain oficial não pôde ser
baixado (os *release assets* do GitHub são bloqueados neste ambiente). A
alternativa usada foi o **Zig** (`pip install ziglang`), que traz clang + lld.

O que foi montado (`scripts/expansion/toolchain_zig/`):

| Peça | Papel |
|---|---|
| `_common.py` | normaliza flags do GCC-ARM para o clang; `-fpack-struct=4` e `-fshort-enums` (equivalem ao `-mabi=apcs-gnu` do GCC) |
| `arm-none-eabi-gcc` / `arm-fake-cc1` | compilador C (clang) |
| `arm-none-eabi-as` | assembler com autocorreção das diferenças GNU→LLVM |
| `arm-none-eabi-cpp`, `arm-none-eabi-ld`, `pkg-config` | preprocessador, linker, libpng |

**Até onde chegou:** ~95% dos objetos compilados (todo o C, gráficos, mapas,
`sound/`). **Onde parou:** arquivos `.s` que usam macros do GNU `as`
(`Call`/`CreatePinkHearts` em `data/battle_anim_scripts.s`) que o assembler do
LLVM não expande do mesmo jeito. Não é um problema de configuração: é uma
limitação do assembler alternativo.

Conclusão: **use `arm-none-eabi-*` de verdade** (devkitPro). O Zig serve apenas
como quebra-galho e não fecha o build.

---

## 5. Fase 2 — tradução PT-BR

Não existe tradução PT-BR pronta para a expansion. O caminho realista:

1. Obter um patch de tradução PT-BR de **Emerald** (projeto de fã, aplicável em
   ROM limpa).
2. Extrair os textos do ROM traduzido (`scripts/gba_poketext.py` do projeto já
   faz leitura; seria preciso o inverso: gerar os `.inc`/`.h` de texto).
3. Substituir os arquivos de texto da expansion (`data/text/*.inc`,
   `src/data/*.h`) pelos equivalentes traduzidos.
4. Recompilar e corrigir os transbordamentos de largura de linha.

É trabalho de semanas, não de uma sessão — e é o único caminho que preserva
"todos os Pokémon" **e** PT-BR.

---

## 6. Limites e legalidade

- **Não distribuímos ROM nem assets.** O repositório do projeto guarda apenas
  scripts e documentação; o `.gba` gerado fica na sua máquina (`rom/` e
  `rom_mod/` estão no `.gitignore`).
- A expansion é um projeto de fã sobre código decompilado; os gráficos e nomes
  são propriedade da Nintendo/Game Freak/The Pokémon Company. Uso pessoal.
- O build produz 32 MB — o máximo do cartucho GBA; funciona em mGBA, MyBoy
  (Android) e flashcarts.

---

## 7. Referências

- `rh-hideout/pokeemerald-expansion` (v1.17.2, branch `master`)
- `pret/pokeemerald` (base decompilada)
- Documentação de configuração: `include/config/*.h` no próprio repositório
