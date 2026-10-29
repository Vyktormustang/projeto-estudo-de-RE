import React, { useCallback, useState } from 'react';
import { Target, CheckCircle2, RefreshCw, Flame } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface WeeklyGoal {
  id: string;
  title: string;
  target: number;
  unit: string;
  completed: number;
}

interface WeeklyGoalsProps {
  bioDayId: string;
  vault: VaultState;
  onUpdateVault: (next: VaultState) => void;
}

export const WeeklyGoals: React.FC<WeeklyGoalsProps> = ({ bioDayId, vault, onUpdateVault }) => {
  const [goals, setGoals] = useState<WeeklyGoal[]>([
    { id: 'workouts', title: 'Treinos por semana', target: 4, unit: 'sessoes', completed: 0 },
    { id: 'checkins', title: 'Check-ins diarios', target: 7, unit: 'dias', completed: 0 },
    { id: 'mental', title: 'Sessoes mentais', target: 3, unit: 'sessoes', completed: 0 },
  ]);

  const last7Days = useCallback(() => {
    const days: string[] = [];
    let d = bioDayId;
    for (let i = 0; i < 7; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const updateProgress = useCallback(() => {
    const days = last7Days();
    const workoutsCount = vault.workouts.filter((w) => days.includes(w.bioDayId)).length;
    const checkInsCount = days.filter((d) => vault.checkIns[d]).length;
    const mentalCount = (vault.cognitiveLogs ?? []).filter((c) => days.includes(c.bioDayId)).length
      + (vault.deliberatePractice ?? []).filter((d) => days.includes(d.bioDayId)).length;

    setGoals((prev) => prev.map((g) => {
      if (g.id === 'workouts') return { ...g, completed: Math.min(g.target, workoutsCount) };
      if (g.id === 'checkins') return { ...g, completed: Math.min(g.target, checkInsCount) };
      if (g.id === 'mental') return { ...g, completed: Math.min(g.target, mentalCount) };
      return g;
    }));
  }, [vault, last7Days]);

  React.useEffect(() => {
    updateProgress();
  }, [vault, updateProgress]);

  const allCompleted = goals.every((g) => g.completed >= g.target);

  const handleEditTarget = (id: string) => {
    const newTarget = window.prompt(`Nova meta para "${goals.find((g) => g.id === id)?.title}":`);
    if (newTarget) {
      const n = Math.max(1, Math.min(30, parseInt(newTarget, 10) || 1));
      setGoals((prev) => prev.map((g) => g.id === id ? { ...g, target: n } : g));
      triggerHaptic('light');
    }
  };

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--amber)' }}>
            Metas Semanais • Ultimos 7 Dias
          </div>
          <h2 className="section-title">Suas Metas da Semana</h2>
        </div>
        <Target size={20} color="var(--amber)" />
      </div>

      <div style={{ gap: 10 }}>
        {goals.map((goal) => {
          const pct = Math.min(100, Math.round((goal.completed / goal.target) * 100));
          const done = goal.completed >= goal.target;
          return (
            <div key={goal.id} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', background: done ? 'var(--emerald)15' : 'var(--bg-surface)', border: `1px solid ${done ? 'var(--emerald)' : 'var(--border-subtle)'}` }}>
                {done ? <CheckCircle2 size={14} style={{ color: 'var(--emerald)' }} /> : <Target size={14} style={{ color: 'var(--amber)' }} />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold" style={{ color: done ? 'var(--emerald)' : 'var(--text-primary)' }}>
                  {goal.title}
                </div>
                <div className="text-[10px] text-slate-500">{goal.completed}/{goal.target} {goal.unit}</div>
              </div>
              <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full" style={{ width: `${pct}%`, background: done ? 'var(--emerald)' : 'var(--amber)' }}></div>
              </div>
              <div className="text-[10px] font-bold" style={{ color: 'var(--text-secondary)' }}>{pct}%</div>
              <button
                onClick={() => handleEditTarget(goal.id)}
                className="ml-2 p-1 text-slate-400 hover:text-white"
                title="Editar meta"
              >
                <RefreshCw size={12} />
              </button>
            </div>
          );
        })}
      </div>

      {allCompleted && (
        <div style={{ padding: '10px 14px', background: 'var(--emerald-soft)', borderRadius: 8, border: '1px solid rgba(16,185,129,0.35)', fontSize: 12.5, color: 'var(--emerald)', fontWeight: 600, marginTop: 8 }}>
          <Flame size={14} style={{ marginRight: 6 }} /> 🎯 Todas as metas semanais cumpridas!
        </div>
      )}
    </div>
  );
};

export default WeeklyGoals;
