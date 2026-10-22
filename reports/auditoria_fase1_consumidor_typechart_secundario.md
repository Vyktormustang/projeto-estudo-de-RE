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

A inspeção seguiu cinco cadeias de dados locais. O dispatch de moves documentado em `reports/ciclo_21_catalogo_moves_dispatch_efeitos.md` usa o byte `+0` do registro para selecionar uma word em `0x081D65A8` e grava o destino no cursor `0x02023D74`. Os registros candidatos de índices 68, 176, 205, 301, 243 e 280 têm byte `+0` igual a `0x59`, `0x5D`, `0x75`, `0x75`, `0x90` e `0xBA`; as entradas correspondentes da tabela local apontam para `0x081D7433`, `0x081D74D6`, `0x081D78A0`, `0x081D78A0`, `0x081D7A89` e `0x081D81B9`.

- Entrada `0x59`, ponteiro `0x081D7433`: bytes `00 A1 F0 7D 1D 08 01 5E 69 1D 08 00 00 02 03 4A`; `0x4A` em `+15`.
- Entrada `0x75`, ponteiro `0x081D78A0`: bytes iniciais `00 02 1D 01 00 10 00 00 AD 78 1D 08 03 01 B4 78 1D 08 00 00 4A`; `0x4A` em `+20`.
- Entrada `0x90`, ponteiro `0x081D7A89`: bytes `00 A2 F0 7D 1D 08 01 5E 69 1D 08 00 00 02 03 4A`; `0x4A` em `+15`.
- Entrada `0xBA`, ponteiro `0x081D81B9`: o fluxo local chega a `0x4A` em `+51`, após a sequência de comandos/operandos validada pelo macro-layout upstream.
- Entrada `0x5D`, ponteiro `0x081D74D6`: bytes `00 02 03 A6 F2 7D 1D 08 09 0A`; `0xA6` em `+3` e o word de operando aponta para `0x081D7DF2`.

Como verificação adicional de uso dos valores numéricos dos registros, a tabela local candidata de learnsets (`0x0825D7B4`, 412 ponteiros) contém os mesmos IDs numéricos nos campos `word & 0x01FF`. Resultado da leitura local (índices da tabela de learnsets, sem atribuir nomes a espécies):

| ID numérico | Ocorrências nas listas | Índices de tabela com ocorrência |
|---:|---:|---|
| 68 | 9 | 107, 202, 214, 237, 307, 360, 364, 365, 366 |
| 176 | 2 | 137, 233 |
| 205 | 16 | 39, 74, 75, 76, 100, 101, 143, 183, 184, 206, 231, 232, 241, 313, 314 |
| 301 | 3 | 341, 342, 343 |
| 243 | 6 | 100, 101, 202, 222, 245, 360 |
| 280 | 3 | 106, 127, 214 |

O ID 205 ocorre duas vezes na lista apontada pelo índice 314; por isso 16 ocorrências aparecem em 15 índices. Essa interseção dá suporte local para que os índices de registro sejam valores usados em listas de aprendizado, mas não prova que um jogador escolha esses moves ou que a batalha alcance os scripts.

A tabela local encaminha `0x4A` a `0x08023C38` e `0xA6` a `0x08029DAC`. Os registros, destinos e bytes acima são fatos locais. O comprimento dos comandos usado para identificar os limites em `0x59`, `0x75`, `0x90` e `0xBA` é **cross-reference separado**: `asm/macros/battle_script.inc` no commit upstream `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`. Nesse upstream, os quatro macros `typecalc2` aparecem nas entradas 89/117/144/186, e `settypetorandomresistance` na 93; `data/battle_scripts_1.s` SHA-256 `27e9c39f3147b05e5ba2ed36ca0c89fcdc9b26718778083bd362c582de800034`. Esses nomes/ocorrências upstream orientam o parse, mas não provam proveniência ou execução da ROM local.

O caminho de dispatch indireto foi parcialmente reconstruído localmente. Uma tabela candidata de 23 ponteiros em `0x08250038` tem no slot 0 o ponteiro Thumb `0x08015CA1`. O código local em `0x080155C8–0x08015660` indexa essa tabela pelo byte em RAM `0x02023BE3` e passa o ponteiro escolhido ao trampoline `0x081E3BA8` (`BX r0`). Antes do lookup, lê também o byte `0x02023E8A`; se não for zero, grava `0x0C` em `0x02023BE3`, e se for zero deixa o índice anterior intacto. Portanto, o slot 0 só é selecionado se o valor preservado for zero e esse dispatch ocorrer; isso não foi confirmado em runtime.

Esse código tem prólogo local em `0x08015CA0`, retorno observado em `0x0801635C` e contém o bloco básico de lookup em `0x0801632C`. Sete branches locais (`0x08015FA8`, `0x08016158`, `0x080161E2`, `0x08016272`, `0x0801628A`, `0x080162C2`, `0x08016316`) convergem no bloco; instruções/destinos, slot da tabela e trampoline são conferidos pelo verificador. A origem de um valor zero já presente no índice, a chamada/execução real desse dispatch e o call path externo do código em `0x080155C8` continuam sem prova dinâmica. A antiga busca por BL direto ao bloco não era um teste de caller adequado, pois `0x0801632C` é interno à função apontada pelo slot 0.

As cinco cadeias locais resolvem a lacuna anterior de ausência de exemplos de bytecode; não demonstram que os registros candidatos sejam selecionados em batalha, nem que os scripts completem os fluxos ou que o caso de índice 112 ocorra. A amostra corresponde aos quatro usos de `typecalc2` e ao uso de `settypetorandomresistance` no cross-reference upstream, mas **não é um scanner exaustivo de todos os bytecodes locais**. Verificador: `scripts/inspect_typechart_script_references.py`.

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

A mesma rotina contém um segundo scan em `0x08029F0A`: incrementa o deslocamento em 3 e compara com literal `0x14F` (335), cobrindo offsets 0–333, isto é, índices 0–111. Esse limite é coerente com a tabela. A word em `0x08029F90` fornece a base nos loads `0x08029EAC` e `0x08029F0A`. Além da entrada `0xA6 → 0x08029DAC` no dispatch local, o bytecode local da entrada `0x5D` contém `0xA6`; a emissão por script foi confirmada estaticamente, mas execução não.

## Verificação reproduzível

```bash
python scripts/inspect_typechart_bounds.py
python scripts/inspect_typechart_script_references.py
```

O primeiro verificador read-only confirma hash, duas entradas do dispatch, bytes/incremento/constantes do LCG, sequência de máscara/limite do handler e bytes imediatamente após a tabela candidata. O segundo confirma seis bytes `+0` de registros candidatos, cinco destinos da tabela de scripts, as sequências de bytes, os handlers locais, o callback slot 0 e seu trampoline, sete branches para o bloco `0x0801632C` e as ocorrências dos seis IDs numéricos nas listas locais de learnsets. O alinhamento dos comandos usa tamanhos do macro upstream fixado; nenhum dos verificadores prova seleção em batalha, estado RNG real ou execução dinâmica.

## Fechamento das ocorrências candidatas e lacunas

O scanner encontra nove palavras brutas coincidentes com `0x0824F050`. O ciclo 25 examinou seis dentro/ao redor do handler `0x0801E848`; esta nota seguiu as outras três words: `0x08023CD8`, `0x08029F90` e `0x08039E38`. A classificação descreve código local estático; não prova que todos os fluxos sejam alcançados em cada modo de jogo ou que outros leitores indiretos inexistam.

## Próximo passo

1. Enumerar mais referências em bytecodes locais e rastrear a origem do índice `0x02023BE3`, a chamada externa do dispatch `0x080155C8` e o caminho de seleção dos registros candidatos, sem tratar os exemplos atuais como cobertura total.
2. Se o gate de escopo permitir, verificar em contexto isolado o candidato de índice 112 e o ramo que rejeita `+2 = 0xCC`; não editar ROM/save-base nem converter leitura estática em bug confirmado sem teste.
3. Continuar inventário de UI, nomes, ícones e outros consumidores de tipos; este relatório não demonstra suporte geral a novos códigos de tipo.
