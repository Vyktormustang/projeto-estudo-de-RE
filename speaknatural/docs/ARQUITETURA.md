# SpeakNatural — arquitetura do código

Documento para quem vai **mexer no código** (o README.md, na raiz de `speaknatural/`,
é o guia do usuário).

---

## 1. Decisões técnicas (o porquê de cada peça)

1. **Dois modelos, dois papéis.** O `faster-whisper small.en` (CPU/int8) responde
   *“quais palavras foram ditas e quando”*; o `wav2vec2-xlsr-53-espeak-cv-ft` responde
   *“quais sons IPA foram produzidos”*. Nenhum dos dois responde as duas perguntas bem.
   Cruzar os dois é o que permite dizer “você falou a palavra, mas o /θ/ saiu como /t/”.
   Custo: ~1,7 GB de download e ~2 GB de RAM na primeira análise (carregamento *lazy*,
   o servidor sobe em ~1 s).

2. **Nota = fonemas + presença, nunca só um deles.** Somente fonemas é instável
   (o modelo CTC inventa símbolos em silêncio); somente transcrição não vê sotaque.
   A fórmula (`services/scoring.py`) mistura os dois com pesos explícitos e comentados,
   e tem regras especiais para palavras de 1–2 sons e para palavras puladas.

3. **Alinhamento Needleman-Wunsch com “sons parecidos”.** Alinhar sequências de tamanhos
   diferentes com `zip()` produz notas sem sentido. A matriz DP (em `services/align.py`)
   trata substituição, omissão e inserção; a tabela de confusões (`services/ipa.py`)
   transforma trocas típicas de brasileiro (`ɪ`↔`iː`, `θ`↔`t`, `ɹ`↔`r`, flap `ɾ`) em
   **nota parcial**, e não em zero.

4. **Recorte por tempo de palavra.** Cada palavra tem sua janela (start/end do whisper);
   só os fonemas cujo centro cai nessa janela são comparados. Sem isso, o /s/ de uma
   palavra contaminaria a vizinha. Se o whisper não devolver tempos, distribuímos o
   áudio proporcionalmente ao tamanho das palavras (fallback documentado).

5. **Tudo local, tudo degradável.** Sem chave de API, sem nuvem, sem conta. O app
   funciona mesmo quando falta algo, com aviso em português na tela:
   sem `espeak-ng` → dicionário de fonemas embutido; sem `ffmpeg` → modo de emergência
   para WAV; sem modelos → `503` com explicação e nomes de modelos na mensagem;
   `SN_FAKE_MODELS=1` → modo demonstração determinístico para testar UI/CI sem IA.

---

## 2. Fluxo de uma análise

```
[APK / navegador]
   │  MediaRecorder -> Blob (webm/ogg/mp4)
   │  POST /analyze  (multipart: audio + sentence_id)
   ▼
api/routes_analyze.py
   │  1. valida sentence_id, tamanho do upload, grava em data/tmp
   │  2. services/audio.prepare_audio()
   │       ffmpeg -> WAV 16 kHz mono, corta silêncio, checa duração/volume
   │  3. lock global (1 análise por vez)
   ▼
services/analyzer.run_analysis()
   │  a. g2p.sentence_phonemes()        espeak-ng  -> ["s","p","iː","k"]
   │  b. asr.transcribe()               whisper    -> texto + tempos por palavra
   │  c. phoneme_recognizer.recognize() wav2vec2   -> lista de IPA com tempos
   │  d. word_alignment.match_words()   casa esperado x transcrito (presença + janela)
   │  e. align.align_phonemes()         DP por palavra
   │  f. scoring.word_score()/overall   notas + cores
   │  g. tips.*                         dicas em português
   ▼
services/history.save_attempt()  -> SQLite (attempts, attempt_words, word_stats)
   ▼
JSON AnalyzeResponse  ->  [APK] pinta as palavras e abre o painel de sons
```

O áudio enviado é apagado em `finally` (mesmo em caso de erro).

---

## 3. Mapa dos módulos

### Backend (`backend/app/`)

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | cria o FastAPI, CORS, handlers de erro (JSON em português), monta o `dist/` do frontend se existir |
| `config.py` | todas as constantes e variáveis de ambiente (modelos, limites de áudio, faixas de cor) |
| `db.py` | engine SQLite (WAL), `SessionLocal`, `init_db()` |
| `models.py` | `Attempt`, `AttemptWord`, `WordStat` |
| `schemas.py` | Pydantic v2 = contrato OpenAPI |
| `api/routes_health.py` | `GET /health` (estado dos modelos, ffmpeg, avisos) |
| `api/routes_sentences.py` | `GET /sentences?level=` |
| `api/routes_analyze.py` | `POST /analyze` (upload, lock, cleanup) |
| `api/routes_history.py` | `GET /history` |
| `data/sentences.py` | as 40 frases + dicas |
| `data/fallback_phonemes.json` | gabarito de reserva (gerado por `tools/gen_fallback_phonemes.py`) |
| `services/audio.py` | ffmpeg, resample, trim de silêncio, validações |
| `services/asr.py` | faster-whisper (lazy load, word timestamps, VAD) |
| `services/phoneme_recognizer.py` | wav2vec2 + decodificação CTC com tempos |
| `services/g2p.py` | phonemizer/espeak-ng + cache + fallback |
| `services/ipa.py` | inventário IPA, tokenização, tabela de sons parecidos |
| `services/align.py` | Needleman-Wunsch + nota por fonema |
| `services/scoring.py` | fórmula da palavra/geral + cores |
| `services/tips.py` | dicas em português por som/palavra |
| `services/word_alignment.py` | casamento palavra esperada ↔ transcrita (presença/janela) |
| `services/fake.py` | modo demonstração |
| `services/history.py` | gravação e agregações (palavras difíceis, dias seguidos) |
| `services/errors.py` | catálogo de erros com mensagem pronta em português |

### Frontend (`frontend/src/`)

| Arquivo | Responsabilidade |
|---|---|
| `App.tsx` | shell: abas, tema, indicador de conexão |
| `components/PracticeTab.tsx` | frase, microfone, resultado colorido, botões |
| `components/WordSheet.tsx` | painel da palavra (sons, esperado x ouvido, dica) |
| `components/HistoryTab.tsx` | estatísticas, palavras difíceis, últimas tentativas |
| `components/SettingsTab.tsx` | endereço do servidor, testar conexão, tema, ajuda do IP |
| `lib/api.ts` | cliente HTTP, erros traduzidos, timeouts |
| `lib/recorder.ts` | MediaRecorder (formato, permissões, limite de 30 s) |
| `lib/speech.ts` | voz de referência: plugin nativo no APK + Web Speech API no navegador |
| `lib/settings.ts` | endereço do servidor, tema e nível salvos no aparelho |
| `lib/format.ts` | percentuais, cores, datas, tokenização da frase |

### Android (`frontend/android/`)

Projeto gerado pelo Capacitor 6 (`npx cap add android`) e **versionado** para o CI
funcionar sem Android Studio. Modificações em relação ao template:

* `AndroidManifest.xml`: `RECORD_AUDIO`, `MODIFY_AUDIO_SETTINGS`, `usesCleartextTraffic`,
  `networkSecurityConfig`, `<queries>` para o motor de TTS;
* `res/xml/network_security_config.xml`: permite HTTP na rede local (servidor sem HTTPS);
* plugin `@capacitor-community/text-to-speech@5.1.0` (voz nativa no Android — o WebView
  do Android não implementa `speechSynthesis`);
* ícones e splash gerados a partir de `resources/icon.png` (`resources/make_icons.py`).

---

## 4. Banco de dados

```
attempts(id, sentence_id, sentence_text, level, transcript, overall_score,
         duration_seconds, engine_version, created_at)
attempt_words(id, attempt_id → attempts.id, position, text, normalized,
              score, color, presence, phonemes[JSON])
word_stats(id, normalized, display, level, attempts, total_score,
           best_score, last_score, updated_at)   UNIQUE(normalized, level)
```

* `word_stats` é um *upsert* por (palavra, nível) e alimenta “palavras mais difíceis”.
* `phonemes` guarda a lista completa `[{expected, heard, score, tip}]` — se um dia você
  quiser reabrir o detalhe de uma tentativa antiga, o dado já está lá.
* Apagar `backend/data/speaknatural.db` zera o histórico (recriado no próximo start).

---

## 5. Como estender (o que já está preparado)

**Nova frase:** adicione um dicionário em `data/sentences.py` (id novo).
**Novo nível:** inclua em `LEVELS` e ajuste os `Literal` de `schemas.py` + chips do frontend.
**Ajustar rigor:** `config.py` (`GREEN_MIN`, `YELLOW_MIN`, `NEAR_SOUND_SCORE`, `GAP_PENALTY`).
**Outro idioma:** `SN_PHONEMIZER_LANGUAGE` (espeak) + um modelo wav2vec2 de fonemas do
idioma + `language` no `asr.transcribe` (hoje fixo em `"en"`).
**Modo conversa (fase futura):** crie `services/conversation.py` e
`api/routes_conversation.py`; o `whisper` já devolve texto contínuo e o
`phoneme_recognizer` já aceita qualquer duração até 60 s.
**Contas de usuário:** `Attempt` já é uma tabela isolada — basta um
`user_id` + tabela `users` e o filtro nas rotas de histórico.
**Nuvem/GPU:** `SN_WHISPER_DEVICE=cuda` e `SN_WHISPER_COMPUTE_TYPE=float16`; o resto não muda.

---

## 6. Testes

```bash
cd backend && python -m pytest -q       # 26 testes: IPA, alinhamento, notas, API completa
cd frontend && npm test                 # 21 testes: formatação, endereço do servidor, render sem crash
cd frontend && npm run typecheck        # TypeScript estrito
```

Os testes do backend rodam com `SN_FAKE_MODELS=1` e um SQLite temporário — **não**
baixam modelos e terminam em ~1 s.

---

## 7. Desempenho medido (PC comum, CPU, int8)

| Etapa | Tempo |
|---|---|
| subir o servidor (modelos não carregados) | ~1 s |
| carregar os modelos na 1ª análise | 10–25 s (depois ficam em RAM) |
| converter áudio (`ffmpeg`) | 50–150 ms |
| transcrever (`small.en`, frase de ~4 s) | 1–4 s |
| fonemas (`wav2vec2`, frase de ~4 s) | 2–12 s |
| alinhamento + notas + dicas | < 20 ms |
| salvar no SQLite | < 10 ms |

Para PC fraco: `SN_WHISPER_MODEL=base.en` (≈3× mais rápido, um pouco menos preciso).
