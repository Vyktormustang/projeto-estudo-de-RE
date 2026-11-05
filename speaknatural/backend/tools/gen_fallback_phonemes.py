"""Gera backend/app/data/fallback_phonemes.json (plano B do gabarito de fonemas).

Uso:
    python tools/gen_fallback_phonemes.py             (usa espeak-ng, se existir)
    python tools/gen_fallback_phonemes.py --engine eng_to_ipa

O arquivo gerado e um dicionario palavra -> IPA. Ele so e usado quando o
espeak-ng NAO esta instalado no PC do servidor; nesse caso o app avisa na tela
que o gabarito veio do dicionario embutido (precisao um pouco menor).

Nao e preciso rodar isto no dia a dia: o JSON ja esta versionado no repositorio.
Rode de novo apenas se voce adicionar/editar frases em app/data/sentences.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.data.sentences import all_sentences  # noqa: E402
from app.services.text import normalize_word, split_words  # noqa: E402

OUTPUT = BACKEND_DIR / "app" / "data" / "fallback_phonemes.json"

#: Palavras que nao estao no dicionario CMU (contracoes duplas, gíria).
#: Entradas conferidas a mao com a pronuncia do espeak-ng (en-us).
MANUAL_OVERRIDES: dict[str, str] = {
    "shouldn't've": "ˈʃʊdəntəv",
    "whatcha": "ˈwʌtʃə",
    "gonna": "ˈɡʌnə",
    "wanna": "ˈwɑnə",
}


def phonemize_with_espeak(words: list[str]) -> dict[str, str]:
    from phonemizer.backend import EspeakBackend

    backend = EspeakBackend(language="en-us", preserve_punctuation=False, with_stress=True, tie=False)
    result = backend.phonemize(words, strip=True, njobs=1)
    return {word: ipa for word, ipa in zip(words, result)}


def phonemize_with_eng_to_ipa(words: list[str]) -> dict[str, str]:
    import eng_to_ipa as ipa_tool

    mapping: dict[str, str] = {}
    for word in words:
        try:
            converted = ipa_tool.convert(word)
        except Exception:
            converted = ""
        if converted and "*" not in converted:
            mapping[word] = converted
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        choices=("auto", "espeak", "eng_to_ipa"),
        default="auto",
        help="Motor de conversão grafema->fonema (padrão: auto)",
    )
    args = parser.parse_args()

    words: list[str] = []
    seen: set[str] = set()
    for sentence in all_sentences():
        for raw in split_words(sentence["text"]):
            word = normalize_word(raw)
            if word and word not in seen:
                seen.add(word)
                words.append(word)
    words.sort()

    engine_used = ""
    mapping: dict[str, str] = {}
    if args.engine in ("auto", "espeak"):
        try:
            mapping = phonemize_with_espeak(words)
            engine_used = "phonemizer + espeak-ng (en-us)"
        except Exception as exc:
            print(f"[aviso] espeak-ng indisponível: {exc}", file=sys.stderr)
            if args.engine == "espeak":
                return 1
    if not mapping:
        try:
            mapping = phonemize_with_eng_to_ipa(words)
            engine_used = "eng_to_ipa (dicionário CMU convertido para IPA)"
        except Exception as exc:
            print(f"[erro] eng_to_ipa indisponível: {exc}", file=sys.stderr)
            return 1

    for word, ipa in MANUAL_OVERRIDES.items():
        if word in seen:
            mapping[word] = ipa
    missing = [w for w in words if w not in mapping]
    payload = {
        "meta": {
            "generated_on": date.today().isoformat(),
            "engine": engine_used,
            "words": len(mapping),
            "missing": missing,
            "note": "Plano B para quando o espeak-ng não está instalado. "
            "Rode tools/gen_fallback_phonemes.py para regerar.",
        },
        "words": dict(sorted(mapping.items())),
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: {OUTPUT} ({len(mapping)} palavras, motor: {engine_used})")
    if missing:
        print(f"[aviso] sem fonemas: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
