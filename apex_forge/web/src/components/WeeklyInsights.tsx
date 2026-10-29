import React, { useMemo } from 'react';
import { Lightbulb, TrendingUp, TrendingDown, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';

interface WeeklyInsightsProps {
  bioDayId: string;
  vault: VaultState;
}

export const WeeklyInsights: React.FC<WeeklyInsightsProps> = ({ bioDayId, vault }) => {
  const last7Days = useMemo(() => {
    const days: string[] = [];
    let d = bioDayId;
    for (let i = 0; i < 7; i++) {
      days.push(d);
      d = addDaysToBioDay(d, -1);
    }
    return days.reverse();
  }, [bioDayId]);

  const insights = useMemo(() => {
    const list: Array<{ type: 'info' | 'success' | 'warning'; icon: React.ElementType; title: string; text: string }> = [];

    const workoutsCount = vault.workouts.filter((w) => last7Days.includes(w.bioDayId)).length;
    const checkInsCount = last7Days.filter((d) => vault.checkIns[d]).length;
    const mentalCount = (vault.cognitiveLogs ?? []).filter((c) => last7Days.includes(c.bioDayId)).length;

    if (workoutsCount >= 5) {
      list.push({
        type: 'success',
        icon: CheckCircle2,
        title: 'Excelente consistência de treino',
        text: `${workoutsCount} treinos esta semana. Você está construindo o hábito sólido.`,
      });
    } else if (workoutsCount >= 2) {
      list.push({
        type: 'info',
        icon: Lightbulb,
        title: 'Bom começo de treino',
        text: `${workoutsCount} treinos. Tente adicionar mais um dia nos próximos 7 dias.`,
      });
    } else {
      list.push({
        type: 'warning',
        icon: AlertTriangle,
        title: 'Pouca atividade física',
        text: `Apenas ${workoutsCount} treino(s). Lembre-se: o piso mínimo é 5 minutos.`,
      });
    }

    if (checkInsCount === 7) {
      list.push({
        type: 'success',
        icon: CheckCircle2,
        title: 'Check-in perfeito',
        text: 'Você registrou todos os 7 dias. Essa consistência é a chave.',
      });
    } else if (checkInsCount >= 4) {
      list.push({
        type: 'info',
        icon: Lightbulb,
        title: 'Check-in regular',
        text: `${checkInsCount}/7 dias. Tente não pular nenhum amanhã.`,
      });
    } else {
      list.push({
        type: 'warning',
        icon: AlertTriangle,
        title: 'Check-in esporádico',
        text: `Apenas ${checkInsCount}/7 dias. O registro diário melhora o autoconscimento.`,
      });
    }

    if (mentalCount >= 3) {
      list.push({
        type: 'success',
        icon: TrendingUp,
        title: 'Treinamento mental ativo',
        text: `${mentalCount} sessão(ões) de prática deliberada/cognitiva.`,
      });
    } else if (mentalCount > 0) {
      list.push({
        type: 'info',
        icon: Lightbulb,
        title: 'Algum treino mental',
        text: `${mentalCount} sessão(ões). Tente 2-3 vezes por semana.`,
      });
    }

    const avgReadiness = last7Days.map((d) => {
      const ci = vault.checkIns[d];
      if (!ci) return null;
      return (ci.sleepQuality + ci.energyLevel + ci.mentalCalm + ci.muscularRecovery) / 28;
    }).filter((s): s is number => s !== null);

    if (avgReadiness.length > 0) {
      const avg = avgReadiness.reduce((a, b) => a + b, 0) / avgReadiness.length;
      if (avg >= 0.75) {
        list.push({
          type: 'success',
          icon: TrendingUp,
          title: 'Disposição elevada',
          text: `Média de ${Math.round(avg * 100)}/100 nos últimos 7 dias.`,
        });
      } else if (avg < 0.5) {
        list.push({
          type: 'warning',
          icon: AlertTriangle,
          title: 'Disposição baixa',
          text: `Média de ${Math.round(avg * 100)}/100. Priorize sono e recuperação.`,
        });
      }
    }

    return list;
  }, [vault, last7Days]);

  if (insights.length === 0) return null;

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--amber)' }}>
            Insights Automáticos • Últimos 7 Dias
          </div>
          <h2 className="section-title">O que seus dados dizem</h2>
        </div>
        <Lightbulb size={20} color="var(--amber)" />
      </div>

      <div style={{ gap: 8 }}>
        {insights.map((insight, idx) => (
          <div
            key={idx}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 8,
              padding: '8px 10px',
              background: insight.type === 'success'
                ? 'var(--emerald-soft)'
                : insight.type === 'warning'
                  ? 'var(--rose-soft)'
                  : 'var(--cyan-soft)',
              borderRadius: 8,
              border: `1px solid ${insight.type === 'success' ? 'var(--emerald)' : insight.type === 'warning' ? 'var(--rose)' : 'var(--cyan)'}30`,
            }}
          >
            <insight.icon size={14} style={{ color: insight.type === 'success' ? 'var(--emerald)' : insight.type === 'warning' ? 'var(--rose)' : 'var(--cyan)', marginTop: 1 }} />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-bold" style={{ color: insight.type === 'success' ? 'var(--emerald)' : insight.type === 'warning' ? 'var(--rose)' : 'var(--cyan)' }}>
                {insight.title}
              </div>
              <div className="text-[11px] text-slate-600">{insight.text}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WeeklyInsights;
