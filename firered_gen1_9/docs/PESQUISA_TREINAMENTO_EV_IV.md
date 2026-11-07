# Pesquisa: treinamento RPG, EVs e IVs

**Estado:** a opção escolhida — conservar os EVs ganhos nas batalhas e redistribuir apenas esses pontos — foi implementada em uma cópia separada da ROM de encontros. IVs são visíveis, mas não são alterados. Os controles, limites, testes e ressalvas estão em [TREINAMENTO_EV_IV.md](TREINAMENTO_EV_IV.md). A prévia anterior era apenas uma simulação; a ROM entregue agora contém a interface funcional.

## Referências pesquisadas

| Referência | Ideia útil | Limite para este projeto |
|---|---|---|
| [Custom EV/IV Display, de Acimut](https://github.com/Acimut/Custom-EV-IV-Display-Screen/blob/SummaryScreen/README.en.md) | Mostra EVs, IVs e atributos-base no resumo. | É um visualizador, não um sistema de treinamento. Seus endereços e código não foram aplicados à nossa ROM. |
| [Stat Scanner de Pokémon Unbound](https://unboundwiki.com/items/key-items/stat-scanner/) | Exibe dados ocultos; edições avançadas dependem de melhorias e progresso. | A disponibilidade depende da versão/dificuldade e não estabelece compatibilidade com esta base. |
| [Emerald Battle Revolution](https://github.com/damon-murdoch/emerald-battle-revolution-legacy) | Mostra EVs e IVs na página de atributos e usa itens de treinamento. | É baseado em Emerald. Aqui L/R já abrem a ajuda, então a implementação usa SELECT. |
| [Discussão comunitária sobre EVs e IVs](https://www.reddit.com/r/PokemonROMhacks/comments/13xbbhk/about_ivs_and_evs_mechanics_in_pokemon_romhacks/) | Treinamento por foco ou pontos são ideias possíveis de design. | Sugestões não são uma prova de compatibilidade ou balanceamento. |
| [Effort values — Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Effort_values) | Explica EVs, limites e arredondamento nas gerações. | A mecânica de um hack específico precisa de verificação própria. |

Na mecânica tradicional, IVs vão de 0 a 31. Na geração III, o limite é **255 EVs por atributo e 510 no total**, embora 252 seja o máximo útil por atributo para a fórmula no nível 100. No nível 100, cada 4 EVs no mesmo atributo produzem aproximadamente 1 ponto antes do efeito da natureza; no nível 50 o efeito é aproximadamente metade. Arredondamento e casos especiais importam.

## Observações e decisão

Na versão de encontros, um Bulbasaur ganhou 1 EV de Ataque ao derrotar um Pancham. Em estados temporários, Ataque 252 passou a 253, 255 permaneceu 255, total 509 passou a 510 e total 510 permaneceu 510. Esses ensaios sustentam os limites 255/510 para o caminho de batalha observado, sem validar todo item ou modo de ganho.

Foi escolhida a **redistribuição conservadora**: em vez de conceder pontos por nível ou criar um segundo bônus, o jogador retira EVs existentes para um saldo temporário e os coloca em outro atributo. A soma deve ser a mesma ao confirmar; B cancela. Valores antigos 253–255 são mantidos, e não existe melhoria de IVs nesse treino.

Esse desenho respeita os tetos observados e não infla a soma de EVs; a facilidade de concentrá-los pode, ainda assim, facilitar o jogo. O impacto no início, meio e fim da campanha não foi completamente medido. Os testes de funcionamento e as restrições concretas estão no guia principal.

O modelo independente `scripts/modelo_treino.py` continua disponível para estudar as regras; ele não instala o mod. A instalação de fato está em `scripts/treino_ev.py` e `patches/treino_ev/`.
