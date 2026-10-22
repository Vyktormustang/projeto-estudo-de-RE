# Fase 1 — domínios numéricos locais de moves e tipos

**Estado:** revalidação estática somente leitura dos campos numéricos nas tabelas candidatas de species, moves, learnsets e type effectiveness. O relatório registra valores e limites da ROM-base; não lhes atribui nomes semânticos externos. Não houve alteração de ROM/save nem execução dinâmica.

## Identidade e reprodução

- ROM `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Verificador: `python scripts/inspect_expansion_numeric_domains.py`.
- Desmontagens anteriores dos caminhos de leitura: ciclos 20, 21 e 25. Capstone foi usado para Thumb; REA/Ghidra e emulador não foram usados nesta auditoria.

## Valores numéricos lidos diretamente

| Região candidata | Campos/formatos conferidos | Valores observados na ROM-base |
|---|---|---|
| SpeciesInfo `0x08254784`, 412 × `0x1C` | bytes `+6`, `+7` nos registros 1–411 | distintos: `0..8`, `10..17`; máximo 17 |
| Catálogo move `0x08250C04`, 355 × 12 | byte `+2` (todos registros) e byte `+0` | tipos distintos: `0..17`; efeito `+0` máximo 213 |
| Learnsets, 412 ponteiros em `0x0825D7B4` | 411 listas únicas, palavras u16 antes do terminador | 4.036 palavras; ID lower-nine-bit máximo 354; nível máximo 99 |
| Type effectiveness `0x0824F050`, 112 × 3 | bytes `+0`, `+1`, excluídos marcadores locais `FE`/`FF` | tipos distintos: `0..8`, `10..17`; máximo 17; marcador `FE FE 00` no índice 108 e terminador `FF FF 00` no índice 111 |

As faixas e conjuntos acima são observações dos bytes, não rótulos de tipos como Água/Fada nem prova de que a build suporte tipos além dos encontrados. A tabela de effectiveness é uma lista de relações de 3 bytes percorrida pelo handler local, não um array indexado diretamente pelo número do tipo.

## Limites de representação e consumidores

### ID de move em learnsets

O consumidor local decodifica cada halfword com máscara `0x01FF` para o ID do move e `0xFE00` para o nível (ciclo 20); `0xFFFF` termina a lista. Logo, o campo comporta numericamente IDs de `0` a `511`. A maior ID encontrada nos dados atuais é 354. Uma fonte futura com IDs acima de 511 não cabe nesse formato sem mudar o encoding e todos os consumidores de learnset. O nível máximo efetivamente observado foi 99; esta amostra não exige mudança do campo de nível.

A largura de u16 nos slots de moves de BoxMon e da equipe não remove essa restrição específica do formato de learnset. Também não prova que todos os outros caminhos aceitem qualquer valor u16.

### Índice de move e efeito

No caminho local em `0x0801632C`, o ID corrente em `0x02023D4A` é usado para calcular `moveId × 12 + 0x08250C04`; o byte `+0` seleciona uma word na tabela candidata de 214 ponteiros a partir de `0x081D65A8`, e o destino é gravado em `0x02023D74` (ciclo 21). No accessor de PP `0x0803E9A4`, o ID também é escalado por 12 e o byte `+4` é lido. Os trechos examinados não mostram um clamp de faixa antes desses acessos.

O byte de efeito `+0` tem largura de 8 bits, mas a tabela local observada contém somente 214 destinos (índices 0–213) e os registros atuais não excedem 213. Portanto, atribuir a um novo move um efeito acima de 213 requer expandir/relocar a dispatch table e auditar o lookup; valores acima de 255 não cabem sequer no byte de efeito. Isso não limita a quantidade de moves a 214: vários moves podem apontar ao mesmo efeito, conforme dados e implementação.

### Códigos de tipo

Os campos locais usados como tipos são bytes nas estruturas observadas: offsets `+6/+7` de SpeciesInfo e `+2` do registro de move. O handler typecalc seleciona o byte `+2` do move ou, em condição especial, um byte dinâmico mascarado com `0x3F`; depois compara tipos do atacante/defensor e percorre a lista de effectiveness até o terminador `0xFF` (ciclo 25). A máscara só demonstra que esse caminho usa os seis bits baixos; não prova que IDs 18–63 sejam aceitos em menus, dados, habilidades ou outros consumidores.

Adicionar um código de tipo novo exigiria mais que acrescentar linhas à lista de effectiveness: ainda faltam auditar validação e todos os consumidores de tipos, textos/nomes, UI, ícones, seleção dinâmica e interações com habilidades. Nenhum desses códigos recebeu nome neste relatório.

## Consequência para o plano de expansão

1. Antes de importar dados, o dataset versionado deve conferir `max(moveId) <= 511` para learnsets e `max(effectId) <= 213` se a dispatch table ficar inalterada; falhar fechado se ultrapassar.
2. Se o corte exigir ID de move maior que 511, ampliar o encoding de learnset e cobrir os cinco consumidores locais já identificados, incluindo seus caps de 20 entradas.
3. Se forem introduzidos efeitos além de 213, implementar handlers reais, ampliar a tabela e testar cada caminho; não atribuir efeitos por proximidade/semelhança sem verificação.
4. Para tipo novo, rastrear faixas e renderização de todas as rotas antes de declarar suporte. Os conjuntos numéricos acima são baseline local, não enum completo do jogo.
5. A geração/data de corte continua pendente. Nenhum dado foi importado nem patch construído nesta etapa.
