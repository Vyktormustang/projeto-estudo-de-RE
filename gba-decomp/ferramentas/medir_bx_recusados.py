#!/usr/bin/env python3
"""Os `bx rN` que o levantador RECUSA: quais tem valor conhecido em traducao?

Por que isto existe: `bx rN` e' a maior lacuna do levantamento (39 das 191 recusas
na ROM de estudo) e o relatorio a tratava como um bloco so', sob o rotulo "sem
origem conhecida". A pergunta que decide se ha' o que implementar e': o valor do
registrador existe em tempo de TRADUCAO?

  * se existe, o destino e' FIXO -- e a recusa tem de dizer por que ela acontece
    mesmo assim (o alvo esta' em outro modo de CPU? fora da imagem?);
  * se nao existe, o destino e' um PARAMETRO de quem chamou, e recusar e' a
    resposta certa -- nao falta implementar instrucao nenhuma ali.

Como isto difere de `onde_estao_as_lacunas.py`: la' a origem do registrador e'
CLASSIFICADA por leitura de TEXTO do desmonte (heuristica, para escolher o que
atacar). Aqui a recusa vem do PROPRIO levantador (espiao em `_Emissor._bx`) e o
valor e' LIDO -- `adr` calculado pela mesma conta do levantador, literal do pool
lido da imagem. E a classificacao aqui e' refeita POR FORA, de proposito: so'
assim esta sonda pode DISCORDAR da mensagem de recusa, em vez de repeti-la.

Medido com esta sonda na ROM de estudo (rodada r19): 39 recusas `bx rN` -- 11 sao
thunks de janela de 4 bytes, 1 e' chamada indireta ARM->Thumb montada a mao, 3
sao `adr` + `bx` dando valor PAR (bit0 = 0 em `bx` = modo ARM, ou seja o destino e'
o trecho no outro modo, que uma janela Thumb nao levanta), 1 e' literal de pool
apontando para RAM (0x030028E1, fora da imagem) e os outros 23 nao tem valor em
traducao. A primeira versao desta sonda errou feio por nao usar o caminho do
levantador: filtrando `bx` por conta propria ela mediu 6 973 sitios em vez de 39.

Uso:
    python ferramentas/medir_bx_recusados.py ROM.gba [--censo functions.csv] \\
        [--json bx_recusados.json] [--exemplos 40]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import capstone                                            # noqa: E402
from gbadecomp import decompile as decompile_mod          # noqa: E402
from gbadecomp import disasm as disasm_mod                # noqa: E402
from gbadecomp import rom as rom_mod                      # noqa: E402


def recusas_de_bx(desmontagem, imagem: bytes, base: int = rom_mod.ROM_BASE) -> list:
    """As recusas `bx rN` do levantador, ditas por ELE (espiao em `_Emissor._bx`).

    Devolve `(entrada da janela, endereco do `bx`, registrador, motivo)` por site.
    Nao usar um filtro parecido no lugar disto: `bx lr` e o `bx rN` de retorno
    (depois de `pop {rN}`) NAO sao recusa nenhuma, e o registrador que a mensagem
    cita e' o que o levantador tentou traduzir.
    """
    recusados: list = []
    original = decompile_mod._Emissor._bx

    def espiao(self, ins):
        try:
            return original(self, ins)
        except decompile_mod._NaoLevantado as erro:
            recusados.append((self.f.entrada, ins.address,
                              ins.op_str.split(",")[0].strip(), str(erro)))
            raise

    decompile_mod._Emissor._bx = espiao
    try:
        decompile_mod.decompilar(desmontagem, imagem, base=base)
    finally:
        # devolver a funcao mesmo se o levantamento estourar no meio
        decompile_mod._Emissor._bx = original
    return recusados


def _valor_da_anterior(janela, imagem: bytes, base: int, site: int, registrador: str):
    """`(valor, como)` que a instrucao anterior ao `bx` deixa no registrador.

    Usa as pecas do PROPRIO levantador (`_Emissor.cs`, `_pc_da_instrucao`) para
    nao duplicar a conta do `pc` -- conta do Thumb (endereco + 4, alinhado a 4) e
    do ARM (endereco + 8) que ja' custou um deslocamento de 4 bytes uma vez.
    """
    anteriores = [i for i in janela.instrucoes if i.endereco < site]
    if not anteriores:
        return None
    anterior = anteriores[-1]
    emissor = decompile_mod._Emissor(janela, imagem, base, {})
    ins = next(emissor.cs.disasm(bytes(anterior.bytes_), anterior.endereco), None)
    if ins is None or len(ins.operands) < 2:
        return None
    if (ins.mnemonic == "adr"
            and ins.operands[1].type == capstone.arm.ARM_OP_IMM):
        if emissor._reg(ins.operands[0]) != registrador:
            return None
        return (emissor._pc_da_instrucao(ins) + ins.operands[1].imm, "adr")
    if (ins.mnemonic.startswith("ldr")
            and ins.operands[1].type == capstone.arm.ARM_OP_MEM):
        if ins.operands[1].mem.base != capstone.arm.ARM_REG_PC:
            return None
        if emissor._reg(ins.operands[0]) != registrador:
            return None
        endereco = emissor._pc_da_instrucao(ins) + ins.operands[1].mem.disp
        deslocamento = endereco - base
        if deslocamento < 0 or deslocamento + 4 > len(imagem):
            return None
        return (int.from_bytes(imagem[deslocamento:deslocamento + 4], "little"),
                f"ldr do pool 0x{endereco:08X}")
    return None


def medir(desmontagem, imagem: bytes, base: int = rom_mod.ROM_BASE) -> dict:
    """O veredito por site: valor conhecido? e o valor e' o que?"""
    por_tipo: collections.Counter = collections.Counter()
    sites = []
    for entrada, site, registrador, motivo in recusas_de_bx(desmontagem, imagem, base):
        medido = _valor_da_anterior(desmontagem.funcoes[entrada], imagem, base,
                                    site, registrador)
        if medido is None:
            tipo = "sem valor em traducao"
        else:
            valor, _ = medido
            if not (base <= (valor & ~1) < base + len(imagem)):
                tipo = "valor fora da imagem (RAM/IO)"
            elif valor & 1:
                tipo = "valor na imagem com bit0 = 1 (Thumb)"
            else:
                tipo = "valor par: troca de modo de CPU (ARM)"
        por_tipo[tipo] += 1
        sites.append({
            "site": f"0x{site:08X}", "janela": f"0x{entrada:08X}",
            "registrador": registrador,
            "valor": None if medido is None else f"0x{medido[0]:08X}",
            "como": None if medido is None else medido[1],
            "tipo": tipo, "motivo": motivo,
        })
    return {"recusas_bx": len(sites), "por_tipo": dict(por_tipo.most_common()),
            "sites": sites}


def medir_rom(caminho_rom: str, caminho_censo: str | None) -> dict:
    """Desmonta a ROM (com o censo como sementes, se houver) e mede os `bx`."""
    imagem = Path(caminho_rom).read_bytes()
    sementes = None
    if caminho_censo:
        sementes = {s.addr: (s.mode or "thumb")
                    for s in rom_mod.carregar_funcoes_csv(caminho_censo)}
    desmontagem = disasm_mod.desmontar_por_sementes(imagem, sementes=sementes)
    medido = medir(desmontagem, imagem)
    medido["rom"] = caminho_rom
    medido["censo"] = caminho_censo
    medido["funcoes"] = len(desmontagem.funcoes)
    return medido


def relatar(medido: dict, exemplos: int) -> str:
    linhas = [f"recusas `bx rN` do levantador: {medido['recusas_bx']}",
              f"funcoes desmontadas: {medido.get('funcoes', '?')}", ""]
    for tipo, quantos in medido["por_tipo"].items():
        linhas.append(f"  {quantos:3d}  {tipo}")
        mostrados = [s for s in medido["sites"] if s["tipo"] == tipo]
        for site in mostrados[:exemplos]:
            detalhe = "" if site["valor"] is None else \
                f" = {site['valor']} via {site['como']}"
            linhas.append(f"        {site['site']} (janela {site['janela']}) "
                          f"bx {site['registrador']}{detalhe}")
        if len(mostrados) > exemplos:
            linhas.append(f"        ... (+{len(mostrados) - exemplos}; o JSON tem todos)")
    linhas += ["",
               "o que cada recusa diz hoje (conferir contra a medicao acima):"]
    for motivo, quantos in collections.Counter(
            s["motivo"] for s in medido["sites"]).most_common(8):
        linhas.append(f"  {quantos:3d}  {motivo[:110]}")
    return "\n".join(linhas)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom")
    parser.add_argument("--censo", help="functions.csv do censo (mesmas sementes)")
    parser.add_argument("--json", help="gravar a medicao neste arquivo")
    parser.add_argument("--exemplos", type=int, default=40,
                        help="quantos sites listar por tipo (padrao: 40)")
    args = parser.parse_args(argv)

    medido = medir_rom(args.rom, args.censo)
    print(relatar(medido, args.exemplos))
    if args.json:
        Path(args.json).write_text(json.dumps(medido, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
        print(f"\nJSON gravado em {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
