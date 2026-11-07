# Auditoria de obtenção — 1.025 Pokémon na V40

**06/11/2026 · somente leitura · nenhuma V41 gerada**

## Resposta: quanto falta?

**Foram identificadas referências de obtenção para os 1.025 Pokémon. Isso não significa que os 1.025 estejam comprovadamente acessíveis numa campanha normal.**

- **931/931 não lendários/míticos** constam nas tabelas selvagens, incluindo Ultra Beasts, Paradox e Unown nas câmaras de Tanoby.
- Os **94 lendários/míticos** têm referências em tabelas, objetos adicionais, eventos nativos ou evoluções. Não há espécie sem qualquer referência no levantamento.
- A pendência mais concreta é **Type: Null**: sua tabela existe e gera a espécie, mas exige **a variante 7 de Altering Cave**, não a padrão. Falta comprovar um meio normal de selecionar essa variante, ou propor uma correção.
- **Lugia, Ho-Oh e Deoxys** possuem eventos nativos rastreados. Falta comprovar o acesso às ilhas, incluindo bilhetes/condições de liberação, e executar os eventos completos.
- Para **Solgaleo e Lunala no mesmo save**, falta verificar uma segunda cópia de Cosmog ou a repetibilidade de sua obtenção. O inventário contém um objeto adicional de Cosmog; demonstrar as duas evoluções isoladamente não resolve esse ponto.

**Não é correto dizer que “faltam adicionar quatro Pokémon” nem que “todos já são capturáveis”.** Há uma condição de seleção de tabela confirmada, acessos especiais ainda não certificados e validações de campanha pendentes. Não foi feita nenhuma alteração para resolver esses pontos nesta etapa.

A expansão noturna é outra métrica: permanece em **68 de 78 áreas terrestres elegíveis**. As dez áreas restantes não equivalem a dez espécies ausentes.

## Contagem sem duplicações

A planilha principal escolhe uma referência por espécie; alternativas estão nos arquivos auxiliares.

| Referência preferencial | Espécies | O que foi estabelecido |
|---|---:|---|
| Tabelas terrestres/aquáticas elegíveis | 931 | Espécie, mapa, slot, período e nível lidos da V40 |
| Unown em Tanoby | 1 | Presença nas tabelas condicionadas ao desbloqueio |
| Objetos fixos adicionais, sem referência preferencial acima | 81 | Objeto ativo, espécie, posição, flag e script compartilhado |
| Eventos lendários nativos | 7 | Caminho de script desde o mapa até preparar a espécie e iniciar batalha |
| Cresselia e Type: Null em tabelas condicionais excluídas da distribuição comum | 2 | Dados estruturais e sondagens nativas no emulador |
| Cosmoem, Solgaleo e Lunala por evolução | 3 | Registros e retorno da rotina nativa no emulador |
| **Total** | **1.025** | **Referências, não certificado de capturas** |

A primeira linha contém **930 não lendários/míticos + Terapagos**. O outro não lendário/mítico é Unown, separado na segunda linha. Assim, a contagem de 931 da primeira linha não deve ser confundida com o conjunto de 931 não lendários/míticos.

Há **110 objetos adicionais ativos**: 81 lendários/míticos, 9 Ultra Beasts e 20 Paradox. Os últimos 29 já têm referência preferencial em tabelas. **224 objetos estacionados em (-1024,-1024) foram excluídos**, em vez de contados como disponíveis. Foram verificados 1.982 objetos do catálogo de 425 mapas e as 334 referências ao script compartilhado.

A união bruta de tabelas selvagens e objetos adicionais cobre **1.015 espécies**. As dez restantes são exatamente os sete eventos nativos e as três evoluções abaixo. A leitura bruta das tabelas encontra 934 espécies; o critério histórico de tabelas elegíveis, incluindo a exceção de Unown em Tanoby, encontra 932. A diferença são Cresselia e Type: Null.

## Pontos especiais e resultados do emulador

### Type: Null — seleção de tabela ainda pendente

- Local: **SixIsland_AlteringCave**, grupo/mapa **1/122**.
- Entrada efetiva: header **130**, variante **7**, slot **2**, nível **20**, **10% nominal**.
- A rotina nativa consulta **VAR 0x4024**: valores 0–8 selecionam headers 123–131; valores acima de 8 voltam ao header 123.
- Em sondagens com estado sintético, foram testados 0–8, 9 e 65535, de dia e à noite. No mesmo sorteio do slot 2, **somente a variante 7 gerou Type: Null**. A variante 0 gerou Trubbish, nível 8.
- **Não foi comprovado um seletor normalmente acessível para chegar à variante 7.** Não se deve apresentar “Altering Cave, 10%” sem essa condição. A ausência de um caminho verificado não prova impossibilidade absoluta.

### Cresselia — geração confirmada, desbloqueio natural pendente

- Local: **SevenIsland_TanobyRuins_DilfordChamber**, **2/30**, slot **1**, nível **25**, **20% nominal**.
- **FLAG 0x849 desligada:** a consulta nativa retornou `0xFFFF`, sem header de encontro.
- **Flag ligada:** header **3**; a chamada nativa de geração criou **Cresselia válida, nível 25**, tanto de dia quanto à noite.
- O mapa não força toda espécie a virar Unown. Cresselia foi gerada como Cresselia.
- O desbloqueio pelo puzzle, o deslocamento até a câmara e uma captura caminhando normalmente **não foram executados nesta auditoria**. Unown também depende do desbloqueio de Tanoby; suas formas não foram auditadas individualmente.

### Cosmog → Cosmoem → Solgaleo / Lunala

Cosmog tem objeto adicional em **RockTunnel_1F**, objeto **11**, posição **(12,12)**, flag `0x5315`. Não foi capturado nesta etapa.

| Origem | Nível testado | Retorno da rotina de evolução |
|---|---|---|
| Cosmog | 42 | Nenhum |
| Cosmog | 43, 44 e 100 | Cosmoem |
| Cosmoem | 52 | Nenhum |
| Cosmoem | 53 | Solgaleo |
| Cosmoem | 54, 55 e 100 | Lunala |

Todos esses limites foram testados de dia e à noite. Everstone bloqueou as evoluções nos casos de controle. A tabela tem método 4 (nível): Cosmog ≥43 → Cosmoem; Cosmoem ≥53 → Solgaleo; a entrada posterior de Cosmoem ≥54 → Lunala prevalece.

**É uma regra simplificada da base, não a regra moderna por versão/horário.** Para buscar Lunala por essa cadeia, é necessário manter Cosmoem sem evoluir no nível 53. Foram testados retornos de função, com checksum e estado do Pokémon preservados, **não as cenas completas de evolução/cancelamento**. Também falta validar a obtenção de cópias suficientes para as duas ramificações no mesmo save; não foi presumida reprodução ou troca disponível.

## Sete eventos nativos localizados

Offsets abaixo são **de arquivo**, hexadecimais. IDs das espécies são nacionais.

| Pokémon | Local | Nível | Raiz do script | Gatilho |
|---|---|---:|---|---|
| Articuno #144 | SeafoamIslands_B4F | 50 | `18BB98` | Objeto 3 |
| Zapdos #145 | PowerPlant | 50 | `18C1A4` | Objeto 6 |
| Moltres #146 | MtEmber_Summit | 50 | `18C51F` | Objeto 1 |
| Mewtwo #150 | CeruleanCave_B1F | 70 | `18AEE1` | Objeto 3 |
| Lugia #249 | NavelRock_Base | 70 | `18DB20` | Objeto 1 |
| Ho-Oh #250 | NavelRock_Summit | 70 | `18D9E7` | Coordenada (9,12), VAR 0x4001 = 0 |
| Deoxys #386 | BirthIsland_Exterior | 30 | `18DC5D` | Triângulo, objeto 1; sequência condicional |

O script nulo no objeto visual de Ho-Oh ou Deoxys **não indica ausência do evento**: Ho-Oh tem gatilho de coordenada; Deoxys parte do triângulo. O decodificador seguiu limites de instruções e branches desde essas raízes, até `setwildbattle` ou `CreateEnemyEventMon`, seguido de `StartLegendaryBattle`. Não foi usada busca cega pelo byte de criação.

O JSON registra os offsets de preparação, início da batalha e sequência de instruções de cada caminho. **Branches possíveis não provam que suas condições sejam satisfeitas em jogo.** Bilhetes, flags, puzzles, reaparecimento, batalha e captura desses sete eventos não foram certificados. A obtenção normal de Mystic/Aurora Ticket e as condições do transporte devem ser verificadas na base real, não inferidas de outra revisão de FireRed.

## Entregáveis e como ler

- **[cobertura_1025_v40.csv](cobertura_1025_v40.csv):** 1.025 linhas, uma por espécie; referência preferencial, local, período, nível quando extraído, chance de slot e pendências.
- **[locais_obtencao_v40.csv](locais_obtencao_v40.csv):** 2.992 ocorrências em tabelas, incluindo slots diurnos/noturnos e variantes de Altering Cave. São linhas de slots, não 2.992 espécies ou locais únicos.
- **[eventos_obtencao_v40.csv](eventos_obtencao_v40.csv):** 117 referências de evento — os 110 objetos adicionais ativos e os sete eventos nativos. Inclui as alternativas dos 29 objetos já cobertos por tabelas.
- **[evolucoes_v40.csv](evolucoes_v40.csv):** 449 registros nativos, com origem, destino, método numérico, parâmetro, posição e offset. Só a cadeia de Cosmog recebeu as sondagens desta etapa; exportar os demais registros não certifica todas as evoluções.
- **[auditoria_obtencao_v40.json](auditoria_obtencao_v40.json):** contagens, objetos ativos e evidência dos caminhos nativos.
- **[sondagens_obtencao_v40.json](sondagens_obtencao_v40.json):** 46 observações — 22 evoluções, 22 seleções/gerações de Altering Cave e duas verificações de bloqueio/liberação/geração em Tanoby.
- **[validacao_obtencao_v40.json](validacao_obtencao_v40.json)** e **[auditoria_obtencao_v40.log](auditoria_obtencao_v40.log):** identificação dos 14 métodos, resultado e ambiente.

Períodos: **dia 06:00–19:59 / noite 20:00–05:59**, pelo tempo acelerado do jogo, não RTC. “Ambos” significa que a entrada não usa a substituição noturna da V40; não remove condições de progresso.

Chances são **nominais por slot e condicionais ao encontro da modalidade**, antes de Repel e demais filtros, não frequência por passo. A referência preferencial de tabela usa maior chance de slot, depois menor nível e desempates determinísticos: não é promessa de caminho mais cedo na campanha. Campos vazios significam “não aplicável/não extraído”, não zero. Níveis dos objetos adicionais não foram extraídos. Os nomes seguem o catálogo técnico; `group/number` e offsets permitem desambiguação. A cobertura é por espécie nacional, não por todas as formas.

## Validação e limites

**14/14 métodos aprovados em 23,245 s**, sem falhas, erros ou skips: **10 estruturais + 4 de sondagens nativas em mGBA**. A rodada inicial teve erro de configuração do caminho do core; o caminho foi corrigido e a rodada final completa passou. Não foi problema da ROM.

- Integridade da ROM e dos catálogos; rejeição de entrada errada/corrompida.
- Cobertura de 1.025 IDs únicos, categorias exclusivas e nenhuma promoção de objetos estacionados.
- Referências de eventos, rejeição de opcode desconhecido e falso positivo em dados de mensagem.
- Tabelas noturnas reais confrontadas com a política V40, 68 × 12 slots noturnos.
- Reprodutibilidade de CSV/JSON, saída exclusiva em diretório novo, ROM inalterada.
- Fixture sintético novo na V40 exata. Flags, variáveis, mapa e RNG foram preparados **nas cópias do estado para chamadas isoladas**. Não houve campanha percorrida, captura individual ou importação de estado de outra versão.

Os **103 testes da entrega V40** continuam como resultado histórico separado; **não foram reexecutados aqui nem somados aos 14**. Esta auditoria não é certificação de campanha, disponibilidade de todos os itens/serviços, link/troca, reprodução, “living dex”, todas as capturas, hardware, saves pessoais ou fidelidade total a Scarlet/Violet.

### Reprodução a partir da raiz do repositório

O script só lê a ROM e exige diretório de saída inexistente:

```sh
python3 -B firered_gen1_9/scripts/auditar_obtencao_v40.py \
  --rom deliver/v40/FireRed_Gen1-9_motor_v40.gba \
  --saida deliver/auditoria_1025_nova
```

Para testes, configure `AUDITORIA_V40_ROM` com o caminho absoluto da V40, `MGBA_CORE` com o core mGBA 0.10.5 e, opcionalmente, `AUDITORIA_V40_PROBES` com um **arquivo novo** para as observações. No ambiente com as dependências do harness:

```sh
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests python3 -B -m unittest -v \
  test_auditoria_obtencao_v40.AcquisitionAuditTests \
  test_auditoria_obtencao_v40_mgba.AcquisitionNativeProbes
```

- ROM V40, 33.554.432 bytes: SHA-256 `10214ba64a38a543d381db9d41eb37f46458a0926057d028dda2839b1f87e7e1`.
- Core mGBA 0.10.5, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`: SHA-256 `07ab56ae80ed30486eff67ab4907b345f46ebb5e60f47f98869dc534df18dad9`.
- Semântica de referência: [pret/pokefirered](https://github.com/pret/pokefirered/tree/ce6406d8c2eaf46d543c8a2606de0c3cb1951982), commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; ponteiros, IDs e resultados vieram da V40, não de offsets importados da referência.

## Próxima etapa recomendada

1. **Type: Null:** rastrear como VAR 0x4024 chega a 7 na base real; se não houver meio normal utilizável, propor um encontro acessível que não dependa dessa seleção.
2. **Lugia/Ho-Oh/Deoxys:** verificar entrega dos bilhetes e liberação do transporte; depois executar gatilho, batalha, captura e persistência dos três eventos.
3. **Cadeia de Cosmog:** executar evolução/cancelamento e verificar repetição/segunda cópia para Solgaleo e Lunala no mesmo save.
4. **Tanoby e demais rotas:** verificar o desbloqueio natural e ampliar a amostragem de acessos e capturas. Não declarar as demais espécies certificadas por exclusão.

**Entrega local. Nenhuma ROM, tabela de encontro, flag de progresso ou save pessoal foi alterado. Sem publicação no Drive, commit ou push.**
