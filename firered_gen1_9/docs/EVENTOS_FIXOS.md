# Pokémon fixos comuns no mapa

Esta variante parte da ROM com encontros selvagens **e** treino de EV/IV. Ela retira do mapa os Pokémon comuns que usavam o sistema adicional de encontros fixos identificado nesta ROM. A ROM anterior e o save original não são editados.

## O que foi feito

- Foram examinados 425 mapas, 1.982 objetos e 334 objetos que apontam ao mesmo script de Pokémon fixo, em 57 mapas. Os 334 ponteiros diretos a esse script foram encontrados nos objetos inventariados.
- **224 objetos de espécies comuns**, em 41 mapas, foram colocados fora dos limites jogáveis. Todas essas espécies já têm ao menos uma entrada estrutural em grama/caverna ou surf no guia existente. Exemplos: Tarountula, Ralts, Chikorita, Wooloo e Fennekin.
- Os **110 objetos especiais** desse mesmo sistema foram preservados integralmente: 81 lendários/míticos pela PokéAPI, 9 Ultra Beasts e 20 Paradox. Ultra Beasts e Paradox são conservados por precaução, mesmo quando o catálogo não os marca como lendários. Alguns também já estavam nas tabelas selvagens anteriores.
- **Eventos de história e outros sistemas não foram alterados.** Em particular, Snorlax nas rotas, o fantasma Marowak na Torre, a cena de Hypno e os Electrode disfarçados continuam como na versão anterior. Assim, não se deve afirmar que todo encontro especial de espécie comum foi removido: o escopo é o sistema de objetos extras auditado, não eventos ligados à história ou outros scripts.
- A ROM com treino e suas tabelas selvagens foram preservadas. A mudança não mexe nos Pokémon já capturados, nos itens, em flags de captura ou no save.

[Inventário dos 334 objetos, suas categorias e uma localização selvagem quando há](eventos_fixos_inventario.csv). [Guia de 931 espécies não lendárias/míticas](guia_encontros.csv). Em ambos, a chance é **condicional a um encontro** na modalidade indicada; 1% não quer dizer um encontro a cada 100 passos. O guia lista um local, não necessariamente todos, e os dados não provam acessibilidade de cada mapa nem cada captura.

Exemplo: Tarountula não fica mais parado na Rota 1; foi verificado em batalha selvagem no **Mt Ember Exterior**, grama, nível 42, slot de **1% por encontro**. Essa área é posterior na aventura; não se promete Tarountula selvagem no começo do jogo.

## Uso e saves

1. Faça backup do `.sav` original. Use a ROM nova como uma cópia separada, sem apagar a anterior.
2. **Copie** o save para o nome esperado pela ROM nova (geralmente o mesmo nome da ROM com extensão `.sav`, na pasta de saves do emulador). Não renomeie nem sobrescreva seu único arquivo; alguns emuladores usam pastas ou função de importação próprias.
3. Carregue o **save feito no menu do jogo**, não um save state/estado rápido feito com a ROM antiga.
4. Se o save foi feito em um mapa que tinha os fixos comuns, pode aparecer um sprite antigo ao carregar: o save guarda uma cópia temporária dos objetos daquele mapa. **Entre em outro mapa e volte**, depois salve pelo menu do jogo. O modelo atualizado então é carregado. Em um teste com save de uma Rota 1 antiga, a transição e o save/reload seguintes mantiveram o Pokémon da equipe byte a byte.
5. EV/IV continuam em Equipe → Resumo → Atributos: SELECT alterna páginas; na página de EV, A edita; cima/baixo selecionam, esquerda/direita transferem, SELECT alterna passo, A confirma com saldo zero e B cancela. Veja [treinamento](TREINAMENTO_EV_IV.md).

A compatibilidade foi testada com um save criado para o teste em mGBA 0.10.5; o save particular do usuário e todos os emuladores não foram testados.

## Método e proteção

A ROM usa `gMapGroups` no offset de arquivo `0x8493E8` (endereço GBA `0x088493E8`) e objetos de 24 bytes. Os objetos desse sistema têm `graphicsId=0x98`, script compartilhado `0x081EF400`, espécie no campo auxiliar e flag `0x5000 + espécie`. O Tarountula auditado era objeto 6 da Rota 1, `(17,9)`. O parser valida cabeçalhos, faixas não sobrepostas, IDs, flags, script, espécies, 334 referências e cobertura selvagem; também recusa mover alvo de um clone. A lista de grupos deriva de [pret/pokefirered](https://github.com/pret/pokefirered) commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, conferida contra a estrutura real da ROM.

Para não reordenar IDs (que podem ser usados por scripts/clones ou saves), o patch **não remove entradas do array**. Muda apenas `x` e `y` dos 224 objetos selecionados para `(-1024,-1024)`, fora da área visível/acessível. Os 896 bytes que diferem são exclusivamente esses campos; estrutura, ordem, contagens, flags, scripts, encontros selvagens, outros objetos e código de treino permanecem idênticos. Não há mudança de flag global nem código novo.

- Entrada: SHA-256 `1123e7995b37008a75c818f09fb852bfd4910e1f074ae2e630cbd9c8af994abc`
- Saída: SHA-256 `c563d43a8f15976314ad5fb271ad44a83cdf3143749389311f261ffd506a466b`

O instalador exige a entrada exata, hashes dos catálogos, contagens e hash de saída. Ele cria uma ROM nova e recusa sobrescrita, inclusive links. Não contém nem baixa ROMs:

```sh
python3 scripts/eventos_fixos.py --self-test
python3 scripts/eventos_fixos.py --rom minha_rom_com_treino.gba --saida nova_copia.gba
```

## Testes e limites

Em uma execução com as ROMs privadas locais e mGBA 0.10.5, **71/71 testes** passaram, incluindo:

- Comparação byte a byte, inventário completo do script compartilhado, exclusão dos 110 objetos protegidos e preservação dos encontros selvagens e do payload de treino.
- Transição natural à Rota 1 comparando versões, NPC mantido, Ralts ausente e Tarountula antigo presente só na anterior.
- Batalha selvagem de Tarountula nível 42 no Mt Ember, e batalhas fixas de Phione e Moltres. Para chegar aos locais distantes, o teste usa **cópias temporárias instrumentadas apenas com warp**; as ROMs entregues não contêm esse warp. O encontro selvagem foi gerado pelo mecanismo normal, sem alterar o RNG.
- Save anterior salvo na Rota 1 → nova ROM → saída e retorno ao mapa → save normal e reload, com Pokémon da equipe intacto. Outros mapas, saves pessoais e estados rápidos não foram exaustivamente testados.
- Nove testes mGBA da interface de treino na nova ROM, incluindo limites de EV, cancelamento, checksum, seis slots e HP. A campanha inteira, o caminho natural ao Mt Ember, todas as capturas e todos os emuladores não foram testados.

Para reproduzir a suíte completa sem fornecer ROMs ao repositório:

```sh
FIXOS_TEST_BASE=google_drive/ptbr_gen1-9_selvagens_treino.gba \
FIXOS_TEST_ROM=rom_mod/ptbr_gen1-9_selvagens_treino_sem_fixos_comuns.gba \
TREINO_TEST_ROM=rom_mod/ptbr_gen1-9_selvagens_treino_sem_fixos_comuns.gba \
MGBA_CORE=/caminho/mgba_libretro.so python3 -m unittest discover -s tests -v
```
