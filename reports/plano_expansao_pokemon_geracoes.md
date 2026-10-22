# Plano de expansão da ROM BR: espécies, ataques e tipos

**Estado:** plano de trabalho aprovado pelo usuário; etapa inicial de escopo e inventário em andamento. Ainda não houve modificação da ROM ou de saves.

## Objetivo

Expandir Pokémon FireRed BR para comportar o conjunto de espécies, formas, movimentos e tipos definidos por um corte oficial versionado, com dados em português brasileiro, integração no motor de batalha e validação de save/partida. O alvo da geração e a lista de formas devem ser congelados antes da importação completa de dados; este documento não presume um número de geração atual.

## Regras de implementação e evidência

- A ROM local e seus bytes são a fonte de verdade sobre o que esta build suporta hoje. Nomes ou layouts upstream são pistas cruzadas, não evidência da ROM BR.
- Não ampliar uma tabela com base somente em um limite estrutural candidato: primeiro mapear consumidores e verificações de faixa.
- Gerar tabelas binárias de um dataset canônico, versionado e validado; evitar edição manual de bytes como processo de produção.
- Separar dados do movimento de sua implementação: cada efeito precisa estar implementado e testado para ser anunciado como funcional.
- Preservar a ROM original e saves. Qualquer patch deve identificar hash da ROM-base e ter backup/migração testada.
- Ghidra se aplica a código nativo; REA se aplica à investigação transversal de arquivos. Nenhum foi usado nesta auditoria inicial; Capstone não os substitui.

## Escopo provisório proposto — ainda precisa de congelamento

1. Todas as espécies oficiais existentes até uma versão-alvo explicitamente fixada, incluindo formas com diferenças de jogo (stats, tipo, habilidade, learnset ou evolução).
2. Formas puramente cosméticas registradas como variantes de recurso/dex, sem criar IDs de espécie extras salvo exigência da ROM.
3. Todos os movimentos oficiais do mesmo corte; registrar dados e learnsets de nível, TM/HM, tutor e ovo conforme disponível.
4. Habilidades necessárias aos Pokémon/efeitos incluídos e todos os tipos necessários no corte. O motor deve usar tabelas de tipos extensíveis, sem presumir o limite futuro.
5. Português brasileiro; jogo solo primeiro. Trocas/compatibilidade de rede ficam fora do primeiro marco, a menos que o escopo seja alterado.
6. Saves existentes devem ser preservados quando tecnicamente seguro; se houver mudança incompatível, definir migração e requisito de backup antes da entrega.

### Decisões que bloqueiam a importação integral

- Versão/data do dataset e jogos oficiais que definem “geração atual”.
- Inclusão de formas temporárias (Mega, primal, Dynamax/Terastal ou equivalentes do corte), formas cosméticas, gender forms e variantes regionais.
- Se trocas e interação com outras ROMs são requisito desde o primeiro lançamento.
- Política final de compatibilidade de save e ativos gráficos/sonoros.

Podemos avançar na auditoria de arquitetura enquanto essas decisões estão pendentes; não devemos congelar IDs nem importar milhares de dados antes delas.

## Inventário inicial confirmado na ROM local

ROM `google_drive/Pokemon - Fire Red (BR).gba`: 16.777.216 bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.

Os verificadores existentes foram executados novamente nesta etapa:

- `scripts/inspect_species_table.py`: região candidata em `0x08254784`, stride `0x1C`, 412 registros examinados (índice 0 zero; 411 não-zero), fim estrutural candidato `0x08257494`. O relatório do ciclo 19 ressalta que isso não prova todos os limites de todos os consumidores nem autoriza extensão.
- `scripts/inspect_level_up_learnsets.py`: tabela de 412 ponteiros em `0x0825D7B4`; 411 destinos únicos/entradas não-zero, listas candidatas terminadas em `0xFFFF`; máximo local decodificado de nível 99 e ID de movimento 354. A semântica e mapeamento integral para espécies dependem dos limites do jogo e do cross-reference.
- `scripts/inspect_move_catalog.py`: região candidata de 355 registros de 12 bytes em `0x08250C04` (índices 0–354), com byte `+0` entre 0 e 213; a tabela de scripts candidata em `0x081D65A8` tem 214 ponteiros internos à ROM. Limites estruturais não substituem auditoria de faixa dos callers.
- `scripts/inspect_typecalc_path.py`: tabela candidata local em `0x0824F050`, 112 registros de 3 bytes até sentinela/terminador; o handler local usa registros de movimento e campos de tipo. Nem todo consumidor/efeito foi seguido dinamicamente.
- Ciclo 17 já documenta uma camada de dados BoxMon/equipe: cópia de `0x50` bytes para a extensão local de equipe e acessores a campos; interpretação estrutural upstream permanece separada.

Todos esses comandos terminaram com status de sucesso e conferiram o hash esperado. Isso é uma revalidação dos artefatos existentes, não uma nova prova de capacidade para a geração-alvo. Nenhuma ROM/save foi escrita. A ROM ter bytes `FF` no final não prova, por si só, espaço livre utilizável; o mapa de espaço e a estratégia de extensão ainda precisam de validação.

## Etapas, gates e entregáveis

### Fase 0 — Congelar requisitos e fontes

**Ações:** decidir corte oficial, espécies/formas, categorias de movimentos, habilidades, idioma, compatibilidade e política de saves. Escolher fontes de dados versionadas e registrar origem/licença dos recursos. Criar manifest com IDs externos, IDs internos, aliases, formas e regras de conversão.

**Gate:** nenhum campo crítico de escopo fica implícito; dataset de referência tem versão/hash e número esperado de espécies, formas, movimentos, habilidades e tipos.

### Fase 1 — Auditoria de limites e consumidores da ROM

**Ações:** mapear tabelas, strides, regiões ROM, dispatches e cada caminho que indexa espécies/movimentos/tipos/learnsets. Procurar truncamentos, sentinelas, limites máximos e IDs fixos em scripts, UI, dex, party, PC, save/load, evolução, ovos, encontros, captura, batalha, itens e animações. Auditar buffers/tamanhos de texto e referências gráficas. Medir espaço livre com um verificador reproduzível e determinar como novos dados/código seriam endereçados.

**Gate:** ledger de consumidores com evidência local, limites confirmados/hipotéticos separados, plano de patching e save com riscos residuais declarados.

### Fase 2 — Dataset canônico e gerador

**Ações:** esquema normalizado para espécie/forma, tipos, habilidades, atributos, movimentos, efeitos, learnsets e assets. Validadores para IDs únicos, referências, faixas, campos obrigatórios, compatibilidade de learnsets e arquivos ausentes. Gerar relatórios e estruturas ROM sem gravar na ROM original.

**Gate:** geração determinística, testes unitários e diff auditável entre fonte e saída.

### Fase 3 — Prova vertical de capacidade

**Ações:** prototipar uma espécie além do maior índice atual, uma forma com dados distintos se no escopo, um movimento novo e, se necessário, um tipo não representável hoje. Exibir em Pokédex/resumo; encontrar/capturar/ensinar; batalhar; salvar/carregar; validar caixas e party.

**Gate:** prova reproduzível sem corrupção ou regressão. Se não passar, revisar arquitetura antes de importar o catálogo completo.

### Fase 4 — Ampliar estruturas, índices e saves

**Ações:** adaptar tabelas, rotinas, ranges, strings e armazenamento para o tamanho-alvo; escolher mecanismo de expansão de ROM; testar leitura/escrita de ID alto em todos os consumidores. Definir versão de save, migração e fallback seguro.

**Gate:** testes de limites inferior/superior e upgrade de save passam, ou requisito de partida nova é explícito e verificado.

### Fase 5 — Importar espécies, formas e aprendizado

**Ações:** integrar species data, tipos, habilidades, experiência, evolução, learnsets, reprodução e variantes. Completar nomes, descrições e recursos de cada forma incluída. Gerar auditorias de dados faltantes e de mapeamento.

**Gate:** 100% das entradas da lista-alvo têm dados obrigatórios válidos e nenhuma referência fora do intervalo.

### Fase 6 — Motor de movimentos e tipos

**Ações:** definir esquema de efeitos; implementar famílias e efeitos especiais; revisar categorias físico/especial, prioridade, alvo, precisão, PP, status, clima, campos, múltiplos golpes e interações. Integrar tabela de eficácia completa e tipos adicionais, se houver. Criar testes de batalha com resultados esperados para cada efeito.

**Gate:** todo movimento do escopo é classificado como implementado/testado ou explicitamente não suportado; nenhum é silenciosamente tratado como outro efeito.

### Fase 7 — Interface, dex e ativos

**Ações:** atualizar menus, ordenação/busca, tela de equipe, PC, dex, evolução, aprendizado, nomes longos, acentos, paletas, sprites, ícones, cries, animações e mensagens. Fazer revisão visual/sonora em emulador.

**Gate:** navegação funciona em índices altos; recursos obrigatórios presentes; fallback de qualquer recurso ausente é intencional.

### Fase 8 — QA, release e documentação

**Ações:** testes automatizados de dataset/ROM, testes de regressão, cenários de captura/evolução/troca interna/save-load e partidas longas; testes de emulador e hardware conforme escopo. Criar patch para a ROM-base exata, notas de instalação, compatibilidade, migração e limitações.

**Gate:** patch reproduzível, ROM-base validada por hash, saves testados e matriz de cobertura publicada.

## Primeiros resultados da Fase 1 — ledger de consumidores e lacunas

| Domínio | Evidência local atualmente revalidada | Cobertura/risco que permanece |
|---|---|---|
| Espécies | `0x08254784`, stride `0x1C`, região candidata com 412 posições; ciclos 18–19 seguem cálculo de stats/nível e leituras de offsets usados como tipos, habilidades e outro campo. | Contagem é candidata, vários campos/consumidores não auditados; 56 ocorrências u32 brutas da base em ROM são pistas, não 56 xrefs de código validados. Não assumir que adicionar registros é seguro. |
| Crescimento/XP | Base `0x08253AE4`, stride `0x194`; o cálculo de nível por growth rate foi seguido em ciclo 18. | Outros consumers, limites, alteração de curvas e comportamento futuro sem teste dinâmico. |
| Learnsets | Tabela candidata de 412 ponteiros em `0x0825D7B4`; cinco consumidores locais já identificados: `0x0803E9E0`, `0x0803EA88` (ciclo 20), `0x08043C84`, `0x08043DD4` e `0x08043E2C`. Nos três últimos, a ROM implementa cap de 20 entradas por lista; detalhes em `reports/auditoria_fase1_consumidores_learnsets.md`. | Listas locais observadas têm 1–18 palavras, mas compatibilidade com novas IDs e os demais callers ainda precisa ser auditada. Dataset do corte deve sinalizar listas com >20 entradas; suportá-las exige revisar/testar esses caminhos. |
| Movimentos | 355 registros candidatos × 12 bytes em `0x08250C04`; byte `+0` atual máximo 213 para 214 scripts candidatos; campo move em learnsets usa `0x01FF` (ID numérico máximo 511), enquanto o maior ID atual decodificado é 354. | Campos `+3`, `+5`, `+7` e outros offsets ainda incompletos; lookup `ID×12` sem clamp visível nos trechos examinados; suporte a novos efeitos depende de expandir/testar dispatch. Detalhes: `reports/auditoria_fase1_limites_moves_tipos.md`. |
| Tipos/eficácia | Tabela candidata em `0x0824F050`, 112 registros × 3 bytes; bytes de tipo observados até 17 e máscara dinâmica local `0x3F` (ciclo 25); três leitores adicionais seguidos em `0x08039DB4`, `0x08023C38` e `0x08029DAC`. Quatro entradas candidatas de scripts de efeito contêm `0x4A` e uma contém `0xA6`, com registros candidatos apontando para elas (índices de registros 68, 176, 205, 301, 243 e 280); esses valores numéricos também ocorrem nas listas locais candidatas de learnsets. | Em `0x08029DAC`, o LCG permite índice 112 (um além do limite candidato), lê `C8 C9 CC` e rejeita o registro ao testar `+2 > 5`; leitura além da tabela confirmada estaticamente, sem efeito dinâmico provado. O código 9 aparece em move `+2`, mas não nos offsets de espécie ou nas linhas ativas do chart; sem semântica atribuída. A rota estática de callbacks até o lookup foi seguida; os predicados/estado runtime e origem de `0x02023E8A`, a execução em batalha, UI/enum e efeitos seguem pendentes. Detalhes/verificadores: `reports/auditoria_fase1_limites_moves_tipos.md`, `reports/auditoria_fase1_consumidor_typechart_secundario.md`, `scripts/inspect_typechart_bounds.py` e `scripts/inspect_typechart_script_references.py`. |
| Party/BoxMon/save | Ciclo 17 analisou acessores BoxMon/equipe, bloco cifrado e checksum; conversão copia 0x50 bytes e acessa extensão de equipe. | Migração de saves, IDs altos em cada getter/setter, slots/PC, estruturas persistentes e round-trip não testados. |
| UI/Pokédex/assets | Nenhuma auditoria suficiente de todos os nomes, descrições, sprites, ícones, paletas, cries, animações ou limites de menu nesta iniciativa. | Trilha aberta: inventariar asset, tabelas de texto, renderizadores e buffers, além de sua indexação por espécie/move/type. |
| Espaço/patch | Imagem-base tem 16 MiB; os validadores acima não escrevem na ROM. | Espaço livre e estratégia de expansão não validados; bytes `FF` no fim ou um mapa antigo não bastam como prova. |

O script `scripts/scan_expansion_table_literals.py` revalida ocorrências brutas de palavras little-endian nas bases candidatas e, opcionalmente, candidatos Thumb LDR literal: 56/55 species, 18/18 experience, 6/6 learnset pointers, 137/136 moves, 6/6 effect-script table e 9/9 typechart (brutas/com padrão LDR candidato). O padrão/opcode e a contagem são apenas índices de busca; cada endereço ainda precisa ser classificado como instrução alcançável, falsa coincidência ou referência efetiva antes de afirmar consumidor.

## Próxima tarefa concreta

Continuar Fase 0 e Fase 1 como auditoria somente leitura: classificar os candidatos de referência e ampliar o ledger para todos os consumidores de espécies, movimentos, tipos, learnsets, save/party/PC e assets; levantar limites e estratégia de patch. Não escrever na ROM nem importar o catálogo integral. Antes de dados completos, congelar as decisões de corte/formas/compatibilidade e aprovar uma prova vertical.

Este projeto não é concluído pelos ciclos de comandos de batalha. A compreensão ampla da ROM e a expansão de conteúdo são trilhas relacionadas, mas a meta de “todos os Pokémon” só estará concluída quando os gates de conteúdo, motor, assets, saves e QA forem satisfeitos.
