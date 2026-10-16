#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_ident.py — FASE 1: triagem/identificação de ROM de Game Boy Advance
=======================================================================

OBJETIVO
    Gerar um relatório técnico inicial (JSON + TSVs + resumo em texto) de uma
    ROM de GBA: hashes, parse do cabeçalho (referência: GBATEK), distribuição
    de bytes, entropia por bloco, strings ASCII e padrões de bytes que SUGEREM
    código (pares BL de Thumb / BL de ARM) ou dados.

PRÉ-REQUISITOS
    Python 3.9+. Somente biblioteca padrão (capstone NÃO é exigido neste script).

ENTRADAS
    Caminho de uma ROM bruta (.gba/.agb/.bin), não compactada.

SAÍDAS (em --outdir, padrão: ../reports relativo ao script)
    <nome>_ident.json    — relatório completo legível por máquina
    <nome>_strings.tsv   — strings ASCII extraídas: offset_hex<TAB>texto
    <nome>_regioes.tsv   — classificação por bloco: offset_hex, classe, entropia
    logs/gba_ident_runs.jsonl — log append-only de execuções (UTC, argv, sha256, duração)
    Com --update-inventory: atualiza inventory.json (manifesto do projeto).

USO
    python3 gba_ident.py ROM.gba [-o reports] [--block-size 65536] [--min-str 6]
                                 [--update-inventory ../inventory.json] [-v]
    python3 gba_ident.py --self-test [--keep-fixture]

SELF-TEST
    Constrói uma ROM SINTÉTICA rotulada (tests/fixture_sintetico.gba) com
    cabeçalho válido, bloco de padrão BL-Thumb denso, bloco de alta entropia
    determinístico (seed fixa) e bloco de preenchimento; executa a análise e
    verifica cada item contra valores conhecidos. Exit 0 = tudo OK.
    A fixture NÃO é um jogo e NUNCA deve ser tratada como evidência sobre a ROM real.

LIMITAÇÕES DECLARADAS (conforme as regras do projeto)
    1. Campos do cabeçalho NÃO provam identidade/versão do jogo (hacks/bootlegs
       copiam ou alteram cabeçalhos). São indícios, nada mais.
    2. Strings ASCII perdem textos com codificação própria (muito comum em GBA).
    3. A classificação código/dados (entropia + padrões BL) é HEURÍSTICA:
       gera HIPÓTESES a validar na Fase 2 (desassemblado real), nunca fatos.
    4. Este script NÃO desassembla nem executa a ROM.
    5. Tabelas de categoria do game code / região baseiam-se no GBATEK e são
       marcadas como "indício"; letras não mapeadas ficam DESCONHECIDO.

CÓDIGOS DE SAÍDA
    0 ok | 1 falha no self-test | 2 erro de argumentos | 3 erro de arquivo/análise
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSAO_FERRAMENTA = "1.0.0"

# Endereço onde a ROM é mapeada no barramento do GBA (GBATEK, "GBA Memory Map")
GBA_ROM_BASE = 0x08000000

# Logo da Nintendo (156 bytes em 0x004..0x09F) — constante idêntica em toda ROM
# licenciada (referência: GBATEK, "GBA Cartridge Header"). Usada apenas para
# verificar a CONSISTÊNCIA do cabeçalho, não a legitimidade do arquivo.
NINTENDO_LOGO = bytes.fromhex(
    "24FFAE51699AA2213D84820A84E409AD"
    "11248B98C0817F21A352BE199309CE20"
    "10464A4AF82731EC58C7E83382E3CEBF"
    "85F4DF94CE4B09C194568AC01372A7FC"
    "9F844D73A3CA9A615897A327FC039876"
    "231DC7610304AE56BF38840040A70EFD"
    "FF52FE036F9530F197FBC08560D68025"
    "A963BE03014E38E2F9A234FFBB3E0344"
    "780090CB88113A9465C07C6387F03CAF"
    "D625E48B380AAC7221D4F807"
)
assert len(NINTENDO_LOGO) == 156

# Indícios (NÃO provas) derivados do 1º caractere do game code — ref. GBATEK.
GAME_CODE_CATEGORIA = {
    "A": "jogo padrão (lotes antigos, ~2001-2003)",
    "B": "jogo padrão (lotes mais novos, ~2003+)",
    "F": "Classic NES / Famicom Mini (série)",
    "K": "hardware extra: sensor de movimento/acelerômetro (ex.: Yoshi Universal Gravitation)",
    "P": "e-Reader",
    "R": "hardware extra: giroscópio/rumble (ex.: WarioWare: Twisted!)",
    "U": "hardware extra: sensor especial (ex.: Boktai — sensor solar)",
    "V": "hardware extra: rumble (ex.: Drill Dozer)",
}

# Indícios do 4º caractere do game code (letra de idioma/região) — ref. GBATEK/No-Intro.
GAME_CODE_IDIOMA = {
    "J": "Japão",
    "E": "América / Inglês",
    "P": "Europa (frequentemente multilíngue)",
    "F": "França / Francês",
    "G": "Alemanha / Alemão",
    "S": "Espanha / Espanhol",
    "I": "Itália / Italiano",
}

# Subconjunto mínimo e seguro de maker codes (não inventar tabela completa).
MAKER_CODES = {"01": "Nintendo"}


class AnalysisError(Exception):
    """Erro de entrada/análise tratado pelo main (exit 3)."""


# --------------------------------------------------------------------------- #
# Primitivas de análise
# --------------------------------------------------------------------------- #

def hashes_do_arquivo(data: bytes) -> dict:
    return {
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def entropia_shannon(bloco: bytes) -> float:
    """Entropia de Shannon em bits/byte (0.0..8.0)."""
    if not bloco:
        return 0.0
    n = len(bloco)
    ent = 0.0
    for c in Counter(bloco).values():
        p = c / n
        ent -= p * math.log2(p)
    return ent


def header_checksum(data: bytes) -> int:
    """Checksum do cabeçalho GBA: complemento sobre 0xA0..0xBC (ref. GBATEK)."""
    x = 0
    for i in range(0xA0, 0xBD):
        x = (x - data[i]) & 0xFF
    return (x - 0x19) & 0xFF


def decodificar_ponto_entrada(data: bytes) -> dict:
    """Decodifica a 1ª instrução ARM (0x000..0x003). NÃO assume que é branch."""
    word = int.from_bytes(data[0:4], "little")
    info = {
        "instrucao_hex": f"0x{word:08x}",
        "eh_branch_incondicional": False,
        "mnemonico": None,
        "destino_hex": None,
        "observacao": None,
    }
    cond = (word >> 28) & 0xF
    opcode_branch = (word >> 25) & 0b111          # 101 = B/BL
    if opcode_branch == 0b101:
        link = (word >> 24) & 1
        imm24 = word & 0xFFFFFF
        desloc = imm24 << 2
        if desloc & (1 << 25):                     # estende sinal de imm24<<2
            desloc -= 1 << 26
        destino = (GBA_ROM_BASE + 8 + desloc) & 0xFFFFFFFF   # PC = endereço+8 (pipeline ARM)
        info["eh_branch_incondicional"] = (cond == 0xE)
        info["mnemonico"] = "BL" if link else "B"
        info["destino_hex"] = f"0x{destino:08x}"
        if cond != 0xE:
            info["observacao"] = f"branch condicional (cond=0x{cond:x}) — atípico para entry point"
    else:
        info["observacao"] = "primeira instrução não é B/BL — cabeçalho atípico; NÃO desassemblar a frio"
    return info


def parse_cabecalho(data: bytes) -> dict:
    titulo_raw = data[0xA0:0xAC]
    codigo_raw = data[0xAC:0xB0]
    maker_raw = data[0xB0:0xB2]
    codigo_str = codigo_raw.decode("ascii", errors="replace")

    cat_letra = codigo_str[0] if len(codigo_str) >= 1 else ""
    idioma_letra = codigo_str[3] if len(codigo_str) >= 4 else ""

    calc = header_checksum(data)
    armaz = data[0xBD]

    return {
        "titulo_ascii": titulo_raw.decode("ascii", errors="replace").strip("\x00").strip(),
        "titulo_raw_hex": titulo_raw.hex(),
        "codigo_jogo": codigo_str,
        "categoria_game_code": {
            "letra": cat_letra,
            "indicativo": GAME_CODE_CATEGORIA.get(cat_letra, "DESCONHECIDO — verificar GBATEK"),
        },
        "regiao_idioma": {
            "letra": idioma_letra,
            "indicativo": GAME_CODE_IDIOMA.get(idioma_letra, "DESCONHECIDO — verificar GBATEK/No-Intro"),
            "observacao": "indício do cabeçalho, não prova de região/versão",
        },
        "codigo_fabricante": maker_raw.decode("ascii", errors="replace"),
        "fabricante_nome": MAKER_CODES.get(
            maker_raw.decode("ascii", errors="replace"),
            "DESCONHECIDO — cruzar com GBATEK/No-Intro",
        ),
        "fixo_0x96_ok": data[0xB2] == 0x96,
        "unit_code": f"0x{data[0xB3]:02x}",
        "device_type": f"0x{data[0xB4]:02x}",
        "versao_software": data[0xBC],
        "checksum": {"armazenado": f"0x{armaz:02x}", "calculado": f"0x{calc:02x}", "valido": armaz == calc},
        "logo_nintendo_valido": data[0x004:0x0A0] == NINTENDO_LOGO,
        "ponto_entrada": decodificar_ponto_entrada(data),
    }


def extrair_strings(data: bytes, min_len: int) -> list[dict]:
    """Extrai sequências ASCII imprimíveis (0x20..0x7E) com >= min_len bytes."""
    out = []
    inicio = None
    for i, b in enumerate(data):
        if 0x20 <= b <= 0x7E:
            if inicio is None:
                inicio = i
        else:
            if inicio is not None and i - inicio >= min_len:
                out.append({"offset_hex": f"0x{inicio:08x}",
                            "texto": data[inicio:i].decode("ascii")})
            inicio = None
    if inicio is not None and len(data) - inicio >= min_len:
        out.append({"offset_hex": f"0x{inicio:08x}",
                    "texto": data[inicio:].decode("ascii")})
    return out


def contar_padroes_codigo(bloco: bytes) -> tuple[int, int]:
    """Conta padrões que SUGEREM código (heurística, gera hipótese — não fato):

    - thumb_bl: pares de halfwords 0xF000..0xF7FF seguidos de 0xF800..0xFFFF
      (codificação do BL longo do Thumb).
    - arm_bl: instruções 0xEB?????? alinhadas a 4 bytes (BL do ARM, cond=ALWAYS).
    """
    thumb_bl = 0
    n2 = len(bloco) - 3
    for i in range(0, n2, 2):
        w1 = bloco[i] | (bloco[i + 1] << 8)
        if 0xF000 <= w1 <= 0xF7FF:
            w2 = bloco[i + 2] | (bloco[i + 3] << 8)
            if 0xF800 <= w2 <= 0xFFFF:
                thumb_bl += 1
    arm_bl = 0
    for i in range(3, len(bloco), 4):
        if bloco[i] == 0xEB:
            arm_bl += 1
    return thumb_bl, arm_bl


def classificar_bloco(bloco: bytes) -> dict:
    """Classificação HEURÍSTICA do bloco — sempre nível HIPÓTESE."""
    n = len(bloco)
    if n == 0:
        return {"classe": "VAZIO", "entropia": 0.0, "pct_00_ff": 0.0, "thumb_bl": 0, "arm_bl": 0}
    zeros = bloco.count(0)
    ffs = bloco.count(0xFF)
    pct_fill = (zeros + ffs) / n
    ent = entropia_shannon(bloco)
    thumb_bl, arm_bl = contar_padroes_codigo(bloco)
    densidade_bl_k = (thumb_bl + arm_bl) * 1024.0 / n   # padrões BL por KiB

    if pct_fill >= 0.98:
        classe = "PREENCHIMENTO_00_FF (provavel espaco nao utilizado)"
    elif densidade_bl_k >= 8:
        classe = "CODIGO_CANDIDATO (padroes BL Thumb/ARM densos)"
    elif ent >= 6.5:
        classe = "ALTA_ENTROPIA (dados comprimidos/criptografados ou recursos graficos/audio)"
    elif ent >= 4.0:
        classe = "MISTO (codigo esparso, dados estruturados ou strings)"
    else:
        classe = "BAIXA_ENTROPIA (tabelas, area esparsa ou dados repetitivos)"

    return {
        "classe": classe,
        "entropia": round(ent, 4),
        "pct_00_ff": round(pct_fill, 4),
        "thumb_bl": thumb_bl,
        "arm_bl": arm_bl,
        "densidade_bl_por_kib": round(densidade_bl_k, 2),
    }


def tamanho_efetivo_aprox(data: bytes) -> int:
    """Último offset não-0x00/0xFF + 1: limite superior heurístico do conteúdo útil."""
    for i in range(len(data) - 1, -1, -1):
        if data[i] not in (0x00, 0xFF):
            return i + 1
    return 0


# --------------------------------------------------------------------------- #
# Análise completa
# --------------------------------------------------------------------------- #

def analyze_rom(caminho: Path, block_size: int, min_str: int) -> dict:
    if not caminho.exists():
        raise AnalysisError(f"arquivo não encontrado: {caminho}")
    if not caminho.is_file():
        raise AnalysisError(f"não é um arquivo regular: {caminho}")
    if caminho.suffix.lower() in (".zip", ".7z", ".rar"):
        raise AnalysisError("arquivo compactado — extraia a ROM antes (não executo descompressão automática)")

    data = caminho.read_bytes()
    if len(data) < 0xC0:
        raise AnalysisError(
            f"arquivo com {len(data)} bytes: menor que o cabeçalho GBA (0xC0). Não parece uma ROM válida."
        )

    n = len(data)
    tamanhos_tipicos = (4 * 2**20, 8 * 2**20, 16 * 2**20, 32 * 2**20)
    pot2 = (n & (n - 1)) == 0 and n >= 32 * 1024

    blocos = []
    for off in range(0, n, block_size):
        info = classificar_bloco(data[off:off + block_size])
        info["offset_hex"] = f"0x{off:08x}"
        info["endereco_gba_hex"] = f"0x{GBA_ROM_BASE + off:08x}"
        blocos.append(info)
    resumo_classes: Counter = Counter(b["classe"].split(" (")[0] for b in blocos)

    strings = extrair_strings(data, min_str)
    hist = Counter(data)
    top10 = [[f"0x{b:02x}", c, round(c / n * 100, 2)] for b, c in hist.most_common(10)]

    return {
        "meta": {
            "ferramenta": "gba_ident.py",
            "versao": VERSAO_FERRAMENTA,
            "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "arquivo": {
            "nome": caminho.name,
            "caminho": str(caminho.resolve()),
            "tamanho_bytes": n,
            "tamanho_humano": f"{n / 2**20:.2f} MiB" if n >= 2**20 else f"{n / 1024:.1f} KiB",
            "potencia_de_dois": pot2,
            "tamanhos_tipicos_mib": [t // 2**20 for t in tamanhos_tipicos],
            "ultimo_byte_util_hex": f"0x{tamanho_efetivo_aprox(data) - 1:08x}",
            **hashes_do_arquivo(data),
        },
        "cabecalho": parse_cabecalho(data),
        "bytes_globais": {
            "entropia_global": round(entropia_shannon(data), 4),
            "pct_00": round(hist.get(0, 0) / n * 100, 2),
            "pct_ff": round(hist.get(0xFF, 0) / n * 100, 2),
            "histograma_top10": top10,
        },
        "strings": {
            "min_len": min_str,
            "total": len(strings),
            "amostra_primeiras_200": strings[:200],
            "_todas_strings": strings,  # uso interno; removido antes do JSON (pode ser enorme)
            "aviso": "somente ASCII; textos com encoding próprio não aparecem aqui",
        },
        "regioes": {
            "tamanho_bloco": block_size,
            "total_blocos": len(blocos),
            "resumo_classes": dict(resumo_classes),
            "blocos": blocos,
            "aviso": "classificacao HEURISTICA — nivel HIPOTESE ate validacao por desassembly (Fase 2)",
        },
        "limitacoes": [
            "Campos do cabecalho sao INDICIOS, nao prova de identidade/versao/regiao.",
            "Classificacao codigo/dados por entropia+BL e heuristica (gera hipoteses).",
            "Sem desassembly real nesta fase — isso e trabalho da Fase 2 (Ghidra/capstone).",
        ],
    }


# --------------------------------------------------------------------------- #
# Saídas
# --------------------------------------------------------------------------- #

def escrever_relatorios(rep: dict, outdir: Path) -> dict:
    """Grava JSON (sem a lista completa de strings) + TSVs. Retorna {papel: caminho}."""
    outdir.mkdir(parents=True, exist_ok=True)
    base = Path(rep["arquivo"]["nome"]).stem
    caminhos = {}

    todas_strings = rep["strings"].pop("_todas_strings",
                                       rep["strings"]["amostra_primeiras_200"])

    p_json = outdir / f"{base}_ident.json"
    p_json.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    caminhos["relatorio_json"] = str(p_json)

    p_str = outdir / f"{base}_strings.tsv"
    with p_str.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["offset_hex", "texto"])
        for s in todas_strings:
            w.writerow([s["offset_hex"], s["texto"]])
    caminhos["strings_tsv"] = str(p_str)

    p_reg = outdir / f"{base}_regioes.tsv"
    with p_reg.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["offset_hex", "endereco_gba_hex", "classe", "entropia",
                    "pct_00_ff", "thumb_bl", "arm_bl", "densidade_bl_por_kib"])
        for b in rep["regioes"]["blocos"]:
            w.writerow([b["offset_hex"], b["endereco_gba_hex"], b["classe"],
                        b["entropia"], b["pct_00_ff"], b["thumb_bl"],
                        b["arm_bl"], b["densidade_bl_por_kib"]])
    caminhos["regioes_tsv"] = str(p_reg)
    return caminhos


def resumo_humano(rep: dict) -> str:
    a, c = rep["arquivo"], rep["cabecalho"]
    b = rep["bytes_globais"]
    chk = c["checksum"]
    chk_txt = "OK" if chk["valido"] else (
        f"INVÁLIDO (esperado {chk['calculado']}, lido {chk['armazenado']})")
    entry_txt = (f"{c['ponto_entrada']['mnemonico']} {c['ponto_entrada']['destino_hex']}"
                 if c["ponto_entrada"]["mnemonico"]
                 else c["ponto_entrada"]["observacao"])
    linhas = [
        "=" * 70,
        f"FASE 1 — IDENTIFICACAO DA ROM  (gba_ident {VERSAO_FERRAMENTA})",
        "=" * 70,
        f"Arquivo....: {a['nome']}  ({a['tamanho_humano']}, {'tamanho padrão' if a['potencia_de_dois'] else 'tamanho ATÍPICO'})",
        f"SHA-256....: {a['sha256']}",
        f"MD5/SHA-1..: {a['md5']} / {a['sha1']}",
        "",
        f"Título.....: {c['titulo_ascii']!r}  (raw: {c['titulo_raw_hex']})",
        f"Game code..: {c['codigo_jogo']}  → categoria: {c['categoria_game_code']['indicativo']}",
        f"Região.....: letra '{c['regiao_idioma']['letra']}' → {c['regiao_idioma']['indicativo']} (indício, não prova)",
        f"Fabricante.: '{c['codigo_fabricante']}' → {c['fabricante_nome']}",
        f"Versão s/w.: {c['versao_software']}   unit_code={c['unit_code']} device_type={c['device_type']}",
        f"Cabeçalho..: 0x96 {'OK' if c['fixo_0x96_ok'] else 'INVÁLIDO'} | "
        f"logo {'OK' if c['logo_nintendo_valido'] else 'INVÁLIDO'} | "
        f"checksum {chk_txt}",
        f"Entry......: {c['ponto_entrada']['instrucao_hex']} → {entry_txt}",
        "",
        f"Bytes......: entropia global {b['entropia_global']} bits/byte | 0x00: {b['pct_00']}% | 0xFF: {b['pct_ff']}%",
        f"Útil até...: {a['ultimo_byte_util_hex']} (heurístico, limite superior)",
        f"Strings....: {rep['strings']['total']} sequências ASCII >= {rep['strings']['min_len']} bytes",
        "",
        "Regiões por classe (HEURÍSTICA = HIPÓTESE):",
        *[f"  {k:<22} {v} bloco(s)" for k, v in rep["regioes"]["resumo_classes"].items()],
        "",
        "LIMITAÇÕES:",
        *[f"  - {l}" for l in rep["limitacoes"]],
        "=" * 70,
    ]
    return "\n".join(linhas)


def log_execucao(log_dir: Path, entrada: dict) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "gba_ident_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def atualizar_inventory(caminho_inv: Path, rep: dict, relatorios: dict) -> None:
    inv = json.loads(caminho_inv.read_text(encoding="utf-8")) if caminho_inv.exists() else {
        "projeto": "gba-re", "versao_inventario": 1, "rom": {}, "arquivos": []}
    inv["atualizado_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    inv["rom"].update({
        "status": "COPIA_REGISTRADA",
        "caminho_copia_trabalho": rep["arquivo"]["caminho"],
        "sha256": rep["arquivo"]["sha256"],
        "tamanho_bytes": rep["arquivo"]["tamanho_bytes"],
        "titulo_cabecalho_indicio": rep["cabecalho"]["titulo_ascii"],
        "game_code_indicio": rep["cabecalho"]["codigo_jogo"],
    })
    existentes = {e["caminho"] for e in inv.get("arquivos", [])}
    for papel, c in relatorios.items():
        p = Path(c)
        if str(p) not in existentes:
            inv.setdefault("arquivos", []).append({
                "caminho": str(p), "papel": f"Fase 1 — {papel}",
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    caminho_inv.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Self-test (fixture sintética rotulada)
# --------------------------------------------------------------------------- #

def construir_fixture() -> bytes:
    """ROM sintética determinística com características conhecidas. NÃO é um jogo."""
    rnd = random.Random(0xC0DE)  # seed fixa → fixture reproduzível
    header = bytearray(0xC0)
    header[0:4] = b"\x2E\x00\x00\xEA"                      # B 0x080000C0 (ARM, real GBATEK-style)
    header[4:4 + 156] = NINTENDO_LOGO
    header[0xA0:0xAC] = b"TESTFIXTURE\0"
    header[0xAC:0xB0] = b"TZNE"                            # categoria 'T' (não mapeada) / idioma 'E'
    header[0xB0:0xB2] = b"01"
    header[0xB2] = 0x96
    header[0xBD] = header_checksum(header)

    body = bytearray(header)
    body += bytes(0x1000 - len(body))                       # pad até 0x1000
    body += (b"\x00\xF0\x00\xF8" * 1024)                    # bloco 1: BL-Thumb denso (candidato código)
    body += rnd.randbytes(0x1000)                           # bloco 2: alta entropia determinística
    body[-8:] = bytes(8)                                    # garante terminador não-ASCII antes da string
    bloco_str = bytearray(0x1000)
    bloco_str[0:16] = b"HELLO GBA WORLD!"                   # bloco 3: string conhecida @0x3000
    body += bloco_str
    body += bytes(0x4000)                                   # blocos 4-7: zeros (preenchimento)
    return bytes(body)


def self_test(workdir: Path, verbose: bool, keep_fixture: bool) -> int:
    fixture = workdir / "fixture_sintetico.gba"
    data = construir_fixture()
    fixture.write_bytes(data)

    rep = analyze_rom(fixture, block_size=0x1000, min_str=6)

    cab, arq = rep["cabecalho"], rep["arquivo"]
    blocos = rep["regioes"]["blocos"]
    strs = rep["strings"]["amostra_primeiras_200"]

    checks = [
        ("tamanho do arquivo",            arq["tamanho_bytes"] == len(data)),
        ("sha256 registrado",             arq["sha256"] == hashlib.sha256(data).hexdigest()),
        ("título parseado",               cab["titulo_ascii"] == "TESTFIXTURE"),
        ("game code parseado",            cab["codigo_jogo"] == "TZNE"),
        ("categoria 'T' = DESCONHECIDO",  cab["categoria_game_code"]["indicativo"].startswith("DESCONHECIDO")),
        ("idioma 'E' mapeado",            "América" in cab["regiao_idioma"]["indicativo"]),
        ("maker '01' = Nintendo",         cab["fabricante_nome"] == "Nintendo"),
        ("valor fixo 0x96 ok",            cab["fixo_0x96_ok"] is True),
        ("logo da Nintendo ok",           cab["logo_nintendo_valido"] is True),
        ("checksum do cabeçalho ok",      cab["checksum"]["valido"] is True),
        ("entry point → 0x080000C0",      cab["ponto_entrada"]["destino_hex"] == "0x080000c0"),
        ("string conhecida @0x3000",      any(s["texto"] == "HELLO GBA WORLD!" and s["offset_hex"] == "0x00003000" for s in strs)),
        ("bloco 1 = CODIGO_CANDIDATO",    "CODIGO_CANDIDATO" in blocos[1]["classe"]),
        ("bloco 2 = ALTA_ENTROPIA",       "ALTA_ENTROPIA" in blocos[2]["classe"]),
        ("bloco 4 = PREENCHIMENTO",       "PREENCHIMENTO" in blocos[4]["classe"]),
        ("entropia bloco 2 > 7.0",        blocos[2]["entropia"] > 7.0),
    ]

    falhas = 0
    for nome, ok in checks:
        marca = "PASS" if ok else "FAIL"
        if verbose or not ok:
            print(f"  [{marca}] {nome}")
        if not ok:
            falhas += 1

    print(f"self-test: {len(checks) - falhas}/{len(checks)} verificações OK "
          f"(fixture: {fixture} — ROM SINTÉTICA, não é um jogo)")
    if falhas:
        print("self-test FALHOU — não use esta ferramenta até corrigir.", file=sys.stderr)
    elif not keep_fixture:
        fixture.unlink()
    return 1 if falhas else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    script_dir = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(
        description="FASE 1 — identificação/triagem de ROM GBA (ver docstring do módulo).",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", type=Path, help="caminho da ROM bruta (.gba/.agb/.bin)")
    ap.add_argument("-o", "--outdir", type=Path, default=script_dir.parent / "reports",
                    help="diretório de saída (padrão: ../reports)")
    ap.add_argument("--block-size", type=lambda s: int(s, 0), default=65536,
                    help="tamanho do bloco p/ entropia/classificação (ex.: 0x10000) [65536]")
    ap.add_argument("--min-str", type=int, default=6, help="tamanho mínimo de string ASCII [6]")
    ap.add_argument("--update-inventory", type=Path, default=None,
                    help="atualiza inventory.json com os resultados")
    ap.add_argument("--self-test", action="store_true",
                    help="valida a ferramenta com ROM sintética rotulada e sai")
    ap.add_argument("--keep-fixture", action="store_true", help="mantém a fixture do self-test")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logs_dir = script_dir.parent / "logs"

    if args.self_test:
        tests_dir = script_dir.parent / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        return self_test(tests_dir, args.verbose, args.keep_fixture)

    if not args.rom:
        ap.print_help()
        print("\nerro: informe a ROM (ou use --self-test).", file=sys.stderr)
        return 2
    if args.block_size < 512:
        print("erro: --block-size mínimo é 512.", file=sys.stderr)
        return 2
    if args.min_str < 3:
        print("erro: --min-str mínimo é 3.", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    try:
        rep = analyze_rom(args.rom, args.block_size, args.min_str)
    except AnalysisError as e:
        print(f"erro de análise: {e}", file=sys.stderr)
        return 3

    relatorios = escrever_relatorios(rep, args.outdir)

    if args.update_inventory:
        atualizar_inventory(args.update_inventory, rep, relatorios)

    duracao = round(time.perf_counter() - t0, 3)
    print(resumo_humano(rep))
    print("\nArtefatos:")
    for k, v in relatorios.items():
        print(f"  {k:<16} {v}")
    if args.update_inventory:
        print(f"  inventory        atualizado: {args.update_inventory}")

    log_execucao(logs_dir, {
        "utc": rep["meta"]["utc"], "ferramenta": "gba_ident.py",
        "versao": VERSAO_FERRAMENTA, "argv": sys.argv,
        "rom_sha256": rep["arquivo"]["sha256"],
        "duracao_s": duracao, "saidas": relatorios,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
