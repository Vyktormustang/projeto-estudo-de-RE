# Publicação do progresso e da V42 — 07/11/2026

Publicação solicitada pelo usuário: fontes/progresso no GitHub e última versão funcional no Drive. Não cria V43 e não mistura o projeto Gen1–9 com o BAG_MOD histórico de 16 MiB.

## Última versão validada

**FireRed Gen1–9 motor V42**, 33.554.432 bytes.

```text
SHA-256 6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a
MD5     663e6a24b672f3473d94eb67a08d74cc
```

- [ROM no Drive](https://drive.google.com/file/d/17p985dQwZ3kkoIKeCA6sEWWsUjTwh1Bv/view)
- [Pasta da publicação](https://drive.google.com/drive/folders/1NIeOi3gwbATumquRBH9rdT5rEEg2UbfN)
- [Fontes na branch de trabalho](https://github.com/Vyktormustang/projeto-estudo-de-RE/tree/arena/8b7d7c0a-projeto-estudo-de-re/firered_gen1_9)

O checksum SHA-256 e o tamanho devolvidos pelo Drive coincidiram com os locais após o upload. As versões antigas não foram substituídas e não foi criado acesso público “qualquer pessoa com o link”. A pasta herda as regras do diretório de colaboração existente.

## Validação e limites

| Execução | Resultado | Natureza |
|---|---|---|
| Criação da V42, 06/11 | 19/19; 220,527 s | Histórico preservado em `motor_v42_resultados.json` e `motor_v42.log` |
| Trajetos das ilhas, 06/11 | 6/6; 98,001 s | Histórico: 24 mapas, 549 passos, retornos e SAVE/Continuar |
| Preparação desta publicação, 07/11 | 15/15; 13,624 s | Construção, scripts, topologia e dados de Cosmog; **sem emulador** |

Essas contagens são execuções distintas, não uma nova suíte cumulativa. A preparação desta publicação reconstruiu a cadeia V18 → V42, conferindo os hashes de entrada e saída em cada etapa e a igualdade byte a byte da saída final. Não repetiu os testes nativos históricos.

A auditoria adicional de Cosmog está **parcial**, conforme [PROGRESSO_COSMOG_V42.md](PROGRESSO_COSMOG_V42.md). Não se certificam eclosão, dois lendários finais simultâneos, campanha completa, todos os 1.025 Pokémon, hardware/link ou fidelidade integral a Scarlet/Violet.

## Conteúdo e segurança

GitHub: fontes, dados gerados do projeto, payloads dos patches, testes, relatórios e evidências textuais. Sem ROM comercial, save, savestate, credenciais ou telas extraídas do jogo. O teste nativo de Cosmog é publicado como trabalho em andamento, não como validação final aprovada.

Drive: ROM V42, instruções, checksums e relatórios principais. Sem save pessoal e sem sobrescrever a V18.

Antes de atualizar o jogo, faça backup independente do save normal. Use “Continuar”; não transporte savestates entre versões. Veja [MOTOR_V42.md](MOTOR_V42.md) e [AUDITORIA_TRAJETOS_V42.md](AUDITORIA_TRAJETOS_V42.md).
