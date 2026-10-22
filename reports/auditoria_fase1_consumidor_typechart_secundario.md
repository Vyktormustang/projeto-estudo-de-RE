# Fase 1 — leitores adicionais da tabela local de effectiveness

**Estado:** seguidos estaticamente três fluxos locais fora do handler typecalc do ciclo 25: uma rotina que consome os tipos armazenados por espécie, um fluxo de batalha que consulta move/estrutura e effectiveness, e um leitor de effectiveness chamado duas vezes por uma rotina superior. No leitor de índice aleatório, o código admite numericamente o índice 112 para uma tabela observada com índices 0–111: registramos como risco de leitura one-past, não como bug dinâmico confirmado. Call paths/runtimes completos continuam parciais. Nenhuma ROM/save foi modificada.

## Proveniência e método

- ROM BR local, somente leitura, 16 MiB; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Desmontagem Thumb com Capstone 5.0.7 temporário (`/tmp/capstone-py`); as palavras-base, pools, sequências e callsites citados foram conferidos contra bytes locais.
- Tabela/handler já revalidados por `scripts/inspect_typecalc_path.py` e `scripts/inspect_expansion_numeric_domains.py`. REA/Ghidra e emulação não foram usados.
- Identificadores de tipo/ability e propósitos de jogo não são atribuídos aos códigos numéricos locais.

## Leitor local `0x08039DB4` e caller `0x08039E3C`

A rotina `0x08039DB4` tem prólogo Thumb em `0x08039DB4` e retorna em `0x08039E34`. Ela preserva os argumentos: `r0` em stack local, `r1` em `sb`, `r2` em `r8` e `r3` em `r6`. Em `0x08039DD6`, carrega da pool em `0x08039E38` o endereço `0x0824F050` e percorre registros de três bytes:

1. Se o byte `+0` do registro for `0xFF`, sai; se for `0xFE`, avança três bytes sem o caminho normal.
2. Para os demais registros, compara `+0` com o valor inicial `r0` e `+1` com `r1`/`r2` preservados.
3. Nas correspondências, lê `+2`, multiplica por esse valor o byte apontado por `r3`, divide o produto por 10 via helper `0x081E4018` e escreve o resultado no mesmo endereço.
4. Avança pelo stride 3 até `0xFF`.

O chamador `0x08039E3C` chama esse helper nos sites locais `0x08039FAE` e `0x08039FBC`. Antes disso, lê um valor pelo dispatcher `0x0803FBE8` com seletor `0x0B`, indexa a base de espécies `0x08254784` por esse valor × `0x1C` e carrega os bytes `+6/+7`. Inicializa um byte local com 10 e chama o helper duas vezes, passando em `r0` bytes em offsets `+0x21` e `+0x22` de uma estrutura indexada por stride `0x58`, além dos dois bytes da tabela de espécie e do endereço do byte local. Isso demonstra o encadeamento local SpeciesInfo `+6/+7` → lookup do typechart → atualização de um valor; não atribuo nomes aos tipos ou ao valor atualizado.

Sites BL diretos da ROM para `0x08039E3C`: `0x08038760` e `0x08039CB8`. O propósito superior desses fluxos não foi determinado. O helper percorre até terminador sem contador máximo; falta testar comportamento se o terminador estiver ausente/deslocado.

## Fluxo local `0x08023C38`

A rotina começa em `0x08023C38` com prólogo Thumb e retorna em `0x08023E58`. Ela lê o ID corrente em `0x02023D4A`, calcula `ID × 12 + 0x08250C04` e carrega o byte `+2` do registro. Também calcula uma estrutura a partir de `0x02023BE4 + índice × 0x58` e lê o byte `+0x20`.

Se esse byte for `0x1A` e o código de tipo do move for `4`, toma um ramo especial; caso contrário, entra no scan que usa a base `0x0824F050` carregada em `0x08023CCC` a partir da word em `0x08023CD8`. No scan local:

- compara o byte `+0` de cada linha com o byte de tipo do move;
- compara `+1` com bytes em offsets `+0x21/+0x22` da estrutura de stride `0x58`;
- consulta `+2`; os valores imediatos `0`, `5` e `20` têm ramos distintos que alteram flags locais;
- avança de três em três; `0xFF` encerra, e `0xFE` toma um ramo que testa um bit de uma word em offset `+0x50` da estrutura.

Depois do scan, há outros testes locais, incluindo comparação com imediato `0x19` e leitura do byte `+1` do registro de move. Esta nota não nomeia os imediatos, os bits, nem os efeitos finais. O caller/entry path dessa rotina não foi estabelecido.

## Fluxo local `0x08029DAC` e leitura one-past potencial

A rotina tem prólogo em `0x08029DAC` e usa o helper local `0x08044EC8`, cuja sequência lê um estado, multiplica/soma constantes, grava o novo estado e retorna a metade alta. O trecho `0x08029E9C–0x08029EBE` mascara o retorno com `0x7F`, compara com `0x70` e repete somente quando o valor é maior que 112. Para valores aceitos, calcula `3 × valor`, soma `0x0824F050` e lê o byte no começo dessa posição.

A tabela delimitada localmente tem 112 registros, índices 0–111, intervalo `[0x0824F050, 0x0824F1A0)`. Como `0x70` (112) passa pela comparação `bhi`, há um valor permitido que aponta para `0x0824F1A0`, logo após o intervalo; os bytes locais nesse endereço começam `C8 C9 CC`. A rotina usa o byte lido em comparações antes de qualquer uso posterior da linha. Isto é uma **possibilidade estática de leitura um registro além do limite candidato**; sem execução, sem determinar a distribuição/alcance do RNG neste fluxo e sem rastrear todas as condições, não afirmamos crash, corrupção nem efeito de jogo.

A mesma rotina contém um segundo scan em `0x08029F0A`: incrementa o deslocamento em 3 e compara com literal `0x14F` (335), cobrindo offsets 0–333, isto é, 112 posições (0–111). Esse limite é coerente com o comprimento candidato e contrasta com o caminho aleatório que admite índice 112. A word local `0x08029F90` fornece a base em ambos os loads (`0x08029EAC` e `0x08029F0A`). Caller/alcance do fluxo `0x08029DAC` ainda não rastreados.

## Fechamento das ocorrências candidatas e lacunas

O scanner encontra nove palavras brutas coincidentes com `0x0824F050`. O ciclo 25 examinou seis dentro/ao redor do handler `0x0801E848`; esta nota seguiu as outras três words: `0x08023CD8`, `0x08029F90` e `0x08039E38`. A classificação descreve código local estático; não prova que todos os fluxos sejam alcançados em cada modo de jogo ou que outros leitores indiretos inexistam.

## Próximo passo

1. Rastrear os callers/dispatch indiretos de `0x08023C38` e `0x08029DAC` e verificar se o índice 112 é alcançável antes de decidir se a leitura one-past é funcional, inalcançável ou erro.
2. Verificar testes/control flow em contexto isolado, sem editar ROM/save-base; manter a tabela fechada até compreender todos os leitores.
3. Continuar inventário de UI, nomes, ícones e outros consumidores de tipos; este relatório não demonstra suporte geral a novos códigos de tipo.
