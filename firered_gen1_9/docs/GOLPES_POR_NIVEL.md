# Golpes por nível: variante Gen 1–9

Esta variante parte da ROM PT-BR com selvagens, treino e fixos comuns removidos. Ela atualiza os **aprendizados por nível** e substitui a codificação antiga de IDs de golpes, que truncava valores acima de 511. A ROM de entrada e os saves não são alterados pelo instalador.

- Entrada: SHA-256 `c563d43a8f15976314ad5fb271ad44a83cdf3143749389311f261ffd506a466b`
- Nova ROM: SHA-256 `412bcd89214d4126d92f6c2256a56227c6f30fa138e0b262ef287f5b12b3997b`

## O que mudou

- O catálogo tem **14.018 entradas espécie/nível/golpe**, para as 1.025 espécies base. A referência preferida é Scarlet/Violet (733 espécies). Quando não há lista da espécie nesse jogo, usam-se Sword/Shield (244), Brilliant Diamond/Shining Pearl (39) e, por último, Ultra Sun/Ultra Moon (9). As contagens são de espécies, não de formas alternativas. Crabrawler recebe um golpe inicial seguro de USUM porque a referência escolhida não tinha golpe inicial registrado.
- A rotina de aprendizado, golpes iniciais, relembrador, evolução e consulta de golpes por nível na creche passam a ler o ID completo. Os dados de Pokémon e o formato do save não mudam.
- Exemplos testados: Tarountula aprende **Struggle Bug** (ID interno 518) no nível 5, em vez do **Pay Day** causado pelo truncamento. Charizard pode aprender **Flare Blitz** no 62 e **Air Slash** na evolução; são golpes de gerações anteriores usados aqui como exemplos, não exclusivos da geração 9.
- As tabelas de encontros selvagens, os modelos dos 1.982 objetos dos mapas e o código de treino foram comparados com a entrada e permaneceram iguais. Os fixos especiais, incluindo Moltres e Phione, continuam nos mesmos locais e seus eventos foram exercitados por amostragem. **Os golpes iniciais de Pokémon recém-gerados, inclusive lendários, podem mudar** com as novas listas; a posição e o evento não mudaram.
- O treino permanece em Equipe → Resumo → Atributos → SELECT. Na página de EV, A edita, direções redistribuem, A confirma com saldo zero e B cancela. Só redistribui EVs já conquistados; IVs são apenas exibidos. Detalhes em [TREINAMENTO_EV_IV.md](TREINAMENTO_EV_IV.md).

## Limitações importantes

- **Não foram implementados ou atualizados efeitos, animações, poderes, precisão nem compatibilidade de TM/HM.** A ROM mantém os dados de batalha anteriores. Um nome presente não garante a mecânica de Scarlet/Violet. Por exemplo, nesta base Struggle Bug causa dano, mas não tem o efeito secundário moderno de reduzir Ataque Especial; Flare Blitz conserva o efeito anterior de recuo, sem a queimadura moderna. Outros golpes podem ter diferenças ou animações genéricas.
- Para evitar ensinar alguns placeholders identificados na base, **1.011 entradas** foram omitidas: 890 sem efeito utilizável e 121 com poder dinâmico não implementado. A contagem é de ocorrências na lista, não de nomes distintos. Por exemplo, **Heat Crash** de Emboar foi omitido; não foi implementado nesta variante. A relação é [golpes_por_nivel_nao_incluidos.csv](golpes_por_nivel_nao_incluidos.csv). Essa filtragem não garante que todos os demais efeitos estejam completos.
- TM/HM, tutores e tabelas próprias de golpes por ovo não foram atualizados para a Gen 9. Não foi feita uma campanha completa nem testados todos os golpes, Pokémon, mapas, formas, métodos de reprodução ou emuladores.
- O relembrador comporta até **24 golpes mais Cancelar**. Se houver mais elegíveis, mostra os 24 mais recentes da lista; alguns antigos podem não aparecer. Nomes compridos são abreviados em determinados menus e textos para respeitar o tamanho dos buffers.
- Pokémon que já estão no save **não têm os golpes substituídos automaticamente**. Um golpe errado recebido antes da correção não é identificado nem consertado retroativamente. Depois de atualizar, veja o relembrador do jogo para golpes elegíveis, sujeito ao limite acima.

## Usar com segurança

1. Guarde a ROM anterior e faça um **backup do `.sav` original** em outra pasta. Não use seu único arquivo como teste.
2. Copie o save para o nome esperado pela ROM nova, geralmente `ptbr_gen1-9_selvagens_treino_golpes_nivel.sav`, na pasta de saves do emulador. Alguns emuladores usam outra pasta ou uma função de importação.
3. Carregue um save feito pelo **menu do jogo**. Não reutilize save state/estado rápido da ROM antiga: ele pode carregar código ou dados temporários incompatíveis.
4. Confirme equipe, golpes e progresso. Se um sprite fixo antigo aparecer num mapa, saia e entre novamente nesse mapa; então salve pelo menu. Isso pode ocorrer porque o save guarda temporariamente objetos do mapa.

Um save anterior foi gerado pelo próprio jogo para teste, carregado na nova ROM, salvo de novo e recarregado com a equipe preservada. Isso não garante a compatibilidade de todos os saves pessoais ou emuladores. Nenhum save pessoal foi utilizado.

## Fonte e reprodução

O catálogo usa os CSVs da [PokéAPI no commit `6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce`](https://github.com/PokeAPI/pokeapi/tree/6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce/data/v2/csv). A licença BSD, copyright e disclaimer acompanham os dados em [POKEAPI_LICENSE.txt](../data/POKEAPI_LICENSE.txt). O gerador `scripts/gerar_catalogo_golpes.py` requer esses CSVs e a ROM de entrada particular; não baixa nem distribui ROMs. O código ARM/Thumb e o binário auditável ficam em `patches/golpes_gen9/`.

O instalador confere hash, catálogo, hooks, região livre e saída, e **recusa sobrescrever arquivos**:

```sh
python3 scripts/golpes_gen9.py --self-test
python3 scripts/golpes_gen9.py --rom minha_rom_anterior.gba --saida nova_copia.gba
```

Ele se aplica somente à ROM identificada pelo hash acima. A presença de região `0xFF` sem referências alinhadas é uma salvaguarda, não uma prova geral de que qualquer ROM tenha o mesmo espaço livre.

## O que foi testado

- Equivalência de todas as 1.025 listas geradas ao catálogo; limites do relembrador, consulta da creche, nomes, múltiplos golpes no mesmo nível, equipe cheia e evolução/cancelamento em mGBA com estados sintéticos.
- Início normal com Bulbasaur; encontro selvagem normal de Tarountula nível 42 no Mt Ember com golpes `(68, 29, 508, 630)`; batalha com Tarountula sintético nível 4, subida ao 5 e substituição de um golpe por Struggle Bug; batalha e evolução normal de Charmeleon para Charizard com Air Slash.
- Relembrador do jogo ensinando Struggle Bug; Phione e Moltres em batalha fixa; ausência do Tarountula parado da Rota 1. Para alcançar mapas distantes e fornecer um cogumelo ao relembrador, os testes usaram **cópias descartáveis instrumentadas**; a ROM entregue não contém esses auxílios.
- Save de teste criado na ROM anterior com Pokémon sintético, carregado na nova ROM sem mudança nos dados da equipe; uma batalha concedeu EV, subiu Charizard ao nível 62 e ensinou Flare Blitz. O novo save foi recarregado com os dados preservados. Os nove testes mGBA da tela de treino também passaram na nova variante.
- Testes são amostrais: ovos/troca foram exercitados por rotinas e estados simulados, e não pelo ciclo completo de reprodução/troca. Não se pode extrapolar para todas as campanhas, eventos ou aparelhos.

A suíte pode ser repetida sem salvar ROMs no repositório:

```sh
GOLPES_TEST_BASE=/caminho/rom_anterior.gba \
GOLPES_TEST_ROM=/caminho/rom_nova.gba \
TREINO_TEST_ROM=/caminho/rom_nova.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s tests -v
```

Outros testes da suíte exigem versões anteriores específicas e são pulados quando elas não são fornecidas. Veja também a [pesquisa preliminar](PESQUISA_GOLPES_GEN9.md), a [documentação de encontros](ENCONTROS_SELVAGENS.md) e a [de fixos](EVENTOS_FIXOS.md).
