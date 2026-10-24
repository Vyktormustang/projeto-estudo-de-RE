#!/usr/bin/env python3
"""E7, passo 0: a Pokédex nacional existe desde o início e cabe em 4 dígitos.

Por que isso é necessário
-------------------------
O FireRed vanilla tem 386 espécies e a **Pokédex nacional só é entregue depois
da Elite 4** (`VAR_NATIONAL_DEX == 0x6258` + `FLAG_SYS_NATIONAL_DEX` +
`nationalMagic == 0xB9`). Enquanto ela não chega:

- a Pokédex lista **151** entradas (só Kanto) e não tem como registrar as
  espécies 387-1025: elas são capturadas e **não entram** na dex;
- `SpeciesToPokedexNum()` devolve `0xFFFF` para espécie > 151, e a ficha mostra
  `No ???` (foi assim que o Turtwig da E6 apareceu);
- `MonCanEvolve()` (menu do time) **recusa a pedra de evolução** de qualquer
  espécie fora de Kanto;
- `DexScreen_CanShowMonInDex()` esconde a espécie no dex.

Num jogo que tem as 9 gerações, isso não é "detalhe de progressão": é a
Pokedex inteira ficando inacessível. A troca mínima é fazer
`IsNationalPokedexEnabled()` responder `TRUE` sempre — **uma função, um
arquivo**. O script que dá a dex do Oak continua chamando
`EnableNationalPokedex()`, que passa a não ter efeito prático (e nenhum efeito
colateral).

Se um dia a progressão vanilla for desejada de volta, é só reverter este patch:
nada mais no motor depende dele.

Por que também os 4 dígitos
---------------------------
Metade do código de UI do FireRed formata o número da dex em **3 dígitos**
(`CHAR_0 + num/100`, `ConvertIntToDecimalStringN(..., 3)`). De 1000 em diante o
número sai truncado (`1025` -> `102`), e a contagem "vistos/donos" do menu
inicial e da dex estoura o buffer. A E1 já tratou o número da **entrada** da
dex (`DexScreen_PrintNum3LeadingZeroes`); faltavam os contadores e a ficha.

O que muda
----------
| arquivo                          | mudança                                          |
|----------------------------------|--------------------------------------------------|
| `src/event_data.c`               | `IsNationalPokedexEnabled()` -> sempre `TRUE`    |
| `src/pokemon_summary_screen.c`   | número da dex: 4 dígitos quando >= 1000          |
| `src/pokedex_screen.c`           | contador vistos/donos: 4 dígitos quando >= 1000  |
| `src/main_menu.c`                | contagem da dex no "CONTINUE": 4 dígitos >= 1000 |

Em todos os casos, até 999 o desenho é **idêntico ao vanilla** — a mudança só
aparece quando o número realmente precisa de 4 casas.

Uso
---
    python3 scripts/firered/apply_e7_port.py --self-test
    python3 scripts/firered/apply_e7_port.py --pokefirered /tmp/pokefirered
    python3 scripts/firered/apply_e7_port.py --pokefirered /tmp/pokefirered --check
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

MARCA = "E7: Pokedex nacional e 4 digitos"

# --------------------------------------------------------------------------- #
# 1. event_data.c — a nacional vale desde o início
# --------------------------------------------------------------------------- #
EVENT_DATA_ANTIGO = """bool32 IsNationalPokedexEnabled(void)
{
    if (gSaveBlock2Ptr->pokedex.nationalMagic == 0xB9
            && VarGet(VAR_NATIONAL_DEX) == 0x6258
            && FlagGet(FLAG_SYS_NATIONAL_DEX))
        return TRUE;

    return FALSE;
}"""

EVENT_DATA_NOVO = """bool32 IsNationalPokedexEnabled(void)
{
    // E7: a Pokedex nacional vale desde o inicio do jogo.
    // O vanilla so a liga depois da Elite 4 (nationalMagic 0xB9 + VAR 0x6258 +
    // FLAG_SYS_NATIONAL_DEX). Neste jogo as 1025 especies existem desde a
    // primeira rota, e sem a nacional: a dex lista so 151, especie > 151 vira
    // "No ???" na ficha (SpeciesToPokedexNum devolve 0xFFFF), a pedra de
    // evolucao e recusada (MonCanEvolve) e a especie nao e registrada ao ser
    // capturada. EnableNationalPokedex() continua existindo e nao faz mal.
    return TRUE;
}"""

# --------------------------------------------------------------------------- #
# 2. pokemon_summary_screen.c — número da dex com 4 dígitos
# --------------------------------------------------------------------------- #
SUMMARY_ANTIGO = """    else
        ConvertIntToDecimalStringN(sMonSummaryScreen->summary.dexNumStrBuf, dexNum, STR_CONV_MODE_LEADING_ZEROS, 3);"""

SUMMARY_NOVO = """    else
        // E7: a dex vai ate 1025. Ate 999 fica com 3 digitos (igual ao vanilla);
        // de 1000 em diante precisa de 4, senao "1025" sai truncado.
        ConvertIntToDecimalStringN(sMonSummaryScreen->summary.dexNumStrBuf, dexNum,
                                   STR_CONV_MODE_LEADING_ZEROS, dexNum >= 1000 ? 4 : 3);"""

# --------------------------------------------------------------------------- #
# 3. pokedex_screen.c — contadores vistos/donos
# --------------------------------------------------------------------------- #
DEXSCREEN_ANTIGO = """static void DexScreen_PrintNum3RightAlign(u8 windowId, u8 fontId, u16 num, u8 x, u8 y, u8 colorIdx)
{
    u8 buff[4];
    int i;
    buff[0] = (num / 100) + CHAR_0;
    buff[1] = ((num %= 100) / 10) + CHAR_0;
    buff[2] = (num % 10) + CHAR_0;
    buff[3] = EOS;
    for (i = 0; i < 3; i++)
    {
        if (buff[i] != CHAR_0)
            break;
        buff[i] = CHAR_SPACE;
    }"""

DEXSCREEN_NOVO = """static void DexScreen_PrintNum3RightAlign(u8 windowId, u8 fontId, u16 num, u8 x, u8 y, u8 colorIdx)
{
    // E7: o contador de vistos/donos vai ate 1025. Monta sempre 4 digitos e
    // descarta o milhar quando ele e zero — o desenho ate 999 fica igual ao
    // vanilla (3 caracteres, zeros a esquerda como espaco, alinhado a direita).
    u8 buff[5];
    int i;

    buff[0] = ((num / 1000) % 10) + CHAR_0;
    buff[1] = ((num / 100) % 10) + CHAR_0;
    buff[2] = ((num / 10) % 10) + CHAR_0;
    buff[3] = (num % 10) + CHAR_0;
    buff[4] = EOS;
    if (num >= 1000)
    {
        x -= 6;                         // recua 1 caractere: continua a direita
    }
    else
    {
        for (i = 0; i < 4; i++)
            buff[i] = buff[i + 1];      // descarta o milhar
        for (i = 0; i < 3; i++)
        {
            if (buff[i] != CHAR_0)
                break;
            buff[i] = CHAR_SPACE;
        }
    }"""

# --------------------------------------------------------------------------- #
# 4. main_menu.c — contagem no "CONTINUE"
# --------------------------------------------------------------------------- #
MAINMENU_ANTIGO = """        ptr = ConvertIntToDecimalStringN(strbuf, dexcount, STR_CONV_MODE_LEFT_ALIGN, 3);"""

MAINMENU_NOVO = """        // E7: a contagem da dex vai ate 1025
        ptr = ConvertIntToDecimalStringN(strbuf, dexcount, STR_CONV_MODE_LEFT_ALIGN,
                                         dexcount >= 1000 ? 4 : 3);"""

MUDANCAS: list[tuple[str, str, str, int]] = [
    ("src/event_data.c", EVENT_DATA_ANTIGO, EVENT_DATA_NOVO, 1),
    ("src/pokemon_summary_screen.c", SUMMARY_ANTIGO, SUMMARY_NOVO, 1),
    ("src/pokedex_screen.c", DEXSCREEN_ANTIGO, DEXSCREEN_NOVO, 1),
    ("src/main_menu.c", MAINMENU_ANTIGO, MAINMENU_NOVO, 1),
]


def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8", errors="surrogateescape")


def _gravar(caminho: Path, texto: str) -> None:
    caminho.write_text(texto, encoding="utf-8", errors="surrogateescape")


def ja_aplicado(pf: Path) -> bool:
    return MARCA in _ler(pf / "src/event_data.c")


def faltando(pf: Path) -> list[str]:
    pendentes = []
    for arquivo, antigo, _, vezes in MUDANCAS:
        if _ler(pf / arquivo).count(antigo) == vezes:
            pendentes.append(f"{arquivo}: falta a mudanca ({antigo.splitlines()[0].strip()!r})")
    return pendentes


def quantidades_erradas(pf: Path) -> list[str]:
    erros = []
    for arquivo, antigo, _, vezes in MUDANCAS:
        achados = _ler(pf / arquivo).count(antigo)
        if 0 < achados != vezes:
            erros.append(f"{arquivo}: esperava {vezes}x, achei {achados}")
    return erros


def aplicar(pf: Path) -> list[str]:
    feitos: list[str] = []
    por_arquivo: dict[str, list[tuple[str, str, int]]] = {}
    for arquivo, antigo, novo, vezes in MUDANCAS:
        por_arquivo.setdefault(arquivo, []).append((antigo, novo, vezes))

    for arquivo, itens in sorted(por_arquivo.items()):
        caminho = pf / arquivo
        texto = _ler(caminho)
        marcado = f"// {MARCA}" in texto
        quantas = 0
        for antigo, novo, vezes in itens:
            achados = texto.count(antigo)
            if achados == 0:
                continue                       # essa já foi
            if achados != vezes:
                raise SystemExit(f"{arquivo}: esperava {vezes} ocorrencia(s), achei {achados}")
            texto = texto.replace(antigo, novo)
            quantas += 1
        if quantas:
            if not marcado:
                texto += f"\n// {MARCA}\n"
            _gravar(caminho, texto)
            feitos.append(f"{arquivo} ({quantas})")
    return feitos


def conferir(pf: Path) -> list[str]:
    erros: list[str] = []
    texto = _ler(pf / "src/event_data.c")
    if EVENT_DATA_ANTIGO in texto:
        erros.append("event_data.c: IsNationalPokedexEnabled ainda exige a flag do Oak")
    if "return TRUE;" not in EVENT_DATA_NOVO or EVENT_DATA_NOVO not in texto:
        erros.append("event_data.c: IsNationalPokedexEnabled nao foi reescrito")
    for arquivo, _, novo, _ in MUDANCAS[1:]:
        if novo not in _ler(pf / arquivo):
            erros.append(f"{arquivo}: a mudanca de 4 digitos nao esta aplicada")
    # o corpo antigo do contador nao pode ter sobrado
    if "u8 buff[4];\n    int i;\n    buff[0] = (num / 100) + CHAR_0;" in _ler(pf / "src/pokedex_screen.c"):
        erros.append("pokedex_screen.c: contador ainda monta 3 digitos")
    return erros


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
def self_test() -> int:
    import tempfile

    casos = ok = 0

    def checa(nome: str, cond: bool):
        nonlocal casos, ok
        casos += 1
        if cond:
            ok += 1
            print(f"  ok: {nome}")
        else:
            print(f"  FALHA: {nome}")

    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        for arquivo, antigo, _, vezes in MUDANCAS:
            caminho = raiz / arquivo
            caminho.parent.mkdir(parents=True, exist_ok=True)
            _gravar(caminho, _ler(caminho) + antigo * vezes + "\n" if caminho.exists()
                    else antigo * vezes + "\n")

        checa("antes: nao aplicado", not ja_aplicado(raiz))
        checa("antes: faltando lista tudo", len(faltando(raiz)) == len(MUDANCAS))
        checa("antes: conferir acusa", conferir(raiz) != [])

        feitos = aplicar(raiz)
        checa("aplicar mexe nos 4 arquivos", len(feitos) == len({m[0] for m in MUDANCAS}))
        checa("depois: aplicado", ja_aplicado(raiz))
        checa("depois: nada faltando", not faltando(raiz))
        checa("depois: conferir passa", conferir(raiz) == [])
        checa("idempotente (2a passada nao mexe)", aplicar(raiz) == [])

        texto = _ler(raiz / "src/event_data.c")
        checa("national dex sempre TRUE",
              "return TRUE;" in texto and "pokedex.nationalMagic == 0xB9" not in texto)
        checa("summary usa 4 digitos so a partir de 1000",
              "dexNum >= 1000 ? 4 : 3" in _ler(raiz / "src/pokemon_summary_screen.c"))
        checa("contador da dex chega a 1025",
              "num >= 1000" in _ler(raiz / "src/pokedex_screen.c"))
        checa("menu inicial chega a 1025",
              "dexcount >= 1000 ? 4 : 3" in _ler(raiz / "src/main_menu.c"))

        # guarda de quantidade: duas cópias do original têm de abortar
        with tempfile.TemporaryDirectory() as d2:
            r2 = Path(d2)
            for arquivo, antigo, _, vezes in MUDANCAS:
                caminho = r2 / arquivo
                caminho.parent.mkdir(parents=True, exist_ok=True)
                _gravar(caminho, antigo * vezes + "\n")
            cam = r2 / "src/main_menu.c"
            _gravar(cam, _ler(cam) + MAINMENU_ANTIGO + "\n")
            try:
                aplicar(r2)
                checa("quantidade errada aborta", False)
            except SystemExit:
                checa("quantidade errada aborta", True)

        # arquivo sem o trecho: não inventa, só não mexe
        with tempfile.TemporaryDirectory() as d3:
            r3 = Path(d3)
            for arquivo, _, _, _ in MUDANCAS:
                caminho = r3 / arquivo
                caminho.parent.mkdir(parents=True, exist_ok=True)
                _gravar(caminho, "// nada a ver\n")
            checa("arquivo sem o trecho nao e alterado", aplicar(r3) == [])

    print(f"\n{ok}/{casos} casos ok")
    return 0 if ok == casos else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    pf = Path(a.pokefirered)
    if a.check:
        if not ja_aplicado(pf):
            print("nada aplicado")
            return 1
        erros = conferir(pf) + faltando(pf) + quantidades_erradas(pf)
        if erros:
            for e in erros:
                print("  - " + e)
            return 1
        print("ok: Pokedex nacional sempre ativa e numeros com 4 digitos")
        return 0

    feitos = aplicar(pf)
    if not feitos:
        print("nada a fazer: ja aplicado")
        return 0
    print("aplicado: " + "; ".join(feitos))
    erros = conferir(pf)
    if erros:
        for e in erros:
            print("  - " + e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
