# Treino de EV e visualização de IV — edição de encontros Gen 1–9

Esta variante é uma **cópia separada** da ROM de encontros selvagens. Ela mantém o ganho de EVs da própria ROM e permite redistribuir somente pontos já presentes em cada Pokémon. **Não concede pontos extras nem edita IVs.** A pesquisa das alternativas está em [PESQUISA_TREINAMENTO_EV_IV.md](PESQUISA_TREINAMENTO_EV_IV.md).

## Como usar no jogo

1. Abra **Pokémon → escolha um Pokémon → Resumo → Atributos** a partir da sua equipe, fora de batalha.
2. Pressione **SELECT** para alternar entre os atributos normais, os **EVs** e os **IVs**. O aviso `SELECT EV/IV` aparece no alto. Os seis números seguem a ordem da tela: HP, ataque, defesa, ataque especial, defesa especial e velocidade.
3. Na visualização de EVs, o rodapé mostra o total, por exemplo `EV 30/510`, e `A:TREINAR`. Pressione **A** para abrir o treino.
4. A seta `>` marca o atributo selecionado. Use **cima/baixo** para escolhê-lo. Use **esquerda** para retirar EVs dele e formar um `SALDO` temporário; use **direita** para gastar esse saldo no atributo escolhido. **SELECT** alterna passos de 4 e de 1.
5. **A** confirma apenas quando `SALDO` volta a zero. **B** cancela e restaura a distribuição anterior, mesmo se ainda houver saldo. Enquanto o treino está aberto, as setas não mudam de Pokémon ou de página: confirme ou cancele primeiro.

**Exemplo:** depois de vencer um Pidgey e ganhar 1 EV de velocidade, entre em EV → A, pressione cima para ir de HP a velocidade e esquerda para retirar o ponto; pressione baixo duas vezes para selecionar ataque e direita para aplicá-lo. Com saldo zero, A confirma. No nível baixo, a mudança pode não alterar o número visível do atributo devido ao arredondamento da fórmula.

- É possível abrir o treino com zero EVs, mas não há pontos para distribuir até que o Pokémon os tenha ganhado.
- O limite da ROM é **255 por atributo e 510 somados**. EVs 253–255 já existentes não são apagados. Um dado com total acima de 510 é marcado como inválido e a edição fica bloqueada.
- IVs são exibidos, mas não podem ser alterados. A barra verde continua sendo **HP**, não uma barra de EVs. Ao voltar à tela normal, a descrição original da habilidade reaparece.
- A função é restrita ao resumo da própria equipe, fora de batalha. Ela não foi habilitada deliberadamente em resumos de PC, troca, adversário, seleção de golpe ou combate. Ovos e Pokémon com dados inválidos não são editados.
- L/R continuam abrindo a ajuda original. Se a ajuda for aberta durante um treino, volte dela e então confirme ou cancele o rascunho; não confunda o B da ajuda com o B do treino.

## Segurança de saves

**Faça uma cópia de segurança do `.sav` antes de experimentar.** Não substitua a ROM anterior nem o único save. Muitos emuladores associam o save ao nome da ROM: nesse caso, copie o `.sav` antigo para o nome correspondente à nova ROM, mantendo o arquivo antigo intacto. O nome e o local variam conforme o emulador. Prefira o save normal do jogo; não confie em save states de outra versão de ROM.

O patch não adiciona um formato de save: grava os campos existentes de EV após confirmação. No teste com um save criado para a versão de encontros, um Pokémon foi carregado byte por byte sem mudanças; um save de teste da nova versão também foi salvo e recarregado após redistribuição. **O save pessoal do usuário e todos os emuladores não foram testados**, portanto compatibilidade total não é garantida.

Ao confirmar, o jogo recalcula os atributos. Pokémon desmaiados permanecem com HP zero; para um Pokémon vivo, a diferença de HP máximo é aplicada ao HP atual, limitado a pelo menos 1 e no máximo ao novo HP máximo. O original só é substituído depois de verificar checksum, orçamento e se o rascunho corresponde ao mesmo Pokémon; mudanças em outros campos não são autorizadas.

## Reproduzir a ROM

São necessárias as próprias cópias do usuário. A ROM e os saves **não ficam no repositório**.

| Arquivo | SHA-256 |
|---|---|
| Entrada: `ptbr_gen1-9_selvagens.gba` | `3f8cc9e3a52b1bad8a2f22df9a302f79a355e929669c5425ef023017bd4c4e49` |
| Saída: `ptbr_gen1-9_selvagens_treino.gba` | `1123e7995b37008a75c818f09fb852bfd4910e1f074ae2e630cbd9c8af994abc` |

```bash
python3 scripts/treino_ev.py \
  --rom caminho/ptbr_gen1-9_selvagens.gba \
  --saida caminho/ptbr_gen1-9_selvagens_treino.gba
python3 -m unittest discover -s tests -v
```

A saída não pode existir e a entrada não é alterada. O instalador exige o hash exato, testa o prólogo esperado, uma área de 4 KiB preenchida por `FF` e ausência de ponteiros **alinhados** para essa área; em seguida verifica que todas as diferenças estão no hook de 8 bytes e no payload. Isso não é uma prova universal contra referências indiretas e **não autoriza aplicar o patch a outra ROM ou combinar patches arbitrários**.

O código-fonte está em `patches/treino_ev/treino_ev.c`, o trampolim em `entry.s` e o payload compilado em `payload.bin` (SHA-256 `cdf2238a72f00298a7b5a06721d266b6e9ff9826f5174006b64ea6e07c28f6fb`). O binário foi produzido com Zig 0.13.0 para ARM7TDMI Thumb; uma recompilação local retornou bytes idênticos:

```bash
zig cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -mfloat-abi=soft -Oz -ffreestanding -fno-builtin -fno-unwind-tables \
  -fno-asynchronous-unwind-tables -fno-stack-protector -nostdlib \
  -Wl,-T,patches/treino_ev/payload.ld -Wl,--gc-sections -Wl,-e,treino_entry \
  patches/treino_ev/entry.s patches/treino_ev/treino_ev.c -o /tmp/treino.elf
zig objcopy -O binary /tmp/treino.elf /tmp/treino.bin
sha256sum /tmp/treino.bin
```

Os nove testes opcionais de integração reproduzem uma partida de teste e exigem uma cópia da ROM resultante e o core **mGBA libretro 0.10.5**:

```bash
TREINO_TEST_ROM=caminho/ptbr_gen1-9_selvagens_treino.gba \
MGBA_CORE=caminho/mgba_libretro.so \
python3 -m unittest discover -s tests -p 'test_treino_ev_mgba.py' -v
```

Eles não escrevem saves existentes: criam a partida e alteram dados somente em estados temporários em memória. Sem essas variáveis, são marcados como pulados.

## Validação e limites

- No core mGBA 0.10.5, a ROM final iniciou uma partida, mostrou atributos/EVs/IVs e foi exercitada com saldo pendente, confirmação, cancelamento, passos 1/4, limites 255/510, dados 253–255 e checksum. Os seis slots foram testados com **cópias sintéticas** de um Pokémon legítimo; os demais slots permaneceram byte a byte inalterados.
- Um Pokémon ganhou 1 EV de velocidade ao vencer um Pidgey, transferiu o ponto para ataque e conservou EVs, IVs e checksum depois de salvar e recarregar. Em outra batalha de teste, com HP previamente restaurado **somente no estado temporário**, subiu ao nível 6, manteve o EV transferido e ganhou outro EV normalmente.
- Estados temporários também testaram HP zero, HP 1 com redução de máximo, limite inválido, checksum inválido, cópia desatualizada e restrições de contexto. A tela de ajuda foi aberta durante um treino, o B posterior cancelou sem alterar a equipe, e um rascunho ficou estável por 3.600 quadros.
- Em uma amostra real, a ficha de personagem abriu e, na batalha, SELECT na tela de atributos manteve o comportamento normal. As tabelas de encontros e eventos estão fora das duas regiões modificadas; a entrega anterior já tinha testes amostrais de capturas/eventos.
- Foram executados **51 testes automatizados**, incluindo os nove com mGBA e as três verificações que exigem a ROM de base privada. Sem esses arquivos locais, esses testes são pulados.
- Não foram percorridos todos os Pokémon, métodos de ganho, evolução, PC/trocas, lendários, rotas, emuladores ou etapas de campanha com esta variante. Os testes de ovo/PC/troca usam flags simuladas, não fluxos completos. O teto evita inflação de EVs, mas a facilidade de otimizar a equipe pode alterar a dificuldade; o equilíbrio completo de campanha permanece sem validação.
