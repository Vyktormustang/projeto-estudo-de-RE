@ Encontro estático ("como os lendários") — script ÚNICO para todas as
@ espécies inobtíveis. A espécie vem do template do objeto tocado
@ (trainer_sight_or_berry_tree_id), lida pelo special EstaticoPrepararEncontro,
@ que também preenche STR_VAR_1 e o nível. Padrão copiado do MEWTWO.

EventScript_EncontroEstatico::
	goto_if_questlog EventScript_ReleaseEnd
	special QuestLog_CutRecording
	lock
	faceplayer
	special EstaticoPrepararEncontro
	goto_if_eq VAR_RESULT, FALSE, EventScript_EncontroEstatico_Fim
	waitse
	playmoncry VAR_0x8004, CRY_MODE_ENCOUNTER
	message Text_EncontroEstatico
	waitmessage
	waitmoncry
	delay 20
	playbgm MUS_ENCOUNTER_GYM_LEADER, 0
	waitbuttonpress
	special EstaticoCriarInimigo
	setflag FLAG_SYS_SPECIAL_WILD_BATTLE
	special StartLegendaryBattle
	waitstate
	clearflag FLAG_SYS_SPECIAL_WILD_BATTLE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_CAUGHT, EventScript_EncontroEstatico_Capturado
EventScript_EncontroEstatico_Fim::
	release
	end

EventScript_EncontroEstatico_Capturado::
	removeobject VAR_LAST_TALKED
	release
	end

Text_EncontroEstatico::
	.string "O {STR_VAR_1} selvagem está te\n"
	.string "encarando!$"
