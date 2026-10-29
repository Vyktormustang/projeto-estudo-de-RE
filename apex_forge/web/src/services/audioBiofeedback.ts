let sharedCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  try {
    if (typeof window === 'undefined') return null;
    const Ctor =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return null;
    if (!sharedCtx) {
      sharedCtx = new Ctor();
    }
    if (sharedCtx.state === 'suspended') {
      void sharedCtx.resume();
    }
    return sharedCtx;
  } catch {
    return null;
  }
}

/** Guia acustico suave para protocolos autonomicos (Coerencia 0.1 Hz, Suspiro Fisiologico Stanford 2023 e Box 4-4-4-4) */
export function playBreathPhaseCue(phase: 'INHALE' | 'EXHALE' | 'TOP_SIGH' | 'HOLD'): void {
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';

    if (phase === 'INHALE') {
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.exponentialRampToValueAtTime(329.63, now + 0.45);
    } else if (phase === 'TOP_SIGH') {
      osc.frequency.setValueAtTime(349.23, now);
      osc.frequency.exponentialRampToValueAtTime(440.0, now + 0.25);
    } else if (phase === 'HOLD') {
      osc.frequency.setValueAtTime(293.66, now);
      osc.frequency.setValueAtTime(293.66, now + 0.3);
    } else {
      osc.frequency.setValueAtTime(293.66, now);
      osc.frequency.exponentialRampToValueAtTime(196.0, now + 0.55);
    }

    gain.gain.setValueAtTime(0.001, now);
    gain.gain.exponentialRampToValueAtTime(0.06, now + 0.08);
    gain.gain.exponentialRampToValueAtTime(0.0008, now + 0.65);

    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.7);
  } catch {
    // Silencioso caso audio esteja bloqueado
  }
}

/** Alerta tatico de fim de descanso ou conclusao de bloco */
export function playTacticalChime(kind: 'REST_DONE' | 'VICTORY'): void {
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const notes = kind === 'VICTORY' ? [440, 554.37, 659.25, 880] : [523.25, 659.25];
    notes.forEach((freq, idx) => {
      const start = ctx.currentTime + idx * 0.11;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, start);
      gain.gain.setValueAtTime(0.001, start);
      gain.gain.exponentialRampToValueAtTime(0.09, start + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.0008, start + 0.32);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(start);
      osc.stop(start + 0.35);
    });
  } catch {
    // Ignorado
  }
}

export type ChessSoundKind =
  | 'MOVE'
  | 'CAPTURE'
  | 'CHECK'
  | 'CASTLE'
  | 'PROMOTE'
  | 'GAME_END'
  | 'PUZZLE_OK'
  | 'ILLEGAL';

/** Sintese acustica percussiva estilo tabuleiro de madeira / Chess.com (100% offline WebAudio) */
export function playChessSound(kind: ChessSoundKind): void {
  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const now = ctx.currentTime;

    if (kind === 'MOVE' || kind === 'CAPTURE' || kind === 'CASTLE') {
      const playTap = (offset: number, fStart: number, fEnd: number, peak: number) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = kind === 'CAPTURE' ? 'sawtooth' : 'triangle';
        osc.frequency.setValueAtTime(fStart, now + offset);
        osc.frequency.exponentialRampToValueAtTime(fEnd, now + offset + 0.055);
        gain.gain.setValueAtTime(0.001, now + offset);
        gain.gain.linearRampToValueAtTime(peak, now + offset + 0.006);
        gain.gain.exponentialRampToValueAtTime(0.0008, now + offset + 0.075);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + offset);
        osc.stop(now + offset + 0.08);
      };

      if (kind === 'MOVE') {
        playTap(0, 290, 115, 0.14);
      } else if (kind === 'CAPTURE') {
        playTap(0, 420, 95, 0.18);
        playTap(0.02, 210, 75, 0.12);
      } else {
        playTap(0, 290, 115, 0.13);
        playTap(0.085, 330, 130, 0.13);
      }
      return;
    }

    if (kind === 'CHECK') {
      [587.33, 880].forEach((freq, i) => {
        const t = now + i * 0.06;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.001, t);
        gain.gain.exponentialRampToValueAtTime(0.11, t + 0.015);
        gain.gain.exponentialRampToValueAtTime(0.0008, t + 0.18);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t);
        osc.stop(t + 0.2);
      });
      return;
    }

    if (kind === 'PROMOTE' || kind === 'PUZZLE_OK' || kind === 'GAME_END') {
      const seq =
        kind === 'GAME_END' ? [392, 523.25, 659.25] : [523.25, 659.25, 783.99];
      seq.forEach((freq, i) => {
        const t = now + i * 0.08;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.001, t);
        gain.gain.exponentialRampToValueAtTime(0.1, t + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0008, t + 0.24);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t);
        osc.stop(t + 0.26);
      });
      return;
    }

    // ILLEGAL
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(140, now);
    gain.gain.setValueAtTime(0.06, now);
    gain.gain.exponentialRampToValueAtTime(0.0008, now + 0.12);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.13);
  } catch {
    // Ignorado
  }
}

