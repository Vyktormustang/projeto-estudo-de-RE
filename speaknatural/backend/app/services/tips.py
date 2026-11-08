"""Dicas em portugues para cada som.

Duas coisas aparecem na tela do app:
  * a dica do som errado  -> `phoneme_tip(expected, heard, score)`
  * a dica da palavra     -> `word_tip(...)` (o que fazer com a palavra toda)

Tudo escrito em linguagem de conversa, sem jargao de fonetica. Se voce for
adicionar um som novo em ipa.py, coloque a dica aqui tambem.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Nome/curiosidade de cada simbolo IPA (usado quando nao ha par especifico)
# ---------------------------------------------------------------------------
PHONEME_INFO: dict[str, str] = {
    # vogais
    "iː": "/iː/ longo, como em “see” — sorria e segure o som.",
    "ɪ": "/ɪ/ curto e relaxado, como em “sit” — não estique.",
    "eɪ": "/eɪ/ como em “day” — deslize de “ê” para “i”.",
    "ɛ": "/ɛ/ aberto, como em “bed”.",
    "æ": "/æ/ muito aberto, entre “é” e “á”, como em “cat”.",
    "ɑː": "/ɑː/ como em “father” — boca bem aberta, som longo.",
    "ɔː": "/ɔː/ como em “saw” — lábios arredondados.",
    "oʊ": "/oʊ/ como em “go” — desliza de “ô” para “u”.",
    "ʊ": "/ʊ/ curto, como em “book”.",
    "uː": "/uː/ longo, como em “food” — lábios bem para frente.",
    "ʌ": "/ʌ/ como em “cup” — som curto no centro da boca (parecido com “â”).",
    "ə": "/ə/ é o som mais fraco do inglês (“about”) — quase um “â” relaxado.",
    "ɚ": "/ɚ/ como o “er” final de “water” (sotaque americano).",
    "ɝ": "/ɝ/ “er” tônico, como em “bird”.",
    "aɪ": "/aɪ/ como em “my” — de “á” para “i”.",
    "aʊ": "/aʊ/ como em “now” — de “á” para “u”.",
    "ɔɪ": "/ɔɪ/ como em “boy”.",
    # consoantes
    "θ": "/θ/ de “think”: língua ENTRE os dentes, soprando (não é /t/ nem /f/).",
    "ð": "/ð/ de “this”: língua entre os dentes, vibrando (não é /d/ nem /v/).",
    "ɹ": "/ɹ/ de “red”: língua perto do céu da boca sem tocar, lábios um pouco para frente.",
    "r": "/ɹ/ americano: não bata a língua como no “r” de “caro”.",
    "l": "/l/ de “like”: ponta da língua nos dentes de cima.",
    "ɫ": "/l/ escuro (fim de sílaba, “full”): língua mais para trás.",
    "ɾ": "/ɾ/ é o “t/d” suave de “water/butter” (como o “r” de “careta”).",
    "ʔ": "/ʔ/ é um “t” cortado na garganta, como em “button”.",
    "ŋ": "/ŋ/ de “sing”: som no fundo, sem “g” depois.",
    "ʃ": "/ʃ/ de “she” — como o “ch” de “chave”.",
    "ʒ": "/ʒ/ de “measure” — como o “j” de “janela”, mais suave.",
    "tʃ": "/tʃ/ de “cheap” — como o “tch” de “tchau”.",
    "dʒ": "/dʒ/ de “job” — como o “dj” de “dia” falado rápido.",
    "v": "/v/ de “very”: dentes de cima no lábio de baixo, vibrando.",
    "w": "/w/ de “we”: lábios arredondados, sem encostar os dentes.",
    "j": "/j/ de “yes”: como o “i” de “iate”.",
    "h": "/h/ de “hello”: só ar, sem raspar a garganta.",
    "z": "/z/ de “zoo”: vibra como o “z” de “casa”.",
    "s": "/s/ de “see”: não vira “z” no fim das palavras.",
    "p": "/p/ com um sopro de ar no fim (no inglês o p é aspirado).",
    "t": "/t/ com sopro de ar; no meio da palavra pode virar /ɾ/.",
    "k": "/k/ com sopro de ar.",
    "b": "/b/ com mais força que em português.",
    "d": "/d/ com a língua nos dentes de cima, não no céu da boca.",
    "ɡ": "/ɡ/ de “go”, sempre duro.",
}

# ---------------------------------------------------------------------------
# Trocas tipicas de brasileiros -> explicacao personalizada
# ---------------------------------------------------------------------------
TIPS_BY_PAIR: dict[tuple[str, str], str] = {
    ("iː", "ɪ"): "Você fez o som curto /ɪ/. Aqui o esperado é /iː/ longo: sorria e segure (compare “sit” x “seat”).",
    ("i", "ɪ"): "Faltou esticar: o /iː/ é mais longo e mais fechado que o /ɪ/.",
    ("ə", "ʌ"): "O /ə/ é o som fraco de sílaba não acentuada. Não coloque força: diga quase “â” com a boca relaxada.",
    ("ɚ", "ə"): "No fim de palavra (water, teacher) o americano usa /ɚ/, com um “r” leve. Sem o /r/ soa estrangeiro.",
    ("æ", "ɛ"): "Abra mais a boca: /æ/ fica entre o “é” e o “á” (cat, bad).",
    ("ɛ", "eɪ"): "Não deslize: aqui é um /ɛ/ curto, sem virar “ei”.",
    ("ʌ", "ɑː"): "O /ʌ/ é curto e no centro da boca; /ɑː/ é longo e aberto.",
    ("uː", "ʊ"): "Arredonde mais os lábios e segure o som (/uː/ x /ʊ/).",
    ("ʊ", "uː"): "Aqui o som é curto: não estique nem arredonde demais.",
    ("oʊ", "ɔː"): "O /oʊ/ tem um deslize no fim (“ou”). O /ɔː/ é um “ó” parado.",
    ("θ", "t"): "Cuidado: não é /t/. Coloque a ponta da língua entre os dentes e sopre (think, thing).",
    ("θ", "s"): "Não é /s/. Língua entre os dentes, ar saindo por cima dela (think).",
    ("θ", "f"): "Não é /f/. O /θ/ usa a língua nos dentes, não o lábio (three).",
    ("ð", "d"): "Não é /d/. Língua entre os dentes vibrando (this, mother).",
    ("ð", "z"): "Quase isso: o /ð/ é o “z” feito com a língua entre os dentes.",
    ("ð", "v"): "Não é /v/. Use a língua entre os dentes, não o lábio (brother).",
    ("ɹ", "r"): "Não bata a língua (como no “r” de “caro”). A língua fica perto do céu da boca, sem encostar.",
    ("ɹ", "w"): "Não arredonde os lábios como /w/; o /ɹ/ é feito com a língua.",
    ("l", "ɹ"): "Esse é /l/: a ponta da língua encosta nos dentes de cima.",
    ("ɾ", "t"): "Ótimo: aqui o “t” americano é justamente esse /ɾ/ suave. Você já faz isso em português.",
    ("t", "ɾ"): "No inglês americano esse /t/ entre vogais vira /ɾ/ (water). Se você fez /t/ forte, soa estrangeiro.",
    ("n", "ŋ"): "No fim de -ing use /ŋ/ (som no fundo da boca), sem terminar com /n/.",
    ("ŋ", "n"): "Aqui o /ŋ/ é mais grave: a parte de trás da língua encosta no céu da boca (sing).",
    ("ʃ", "tʃ"): "Sem o “t”: /ʃ/ é só o chiado (she), não “tch”.",
    ("tʃ", "ʃ"): "Faltou o “t” antes: /tʃ/ é “tch” (cheap).",
    ("dʒ", "ʒ"): "Faltou o “d”: /dʒ/ é “dj” (job).",
    ("w", "v"): "Não encoste os dentes no lábio: /w/ é só lábios arredondados.",
    ("v", "w"): "Aqui é /v/: dentes de cima no lábio de baixo, vibrando.",
    ("p", "b"): "Som surdo: /p/ sem vibração na garganta.",
    ("b", "p"): "Som sonoro: /b/ com vibração na garganta.",
    ("t", "d"): "Som surdo: /t/ sem vibração.",
    ("d", "t"): "Som sonoro: /d/ com vibração.",
    ("k", "ɡ"): "Som surdo: /k/ sem vibração.",
    ("ɡ", "k"): "Som sonoro: /ɡ/ com vibração.",
    ("s", "z"): "Aqui é /s/ surdo, sem vibrar (see, this).",
    ("z", "s"): "Aqui é /z/ sonoro, vibrando (zoo, is).",
    ("f", "v"): "Som surdo: /f/ sem vibração no lábio.",
    ("h", "x"): "O /h/ inglês é só ar, sem raspar a garganta como o “rr” do português.",
}

#: Indice do dicionario acima com as duas ordens (esperado/ouvido pode chegar
#: em qualquer ordem). Construido uma vez, na importacao.
_TIP_LOOKUP: dict[tuple[str, str], str] = {}
for (_expected, _heard), _tip in TIPS_BY_PAIR.items():
    _TIP_LOOKUP.setdefault((_expected, _heard), _tip)
    _TIP_LOOKUP.setdefault((_heard, _expected), _tip)

# Dicas para sons que simplesmente NAO apareceram ou sobraram
MISSING_TIP = "Esse som não apareceu na sua fala. Diminua a velocidade e pronuncie cada som da palavra."
EXTRA_TIP = "Você falou um som a mais aqui. Tente juntar os sons sem acrescentar vogal (por exemplo, “sp” sem “espi”)."


def phoneme_tip(expected: str | None, heard: str | None, score: float) -> str:
    """Dica curta para um par de fonemas."""
    if expected and heard and expected == heard:
        return ""
    if expected is None:
        return EXTRA_TIP
    if heard is None:
        base = PHONEME_INFO.get(expected, "")
        return f"{MISSING_TIP} {base}".strip()

    tip = _TIP_LOOKUP.get((expected, heard))
    if tip is None:
        info = PHONEME_INFO.get(expected or "", "")
        if score >= 0.5:
            tip = f"Quase certo. {info}".strip()
        else:
            tip = f"O esperado aqui é {info}".strip()
    return tip


def word_tip(
    word: str,
    score: float,
    presence: float,
    worst: tuple[str | None, str | None] | None = None,
) -> str:
    """Dica para a palavra inteira (mostrada no cartao da palavra)."""
    if presence <= 0.0:
        return f"“{word}” não apareceu na sua leitura. Leia a frase devagar para não pular palavras."
    if score >= 0.85:
        return f"“{word}” ficou muito bom. Siga assim."
    if worst:
        expected, heard = worst
        detail = phoneme_tip(expected, heard, 0.0 if expected is None or heard is None else 0.5)
        if detail:
            return detail
    if score >= 0.5:
        return f"“{word}” está no caminho. Repita devagar, exagerando o som mais difícil."
    return f"“{word}” precisa de atenção. Ouça a referência e repita em voz alta três vezes."
