"""Frases de pratica embutidas (~40), em ingles, separadas por nivel.

Regras usadas ao escrever as frases:
  * fala natural de verdade (contracoes, "gonna", "wanna", "gotta", linking);
  * vocabulario do dia a dia (casa, trabalho, restaurant, viagem);
  * cada frase tem uma "focus": uma dica em portugues do que observar.

Para adicionar frases: copie um dicionario e mude o id (letra do nivel + numero).
Nada mais precisa ser alterado: a API, o frontend e o historico leem daqui.
"""

from __future__ import annotations

from typing import Any

# id: [letra do nivel][2 digitos]  ->  e01..e14 (easy), m01..m14 (medium), h01..h12 (hard)
SENTENCES: list[dict[str, Any]] = [
    # ------------------------------------------------------------------ EASY
    {
        "id": "e01",
        "text": "I wanna grab a coffee.",
        "level": "easy",
        "focus": "\"wanna\" = \"want to\". Fale como uma palavra só: /ˈwɑnə/.",
        "tags": ["gonna/wanna"],
    },
    {
        "id": "e02",
        "text": "How's it going?",
        "level": "easy",
        "focus": "Contração + linking: \"how's it\" soa /haʊzɪt/, tudo junto.",
        "tags": ["contração", "linking"],
    },
    {
        "id": "e03",
        "text": "What are you doing today?",
        "level": "easy",
        "focus": "\"What are you\" vira /ˈwʌtʃə/ na fala rápida.",
        "tags": ["redução"],
    },
    {
        "id": "e04",
        "text": "Can I get a glass of water?",
        "level": "easy",
        "focus": "\"glass of\" liga em /ˈɡlæsəv/; \"water\" nos EUA tem T suave: /ˈwɔɾɚ/.",
        "tags": ["linking", "flap T"],
    },
    {
        "id": "e05",
        "text": "I'm gonna be a little late.",
        "level": "easy",
        "focus": "\"gonna\" /ˈɡʌnə/ e \"little\" com T suave /ˈlɪɾl̩/.",
        "tags": ["gonna/wanna", "flap T"],
    },
    {
        "id": "e06",
        "text": "Thanks a lot for your help.",
        "level": "easy",
        "focus": "/θ/ em \"thanks\": língua entre os dentes, sem sopro de /t/.",
        "tags": ["th"],
    },
    {
        "id": "e07",
        "text": "See you tomorrow morning.",
        "level": "easy",
        "focus": "\"See you\" costuma virar /ˈsiːjə/. Não separe as palavras.",
        "tags": ["linking"],
    },
    {
        "id": "e08",
        "text": "Where are you from?",
        "level": "easy",
        "focus": "\"Where are\" liga no /r/: /ˈwerɑr/. Entonação sobe no fim.",
        "tags": ["linking", "pergunta"],
    },
    {
        "id": "e09",
        "text": "I don't know what to say.",
        "level": "easy",
        "focus": "\"don't know\" vira /ˈdoʊnoʊ/ (o T desaparece).",
        "tags": ["redução"],
    },
    {
        "id": "e10",
        "text": "Let's go for a walk.",
        "level": "easy",
        "focus": "\"go for a\" vira /ˈɡoʊfərə/, tudo emendado.",
        "tags": ["linking"],
    },
    {
        "id": "e11",
        "text": "Do you have a minute?",
        "level": "easy",
        "focus": "\"Do you\" vira /dʒə/ e \"have a\" vira /hævə/.",
        "tags": ["redução", "linking"],
    },
    {
        "id": "e12",
        "text": "It's really nice to meet you.",
        "level": "easy",
        "focus": "\"meet you\" /ˈmiːtʃu/ — o T e o Y se juntam.",
        "tags": ["linking"],
    },
    {
        "id": "e13",
        "text": "I need to check my email.",
        "level": "easy",
        "focus": "\"need to\" vira /ˈniɾə/ na fala natural.",
        "tags": ["redução"],
    },
    {
        "id": "e14",
        "text": "That sounds like a good idea.",
        "level": "easy",
        "focus": "\"like a\" liga em /ˈlaɪkə/; \"good idea\" emenda no /d/.",
        "tags": ["linking"],
    },
    # ---------------------------------------------------------------- MEDIUM
    {
        "id": "m01",
        "text": "I've been working here for almost three years.",
        "level": "medium",
        "focus": "Present perfect contínuo: \"I've been working\" com /v/ bem audível.",
        "tags": ["present perfect", "linking"],
    },
    {
        "id": "m02",
        "text": "Could you pick me up at the airport?",
        "level": "medium",
        "focus": "\"pick me up at the\" emendado: /ˈpɪkmiəpətðə/.",
        "tags": ["phrasal verb", "linking"],
    },
    {
        "id": "m03",
        "text": "She's gonna call you back in a few minutes.",
        "level": "medium",
        "focus": "\"gonna\" + \"call you\" /ˈkɔːljə/ + \"in a\" /ɪnə/.",
        "tags": ["gonna/wanna", "linking"],
    },
    {
        "id": "m04",
        "text": "We should've left earlier, but it's fine.",
        "level": "medium",
        "focus": "\"should've\" = /ˈʃʊdəv/ (nunca \"should of\").",
        "tags": ["contração", "should've"],
    },
    {
        "id": "m05",
        "text": "What do you wanna eat for dinner tonight?",
        "level": "medium",
        "focus": "\"What do you\" vira /ˈwʌdʒə/ na fala rápida.",
        "tags": ["gonna/wanna", "redução"],
    },
    {
        "id": "m06",
        "text": "I'm not sure if I can make it on Friday.",
        "level": "medium",
        "focus": "\"if I\" liga em /ɪfaɪ/ e \"make it\" em /ˈmeɪkɪt/.",
        "tags": ["linking"],
    },
    {
        "id": "m07",
        "text": "Could you speak a little more slowly, please?",
        "level": "medium",
        "focus": "\"speak a\" liga no /k/: /ˈspiːkə/. Cuidado com o /l/ de \"slowly\".",
        "tags": ["linking", "pedido"],
    },
    {
        "id": "m08",
        "text": "He doesn't really like spicy food.",
        "level": "medium",
        "focus": "\"doesn't\" /ˈdʌzənt/ e \"spicy\" /ˈspaɪsi/ — o I é /aɪ/.",
        "tags": ["contração"],
    },
    {
        "id": "m09",
        "text": "I'd rather stay home and watch a movie.",
        "level": "medium",
        "focus": "\"I'd rather\" = preferência: /aɪd ˈræðɚ/. O TH de \"rather\" vibra.",
        "tags": ["would rather", "th"],
    },
    {
        "id": "m10",
        "text": "They're supposed to arrive around eight.",
        "level": "medium",
        "focus": "\"supposed to\" vira /səˈpoʊstə/ — o D some.",
        "tags": ["redução"],
    },
    {
        "id": "m11",
        "text": "I've got a lot of things to do this week.",
        "level": "medium",
        "focus": "\"got a lot of\" emendado; \"things\" com /ŋ/ (não \"thinks\").",
        "tags": ["linking", "ng"],
    },
    {
        "id": "m12",
        "text": "Do you mind if I open the window?",
        "level": "medium",
        "focus": "\"mind if I\" soa /ˈmaɪndɪfaɪ/. Pedido educado.",
        "tags": ["linking", "pedido"],
    },
    {
        "id": "m13",
        "text": "It looks like it's going to rain soon.",
        "level": "medium",
        "focus": "\"going to\" rápido vira \"gonna\" /ˈɡʌnə/.",
        "tags": ["gonna/wanna"],
    },
    {
        "id": "m14",
        "text": "Let me know as soon as you get there.",
        "level": "medium",
        "focus": "\"Let me\" vira /ˈlɛmi/ e \"get there\" perde o T: /ɡɛˈðer/.",
        "tags": ["redução", "linking"],
    },
    # ------------------------------------------------------------------ HARD
    {
        "id": "h01",
        "text": "I would've told you if I'd known about it.",
        "level": "hard",
        "focus": "Terceira condicional: \"would've\" /ˈwʊdəv/ e \"I'd\" /aɪd/ bem curtos.",
        "tags": ["would've", "condicional"],
    },
    {
        "id": "h02",
        "text": "Whatcha gonna do about the broken windshield?",
        "level": "hard",
        "focus": "\"Whatcha\" = \"what are you\" /ˈwʌtʃə/. Fala de rua, muito comum.",
        "tags": ["redução", "gonna/wanna"],
    },
    {
        "id": "h03",
        "text": "She shouldn't've said that in front of everybody.",
        "level": "hard",
        "focus": "\"shouldn't've\" tem 3 pedaços: /ˈʃʊdəntəv/. Vá devagar.",
        "tags": ["contração tripla"],
    },
    {
        "id": "h04",
        "text": "I'm gonna have to think about it for a couple of days.",
        "level": "hard",
        "focus": "\"gonna have to\" = /ˈɡʌnəhæftə/; \"couple of\" = /ˈkʌpələ/.",
        "tags": ["gonna/wanna", "linking"],
    },
    {
        "id": "h05",
        "text": "We could've gone somewhere else, but it turned out fine.",
        "level": "hard",
        "focus": "\"could've\" /ˈkʊdəv/ + \"turned out\" ligado: /tɝndˈaʊt/.",
        "tags": ["could've", "phrasal verb"],
    },
    {
        "id": "h06",
        "text": "They must've forgotten to send us the invitation.",
        "level": "hard",
        "focus": "\"must've\" /ˈmʌstəv/ e \"send us\" /ˈsɛndəs/.",
        "tags": ["contração", "linking"],
    },
    {
        "id": "h07",
        "text": "You'd better get used to driving in heavy traffic.",
        "level": "hard",
        "focus": "\"get used to\" tem /juːst/ (S com som de S, não de Z).",
        "tags": ["used to"],
    },
    {
        "id": "h08",
        "text": "I didn't wanna bother you while you were working.",
        "level": "hard",
        "focus": "\"didn't wanna\" e \"while you were\" com /w/ bem redondo.",
        "tags": ["gonna/wanna", "linking"],
    },
    {
        "id": "h09",
        "text": "Honestly, I don't think it's worth the trouble.",
        "level": "hard",
        "focus": "/θ/ em \"think\" e \"worth\": língua entre os dentes.",
        "tags": ["th"],
    },
    {
        "id": "h10",
        "text": "He's been trying to get ahold of you all morning.",
        "level": "hard",
        "focus": "\"trying to\" vira /ˈtraɪnə/ e \"get ahold of\" emenda todo.",
        "tags": ["redução", "linking"],
    },
    {
        "id": "h11",
        "text": "If I were you, I'd take the earlier train.",
        "level": "hard",
        "focus": "Condicional com \"were\": /ɪf aɪ wɚ ju/. Não fale \"was\".",
        "tags": ["condicional"],
    },
    {
        "id": "h12",
        "text": "That's exactly what I was trying to say.",
        "level": "hard",
        "focus": "\"exactly\" tem /gz/ + /t/: /ɪɡˈzæktli/. Cuidado para não cortar o /t/.",
        "tags": ["consoantes"],
    },
]

LEVELS: tuple[str, ...] = ("easy", "medium", "hard")
LEVEL_LABELS_PT: dict[str, str] = {"easy": "Fácil", "medium": "Médio", "hard": "Difícil"}

_BY_ID: dict[str, dict[str, Any]] = {item["id"]: item for item in SENTENCES}


def all_sentences() -> list[dict[str, Any]]:
    """Todas as frases, ja com word_count calculado."""
    return [_with_counts(item) for item in SENTENCES]


def by_level(level: str | None) -> list[dict[str, Any]]:
    if not level:
        return all_sentences()
    return [_with_counts(item) for item in SENTENCES if item["level"] == level]


def get_sentence(sentence_id: str) -> dict[str, Any] | None:
    item = _BY_ID.get(sentence_id)
    return _with_counts(item) if item else None


def _with_counts(item: dict[str, Any]) -> dict[str, Any]:
    """Copia a frase e adiciona word_count (a UI usa para estimar dificuldade)."""
    data = dict(item)
    data["word_count"] = len(data["text"].split())
    data.setdefault("tags", [])
    return data
