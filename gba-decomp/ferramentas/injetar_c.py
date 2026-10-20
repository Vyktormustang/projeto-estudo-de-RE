"""Compila uma modificacao em C e injeta na ROM, num ponto que roda sozinho.

Este e' o caminho "escrever codigo novo e compilar", em vez de so' trocar
bytes. A cadeia e':

  C  --(zig cc, Thumb/ARM7TDMI)-->  objeto ELF  --(.text)-->  bytes
     --(espaco livre da ROM)-->  ROM patcheada

O gancho e' sempre um `bl` existente: o stub executa a funcao nova e depois
refaz a chamada original, entao o jogo nao percebe diferenca. Escolher o `bl`
certo e' escolher QUANDO o codigo roda -- ver `--hook` e `--reexecutar`.

Pontos medidos nesta ROM (ver NOTAS_DE_TRABALHO.md):

  0x080004A6  `bl 0x08000890` (VBlankIntrWait) dentro do loop de AgbMain
              -> roda 1x por quadro. AgbMain roda DA ROM (crt0 faz
              `bx 0x080003A5`), entao `bl` comum funciona.

Cuidados que custaram tempo e estao codificados aqui:

 1. **O objeto e' montado com base 0.** Todos os literais sao relativos ao PC;
    para continuarem certos, o codigo tem de ser injetado em endereco
    alinhado a 4. Endereco 2-mod-4 desloca todo `ldr [pc, ...]`.
 2. **`ldr rX, =VALOR` do keystone e' quebrado** -- por isso o stub usa
    `montar_thumb_literais`, que monta o pool por conta propria.
 3. O stub preserva r0-r3 antes de chamar a funcao nova (o ponto de chamada
    pode ter valores vivos) e refaz a chamada original depois.
 4. **`bl` do Thumb no ARM7TDMI alcanca so' +/- 4 MiB** -- e' a codificacao de
    22 bits (S + imm10 + imm11) << 1. O keystone monta e o capstone desmonta
    esse salto como se fosse o `bl` de 32 bits do Thumb-2 (+/- 16 MiB) e nao
    avisam: o salto de 7 MiB "monta" e cai 4 MiB antes do destino. Foi essa a
    causa de varios "o hook nao roda" anteriores. Por isso `injetar` CONFERe
    o alcance e recusa; use `--endereco 0x080000C0` (padding livre desta ROM)
    quando o espaco livre do fim estiver longe demais.

Uso:
    python ferramentas/injetar_c.py ROM.gba -o ROM_mod.gba \\
        --fonte mod.c --hook 0x080004A6 --reexecutar 0x08000890

O `--hook` e' o endereco da instrucao `bl` a substituir; `--reexecutar` e' o
destino dessa mesma `bl` (o script confere que batem).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp import patch  # noqa: E402

ZIG_PADRAO = RAIZ.parent / ".venv/lib/python3.11/site-packages/ziglang/zig"


class ErroDeInjecao(Exception):
    """Falha ao compilar ou injetar."""


def achar_zig() -> Path:
    if ZIG_PADRAO.exists():
        return ZIG_PADRAO
    no_path = shutil.which("zig")
    if no_path:
        return Path(no_path)
    raise ErroDeInjecao(
        f"zig nao encontrado em {ZIG_PADRAO} nem no PATH. "
        "Sem compilador nao ha' como compilar o C.")


def compilar(fonte: Path, objeto: Path) -> None:
    """Compila `fonte` para Thumb (ARM7TDMI), freestanding, sem biblioteca."""
    comando = [
        str(achar_zig()), "cc",
        "-target", "thumb-freestanding-eabi",
        "-mcpu=arm7tdmi",
        "-Os",
        "-ffreestanding", "-fno-builtin", "-nostdlib",
        "-fno-asynchronous-unwind-tables", "-fno-exceptions",
        "-c", str(fonte), "-o", str(objeto),
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise ErroDeInjecao(
            f"zig cc falhou:\n{resultado.stdout}\n{resultado.stderr}")
    if not objeto.exists() or objeto.stat().st_size == 0:
        raise ErroDeInjecao("o compilador nao gerou objeto")


def extrair_texto(objeto: Path) -> bytes:
    """Bytes da secao `.text`, sem tabela de simbolos nem realocacao."""
    from elftools.elf.elffile import ELFFile

    with open(objeto, "rb") as arquivo:
        secao = ELFFile(arquivo).get_section_by_name(".text")
        if secao is None:
            raise ErroDeInjecao("o objeto nao tem secao .text")
        dados = secao.data()
    if not dados:
        raise ErroDeInjecao(".text vazia")
    return dados


def montar_stub(chamada: int, reexecutar: int, endereco: int) -> bytes:
    """Stub Thumb: preserva r0-r3, chama o codigo novo, refaz a `bl` original.

    Se o codigo novo estiver fora dos +/- 4 MiB do `bl` do ARM7TDMI, a chamada
    passa por um *thunk* `bx r3` colado no fim do stub:

        ldr r3, =destino|1
        bl thunk          ; o `bl` seta lr com o bit Thumb ligado
        ...
        thunk: bx r3

    Por que nao `mov lr, pc; bx r3` (o idioma classico): no Thumb do ARM7TDMI
    a leitura de PC devolve o endereco com o bit 0 ZERADO, entao o `bx lr` do
    destino voltaria em estado ARM e executaria lixo. O `bl` seta o bit.
    """
    if abs(chamada - endereco) <= ALCANCE_BL_THUMB:
        corpo = f"""
push {{r0, r1, r2, r3, lr}}
bl 0x{chamada:08X}
pop {{r0, r1, r2, r3}}
bl 0x{reexecutar:08X}
pop {{pc}}
"""
        return patch.montar_thumb_literais(corpo, endereco)
    thunk = endereco + 0x40          # provisorio; corrigido nas duas passadas
    for _ in range(2):
        corpo = f"""
push {{r0, r1, r2, r3, lr}}
ldr r3, =0x{chamada + 1:08X}
bl 0x{thunk:08X}
pop {{r0, r1, r2, r3}}
bl 0x{reexecutar:08X}
pop {{pc}}
"""
        base = patch.montar_thumb_literais(corpo, endereco)
        thunk = endereco + len(base)
    return base + patch.montar_thumb("bx r3", thunk)


ALCANCE_BL_THUMB = 4 * 1024 * 1024


def conferir_alcance(origem: int, destino: int, o_que: str) -> None:
    """`bl` Thumb no ARM7TDMI so' alcanca +/- 4 MiB. Falhar aqui e' melhor que
    gerar ROM que salta 4 MiB antes do destino e trava sem explicacao."""
    distancia = destino - origem
    if abs(distancia) > ALCANCE_BL_THUMB:
        raise ErroDeInjecao(
            f"{o_que}: `bl` de 0x{origem:08X} para 0x{destino:08X} = "
            f"{distancia / 1024 / 1024:.2f} MiB, fora do alcance de +/- 4 MiB "
            "do BL Thumb do ARM7TDMI (o keystone nao avisa). Use um endereco "
            "de injecao mais perto -- nesta ROM, `--endereco 0x080000C0`.")


def injetar(imagem: bytes, codigo: bytes, hook: int, reexecutar: int,
            endereco: int | None = None) -> tuple[bytes, dict]:
    """Devolve a imagem com o codigo injetado e o hook apontando para ele."""
    esperado = patch.montar_thumb(f"bl 0x{reexecutar:08X}", hook)
    atual = imagem[hook - 0x08000000: hook - 0x08000000 + 4]
    if atual != esperado:
        raise ErroDeInjecao(
            f"0x{hook:08X} nao tem `bl 0x{reexecutar:08X}` "
            f"(tem {atual.hex(' ')}, esperava {esperado.hex(' ')})")

    # area livre alinhada a 4: o objeto foi montado com base 0, e todo literal
    # PC-relativo so' continua certo se o codigo cair em endereco 4-alinhado.
    if endereco is None:
        area = patch.achar_espaco_livre(imagem, len(codigo) + 96, alinhamento=4)
        area_codigo = area + ((len(codigo) + 1) & ~1)
    else:
        area = endereco
        if area % 4:
            raise ErroDeInjecao(f"endereco 0x{area:08X} nao e' multiplo de 4")
        area_codigo = patch.achar_espaco_livre(imagem, len(codigo) + 8, alinhamento=4)
        trecho = imagem[area - 0x08000000: area - 0x08000000 + 32]
        # padding desta ROM mistura 0x00 e 0xFF (0x080000C0..0x08000203 e'
        # zero ate' 0xCF e 0xFF dali em diante). Exigir so' esses dois bytes e'
        # heuristica suficiente para pegar endereco ocupado por codigo/dado.
        padding = len(trecho) == 32 and all(b in (0x00, 0xFF) for b in trecho)
        if not padding:
            raise ErroDeInjecao(
                f"0x{area:08X} nao esta' livre (esperava 32 bytes de padding "
                "0x00/0xFF para o stub)")
    endereco_stub = area
    stub = montar_stub(area_codigo, reexecutar, endereco_stub)
    limite_stub = area + (len(codigo) + 96 if endereco is None else 32)
    if endereco_stub + len(stub) > limite_stub:
        raise ErroDeInjecao(
            f"stub de {len(stub)} B nao coube em 0x{area:08X}")
    saida = bytearray(imagem)
    saida[area_codigo - 0x08000000: area_codigo - 0x08000000 + len(codigo)] = codigo
    saida[endereco_stub - 0x08000000: endereco_stub - 0x08000000 + len(stub)] = stub
    conferir_alcance(hook, endereco_stub, "hook -> stub")
    conferir_alcance(endereco_stub, reexecutar, "stub -> chamada original")
    salto = patch.montar_thumb(f"bl 0x{endereco_stub:08X}", hook)
    saida[hook - 0x08000000: hook - 0x08000000 + 4] = salto
    return bytes(saida), {
        "codigo": area_codigo,
        "stub": endereco_stub,
        "hook": hook,
        "salto": salto.hex(" "),
        "bytes_codigo": len(codigo),
        "bytes_stub": len(stub),
    }


def _alinhar4(valor: int) -> int:
    return (valor + 3) & ~3


def principal(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("-o", "--saida", type=Path, required=True)
    parser.add_argument("--fonte", type=Path, required=True,
                        help="arquivo .c com a modificacao")
    parser.add_argument("--hook", type=lambda s: int(s, 0), required=True,
                        help="endereco da instrucao `bl` a substituir")
    parser.add_argument("--reexecutar", type=lambda s: int(s, 0), required=True,
                        help="destino da `bl` original, refeita pelo stub")
    parser.add_argument("--endereco", type=lambda s: int(s, 0), default=None,
                        help="onde injetar (padrao: primeiro espaco livre). "
                             "Nesta ROM, 0x080000C0 fica perto do loop principal.")
    args = parser.parse_args(argv)

    objeto = args.saida.with_suffix(".o")
    compilar(args.fonte, objeto)
    codigo = extrair_texto(objeto)
    imagem = args.rom.read_bytes()
    nova, info = injetar(imagem, codigo, args.hook, args.reexecutar,
                         args.endereco)
    args.saida.write_bytes(patch.corrigir_cabecalho(nova))
    print(f"fonte      {args.fonte} ({args.fonte.stat().st_size} B)")
    print(f"objeto     {objeto} (.text {info['bytes_codigo']} B)")
    print(f"codigo     0x{info['codigo']:08X}")
    print(f"stub       0x{info['stub']:08X} ({info['bytes_stub']} B)")
    print(f"hook       0x{info['hook']:08X} -> {info['salto']}")
    print(f"saida      {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
