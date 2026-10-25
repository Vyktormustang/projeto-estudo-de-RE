# Tradução PT-BR — Onda 7 (correção pós-entrega): fontes de texto que os
# dicts anteriores não cobriam porque ficam FORA de data/maps/*/text.inc e
# data/text/*.inc:
#   - data/event_scripts.s ........ enfermeira do CENTRO POKéMON, lojas,
#                                   elevadores, PC do OAK, CARD KEY etc.
#   - data/scripts/cable_club.inc . atendentes do 2º andar do Centro
#   - data/scripts/field_moves.inc  CUT/ROCK SMASH/STRENGTH/WATERFALL/DIVE
#   - data/scripts/repel.inc ...... fim do efeito do REPEL
# O aplicar_traducao.py passou a varrer esses arquivos nesta onda.
# Ficam em inglês: onomatopeias (Gyaoo!, Mew!), golpes/itens (CUT, REPEL,
# CARD KEY...), nomes de sistemas (UNION ROOM, BERRY CRUSH, POKéMON JUMP),
# e o Mystery Event (inacessível em jogo normal).
#
# Formato: label -> [(linha, sep)], sep: "n"=\n, "p"=\p, "l"=\l, "$"=fim.

TRADUCOES = {
    # ---------- data/event_scripts.s ----------
    "Text_WouldYouLikeToMixRecords": [
        ("Quer misturar registros com", "n"),
        ("outros TREINADORES?", "$")],
    "Text_WeHopeToSeeYouAgain2": [
        ("Esperamos vê-lo novamente!", "$")],
    "Text_WelcomeTradeCenter": [
        ("Bem-vindo ao CENTRO DE TROCAS do", "n"),
        ("POKéMON CABLE CLUB.", "$")],
    "Text_WelcomeColosseum": [
        ("Bem-vindo ao COLISEU do", "n"),
        ("POKéMON CABLE CLUB.", "$")],
    "Text_WelcomeTimeCapsule": [
        ("Bem-vindo à CÁPSULA DO TEMPO do", "n"),
        ("POKéMON CABLE CLUB.", "$")],
    "Text_PleaseComeAgain": [
        ("Volte sempre!", "$")],
    "Text_HavingDiscountSaleToday": [
        ("Bem-vindo!", "p"),
        ("Hoje temos uma liquidação!", "$")],
    "Text_PlayerWhatCanIDoForYou": [
        ("{PLAYER}{KUN}, bem-vindo!", "p"),
        ("O que posso fazer por você?", "$")],
    "Text_WantWhichFloor": [
        ("Qual andar você deseja?", "$")],
    "Text_BagItemCanBeRegistered": [
        ("Um item da BOLSA pode ser", "n"),
        ("registrado no SELECT para", "l"),
        ("facilitar o uso.", "$")],
    "Text_PlayerBootedUpPC": [
        ("{PLAYER} ligou o PC.", "$")],
    "Text_GiveNicknameToReceivedMon": [
        ("Quer dar um apelido ao", "n"),
        ("{STR_VAR_2} que você recebeu?", "$")],
    "gText_PkmnFainted3": [
        ("{STR_VAR_1} desmaiou…", "p"),
        ("", "$")],
    "Text_WelcomeWantToHealPkmn": [
        ("Bem-vindo ao nosso CENTRO POKéMON!", "p"),
        ("Quer que eu cure os seus POKéMON", "n"),
        ("e os deixe perfeitos de novo?", "$")],
    "Text_TakeYourPkmnForFewSeconds": [
        ("Certo, vou cuidar dos seus POKéMON", "n"),
        ("por alguns segundos.", "$")],
    "Text_WeHopeToSeeYouAgain": [
        ("Esperamos vê-lo novamente!", "$")],
    "Text_RestoredPkmnToFullHealth": [
        ("Obrigada pela espera.", "n"),
        ("Restauramos a saúde dos seus", "l"),
        ("POKéMON por completo.", "$")],
    "Text_WirelessClubUndergoingAdjustments": [
        ("Sinto muito.", "n"),
        ("O POKéMON WIRELESS CLUB está", "l"),
        ("em manutenção no momento.", "$")],
    "Text_AppearsToBeUndergoingAdjustments": [
        ("Parece estar em manutenção…", "$")],
    "Text_HandedOverItem": [
        ("{PLAYER} entregou:", "n"),
        ("{STR_VAR_1}.", "$")],
    "Text_GiveNicknameToThisMon": [
        ("Quer dar um apelido a este", "n"),
        ("{STR_VAR_1}?", "$")],
    "Text_CardKeyOpenedDoor": [
        ("Bingo!", "n"),
        ("A CARD KEY abriu a porta!", "$")],
    "Text_ItNeedsCardKey": [
        ("Não!", "n"),
        ("Precisa de uma CARD KEY!", "$")],
    "Text_AccessedProfOaksPC": [
        ("Acessou o PC do PROF. OAK…", "p"),
        ("Acessou o Sistema de Avaliação", "n"),
        ("da POKéDEX…", "$")],
    "Text_HavePokedexRated": [
        ("Quer ter a sua POKéDEX", "n"),
        ("avaliada?", "$")],
    "Text_ClosedLinkToProfOaksPC": [
        ("Conexão com o PC do PROF. OAK", "n"),
        ("encerrada.", "$")],
    "Text_VoiceRangOutDontRunAway": [
        ("A voz de alguém ecoou:", "n"),
        ("“Não fuja!”", "$")],
    "Text_TheDoorIsOpen": [
        ("A porta está aberta…", "$")],
    "Text_MonFlewAway": [
        ("O {STR_VAR_1} voou para longe!", "$")],
    "Text_FoundTMHMContainsMove": [
        ("{PLAYER} encontrou: {STR_VAR_2}!", "n"),
        ("Contém {STR_VAR_1}.", "$")],
    "Text_MoveCanOnlyBeLearnedOnce": [
        ("Este golpe só pode ser aprendido", "n"),
        ("uma vez. Tudo bem?", "$")],

    # ---------- data/scripts/repel.inc ----------
    "Text_RepelWoreOff": [
        ("O efeito do REPEL acabou…", "$")],

    # ---------- data/scripts/field_moves.inc ----------
    "Text_CutTreeDown": [
        ("Parece que esta árvore pode ser", "n"),
        ("cortada!", "p"),
        ("Quer usar CUT?", "$")],
    "Text_MonUsedMove": [
        ("{STR_VAR_1} usou {STR_VAR_2}!", "$")],
    "Text_TreeCanBeCutDown": [
        ("Parece que esta árvore pode ser", "n"),
        ("cortada!", "$")],
    "Text_UseRockSmash": [
        ("Esta rocha parece quebrável.", "n"),
        ("Quer usar ROCK SMASH?", "$")],
    "Text_MonMaySmashRock": [
        ("É uma rocha robusta, mas um POKéMON", "n"),
        ("talvez consiga quebrá-la.", "$")],
    "Text_UseStrength": [
        ("É uma pedra enorme, mas um POKéMON", "n"),
        ("talvez consiga empurrá-la.", "p"),
        ("Quer usar STRENGTH?", "$")],
    "Text_MonUsedStrengthCanMoveBoulders": [
        ("{STR_VAR_1} usou STRENGTH!", "p"),
        ("A força de {STR_VAR_1} tornou", "n"),
        ("possível mover pedras enormes!", "$")],
    "Text_MonMayPushBoulder": [
        ("É uma pedra enorme, mas um POKéMON", "n"),
        ("talvez consiga empurrá-la.", "$")],
    "Text_StrengthMadeMovingBouldersPossible": [
        ("STRENGTH tornou possível mover", "n"),
        ("pedras enormes.", "$")],
    "Text_WallOfWaterCrashingDown": [
        ("Uma parede de água desaba com", "n"),
        ("um rugido poderoso.", "$")],
    "Text_UseWaterfall": [
        ("É uma grande cachoeira.", "n"),
        ("Quer usar WATERFALL?", "$")],
    "Text_MonUsedWaterfall": [
        ("{STR_VAR_1} usou WATERFALL.", "$")],
    "Text_MonMayGoUnderwater": [
        ("O mar é fundo aqui. Um POKéMON", "n"),
        ("talvez consiga mergulhar.", "$")],
    "Text_SeaIsDeepUseDive": [
        ("O mar é fundo aqui.", "n"),
        ("Quer usar DIVE?", "$")],
    "Text_MonUsedDive": [
        ("{STR_VAR_1} usou DIVE.", "$")],
    "Text_MonMaySurface": [
        ("Uma luz desce filtrada lá de cima.", "n"),
        ("Um POKéMON talvez consiga emergir.", "$")],
    "Text_LightFilteringUseDive": [
        ("Uma luz desce filtrada lá de cima.", "n"),
        ("Quer usar DIVE?", "$")],
    "Text_DiveCantBeUsedHere": [
        ("Há um obstáculo logo acima.", "n"),
        ("DIVE não pode ser usado aqui.", "$")],
    "Text_LooksLikeNothingHere": [
        ("Parece que não há nada aqui…", "$")],

    # ---------- data/scripts/cable_club.inc ----------
    "CableClub_Text_WelcomeWhichCableClubService": [
        ('Bem-vindo ao POKéMON CABLE CLUB.', 'p'),
        ('Qual dos nossos serviços você', 'n'),
        ('deseja usar?', '$'),
    ],
    "CableClub_Text_WhichService": [
        ('Qual dos nossos serviços você', 'n'),
        ('deseja usar?', '$'),
    ],
    "CableClub_Text_TradeMonsUsingLinkCable": [
        ('Troque POKéMON com outro jogador', 'n'),
        ('usando um cabo GBA Game Link.', '$'),
    ],
    "CableClub_Text_BattleUsingLinkCable": [
        ('Você pode batalhar com outro', 'n'),
        ('TREINADOR usando um cabo', 'l'),
        ('GBA Game Link.', '$'),
    ],
    "CableClub_Text_NeedTwoMonsForDoubleBattle": [
        ('Para uma BATALHA EM DUPLA, você', 'n'),
        ('precisa de pelo menos dois POKéMON.', '$'),
    ],
    "CableClub_Text_NeedTwoMonsToTrade": [
        ('Para trocar, você precisa de pelo', 'n'),
        ('menos dois POKéMON com você.', '$'),
    ],
    "CableClub_Text_CantTradeEnigmaBerry": [
        ('Um POKéMON segurando a BERRY', 'n'),
        ('{STR_VAR_1} não pode ser trocado.', '$'),
    ],
    "CableClub_Text_PleaseWaitBCancel": [
        ('Aguarde, por favor.', 'n'),
        ('… … Botão B: Cancelar', '$'),
    ],
    "CableClub_Text_WhenAllPlayersReadyAConfirmBCancel": [
        ('Quando todos estiverem prontos…', 'n'),
        ('Botão A: Confirmar', 'l'),
        ('Botão B: Cancelar', '$'),
    ],
    "CableClub_Text_StartLinkWithXPlayersAConfirmBCancel": [
        ('Iniciar link com {STR_VAR_1}', 'n'),
        ('jogadores.', 'l'),
        ('Botão A: Confirmar', 'l'),
        ('Botão B: Cancelar', '$'),
    ],
    "CableClub_Text_AwaitingLinkupBCancel": [
        ('Aguardando conexão…', 'n'),
        ('… … Botão B: Cancelar', '$'),
    ],
    "CableClub_Text_PleaseEnter": [
        ('Pode entrar.', '$'),
    ],
    "CableClub_Text_DirectYouToYourRoom": [
        ('Vou levá-lo à sua sala agora.', '$'),
    ],
    "CableClub_Text_SomeoneIsNotReadyToLink": [
        ('Alguém não está pronto para o link.', 'p'),
        ('Volte depois que todos tiverem', 'n'),
        ('feito os preparativos.', '$'),
    ],
    "CableClub_Text_LinkErrorPleaseReset": [
        ('Desculpe, houve um erro de link…', 'n'),
        ('Reinicie e tente de novo.', '$'),
    ],
    "CableClub_Text_PlayersMadeDifferentSelections": [
        ('Os parceiros de link parecem ter', 'n'),
        ('feito seleções diferentes.', '$'),
    ],
    "CableClub_Text_PleaseVisitAgain": [
        ('Volte a nos visitar!', '$'),
    ],
    "CableClub_Text_IncorrectNumberOfParticipants": [
        ('O número de participantes está', 'n'),
        ('incorreto.', '$'),
    ],
    "CableClub_Text_CantSingleBattleWithXPlayers": [
        ('O modo BATALHA SIMPLES não pode ser', 'n'),
        ('jogado por {STR_VAR_1} jogadores.', '$'),
    ],
    "CableClub_Text_CantDoubleBattleWithXPlayers": [
        ('O modo BATALHA EM DUPLA não pode', 'n'),
        ('ser jogado por {STR_VAR_1} jogadores.', '$'),
    ],
    "CableClub_Text_NeedFourPlayers": [
        ('São necessários quatro jogadores', 'n'),
        ('para este modo de batalha.', '$'),
    ],
    "CableClub_Text_PleaseConfirmNumberAndRestart": [
        ('Confirme o número de jogadores', 'n'),
        ('e comece de novo.', '$'),
    ],
    "Text_TerminateLinkIfYouLeaveRoom": [
        ('O link será encerrado se você', 'n'),
        ('sair da sala. Tudo bem?', '$'),
    ],
    "Text_TerminateLinkConfirmation": [
        ('Encerrando o link…', 'n'),
        ('Você será acompanhado para fora', 'l'),
        ('da sala. Aguarde.', '$'),
    ],
    "Text_TrainerTooBusyToNotice": [
        ('Este TREINADOR está ocupado demais', 'n'),
        ('para notar…', '$'),
    ],
    "Text_LookedAtPlayersTrainerCard": [
        ('Olha só! Deu para ver o CARTÃO DE', 'n'),
        ('TREINADOR de {STR_VAR_1}!', '$'),
    ],
    "Text_LookedAtPlayersTrainerCardColored": [
        ('Olha só! Deu para ver o CARTÃO DE', 'n'),
        ('TREINADOR de {STR_VAR_1}!', 'p'),
        ('É um cartão {STR_VAR_2}!', '$'),
    ],
    "Text_TakeSeatStartBattle": [
        ('Sente-se, por favor, e comece', 'n'),
        ('a sua batalha.', '$'),
    ],
    "Text_TakeSeatStartTrade": [
        ('Sente-se, por favor, e comece', 'n'),
        ('a sua troca.', '$'),
    ],
    "CableClub_Text_TrainerCardDataOverwritten": [
        ('Os dados do CARTÃO DE TREINADOR', 'n'),
        ('serão sobrescritos.', '$'),
    ],
    "CableClub_Text_HopeToSeeYouAgain": [
        ('Espero vê-lo novamente!', '$'),
    ],
    "CableClub_Text_NotSetUpForFarAwayRegion": [
        ('Sinto muitíssimo.', 'p'),
        ('Ainda não estamos preparados para', 'n'),
        ('trocas com TREINADORES de outra', 'l'),
        ('região distante…', '$'),
    ],
    "CableClub_Text_OtherTrainerNotReady": [
        ('O outro TREINADOR não está pronto.', '$'),
    ],
    "CableClub_Text_YouHaveAMonThatCantBeTaken": [
        ('Você tem pelo menos um POKéMON', 'n'),
        ('que não pode ser levado.', '$'),
    ],
    "CableClub_Text_AdapterNotConnected": [
        ('O Adaptador Wireless não está', 'n'),
        ('conectado direito.', '$'),
    ],
    "CableClub_Text_ParticipantsStepUpToCounter": [
        ('Pedimos aos participantes que se', 'n'),
        ('aproximem do balcão de recepção.', '$'),
    ],
    "CableClub_Text_YouMayTradeHere": [
        ('Aqui você pode trocar os seus', 'n'),
        ('POKéMON com outro TREINADOR.', '$'),
    ],
    "CableClub_Text_YouMayBattleHere": [
        ('Aqui você pode batalhar com os', 'n'),
        ('seus amigos.', '$'),
    ],
    "CableClub_Text_CanMakeBerryPowder": [
        ('De dois a cinco TREINADORES podem', 'n'),
        ('fazer BERRY POWDER juntos.', '$'),
    ],
    "CableClub_Text_CancelSelectedItem": [
        ('Cancela o item do MENU', 'n'),
        ('selecionado.', '$'),
    ],
    "CableClub_Text_NeedBerryForBerryCrush": [
        ('Para usar o serviço BERRY CRUSH,', 'n'),
        ('você precisa de ao menos 1 BERRY.', '$'),
    ],
    "CableClub_Text_NeedTwoMonsForUnionRoom": [
        ('Para entrar na UNION ROOM, você', 'n'),
        ('precisa de ao menos dois POKéMON.', '$'),
    ],
    "CableClub_Text_NoEnigmaBerryInUnionRoom": [
        ('POKéMON segurando a BERRY', 'n'),
        ('{STR_VAR_1} não podem entrar', 'l'),
        ('na UNION ROOM.', '$'),
    ],
    "CableClub_Text_UnionRoomAdapterNotConnected": [
        ('Esta é a UNION ROOM do POKéMON', 'n'),
        ('WIRELESS CLUB.', 'p'),
        ('Infelizmente, o seu Adaptador', 'n'),
        ('Wireless não está bem conectado.', 'p'),
        ('Volte outra hora, por favor.', '$'),
    ],
    "Text_PlayerIsPlayingRightNowGoForIt": [
        ('Parece que {STR_VAR_1} está jogando', 'n'),
        ('agora mesmo.', 'l'),
        ('Boa sorte!', '$'),
    ],
    "Text_DescribeWhichGame": [
        ('Posso explicar as regras dos', 'n'),
        ('jogos, se quiser.', 'p'),
        ('Qual jogo devo descrever?', '$'),
    ],
    "Text_PokemonJumpInfo": [
        ('“POKéMON JUMP”', 'p'),
        ('Faça o seu POKéMON pular a corda', 'n'),
        ('de VINE WHIP com o Botão A.', 'p'),
        ('Só POKéMON pequenos, de uns 71 cm', 'n'),
        ('ou menos, podem participar.', 'p'),
        ('POKéMON que só nadam, cavam ou', 'n'),
        ('voam não são bons de salto.', 'p'),
        ('Por isso, esses POKéMON não podem', 'n'),
        ('participar.', 'p'),
        ('Coisas boas acontecem se todos', 'n'),
        ('pularem juntos.', '$'),
    ],
    "Text_DodrioBerryPickingInfo": [
        ('“DODRIO BERRY-PICKING”', 'p'),
        ('Comande as três cabeças do DODRIO', 'n'),
        ('para pegar as BERRIES que caem.', 'p'),
        ('Aperte direita, cima ou esquerda', 'n'),
        ('no {PLUS} Direcional para mover', 'l'),
        ('as cabeças.', 'p'),
        ('Para jogar, você precisa ter', 'n'),
        ('um DODRIO.', '$'),
    ],
    "Text_TalkToManToPlay": [
        ('Se quiser jogar um jogo, fale', 'n'),
        ('com o homem ao meu lado.', '$'),
    ],
    "Text_WelcomeCanYouWait": [
        ('Oi, bem-vindo!', 'n'),
        ('Você pode jogar pelo Sistema de', 'l'),
        ('Comunicação Wireless.', 'p'),
        ('Pode esperar só um pouquinho?', '$'),
    ],
    "CableClub_Text_ComeAgain": [
        ('Tudo bem, volte sempre!', '$'),
    ],
    "Text_AdapterNotConnectedMinigame": [
        ('O Adaptador Wireless não está', 'n'),
        ('conectado.', 'p'),
        ('Volte quando ele estiver ligado!', '$'),
    ],
    "Text_PlayWhichGame": [
        ('Certo, qual jogo você quer', 'n'),
        ('jogar?', '$'),
    ],
    "Text_EnterWhichPokemon": [
        ('Qual POKéMON você gostaria de', 'n'),
        ('inscrever?', '$'),
    ],
    "Text_AllGoodToGo": [
        ('Pronto, está tudo certo.', 'n'),
        ('Não deixe os outros vencerem!', '$'),
    ],
    "EventScript_ExplainPokemonJumpRequirements": [
        ('Parece que você não tem nenhum', 'n'),
        ('POKéMON que possa inscrever…', 'p'),
        ('Quer que eu explique que tipos', 'n'),
        ('de POKéMON podem entrar?', '$'),
    ],
    "Text_ShortJumpingPokemonAllowed": [
        ('O “POKéMON JUMP” é aberto a', 'n'),
        ('POKéMON de uns 71 cm ou menos.', 'p'),
        ('Não entram os POKéMON que não', 'n'),
        ('conseguem pular.', 'p'),
        ('Sabe, POKéMON que só nadam,', 'n'),
        ('cavam ou voam.', 'p'),
        ('É só isso que precisa saber.', '$'),
    ],
    "Text_OnlyDodrioAllowed": [
        ('“DODRIO BERRY-PICKING”…', 'n'),
        ('Bem, o nome já diz tudo.', 'p'),
        ('Você precisa ter um DODRIO para', 'n'),
        ('jogar este jogo.', '$'),
    ],
    "CableClub_Text_WelcomeWhichDirectCornerRoom": [
        ('Bem-vindo ao DIRECT CORNER do', 'n'),
        ('POKéMON WIRELESS CLUB.', 'p'),
        ('Aqui você pode interagir', 'n'),
        ('diretamente com os seus amigos.', 'p'),
        ('Em qual sala você gostaria', 'n'),
        ('de entrar?', '$'),
    ],
    "CableClub_Text_TradePokemon": [
        ('Você gostaria de trocar POKéMON?', '$'),
    ],
    "CableClub_Text_PlayWhichBattleMode": [
        ('Qual modo de batalha você', 'n'),
        ('gostaria de jogar?', '$'),
    ],
    "CableClub_Text_UseBerryCrush": [
        ('Você gostaria de usar o', 'n'),
        ('Sistema BERRY CRUSH?', '$'),
    ],
    "CableClub_Text_ExplainBattleModes": [
        ('Há três modos de batalha.', 'p'),
        ('BATALHA SIMPLES é para dois', 'n'),
        ('TREINADORES com um ou mais', 'l'),
        ('POKéMON cada.', 'p'),
        ('Cada TREINADOR usa um POKéMON', 'n'),
        ('em batalha por vez.', 'p'),
        ('BATALHA EM DUPLA é para dois', 'n'),
        ('TREINADORES com dois ou mais', 'l'),
        ('POKéMON cada.', 'p'),
        ('Cada TREINADOR manda dois POKéMON', 'n'),
        ('à batalha por vez.', 'p'),
        ('BATALHA MULTI é para quatro', 'n'),
        ('TREINADORES com um ou mais', 'l'),
        ('POKéMON cada.', 'p'),
        ('Cada TREINADOR usa um POKéMON', 'n'),
        ('em batalha por vez.', '$'),
    ],
    "CableClub_Text_ChooseGroupLeaderOfTwo": [
        ('Decidam qual de vocês dois', 'n'),
        ('será o LÍDER.', 'p'),
        ('O outro jogador deve então', 'n'),
        ('escolher “JOIN GROUP”.', '$'),
    ],
    "CableClub_Text_ChooseGroupLeaderOfFour": [
        ('Decidam qual de vocês quatro', 'n'),
        ('será o LÍDER DO GRUPO.', 'p'),
        ('Os outros jogadores devem então', 'n'),
        ('escolher “JOIN GROUP”.', '$'),
    ],
    "CableClub_Text_ChooseGroupLeader": [
        ('Decidam qual de vocês', 'n'),
        ('será o LÍDER DO GRUPO.', 'p'),
        ('Os outros jogadores devem então', 'n'),
        ('escolher “JOIN GROUP”.', '$'),
    ],
    "CableClub_Text_WelcomeUnionRoomEnter": [
        ('Bem-vindo à UNION ROOM do', 'n'),
        ('POKéMON WIRELESS CLUB.', 'p'),
        ('Aqui você pode interagir', 'n'),
        ('diretamente com outros', 'l'),
        ('TREINADORES, até desconhecidos.', 'p'),
        ('Você gostaria de entrar na SALA?', '$'),
    ],
    "CableClub_Text_UnionRoomInfo": [
        ('Os TREINADORES na UNION ROOM', 'n'),
        ('serão os jogadores ao seu redor', 'l'),
        ('que também entraram na SALA.', 'p'),
        ('Você pode fazer de tudo aqui,', 'n'),
        ('como trocar cumprimentos.', 'p'),
        ('Pode inscrever dois POKéMON de', 'n'),
        ('até Nv. 30 para um duelo 1x1.', 'p'),
        ('Pode participar de um bate-papo', 'n'),
        ('com duas a cinco pessoas.', 'p'),
        ('Ou pode registrar um POKéMON', 'n'),
        ('para troca.', 'p'),
        ('Você gostaria de entrar na SALA?', '$'),
    ],
    "CableClub_Text_FirstTimeRightThisWay": [
        ('Olá!', 'n'),
        ('Meu nome é TEALA.', 'p'),
        ('Esta deve ser a sua primeira', 'n'),
        ('vez aqui em cima.', 'p'),
        ('Vou mostrar como funciona o', 'n'),
        ('Sistema de Comunicação Wireless.', 'p'),
        ('Primeiro, preciso mostrar este', 'n'),
        ('andar do nosso CENTRO POKéMON.', 'p'),
        ('Por aqui, por favor.', '$'),
    ],
    "CableClub_Text_ExplainWirelessClubFirstTime": [
        ('No último andar há duas salas.', 'p'),
        ('Primeiro, a sala da esquerda.', 'n'),
        ('É a UNION ROOM.', 'p'),
        ('Você pode se conectar com', 'n'),
        ('TREINADORES por perto que também', 'l'),
        ('entraram na UNION ROOM.', 'p'),
        ('Com eles, você pode conversar,', 'n'),
        ('batalhar e trocar.', 'p'),
        ('Segundo, a sala da direita é', 'n'),
        ('o DIRECT CORNER.', 'p'),
        ('Nessa sala você pode trocar ou', 'n'),
        ('batalhar POKéMON com amigos.', 'p'),
        ('Se o Adaptador Wireless não', 'n'),
        ('estiver conectado, ainda dá para', 'l'),
        ('usar um cabo GBA Game Link.', 'p'),
        ('Nesse caso, você deve ir ao', 'n'),
        ('DIRECT CORNER.', 'p'),
        ('Espero que aproveite o Sistema', 'n'),
        ('de Comunicação Wireless.', '$'),
    ],
    "CableClub_Text_AskAboutLinking": [
        ('Olá, {PLAYER}!', 'p'),
        ('Sou eu, TEALA, a atendente do 2º', 'n'),
        ('andar do CENTRO POKéMON.', 'p'),
        ('Há algo que você queira me', 'n'),
        ('perguntar sobre links?', '$'),
    ],
    "CableClub_Text_ExplainWirelessClub": [
        ('Deixe-me explicar como funciona', 'n'),
        ('o POKéMON WIRELESS CLUB.', 'p'),
        ('Neste último andar há duas', 'n'),
        ('salas.', 'p'),
        ('Primeiro, a sala da esquerda.', 'n'),
        ('É a UNION ROOM.', 'p'),
        ('Você pode se conectar com', 'n'),
        ('TREINADORES por perto que também', 'l'),
        ('entraram na UNION ROOM.', 'p'),
        ('Com eles, você pode conversar,', 'n'),
        ('batalhar e trocar.', 'p'),
        ('Segundo, a sala da direita é', 'n'),
        ('o DIRECT CORNER.', 'p'),
        ('Nessa sala você pode trocar ou', 'n'),
        ('batalhar POKéMON com amigos.', 'p'),
        ('Às vezes, pode ser que você não', 'n'),
        ('ache os seus amigos na UNION ROOM', 'l'),
        ('nem no DIRECT CORNER.', 'p'),
        ('Nesse caso, aproxime-se mais', 'n'),
        ('dos seus amigos.', 'p'),
        ('Se o Adaptador Wireless não', 'n'),
        ('estiver conectado, ainda dá para', 'l'),
        ('usar um cabo GBA Game Link.', 'p'),
        ('Nesse caso, você deve ir ao', 'n'),
        ('DIRECT CORNER.', 'p'),
        ('Espero que aproveite o Sistema', 'n'),
        ('de Comunicação Wireless.', '$'),
    ],
    "CableClub_Text_HopeYouEnjoyWirelessSystem": [
        ('Espero que aproveite o Sistema', 'n'),
        ('de Comunicação Wireless.', '$'),
    ],
}
