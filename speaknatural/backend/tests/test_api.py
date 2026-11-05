"""Testes da API inteira (modo demonstracao: nao baixa modelos de IA)."""

from __future__ import annotations

from pathlib import Path


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["database"] == "sqlite"
    assert body["fake_models"] is True


def test_sentences_todos_os_niveis(client):
    response = client.get("/sentences")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 40
    niveis = {item["level"] for item in body["sentences"]}
    assert niveis == {"easy", "medium", "hard"}


def test_sentences_filtradas(client):
    body = client.get("/sentences", params={"level": "hard"}).json()
    assert body["total"] == 12
    assert all(item["level"] == "hard" for item in body["sentences"])


def test_sentences_nivel_invalido(client):
    assert client.get("/sentences", params={"level": "impossivel"}).status_code == 422


def test_analyze_fluxo_completo(client, wav_file: Path):
    sentenca = client.get("/sentences", params={"level": "easy"}).json()["sentences"][0]

    with wav_file.open("rb") as handle:
        response = client.post(
            "/analyze",
            data={"sentence_id": sentenca["id"]},
            files={"audio": ("audio.wav", handle, "audio/wav")},
        )

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["sentence_id"] == sentenca["id"]
    assert 0.0 <= body["overall_score"] <= 1.0
    assert body["overall_color"] in {"green", "yellow", "red"}
    assert len(body["words"]) >= 3
    assert body["attempt_id"] > 0

    for palavra in body["words"]:
        assert palavra["color"] in {"green", "yellow", "red"}
        assert 0.0 <= palavra["score"] <= 1.0
        for fonema in palavra["phonemes"]:
            assert 0.0 <= fonema["score"] <= 1.0
            assert "expected" in fonema and "heard" in fonema and "tip" in fonema

    # o historico deve conter a tentativa
    historico = client.get("/history").json()
    assert historico["total_attempts"] >= 1
    assert any(item["id"] == body["attempt_id"] for item in historico["attempts"])
    assert len(historico["hard_words"]) >= 1


def test_analyze_frase_inexistente(client, wav_file: Path):
    with wav_file.open("rb") as handle:
        response = client.post(
            "/analyze",
            data={"sentence_id": "zz99"},
            files={"audio": ("audio.wav", handle, "audio/wav")},
        )
    assert response.status_code == 404
    assert response.json()["code"] == "sentence_not_found"


def test_analyze_sem_audio(client):
    response = client.post("/analyze", data={"sentence_id": "e01"})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_analyze_audio_curto(client, tmp_path: Path):
    import numpy as np
    import soundfile as sf

    curto = tmp_path / "curto.wav"
    sf.write(str(curto), np.zeros(1600, dtype="float32"), 16_000)
    with curto.open("rb") as handle:
        response = client.post(
            "/analyze",
            data={"sentence_id": "e01"},
            files={"audio": ("curto.wav", handle, "audio/wav")},
        )
    assert response.status_code == 422
    assert response.json()["code"] in {"audio_too_short", "no_speech"}
    assert "detail" in response.json()


def test_openapi_documenta_rotas(client):
    schema = client.get("/openapi.json").json()
    for rota in ("/health", "/sentences", "/analyze", "/history"):
        assert rota in schema["paths"]
