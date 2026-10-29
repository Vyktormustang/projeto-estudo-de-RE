import React, { useCallback, useState } from 'react';
import { CheckCircle2, Clock, Plus, RefreshCw } from 'lucide-react';
import { VaultState } from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface Habit {
  id: string;
  name: string;
  color: string;
  icon: React.ElementType;
}

interface HabitTrackerProps {
  bioDayId: string;
  vault: VaultState;
  onUpdateVault: (next: VaultState) => void;
}

const DEFAULT_HABITS: Habit[] = [
  { id: 'meditacao', name: 'Meditação', color: '#8b5cf6', icon: Clock },
  { id: 'leitura', name: 'Leitura', color: '#3b82f6', icon: Plus },
  { id: 'agua', name: 'Beber Água', color: '#22d3ee', icon: RefreshCw },
  { id: 'gratidao', name: 'Gratidão', color: '#fbbf24', icon: CheckCircle2 },
];

interface HabitEntry {
  habitId: string;
  bioDayId: string;
  completed: boolean;
  timestampMs: number;
}

export const HabitTracker: React.FC<HabitTrackerProps> = ({ bioDayId, vault, onUpdateVault }) => {
  const [habits, setHabits] = useState<Habit[]>(DEFAULT_HABITS);
  const [habitEntries, setHabitEntries] = useState<HabitEntry[]>([]);

  // Carregar entradas existentes do vault (se houver)
  const existingEntries = useCallback(() => {
    const raw = localStorage.getItem(`habit_entries_${bioDayId}`);
    if (raw) {
      try {
        setHabitEntries(JSON.parse(raw));
      } catch {}
    }
  }, [bioDayId]);

  const toggleHabit = (habitId: string) => {
    triggerHaptic('light');
    const existing = habitEntries.find((e) => e.habitId === habitId && e.bioDayId === bioDayId);
    
    let nextEntries: HabitEntry[];
    if (existing) {
      nextEntries = habitEntries.filter((e) => !(e.habitId === habitId && e.bioDayId === bioDayId));
    } else {
      nextEntries = [...habitEntries, {
        habitId,
        bioDayId,
        completed: true,
        timestampMs: Date.now(),
      }];
    }
    
    setHabitEntries(nextEntries);
    localStorage.setItem(`habit_entries_${bioDayId}`, JSON.stringify(nextEntries));
    
    // Também salvar no vault como markUpgrades para persistência
    const entry = nextEntries.find((e) => e.habitId === habitId && e.bioDayId === bioDayId);
    const next: VaultState = {
      ...vault,
      markUpgrades: [
        ...vault.markUpgrades,
        {
          id: `habit_${habitId}_${bioDayId}`,
          bioDayId,
          versionLabel: 'habit_tracker',
          failureWhatHappened: '',
          rootCause: '',
          systemPatchInstalled: `habit:${habitId}:${entry ? 'completed' : 'skipped'}`,
        },
      ],
    };
    onUpdateVault(next);
  };

  const isCompleted = (habitId: string) => {
    return habitEntries.some((e) => e.habitId === habitId && e.bioDayId === bioDayId);
  };

  const completedCount = habitEntries.filter((e) => e.bioDayId === bioDayId).length;

  return (
    <div className="card card-emerald" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--emerald)' }}>
            Hábitos Diários
          </div>
          <h2 className="section-title">Acompanhe Seus Hábitos</h2>
        </div>
        <CheckCircle2 size={20} color="var(--emerald)" />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 14px',
          background: 'var(--bg-input)',
          borderRadius: 10,
          border: '1px solid var(--border-subtle)',
          marginBottom: 12,
        }}
      >
        <div>
          <div className="text-xs text-slate-400 uppercase tracking-wider">Progresso Hoje</div>
          <div className="text-sm font-bold text-white">
            {completedCount}/{habits.length}
          </div>
        </div>
        <div className="text-xs font-bold text-white" style={{ color: 'var(--emerald)' }}>
          {completedCount === habits.length && habits.length > 0 ? '100%' : Math.round((completedCount / habits.length) * 100)}%
        </div>
      </div>

      <div style={{ gap: 8 }}>
        {habits.map((habit) => {
          const done = isCompleted(habit.id);
          return (
            <div
              key={habit.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 12px',
                background: 'var(--bg-surface)',
                borderRadius: 8,
                border: `1px solid ${done ? habit.color : 'var(--border-subtle)'}`,
              }}
            >
              <habit.icon size={14} style={{ color: done ? habit.color : 'var(--text-secondary)' }} />
              <span
                className="text-sm"
                style={{
                  color: done ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontWeight: done ? 600 : 400,
                  textDecoration: done ? 'line-through' : 'none',
                }}
              >
                {habit.name}
              </span>
              <button
                onClick={() => toggleHabit(habit.id)}
                className="p-2 rounded-md"
                style={{
                  background: done ? `${habit.color}20` : 'transparent',
                  border: `1px solid ${done ? habit.color : 'var(--border-subtle)'}`,
                  color: done ? habit.color : 'var(--text-secondary)',
                }}
              >
                {done ? <CheckCircle2 size={12} /> : <Plus size={12} />}
              </button>
            </div>
          );
        })}
      </div>

      {completedCount === habits.length && habits.length > 0 && (
        <div
          style={{
            padding: '8px 14px',
            background: 'var(--emerald-soft)',
            borderRadius: 8,
            border: '1px solid rgba(16,185,129,0.35)',
            fontSize: 12.5,
            color: 'var(--emerald)',
            fontWeight: 600,
            marginTop: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <CheckCircle2 size={14} /> Todos os hábitos completos hoje!
        </div>
      )}
    </div>
  );
};

export default HabitTracker;
