import React, { useMemo } from 'react';
import { Flame, Activity, Clock } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';

interface StreakTrackerProps {
  bioDayId: string;
  vault: VaultState;
}

export const StreakTracker: React.FC<StreakTrackerProps> = ({ bioDayId, vault }) => {
  const checkIns = vault.checkIns;

  // Calcular streak atual (dias consecutivos terminando em bioDayId)
  const currentStreak = useMemo(() => {
    let count = 0;
    let d = bioDayId;
    while (checkIns[d]) {
      count++;
      d = addDaysToBioDay(d, -1);
    }
    return count;
  }, [checkIns, bioDayId]);

  // Calcular melhor streak de todos os tempos
  const allDates = Object.keys(checkIns).sort();
  const bestStreak = useMemo(() => {
    if (allDates.length === 0) return 0;
    let best = 0;
    let current = 0;
    let prevDate: string | null = null;
    for (const d of allDates) {
      if (prevDate && addDaysToBioDay(prevDate, 1) === d) {
        current++;
      } else {
        current = 1;
      }
      best = Math.max(best, current);
      prevDate = d;
    }
    return best;
  }, [allDates]);

  // Dias dos últimos 30 dias com check-in
  const last30Days = useMemo(() => {
    const days: string[] = [];
    let d = bioDayId;
    for (let i = 0; i < 30; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const checkInDays = last30Days.filter((d) => checkIns[d]);

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--amber)' }}>
            Sequência de Consistência
          </div>
          <h2 className="section-title">Seu Streak</h2>
        </div>
        <Flame size={20} color="var(--amber)" />
      </div>

      {/* Cartões principais */}
      <div className="grid-3" style={{ gap: 10, marginBottom: 14 }}>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--amber)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Atual</div>
          <div className="metric-value" style={{ fontSize: 32, fontWeight: 900, color: 'var(--amber)' }}>{currentStreak}</div>
          <div className="metric-sub">dias consecutivos</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--rose)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Melhor</div>
          <div className="metric-value" style={{ fontSize: 32, fontWeight: 900, color: '#ef4444' }}>{bestStreak}</div>
          <div className="metric-sub">dias consecutivos</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--cyan)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Neste Mês</div>
          <div className="metric-value" style={{ fontSize: 32, fontWeight: 900, color: '#22d3ee' }}>{checkInDays.length}</div>
          <div className="metric-sub">de 30 dias</div>
        </div>
      </div>

      {/* Calendário visual de streak (últimos 30 dias) */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-secondary)', marginBottom: 6 }}>
          {last30Days.map((d, i) => (
            <div key={d} style={{ textAlign: 'center', flex: 1 }}>
              {d.slice(5)}
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          {last30Days.map((d) => {
            const hasCheckIn = Boolean(checkIns[d]);
            const isToday = d === bioDayId;
            return (
              <div
                key={d}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: 2,
                  background: hasCheckIn
                    ? isToday
                      ? 'var(--amber)'
                      : 'var(--emerald)'
                    : 'rgba(255,255,255,0.08)',
                  border: isToday ? '1px solid var(--text-primary)' : 'none',
                }}
              />
            );
          })}
        </div>
      </div>

      {/* Mensagem motivacional */}
      {currentStreak > 0 && (
        <div
          style={{
            padding: '10px 14px',
            background: 'var(--bg-surface)',
            borderRadius: 8,
            border: '1px solid var(--border-subtle)',
            fontSize: 12,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <Activity size={14} color="var(--cyan)" />
            <span className="text-xs font-bold text-slate-300 uppercase">
              {currentStreak >= 7 ? 'Forte!' : currentStreak >= 3 ? 'Bom!' : 'Iniciando!'}
            </span>
          </div>
          <div className="text-[11px] text-slate-500">
            {currentStreak >= 30
              ? 'Um mês inteiro de consistência. Você está no caminho da maestria.'
              : currentStreak >= 7
                ? 'Uma semana inteira sem faltar. Mantenha esse ritmo.'
                : currentStreak >= 1
                  ? 'Você começou bem. Cada dia conta para formar o hábito.'
                  : 'Comece seu primeiro check-in para iniciar a sequência.'}
          </div>
        </div>
      )}
    </div>
  );
};

export default StreakTracker;
