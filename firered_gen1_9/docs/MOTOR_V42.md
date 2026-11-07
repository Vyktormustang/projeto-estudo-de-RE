# V42 — Bilhetes das ilhas pelo marinheiro de Vermilion

**Concluída em 06/11/2026. 19/19 testes aprovados em 220,527 s, sem falhas, erros ou skips.**

Esta versão resolve a pendência de obtenção dos bilhetes identificada na auditoria da V41. É uma alteração localizada de script: **535 bytes diferentes**, em três regiões. Não expande encontros nem reinicia eventos lendários.

## Como receber

1. Tenha o **Rainbow Pass** na bolsa e a progressão correspondente concluída.
2. Fale com o **marinheiro da balsa no porto de Vermilion**.
3. Ele entrega **Mystic Ticket**, para Navel Rock (Lugia/Ho-Oh), e **Aurora Ticket**, para Birth Island (Deoxys). Depois, continua para o menu nativo da balsa.

Não é necessário Mystery Gift, código externo ou começar um save novo. A entrega acontece ao conversar com esse marinheiro — não automaticamente ao carregar o save ou em todos os portos.

| Situação | Comportamento |
|---|---|
| Nenhum bilhete, duas vagas | Entrega ambos e habilita os dois destinos |
| Bilhete já possuído, liberação ausente | Confirma o bilhete e corrige somente a flag daquele destino |
| Ambos possuídos e liberados | Não duplica nem repete os avisos novos; segue ao menu nativo |
| Bolsa de itens-chave cheia | Não adiciona o que não couber e não concede uma nova liberação sem o item; exibe um aviso |
| Uma única vaga, nenhum bilhete | Mystic primeiro; Aurora fica pendente para outra conversa quando houver espaço |
| Aurora já possuído, Mystic ausente e bolsa cheia | Ainda corrige a liberação do Aurora; a falta de espaço para Mystic não interrompe a verificação do outro bilhete |
| Requisitos de entrega ausentes | Conversa/transporte originais; não antecipa a entrega |

Flags de liberação que já estavam ativas não são apagadas quando uma adição falha. Reparar bilhete já possuído não exige espaço. O aviso de capacidade aparece uma vez por conversa, após processar os dois itens.

**Faça backup independente do save antes de atualizar.** Use o save normal do jogo e “Continuar”; não transporte savestates entre versões. O teste de atualização usou um save sintético escrito pela V41, carregado na V42 e atendido pelo marinheiro **sem sair e entrar no mapa**. Também passou o retorno V42 → V41 → V42.

## O que mudou tecnicamente

- Entrada obrigatória: V41 exata, 33.554.432 bytes.
- Requisitos para **entregar/reparar**: `VAR 0x407E = 3`, `VAR 0x4076 >= 5` e posse do item **368 (Rainbow Pass)**. O item 369 é Tea e não satisfaz o requisito.
- Mystic: item 370, flag `0x084A`. Aurora: item 371, flag `0x084B`.
- Usa `checkitem`, `additem` e `setflag` nativos. Só habilita um item novo após sucesso de `additem`; bilhete existente apenas repara sua flag ausente.
- Usa temporariamente `VAR 0x8000` para reunir falhas de capacidade. Nenhuma variável persistente, formato de save, flag de recebimento nova ou hook ARM foi adicionado.
- Não escreve as flags de recebimento Mystery Gift `0x02A7/0x02A8`, nem limpa flags de batalha, captura, ocultação, fuga ou puzzle.
- Guarda de reprodução do Quest Log (`special 0x0187`, resultado 2), seguindo a convenção nativa. A guarda foi verificada estruturalmente; não se certificou uma sessão completa de replay.

| Região da ROM | Comprimento | Alteração |
|---|---:|---|
| `0x18F32D` | 7 bytes | Salto de script para o novo wrapper, com dois NOPs não executados |
| `0x1135000` | 247 bytes | Script de entrega/verificação |
| `0x1135400` | 287 bytes | Cinco mensagens novas |

O ponteiro do objeto 6 em `0x7C0F3C` **continua sendo `0x0818F32D`**, inclusive para templates antigos em saves. Ao finalizar, o wrapper reproduz os sete bytes originais (`lock`, `faceplayer`, comparação da cena) e continua em `0x0818F334`. As decisões e os menus originais permanecem depois desse ponto.

A reserva `0x1135000..0x1135FFF` estava inteiramente `FF` e não tinha referências de palavras alinhadas na entrada exata. O builder verifica isso, o prefixo original, os registros reais dos itens e ambos os hashes. Reverter as três regiões declaradas restitui **byte a byte** a V41. Os 541 bytes de abrangência contêm seis bytes coincidentes; a diferença efetiva é de 535 bytes.

Preservados estruturalmente: todas as tabelas de encontro, as 68 áreas noturnas, Type: Null, guia, relógio, evoluções, objetos/eventos catalogados e alterações anteriores. Os requisitos acima limitam a nova entrega, **não substituem as regras de acesso que a balsa já tinha** para bilhetes e flags existentes.

## Validação desta versão

**8 testes de construção/contrato + 11 métodos no mGBA, todos na versão final abaixo.** Não se somam aqui as contagens históricas da V40/V41.

- Reconstrução exata, rejeição de entrada errada, saída exclusivamente nova, recusa de sobrescrita/alias da entrada e prova de alterações restritas às três regiões.
- Interpretador independente do bytecode: limites de progresso, posse do Rainbow Pass, guarda de replay, 16 combinações de itens/flags com espaço e as mesmas 16 sem espaço, repetição e recuperação após falta de vaga. Este modelo não substitui a execução nativa.
- **16 combinações nativas de itens/flags** com requisitos de entrega: sempre termina com uma unidade de cada bilhete e as duas liberações.
- Sete controles nativos negativos, incluindo Tea em vez de Rainbow Pass, e limite positivo de progresso 6. A matriz nativa anterior de 16 combinações, sem Rainbow Pass, também foi reexecutada para verificar o comportamento original.
- Bolsa de itens-chave cheia, uma vaga, entrega parcial, segunda conversa após vaga, bilhetes já possuídos, flags anteriores ativas e Aurora reparado mesmo quando a adição do Mystic falha. A liberação de vagas é preparação sintética por API nativa, não demonstra descarte de itens-chave pela interface.
- Três conversas repetidas chegam diretamente ao menu, sem novos avisos de entrega ou duplicação. Cancelamento restaura movimento; campo permanece funcional por mais 3.600 frames (60 segundos emulados).
- **Recebimento real pelo marinheiro seguido de embarque nativo até cada um dos dois portos.** Só a chegada a Vermilion, a progressão e o Rainbow Pass são preparados; os bilhetes e flags de entrega não são injetados nesse teste. Há ainda duas viagens de regressão com bilhetes preparados.
- **Lugia nível 70, Ho-Oh nível 70 e Deoxys nível 30 capturados novamente** por eventos nativos, com Pokémon, flags e desaparecimento do objeto preservados após save normal/Continuar na V42. O puzzle de Deoxys percorre as 11 interações e 52 passos sem forçar os contadores.
- Preservação de um padrão preparado de 12 flags de eventos/recebimento durante a entrega/reparação; atualização de flash V41 → V42, aquisição, retorno à V41 e nova carga na V42 sem perder os bilhetes.
- Novo jogo continua sem os bilhetes/liberações. **2.200 sorteios determinísticos de Altering Cave** revalidam as nove variantes, dia/noite e fallback inválido, mantendo Type: Null nível 20 e 10% nominal.

### Limites

Os testes usam somente estados/saves sintéticos. Progresso e Rainbow Pass foram preparados, não conquistados em uma campanha completa nesta rodada. As três capturas usam chegadas independentes aos locais dos eventos e Master Balls sintéticas; não são uma campanha contínua do início às capturas, nem ensaio de taxa de captura comum. Trajetos internos completos, viagens de retorno, hardware real, link e fidelidade integral a Scarlet/Violet não estão certificados. Saves pessoais não foram abertos ou modificados. As capturas nativas e seu save/Continuar são na V42; o teste de atualização de V41 é separado.

## Identificação

| Arquivo | SHA-256 |
|---|---|
| V41 de entrada | `662225325c50af5aeb568da97a10110cff300aff55e1a6ec87f0d11c1a5f5d50` |
| **V42 final** | **`6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a`** |
| mGBA libretro 0.10.5 | `07ab56ae80ed30486eff67ab4907b345f46ebb5e60f47f98869dc534df18dad9` |

Core construído do commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`, conforme as instruções de construção em `MOTOR_V40.md`. A cadeia V18 → V41 foi reconstruída conferindo cada hash antes de produzir a V42. Nenhuma ROM, save, state ou captura de tela comercial é adicionada ao Git. Sem publicação no Drive, commit ou push.

## Reproduzir com cópias próprias

Na raiz do repositório, com Python, Pillow e o core mGBA indicado:

```sh
python3 -B firered_gen1_9/scripts/motor_v42.py \
  --rom /caminho/FireRed_Gen1-9_motor_v41.gba \
  --saida /caminho/novo/FireRed_Gen1-9_motor_v42.gba

python3 -B firered_gen1_9/scripts/validar_motor_v42.py \
  --base /caminho/FireRed_Gen1-9_motor_v41.gba \
  --rom /caminho/novo/FireRed_Gen1-9_motor_v42.gba \
  --core /caminho/mgba_libretro.so \
  --saida /caminho/resultados-v42-novos
```

O diretório de resultados precisa ser novo. O runner seleciona somente as três classes relevantes e retorna falha se houver erro, falha de teste ou skip. Resultados complementares: `motor_v42_resultados.json`, `motor_v42_observacoes.json`, `motor_v42_estrutura.json`, `motor_v42_matriz.csv`, `motor_v42_capturas.csv` e `motor_v42.log`.
