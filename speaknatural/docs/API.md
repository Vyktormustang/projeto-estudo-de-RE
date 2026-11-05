# SpeakNatural — API (referência)

Servidor local: `http://localhost:8000` (ou `http://IP-DO-PC:8000` no celular).
Documentação interativa gerada automaticamente: **http://localhost:8000/docs**
(OpenAPI 3.1 em `/openapi.json`).

Todas as respostas são JSON com `Content-Type: application/json`.
Erros seguem sempre o mesmo formato:

```json
{
  "detail": "A gravação ficou curta demais. Espere o microfone abrir, leia a frase inteira e só então pare.",
  "code": "audio_too_short"
}
```

| Código HTTP | `code`                  | Quando acontece                                        |
|-------------|-------------------------|--------------------------------------------------------|
| 400         | `empty_audio`           | nenhum áudio chegou                                    |
| 404         | `sentence_not_found`    | `sentence_id` inexistente                              |
| 413         | `upload_too_big`        | arquivo acima de 12 MB                                 |
| 413         | `audio_too_long`        | gravação acima de 60 s                                 |
| 422         | `audio_too_short`       | gravação abaixo de 0,6 s                               |
| 422         | `no_speech`             | silêncio (volume abaixo do limiar)                     |
| 422         | `validation_error`      | faltou o campo `audio` ou `sentence_id`                |
| 500         | `ffmpeg_missing`        | ffmpeg não instalado no PC do servidor                 |
| 500         | `audio_convert_failed`  | arquivo corrompido / formato não suportado             |
| 503         | `models_unavailable`    | modelo de IA falhou ao carregar (rede, RAM)            |
| 503         | `models_disabled`       | servidor rodando com `SN_DISABLE_MODELS=1`             |

---

## GET /health

Testa o servidor (usado pelo botão **“Testar conexão”** do app).

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "sqlite",
  "ffmpeg": true,
  "whisper": "small.en: nao carregado",
  "phonemes": "wav2vec2-xlsr-53-espeak-cv-ft: nao carregado | esperado: espeak-ng",
  "fake_models": false,
  "messages": [],
  "server_time": "2026-11-05T21:00:00Z"
}
```

* `status`: `ok` (tudo certo) ou `degraded` (falta ffmpeg ou um modelo falhou).
* `whisper` / `phonemes`: `nao carregado` é **normal** antes da primeira análise;
  os modelos carregam na primeira chamada de `/analyze` (e ficam na memória).
* `messages`: avisos em português, os mesmos que o app mostra.

---

## GET /sentences

Lista as frases embutidas (~40), com filtro opcional por nível.

| Parâmetro | Tipo                          | Obrigatório | Descrição                     |
|-----------|-------------------------------|-------------|-------------------------------|
| `level`   | `easy` \| `medium` \| `hard`  | não         | filtra por dificuldade        |

```bash
curl "http://localhost:8000/sentences?level=medium"
```

```json
{
  "level": "medium",
  "total": 14,
  "sentences": [
    {
      "id": "m07",
      "text": "Could you speak a little more slowly, please?",
      "level": "medium",
      "focus": "\"speak a\" liga no /k/: /ˈspiːkə/. Cuidado com o /l/ de \"slowly\".",
      "tags": ["linking", "pedido"],
      "word_count": 8
    }
  ]
}
```

* `focus` é uma dica em **português** sobre o que treinar naquela frase.
* `id` é o valor que vai em `sentence_id` do `POST /analyze`.

---

## POST /analyze

Analisa a leitura de uma frase. `multipart/form-data`.

| Campo         | Tipo   | Obrigatório | Descrição                                              |
|---------------|--------|-------------|--------------------------------------------------------|
| `audio`       | file   | sim         | gravação (webm, ogg, wav, m4a, mp3, aac, opus)          |
| `sentence_id` | string | sim         | `id` vindo de `GET /sentences`                          |

```bash
curl -X POST http://localhost:8000/analyze \
  -F "sentence_id=m07" \
  -F "audio=@minha-leitura.webm"
```

Resposta (resumida):

```json
{
  "attempt_id": 42,
  "sentence_id": "m07",
  "sentence_text": "Could you speak a little more slowly, please?",
  "level": "medium",
  "transcript": "could you speak a little more slowly please",
  "overall_score": 0.8148,
  "overall_color": "yellow",
  "duration_seconds": 3.42,
  "created_at": "2026-11-05T21:03:11.482Z",
  "warnings": [],
  "words": [
    {
      "text": "speak",
      "normalized": "speak",
      "score": 1.0,
      "color": "green",
      "presence": 1.0,
      "tip": "“speak” ficou muito bom. Siga assim.",
      "phonemes": [
        { "expected": "s", "heard": "s", "score": 1.0, "tip": "" },
        { "expected": "p", "heard": "p", "score": 1.0, "tip": "" },
        { "expected": "iː", "heard": "ɪ", "score": 0.65,
          "tip": "Você fez o som curto /ɪ/. Aqui o esperado é /iː/ longo: sorria e segure." },
        { "expected": "k", "heard": "k", "score": 1.0, "tip": "" }
      ]
    },
    {
      "text": "slowly",
      "normalized": "slowly",
      "score": 0.0,
      "color": "red",
      "presence": 0.0,
      "tip": "“slowly” não apareceu na sua leitura. Leia a frase devagar para não pular palavras.",
      "phonemes": [
        { "expected": "s", "heard": null, "score": 0.0,
          "tip": "Esse som não apareceu na sua fala. Diminua a velocidade." }
      ]
    }
  ]
}
```

### Campos da resposta

| Campo             | Significado                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| `overall_score`   | nota geral 0..1 (média das palavras ponderada pelo nº de fonemas)            |
| `overall_color`   | `green` (≥0,85) · `yellow` (0,50–0,84) · `red` (<0,50)                       |
| `transcript`      | o que o faster-whisper entendeu da sua fala                                  |
| `words[].text`    | a palavra escrita (na ordem da frase)                                        |
| `words[].score`   | nota da palavra 0..1                                                         |
| `words[].color`   | cor a pintar na tela (mesma regra do `overall_color`)                        |
| `words[].presence`| 1 = transcrita igual · 0,5 = parecida · 0 = não falada                       |
| `words[].phonemes[].expected` | som IPA esperado (espeak-ng) — `null` quando é um som extra seu  |
| `words[].phonemes[].heard`    | som IPA ouvido pelo wav2vec2 — `null` quando o som não saiu      |
| `words[].phonemes[].score`    | 1,0 exato · 0,65 som parecido · 0,3 vogal trocada · 0 ausente    |
| `words[].tip`     | dica em português da palavra                                                 |
| `warnings`        | avisos em português (ffmpeg faltando, áudio baixo, modo demo...)             |

---

## GET /history

Histórico de tentativas + palavras mais difíceis.

| Parâmetro   | Tipo | Padrão | Máx | Descrição                      |
|-------------|------|--------|-----|--------------------------------|
| `limit`     | int  | 30     | 200 | nº de tentativas               |
| `hard_words`| int  | 12     | 50  | nº de palavras difíceis        |

```bash
curl http://localhost:8000/history
```

```json
{
  "total_attempts": 12,
  "average_score": 0.7123,
  "best_score": 0.94,
  "streak_days": 3,
  "attempts": [
    {
      "id": 12,
      "sentence_id": "m07",
      "sentence_text": "Could you speak a little more slowly, please?",
      "level": "medium",
      "overall_score": 0.8148,
      "created_at": "2026-11-05T21:03:11.482Z"
    }
  ],
  "hard_words": [
    {
      "normalized": "slowly",
      "display": "slowly",
      "level": "medium",
      "attempts": 4,
      "average_score": 0.5125,
      "best_score": 0.72,
      "last_score": 0.68
    }
  ]
}
```

---

## Variáveis de ambiente (todas opcionais)

| Variável | Padrão | Para que serve |
|---|---|---|
| `SN_HOST` / `SN_PORT` | `0.0.0.0` / `8000` | endereço/porta do servidor |
| `SN_WHISPER_MODEL` | `small.en` | modelo do faster-whisper (`base.en` = mais rápido, menos preciso) |
| `SN_WHISPER_COMPUTE_TYPE` | `int8` | `int8` (rápido) ou `float32` (mais preciso, mais lento) |
| `SN_PHONEME_MODEL` | `facebook/wav2vec2-xlsr-53-espeak-cv-ft` | modelo de fonemas |
| `SN_MIN_AUDIO_SECONDS` | `0.6` | duração mínima aceita |
| `SN_MAX_AUDIO_SECONDS` | `60` | duração máxima aceita |
| `SN_SILENCE_RMS` | `0.004` | sensibilidade para considerar “silêncio” |
| `SN_FFMPEG_BIN` | `ffmpeg` | caminho do ffmpeg, se não estiver no PATH |
| `SN_CORS_ORIGINS` | `*` | origens permitidas (separadas por vírgula) |
| `SN_DATA_DIR` | `backend/data` | onde ficam banco e áudios temporários |
| `SN_FAKE_MODELS` | `0` | `1` = modo demonstração (notas simuladas, sem IA) |
| `SN_DISABLE_MODELS` | `0` | `1` = sobe a API sem carregar modelos (útil em CI) |

Exemplo (Windows, Prompt):

```bat
set SN_WHISPER_MODEL=base.en
start-server.bat
```

Exemplo (Linux/macOS):

```bash
SN_WHISPER_MODEL=base.en ./start-server.sh
```

---

## Python (integração direta)

```python
from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    frase = client.get("/sentences", params={"level": "easy"}).json()["sentences"][0]
    with open("leitura.wav", "rb") as audio:
        resultado = client.post(
            "/analyze",
            data={"sentence_id": frase["id"]},
            files={"audio": ("leitura.wav", audio, "audio/wav")},
        ).json()
    print(resultado["overall_score"], [w["color"] for w in resultado["words"]])
```

---

## Limites conhecidos

* Um pedido de análise por vez (o servidor usa um lock: o wav2vec2 consome ~1,5 GB de RAM).
* Primeira análise é lenta (carrega os modelos; se ainda não baixou, baixa ~2 GB).
* Áudio é apagado do disco logo após a análise; só as notas ficam no SQLite.
* Sem autenticação: é um servidor **de rede local**. Não exponha na internet.
