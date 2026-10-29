import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Play, Pause, SkipForward, Timer, RefreshCw, Clock } from 'lucide-react';
import { VaultState } from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface PomodoroTimerProps {
  bioDayId: string;
  vault?: VaultState;
  onUpdateVault?: (next: VaultState) => void;
}

export const PomodoroTimer: React.FC<PomodoroTimerProps> = ({ bioDayId, vault, onUpdateVault }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [isBreak, setIsBreak] = useState(false);
  const [timeLeft, setTimeLeft] = useState(25 * 60); // 25 min em segundos
  const [sessionCount, setSessionCount] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const focusDuration = 25 * 60;
  const breakDuration = 5 * 60;
  const longBreakDuration = 15 * 60;

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const playSound = useCallback(() => {
    try {
      if (!audioRef.current) {
        audioRef.current = new Audio('data:audio/wav;base64,UklGRlAAAAXQV0');
      }
      audioRef.current.play().catch(() => {});
    } catch {}
  }, []);

  const handleStartStop = useCallback(() => {
    if (timeLeft === 0) {
      // Reiniciar sessão
      setTimeLeft(isBreak ? breakDuration : focusDuration);
      setIsRunning(true);
      return;
    }
    setIsRunning((prev) => {
      if (!prev) triggerHaptic('light');
      return !prev;
    });
  }, [isRunning, timeLeft, isBreak]);

  const handleSkip = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    setIsRunning(false);
    if (isBreak) {
      setIsBreak(false);
      setTimeLeft(focusDuration);
    } else {
      setIsBreak(true);
      setSessionCount((prev) => prev + 1);
      setTimeLeft(sessionCount % 4 === 3 ? longBreakDuration : breakDuration);
    }
    triggerHaptic('light');
  }, [isBreak, sessionCount]);

  const handleReset = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    setIsRunning(false);
    setIsBreak(false);
    setTimeLeft(focusDuration);
    setSessionCount(0);
    triggerHaptic('light');
  }, []);

  useEffect(() => {
    if (!isRunning || timeLeft === 0) return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev === 1) {
          playSound();
          if (isBreak) {
            setIsBreak(false);
            setSessionCount((prev) => prev + 1);
            return focusDuration;
          } else {
            setIsBreak(true);
            setSessionCount((prev) => prev + 1);
            return sessionCount % 4 === 3 ? longBreakDuration : breakDuration;
          }
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning, timeLeft, isBreak, sessionCount, playSound]);

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const progress = isBreak
    ? 1 - timeLeft / (sessionCount % 4 === 3 ? longBreakDuration : breakDuration)
    : 1 - timeLeft / focusDuration;
  const label = isBreak ? 'Pausa' : 'Foco';
  const color = isBreak ? '#34d399' : '#ef4444';

  return (
    <div className="card card-rose" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--rose)' }}>
            Temporizador de Foco
          </div>
          <h2 className="section-title">{label} {sessionCount + 1}</h2>
        </div>
        <Timer size={20} style={{ color }} />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
          marginBottom: 14,
        }}
      >
        <div
          style={{
            width: 120,
            height: 120,
            borderRadius: '50%',
            border: `4px solid ${color}20`,
            background: `conic-gradient(${color} ${progress * 100}%, #1e293b 0%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
          }}
        >
          <div style={{ position: 'absolute', inset: 4, borderRadius: '50%', background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center' }}>
              <div className="text-3xl font-bold font-mono text-white">{minutes.toString().padStart(2, '0')}:{seconds.toString().padStart(2, '0')}</div>
              <div className="text-xs text-slate-400 uppercase tracking-wider">{label}</div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 10 }}>
        <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full" style={{ width: `${Math.round(progress * 100)}%`, background: color }}></div>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
          Sessões hoje: {sessionCount}
        </div>
      </div>

      <div className="grid-3" style={{ gap: 6 }}>
        <button
          onClick={handleStartStop}
          className="btn btn-primary btn-block"
        >
          {isRunning ? <Pause size={14} /> : <Play size={14} />} {isRunning ? 'Pausar' : 'Iniciar'}
        </button>
        <button
          onClick={handleSkip}
          className="btn btn-ghost btn-block"
        >
          <SkipForward size={14} /> Pular
        </button>
        <button
          onClick={handleReset}
          className="btn btn-ghost btn-block"
        >
          <RefreshCw size={14} /> Resetar
        </button>
      </div>

      <div style={{ marginTop: 10, padding: '8px 12px', background: 'var(--bg-surface)', borderRadius: 8, fontSize: 11.5, color: 'var(--text-secondary)' }}>
        <Clock size={12} style={{ marginRight: 6 }} />
        25 min foco → 5 min pausa → a cada 4 sessões, pausa longa de 15 min
      </div>
    </div>
  );
};

export default PomodoroTimer;
