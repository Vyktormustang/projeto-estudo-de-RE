# Motor v17 — ordem de criação dos hazards

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** Correção dirigida sobre a v16 exata, com saída nova e equipes/estados exclusivamente sintéticos. Não é o BAG_MOD histórico e não certifica o motor completo de Scarlet/Violet.

## Defeito da base e regra da saída

A [auditoria da v16](AUDITORIA_V16_HAZARDS_COMBINADOS_DUPLAS.md) demonstrou Spikes executando antes de Stealth Rock independentemente da ordem de colocação. O HP final podia coincidir e ocultar o erro; os eventos intermediários e as mensagens mostravam a diferença.

A v17 mantém uma fila por lado, na **ordem de criação das condições**. Uma camada adicional não cria outra condição nem muda sua posição. Remover e recolocar cria uma posição nova, depois das condições ainda presentes. Court Change transporta a fila junto com os hazards.

| Preparação / entrante Fire, maxHP 400 | Base v16 | Saída v17 exigida |
|---|---|---|
| Stealth Rock, depois uma camada de Spikes; HP 400 | Spikes **400→350**, SR **350→250** | SR **400→300**, Spikes **300→250** |
| Mesma ordem, HP 100 | Spikes **100→50**, SR **50→0** | SR **100→0**, sem Spikes nesse entrante |
| SR, depois três camadas; HP 100 | Spikes causa o KO | SR causa o KO; a diferença é exigida também pela mensagem |
| Spikes antes de SR | Spikes primeiro | Preserva Spikes primeiro |

Os negativos são executados separadamente na **base v16**. As expectativas defeituosas não são reaproveitadas como regra da saída. Cada versão cria suas próprias fixtures; não são transferidos estados entre ROMs.

## Implementação e memória

Arquivos: `scripts/motor_v17.py` e `patches/motor_v17/{motor_v17.c,entry.s,payload.ld,payload.bin}`.

- Payload Thumb de **3.148 bytes**, em `0x090DB000..0x090DBC4B`, dentro da área antes `0xFF` reservada pelo aplicador até `0x090DC000` exclusivo.
- **Oito ponteiros de quatro bytes** redirecionados, mais o payload: nove intervalos de escrita. Sete são literais de vetores v8, preservando os encadeamentos superiores v9/v10; o oitavo é o comando nativo de colocação de Spikes (`0xB0`). O wrapper de phazing v16 continua instalado.
- **Oito bytes efêmeros** em `0x0203FC90..0x0203FC97`, dentro da reserva v8 e depois da estrutura v8 de 44 bytes. Não há alteração de formato de save. Uma asserção de compilação impede sobreposição da estrutura v8 com a fila.
- Duas filas de quatro bytes: `1=Spikes`, `2=Stealth Rock`, `3=Toxic Spikes`, `4=Sticky Web`, `0=vazio`. Não há contador global que possa sofrer wraparound.
- O cursor, banco e identificador da entrada reutilizam os campos efêmeros v8. A fila é limpa no início de cada batalha; a sequência é reiniciada por entrada, troca de ocupante/banco e KO.

O arquivo C inclui as regras/helpers v8 para reutilizar aterramento, efetividade, scripts de dano e limpeza. `--gc-sections` descarta os hooks não referenciados; os arquivos v8 e seus payloads antigos não são regravados. O patch só muda os sete literais especificados dentro da área v8, não recompila todo o motor antigo no lugar.

### Ciclo de vida

| Caminho interceptado | Tratamento da fila |
|---|---|
| Spikes nativo (`0xB0`) | Acrescenta apenas na primeira colocação bem-sucedida; limite de camadas preservado |
| Stealth Rock, Toxic Spikes e Sticky Web | Sincroniza antes/depois da aplicação de campo; duplicatas e camadas preservam a posição |
| Stone Axe / Ceaseless Edge | Registra a condição criada pelo golpe; falhas não criam fila artificial |
| Rapid Spin / Mortal Spin | Remove as condições efetivamente limpas no próprio lado, preservando o outro |
| Defog / Tidy Up | Remove as condições efetivamente limpas nos dois lados |
| Court Change | Troca as filas completas junto com as condições dos lados |
| Absorção de Toxic Spikes | Apaga a posição **sem compactar durante a entrada**; evita saltar o hazard seguinte |
| Próxima mutação/entrada | Compacta posições vazias preservando a ordem relativa |
| Nova batalha | Limpa os oito bytes; guardas vizinhas são testadas |

Há um fallback determinístico para condições presentes sem registro na fila, útil às fixtures antigas que semeiam hazards antes da execução. **Não recupera a ordem histórica de um estado salvo por outra versão.** Migração de save states v16→v17 não é suportada nem validada por esse fallback.

### Sequência de entrada e desmaio

A v17 executa o prólogo nativo necessário à participação/EXP e às flags de reposição **antes** dos hazards: `UpdateSentPokesToOpponentValue`, limpeza do marcador de desmaio do banco e de `faintedHasReplacement`. Os endereços/stride foram conferidos na desmontagem da ROM expandida exata, não transplantados cegamente da ROM original.

A seguir percorre a fila. Cada etapa avança o cursor antes de abrir seu script; se o HP chega a zero, nenhuma etapa posterior atinge aquele membro. A reposição seguinte recebe uma sequência nova, inclusive quando reutiliza o mesmo banco.

Para sobreviventes, a rotina nativa continua com habilidades/itens, cancelamento da ação e avanço do banco. O bit transitório nativo `SIDE_STATUS_SPIKES_DAMAGED` (`0x0200`) impede **uma segunda aplicação** de Spikes. Não se apaga temporariamente a condição de campo. Se uma habilidade abre um script, a fase final permanece até o retorno e conclusão nativa.

Isso também evita executar Intimidate de um entrante que já caiu nos hazards. O controle dirigido usa Ekans vivo versus derrubado por SR, além dos testes de reposição/EXP. Não é uma auditoria completa da ordem de todas as habilidades, itens e efeitos modernos de entrada.

## Testes dirigidos

### Dano e ordem em duplas — quatro métodos / 20 subcasos

`test_motor_v17_combined_hazards_mgba.py`:

- Spikes primeiro e SR primeiro, com uma, duas e três camadas.
- Reservas saudáveis, KO no primeiro hazard ou no segundo, segundo reserva sobrevivente.
- Ator 0 na matriz principal; ator 2 nos controles de quarta tentativa de Spikes e segunda de SR.
- Dano por PID, mensagens, PP, checksum, identidade, EXP, bancos distintos/ausentes, histórico dos entrantes e outro turno sem repetição de dano.
- Contador de camadas, presença de SR e fila preservados após entrada/KO.

Spikes causa **50/66/100** e SR **100** nos reservas Fire com maxHP 400. Os golpes e os KOs são reais; depois de iniciar as ações, não se alteram HP, RNG, hazards, índices, histórico ou EXP para produzir o resultado.

### Ciclo de vida — seis métodos / 13 subcasos

`test_motor_v17_lifecycle_mgba.py`:

1. Nova batalha com fila suja no preparo e guardas vizinhas: fila zerada e guardas preservadas (**1**).
2. Camadas intercaladas com SR, Court Change ida/volta, Defog/Tidy Up e recriação em ordem inversa (**2**).
3. Rapid Spin/Mortal Spin limpando só o próprio lado, preservação do oposto e novas colocações (**2**).
4. Stone Axe/Ceaseless Edge nas duas ordens, incremento e limite das camadas (**2**). A precisão permanece real; as tentativas necessárias para a colocação são limitadas e uma falha não deve criar hazard.
5. Quatro hazards em duas ordens, absorção por Poison sem saltar a próxima etapa, Intimidate do sobrevivente e KO antes de habilidade/absorção/Web (**4**). O observador registra HP persistente, status e estágio de Speed por identidade.
6. Defog/Tidy Up seguidos de recriação inversa e **entrada real de dois reservas**, exigindo SR antes de Spikes no dano e nas mensagens (**2**).

O controle com Ekans usa a EXP nativa: rendimento 62, nível 10, dois participantes e multiplicador de treinador produzem **66 por participante**, não os 69 do Charmander. Após dois KOs originais e Ekans, a EXP é **560→764**, nível 11 (limiar Medium Slow: 742). Não é certificação da fórmula moderna de EXP.

### Contrafactual e regressões

`test_motor_v17_base_mgba.py`: um método / dois subcasos na v16, com uma e três camadas, SR primeiro e HP inicial 100. Exige a divergência da base, tanto com danos diferentes como iguais. Um `ok` aqui significa **defeito reproduzido na entrada**, não falha na saída corrigida.

`test_motor_v17_regressions.py`: fixtures novas na v17, com cinco métodos de reservas insuficientes/encerramento em duplas, sete de hazards/KO em singles, oito positivos de phazing/pivôs/histórico e um controle legado de campo/hazards. Este último inclui entradas Flying/Poison, absorção, envenenamento grave, Sticky Web, limpeza e troca de lados. Os negativos antigos e a comparação de encontros selvagens não são herdados como testes da saída.

`test_motor_v17.py`: entrada exata, hash/vetores do payload, reconstrução determinística, todos os bytes fora dos nove intervalos preservados, rejeição de corrupção/reaplicação e saída exclusiva. O SHA v17 foi acrescentado explicitamente à lista de ROMs identificadas do teste de treino EV/IV; não se desativou a verificação de SHA.

## Resultados finais

**46/46 métodos distintos concluídos, sem skips, todos os processos finais com código zero.** Inclui **um método negativo na base v16**, separado dos positivos da saída. Não são 46 mecânicas modernas distintas nem execução de todas as suítes históricas.

| Processo final desta etapa | Métodos | Tempo | Resultado |
|---|---:|---:|---|
| Build v17 e treino EV/IV | **14** | **44,713 s** | OK |
| Contrafactual v16 (dois subcasos) | **1** | **208,602 s** | Defeito reproduzido na base |
| Ordem/dano na saída v17 (20 subcasos) | **4** | **1.082,700 s** | OK |
| Ciclo de vida / quatro hazards (11 subcasos) | **5** | **971,877 s** | OK |
| Entrada após limpeza/recriação (dois subcasos) | **1** | **188,790 s** | OK |
| Reservas insuficientes e encerramento em duplas | **5** | **1.316,696 s** | OK |
| Singles (7), phazing/pivôs/histórico (8), campo legado (1) | **16** | **1.115,100 s** | OK |

Os seis métodos de ciclo de vida foram executados em dois processos, sem sobreposição: cinco por nome e depois o controle adicional de entrada após recriação. A descoberta final confirma **5 build + 1 base + 4 matriz + 6 ciclo de vida + 21 regressões**, mais nove de treino EV/IV = **46**. Os dez métodos positivos novos de batalha contêm **33 subcasos**, além dos dois negativos da base. Os subcasos das regressões não aumentam esses 33.

Execução com mGBA **0.10.5**; grupos paralelos compartilham CPU, portanto os tempos não são uma comparação de desempenho da engine. Payload recompilado byte a byte idêntico; SHA de entrada/saída reconferidos após os testes. Manifesto atualizado e verificado: **251 entradas**.

Sondas preliminares, repetições e processos interrompidos não integram o total final. O primeiro comando combinado de build/EV encerrou com erro de preparação porque o novo SHA ainda não constava da lista identificada; não foi erro do treino nem aprovação parcial dos nove testes. A lista recebeu apenas o SHA exato v17 e o grupo foi reexecutado.

A primeira execução exploratória do ciclo de vida foi interrompida para corrigir antecipadamente a expectativa de EXP/nível do controle com Ekans: a fixture anterior só tratava o rendimento de Charmander. Nenhum payload foi alterado para ajustar o resultado ao teste.

## Hashes e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada v16, 33.554.432 bytes | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |
| Payload v17, 3.148 bytes | `f25e560c02cd3681a508812050e9fd0bed9d4b652d788dffa221d2a10983703f` |
| Saída v17, 33.554.432 bytes | `5db05cbb54add61a6c50e08d3e392ba610e87ca3ef462095de168de5d3e32957` |

```sh
python3 firered_gen1_9/scripts/motor_v17.py \
  --rom /privado/motor_v16.gba --saida /privado/motor_v17.gba
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V17_BASE=/privado/motor_v16.gba
export MOTOR_V17_ROM=/privado/motor_v17.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V17_ROM"
python3 -m unittest test_motor_v17 test_treino_ev_mgba -v
python3 -m unittest test_motor_v17_base_mgba -v
python3 -m unittest test_motor_v17_combined_hazards_mgba -v
python3 -m unittest test_motor_v17_lifecycle_mgba -v
python3 -m unittest test_motor_v17_regressions -v
```

Recompilação independente com Zig **0.17.0**, byte a byte idêntica:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_init_v17 \
  -Wl,-T,firered_gen1_9/patches/motor_v17/payload.ld \
  firered_gen1_9/patches/motor_v17/entry.s \
  firered_gen1_9/patches/motor_v17/motor_v17.c -o /tmp/v17-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v17-rebuilt.elf /tmp/v17-rebuilt.bin
cmp /tmp/v17-rebuilt.bin firered_gen1_9/patches/motor_v17/payload.bin
```

## Limitações

O recorte novo de ordem é principalmente reposição adversária em duplas. As regressões de seleção do jogador e de singles preservam os cenários anteriores, mas não cobrem todas as permutações de quatro hazards em ambos os lados, habilidades/itens modernos, redirecionamento, link/multi ou entradas simultâneas de quatro treinadores. Os controles de tipos/status/aterramento não certificam todas as interações de Gravity, Magnet Rise, Ingrain, terrenos ou habilidades.

A v17 ordena as quatro condições implementadas no motor parcial; não implementa Heavy-Duty Boots, Toxic Debris ou todas as habilidades modernas ausentes. Não houve auditoria integral de campanha, Teachy TV, save states entre versões ou migração de saves pessoais. **Não se deve confundir 229 TMs disponíveis com fidelidade integral a Scarlet/Violet.**

**Próximo recorte recomendado:** ordem de hazards combinados nas escolhas e reposições do jogador em duplas, incluindo KO durante a seleção, absorção e histórico do novo ocupante.

**ROMs, saves e estados continuam fora do Git. Drive não atualizado; o pacote lá armazenado não passa automaticamente a ser v17.**

## Referências fixadas

- [Auditoria negativa da v16](AUDITORIA_V16_HAZARDS_COMBINADOS_DUPLAS.md), inclusive as tabelas de HP/mensagens e os limites do recorte original.
- [Pokémon Showdown, `sim/battle.ts`, 035c1a1, L1002–1007](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle.ts#L1002-L1007): ordem de criação em `effectOrder`.
- [Pokémon Showdown, `sim/side.ts`, 035c1a1, L413–443](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/side.ts#L413-L443): condição nova versus incremento via `SideRestart`.
- [Pokémon Showdown, `data/moves.ts`, Court Change](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L3032-L3101): transferência dos estados de condições entre lados, sem recriar sua identidade.
- [pret/pokefirered, `battle_script_commands.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): `Cmd_switchineffects`, `Cmd_trysetspikes`, `Cmd_rapidspinfree` e cálculo nativo de EXP. Os endereços usados são os da ROM expandida verificada.
