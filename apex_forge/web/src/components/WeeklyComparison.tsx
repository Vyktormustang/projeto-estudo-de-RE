import React, { useMemo } from 'react';
import { BarChart2, TrendingUp, TrendingDown, Activity, Clock } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';

interface WeeklyComparisonProps {
  bioDayId: string;
  vault: VaultState;
}

export const WeeklyComparison: React.FC<WeeklyComparisonProps> = ({ bioDayId, vault }) => {
  const currentWeek = useMemo(() => {
    const days: string[] = [];
    let d = bioDayId;
    for (let i = 0; i < 7; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const prevWeek = useMemo(() => {
    const days: string[] = [];
    let d = addDaysToBioDay(bioDayId, -7);
    for (let i = 0; i < 7; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const workoutsCurrent = useMemo(() => {
    return currentWeek.filter((d) => vault.workouts.some((w) => w.bioDayId === d)).length;
  }, [currentWeek, vault.workouts]);

  const workoutsPrev = useMemo(() => {
    return prevWeek.filter((d) => vault.workouts.some((w) => w.bioDayId === d)).length;
  }, [prevWeek, vault.workouts]);

  const checkInsCurrent = useMemo(() => {
    return currentWeek.filter((d) => Boolean(vault.checkIns[d])).length;
  }, [currentWeek, vault.checkIns]);

  const checkInsPrev = useMemo(() => {
    return prevWeek.filter((d) => Boolean(vault.checkIns[d])).length;
  }, [prevWeek, vault.checkIns]);

  const calcReadiness = (days: string[]) => {
    const scores = days.map((d) => {
      const ci = vault.checkIns[d];
      if (!ci) return null;
      return (ci.sleepQuality + ci.energyLevel + ci.mentalCalm + ci.muscularRecovery) / 28;
    }).filter((s): s is number => s !== null);
    return scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
  };

  const readinessCurrent = calcReadiness(currentWeek);
  const readinessPrev = calcReadiness(prevWeek);

  const workoutsDelta = workoutsCurrent - workoutsPrev;
  const checkInsDelta = checkInsCurrent - checkInsPrev;
  const readinessDelta = readinessCurrent - readinessPrev;

  const formatDelta = (val: number, prefix: boolean = true) => {
    if (val > 0) return `+${val}`;
    if (val < 0) return `${val}`;
    return prefix ? '±0' : '0';
  };

  return (
    <div className="card card-cyan" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
            Comparativo Semanal
          </div>
          <h2 className="section-title">Esta Semana vs. Semana Passada</h2>
        </div>
        <BarChart2 size={20} color="var(--cyan)" />
      </div>

      <div className="grid-3" style={{ gap: 10, marginBottom: 14 }}>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--cyan)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Treinos</div>
          <div className="metric-value" style={{ fontSize: 24, fontWeight: 900, color: 'var(--cyan)' }}>{workoutsCurrent}</div>
          <div className="metric-sub" style={{ color: workoutsDelta >= 0 ? 'var(--emerald)' : 'var(--rose)' }}>
            {formatDelta(workoutsDelta)} vs semana passada
          </div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--emerald)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Check-ins</div>
          <div className="metric-value" style={{ fontSize: 24, fontWeight: 900, color: '#34d399' }}>{checkInsCurrent}</div>
          <div className="metric-sub" style={{ color: checkInsDelta >= 0 ? 'var(--emerald)' : 'var(--rose)' }}>
            {formatDelta(checkInsDelta)} vs semana passada
          </div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--amber)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Disposição Média</div>
          <div className="metric-value" style={{ fontSize: 24, fontWeight: 900, color: '#f59e0b' }}>{readinessCurrent > 0 ? Math.round(readinessCurrent * 100) : '--'}</div>
          <div className="metric-sub" style={{ color: readinessDelta >= 0 ? 'var(--emerald)' : 'var(--rose)' }}>
            {readinessCurrent > 0 && readinessPrev > 0 ? `${formatDelta(Math.round(readinessDelta * 100), false)}/100` : '—'}
          </div>
        </div>
      </div>

      {/* Gráfico de barras comparativo */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-secondary)', marginBottom: 6 }}>
          <div style={{ textAlign: 'center', flex: 1 }}>Semana Passada</div>
          <div style={{ textAlign: 'center', flex: 1 }}>Esta Semana</div>
        </div>
        <svg
          viewBox="0 0 360 120"
          style={{ width: '100%', height: 'auto', background: 'var(--bg-input)', borderRadius: 10, padding: 8, border: '1px solid var(--border-subtle)' }}
        >
          {/* Semana passada */}
          <g>
            <rect x={30} y={80} width={20} height={40} rx={3} fill="rgba(255,255,255,0.08)" />
            <rect x={30} y={80 - Math.round((workoutsPrev / 7) * 40)} width={20} height={Math.round((workoutsPrev / 7) * 40)} rx={3} fill="rgba(99, 102, 241, 0.4)" />
            <text x={40} y={110} textAnchor="middle" fill="#6366f1" fontSize="11" fontWeight="700">{workoutsPrev}</text>
          </g>
          {/* Esta semana */}
          <g>
            <rect x={310} y={80} width={20} height={40} rx={3} fill="rgba(255,255,255,0.08)" />
            <rect x={310} y={80 - Math.round((workoutsCurrent / 7) * 40)} width={20} height={Math.round((workoutsCurrent / 7) * 40)} rx={3} fill="#6366f1" />
            <text x={320} y={110} textAnchor="middle" fill="#6366f1" fontSize="11" fontWeight="700">{workoutsCurrent}</text>
          </g>
        </svg>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 6, textAlign: 'center' }}>Barras = Treinos por semana</div>
      </div>

      {/* Insight de tendência */}
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
          {workoutsDelta >= 0 && checkInsDelta >= 0 ? (
            <TrendingUp size={14} color="var(--emerald)" />
          ) : (
            <TrendingDown size={14} color="var(--rose)" />
          )}
          <span className="text-xs font-bold text-slate-300 uppercase">
            {workoutsDelta >= 0 && checkInsDelta >= 0 ? 'Tendência de Melhoria' : 'Atenção Necessária'}
          </span>
        </div>
        <div className="text-[11px] text-slate-500">
          {workoutsDelta >= 2
            ? 'Você aumentou seus treinos nesta semana. Ótima evolução!'
            : workoutsDelta <= -2
              ? 'Seus treinos diminuíram. Considere voltar ao ritmo anterior.'
              : 'Seus treinos se mantiveram estáveis. Considere adicionar mais um dia.'}
          {checkInsDelta <= -2 && workoutsDelta >= 0 ? ' ' : ''}
          {checkInsDelta <= -2 ? 'Seus check-ins diminuíram. Tente registrar diariamente.' : ''}
        </div>
      </div>
    </div>
  );
};

export default WeeklyComparison;
