import React, { useMemo } from 'react';
import { Calendar, Flame, Target, BarChart2 } from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { VaultState } from '../engine/types';

interface MonthlyReviewProps {
  bioDayId: string;
  vault: VaultState;
}

export const MonthlyReview: React.FC<MonthlyReviewProps> = ({ bioDayId, vault }) => {
  // Extrair ano/mes do bioDayId (formato YYYY-MM-DD)
  const [year, month] = bioDayId.split('-').map(Number);

  // Primeiro dia do mês
  const firstDay = new Date(year, month - 1, 1);
  const lastDay = new Date(year, month, 0);
  const daysInMonth = lastDay.getDate();

  // Gerar todas as datas do mês atual
  const monthDays: string[] = [];
  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(year, month - 1, d);
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    monthDays.push(`${y}-${m}-${day}`);
  }

  const workoutsMonth = useMemo(() => {
    return monthDays.filter((d) => vault.workouts.some((w) => w.bioDayId === d)).length;
  }, [monthDays, vault.workouts]);

  const checkInsMonth = useMemo(() => {
    return monthDays.filter((d) => Boolean(vault.checkIns[d])).length;
  }, [monthDays, vault.checkIns]);

  const mentalMonth = useMemo(() => {
    return monthDays.filter((d) =>
      (vault.cognitiveLogs ?? []).some((c) => c.bioDayId === d) ||
      (vault.deliberatePractice ?? []).some((p) => p.bioDayId === d)
    ).length;
  }, [monthDays, vault.cognitiveLogs, vault.deliberatePractice]);

  const totalCookiesMonth = useMemo(() => {
    return vault.cookieJar.filter((c) => monthDays.includes(c.bioDayId)).length;
  }, [monthDays, vault.cookieJar]);

  const readinessValues = useMemo(() => {
    return monthDays.map((d) => {
      const ci = vault.checkIns[d];
      if (!ci) return null;
      return (ci.sleepQuality + ci.energyLevel + ci.mentalCalm + ci.muscularRecovery) / 28;
    }).filter((s): s is number => s !== null);
  }, [monthDays, vault.checkIns]);

  const avgReadiness = useMemo(() => {
    if (readinessValues.length === 0) return 0;
    return readinessValues.reduce((a, b) => a + b, 0) / readinessValues.length;
  }, [readinessValues]);

  const daysElapsed = useMemo(() => {
    const today = new Date();
    const currentMonth = today.getMonth() + 1;
    const currentYear = today.getFullYear();
    if (year === currentYear && month === currentMonth) {
      return today.getDate();
    }
    return daysInMonth;
  }, [year, month, daysInMonth]);

  const pctMonth = daysInMonth > 0 ? Math.round((daysElapsed / daysInMonth) * 100) : 100;

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--amber)' }}>
            Revisão Mensal • ${new Date(year, month - 1, 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}
          </div>
          <h2 className="section-title">Balanço do Mês</h2>
        </div>
        <Calendar size={20} color="var(--amber)" />
      </div>

      <div className="grid-4" style={{ gap: 10, marginBottom: 14 }}>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--cyan)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Treinos</div>
          <div className="metric-value" style={{ fontSize: 24, fontWeight: 900, color: 'var(--cyan)' }}>{workoutsMonth}</div>
          <div className="metric-sub">dias ativos</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--emerald)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Check-ins</div>
          <div className="metric-value" style={{ fontSize: 24, fontWeight: 900, color: '#34d399' }}>{checkInsMonth}</div>
          <div className="metric-sub">de ${daysInMonth} dias</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--amber)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Prática Mental</div>
          <div className="metric-value" style={{ fontSize: 24, fontWeight: 900, color: '#f59e0b' }}>{mentalMonth}</div>
          <div className="metric-sub">sessões</div>
        </div>
        <div className="metric-box" style={{ borderLeft: '4px solid var(--rose)', background: 'var(--bg-input)' }}>
          <div className="metric-label" style={{ fontSize: 10.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Vitórias</div>
          <div className="metric-value" style={{ fontSize: 24, fontWeight: 900, color: '#ef4444' }}>{totalCookiesMonth}</div>
          <div className="metric-sub">no pote</div>
        </div>
      </div>

      {/* Barra de progresso do mês */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-secondary)', marginBottom: 6 }}>
          <span>Início do Mês</span>
          <span>${pctMonth}% do Mês</span>
          <span>Fim do Mês</span>
        </div>
        <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full" style={{ width: `${Math.min(100, pctMonth)}%`, background: 'var(--amber)' }}></div>
        </div>
      </div>

      {/* Disposição média */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-secondary)', marginBottom: 6 }}>
          <span>Disposição Média</span>
          <span>${readinessValues.length > 0 ? Math.round(avgReadiness * 100) : '--'}/100</span>
        </div>
        <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
          <div className="h-full" style={{ width: `${Math.round(avgReadiness * 100)}%`, background: avgReadiness >= 0.75 ? 'var(--emerald)' : avgReadiness >= 0.5 ? 'var(--amber)' : 'var(--rose)' }}></div>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4, textAlign: 'center' }}>
          ${readinessValues.length} dias com check-in registrado
        </div>
      </div>

      {/* Mensagem de fechamento */}
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
          <Target size={14} color="var(--amber)" />
          <span className="text-xs font-bold text-slate-300 uppercase">Assinatura do Mês</span>
        </div>
        <div className="text-[11px] text-slate-500">
          ${checkInsMonth >= 20
            ? 'Mês de alta consistência. Você está construindo fundamentos sólidos.'
            : checkInsMonth >= 10
              ? 'Bom mês de consistência. Tente fechar com ainda mais dias registrados.'
              : 'Mês com poucos registros. Cada check-in é um passo na direção certa.'}
        </div>
      </div>
    </div>
  );
};

export default MonthlyReview;
