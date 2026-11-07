# Cosmog na V42 — progresso parcial preservado

**07/11/2026 — auditoria interrompida para atender ao pedido de publicação.**
Não é uma nova versão da ROM nem um certificado de conclusão da auditoria.

## O que já foi observado na sessão

- Captura nativa de Cosmog nível 25 em Rock Tunnel 1F, objeto 11, posição `(12,12)`, flag `0x5315`. A captura, a identidade do Pokémon, a flag e a ausência do objeto persistiram após SAVE/Continuar em um core novo.
- O mesmo exemplar capturado foi elevado pela interface de Rare Candy: Cosmog → Cosmoem no nível 43; checkpoint salvo no nível 52; ramo A → Solgaleo no nível 53; outro carregamento daquele checkpoint, cancelamento com B no nível 53 e → Lunala no nível 54. **Ramos alternativos não são posse simultânea dos dois lendários.**
- A tabela efetiva `0x69D0C8`, com registros de 28 bytes, tem grupos de ovo `[0,0]` para 789–792, não `[15,15]`. A função nativa de compatibilidade em `0x0807F460` usa essa tabela, conforme o literal em `0x0807F578`.
- Chamadas isoladas da rotina nativa retornaram compatibilidade 20 para Cosmog/Ditto de mesmo OT, nas duas ordens; 0 para Cosmog/Cosmog, Ditto/Ditto e Mew/Ditto; 20 para Bulbasaur/Ditto. A chamada direta de entrega gerou um ovo válido de espécie 789, nível 5, mas essa chamada isolada **contorna a disponibilidade do ovo**.
- Em uma sondagem separada com pais sintéticos, o depósito pela interface da creche foi executado. A continuação desse cenário desde um checkpoint sintético percorreu 256 passos, observou a flag de ovo pendente, saiu da creche, recebeu o ovo pelo NPC e fez SAVE/Continuar. O ovo de Cosmog permaneceu válido, com PID diferente do pai, que continuava na creche.

Esses resultados impedem afirmar que só existe uma cópia possível por ser um lendário. Há evidência de reprodução na implementação atual, distinta das regras oficiais.

## O que NÃO foi concluído

- Eclosão do ovo, incubação completa e retirada do pai pela interface.
- Solgaleo e Lunala juntos no mesmo save por essa rota de reprodução.
- Percurso completo desde uma campanha nova, captura de Ditto e acesso normal à creche.
- Varredura exaustiva de presentes, trocas e mecanismos alternativos de repetição de eventos.
- Execução consolidada da **versão atual** de `tests/test_cosmog_v42_mgba.py`. O arquivo recebeu novas asserções e testes após as sondagens; não transferir automaticamente os resultados anteriores para ele. As novas verificações de SAVE/Continuar após cada evolução final ainda precisam de execução consolidada.

## Fontes preservadas para continuar

- `scripts/auditar_cosmog_v42.py`: inventário com SHA da V42 obrigatório; 2.176 slots selvagens e 816 noturnos; um evento adicional ativo de Cosmog, nenhum encontro selvagem da linha; Ditto nas tabelas de Route14 e PokemonMansion B1F.
- `tests/test_cosmog_v42.py`: três verificações estruturais, reexecutadas na preparação da publicação.
- `tests/test_cosmog_v42_mgba.py`: trabalho em andamento, com captura, cenas, contratos e fluxo da creche. Saves e estados são exclusivamente sintéticos e não entram no Git.

As observações nativas acima são um registro de progresso da sessão, **não um novo pacote consolidado de logs/telas**. O ambiente de publicação não reteve os artefatos temporários dessas sondagens. Os relatórios e logs históricos da V42 e dos trajetos das ilhas permanecem no repositório.

## Ambiente e reprodução

ROM: `6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a`.
Core mGBA 0.10.5 usado nas sondagens: `07ab56ae80ed30486eff67ab4907b345f46ebb5e60f47f98869dc534df18dad9`.

```sh
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
COSMOG_V42_ROM=/caminho/FireRed_Gen1-9_motor_v42.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
COSMOG_V42_OBSERVATIONS=/caminho/novo/observacoes.json \
MOTOR_V41_SCREENS=/caminho/novo/telas \
python3 -B -m unittest -v test_cosmog_v42 test_cosmog_v42_mgba
```

Criar os diretórios de saída antes de executar; não fornecer save pessoal. Não alterar a ROM para corrigir a reprodução sem uma decisão específica sobre o comportamento desejado.
