# Fase 1 — leitores adicionais da tabela local de effectiveness

**Estado:** seguidos estaticamente três fluxos locais fora do handler typecalc do ciclo 25: uma rotina que consome tipos da espécie, um fluxo de batalha que consulta move/estrutura e effectiveness, e um leitor chamado duas vezes por uma rotina superior. Além dos handlers na tabela local de comandos, foram encontradas entradas de scripts de efeito que contêm `0x4A` e `0xA6` em limites compatíveis com os comandos. Um registro candidato de move local seleciona cada entrada de efeito, mas nenhuma batalha foi executada. O handler `0x08029DAC` admite numericamente o índice 112 para uma tabela observada com índices 0–111; o RNG local tem ciclo matemático completo, mas a sequência de jogo não foi executada. Registramos leitura além do limite candidato seguida de rejeição, não um bug/efeito de jogo confirmado. Nenhuma ROM/save foi modificada.

## Proveniência e método

- ROM BR local, somente leitura, 16 MiB; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Desmontagem Thumb com Capstone 5.0.7 temporário (`/tmp/capstone-py`); as palavras-base, pools, sequências e callsites citados foram conferidos contra bytes locais.
- Tabela/handler já revalidados por `scripts/inspect_typecalc_path.py` e `scripts/inspect_expansion_numeric_domains.py`. REA/Ghidra e emulação não foram usados.
- Cross-reference de nomes e tamanhos de macros: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; `asm/macros/battle_script.inc` SHA-256 `cd13b8392cf0cf2e7f56e18861e6269a1461c32271c75674a193ac3d39c241c4`. Não é evidência local nem prova de proveniência/equivalência integral.
- Identificadores de tipo/ability e propósitos de jogo não são atribuídos aos códigos numéricos locais.

## Endereços no dispatch local de comandos

O ciclo 25 havia localizado a tabela local de ponteiros de handlers em `0x0825011C`. A leitura direta desta ROM confirma:

- índice/opcode `0x4A` (`74`): word em `0x08250244` é `0x08023C39`, ponteiro Thumb para código em `0x08023C38`;
- índice/opcode `0xA6` (`166`): word em `0x082503B4` é `0x08029DAD`, ponteiro Thumb para código em `0x08029DAC`.

Isso estabelece a associação local tabela→handler, mas, isoladamente, não prova emissão por bytecode.

## Referências locais em scripts de efeito

A inspeção agora seguiu duas cadeias da ROM BR. O dispatch de moves local já documentado em `reports/ciclo_21_catalogo_moves_dispatch_efeitos.md` usa o byte `+0` do registro para selecionar uma word em `0x081D65A8` e grava o destino no cursor de script `0x02023D74`. Os registros candidatos de índices 68 e 176 têm, respectivamente, byte `+0` igual a `0x59` e `0x5D`; as entradas correspondentes da tabela local apontam para `0x081D7433` e `0x081D74D6`.

- Em `0x081D7433`, os bytes locais são `00 A1 F0 7D 1D 08 01 5E 69 1D 08 00 00 02 03 4A`. O `0x4A` está no deslocamento `+15` da entrada candidata. O parse upstream fixado dá tamanhos de 1 byte para `attackcanceler`, 5 para `counterdamagecalculator`, 7 para `accuracycheck`, e 1 cada para `attackstring` e `ppreduce`; esse alinhamento coloca `0x4A` no início do próximo comando.
- Em `0x081D74D6`, os bytes locais são `00 02 03 A6 F2 7D 1D 08 09 0A`. O `0xA6` aparece no deslocamento `+3`, após três opcodes locais cujos handlers são `0x00`, `0x02` e `0x03`; o word seguinte aponta para `0x081D7DF2`.
- A tabela local encaminha `0x4A` a `0x08023C38` e `0xA6` a `0x08029DAC`. As palavras `+0` dos registros e os destinos de script são fatos locais. O vínculo entre limites de comandos e os nomes acima é **cross-reference separado**, fixado em `pret/pokefirered` commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; não substitui análise local nem prova execução.

Essas ocorrências resolvem a lacuna anterior de ausência de exemplos de bytecode, mas não demonstram que os registros candidatos de move sejam selecionados em uma batalha, que os scripts completem o fluxo ou que o caso de índice 112 ocorra. Verificador: `scripts/inspect_typechart_script_references.py`.

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

A rotina tem prólogo em `0x08029DAC` e usa o helper local `0x08044EC8`. As instruções e literais locais mostram estado em `0x03005000`, multiplicador `0x41C64E6D`, incremento `0x6073`, gravação do novo estado e retorno da metade alta. O trecho `0x08029E9C–0x08029EBE` aplica `& 0x7F`, repete se o resultado for maior que `0x70`, e para valores aceitos calcula `3 × índice + 0x0824F050`.

Pelos parâmetros do LCG módulo `2^32` (`c` ímpar e `a ≡ 1 mod 4`), o estado tem período matemático completo. Logo, em seu ciclo existem saídas cuja metade alta, após `& 0x7F`, é 112. Isso estabelece que o valor pertence ao domínio do gerador; não demonstra quantas chamadas ocorrem nem em que ponto o estado real da sessão chega a ele.

A tabela delimitada localmente tem 112 registros, índices 0–111, intervalo `[0x0824F050, 0x0824F1A0)`. O teste admite 112, e `base + 3 × 112 = 0x0824F1A0`, logo após o intervalo; os três bytes locais ali são `C8 C9 CC`. Se o primeiro byte passar na comparação, o código lê `+2` e o compara com 5; `0xCC` segue o ramo de rejeição (`bhi`) antes do caminho que usa uma linha válida. Portanto, a evidência sustenta uma **leitura estática de três bytes além do limite candidato e rejeição desse candidato**, não corrupção, crash ou efeito de jogo comprovado. A frequência/impacto desse retry não foi testada dinamicamente.

A mesma rotina contém um segundo scan em `0x08029F0A`: incrementa o deslocamento em 3 e compara com literal `0x14F` (335), cobrindo offsets 0–333, isto é, índices 0–111. Esse limite é coerente com a tabela. A word em `0x08029F90` fornece a base nos loads `0x08029EAC` e `0x08029F0A`. A entrada `0xA6 → 0x08029DAC` na tabela local de comandos foi confirmada; ainda não localizamos um script específico que emita esse opcode.

## Verificação reproduzível

```bash
python scripts/inspect_typechart_bounds.py
python scripts/inspect_typechart_script_references.py
```

O primeiro verificador read-only confirma hash, duas entradas do dispatch, bytes/incremento/constantes do LCG, sequência de máscara/limite do handler e bytes imediatamente após a tabela candidata. O segundo confirma os dois bytes `+0` de registros candidatos, os destinos da tabela de scripts, as sequências de bytes e os handlers locais. O alinhamento dos comandos que precedem `0x4A` usa tamanhos do macro upstream fixado; nenhum dos verificadores prova seleção em batalha, estado RNG real ou execução dinâmica.

## Fechamento das ocorrências candidatas e lacunas

O scanner encontra nove palavras brutas coincidentes com `0x0824F050`. O ciclo 25 examinou seis dentro/ao redor do handler `0x0801E848`; esta nota seguiu as outras três words: `0x08023CD8`, `0x08029F90` e `0x08039E38`. A classificação descreve código local estático; não prova que todos os fluxos sejam alcançados em cada modo de jogo ou que outros leitores indiretos inexistam.

## Próximo passo

1. Enumerar mais referências a `0x4A`/`0xA6` em scripts e rastrear a seleção/call path dos registros candidatos 68 e 176, sem tratar os dois exemplos como cobertura de todas as batalhas.
2. Se o gate de escopo permitir, verificar em contexto isolado o candidato de índice 112 e o ramo que rejeita `+2 = 0xCC`; não editar ROM/save-base nem converter leitura estática em bug confirmado sem teste.
3. Continuar inventário de UI, nomes, ícones e outros consumidores de tipos; este relatório não demonstra suporte geral a novos códigos de tipo.
