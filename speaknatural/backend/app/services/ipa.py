"""Inventario IPA do ingles, tokenizacao e tabela de sons "parecidos".

Por que este arquivo existe
---------------------------
O modelo wav2vec2 devolve uma STRING de simbolos IPA (ex.: "ˈkʌpələv").
Precisamos comparar simbolo por simbolo, entao tokenizamos a string em
fonemas. Isso exige conhecer os simbolos de varios caracteres (tʃ, dʒ, aɪ,
oʊ, iː, ɚ...) - senao "tʃ" viraria dois fonemas "t" e "ʃ" e a conta ficaria
errada.

Aqui tambem fica a tabela de CONFUSOES PROXIMAS: sons diferentes mas que um
falante de portugues troca com frequencia. Elas valem nota PARCIAL (nao zero),
exatamente como pedido no escopo.
"""

from __future__ import annotations

from ..config import NEAR_SOUND_SCORE

# ---------------------------------------------------------------------------
# Simbolos IPA usados pelo ingles (espeak-ng en-us + wav2vec2 espeak)
# Ordem irrelevante: a tokenizacao ordena por tamanho.
# ---------------------------------------------------------------------------
IPA_SYMBOLS: tuple[str, ...] = (
    # vogais e ditongos
    "iː", "ɪ", "eɪ", "ɛ", "æ", "ɑː", "ɑ", "ɒ", "ɔː", "ɔ", "oʊ", "ʊ", "uː",
    "ʌ", "ə", "ɚ", "ɝ", "ɜː", "ɜ", "aɪ", "aʊ", "ɔɪ", "ɪə", "ɛə", "ʊə",
    "e", "ᵻ", "ɨ", "ɐ", "ɘ", "o", "a", "u", "i", "y", "ø", "œ", "ɵ", "ɞ", "ɯ",
    # consoantes
    "p", "b", "t", "d", "k", "ɡ", "f", "v", "θ", "ð", "s", "z", "ʃ", "ʒ",
    "h", "tʃ", "dʒ", "m", "n", "ŋ", "l", "ɹ", "r", "ɾ", "ʔ", "w", "j", "ç",
    "x", "ʍ", "ɫ", "ɬ", "β", "ɣ", "ɲ", "ʎ", "ɟ", "c", "q", "ɢ", "ʀ", "ʁ",
)

#: Marcas que NAO sao fonemas e podem ser descartadas.
_STRESS_MARKS = "\u02c8\u02cc"  # ˈ ˌ
_DIACRITICS = "\u0329\u031f\u033a\u0303\u031e\u0318"  # ̩ ̟ ̺ ̃ ̞ ̘

#: Normalizacao de simbolos equivalentes entre motores (espeak x wav2vec2).
_CANON = {
    "g": "ɡ",   # g latino -> ɡ IPA (sao o mesmo som)
    "r": "ɹ",   # r ingles aproximante -> ɹ
    "ɜ": "ɜː",  # espeak as vezes sem a marca de duracao
    "e": "ɛ",   # ingles nao usa /e/ puro
    "i": "iː",  # CMU/eng_to_ipa escreve /i/ sem a marca de duracao
    "u": "uː",
    "ɔ": "ɔː",
    "o": "oʊ",
    "ɑ": "ɑː",
    "ᵻ": "ɪ",
    "ɨ": "ɪ",
}

# ---------------------------------------------------------------------------
# Tabela de sons proximos -> nota parcial
# ---------------------------------------------------------------------------
# A chave e um par (ordenado alfabeticamente) e o valor e a nota que damos
# quando o aluno produz um som no lugar do outro. Pensado para brasileiros:
_NEAR_PAIRS: dict[tuple[str, str], float] = {
    # vogais
    ("i", "ɪ"): 0.70, ("iː", "ɪ"): 0.65,           # sit / seat
    ("iː", "ɪə"): 0.55,
    ("ə", "ʌ"): 0.60, ("ə", "ɚ"): 0.65, ("ɚ", "ɝ"): 0.70, ("ə", "ɐ"): 0.55,
    ("æ", "ɛ"): 0.60, ("æ", "e"): 0.50, ("ɛ", "eɪ"): 0.45,
    ("ɑː", "ʌ"): 0.50, ("ɑː", "ɔː"): 0.55, ("ɔː", "oʊ"): 0.55, ("oʊ", "ɔː"): 0.55,
    ("ʊ", "uː"): 0.60, ("uː", "ʊ"): 0.60, ("ɔ", "ɑː"): 0.50,
    ("eɪ", "ɛ"): 0.50, ("aɪ", "eɪ"): 0.40, ("aʊ", "ɔː"): 0.40, ("ɔɪ", "aɪ"): 0.40,
    # consoantes: vozeamento (p/b, t/d, k/ɡ, f/v, s/z, ʃ/ʒ)
    ("p", "b"): 0.55, ("t", "d"): 0.55, ("k", "ɡ"): 0.55,
    ("f", "v"): 0.55, ("s", "z"): 0.55, ("ʃ", "ʒ"): 0.55,
    ("tʃ", "dʒ"): 0.55,
    # TH (θ/ð) - erro classico de brasileiro
    ("θ", "t"): 0.45, ("θ", "s"): 0.45, ("θ", "f"): 0.40,
    ("ð", "d"): 0.45, ("ð", "z"): 0.45, ("ð", "v"): 0.40,
    # flap norte-americano (water = /ˈwɔɾɚ/)
    ("t", "ɾ"): 0.60, ("d", "ɾ"): 0.60, ("ɾ", "ɹ"): 0.45,
    # T glotal (button = /ˈbʌʔn̩/)
    ("t", "ʔ"): 0.55,
    # R e L
    ("ɹ", "r"): 0.60, ("l", "ɹ"): 0.50, ("l", "ɫ"): 0.70, ("ɹ", "w"): 0.45,
    ("d", "dʒ"): 0.45, ("t", "tʃ"): 0.45,
    # nasal e final -ing
    ("n", "ŋ"): 0.55, ("m", "n"): 0.45, ("ŋ", "n"): 0.55,
    # H e W/J aspirados
    ("h", "x"): 0.50, ("w", "v"): 0.50, ("j", "dʒ"): 0.40,
    ("ʃ", "tʃ"): 0.50, ("s", "ʃ"): 0.50, ("z", "ʒ"): 0.50,
}

#: Indice com as duas ordens do par ("iː","ɪ") e ("ɪ","iː"), porque o
#: simbolo esperado pode chegar em qualquer ordem. Evita erro de consulta.
_NEAR_LOOKUP: dict[tuple[str, str], float] = {}
for (_a, _b), _value in _NEAR_PAIRS.items():
    _NEAR_LOOKUP[(_a, _b)] = _value
    _NEAR_LOOKUP[(_b, _a)] = _value

#: Nota dada quando dois simbolos sao do mesmo "tipo" (vogal x vogal /
#: consoante x consoante) mas nao estao na tabela acima. Um erro de vogal
#: ainda preserva o ritmo da palavra, entao vale pouco (0.30).
SAME_CLASS_SCORE_VOWEL = 0.30
SAME_CLASS_SCORE_CONSONANT = 0.20

_VOWELS = frozenset({
    "iː", "ɪ", "eɪ", "ɛ", "æ", "ɑː", "ɒ", "ɔː", "oʊ", "ʊ", "uː", "ʌ", "ə",
    "ɚ", "ɝ", "ɜː", "aɪ", "aʊ", "ɔɪ", "ɪə", "ɛə", "ʊə", "ɐ", "ɨ", "a", "i",
    "u", "y", "ø", "œ", "ɵ", "ɞ", "ɯ", "o", "e",
})

#: Tamanhos usados na tokenizacao (maior primeiro).
_BY_LENGTH: tuple[str, ...] = tuple(sorted(IPA_SYMBOLS, key=len, reverse=True))


def strip_marks(text: str) -> str:
    """Remove acentos de tonicidade/diacriticos: "ˈkʌpəl" -> "kʌpəl"."""
    for mark in _STRESS_MARKS + _DIACRITICS:
        text = text.replace(mark, "")
    return text.strip()


def canonical(symbol: str) -> str:
    """Unifica grafias equivalentes e remove marcas residuais."""
    symbol = strip_marks(symbol)
    return _CANON.get(symbol, symbol)


def tokenize(ipa_text: str) -> list[str]:
    """Converte uma string IPA em lista de fonemas.

    "ˈkʌpələv"  -> ["k", "ʌ", "p", "ə", "l", "ə", "v"]
    "tʃɪldrən"  -> ["tʃ", "ɪ", "l", "d", "ɹ", "ə", "n"]
    """
    text = strip_marks(ipa_text)
    result: list[str] = []
    i = 0
    while i < len(text):
        for symbol in _BY_LENGTH:
            if text.startswith(symbol, i):
                token = canonical(symbol)
                if token:
                    result.append(token)
                i += len(symbol)
                break
        else:
            # Simbolo desconhecido: ignora espacos e pontuacao, guarda o resto.
            char = text[i]
            if not char.isspace() and char not in "|‖‿.-'":
                result.append(canonical(char))
            i += 1
    return [tok for tok in result if tok]


def is_vowel(symbol: str) -> bool:
    return symbol in _VOWELS


def phoneme_similarity(expected: str, heard: str) -> float:
    """Nota 0..1 de quao parecido o som ouvido e do esperado.

    1.0  = som identico
    0.65 = confusao tipica (ex.: ɪ em vez de iː)  <- nota PARCIAL
    0.30 = outra vogal (ritmo preservado)
    0.20 = outra consoante
    0.0  = nada a ver / som ausente (tratado no alinhamento)
    """
    a, b = canonical(expected), canonical(heard)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    near = _NEAR_LOOKUP.get((a, b))
    if near is not None:
        # NEAR_SOUND_SCORE permite calibrar tudo de uma vez pelo .env
        return min(1.0, near * (NEAR_SOUND_SCORE / 0.65))
    if is_vowel(a) and is_vowel(b):
        return SAME_CLASS_SCORE_VOWEL
    if not is_vowel(a) and not is_vowel(b):
        return SAME_CLASS_SCORE_CONSONANT
    return 0.0


def join_phonemes(phonemes: list[str]) -> str:
    """Junta fonemas para exibir na tela (com espaco, mais legivel no celular)."""
    return " ".join(phonemes)
