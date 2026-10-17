"""Aplicar patches numa ROM: montar codigo, injetar, conferir o cabecalho.

Por que isto existe: o levantamento ate' aqui so' LIA a imagem. Para "mudar o
jogo" e' preciso o caminho inverso -- escrever bytes --, e escrever bytes sem
guarda produz ROM quebrada de um jeito dificil de achar. As tres regras deste
modulo vem de defeitos concretos:

  1. **Todo patch carrega os bytes que ESPERA encontrar.** Aplicar um patch num
     endereco que nao tem o byte previsto (ROM diferente, patch ja aplicado) e'
     erro, nao aviso: e' a diferenca entre "nao fez nada" e "corrompeu".
  2. **O cabecalho e' recalculado com a formula oficial**: o complemento em
     0xBD e' `-(soma(0xA0..0xBC)) - 0x19`. O projeto somava 0x00..0xBC e por
     isso reprovava o cabecalho desta ROM, que esta' correto.
  3. **Espaco livre e' medido, nao suposto**: so' entra codigo em sequencia de
     0xFF -- que nao decodifica como instrucao e portanto nao e' codigo vivo.

O que este modulo NAO faz: dizer se o patch e' uma boa ideia. Ele obedece.
"""

from __future__ import annotations

from dataclasses import dataclass

from keystone import KS_ARCH_ARM, KS_MODE_THUMB, Ks, KsError

from . import rom as rom_mod


class ErroDePatch(Exception):
    """O patch nao pode ser aplicado -- e o motivo esta' na mensagem."""


@dataclass
class Patch:
    """Uma escrita de bytes, com o que TEM de estar la' antes."""

    endereco: int
    esperado: bytes
    novo: bytes
    motivo: str

    def __post_init__(self) -> None:
        if len(self.esperado) != len(self.novo):
            # Escrever mais bytes do que se confere seria escrever no escuro.
            raise ErroDePatch(
                f"patch em 0x{self.endereco:08X}: esperado tem {len(self.esperado)} "
                f"bytes e novo tem {len(self.novo)} -- so' se troca o mesmo tanto")
        if not self.motivo.strip():
            raise ErroDePatch(f"patch em 0x{self.endereco:08X} sem motivo declarado")


def complemento_correto(imagem: bytes) -> int:
    """O byte que o cabecalho GBA deve ter em 0xBD.

    A soma comeca em 0xA0: os bytes 0x00..0x9F (ramo inicial + logo) ficam de
    fora. Formula: `0xBD = (-(soma(0xA0..0xBC)) - 0x19) & 0xFF`.
    """
    soma = sum(imagem[0xA0:0xBD]) & 0xFF
    return (0x100 - ((soma + 0x19) & 0xFF)) & 0xFF


def corrigir_cabecalho(imagem: bytes) -> bytes:
    """Devolve a imagem com o complemento de 0xBD recalculado.

    Nao mexe em mais nada: logo, titulo, codigo e versao ficam como estao.
    """
    if len(imagem) < rom_mod.HEADER_SIZE:
        raise ErroDePatch(f"imagem de {len(imagem)} bytes: menor que o cabecalho")
    saida = bytearray(imagem)
    saida[0xBD] = complemento_correto(imagem)
    return bytes(saida)


def montar_thumb(codigo: str, endereco: int) -> bytes:
    """Monta `codigo` (sintaxe do keystone) como Thumb, para rodar em `endereco`.

    O endereco importa: `bl` e literais de pool sao relativos. Montar para um
    endereco e injetar em outro produz desvio para o lugar errado -- por isso a
    funcao exige o destino junto com o codigo.
    """
    montador = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    try:
        bruto, _ = montador.asm(codigo, endereco)
    except KsError as exc:
        raise ErroDePatch(f"o assembler recusou o codigo: {exc}") from exc
    if not bruto:
        raise ErroDePatch("o assembler nao gerou byte nenhum")
    return bytes(bruto)


def achar_espaco_livre(imagem: bytes, tamanho: int, alinhamento: int = 2,
                       minimo_seguro: int = 0x1000,
                       a_partir_de: int = rom_mod.HEADER_SIZE) -> int:
    """Endereco GBA de uma sequencia de 0xFF grande o bastante, alinhada.

    NAO basta achar `tamanho` bytes 0xFF: padding entre funcoes e, pior,
    sequencias dentro de grafico comprimido tambem sao 0xFF. Nesta ROM existem
    66 buracos de 0xFF maiores que 32 bytes, e a maioria e' padding -- escrever
    num deles corrompe dado sem dar erro. Por isso o trecho tem de ter
    `minimo_seguro` bytes (4 KiB por padrao): nesta imagem so' 3 trechos passam,
    e sao justamente os de centenas de KiB no fim da area usada.

    Devolve o PRIMEIRO trecho que serve. Levanta `ErroDePatch` se nao houver.
    """
    if tamanho <= 0:
        raise ErroDePatch("tamanho de injecao tem de ser positivo")
    tamanho_exigido = max(tamanho, minimo_seguro)
    run_inicio = None
    for indice, byte in enumerate(imagem):
        if byte == 0xFF:
            if run_inicio is None:
                run_inicio = indice
            continue
        if run_inicio is not None:
            achado = _trecho_alinhado(run_inicio, indice, tamanho, alinhamento,
                                      a_partir_de, tamanho_exigido)
            if achado is not None:
                return achado
            run_inicio = None
    if run_inicio is not None:
        achado = _trecho_alinhado(run_inicio, len(imagem), tamanho, alinhamento,
                                  a_partir_de, tamanho_exigido)
        if achado is not None:
            return achado
    raise ErroDePatch(
        f"nao ha' trecho de {tamanho} bytes livres num run de pelo menos "
        f"{tamanho_exigido} bytes 0xFF")


def _trecho_alinhado(inicio: int, fim: int, tamanho: int, alinhamento: int,
                     minimo: int, tamanho_exigido: int) -> int | None:
    """Primeiro offset alinhado dentro da sequencia que caiba `tamanho`."""
    if fim - inicio < tamanho_exigido:
        return None
    candidato = max(inicio, minimo)
    resto = candidato % alinhamento
    if resto:
        candidato += alinhamento - resto
    if candidato + tamanho <= fim:
        return rom_mod.to_addr(candidato)
    return None


def aplicar(imagem: bytes, patches: list[Patch]) -> bytes:
    """Aplica os patches, conferindo o `esperado` de cada um antes de escrever.

    Ordem importa: todos os `esperado` sao conferidos ANTES de qualquer escrita,
    para uma falha no meio nao deixar a imagem meio patcheada.
    """
    for patch in patches:
        deslocamento = rom_mod.to_offset(patch.endereco)
        if deslocamento < 0 or deslocamento + len(patch.esperado) > len(imagem):
            raise ErroDePatch(
                f"patch em 0x{patch.endereco:08X} cai fora da imagem "
                f"({len(imagem)} bytes)")
        atual = imagem[deslocamento:deslocamento + len(patch.esperado)]
        if atual != patch.esperado:
            raise ErroDePatch(
                f"patch em 0x{patch.endereco:08X} ({patch.motivo}): a imagem tem "
                f"{atual.hex(' ')}, esperado {patch.esperado.hex(' ')} -- ROM "
                f"diferente ou patch ja' aplicado")
    saida = bytearray(imagem)
    for patch in patches:
        deslocamento = rom_mod.to_offset(patch.endereco)
        saida[deslocamento:deslocamento + len(patch.novo)] = patch.novo
    return bytes(saida)


def relatar(imagem: bytes, patches: list[Patch]) -> str:
    """Resumo legivel do que foi escrito -- vai para o relatorio do patch."""
    linhas = [f"{len(patches)} patch(es) em {len(imagem)} bytes de imagem:"]
    for patch in patches:
        linhas.append(f"  0x{patch.endereco:08X}: {patch.esperado.hex(' ')} -> "
                      f"{patch.novo.hex(' ')}")
        linhas.append(f"      {patch.motivo}")
    atual = imagem[0xBD] if len(imagem) > 0xBD else None
    if atual is not None:
        certo = complemento_correto(imagem)
        linhas.append(f"cabecalho: 0xBD = 0x{atual:02X} "
                      + ("(correto)" if atual == certo
                         else f"(INCORRETO, deveria ser 0x{certo:02X})"))
    return "\n".join(linhas)


# --- manifesto declarativo -------------------------------------------------
# Motivo: cada patch novo nao deveria exigir um script novo. Um manifesto JSON
# descreve endereco/esperado/novo, e a mesma guarda do `Patch` vale para todos.

def _como_bytes(valor, campo: str) -> bytes:
    """Aceita "c8 00", "c800", [200, 0] ou 200 (u8) -- e devolve bytes."""
    if isinstance(valor, int):
        if not 0 <= valor <= 0xFF:
            raise ErroDePatch(f"{campo}: inteiro solto tem de caber em 1 byte")
        return bytes([valor])
    if isinstance(valor, (list, tuple)):
        try:
            return bytes(valor)
        except ValueError as exc:
            raise ErroDePatch(f"{campo}: {exc}") from exc
    texto = str(valor).strip().replace(",", " ")
    if texto.lower().startswith("0x"):
        texto = texto[2:]
    if " " in texto:
        partes = texto.split()
        try:
            return bytes(int(p, 16) for p in partes)
        except ValueError as exc:
            raise ErroDePatch(f"{campo}: byte invalido em {texto!r}") from exc
    try:
        return bytes.fromhex(texto)
    except ValueError as exc:
        raise ErroDePatch(f"{campo}: hex invalido em {texto!r}") from exc


def patches_de_manifesto(manifesto: dict) -> list[Patch]:
    """Converte o JSON em `Patch`, recusando sobreposicao e campo faltando."""
    itens = manifesto.get("patches")
    if not itens:
        raise ErroDePatch("manifesto sem a lista 'patches'")
    patches: list[Patch] = []
    for indice, item in enumerate(itens):
        for campo in ("endereco", "esperado", "novo", "motivo"):
            if campo not in item:
                raise ErroDePatch(f"patch #{indice} sem o campo {campo!r}")
        endereco = item["endereco"]
        if isinstance(endereco, str):
            endereco = int(endereco, 16)
        patches.append(Patch(
            endereco=int(endereco),
            esperado=_como_bytes(item["esperado"], f"patch #{indice} esperado"),
            novo=_como_bytes(item["novo"], f"patch #{indice} novo"),
            motivo=str(item["motivo"]),
        ))
    ordenados = sorted(patches, key=lambda p: p.endereco)
    for anterior, seguinte in zip(ordenados, ordenados[1:]):
        fim = anterior.endereco + len(anterior.esperado)
        if seguinte.endereco < fim:
            raise ErroDePatch(
                f"patches sobrepostos: 0x{anterior.endereco:08X}..0x{fim:08X} e "
                f"0x{seguinte.endereco:08X} -- aplicar um desfaria o outro")
    return patches


def aplicar_manifesto(imagem: bytes, manifesto: dict) -> tuple[bytes, list[Patch]]:
    """Aplica o manifesto e devolve (imagem nova, patches) -- cabecalho incluso."""
    patches = patches_de_manifesto(manifesto)
    return corrigir_cabecalho(aplicar(imagem, patches)), patches
