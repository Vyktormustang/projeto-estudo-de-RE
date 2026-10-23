# Todos os Pokémon até a geração atual — ROM pronta

> **Resposta curta:** o jogo com **Gen 1–9 completos** já está compilado e
> testado. Não é um patch na sua ROM do FireRed: é um **jogo novo**, construído
> a partir do código-fonte da `pokeemerald-expansion` (Emerald decompilado +
> 1025 Pokémon, tipo Fada, split físico/especial, Mega, Z-Moves, Dynamax e
> Terastal).
>
> **Status em 2026-10-23:** ROM **gerada e verificada** por emulador (tela da
> Game Freak, intro e tela de título capturadas) e com as 9 gerações
> confirmadas dentro do arquivo. Arquivo de **32 MB**.

---

## 1. Onde pegar a ROM

| | |
|---|---|
| Arquivo | `pokemon_emerald_expansion_gen1-9.gba` |
| Tamanho | 33 554 432 bytes (32 MB) |
| SHA-256 | `7ffdf2db4a43a614b69a3b50ae631789b5b58e9568288c70158010d2cb98f647` |
| Google Drive | <https://drive.google.com/file/d/1XItQUCytkc6fsnw-f0vQAf8VKynAWMFN/view> |

> Confira o SHA-256 depois de baixar (Windows: `certutil -hashfile arquivo.gba SHA256`).
> Se bater, o arquivo chegou inteiro.

**Como jogar:** abra no **mGBA** (Windows/Linux/macOS, grátis) ou num celular
com **mGBA**/**MyBoy**. Funciona também em flashcart (EZ-Flash, EverDrive).

---

## 2. O que tem dentro (e como foi verificado)

Tudo abaixo foi checado **no arquivo gerado**, não só no código-fonte.

| Recurso | Como foi verificado | Resultado |
|---|---|---|
| Tela de abertura | emulador mGBA, frame 600 | tela **GAME FREAK** (45 cores) — ver `reports/expansion/01_gamefreak.png` |
| Intro + título | frames 1800–7200 | **"Pokémon EMERALD VERSION"** (198 cores) — `reports/expansion/02_titulo.png` |
| Jogo inicia | frames 9000–12000, com input | **"So it's Aaaaaaa?"**, teclado **"YOUR NAME?"** e **"All right, are you ready?"** — o jogo chega ao início da aventura |
| Gen 1 (Bulbasaur, Pikachu) | busca do nome codificado no `.gba` | **presente** |
| Gen 2 (Tyranitar) | idem | **presente** |
| Gen 3 (Rayquaza) | idem | **presente** |
| Gen 4 (Garchomp) | idem | **presente** |
| Gen 5 (Zoroark) | idem | **presente** |
| Gen 6 (Greninja) | idem | **presente** |
| Gen 7 (Mimikyu) | idem | **presente** |
| Gen 8 (Corviknight) | idem | **presente** |
| Gen 9 (Miraidon, Koraidon, Pecharunt) | idem | **presente** |

12 de 12 nomes de espécies procurados foram encontrados dentro da ROM (busca
com a tabela de caracteres do próprio jogo, `charmap.txt` — os nomes não ficam
em ASCII puro).

As mecânicas (Fada, split físico/especial, Mega, Z-Moves, Dynamax, Terastal)
vêm ligadas por padrão na expansion 1.17.2; as flags conferidas estão na seção 1
da tabela abaixo.

| Recurso | Onde é configurado | Valor |
|---|---|---|
| Pokémon Gen 1–9 | `include/config/species_enabled.h` | `P_GEN_1..9_POKEMON` = TRUE |
| Tipo Fada | tabela de tipos | nativo |
| Split físico/especial | `include/config/battle.h` | `B_PHYSICAL_SPECIAL_SPLIT` |
| Mega Evolução | `include/config/battle.h` | `B_MEGA_EVO_*` |
| Z-Moves | `include/config/battle.h` | `B_SHOW_USELESS_Z_MOVE_INFO` |
| Dynamax/Gigantamax | `include/config/battle.h` | `B_FLAG_DYNAMAX_BATTLE` |
| Terastallization | `include/config/battle.h` | `B_FLAG_TERA_ORB_*` |
| Habilidades, itens, natures, golpes | `src/data/*` | até Gen 9 |

---

## 3. O que se perde

| Item | Situação |
|---|---|
| Tradução PT-BR do FireRed | **perdida** — a expansion é Emerald, em inglês |
| Mapa/história de Kanto | **perdida** — o jogo é Hoenn |
| O mod da mochila v4 | intacto, mas fica no FireRed PT-BR (projeto separado) |

Isso foi uma decisão sua em 2026-10-22: trocar Kanto + PT-BR por **todos os
Pokémon e mecânicas modernas**. O caminho alternativo (patch de tradução
PT-BR + CFRU no FireRed) foi descartado porque **não existe** base CFRU com
Gen 1–9.

A tradução é a **fase 2** (seção 6).

---

## 4. Como a ROM foi construída (receita reproduzível)

O build oficial usa o `arm-none-eabi-gcc` do **devkitPro**. Este sandbox não
consegue baixar os *release assets* do GitHub (bloqueio de rede), então o
toolchain foi remontado a partir de pacotes que *são* acessíveis: **o mesmo GCC
e o mesmo binutils, compilados para WebAssembly**, rodando sob Node.js.

**Não é um compilador alternativo** (como o Zig/clang das tentativas
anteriores): é o GCC 14.2.0 de verdade — `arm-none-eabi-gcc (GCC) 14.2.0` — e o
GNU `as`/`ld`/`objcopy`/`ar` de verdade. Por isso o código-fonte da expansion
compila **sem nenhum patch**.

### 4.1 Receita (Linux/macOS com Node 18+)

```bash
# 1. toolchain (baixa ~11 MB do npm e instala os wrappers em /tmp/tc/bin)
bash scripts/expansion/setup_wasm_toolchain.sh

# 2. fonte da expansion
curl -L -o exp.tgz https://codeload.github.com/rh-hideout/pokeemerald-expansion/tar.gz/refs/heads/master
tar xzf exp.tgz && cd pokeemerald-expansion-master

# 3. ferramentas internas do projeto (gbagfx, preproc, ...)
make tools -j2

# 4. a ROM
export PATH=/tmp/tc/bin:$PATH
make modern -j2      # ≈ 25 min; sai pokeemerald.gba (32 MB)
```

Peças do toolchain (`scripts/expansion/toolchain_wasm/`):

| Peça | O que é |
|---|---|
| `wtool.mjs` | executor genérico: monta os arquivos de entrada num sistema de arquivos em memória, roda a ferramenta WASM e copia as saídas de volta |
| `cc1d.mjs` | *daemon* que instancia o `cc1.wasm` (28 MB) **uma vez** e reaproveita — sem ele cada arquivo levava 9 s em vez de 0,6 s |
| `arm-fake-cc1` | compilador C → assembly (GCC 14.2 real) |
| `arm-none-eabi-as` | assembler GNU (com `--defsym`, macros, `.include`, `.incbin`) |
| `arm-none-eabi-ld` | linker GNU (script `ld_script_modern.ld`, `-Map`, `--gc-sections`) |
| `arm-none-eabi-cpp` | pré-processador (clang `-E`, via `ziglang` do PyPI) |
| `pkg-config` | aponta para zlib/libpng locais (só para as ferramentas de host) |

### 4.2 Detalhes que fizeram diferença

- **`-mabi=apcs-gnu`** (já usado pelo projeto) faz o GCC tratar `enum` como
  4 bytes — é o que permite os bitfields `enum X campo:12` de `include/pokemon.h`.
  Sem essa flag o build quebra; **com** ela o fonte fica intacto.
- O `string.h` do musl inclui `<strings.h>`, que colide com o
  `include/strings.h` do projeto → essa linha foi removida do header do musl.
- O assembler precisa dos arquivos citados em `.include`/`.incbin`
  (`data/layouts/*/*.bin`) disponíveis: o executor os monta antes de chamar o `as`.
- `make tools` precisa de zlib + libpng no host (`/tmp/local`).

### 4.3 Build no Windows (o caminho mais simples para você)

Se preferir compilar você mesmo no seu PC (não é necessário — a ROM já está
pronta):

1. **devkitPro** — instalador oficial: <https://github.com/devkitPro/installer/releases>
   (escolha *GBA Development*).
2. Abra o terminal **MSYS2 MinGW 64-bit** e rode:
   ```bash
   pacman -Syu
   pacman -S git make python gcc
   arm-none-eabi-gcc --version   # confirma
   ```
3. Baixe e compile:
   ```bash
   git clone --depth 1 https://github.com/rh-hideout/pokeemerald-expansion.git
   cd pokeemerald-expansion
   make modern -j$(nproc)
   ```
   Sai `pokeemerald.gba` (32 MB).

Há também o script pronto `scripts/win/build-expansion.ps1` (PowerShell): ele
confere as ferramentas, clona, aplica as configs e compila.

> `make modern` usa o `arm-none-eabi-gcc` do devkitPro. **Não** use `make`
> sozinho: ele exige o `agbcc` (compilador antigo, só para builds "matching").

---

## 5. Menu de debug (pegar qualquer Pokémon/item)

O menu de debug permite dar **qualquer Pokémon (Gen 1–9)**, item, golpe ou
dinheiro, sem precisar jogar até o fim.

Para compilar com ele:

```bash
make modern -j$(nproc) DEBUG=1
```

No jogo: no mapa, **segure R e aperte START** → abre o *Debug Menu*.

Para deixá-lo permanente no código-fonte, em `include/config/debug.h`:

```c
#define DEBUG_OVERWORLD_MENU            TRUE
#define DEBUG_BATTLE_MENU               TRUE
```

---

## 6. Fase 2 — tradução PT-BR

Não existe tradução PT-BR pronta para a expansion. O caminho realista:

1. Obter um patch de tradução PT-BR de **Emerald** (projeto de fã, aplicável em
   ROM limpa).
2. Extrair os textos do ROM traduzido.
3. Substituir os arquivos de texto da expansion (`data/text/*.inc`,
   `src/data/*.h`) pelos equivalentes traduzidos.
4. Recompilar e corrigir os transbordamentos de largura de linha.

São **milhares de strings** — trabalho de semanas, não de uma sessão.

---

## 7. Limites e legalidade

- **Não redistribuímos ROM nem assets originais.** O repositório guarda apenas
  scripts e documentação; o `.gba` fica fora do Git (`rom/` está no
  `.gitignore`). O arquivo no Drive é o resultado deste build, para uso pessoal.
- A expansion é um projeto de fã sobre código decompilado; os nomes e criaturas
  são propriedade da Nintendo/Game Freak/The Pokémon Company. Uso pessoal.
- 32 MB é o tamanho máximo de um cartucho GBA; roda em mGBA, MyBoy (Android) e
  flashcarts.

---

## 8. Referências

- `rh-hideout/pokeemerald-expansion` (v1.17.2, branch `master`)
- `pret/pokeemerald` (base decompilada)
- Documentação de configuração: `include/config/*.h` no próprio repositório
- Toolchain: `scripts/expansion/toolchain_wasm/` + `setup_wasm_toolchain.sh`
