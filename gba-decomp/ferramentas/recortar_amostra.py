#!/usr/bin/env python3
"""Recorta uma AMOSTRA do C levantado, com script -- para a evidencia ser refeita.

Por que existe: a amostra em `evidencias/rom_bpre_amostra_levantada.c` dizia, no
cabecalho, numeros medidos (funcoes, instrucoes, taxa de remontagem, objeto) e
mostrava trechos escolhidos a mao. Isso tem dois defeitos praticos:

  1. os numeros do cabecalho eram digitados -- bastava uma rodada nova para o
     cabecalho ficar contando uma medicao que nao e' a do arquivo ao lado;
  2. um trecho "escolhido a mao" nao pode ser refeito por quem le o repositorio,
     entao nao serve de evidencia -- so de ilustracao.

Agora os dois vem do proprio material: os numeros, do JSON que o `cli analisar`
gravou; os trechos, de um recorte que qualquer pessoa roda com o mesmo comando.
O cut da esquerda e o da direita sao os mesmos em qualquer maquina, porque o
recorte e' por linha (nao por byte) e o `.c` de entrada e' deterministico.

Uso (o comando exato esta no README):

    python ferramentas/recortar_amostra.py levantado_rom.c \\
        --analise evidencias/rom_bpre_analise.json \\
        --caso 0x080011E4 "tabela de casos lida da ROM virou switch" \\
        --caso 0x08014040 "desvio para tras: a leitura sai da janela antiga" \\
        --caso 0x081DC45A "bx rN recusado, com o motivo dito por inteiro" \\
        --orcamento 150 --saida evidencias/rom_bpre_amostra_levantada.c

Nada e' editado dentro dos trechos: o que aparece esta byte a byte como no
arquivo inteiro, e o que foi cortado esta declarado no proprio lugar do corte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ATRIBUTO = "__attribute__(("


def nome_da_definicao(linha: str) -> str:
    """`__attribute__((noinline, used)) u32 FUN_080011e4(u32 r0, ...) {` -> FUN_080011e4.

    O tipo de retorno vai entre o atributo e o nome, entao nao da' para pegar o
    nome "logo depois do atributo": pega-se o identificador antes do primeiro
    parentese.
    """
    if not linha.startswith(ATRIBUTO):
        return ""
    resto = linha.split("))", 1)[-1]
    parentese = resto.find("(")
    if parentese < 0:
        return ""
    palavras = resto[:parentese].split()
    return palavras[-1] if palavras else ""


def _marcador(quantidade: int) -> str:
    """Uma LINHA so'. Um marcador multi-linha (com barra invertida de continuacao)
    ja' saiu daqui torto: o comando do cabecalho entrou no meio do texto e o `*/`
    so' fechava duas linhas depois -- C valido, mas ilegivel e facil de quebrar de
    verdade na proxima edicao."""
    return (f"    /* ... {quantidade} linhas omitidas AQUI para a amostra caber; "
            f"a funcao inteira esta no .c levantado do comando do cabecalho */")


def comentarios_balanceados(texto: str) -> None:
    """Verifica que nenhuma linha deixou um comentario aberto sem fechar.

    Pega o defeito que ja' aconteceu aqui: texto de marcador com quebra de linha
    dentro, que empurra o `*/` para depois e faz o recorte parecer comentario
    aberto. Se abrir, tem de fechar -- na MESMA linha ou nas seguintes; o que
    nao pode e' terminar o arquivo ainda dentro de um comentario.
    """
    if texto.count("/*") != texto.count("*/"):
        raise SystemExit(f"amostra com comentario desbalanceado: "
                         f"{texto.count('/*')} `/*` para {texto.count('*/')} `*/`")


def achar_bloco(linhas: list[str], endereco: int) -> tuple[int, int, str]:
    """Acha o bloco (inicio, fim, nome) da funcao cujo ENDERECO e' o de entrada.

    Ancora: a linha `/* origem: 0xADDR (modo), ... */` que o lifter escreve
    imediatamente antes de cada definicao -- e' a unica que diz qual JANELA a
    funcao e' (o mesmo endereco pode aparecer como instrucao de outra janela).
    O bloco vai dessa linha (mais os comentarios colados nela) ate' o `}` que
    fecha a definicao.
    """
    procurado = f"/* origem: 0x{endereco:08X} "
    for indice, linha in enumerate(linhas):
        if not linha.startswith(procurado):
            continue
        # Sobe pelo cabecalho colado: `/* chamada por ... */`, `/* origem: ... */` e o
        # bloco `/* PARCIAL ... */` (que tem linhas de motivo no meio, SEM `/*` no
        # comeco -- foi por isso que a primeira versao deste recorte perdia o
        # proprio motivo da lacuna). A regra e' "linha nao vazia": o gerador separa
        # funcoes com UMA linha em branco, entao a linha em branco e' o corte exato
        # -- e nunca engole o corpo da funcao anterior, que fica acima dela.
        inicio = indice
        while inicio > 0 and linhas[inicio - 1].strip():
            inicio -= 1
        for fim in range(indice, len(linhas)):
            if linhas[fim] == "}":
                nome = ""
                for meio in range(indice, fim):
                    achado = nome_da_definicao(linhas[meio])
                    if achado:
                        nome = achado
                        break
                return inicio, fim + 1, nome
        raise SystemExit(f"bloco de 0x{endereco:08X} comeca e nao fecha")
    raise SystemExit(f"nao achei funcao com entrada 0x{endereco:08X} no C levantado")


def fim_do_cabecalho(linhas: list[str], inicio: int, fim: int) -> int:
    """Indice (exclusivo) onde terminam os comentarios colados na definicao.

    Necessario porque cortar o bloco no meio do `/* PARCIAL ... */` deixaria o
    `*/` do outro lado do corte: comentario aberto ate' o fim do arquivo. O
    cabecalho e' curto (4-6 linhas), entao o corte comeca DEPOIS dele, sempre.
    """
    aberto = False
    limite = inicio
    for indice in range(inicio, fim):
        linha = linhas[indice]
        if aberto:
            limite = indice + 1
            if "*/" in linha:
                aberto = False
            continue
        if not linha.lstrip().startswith("/*"):
            break
        limite = indice + 1
        aberto = "*/" not in linha
    return limite


def recortar(linhas: list[str], inicio: int, fim: int, orcamento: int) -> list[str]:
    """Encurta o bloco para caber `orcamento` linhas, declarando o que tirou."""
    if fim - inicio <= orcamento:
        return linhas[inicio:fim]
    # cabeca com o cabecalho e o comeco do corpo; cauda com o FIM da funcao (o
    # fecho e' justamente o que mostra que a funcao termina, com o retorno).
    sobra = orcamento - 1
    tamanho_cabeca = max(sobra * 2 // 3, fim_do_cabecalho(linhas, inicio, fim) - inicio)
    tamanho_cauda = sobra - tamanho_cabeca
    if tamanho_cauda < 1:
        raise SystemExit(
            f"orcamento {orcamento} pequeno demais para este bloco: so' o cabecalho "
            f"de comentarios tem {tamanho_cabeca} linhas")
    cabeca = linhas[inicio:inicio + tamanho_cabeca]
    cauda = linhas[fim - tamanho_cauda:fim]
    return cabeca + [_marcador(fim - inicio - sobra)] + cauda


def cabecalho(analise: dict, caminho_c: Path, linhas: list[str], casos: list,
              comando_analise: str) -> list[str]:
    """Monta o cabecalho a partir do JSON -- nenhum numero digitado a mao."""
    lev = analise["levantamento"]
    desc = analise["completo"]
    conf = analise["conferencia"]
    comp = analise["compilacao"]
    boot = analise["boot"]
    conferencia_ok = f"{conf['identicas']}/{conf['total']} ({conf['taxa']}%)"
    sha = hashlib.sha256(caminho_c.read_bytes()).hexdigest()
    linhas_cabecalho = [
        "/* ============================================================================",
        "   AMOSTRA do C levantado da ROM real -- Pokemon Fire Red BR (BPRE).",
        "",
        "   A ROM NAO esta no repositorio: e' imagem de terceiros (16 MB), e o",
        "   arquivo inteiro e' reproduzivel com o comando abaixo. Este cabecalho e",
        "   os recortes que seguem saem de `ferramentas/recortar_amostra.py`: os",
        "   numeros vem do JSON da rodada, os trechos do .c dessa mesma rodada --",
        "   nada aqui e' digitado a mao, entao a amostra pode ser refeita:",
        "",
        f"     {comando_analise}",
        f"     sha256 do .c levantado: {sha[:32]}...",
        f"     sha256 da ROM ........: {analise['sha256']}",
        "",
        "   Estado medido (tudo em evidencias/rom_bpre_analise.json, gerado por",
        "   esse comando nesta rodada):",
        f"     descoberta .........: {desc['funcoes']} funcoes,",
        f"                          {desc['instrucoes']} instrucoes listadas,",
        f"                          {desc['arestas']} arestas de chamada,",
        f"                          {desc['descartes']} enderecos descartados",
        f"     censo do projeto ...: {desc['no_censo']}/{analise['censo_funcoes']}"
        f" ({100.0 * desc['no_censo'] / analise['censo_funcoes']:.1f}% das funcoes"
        " do censo)",
        f"     fora do censo ......: {desc['fora_do_censo']} funcoes que o censo nao tinha",
        f"     tabelas de casos ...: {desc['tabelas_de_casos']} reconhecidas,",
        f"                          {desc['casos_de_tabela']} casos lidos da ROM",
        f"     saltos para tras ...: {desc['saidas_para_tras']} saidas de funcao;",
        f"                          {desc['saidas_recuperadas']} trechos orfaos",
        "                          recuperados como janela propria",
        f"     com C para ler .....: {lev['completas']} completas + "
        f"{lev['parciais']} parciais",
        f"                          ({lev['percentual_com_c']}% com C)",
        f"     C ..................: {analise['linhas_c']} linhas / "
        f"{analise['bytes_c']} bytes",
        f"     conferencia bytes ..: {conferencia_ok} remontam identicas ao",
        f"                          binario; {conf['divergentes']} divergencias,"
        f" {conf['nao_remontadas']} fora da sintaxe",
        f"     compilacao .........: {'OK' if comp['compila'] else 'FALHOU'}, "
        f"{comp['n_erros']} erros",
        f"                          (objeto ARM de {comp['bytes_objeto']} bytes, sha256",
        f"                          {comp['sha256_objeto'][:16]}...)",
        f"     boot so' (ARM/Thumb): {boot['funcoes']} funcoes alcancadas pelo vetor",
        "                          de reset (o resto vem do censo)",
        "",
        "   O que isto NAO prova: semantica. Sem verdade-terreno nesta ROM, o que",
        "   se prova e' que cada instrucao remonta byte a byte e que o C compila --",
        "   comportamento so' esta provado no corpus sintetico (emulando o binario",
        "   E o C levantado recompilado). As funcoes com lacuna trazem a lacuna",
        "   MARCADA dentro do proprio C, com endereco e motivo; nada e' silenciado.",
        "",
        "   Cada caso abaixo e' recortado do arquivo inteiro, sem edicao. O que",
        "   esta rodada mostra:",
    ]
    linhas_cabecalho += [f"     - {rotulo}: {nome}" for endereco, rotulo, nome in casos]
    linhas_cabecalho += [
        f"   (o .c inteiro tem {len(linhas)} linhas; os cortes estao marcados no lugar)",
        "   ============================================================================ */",
    ]
    return linhas_cabecalho


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("c_levantado", type=Path, help="arquivo .c que `cli analisar` gerou")
    parser.add_argument("--analise", type=Path, required=True,
                        help="JSON da MESMA rodada (a fonte dos numeros do cabecalho)")
    parser.add_argument("--caso", nargs=2, action="append", default=[], metavar=("END", "ROTULO"),
                        help="endereco da entrada + rotulo, na ordem em que aparecem")
    parser.add_argument("--orcamento", type=int, default=150,
                        help="linhas por caso antes de omitir o meio (padrao 150)")
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--comando-analise", default=None,
                        help="o comando que gerou o .c, como aparece no cabecalho")
    args = parser.parse_args(argv)

    if not args.caso:
        raise SystemExit("informe ao menos um --caso 0xENDERECO \"rotulo\"")
    if args.orcamento < 20:
        raise SystemExit("--orcamento menor que 20 nao mostra cabecalho+corpo util")

    linhas = args.c_levantado.read_text(encoding="utf-8").splitlines()
    analise = json.loads(args.analise.read_text(encoding="utf-8"))
    comando = args.comando_analise or (
        "python -m gbadecomp.cli analisar ROM.gba --censo censo/functions.csv \\\n"
        "            --json evidencias/rom_bpre_analise.json -o levantado_rom.c")

    casos = []
    for texto, rotulo in args.caso:
        endereco = int(texto, 16)
        inicio, fim, nome = achar_bloco(linhas, endereco)
        casos.append((endereco, rotulo, nome))
        print(f"0x{endereco:08X}: {nome} -- linhas {inicio + 1}..{fim} "
              f"({fim - inicio} linhas)")

    saida = cabecalho(analise, args.c_levantado, linhas, casos, comando)
    for endereco, rotulo, nome in casos:
        inicio, fim, _ = achar_bloco(linhas, endereco)
        saida.append("")
        saida.append(f"/* ---------------- {nome} -- {rotulo} ---------------- */")
        saida.append("")
        saida += recortar(linhas, inicio, fim, args.orcamento)
    saida.append("")

    texto = "\n".join(saida) + "\n"
    comentarios_balanceados(texto)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(texto, encoding="utf-8")
    print(f"amostra gravada em {args.saida} ({len(saida)} linhas, "
          f"{args.saida.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
