export interface ChessPuzzleSpec {
  id: string;
  titlePt: string;
  themeTagPt: string;
  rating: number;
  fen: string;
  solutionLan: string[]; // Sequencia alternada: [lanceJogador1, respostaAdversario1, lanceJogador2, ...]
  coachExplanationPt: string;
}

export const CHESS_PUZZLES_CATALOG: ChessPuzzleSpec[] = [
  {
    id: 'puz_01_corredor_basico',
    titlePt: 'Mate do Corredor Clássico',
    themeTagPt: 'Mate em 1 • 8ª Fileira',
    rating: 480,
    fen: '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1',
    solutionLan: ['d1d8'],
    coachExplanationPt:
      'Os próprios peões pretos em f7, g7 e h7 trancam o Rei na 8ª fileira: Td8# é xeque-mate imediato!',
  },
  {
    id: 'puz_02_beijo_da_dama',
    titlePt: 'O Beijo da Dama em f7',
    themeTagPt: 'Mate em 1 • Ataque Direto',
    rating: 520,
    fen: 'r1bqk2r/pppp1ppp/2n2n2/2b1p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
    solutionLan: ['h5f7'],
    coachExplanationPt:
      'A Dama em f7 é protegida pelo Bispo de c4, dando mate sem que nenhuma peça preta possa capturar em f7!',
  },
  {
    id: 'puz_03_mate_arabe',
    titlePt: 'Geometria Árabe (Torre + Cavalo)',
    themeTagPt: 'Mate em 1 • Coordenação',
    rating: 620,
    fen: '7k/7p/5N2/8/8/6R1/5PPP/6K1 w - - 0 1',
    solutionLan: ['g3g8'],
    coachExplanationPt:
      'Padrão imortal de Torre + Cavalo: o Cavalo em f6 controla h7 E protege a Torre em g8 (Tg8#)!',
  },
  {
    id: 'puz_04_garfo_real_cavalo',
    titlePt: 'Garfo Real Triplo em c7',
    themeTagPt: 'Garfo de Cavalo • Ganho de Torre',
    rating: 740,
    fen: 'r3k2r/ppp2ppp/8/3N4/8/8/PPP2PPP/R3K2R w KQkq - 0 1',
    solutionLan: ['d5c7', 'e8d7', 'c7a8'],
    coachExplanationPt:
      'Cc7+ aplica xeque ao Rei em e8 e ataca simultaneamente a Torre em a8!',
  },
  {
    id: 'puz_05_espeto_torre',
    titlePt: 'Espeto Linear na Coluna d (Raio-X)',
    themeTagPt: 'Espeto • Final Tático',
    rating: 820,
    fen: '3q4/8/8/3k4/8/8/5PPP/1R4K1 w - - 0 1',
    solutionLan: ['b1d1', 'd5e5', 'd1d8'],
    coachExplanationPt:
      'Td1+ aplica xeque direto ao Rei exposto em d5; quando o Rei sai da coluna, a Torre captura a Dama em d8 atrás dele!',
  },
  {
    id: 'puz_06_punicao_primeira_fileira',
    titlePt: 'Vigilância na 1ª Fileira (Jogam as Pretas)',
    themeTagPt: 'Mate em 1 • Tática Reversa',
    rating: 880,
    fen: '6k1/5p1p/6p1/8/3q4/8/1B3PPP/6K1 b - - 0 1',
    solutionLan: ['d4d1'],
    coachExplanationPt:
      'Sempre olhe a segurança da 1ª fileira! Dd1# pune imediatamente a falta de casa de respiro do Rei branco.',
  },
  {
    id: 'puz_07_mate_damiano',
    titlePt: 'Cunha Clássica de Damiano (1512)',
    themeTagPt: 'Mate em 1 • Peão Cunha',
    rating: 940,
    fen: '5rk1/5p1p/5PpQ/8/8/8/6PP/6K1 w - - 0 1',
    solutionLan: ['h6g7'],
    coachExplanationPt:
      'O peão cunha em f6 controla g7 e bloqueia a defesa lateral: Dg7# é mate imediato!',
  },
  {
    id: 'puz_08_mate_epaulette',
    titlePt: 'Mate das Dragonas (Epaulette Mate)',
    themeTagPt: 'Mate em 1 • Simetria',
    rating: 1010,
    fen: '3rkr2/8/4Q3/8/8/8/6PP/4R1K1 w - - 0 1',
    solutionLan: ['e6e7'],
    coachExplanationPt:
      'As duas Torres pretas em d8 e f8 trancam as casas de fuga laterais do próprio Rei: De7#!',
  },
  {
    id: 'puz_09_dobradinha_coluna_d',
    titlePt: 'Bateria de Torres na Coluna Aberta',
    themeTagPt: 'Mate em 2 • Domínio Vertical',
    rating: 1080,
    fen: 'r5k1/5ppp/8/8/8/8/3R1PPP/3R2K1 w - - 0 1',
    solutionLan: ['d2d8', 'a8d8', 'd1d8'],
    coachExplanationPt:
      'Torres dobradas multiplicam seu poder: 1.Td8+! força 1...Txd8 e a segunda Torre sela 2.Txd8#!',
  },
  {
    id: 'puz_10_dama_sobrecarregada',
    titlePt: 'O Colapso da Dama Sobrecarregada',
    themeTagPt: 'Mate em 2 • Sobrecarga Defensiva',
    rating: 1180,
    fen: '6k1/1p3ppp/2q5/8/8/2Q5/5PPP/4R1K1 w - - 0 1',
    solutionLan: ['c3c6', 'b7c6', 'e1e8'],
    coachExplanationPt:
      'A Dama preta em c6 ameaçava Dxg2#, mas também era a única guardiã da casa e8! 1.Dxc6! bxc6 2.Te8#!',
  },
  {
    id: 'puz_11_mate_anastasia_puro',
    titlePt: 'Execução na Oitava com Cavalo de Apoio',
    themeTagPt: 'Mate em 2 • Cravada Final',
    rating: 1240,
    fen: '5rk1/4Nppp/8/8/8/8/5PPP/2R3K1 w - - 0 1',
    solutionLan: ['c1c8', 'g8h8', 'c8f8'],
    coachExplanationPt:
      'Com o Cavalo em e7 guardando g8 e atacando f8, 1.Tc8! deixa as Pretas sem defesa contra 2.Txf8#!',
  },
  {
    id: 'puz_12_subpromocao_cavalo',
    titlePt: 'A Joia da Subpromoção para Cavalo!',
    themeTagPt: 'Subpromoção • Garfo Real',
    rating: 1340,
    fen: '8/2q1P3/5k2/8/8/8/6PP/6K1 w - - 0 1',
    solutionLan: ['e7e8n', 'f6e7', 'e8c7'],
    coachExplanationPt:
      'Se promover para Dama (e8=D), a partida segue com Damas no tabuleiro; mas e8=C+!! aplica garfo real imediato em f6 e na Dama em c7!',
  },
  {
    id: 'puz_13_mate_opera_morphy',
    titlePt: 'O Imortal Mate da Ópera de Paul Morphy (1858)',
    themeTagPt: 'Mate em 2 • Sacrifício Histórico',
    rating: 1420,
    fen: '4kb1r/p2n1ppp/4q3/4p1B1/4P3/1Q6/PPP2PPP/2KR4 w k - 0 16',
    solutionLan: ['b3b8', 'd7b8', 'd1d8'],
    coachExplanationPt:
      'Paris, 1858: Morphy sacrifica a Dama com Db8+!! para desviar o Cavalo de d7 e cravar Td8# apoiada pelo Bispo em g5!',
  },
  {
    id: 'puz_14_mate_sufocado_philidor',
    titlePt: 'Legado de Philidor (Mate Sufocado em 2)',
    themeTagPt: 'Mate em 2 • Sacrifício de Dama',
    rating: 1490,
    fen: 'r4r1k/6pp/7N/8/2Q5/8/6PP/6K1 w - - 0 1',
    solutionLan: ['c4g8', 'f8g8', 'h6f7'],
    coachExplanationPt:
      'Dg8+!! força Txg8 (pois Rxg8 é proibido pelo Cavalo em h6!), trancando o próprio Rei para Cf7# mate sufocado!',
  },
  {
    id: 'puz_15_mate_boden',
    titlePt: 'As Tesouras de Boden (Dois Bispos)',
    themeTagPt: 'Mate em 2 • Cruzamento Diagonal',
    rating: 1580,
    fen: '2kr3r/pp1n1ppp/2p5/8/4P3/2Q3B1/PPP2PPP/2KR1B1R w - - 0 1',
    solutionLan: ['c3c6', 'b7c6', 'f1a6'],
    coachExplanationPt:
      'Dc6+!! abre a linha fatal c6-a6 enquanto o Bispo de g3 corta b8 e d6: 1...bxc6 2.Ba6#!',
  },
  {
    id: 'puz_16_xeque_duplo_letal',
    titlePt: 'O Poder Irresistível do Xeque Duplo',
    themeTagPt: 'Mate em 1 • Xeque Duplo Descoberto',
    rating: 1640,
    fen: '6rk/8/6Pp/4N3/8/8/1Q5P/6K1 w - - 0 1',
    solutionLan: ['e5f7'],
    coachExplanationPt:
      'Contra xeque duplo (Dama em b2 revelada na grande diagonal + Cavalo saltando para f7!), nenhuma peça pode bloquear ou capturar os dois atacantes: Cf7#!',
  },
  {
    id: 'puz_17_promocao_com_liquidacao',
    titlePt: 'Liquidação na Oitava & Coroação',
    themeTagPt: 'Final Tático • Promoção',
    rating: 1710,
    fen: '3r2k1/1P3p1p/6p1/8/8/8/5PPP/3R2K1 w - - 0 1',
    solutionLan: ['d1d8', 'g8g7', 'b7b8q'],
    coachExplanationPt:
      'Txd8+ elimina a única peça que vigiava b8 com xeque, garantindo a promoção limpa b8=D no lance seguinte!',
  },
  {
    id: 'puz_18_anastasia_sacrificio_dama',
    titlePt: 'Mate de Anastasia com Sacrifício de Dama!',
    themeTagPt: 'Mate em 2 • Sacrifício em h7',
    rating: 1840,
    fen: '5r1k/4Nppp/8/8/8/5R1Q/6PP/6K1 w - - 0 1',
    solutionLan: ['h3h7', 'h8h7', 'f3h3'],
    coachExplanationPt:
      'Dh7+!! destrói o escudo do Rei (1...Rxh7 forçado) e Th3# fecha a rede de Anastasia guiada pelo Cavalo em e7!',
  },
  {
    id: 'puz_19_mate_en_passant',
    titlePt: 'Raridade FIDE: Xeque-Mate En Passant!',
    themeTagPt: 'Mate em 1 • Captura En Passant',
    rating: 1910,
    fen: '6rb/3N2kp/6pp/5pP1/2B5/6K1/8/8 w - f6 0 1',
    solutionLan: ['g5f6'],
    coachExplanationPt:
      'As Pretas acabaram de jogar ...f7-f5! A captura especial 1.gxf6 e.p.# dá xeque direto em g7 protegido pelo Cavalo de d7 enquanto Bc4 e Cd7 trancam todas as casas de fuga!',
  },
  {
    id: 'puz_20_moinho_philidor_4_lances',
    titlePt: 'A Sinfonia Completa de Philidor (Mate em 4!)',
    themeTagPt: 'Mate em 4 • Obra-Prima Clássica',
    rating: 1990,
    fen: 'r4r1k/6pp/8/4N3/8/1Q6/6PP/6K1 w - - 0 1',
    solutionLan: ['e5f7', 'h8g8', 'f7h6', 'g8h8', 'b3g8', 'f8g8', 'h6f7'],
    coachExplanationPt:
      'A sequência mais bela da tática clássica: 1.Cf7+ Rg8 2.Ch6+ (xeque duplo!) Rh8 3.Dg8+!! Txg8 4.Cf7# mate sufocado!',
  },
  {
    id: 'puz_21_contra_ataque_pretas',
    titlePt: 'Contra-Golpe Letal das Pretas (Jogam as Pretas)',
    themeTagPt: 'Mate em 2 • Sacrifício em h2',
    rating: 2050,
    fen: '6k1/5ppp/5r2/8/8/7q/4nPPP/3R3K b - - 0 1',
    solutionLan: ['h3h2', 'h1h2', 'f6h6'],
    coachExplanationPt:
      'Espelho negro de Anastasia: 1...Dxh2+!! 2.Rxh2 Th6# com o Cavalo preto em e2 trancando g1 e g3!',
  },
  {
    id: 'puz_22_mate_de_legal',
    titlePt: 'A Armadilha Imortal de Sire de Légal (1750)',
    themeTagPt: 'Mate em 2 • Rede de Cavalos & Bispo',
    rating: 2120,
    fen: 'r2qkbnr/ppp2p1p/2np2p1/4N3/2B1P3/2N5/PPPP1PPP/R1BbK2R w KQkq - 0 6',
    solutionLan: ['c4f7', 'e8e7', 'c3d5'],
    coachExplanationPt:
      'Após as Pretas capturarem gananciosamente a Dama em d1, 1.Bxf7+! Re7 (única!) e 2.Cd5# fecha o lendário Mate de Légal no centro do tabuleiro!',
  },
  {
    id: 'puz_23_porcos_cegos_nimzowitsch',
    titlePt: 'Os "Porcos Cegos" de Nimzowitsch na 7ª Fileira',
    themeTagPt: 'Mate em 2 • Dupla de Torres na 7ª',
    rating: 2180,
    fen: '5r1k/4pRRp/8/8/8/8/6PP/6K1 w - - 0 1',
    solutionLan: ['g7h7', 'h8g8', 'f7g7'],
    coachExplanationPt:
      'Duas Torres conectadas na 7ª fileira são implacáveis: 1.Txh7+! Rg8 2.Tfg7# (a própria Torre preta em f8 bloqueia a fuga do Rei)!',
  },
  {
    id: 'puz_24_coroacao_com_mate',
    titlePt: 'Atração na Oitava & Coroação com Mate!',
    themeTagPt: 'Mate em 2 • Sacrifício + Promoção',
    rating: 2260,
    fen: '3r2k1/1P3ppp/8/8/8/8/5PPP/2R3K1 w - - 0 1',
    solutionLan: ['c1c8', 'd8c8', 'b7c8q'],
    coachExplanationPt:
      '1.Tc8!! crava e atrai a Torre de d8: após 1...Txc8 forçado, o peão captura promovendo com xeque-mate imediato: 2.bxc8=D#!',
  },
  {
    id: 'puz_25_mate_de_boden',
    titlePt: 'O Mate de Boden (1853)',
    themeTagPt: 'Sacrifício de Dama • Bispos Cruzados',
    rating: 1420,
    fen: '2kr1b1r/pp1npppp/2p5/8/4PB2/2Q5/PPP2PPP/R3KB1R w KQ - 0 1',
    solutionLan: ['c3c6', 'b7c6', 'f1a6'],
    coachExplanationPt:
      '1.Dxc6+!! destrói o escudo de b7: após 1...bxc6 forçado, 2.Ba6# tranca o Rei preto em c8 numa tesoura mortal dos dois Bispos!',
  },
  {
    id: 'puz_26_mate_de_anastasia',
    titlePt: 'O Mate de Anastasia',
    themeTagPt: 'Sacrifício em h7 • Cavalo + Torre',
    rating: 1520,
    fen: 'r4r1k/pp2Nppp/2p5/7Q/8/6R1/PPP2PPP/6K1 w - - 0 1',
    solutionLan: ['h5h7', 'h8h7', 'g3h3'],
    coachExplanationPt:
      'O Cavalo em e7 controla g8 e g6 enquanto o próprio peão preto em g7 tranca a fuga: 1.Dxh7+! Rxh7 2.Th3# é mate puro!',
  },
  {
    id: 'puz_27_subpromocao_cavalo',
    titlePt: 'Subpromoção Brilhante para Cavalo',
    themeTagPt: 'Subpromoção (=C+) • Garfo Real',
    rating: 1740,
    fen: '8/2q1P3/5k2/8/8/8/6PP/7K w - - 0 1',
    solutionLan: ['e7e8n', 'f6f7', 'e8c7'],
    coachExplanationPt:
      'Promover para Dama (1.e8=D??) levaria mate imediato com 1...Dc1+! 2.De1 Dxe1#! A subpromoção 1.e8=C+!! dá xeque E ganha a Dama em c7!',
  },
  {
    id: 'puz_28_sacrificio_torre_mayet',
    titlePt: 'Abertura da Coluna h (Padrão Mayet)',
    themeTagPt: 'Sacrifício de Torre • Mate Linear',
    rating: 1580,
    fen: 'r4r1k/7p/5Pp1/8/8/1B5R/5PK1/5R2 w - - 0 1',
    solutionLan: ['h3h7', 'h8h7', 'f1h1'],
    coachExplanationPt:
      'O Bispo em b3 proíbe Rg8 e o peão em f6 proíbe Rg7: 1.Txh7+! Rxh7 abre a coluna para a segunda Torre dar mate com 2.Th1#!',
  },
  {
    id: 'puz_29_imortal_reti_tartakower',
    titlePt: 'A Imortal de Réti–Tartakower (Viena, 1910)',
    themeTagPt: 'Sacrifício de Dama • Xeque Duplo',
    rating: 1960,
    fen: 'rnb1kb1r/pp3ppp/2p5/4q3/4n3/3Q4/PPPB1PPP/2KR1BNR w kq - 0 9',
    solutionLan: ['d3d8', 'e8d8', 'd2g5', 'd8e8', 'd1d8'],
    coachExplanationPt:
      'Uma das combinações mais célebres da história: 1.Dd8+!! Rxd8 atrai o Rei para um xeque duplo devastador 2.Bg5+! Re8 3.Td8#!',
  },
  {
    id: 'puz_30_ruptura_tres_peoes',
    titlePt: 'A Ruptura Clássica de 3 contra 3 Peões',
    themeTagPt: 'Final de Peões • Ruptura Dupla',
    rating: 1920,
    fen: '8/ppp5/8/PPP5/8/7k/7P/6K1 w - - 0 1',
    solutionLan: ['b5b6', 'c7b6', 'a5b6', 'a7b6', 'c5c6'],
    coachExplanationPt:
      'Template essencial de finais: 1.b6!! estilhaça a barreira! Após 1...cxb6, 2.a6! bxa6 libera a estrada para 3.c6! coroando imparavelmente!',
  },
  {
    id: 'puz_31_mate_gancho_sacrificio',
    titlePt: 'Mate Gancho com Atração na 8ª',
    themeTagPt: 'Mate Gancho • Sacrifício de Dama',
    rating: 1640,
    fen: '3r1k2/2q1ppp1/5N2/4P3/3Q4/8/6PP/3R2K1 w - - 0 1',
    solutionLan: ['d4d8', 'c7d8', 'd1d8'],
    coachExplanationPt:
      '1.Dxd8+! Dxd8 elimina o defensor da casa d8 e permite 2.Txd8# — o clássico Mate Gancho onde o Cavalo em f6 (protegido por e5) tranca g8!',
  },
  {
    id: 'puz_32_zwischenzug_real',
    titlePt: 'O Lance Intermediário (Zwischenzug)',
    themeTagPt: 'Zwischenzug • Xeque Intermediário',
    rating: 1820,
    fen: '2q2rk1/5ppp/8/3N4/8/8/5PPP/2Q2RK1 w - - 0 1',
    solutionLan: ['d5e7', 'g8h8', 'e7c8'],
    coachExplanationPt:
      'Trocar Damas direto (1.Dxc8? Txc8) empataria o material. O lance intermediário 1.Ce7+!! dá garfo com xeque e captura a Dama em c8 mantendo a sua!',
  },
  {
    id: 'puz_33_cravada_cruzada_f7',
    titlePt: 'Explosão sobre Cravada Absoluta em f7',
    themeTagPt: 'Cravada Cruzada • Mate do Corredor',
    rating: 1880,
    fen: 'r1b2rk1/ppp2ppp/8/7Q/2B5/8/PPP2PPP/4R1K1 w - - 0 1',
    solutionLan: ['h5f7', 'f8f7', 'e1e8'],
    coachExplanationPt:
      '1.Dxf7+!! Txf7 parece entregar a Dama, mas a Torre em f7 fica absolutamente cravada pelo Bispo de c4 — incapaz de voltar para cobrir 2.Te8#!',
  },
  {
    id: 'puz_34_descoberto_real_h7',
    titlePt: 'Demolição em h7 com Descoberto sobre a Dama',
    themeTagPt: 'Ataque Descoberto • Ganho de Dama',
    rating: 1380,
    fen: 'r1b2rk1/ppp2ppp/8/8/3q4/3B4/PPP2PPP/R2Q1RK1 w - - 0 1',
    solutionLan: ['d3h7', 'g8h7', 'd1d4'],
    coachExplanationPt:
      'A Dama preta em d4 está solta na frente da Dama branca em d1! 1.Bxh7+! obriga a resposta ao xeque e 2.Dxd4 captura a Dama inteira!',
  },
  {
    id: 'puz_35_desocupacao_diagonal',
    titlePt: 'Sacrifício de Desocupação de Diagonal (Clearance)',
    themeTagPt: 'Desocupação • Bateria Dama-Bispo',
    rating: 2080,
    fen: '2r3k1/ppp2p1p/6pB/4R3/3Q4/8/PPP2PPP/6K1 w - - 0 1',
    solutionLan: ['e5e8', 'c8e8', 'd4g7'],
    coachExplanationPt:
      'A própria Torre branca em e5 bloqueia a diagonal mortal d4-g7! 1.Te8+!! desocupa e5 com xeque, forçando 1...Txe8 e liberando 2.Dg7#!',
  },
  {
    id: 'puz_36_mate_de_damiano',
    titlePt: 'O Sacrifício Imortal de Damiano (1512)',
    themeTagPt: 'Padrão de Damiano • Sacrifício de Dama',
    rating: 2240,
    fen: 'r5rk/ppp4p/5PpQ/8/5R2/8/PPP3PP/6K1 w - - 0 1',
    solutionLan: ['h6h7', 'h8h7', 'f4h4'],
    coachExplanationPt:
      'Com a própria Torre preta trancando g8 e o peão branco em f6 vigiando g7, 1.Dxh7+!! Rxh7 atrai o Rei para a coluna aberta onde 2.Th4# é mate!',
  },
];

/**
 * Seleciona deterministicamente o Problema Diario (Daily Puzzle) a partir da data ISO YYYY-MM-DD.
 */
export function getDailyPuzzleForDate(dateISO: string): ChessPuzzleSpec {
  let hash = 2166136261;
  for (let i = 0; i < dateISO.length; i++) {
    hash ^= dateISO.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  const idx = Math.abs(hash) % CHESS_PUZZLES_CATALOG.length;
  return CHESS_PUZZLES_CATALOG[idx];
}

/**
 * Seleciona o proximo problema tatico próximo ao Rating de Problemas do usuario, priorizando nao-resolvidos.
 */
export function pickNextRatedPuzzle(
  userPuzzleElo: number,
  solvedIds: string[],
  excludeId?: string,
): ChessPuzzleSpec {
  const solvedSet = new Set(solvedIds);
  const candidates = CHESS_PUZZLES_CATALOG.filter((p) => p.id !== excludeId);
  const unsolved = candidates.filter((p) => !solvedSet.has(p.id));
  const pool = unsolved.length > 0 ? unsolved : candidates;

  return [...pool].sort(
    (a, b) =>
      Math.abs(a.rating - userPuzzleElo) - Math.abs(b.rating - userPuzzleElo),
  )[0];
}

