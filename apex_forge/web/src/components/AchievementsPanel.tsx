import React, { useMemo } from 'react';
import { Award, Flame, ShieldCheck, Zap, Calendar, BookOpen } from 'lucide-react';
import { VaultState } from '../engine/types';

interface Achievement {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  color: string;
  unlocked: boolean;
  progress: number;
  total: number;
}

interface AchievementsPanelProps {
  vault: VaultState;
}

export const AchievementsPanel: React.FC<AchievementsPanelProps> = ({ vault }) => {
  const checkInsCount = Object.keys(vault.checkIns).length;
  const workoutsCount = vault.workouts.length;
  const lessonsCount = Object.keys(vault.teachingProgress ?? {}).length;
  const cookieJarCount = vault.cookieJar.length;
  const decisionsCount = vault.decisionJournal?.length ?? 0;
  const mentalSessionsCount = vault.mentalSessionsCount ?? 0;

  const achievements: Achievement[] = useMemo(() => [
    {
      id: 'primeiro_checkin',
      title: 'Primeiro Check-in',
      subtitle: 'Registrou seu estado pela primeira vez',
      icon: Calendar,
      color: '#34d399',
      unlocked: checkInsCount >= 1,
      progress: Math.min(100, checkInsCount * 100),
      total: 1,
    },
    {
      id: 'semana_consistente',
      title: 'Semana Consistente',
      subtitle: '7 dias de check-in consecutivos',
      icon: Flame,
      color: '#f59e0b',
      unlocked: checkInsCount >= 7,
      progress: Math.min(100, (checkInsCount / 7) * 100),
      total: 7,
    },
    {
      id: 'primeiro_treino',
      title: 'Primeiro Treino',
      subtitle: 'Completou sua primeira sessão de treino',
      icon: Zap,
      color: '#ef4444',
      unlocked: workoutsCount >= 1,
      progress: Math.min(100, workoutsCount * 100),
      total: 1,
    },
    {
      id: 'dez_treinos',
      title: 'Dez Treinos',
      subtitle: 'Dez sessões de treino completadas',
      icon: Flame,
      color: '#f59e0b',
      unlocked: workoutsCount >= 10,
      progress: Math.min(100, (workoutsCount / 10) * 100),
      total: 10,
    },
    {
      id: 'estudioso',
      title: 'Estudioso',
      subtitle: '5 lições da Base Absoluta concluídas',
      icon: BookOpen,
      color: '#06b6d4',
      unlocked: lessonsCount >= 5,
      progress: Math.min(100, (lessonsCount / 5) * 100),
      total: 5,
    },
    {
      id: 'cem_vitorias',
      title: 'Pote das Vitórias',
      subtitle: '10 vitórias registradas no pote',
      icon: Award,
      color: '#fbbf24',
      unlocked: cookieJarCount >= 10,
      progress: Math.min(100, (cookieJarCount / 10) * 100),
      total: 10,
    },
    {
      id: 'decisor_sabio',
      title: 'Decisor Sábio',
      subtitle: '5 decisões auditadas no Tribunal',
      icon: ShieldCheck,
      color: '#34d399',
      unlocked: decisionsCount >= 5,
      progress: Math.min(100, (decisionsCount / 5) * 100),
      total: 5,
    },
    {
      id: 'mente_calma',
      title: 'Mente Calma',
      subtitle: '5 sessões mentais registradas',
      icon: ShieldCheck,
      color: '#8b5cf6',
      unlocked: mentalSessionsCount >= 5,
      progress: Math.min(100, (mentalSessionsCount / 5) * 100),
      total: 5,
    },
  ], [checkInsCount, workoutsCount, lessonsCount, cookieJarCount, decisionsCount, mentalSessionsCount]);

  const unlockedCount = achievements.filter((a) => a.unlocked).length;

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker">Sistema de Conquistas</div>
          <h2 className="section-title">Suas Badges</h2>
        </div>
        <Award size={20} color="var(--amber)" />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--bg-input)', borderRadius: 10, border: '1px solid var(--border-subtle)', marginBottom: 12 }}>
        <div>
          <div className="text-xs text-slate-400 uppercase tracking-wider">Progresso</div>
          <div className="text-sm font-bold text-white">{unlockedCount}/{achievements.length} desbloqueadas</div>
        </div>
        <div className="text-xs font-bold text-white" style={{ color: 'var(--amber)' }}>{Math.round((unlockedCount / achievements.length) * 100)}%</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
        {achievements.map((ach) => (
          <div key={ach.id} className="metric-box" style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderLeft: ach.unlocked ? `3px solid ${ach.color}` : '3px solid var(--border-subtle)', opacity: ach.unlocked ? 1 : 0.6 }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', background: ach.unlocked ? `${ach.color}15` : 'var(--bg-surface)' }}><ach.icon size={14} style={{ color: ach.color }} /></div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold" style={{ color: ach.unlocked ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{ach.title}</div>
              <div className="text-[10px] text-slate-500">{ach.subtitle}</div>
            </div>
            <div className="text-[10px] font-bold" style={{ color: ach.color }}>{ach.progress}%</div>
          </div>
        ))}
      </div>

      {unlockedCount === achievements.length && (
        <div style={{ padding: '10px 14px', background: 'var(--emerald-soft)', borderRadius: 8, border: '1px solid rgba(16,185,129,0.35)', fontSize: 12.5, color: 'var(--emerald)', fontWeight: 600 }}>🏆 Todas as conquistas desbloqueadas! Você é um verdadeiro Ápice.</div>
      )}
    </div>
  );
};

export default AchievementsPanel;