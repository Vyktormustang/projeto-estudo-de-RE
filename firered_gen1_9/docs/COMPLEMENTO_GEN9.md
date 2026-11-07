# Complemento de TMs e golpes — ainda parcial

Esta cópia de **32 MiB** parte da ROM de TMs anterior, que continua intacta. **Não inclui tudo que faltava nem transforma o motor de batalha em Scarlet/Violet.** O aumento do arquivo permitiu novas tabelas e código, mas não resolve sozinho os limites do estojo, do save e das mecânicas. Ela pode ser útil como avanço testado, não como versão completa.

- Entrada SHA-256: `36cf2355789eca9273c2e4110606872fff8ab8ece82dae9ee090cd3bfa0546db`.
- Cópia expandida SHA-256: `6155b6a5fe62528b7b67836d3a47f32b1cb3b1a71c1f2b59bfa7a68af0100d67`.
- Arquivo: `ptbr_gen1-9_complemento_parcial_32mb.gba`.

## TMs e aprendizados

A loja na **placa ao lado da casa em Pallet** passa de 189 para **203 das 229 TMs de Scarlet/Violet**. As 14 adicionadas são:

| TM9 | Golpe | Observação |
|---|---|---|
| 020 | Trailblaze | dano e aumento de velocidade do usuário |
| 021 | Pounce | dano e redução de velocidade do alvo |
| 022 | Chilling Water | dano e redução de ataque do alvo |
| 072 | Electro Ball | cálculo de velocidade parcial |
| 121 | Heavy Slam | cálculo de peso parcial |
| 144, 145, 146 | Fire, Water, Grass Pledge | dano básico; **sem combinações** em duplas |
| 169 | Draco Meteor | dano e redução de ataque especial do usuário |
| 171 | Tera Blast | golpe normal especial; **sem Terastalização** |
| 180 | Gyro Ball | cálculo de velocidade parcial |
| 189 | Heat Crash | cálculo de peso parcial |
| 194 | Grassy Glide | dano básico; **sem prioridade de terreno** |
| 215 | Scorching Sands | dano e chance de queimadura |

Elas custam 3.000, são reutilizáveis e usam a compatibilidade da base PokéAPI conforme as fontes usadas anteriormente. A tabela [tms_gen9_complemento.csv](../data/tms_gen9_complemento.csv) identifica números, nomes e limitações; `disponivel` significa que pode ser comprada e ensinada, **não** que todas as interações de Gen 9 estejam implementadas.

Foram reintroduzidos **116 registros de aprendizagem por nível**, de Shell Smash, Autotomize, Electro Ball, Gyro Ball, Heavy Slam e Heat Crash. O total passa de 14.184 para **14.300 registros** sem remover os anteriores. Pokémon já salvos não têm golpes substituídos automaticamente. O relembrador continua limitado a **24 golpes mais Cancelar**.

Ainda restam **26 TMs indisponíveis** e **729 registros de aprendizagem omitidos**, correspondentes a **81 nomes de golpes**. Por exemplo: Toxic Spikes, Stealth Rock, Tailwind, Trick Room, terrenos, Fling e os golpes Steel Beam, Triple Axel e outros. A lista completa de omissões por nível está em [golpes_pendentes_complemento.csv](golpes_pendentes_complemento.csv). O catálogo não é uma auditoria de fidelidade de todos os 203 golpes oferecidos.

## Alterações e limites do cálculo de batalha

- Shell Smash altera Defesa/Defesa Especial em −1 e Ataque/Ataque Especial/Velocidade em +2. Autotomize aumenta Velocidade em +2, **mas ainda não reduz o peso**.
- Ice Fang e Thunder Fang agora têm duas rolagens de efeito de 10%: congelar/paralisar e causar flinch. Close Combat reduz as duas defesas do usuário; Dual Wingbeat usa a rotina de dois acertos. As interações não foram testadas exaustivamente.
- Gyro Ball e Electro Ball usam uma razão básica de velocidade com estágios, paralisia e Macho Brace. A paralisia segue a regra da ROM base, não necessariamente a de Gen 9. Clima, habilidades, insígnias e outros modificadores não foram todos portados.
- Heavy Slam e Heat Crash usam o peso **da forma padrão da espécie** pela PokéAPI. Formas alternativas, Autotomize e habilidades/itens que alteram peso não são considerados. A IA pode avaliar mal golpes dinâmicos porque a rotina de previsão não foi modernizada. O menu pode exibir `---` como poder, embora o cálculo de combate seja dinâmico.
- Foram acrescentados cálculos básicos para Acrobatics, Stored Power, Power Trip, Venoshock e Hex. Body Press usa a Defesa do usuário; Foul Play, o Ataque do alvo; Psyshock e Psystrike usam a Defesa do alvo. Bônus, habilidades, telas e demais detalhes permanecem os do motor antigo; esses movimentos **não são portações integrais**.
- U-turn, Volt Switch e Flip Turn continuam sem a troca esperada. A IA, habilidades, objetos, animações e outras interações não foram integralmente modernizados. As animações dos dez nomes novos são genéricas.

As TMs/HMs antigas não foram substituídas, e as HMs necessárias à história permanecem. **O estojo continua com 58 tipos de item**, compartilhados entre TMs antigas, novas e HMs; não cabem as 203 TMs simultaneamente. O jogo deve recusar a compra ao estar cheio. Não descarte HMs; para liberar espaço pode ser necessário usar uma TM antiga ou vender uma TM, lembrando que algumas antigas podem ser difíceis de recuperar. O aumento de 16 para 32 MiB não amplia esse espaço no save.

## Antes de jogar

1. Faça um **backup separado do `.sav` original** e mantenha a ROM anterior. Nenhum save pessoal foi usado nos testes.
2. Copie o save para o nome esperado pelo emulador, normalmente `ptbr_gen1-9_complemento_parcial_32mb.sav`, ou use a importação do próprio emulador. Confira equipe, itens e progresso; depois salve pelo menu do jogo.
3. Não reutilize save states/estados rápidos da ROM anterior. Não use na ROM antiga o único save que já contenha os novos IDs de golpes ou itens: mantenha uma cópia anterior segura.
4. Esta ROM tem 32 MiB e precisa de emulador/dispositivo que suporte esse tamanho. A compatibilidade de todos os saves, emuladores e toda a campanha não foi provada.

As tabelas selvagens, os **1.982 objetos de mapa** e o código de treino foram comparados com a entrada e não mudaram. Phione e Moltres, encontro selvagem e retirada de Tarountula parado foram exercitados por amostragem. As listas de golpes iniciais de Pokémon recém-criados, inclusive lendários, podem mudar. O treino continua em Equipe → Resumo → Atributos → SELECT: redistribuição dos EVs já ganhos e consulta de IVs.

## Reprodução e testes

```sh
python3 scripts/complemento_gen9.py \
  --rom minha_rom_tms_anterior.gba \
  --saida nova_copia.gba
```

O aplicador exige o SHA da entrada e dos dados, exige destino novo, realoca tabelas e verifica os ponteiros conhecidos. Tabelas de nível e compatibilidade vêm da PokéAPI no commit `6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce`; preserve [POKEAPI_LICENSE.txt](../data/POKEAPI_LICENSE.txt). `scripts/gerar_complemento_gen9.py` regenera os CSVs e pesos com os dados desse commit. A fonte Thumb e o payload estão em `patches/complemento_gen9/`.

Em mGBA 0.10.5 foram verificados a loja (compra e ensino da TM020 e acesso ao último produto), TMs/HMs antigas, compatibilidade, aprendizado por nível, as categorias físico/especial dos dez golpes novos, efeitos, cálculos básicos, save sintético anterior, save/reload com golpe de ID acima de 796, treino e exemplos de encontros/eventos. Algumas chances foram forçadas somente em cópias temporárias de teste. Uma execução integrada anterior teve **137 testes, 134 aprovados e 3 pulados** por falta da ROM privada original dos encontros; o teste adicional da loja também foi aprovado. Não são testes exaustivos nem uma campanha completa.
