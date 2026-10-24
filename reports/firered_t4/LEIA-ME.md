# T4 — Descrições de itens em PT-BR (nomes em inglês)

Data: 2026-10-24 · Build da prova: `pokefirered_modern.gba` md5 `5c5f497acf1379926d842b3185c283dc`
(o md5 identifica a build desta rodada; muda a cada rebuild e não é critério de regressão)

## O que foi feito (CONFIRMADO)

- Novo dicionário `scripts/firered/traducao_itens_ptbr.py` com **307 descrições**
  (todos os itens com descrição real; os 68 restantes são placeholders "?????").
- **Formato à prova de escapes:** cada entrada é `itemId -> [lista de linhas]`,
  sem nenhum backslash no arquivo; o aplicador junta com `\n` literal.
- `aplicar_traducao.py` ganhou `DICIONARIOS_JSON`/`aplicar_json`: aplica em
  `src/data/items.json` (campo `description_english`) — a fonte da verdade,
  pois `src/data/items.h` é REGENERADO pelo jsonproc no build.
- Aplicação: `307/307 OK, 0 problemas`; nenhuma linha acima de 36 chars.
- **Nomes de itens permanecem em inglês** (decisão do usuário); só descrições
  foram traduzidas. Stats: ATAQUE/DEFESA/AT. ESP./DEF. ESP./VELOCIDADE.
- Regressão E8: PASS. `verificar_rom.py`: ok.

## Correção de ferramenta (bônus)

`savestate.py set_item` agora cifra a quantidade com
`SaveBlock2.encryptionKey` (src/item.c: SetBagItemQuantity). O comentário
`/*0xF20*/` do global.h está desatualizado após a Pokédex Gen 9 — o offset
real, medido com `offsetof` no compilador do projeto, é **0xF24**. Antes a
bolsa mostrava "×?14" (lixo cifrado); agora "× 3" correto.

## Provas em jogo

| Arquivo | O que prova |
| --- | --- |
| `01_potion_descricao_ptbr.png` | POTION × 3 — "Um remédio em spray para feridas…" |
| `02_ultra_ball_descricao_ptbr.png` | ULTRA BALL × 5 — "Uma BOLA de altíssima qualidade…" |
| `03_leftovers_descricao_ptbr.png` | LEFTOVERS — "Um item para um POKéMON segurar…" |

## Método (reprodutível)

1. `aplicar_traducao.py --write` + `make MODERN=1` (items.h regenerado do json).
2. `prova_golpes_e4.py --preparar-estado` → estado limpo na Rota 1.
3. `savestate.py … item --pocket items --slot 0 --id 13 --qtd 3` (e ULTRA BALL id 2,
   LEFTOVERS id 200) → bolsa populada.
4. `nav.py` abre START → BOLSA e fotografa a caixa de descrição.

No Windows: rodar via WSL (ver `docs/FIRERED.md`).
