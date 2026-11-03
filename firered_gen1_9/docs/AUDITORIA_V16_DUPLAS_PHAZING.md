# Auditoria v16 — phazing em duplas e múltiplas reservas

**03/11/2026 — FireRed Gen 1–9 / VYK-57.** Somente ROM identificada por SHA-256 e estados/equipes sintéticos. **Nenhuma mudança na ROM, no payload ou no aplicador. Não há v17 nesta etapa.**

## Resultado

**29/29 verificações concluídas, nenhum skip**, incluindo cinco métodos novos com **60 subcasos**. Não foi demonstrado novo defeito nos cenários auditados:

- Roar, Whirlwind, Dragon Tail e Circle Throw trocaram o alvo por uma reserva elegível, sem selecionar nenhum dos dois membros já ativos daquele lado.
- A seleção funcionou com três reservas válidas e com apenas uma válida entre um desmaiado, um ovo e um slot vazio.
- Com somente os dois ativos elegíveis, a tentativa não trocou ninguém nem encerrou a batalha.
- O banco substituído perdeu o histórico anterior; os demais preservaram o registro da própria ação.
- Eerie Spell não drenou PP do entrante antes da primeira ação dele. No turno seguinte, drenou o Splash registrado, sem atingir os PP do parceiro.
- PP de todos os slots, HP, níveis, EXP, identidade e checksum permaneceram coerentes nos controles descritos abaixo.

Isso amplia a cobertura da [entrega v16](MOTOR_V16.md), mas não certifica todos os modos de duplas, todas as habilidades ou fidelidade integral a Scarlet/Violet.

## Matriz nova

Arquivo: `tests/test_motor_v16_doubles_phazing_mgba.py`.

IDs locais da ROM: Roar **46**, Whirlwind **18**, Dragon Tail **521**, Circle Throw **508**, Eerie Spell **720**. Bancos 0/2 são do jogador; 1/3, do adversário.

| Método / cenário | Subcasos | Observação exigida |
|---|---:|---|
| Usuários 0/2, alvos 1/3, três reservas | 4 golpes × 2 usuários × 2 alvos = **16** | Duas trocas consecutivas; alvo escolhido pela interface; exclusão dos dois ativos a cada tentativa |
| Usuários adversários 1/3, três reservas | 4 golpes × 2 usuários = **8** | Duas trocas consecutivas; alvo da IA observado; exclusão dos ativos no lado do jogador |
| Uma reserva válida | 4 golpes × 4 usuários = **16** | Entra exatamente o slot 2; desmaiado, ovo e vazio não são escolhidos |
| Nenhuma reserva elegível | 4 golpes × 4 usuários = **16** | Índices ativos inalterados, retorno ao menu, resultado de batalha zero e gasto próprio de PP |
| Histórico/Eerie após Dragon Tail | 2 usuários × 2 alvos = **4** | Entrada sem histórico, primeiro Eerie sem dreno, segundo Eerie drenando o golpe efetivamente usado |
| **Total** | **60** | |

Os atacantes de phazing são **nível 5**, os demais membros válidos **nível 10**. Assim, a matriz inclui o caso de atacante inferior coberto pelo ajuste v16, não apenas a antiga condição de nível maior/igual. Não foi instrumentado quantas vezes cada tentativa tomou o caminho de repetição do wrapper.

Nos casos de três reservas, os slots inicialmente ativos de cada lado são 0 e 1; as opções iniciais são **`{2,3,4}`**. Antes da segunda tentativa, o conjunto é recalculado a partir do estado real, pois o membro que saiu pode voltar a ser elegível. Não se fixa qual reserva o RNG deve escolher, nem se permite simplesmente qualquer slot diferente do alvo: **o parceiro ativo também é excluído**.

O alvo adversário 1/3 é escolhido por botões, sem escrita em `gBattlerTarget`. Quando a IA usa phazing, o teste identifica qual banco 0/2 realmente mudou e exige que pertença ao lado oposto. Isso não é controle exaustivo da escolha de alvos pela IA nem de redirecionamento.

## Equipes e observação

As fixtures usam quatro participantes ativos e contexto sintético de treinador em duplas, sem link/multi. As reservas são preparadas antes do primeiro turno testado. Não se escreve em índices ativos, histórico ou RNG entre turnos.

- Pokémon sintéticos Charmander, com **EXP 135 no nível 5** e **560 no nível 10**, coerentes com a curva medium-slow. HP/atributos são deliberadamente artificiais para evitar KO e isolar o fluxo.
- Cada membro recebe PID distinto, preservando `PID % 24`; os blocos são recriptografados e continuam com checksum válido. PID, EXP e OT ID do estado de batalha inicial correspondem à equipe.
- PP varia por slot, permitindo detectar alterações no membro errado. O primeiro movimento dos adversários desta fixture usa o **slot de golpe 1**, mantido válido; não se fabrica um NoPP na preparação.
- As três composições são: três reservas vivas; uma viva + uma desmaiada + ovo + vazio; ou apenas desmaiado/ovo/vazios além dos dois ativos.
- A elegibilidade é conferida por espécie presente, não ser ovo, HP positivo e ausência do conjunto dos dois ativos.

Cada turno exige:

1. retorno ao menu e marcador de isenção `0x800` limpo;
2. nenhum índice ativo duplicado no mesmo lado;
3. na troca bem-sucedida, **exatamente um banco** diferente e reserva pertencente ao conjunto elegível anterior;
4. histórico zero somente no banco substituído, com os outros bancos registrando seu próprio golpe;
5. um PP por ação nos quatro participantes, nos slots anteriores à troca; o entrante não recebe um gasto fictício de ação;
6. preservação dos PP de todos os demais membros, inclusive reservas inválidas;
7. PP de batalha igual à equipe criptografada, checksum válido, HP persistente, nível, EXP, PID e OT ID coerentes.

As outras ações são Splash. Elas acontecem antes do phazing de prioridade negativa; portanto, a matriz não avalia substituição de um alvo cuja ação ainda esteja pendente depois da troca.

### Eerie Spell após a troca

Depois de Dragon Tail, o histórico do banco que recebeu o reserva é zero. O usuário do phazing seleciona Eerie, agindo antes do entrante por velocidade:

- primeiro Eerie causa dano, mas não drena PP; o entrante só gasta seu próprio Splash e passa a ter histórico 150;
- segundo Eerie drena três PP desse Splash, além do PP gasto pela ação atual do alvo;
- o parceiro e os membros fora de campo não recebem o dreno.

São exigidos dano no alvo selecionado, índices estáveis nesses dois turnos e registros de Eerie/Splash, além da contabilidade exata de todos os PP. Não é inferência baseada apenas em mensagem de texto.

## Execução final

mGBA **0.10.5**, ambos os processos finais com código zero:

| Execução | Resultado | Tempo |
|---|---:|---:|
| `test_motor_v16_doubles_phazing_mgba` | **5/5**, 60 subcasos | **591,805 s** |
| `test_motor_v16_mgba` + `test_motor_v16` + `test_treino_ev_mgba` | **24/24** (10 + 5 + 9) | **328,312 s** |
| Total desta etapa | **29/29**, nenhum skip | |

A suíte de singles inclui o contrafactual histórico da v15, separado dos resultados positivos v16, e as comparações de encontros selvagens. Isso não indica defeito novo na v16. As **61 regressões positivas da entrega anterior não foram reexecutadas nesta etapa**, nem os 85 testes originais somados a estes 29.

Uma sonda preliminar conferiu uma troca em cada lado antes do reforço das identidades/EXP das fixtures. Ela não entra na contagem final; a matriz completa foi executada depois desse reforço.

O ambiente temporário foi reconstruído e a cadeia privada parcial→estojo v2→v5…v16 conferida em cada etapa. Os arquivos locais coincidiam com o commit publicado `a4b5193` antes do realinhamento do checkout. Não foi descartado trabalho divergente. A base privada foi somente lida do Drive.

## Reprodução

Na raiz do repositório, com ROM própria:

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V16_BASE=/privado/motor_v15.gba
export MOTOR_V16_ROM=/privado/motor_v16.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V16_ROM"
python3 -m unittest test_motor_v16_doubles_phazing_mgba -v
python3 -m unittest test_motor_v16_mgba test_motor_v16 test_treino_ev_mgba -v
```

SHA-256 da ROM v16 permanece **`644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc`**, 33.554.432 bytes. Payload de 300 bytes permanece **`f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb`**. Aplicador e fontes do motor não foram alterados; catálogo continua com 15.008 registros / 708 de 729 omissões restauradas.

**Nenhuma ROM, save pessoal ou estado foi incluído no Git. Drive não atualizado.**

## Limites e próximos passos

Ainda não estão cobertos:

- phazing simultâneo por dois usuários no mesmo turno, mudanças de ordem, alvo ainda com ação pendente e redirecionamento;
- distribuição estatística uniforme entre reservas ou todas as combinações possíveis de equipes;
- link/multi, equipes divididas entre treinadores e proprietário de cada metade;
- KO do alvo/usuário, hazards e KO na entrada, todos os casos de Substitute, habilidades modernas e itens de troca;
- pivôs usados pelo adversário e a totalidade dos efeitos que devem ou não passar durante uma troca;
- campanha completa, Teachy TV e migração de saves pessoais.

**Próximo recorte recomendado:** KO e hazards durante a troca/entrada, mantendo os controles de identidade, PP e histórico. A engine continua parcial; este relatório não elimina as limitações gerais da entrega v16.

## Referências

- [pret/pokefirered, `battle_script_commands.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): `Cmd_forcerandomswitch`, mínimo de três membros válidos em duplas não-multi e exclusão do alvo/parceiro ativos.
- `patches/motor_v16/motor_v16.c`: wrapper restrito, que continua delegando à seleção nativa.
- [MOTOR_V16.md](MOTOR_V16.md): correção por nível, hashes, referências modernas, testes originais e limites.
