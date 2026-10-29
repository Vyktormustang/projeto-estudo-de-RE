import React, { useMemo, useRef, useState } from 'react';
import { Chess, Color, Move, PieceSymbol, Square } from 'chess.js';
import { ChessBoardThemeId } from '../../engine/types';
import { CHESS_BOARD_THEMES, ChessPieceSvg } from './ChessPiecesSvg';

export interface BoardArrowSpec {
  from: Square;
  to: Square;
  color: string;
  opacity?: number;
}

export interface SquareBadgeOverlay {
  square: Square;
  symbol: string;
  bgColor: string;
}

interface ChessBoardViewProps {
  fen: string;
  orientation: Color;
  themeId: ChessBoardThemeId;
  interactive: boolean;
  allowedMoveColor?: Color | 'both';
  allowPremove?: boolean;
  premove?: { from: Square; to: Square; promotion?: PieceSymbol } | null;
  onSetPremove?: (pm: { from: Square; to: Square; promotion?: PieceSymbol } | null) => void;
  lastMove?: { from: Square; to: Square } | null;
  engineArrows?: BoardArrowSpec[];
  hintSquares?: { from: Square; to: Square } | null;
  badgeOverlay?: SquareBadgeOverlay | null;
  showEvalBar?: boolean;
  evalWhiteCp?: number;
  mateInMoves?: number | null;
  arrowDrawMode?: boolean;
  hideCoordinates?: boolean;
  hidePieces?: boolean;
  onSquareTap?: (sq: Square) => void;
  onMove: (from: Square, to: Square, promotion?: PieceSymbol) => boolean;
}

const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'] as const;
const RANKS_WHITE = [8, 7, 6, 5, 4, 3, 2, 1] as const;
const RANKS_BLACK = [1, 2, 3, 4, 5, 6, 7, 8] as const;

function squareToGridCoords(sq: Square, orientation: Color): { col: number; row: number } {
  const f = sq.charCodeAt(0) - 97;
  const r = parseInt(sq[1], 10); // 1..8
  if (orientation === 'w') {
    return { col: f, row: 8 - r };
  }
  return { col: 7 - f, row: r - 1 };
}

function gridCoordsToSquare(col: number, row: number, orientation: Color): Square | null {
  if (col < 0 || col > 7 || row < 0 || row > 7) return null;
  if (orientation === 'w') {
    return `${FILES[col]}${8 - row}` as Square;
  }
  return `${FILES[7 - col]}${row + 1}` as Square;
}

export const ChessBoardView: React.FC<ChessBoardViewProps> = ({
  fen,
  orientation,
  themeId,
  interactive,
  allowedMoveColor = 'both',
  allowPremove = false,
  premove = null,
  onSetPremove,
  lastMove = null,
  engineArrows = [],
  hintSquares = null,
  badgeOverlay = null,
  showEvalBar = false,
  evalWhiteCp = 0,
  mateInMoves = null,
  arrowDrawMode = false,
  hideCoordinates = false,
  hidePieces = false,
  onSquareTap,
  onMove,
}) => {
  const theme = CHESS_BOARD_THEMES[themeId] ?? CHESS_BOARD_THEMES.CHESS_VERDE;
  const boardRef = useRef<HTMLDivElement | null>(null);

  const [selectedSq, setSelectedSq] = useState<Square | null>(null);
  const [pendingPromotion, setPendingPromotion] = useState<{
    from: Square;
    to: Square;
    color: Color;
    isPremove: boolean;
  } | null>(null);

  const [userArrows, setUserArrows] = useState<BoardArrowSpec[]>([]);
  const [markedSquares, setMarkedSquares] = useState<Set<Square>>(new Set());

  const [dragState, setDragState] = useState<{
    from: Square;
    piece: { color: Color; type: PieceSymbol };
    startX: number;
    startY: number;
    currX: number;
    currY: number;
    isDragging: boolean;
    hoverSq: Square | null;
    isPremoveDrag: boolean;
  } | null>(null);

  const [arrowDraft, setArrowDraft] = useState<{
    from: Square;
    to: Square;
  } | null>(null);

  // Reseta selecao e setas temporarias ao mudar a posicao FEN
  React.useEffect(() => {
    setSelectedSq(null);
    setPendingPromotion(null);
    setUserArrows([]);
    setMarkedSquares(new Set());
  }, [fen]);

  const chess = useMemo(() => {
    try {
      return new Chess(fen);
    } catch {
      return new Chess();
    }
  }, [fen]);

  const legalMoves = useMemo<Move[]>(() => chess.moves({ verbose: true }), [chess]);
  const turn = chess.turn();
  const inCheck = chess.inCheck();

  const checkedKingSq = useMemo<Square | null>(() => {
    if (!inCheck) return null;
    const b = chess.board();
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const cell = b[r][c];
        if (cell && cell.type === 'k' && cell.color === turn) {
          return cell.square;
        }
      }
    }
    return null;
  }, [chess, inCheck, turn]);

  const canDirectMoveColor = (pieceColor: Color): boolean => {
    if (!interactive) return false;
    if (pieceColor !== turn) return false;
    return allowedMoveColor === 'both' || allowedMoveColor === pieceColor;
  };

  const canPremoveColor = (pieceColor: Color): boolean => {
    if (!interactive || !allowPremove || !onSetPremove) return false;
    if (allowedMoveColor === 'both') return false;
    return pieceColor === allowedMoveColor && turn !== allowedMoveColor;
  };

  const legalTargetsForSelected = useMemo(() => {
    const map = new Map<Square, { isCapture: boolean; isPromotion: boolean }>();
    if (!selectedSq) return map;
    const piece = chess.get(selectedSq);
    if (!piece) return map;

    if (canDirectMoveColor(piece.color)) {
      for (const m of legalMoves) {
        if (m.from === selectedSq) {
          map.set(m.to, {
            isCapture: Boolean(m.captured),
            isPromotion: Boolean(m.promotion),
          });
        }
      }
    } else if (canPremoveColor(piece.color)) {
      // Para pre-lance estilo Chess.com, permite casas geometricamente alcancaveis pela peca
      const f0 = selectedSq.charCodeAt(0) - 97;
      const r0 = parseInt(selectedSq[1], 10);
      for (let f = 0; f < 8; f++) {
        for (let r = 1; r <= 8; r++) {
          if (f === f0 && r === r0) continue;
          const df = Math.abs(f - f0);
          const dr = Math.abs(r - r0);
          let ok = false;
          if (piece.type === 'n') ok = (df === 1 && dr === 2) || (df === 2 && dr === 1);
          else if (piece.type === 'b') ok = df === dr;
          else if (piece.type === 'r') ok = df === 0 || dr === 0;
          else if (piece.type === 'q') ok = df === dr || df === 0 || dr === 0;
          else if (piece.type === 'k') ok = (df <= 1 && dr <= 1) || (dr === 0 && df === 2);
          else if (piece.type === 'p') {
            const dir = piece.color === 'w' ? 1 : -1;
            const startRank = piece.color === 'w' ? 2 : 7;
            ok =
              (df <= 1 && r - r0 === dir) ||
              (df === 0 && r0 === startRank && r - r0 === 2 * dir);
          }
          if (ok) {
            const sq = `${FILES[f]}${r}` as Square;
            const isPromo =
              piece.type === 'p' &&
              ((piece.color === 'w' && r === 8) || (piece.color === 'b' && r === 1));
            map.set(sq, {
              isCapture: Boolean(chess.get(sq)),
              isPromotion: isPromo,
            });
          }
        }
      }
    }
    return map;
  }, [selectedSq, chess, legalMoves, interactive, allowedMoveColor, allowPremove, turn]);

  const clientPointToSquare = (clientX: number, clientY: number): Square | null => {
    const el = boardRef.current;
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return null;
    const col = Math.floor(((clientX - rect.left) / rect.width) * 8);
    const row = Math.floor(((clientY - rect.top) / rect.height) * 8);
    return gridCoordsToSquare(col, row, orientation);
  };

  const attemptCommitMove = (from: Square, to: Square, isPremoveAttempt: boolean) => {
    const piece = chess.get(from);
    if (!piece) return;

    const targetRank = parseInt(to[1], 10);
    const needsPromo =
      piece.type === 'p' &&
      ((piece.color === 'w' && targetRank === 8) ||
        (piece.color === 'b' && targetRank === 1));

    if (isPremoveAttempt) {
      if (needsPromo) {
        setPendingPromotion({ from, to, color: piece.color, isPremove: true });
      } else {
        onSetPremove?.({ from, to });
      }
      setSelectedSq(null);
      return;
    }

    const matchingLegal = legalMoves.filter((m) => m.from === from && m.to === to);
    if (matchingLegal.length === 0) return;

    if (needsPromo && matchingLegal.some((m) => m.promotion)) {
      setPendingPromotion({ from, to, color: piece.color, isPremove: false });
      setSelectedSq(null);
      return;
    }

    onMove(from, to);
    setSelectedSq(null);
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (pendingPromotion) return;
    const sq = clientPointToSquare(e.clientX, e.clientY);
    if (!sq) return;

    if (onSquareTap && e.button !== 2 && !arrowDrawMode) {
      e.preventDefault();
      onSquareTap(sq);
      return;
    }

    // Botao direito OU modo seta tatica: inicia desenho de seta/circulo
    if (e.button === 2 || arrowDrawMode) {
      e.preventDefault();
      e.currentTarget.setPointerCapture(e.pointerId);
      setArrowDraft({ from: sq, to: sq });
      return;
    }

    // Limpa marcacoes taticas ao clicar com botao esquerdo
    if (userArrows.length > 0 || markedSquares.size > 0) {
      setUserArrows([]);
      setMarkedSquares(new Set());
    }

    // Se ha pre-lance ativo e clicou sem peca propria, cancela o pre-lance
    if (premove && onSetPremove && !selectedSq) {
      const clickedPiece = chess.get(sq);
      if (!clickedPiece || !canPremoveColor(clickedPiece.color)) {
        onSetPremove(null);
        return;
      }
    }

    // Se ja havia casa selecionada e clicou num destino legal/premove, executa!
    if (selectedSq && sq !== selectedSq && legalTargetsForSelected.has(sq)) {
      const selPiece = chess.get(selectedSq);
      const isPm = selPiece ? canPremoveColor(selPiece.color) : false;
      attemptCommitMove(selectedSq, sq, isPm);
      return;
    }

    const piece = chess.get(sq);
    if (piece && (canDirectMoveColor(piece.color) || canPremoveColor(piece.color))) {
      e.currentTarget.setPointerCapture(e.pointerId);
      const isPm = canPremoveColor(piece.color);
      setSelectedSq(selectedSq === sq ? null : sq);
      setDragState({
        from: sq,
        piece: { color: piece.color, type: piece.type },
        startX: e.clientX,
        startY: e.clientY,
        currX: e.clientX,
        currY: e.clientY,
        isDragging: false,
        hoverSq: sq,
        isPremoveDrag: isPm,
      });
    } else {
      setSelectedSq(null);
    }
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (arrowDraft) {
      const sq = clientPointToSquare(e.clientX, e.clientY);
      if (sq && sq !== arrowDraft.to) {
        setArrowDraft({ ...arrowDraft, to: sq });
      }
      return;
    }
    if (!dragState) return;
    const dist = Math.hypot(e.clientX - dragState.startX, e.clientY - dragState.startY);
    const isDragging = dragState.isDragging || dist > 6;
    const hoverSq = clientPointToSquare(e.clientX, e.clientY);
    if (isDragging && selectedSq !== dragState.from) {
      setSelectedSq(dragState.from);
    }
    setDragState({
      ...dragState,
      currX: e.clientX,
      currY: e.clientY,
      isDragging,
      hoverSq,
    });
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (arrowDraft) {
      const endSq = clientPointToSquare(e.clientX, e.clientY) ?? arrowDraft.to;
      if (endSq === arrowDraft.from) {
        setMarkedSquares((prev) => {
          const next = new Set(prev);
          if (next.has(endSq)) next.delete(endSq);
          else next.add(endSq);
          return next;
        });
      } else {
        setUserArrows((prev) => {
          const exists = prev.some(
            (a) => a.from === arrowDraft.from && a.to === endSq,
          );
          if (exists) {
            return prev.filter(
              (a) => !(a.from === arrowDraft.from && a.to === endSq),
            );
          }
          return [
            ...prev,
            {
              from: arrowDraft.from,
              to: endSq,
              color: 'rgba(245, 166, 35, 0.86)',
            },
          ];
        });
      }
      setArrowDraft(null);
      return;
    }

    if (!dragState) return;
    const targetSq = clientPointToSquare(e.clientX, e.clientY);
    const wasDrag = dragState.isDragging;
    const fromSq = dragState.from;
    const isPm = dragState.isPremoveDrag;
    setDragState(null);

    if (wasDrag && targetSq && targetSq !== fromSq) {
      if (legalTargetsForSelected.has(targetSq)) {
        attemptCommitMove(fromSq, targetSq, isPm);
      }
    }
  };

  // Calculo da Barra de Avaliacao (perspectiva de quem esta embaixo!)
  const whitePct = useMemo(() => {
    if (mateInMoves !== null) {
      return mateInMoves > 0 ? 98 : 2;
    }
    // Sigmoide estilo Chess.com / Lichess
    const clamped = Math.max(-1200, Math.min(1200, evalWhiteCp));
    const p = 50 + 50 * (2 / (1 + Math.exp(-0.0038 * clamped)) - 1);
    return Math.max(4, Math.min(96, p));
  }, [evalWhiteCp, mateInMoves]);

  const evalLabel = useMemo(() => {
    if (mateInMoves !== null) {
      return `M${Math.abs(mateInMoves)}`;
    }
    const pawns = Math.abs(evalWhiteCp) / 100;
    return pawns >= 10 ? pawns.toFixed(0) : pawns.toFixed(1);
  }, [evalWhiteCp, mateInMoves]);

  const whiteAdvantage = mateInMoves !== null ? mateInMoves > 0 : evalWhiteCp >= 0;

  const ranks = orientation === 'w' ? RANKS_WHITE : RANKS_BLACK;
  const files = orientation === 'w' ? FILES : [...FILES].reverse();

  const allArrows: BoardArrowSpec[] = [
    ...engineArrows,
    ...userArrows,
    ...(arrowDraft && arrowDraft.from !== arrowDraft.to
      ? [
          {
            from: arrowDraft.from,
            to: arrowDraft.to,
            color: 'rgba(245, 166, 35, 0.62)',
          },
        ]
      : []),
  ];

  // Posicao relativa do cursor para peca flutuante durante drag
  const floatingStyle = useMemo<React.CSSProperties | null>(() => {
    if (!dragState || !dragState.isDragging || !boardRef.current) return null;
    const rect = boardRef.current.getBoundingClientRect();
    const sqSize = rect.width / 8;
    return {
      position: 'fixed',
      left: dragState.currX - sqSize * 0.58,
      top: dragState.currY - sqSize * 0.68,
      width: sqSize * 1.16,
      height: sqSize * 1.16,
      pointerEvents: 'none',
      zIndex: 80,
    };
  }, [dragState]);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'stretch',
        gap: '6px',
        width: '100%',
        maxWidth: '470px',
        margin: '0 auto',
        userSelect: 'none',
      }}
    >
      {/* Barra de Avaliacao Ao Vivo Estilo Chess.com */}
      {showEvalBar && (
        <div
          aria-label={`Avaliação ${whiteAdvantage ? '+' : '-'}${evalLabel}`}
          style={{
            width: '22px',
            flexShrink: 0,
            borderRadius: '5px',
            overflow: 'hidden',
            background: '#262421',
            border: '1px solid rgba(255,255,255,0.14)',
            position: 'relative',
            display: 'flex',
            flexDirection: orientation === 'w' ? 'column-reverse' : 'column',
          }}
        >
          <div
            style={{
              width: '100%',
              height: `${whitePct}%`,
              background: '#f1f3f5',
              transition: 'height 280ms cubic-bezier(0.22, 1, 0.36, 1)',
            }}
          />
          <span
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              textAlign: 'center',
              fontSize: '9px',
              fontWeight: 800,
              letterSpacing: '-0.3px',
              ...(whiteAdvantage
                ? orientation === 'w'
                  ? { bottom: '4px', color: '#1b1b1b' }
                  : { top: '4px', color: '#1b1b1b' }
                : orientation === 'w'
                  ? { top: '4px', color: '#f1f3f5' }
                  : { bottom: '4px', color: '#f1f3f5' }),
            }}
          >
            {evalLabel}
          </span>
        </div>
      )}

      {/* Tabuleiro 8x8 Principal */}
      <div
        ref={boardRef}
        onContextMenu={(e) => e.preventDefault()}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={() => {
          setDragState(null);
          setArrowDraft(null);
        }}
        style={{
          position: 'relative',
          flex: 1,
          aspectRatio: '1 / 1',
          borderRadius: '6px',
          overflow: 'hidden',
          boxShadow: '0 8px 26px rgba(0, 0, 0, 0.45)',
          touchAction: 'none',
          display: 'grid',
          gridTemplateColumns: 'repeat(8, 1fr)',
          gridTemplateRows: 'repeat(8, 1fr)',
          cursor: interactive ? 'pointer' : 'default',
        }}
      >
        {ranks.map((rank, rIdx) =>
          files.map((file, cIdx) => {
            const sq = `${file}${rank}` as Square;
            const fileIdx = FILES.indexOf(file);
            const isLight = (fileIdx + rank) % 2 !== 0;
            const isLastMove =
              lastMove?.from === sq || lastMove?.to === sq;
            const isSelected = selectedSq === sq;
            const isPremoveSq =
              premove?.from === sq || premove?.to === sq;
            const isHintSq =
              hintSquares?.from === sq || hintSquares?.to === sq;
            const isMarked = markedSquares.has(sq);
            const isHoverTarget =
              dragState?.isDragging &&
              dragState.hoverSq === sq &&
              legalTargetsForSelected.has(sq);

            let bg = isLight ? theme.lightSq : theme.darkSq;
            if (isLastMove) {
              bg = isLight ? theme.lastMoveLight : theme.lastMoveDark;
            }
            if (isSelected) {
              bg = theme.selectedSq;
            }
            if (isPremoveSq) {
              bg = isLight ? '#f48c84' : '#d6534b';
            }

            const piece = chess.get(sq);
            const legalInfo = legalTargetsForSelected.get(sq);
            const hideDraggedPiece =
              dragState?.isDragging && dragState.from === sq;

            const badgeHere =
              badgeOverlay && badgeOverlay.square === sq ? badgeOverlay : null;

            return (
              <div
                key={sq}
                data-square={sq}
                style={{
                  position: 'relative',
                  background: bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxSizing: 'border-box',
                  boxShadow: isHoverTarget
                    ? 'inset 0 0 0 3px rgba(255,255,255,0.85)'
                    : isHintSq
                      ? 'inset 0 0 0 3.5px #22d3ee'
                      : isMarked
                        ? 'inset 0 0 0 3.5px rgba(235, 77, 75, 0.85)'
                        : undefined,
                }}
              >
                {/* Brilho Radial Vermelho de Xeque */}
                {checkedKingSq === sq && (
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background:
                        'radial-gradient(circle, rgba(239,68,68,0.92) 0%, rgba(185,28,28,0.62) 55%, rgba(185,28,28,0) 78%)',
                      pointerEvents: 'none',
                    }}
                  />
                )}

                {/* Coordenada de Fileira (1..8) na borda esquerda */}
                {cIdx === 0 && !hideCoordinates && (
                  <span
                    style={{
                      position: 'absolute',
                      top: '2px',
                      left: '3px',
                      fontSize: '10px',
                      fontWeight: 800,
                      lineHeight: 1,
                      color: isLight ? theme.coordOnLight : theme.coordOnDark,
                      pointerEvents: 'none',
                    }}
                  >
                    {rank}
                  </span>
                )}

                {/* Coordenada de Coluna (a..h) na borda inferior */}
                {rIdx === 7 && !hideCoordinates && (
                  <span
                    style={{
                      position: 'absolute',
                      bottom: '2px',
                      right: '3px',
                      fontSize: '10px',
                      fontWeight: 800,
                      lineHeight: 1,
                      color: isLight ? theme.coordOnLight : theme.coordOnDark,
                      pointerEvents: 'none',
                    }}
                  >
                    {file}
                  </span>
                )}

                {/* Peca */}
                {piece && !hidePieces && !hideDraggedPiece && (
                  <div style={{ width: '88%', height: '88%', zIndex: 2 }}>
                    <ChessPieceSvg color={piece.color} type={piece.type} />
                  </div>
                )}

                {/* Indicador de Lance Legal (Ponto ou Anel de Captura Estilo Chess.com) */}
                {legalInfo && (
                  <div
                    style={{
                      position: 'absolute',
                      width: legalInfo.isCapture ? '84%' : '30%',
                      height: legalInfo.isCapture ? '84%' : '30%',
                      borderRadius: '50%',
                      background: legalInfo.isCapture
                        ? 'transparent'
                        : 'rgba(0, 0, 0, 0.22)',
                      border: legalInfo.isCapture
                        ? '4.5px solid rgba(0, 0, 0, 0.24)'
                        : undefined,
                      boxSizing: 'border-box',
                      pointerEvents: 'none',
                      zIndex: 3,
                    }}
                  />
                )}

                {/* Selo de Classificacao da Revisao de Partida (!!, !, ★, ?!, ?, ??) */}
                {badgeHere && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '-2px',
                      right: '-2px',
                      minWidth: '18px',
                      height: '18px',
                      padding: '0 3px',
                      borderRadius: '999px',
                      background: badgeHere.bgColor,
                      color: '#fff',
                      fontSize: '10px',
                      fontWeight: 900,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 2px 5px rgba(0,0,0,0.45)',
                      border: '1.5px solid #ffffff',
                      zIndex: 6,
                      pointerEvents: 'none',
                    }}
                  >
                    {badgeHere.symbol}
                  </div>
                )}
              </div>
            );
          }),
        )}

        {/* Camada Vetorial SVG de Setas Taticas e do Treinador */}
        {allArrows.length > 0 && (
          <svg
            viewBox="0 0 800 800"
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              zIndex: 5,
            }}
          >
            {allArrows.map((arr, idx) => {
              const p1 = squareToGridCoords(arr.from, orientation);
              const p2 = squareToGridCoords(arr.to, orientation);
              const x1 = p1.col * 100 + 50;
              const y1 = p1.row * 100 + 50;
              const x2 = p2.col * 100 + 50;
              const y2 = p2.row * 100 + 50;
              const dx = x2 - x1;
              const dy = y2 - y1;
              const len = Math.hypot(dx, dy);
              if (len < 10) return null;
              const ux = dx / len;
              const uy = dy / len;
              const px = -uy;
              const py = ux;

              // Recua a ponta para o centro da casa de destino com cabeca triangular limpa
              const startX = x1 + ux * 18;
              const startY = y1 + uy * 18;
              const headTipX = x2 - ux * 8;
              const headTipY = y2 - uy * 8;
              const neckX = headTipX - ux * 34;
              const neckY = headTipY - uy * 34;
              const halfShaft = 10.5;
              const halfHead = 25;

              const points = [
                `${startX + px * halfShaft},${startY + py * halfShaft}`,
                `${neckX + px * halfShaft},${neckY + py * halfShaft}`,
                `${neckX + px * halfHead},${neckY + py * halfHead}`,
                `${headTipX},${headTipY}`,
                `${neckX - px * halfHead},${neckY - py * halfHead}`,
                `${neckX - px * halfShaft},${neckY - py * halfShaft}`,
                `${startX - px * halfShaft},${startY - py * halfShaft}`,
              ].join(' ');

              return (
                <polygon
                  key={`${arr.from}-${arr.to}-${idx}`}
                  points={points}
                  fill={arr.color}
                  opacity={arr.opacity ?? 0.86}
                />
              );
            })}
          </svg>
        )}

        {/* Seletor Oficial de Promocao / Subpromocao (Dama, Torre, Bispo, Cavalo) */}
        {pendingPromotion && (
          <div
            onPointerDown={(e) => e.stopPropagation()}
            style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(10, 12, 16, 0.72)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              zIndex: 30,
              padding: '12px',
            }}
          >
            <div
              style={{
                background: '#1c1f26',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '12px',
                padding: '12px 14px',
                boxShadow: '0 12px 30px rgba(0,0,0,0.65)',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  fontSize: '12px',
                  fontWeight: 800,
                  color: '#f8fafc',
                  marginBottom: '10px',
                  letterSpacing: '0.4px',
                }}
              >
                ESCOLHA A PEÇA DE PROMOÇÃO
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {(
                  [
                    { p: 'q', label: 'Dama' },
                    { p: 'n', label: 'Cavalo' },
                    { p: 'r', label: 'Torre' },
                    { p: 'b', label: 'Bispo' },
                  ] as const
                ).map(({ p, label }) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => {
                      const { from, to, isPremove } = pendingPromotion;
                      setPendingPromotion(null);
                      if (isPremove) {
                        onSetPremove?.({ from, to, promotion: p });
                      } else {
                        onMove(from, to, p);
                      }
                    }}
                    style={{
                      width: '62px',
                      padding: '6px 4px',
                      borderRadius: '10px',
                      border: '1px solid rgba(255,255,255,0.18)',
                      background: '#ebecd0',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '3px',
                    }}
                  >
                    <div style={{ width: '42px', height: '42px' }}>
                      <ChessPieceSvg color={pendingPromotion.color} type={p} />
                    </div>
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 800,
                        color: '#1e293b',
                      }}
                    >
                      {label}
                    </span>
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => setPendingPromotion(null)}
                style={{
                  marginTop: '10px',
                  padding: '4px 12px',
                  borderRadius: '6px',
                  border: '1px solid rgba(255,255,255,0.16)',
                  background: 'transparent',
                  color: '#cbd5e1',
                  fontSize: '11px',
                  cursor: 'pointer',
                }}
              >
                Cancelar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Peca Flutuante Durante Arraste (Drag-and-Drop) */}
      {floatingStyle && dragState && (
        <div style={floatingStyle}>
          <ChessPieceSvg
            color={dragState.piece.color}
            type={dragState.piece.type}
          />
        </div>
      )}
    </div>
  );
};
