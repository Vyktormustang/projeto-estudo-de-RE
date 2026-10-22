# Fase 1 — leitor adicional da tabela local de effectiveness

**Estado:** um leitor adicional da tabela `0x0824F050` foi seguido em código Thumb local. A rota é estática; o caller/alcance em runtime permanece sem comprovação. A ROM e saves ficaram intactos.

## Proveniência e método

- ROM BR local, somente leitura, 16 MiB; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Desmontagem do intervalo com Capstone 5.0.7 temporário (`/tmp/capstone-py`); o helper e a tabela já tinham sido revalidados por `scripts/inspect_typecalc_path.py` e `scripts/inspect_expansion_numeric_domains.py`.
- REA/Ghidra e emulação não foram usados. Nomes semânticos de tipos, habilidades ou função de jogo não são inferidos aqui.

## Leitor local `0x08039DB4`

A rotina começa com prólogo Thumb em `0x08039DB4` e termina no retorno em `0x08039E34`. Ela preserva os argumentos: `r0` em stack local, `r1` em `sb`, `r2` em `r8` e `r3` em `r6`. Em `0x08039DD6`, carrega da pool literal em `0x08039E38` o endereço `0x0824F050` e percorre registros de três bytes:

1. Se o byte `+0` do registro for `0xFF`, sai. Se for `0xFE`, avança três bytes sem aplicar a rotina normal.
2. Para os demais, compara `+0` com o argumento inicial `r0` e `+1` com `r1`/`r2` preservados.
3. Nas correspondências, lê o byte `+2`, multiplica por esse valor o byte apontado pelo argumento `r3`, divide por 10 chamando `0x081E4018` e escreve o resultado de volta no endereço apontado.
4. Avança por stride 3 e continua até encontrar o byte `0xFF`.

Isto comprova um segundo caminho local que consulta os campos dos registros de três bytes e aplica um multiplicador. Não atribuo nomes aos argumentos nem afirmo que o byte escrito seja necessariamente o dano: isso exigiria rastrear o caller e o estado em que fornece os argumentos.

O loop não usa nesta sequência um contador máximo de linhas; depende do terminador `0xFF`, que foi observado na tabela local em índice 111. Não foi testado o comportamento caso o terminador esteja ausente ou deslocado.

## Referências adicionais ainda em aberto

O scanner de padrões brutos encontra nove palavras coincidentes com `0x0824F050`; o ciclo 25 já seguiu seis ocorrências dentro do handler `0x0801E848`. Fora dessa fatia:

- a word em `0x08039E38` agora está associada ao leitor acima;
- a word em `0x08023CD8` e seu candidato de load em `0x08023CCC` aparecem em outro fluxo com comparações de tipo e acesso aos offsets `+0x21/+0x22` de uma estrutura indexada por stride `0x58`; esse fluxo ainda não foi traçado desde sua entrada;
- a word em `0x08029F90` possui loads candidatos em `0x08029EAC` e `0x08029F0A`; contexto parcial indica mais de uma passagem/consulta, mas sua relação funcional e chamadores não foram estabelecidos.

As ocorrências de padrão LDR são apenas pistas. Nenhum item em aberto foi promovido a consumidor confirmado com base apenas nessa assinatura.

## Próximo passo

Seguir um caller local de `0x08039DB4` (ou comprovar entrada indireta), e depois classificar os dois fluxos restantes sem pressupor que sejam código alcançável. Em paralelo, continuar a auditoria de nomes/renderização de tipos, efeitos e arrays de UI. Esta fatia não demonstra suporte geral a novos tipos nem cobre todos os consumidores da ROM.
