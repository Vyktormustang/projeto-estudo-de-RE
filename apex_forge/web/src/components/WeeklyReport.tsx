import React, { useMemo } from 'react';
import { BarChart2 } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';

interface WeeklyReportProps {
  bioDayId: string;
  vault: VaultState;
}

export const WeeklyReport: React.FC<WeeklyReportProps> = ({ bioDayId, vault }) => {
  const last7Days = useMemo(() => {
    const days: string[] = [];
    let d = bioDayId;
    for (let i = 0; i < 7; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const workoutsByDay = useMemo(() => {
    const map: Record<string, number> = {};
    vault.workouts.forEach((w) => {
      map[w.bioDayId] = (map[w.bioDayId] ?? 0) + 1;
    });
    return map;
  }, [vault.workouts]);

  const checkInsByDay = useMemo(() => {
    const map: Record<string, boolean> = {};
    Object.keys(vault.checkIns).forEach((d) => {
      map[d] = true;
    });
    return map;
  }, [vault.checkIns]);

  const totalWorkouts = last7Days.reduce((sum, d) => sum + (workoutsByDay[d] ?? 0), 0);
  const totalCheckIns = last7Days.filter((d) => checkInsByDay[d]).length;
  const avgReadiness = useMemo(() => {
    const scores = last7Days.map((d) => {
      const ci = vault.checkIns[d];
      if (!ci) return null;
      return Math.round(((ci.sleepQuality + ci.energyLevel + ci.mentalCalm + ci.muscularRecovery) / 28) * 100);
    }).filter((s): s is number => s !== null);
    return scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;
  }, [vault.checkIns, last7Days]);

  const maxWorkouts = Math.max(3, ...last7Days.map((d) => workoutsByDay[d] ?? 0));

  return (
    <div className="card card-cyan" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
            Relatório Semanal • Últimos 7 Dias
          </div>
          <h2 className="section-title">Visão Geral de Desempenho</h2>
        </div>
        <BarChart2 size={20} color="var(--cyan)" />
      </div>

      <div className="grid-4" style={{ gap: 10, marginBottom: 14 }}>
        <div className="metric-box" style={{ borderLeft: '3px solid var(--cyan)' }}>
          <div className="metric-label">Treinos na Semana</div>
          <div className="metric-value">{totalWorkouts}</div>
          <div className="metric-sub">{last7Days.length} dias</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '3px solid var(--emerald)' }}>
          <div className="metric-label">Check-ins</div>
          <div className="metric-value">{totalCheckIns}</div>
          <div className="metric-sub">de {last7Days.length} dias</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '3px solid var(--amber)' }}>
          <div className="metric-label">Disposição Média</div>
          <div className="metric-value">{avgReadiness ?? '--'}</div>
          <div className="metric-sub">/100</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '3px solid var(--rose)' }}>
          <div className="metric-label">Consistência</div>
          <div className="metric-value">{Math.round((totalCheckIns / last7Days.length) * 100)}%</div>
          <div className="metric-sub">adesão ao protocolo</div>
        </div>
      </div>

      <div style={{ background: 'var(--bg-input)', borderRadius: 10, border: '1px solid var(--border-subtle)', padding: '12px 14px', marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>
          {last7Days.map((d) => (
            <div key={d} style={{ textAlign: 'center', flex: 1 }}>
              <div className="text-xs text-slate-500">{d.slice(5)}</div>
            </div>
          ))}
        </div>
        <svg viewBox="0 0 360 110" style={{ width: '100%', height: 'auto', display: 'block' }}>
          {last7Days.map((d, idx) => {
            const w = workoutsByDay[d] ?? 0;
            const barH = Math.round((w / maxWorkouts) * 55);
            const x = 12 + idx * 48;
            return (
              <g key={d}>
                <rect x={x} y={100 - barH} width={24} height={Math.max(2, barH)} rx={3} fill={w > 0 ? 'rgba(6, 182, 212, 0.7)' : 'rgba(255,255,255,0.08)'} />
                {w > 0 && (
                  <text x={x + 12} y={92 - barH} textAnchor="middle" fill="#22d3ee" fontSize="11" fontWeight="700" fontFamily="monospace">{w}</text>
                )}
              </g>
            );
          })}
        </svg>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 6, textAlign: 'center' }}>Barras = Treinos por dia • Azul claro = atividade registrada</div>
      </div>

      <div style={{ padding: '10px 14px', background: 'var(--bg-surface)', borderRadius: 8, border: '1px solid var(--border-subtle)', fontSize: 12.5 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span className="text-sm text-slate-400">Tendência de Treino</span>
          <span className="text-xs font-bold" style={{ color: totalWorkouts >= 3 ? 'var(--emerald)' : 'var(--amber)' }}>
            {totalWorkouts >= 3 ? '↑ Forte' : totalWorkouts >= 1 ? '→ Moderado' : '↓ Baixo'}
          </span>
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--text-secondary)' }}>
          {totalWorkouts >= 5 ? 'Excelente semana de consistência. Mantenha o ritmo.' : totalWorkouts >= 3 ? 'Boa semana. Tente adicionar mais um treino nos próximos dias.' : totalWorkouts >= 1 ? 'Começo tímido. Foque no piso mínimo de 5 minutos.' : 'Sem treinos registrados esta semana. Comece pequeno, comece hoje.'}
        </div>
      </div>
    </div>
  );
};

export default WeeklyReport;