"""Codificar e decodificar o texto do jogo (charset medido na secao 9.5).

Motivo: patch de texto e' patch de DADO -- nao da' para provar por emulacao que
"a tela mostra", mas da' para provar que os bytes gravados decodificam no texto
que se quis escrever, com a mesma tabela que decodificou quatro strings
conhecidas da ROM.

Tabela (medida, nao chutada):

    A-Z  0xBB-0xD4      a-z  0xD5-0xEE      0x00 espaco
    0xAB '!'   0xAC '?'   0xAD '.'   0xB8 ','
    0x1B 'e' com acento agudo (e')   0x17 'a' agudo   0x1C 'e' circunflexo
    0xF4 'a' til       0xFE quebra de linha      0xFF fim da string

O `0xFF` termina: tudo depois dele e' lixo e nao deve ser lido.
"""

from __future__ import annotations

ACENTOS = {
    "\u00e9": 0x1B,   # é
    "\u00e1": 0x17,   # á
    "\u00ea": 0x1C,   # ê
    "\u00e3": 0xF4,   # ã
    "!": 0xAB,
    "?": 0xAC,
    ".": 0xAD,
    ",": 0xB8,
    " ": 0x00,
}
PONTUACAO = {valor: chave for chave, valor in ACENTOS.items()}
FIM = 0xFF
QUEBRA = 0xFE


def codificar(texto: str, terminador: bool = True) -> bytes:
    """Converte texto para os bytes do jogo.

    `terminador=True` acrescenta o 0xFF. Caractere fora da tabela e' erro, nao
    interrogancia silenciosa: um patch que grava `?` no lugar da letra e' pior
    que um patch que se recusa a rodar.
    """
    saida = bytearray()
    for posicao, caractere in enumerate(texto):
        if "A" <= caractere <= "Z":
            saida.append(0xBB + ord(caractere) - ord("A"))
        elif "a" <= caractere <= "z":
            saida.append(0xD5 + ord(caractere) - ord("a"))
        elif "\n" == caractere:
            saida.append(QUEBRA)
        elif caractere in ACENTOS:
            saida.append(ACENTOS[caractere])
        else:
            raise ValueError(
                f"caractere {caractere!r} na posicao {posicao} nao esta' na "
                f"tabela medida do charset")
    if terminador:
        saida.append(FIM)
    return bytes(saida)


def decodificar(dados: bytes, parar_no_fim: bool = True) -> str:
    """Converte bytes do jogo para texto, parando no 0xFF (por padrao)."""
    saida = []
    for byte in dados:
        if byte == FIM and parar_no_fim:
            break
        if byte == QUEBRA:
            saida.append("\n")
        elif byte == 0x00:
            saida.append(" ")
        elif 0xBB <= byte <= 0xD4:
            saida.append(chr(ord("A") + byte - 0xBB))
        elif 0xD5 <= byte <= 0xEE:
            saida.append(chr(ord("a") + byte - 0xD5))
        elif byte in PONTUACAO:
            saida.append(PONTUACAO[byte])
        else:
            saida.append(f"\\x{byte:02X}")
    return "".join(saida)


def caber(texto: str, campo: int) -> bytes:
    """Bytes de `texto` preenchendo um campo de `campo` bytes (0xFF no resto).

    0xFF e' terminador e tambem preenchimento: o jogo para no primeiro.
    """
    bytes_texto = codificar(texto)
    if len(bytes_texto) > campo:
        raise ValueError(
            f"{texto!r} ocupa {len(bytes_texto)} bytes (com terminador) e o campo "
            f"tem {campo}")
    return bytes_texto + b"\xFF" * (campo - len(bytes_texto))
