# Repasse técnico — FireRed Gen 1–9 e hook v3 histórico

**Fotografia de 31/10/2026.** O projeto segue incompleto. Este material foi preparado para colaboração **sem acesso ao GitHub**: fatos, código e testes estão no Drive; questões e próximos passos ficam no Linear. As atualizações são manuais, não há sincronização automática.

- Acompanhamento: [Linear VYK-57](https://linear.app/vyktormustang/issue/VYK-57/repasse-ao-claude-e-revisao-do-motor-de-tms-gen-1-9).
- [Pasta de colaboração no Drive](https://drive.google.com/drive/folders/1CCI4TsHaM7HwdOoYftrVVuz89nu5R1Ri), com permissões herdadas; acesso depende da conta e das conexões do usuário. Nenhuma permissão pública foi criada para este repasse.
- Leitura: [hook v3 histórico — diagnóstico, HANDOFF e builder](https://drive.google.com/file/d/14YFDRbUgfR2ttF_LA1BEUtVCw-2_JTsB/view), [motor Gen 1–9 — fontes e testes](https://drive.google.com/file/d/1azq4dEBnbCrHQWdu0Bn53wE8d2Zzfd3M/view), [estojo v2 — fontes e testes](https://drive.google.com/file/d/16nCjq0qYzCrl3YQ5gTaXBHVOHFfubGw9/view), [catálogo experimental de TMs](https://drive.google.com/file/d/1B0zyLOnlxsJWTEaAH9cO4mCkCK36y5en/view).
- A pasta também contém versões em Google Docs para leitura e o arquivo `05 — Fontes e testes sem ROM.zip` com arquivos exatos, manifestos SHA-256, dados, patches e testes. Na conversão para Google Docs, linhas em branco podem mudar: para bytes exatos, use o ZIP ou os `.txt` sem conversão. O ZIP **não contém ROM, save, save state nem o core mGBA**.

## O que o usuário pediu

Adicionar TMs e aprendizados de Scarlet/Violet sem substituir as TMs antigas; preservar HMs necessárias à história; remover limites do estojo e corrigir itens e mecânicas. O usuário autorizou aumentar o tamanho da ROM e criar um novo motor quando necessário. Também pediu Pokémon comuns e inobtíveis por métodos indisponíveis na natureza, a correção de comuns parados no mapa, preservação dos lendários e eventos essenciais e treino equilibrado com visualização de EVs/IVs e redistribuição dos EVs já conquistados.

Não tratar uma ROM parcial, uma lista de itens disponíveis, um boot bem-sucedido ou um teste sintético como prova de implementação completa.

## Duas bases diferentes: não misturar

### 1. ROM Gen 1–9: trabalho atual

| Artefato | SHA-256 | Situação |
|---|---|---|
| [Complemento parcial 32 MiB](https://drive.google.com/file/d/19kJJSX-j1GcLtl4maLMOBCqXNf6aFhE6/view) | `6155b6a5fe62528b7b67836d3a47f32b1cb3b1a71c1f2b59bfa7a68af0100d67` | Já entregue; 203/229 TMs listadas como disponíveis. Não é uma engine Scarlet/Violet completa. |
| Estojo expandido v2 | `93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907` | Rascunho reconstruível a partir do complemento; testes pontuais 18/18 passaram anteriormente. Não é a ROM parcial entregue. |
| Motor v5 experimental | `cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87` | Resultado anteriormente construído sobre o estojo v2; precisa ser reconstruído e sua suíte ampla executada. Não foi entregue como versão pronta. |

A ROM entregue contém 14.300 aprendizados por nível, 729 registros omitidos de 81 nomes de golpes, 203 TMs disponíveis e 38.963 compatibilidades. "Disponível" quer dizer oferecida/ensinável no catálogo, **não** fidelidade completa da mecânica. O estojo dessa entrega ainda tem 58 tipos compartilhados entre TMs e HMs. Veja [instruções da entrega](https://drive.google.com/file/d/1pfL6MGNbuiFozrae1JLHY5T2dT-rkE4T/view), [catálogo da entrega](https://drive.google.com/file/d/16cOvLTt272iRDJhiOkn-RtwGXeDGrBwd/view), [omissões por nível](https://drive.google.com/file/d/1WuhI59a5hErSN3RMWkwILDd6ZQ7jq4sm/view) e [licença PokéAPI](https://drive.google.com/file/d/1oMQc0GSy4JPb5gJfA6WXCzgCfAVxim_i/view).

O estojo v2 mantém os 58 slots originais e acrescenta 229 quantidades compactadas de 10 bits para IDs 375–603, assinatura `T9X1`, em `SaveBlock1+0x34D8..0x3667`, com três páginas. Foram feitos testes sintéticos de capacidade, navegação, consumo, save/recarga e Pokedude; Teachy TV completa e link entre dois jogadores não foram comprovados. Não presumir que o backup temporário de link cubra uma extensão modificada.

No motor v4 foram testados Hard Press, consumo e substituição por interface; a suíte daquele estado passou 14/14. O v5 adiciona correção do Quest Log, cuja rotina foi exercitada em estados sintéticos com itens 294, 339, 346, 394 e 599 para aprender/substituir; **a suíte ampla v5 ainda não foi executada**. Hard Press é item 599/TM225, golpe interno 807, poder 1–100 proporcional ao HP atual/máximo do alvo; o catálogo do rascunho passa a 204/229. `OUTPUT_SHA256` está vazio nos aplicadores: confirme os hashes manualmente. Os binários do Quest Log foram restaurados a seus hashes esperados antes deste repasse; `checked_inputs()` e dois testes de catálogo passaram em 31/10. Quatro testes estruturais que dependem das duas ROMs foram pulados por falta dessas ROMs no workspace; isso não é aprovação da suíte completa.

Ainda faltam 25 TMs no rascunho: Fling, Snowscape, Toxic Spikes, Tailwind, Stealth Rock, Electric/Grassy/Psychic/Misty Terrain, Trick Room, Steel Beam, Gravity, Burning Jealousy, Poltergeist, Lash Out, Misty Explosion, Temper Flare, Supercell Slam, Triple Axel, Coaching, Meteor Beam, Dragon Cheer, Alluring Voice, Psychic Noise e Upper Hand. U-turn, Volt Switch e Flip Turn ainda não efetuam a troca. IA, clima, habilidades, itens, formas, animações e muitas interações modernas não estão integralmente implementados ou testados. A campanha inteira e a migração de todos os saves não foram comprovadas.

### 2. Hook v3 de mochila: investigação histórica separada

A base é a ROM FireRed BR histórica SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`, **não** a Gen 1–9. No ZIP histórico, o builder `scripts/apply_mod_v3.py` e os hex originais montam v3 SHA-256 `348025c13828517f3a4ae03cd9fe963df07fcb12ed087933b0d319d4892215a3`. O builder antigo pode sobrescrever a saída indicada; o resultado é defeituoso e não é uma solução de jogo.

```text
08000a38  01 4b      ldr r3, [pc, #4]
08000a3a  18 47      bx  r3
08000a3c  01 0c eb 08   .word 0x08eb0c01  ; pretendido
08000a40  09 0c 5f 2c   .word 0x2c5f0c09  ; efetivamente lido
```

O veneer original lê `0x08000A40`; `00 4b` carrega o literal pretendido em `0x08000A3C`. O retorno após replay deve ser `0x08000A41` em Thumb, não `0x08000A43`. O payload original também constrói `0x022058B8`, não `0x020258B8`: consertar só veneer e retorno **não** torna o mod funcional. Uma versão histórica em outro branch já tinha `00 4b` no arquivo do site; o hex dentro do ZIP usa `01 4b`. São materiais distintos.

No mGBA 0.10.5, chamada forçada usando o veneer antigo deixou o contador em zero; a versão instrumentada corrigida contou uma chamada, retornou ao sentinela e preservou `0x1234`. Na sessão sintética, já no quarto (grupo 4, mapa 1), um contador de 32 bits em `0x0203FFFC` marcou 360/720/1080/1440 após 60/120/180/240 frames; a ROM sem instrumentação permaneceu em zero. A suíte do diagnóstico passou **4/4** em 31/10. Isso contradiz a hipótese de que o hook só roda na inicialização nesse cenário, mas **não testa o combo**, não prova outros cenários e não valida o mod v3. O endereço do contador era exclusivamente de teste.

## Reprodução segura

O pacote de fontes do Drive não inclui ROMs. Para o motor, obtenha a ROM parcial do próprio Drive autorizado, confira o SHA de entrada e trabalhe em diretório de testes. Use apenas saves sintéticos; preserve um backup separado do save real e não reutilize save states entre versões.

```sh
# Executar na raiz do pacote extraído; substitua os caminhos.
mkdir -p area_teste
sha256sum /caminho/ptbr_gen1-9_complemento_parcial_32mb.gba
python3 scripts/estojo_expandido.py \
  --rom /caminho/ptbr_gen1-9_complemento_parcial_32mb.gba \
  --saida area_teste/estojo_v2.gba
sha256sum area_teste/estojo_v2.gba   # esperado 93dc62e8…c280907
python3 scripts/motor_ampliado.py \
  --rom area_teste/estojo_v2.gba \
  --saida area_teste/motor_v5.gba
sha256sum area_teste/motor_v5.gba   # esperado cf1de0e2…a7a4fc87
MOTOR_TEST_BASE="$PWD/area_teste/estojo_v2.gba" \
MOTOR_TEST_ROM="$PWD/area_teste/motor_v5.gba" \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s tests -p 'test_motor_ampliado*.py' -v
```

Para o diagnóstico v3, forneça a ROM histórica de hash exato e um core libretro mGBA 0.10.5 compatível. A desmontagem automatizada requer Capstone; sem dependências ou variáveis, verifique quais testes foram **pulados**.

```sh
python3 scripts/diagnostico_hook_v3.py --rom /caminho/base_BR.gba --core /caminho/mgba_libretro.so
HOOK_TEST_ROM=/caminho/base_BR.gba MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s tests -p 'test_diagnostico_hook_v3.py' -v
```

O ZIP traz um `gba-re_project (1).zip` **mínimo**, diferente do ZIP histórico integral: apenas o driver Python e os hex/scripts necessários aos testes, preservados byte a byte. A base, o core e os saves não são incluídos. Alguns testes dependem especificamente do formato de estado libretro mGBA 0.10.5.

## Pedido objetivo ao Claude

1. Confira o diagnóstico v3 e examine os bytes e a execução do hook; proponha testes e correções separando fatos de hipóteses. Não conclua que o combo funciona com base no contador.
2. Revise o motor Gen 1–9 e o estojo: fronteiras dos IDs, consumo de TMs/HMs, buffers de nomes longos, cancelamento, Quest Log, backup/recarga e fluxos anormais/Pokedude/link. Indique erros demonstráveis, endereços, riscos e testes reproduzíveis.
3. Organize as 25 TMs e as omissões restantes por mecanismos compartilhados, sem marcar como concluídas. Sugira uma implementação incremental que preserve encontros, eventos e treino.
4. Registre o resultado em VYK-57 ou retorne um diff/texto e logs verificáveis. Antes de qualquer mudança real, validar SHA da base, executar em cópias e declarar o que foi e o que não foi testado.

Quando houver avanços, atualizar este repasse no Drive e o acompanhamento no Linear, registrando data, hash, alterações, evidências, falhas e pendências. Não há compartilhamento público nem atualização automática implícita.
