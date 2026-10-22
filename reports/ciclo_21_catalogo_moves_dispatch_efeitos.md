# Ciclo 21 — Catálogo local de moves e dispatch por efeito

**Estado:** rastreamento estático local da região candidata de registros de moves, dos offsets lidos por consumidores e de uma rotina que usa o byte `+0` para selecionar um ponteiro numa tabela indexada por efeito. O dispatch genérico foi localizado; handlers individuais, execução dinâmica e cobertura de todos os consumidores continuam pendentes.

## Identidade, método e limites

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`, 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- VA GBA = offset de arquivo + `0x08000000`.
- Inspeção local de bytes e desmontagem Thumb com Capstone 5.0.7 temporário em `/tmp/capstone-py`; script reproduzível sem dependências externas: `scripts/inspect_move_catalog.py`.
- Cruzamento semântico separado com `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`. Esse upstream serve como hipótese/nomenclatura, não como prova da origem ou equivalência integral da ROM BR.
- Não foram usados REA nem Ghidra; não houve execução dinâmica, alteração da ROM ou alteração de save.

## Região local candidata a catálogo

O código local em `0x08016332–0x08016346` calcula `ID × 12`, soma o endereço literal `0x08250C04` e carrega o byte no início do registro. O consumidor de PP `0x0803E9A4` já havia mostrado o mesmo stride e a leitura de `+4`. A inspeção de bytes encontra 355 registros candidatos no intervalo `[0x08250C04, 0x08251CA8)` (índices 0–354), com stride `0x0C`:

- registro 0 é inteiramente zero;
- bytes `+9..+11` são zero nos 355 registros;
- a sequência seguinte, em `0x08251CA8`, já começa `34 00 10 00 01 01 00 00 FF FF FF FF`, diferente do padrão de cauda observado nos registros candidatos;
- no byte `+0`, há 198 valores distintos entre 0 e 213; o valor zero ocorre em 24 registros.

Isso sustenta o limite **candidato** de 355 entradas, em conjunto com o stride calculado por código. Não há aqui prova de que todos os valores aceitos por todos os caminhos estejam dentro do intervalo, nem uma comparação de faixa visível no trecho de dispatch analisado.

### Leituras locais observadas

Os offsets abaixo são fatos de acesso na ROM; os significados nominais não são inferidos apenas pelos loads:

| Endereço local | Observação |
|---|---|
| `0x08019B58` | Calcula o registro por ID×12, lê `+0` e compara o valor com `0x7D`. É um consumidor especial do byte inicial, não o dispatch genérico. |
| `0x0801976C` | Lê o byte `+1`. |
| `0x0803E9A4` | Calcula ID×12 e lê `+4` no preenchimento de PP, conforme rastreado no ciclo 20. |
| `0x08015F62`, `0x0801D8E6`, `0x0801DA00` | Lêem byte `+8` em trechos locais. |
| `0x08015F6A` | Lê byte `+6`. |
| `0x08016332–0x08016346` | Lê `+0` e o usa como índice no dispatch de ponteiros descrito abaixo. |

Não foi demonstrado que essa lista esgote os consumidores. Os offsets `+2`, `+3`, `+5` e `+7` não foram caracterizados neste ciclo.

## Dispatch local por byte `+0`

O bloco Thumb local em `0x0801632C` contém uma cadeia direta que pode ser reconstituída sem nomes do upstream. Sete branches locais convergem nele (`0x08015FA8`, `0x08016158`, `0x080161E2`, `0x08016272`, `0x0801628A`, `0x080162C2`, `0x08016316`). A rota estática de callbacks foi seguida: `0x08000524` chama slots da callback principal; `0x080123E4` encaminha a callback guardada em `0x03004F84`; caminhos locais instalam `0x080154A0`, que em `0x08015562` zera `0x02023BE3`, mas logo em `0x08015568` copia para ele o primeiro byte do buffer local com base `0x02023BDA`. O mesmo buffer recebe writes indexados em `0x080150D0–0x080150E0`; o valor de seu primeiro byte no momento da cópia não está rastreado. O callback agenda `0x080155C8`, que grava `0x0C` se `0x02023E8A` for não-zero; caso contrário, retém o byte copiado. Portanto, slot 0 (`0x08015CA1`) da tabela primária candidata em `0x08250038` só é selecionado se o valor recebido no dispatch for zero — isso não está provado. A correção de limites identifica uma tabela primária candidata de 14 ponteiros e uma tabela secundária candidata de 9 ponteiros em `0x08250070`; callbacks primários em slots 2/3/8 escrevem guardas 4/6, que podem selecionar slots 4/6 da tabela secundária. Os limites e a semântica permanecem candidatos; os predicados e a execução em runtime não foram confirmados.

1. carrega o ID corrente de move do endereço RAM `0x02023D4A`;
2. calcula `ID × 12` e soma a base de registros `0x08250C04`;
3. carrega o byte `+0` do registro;
4. multiplica esse byte por quatro, soma a base `0x081D65A8` e carrega a word u32 selecionada;
5. grava o ponteiro resultante no endereço RAM `0x02023D74`.

Os literais usados por essa sequência estão em `0x08016360–0x0801636F`: `0x02023D74`, `0x081D65A8`, `0x08250C04` e `0x02023D4A`, nessa ordem. Isso confirma na ROM local um dispatch indireto indexado pelo campo `+0`; não é apenas uma comparação de um efeito isolado.

Em `0x081D65A8` há uma sequência candidata de 214 palavras u32 cujos valores apontam para dentro da ROM, ocupando `[0x081D65A8, 0x081D6910)`. A palavra imediatamente seguinte, em `0x081D6910`, é `0x3D4A012A`, que não é um endereço da ROM; a evidência de limite é estrutural, não um símbolo local. Os 214 destinos candidatos têm 185 valores únicos. Todos os valores `+0` encontrados nos 355 registros (máximo 213) cabem nesses 214 índices. Exemplos de índice→word local: `0→0x081D6900`, `1→0x081D696D`, `125→0x081D7977`, `213→0x081D865F`.

O caminho prova seleção e gravação de um ponteiro por efeito; não foram seguidos todos os ponteiros até cada bytecode/handler nem observada a execução de uma batalha. Também não foi localizado neste ciclo um teste local de faixa antes do lookup.

## Correspondência estrutural upstream — separada da evidência local

No commit upstream fixado, `include/pokemon.h` define `struct BattleMove` com campos de um byte `effect`, `power`, `type`, `accuracy`, `pp`, `secondaryEffectChance`, `target`, `priority` e `flags`, nessa ordem. Isso é compatível com os offsets locais `+0..+8`, o stride local 12 e os três bytes finais zerados; a correspondência não estabelece que cada nome seja semanticamente correto para esta build.

O mesmo upstream nomeia a tabela de ponteiros de scripts `gBattleScriptsForMoveEffects` e a usa ao escolher um script em `src/battle_main.c`. Isso é compatível com a cadeia local `byte +0 → base 0x081D65A8 → ponteiro → RAM 0x02023D74`. O nome upstream não foi tratado como nome local confirmado.

No upstream, `0x7D` corresponde a `EFFECT_THAW_HIT` em `include/constants/battle_move_effects.h`; localmente só está demonstrado o compare com imediato `0x7D` em `0x08019B58`. O vínculo do ramo local à mesma semântica é hipótese de cruzamento.

## Reprodução e verificação

```bash
python scripts/inspect_move_catalog.py
PYTHONPATH=/tmp/capstone-py bash scripts/run_all_tests.sh
```

O script verifica o hash, os 355 registros candidatos, zeros de `+9..+11`, bytes do dispatch e seus literais, os 214 ponteiros candidatos e o word seguinte. Não escreve no arquivo. A bateria de self-tests deve ser executada com o `PYTHONPATH` temporário porque o Capstone não está instalado no Python global; qualquer falha ambiental ou de teste deve ser registrada separadamente.

## Lacunas e próximo recorte

1. Seguir exemplos de ponteiros de efeito em `0x081D65A8` até os comandos de script e handlers locais, começando por efeitos comuns e por índice 125; distinguir opcode/script de handler nativo.
2. Caracterizar leituras dos offsets ainda não cobertos e procurar outros consumidores do catálogo e caminhos que validem IDs.
3. Seguir estaticamente os predicados que alcançam as gravações de callback, a origem de `0x02023E8A` e o caller externo desses pontos; manter runtime/emulação gated até aprovação de escopo e então conectar a seleção de efeito a um fluxo mais amplo.
4. Em paralelo, manter como trabalho amplo PC/armazenamento, evolução/creche, batalha/IA/captura, encontros, itens, mapas, persistência e demais regiões não inventariadas.

Este é um avanço em uma fatia de dados/consumidores, não conclusão sobre o motor de batalha nem sobre a ROM inteira.
