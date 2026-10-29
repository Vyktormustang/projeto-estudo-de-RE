import React, { useMemo } from 'react';
import { Activity, Clock, Flame, Heart, Moon, Sun, Zap } from 'lucide-react';
import { addDaysToBioDay, computeBioDayId } from '../engine/stateEngine';
import { DailyCheckIn, VaultState } from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface DailySummaryProps {
  bioDayId: string;
  vault: VaultState;
  onUpdateVault: (next: VaultState) => void;
}

export const DailySummary: React.FC<DailySummaryProps> = ({
  bioDayId,
  vault,
  onUpdateVault,
}) => {
  const profile = vault.profile;
  const todayCheckIn = vault.checkIns[bioDayId];
  const todayLedger = vault.ledger[bioDayId];

  const readinessScore = useMemo(() => {
    if (!todayCheckIn) return null;
    return Math.round(
      ((todayCheckIn.sleepQuality +
        todayCheckIn.energyLevel +
        todayCheckIn.mentalCalm +
        todayCheckIn.muscularRecovery) /
        28) *
        100,
    );
  }, [todayCheckIn]);

  const readinessZone = useMemo(() => {
    if (!readinessScore) return 'VERDE';
    if (readinessScore >= 75) return 'VERDE';
    if (readinessScore >= 50) return 'AMARELO';
    return 'VERMELHO';
  }, [readinessScore]);

  const zoneConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
    VERDE: { label: 'Sinal Verde', color: '#10b981', icon: Zap },
    AMARELO: { label: 'Sinal Amarelo', color: '#f59e0b', icon: Sun },
    VERMELHO: { label: 'Sinal Vermelho', color: '#ef4444', icon: Moon },
  };

  const zone = zoneConfig[readinessZone];

  const handleCompleteCheckIn = () => {
    if (todayLedger?.status === 'LOGGED_ACTIVE' || todayLedger?.status === 'REST_CONFIRMED') {
      triggerHaptic('light');
      return;
    }

    const next: VaultState = {
      ...vault,
      ledger: {
        ...vault.ledger,
        [bioDayId]: {
          bioDayId,
          status: 'LOGGED_ACTIVE',
          internalLoadAu: todayCheckIn ? 50 : 0,
          usedMinimumFloor: false,
        },
      },
    };
    triggerHaptic('success');
    onUpdateVault(next);
  };

  const yesterday = addDaysToBioDay(bioDayId, -1);
  const yesterdayCheckIn = vault.checkIns[yesterday];
  const streak = useMemo(() => {
    let count = 0;
    let d = bioDayId;
    while (vault.checkIns[d]) {
      count++;
      d = addDaysToBioDay(d, -1);
    }
    return count;
  }, [vault.checkIns, bioDayId]);

  if (!profile) return null;

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker">Resumo do Dia</div>
          <h2 className="section-title">Hoje: {bioDayId.slice(5)}</h2>
        </div>
        <Activity size={20} color="var(--amber)" />
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          padding: '10px 12px',
          background: 'var(--bg-input)',
          borderRadius: 10,
          border: `1px solid var(--border-subtle)`,
          marginBottom: 12,
        }}
      >
        <div className="flex items-center gap-8">
          <div className="flex flex-col items-center">
            <div className="text-xs text-slate-400 uppercase tracking-wider">Disposição</div>
            <div className={`text-xl font-bold ${zone.color}`}>
              {readinessScore ?? '--'}/100
            </div>
          </div>
          <div className="w-px h-6 bg-slate-700" />
          <div className="flex flex-col items-center">
            <div className="text-xs text-slate-400 uppercase tracking-wider">Sequência</div>
            <div className="text-xl font-bold text-white">{streak} dias</div>
          </div>
        </div>
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
          style={{
            background: `${zone.color}15`,
            border: `1px solid ${zone.color}40`,
          }}
        >
          <zone.icon size={14} style={{ color: zone.color }} />
          <span className="text-xs font-bold uppercase tracking-wider" style={{ color: zone.color }}>
            {zone.label}
          </span>
        </div>
      </div>

      {todayCheckIn && (
        <div className="grid-4" style={{ gap: 8, marginBottom: 12 }}>
          <div className="metric-box">
            <div className="metric-label">Sono</div>
            <div className="metric-value">{todayCheckIn.sleepHours}h</div>
            <div className="metric-sub">Qualidade: {todayCheckIn.sleepQuality}/7</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Energia</div>
            <div className="metric-value">{todayCheckIn.energyLevel}/7</div>
            <div className="metric-sub">Calma mental: {todayCheckIn.mentalCalm}/7</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Recuperação</div>
            <div className="metric-value">{todayCheckIn.muscularRecovery}/7</div>
            <div className="metric-sub">Dor: {todayCheckIn.painKind}</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Estresse</div>
            <div className="metric-value">
              {todayCheckIn.externalLifeStressEvent ? 'Sim' : 'Não'}
            </div>
            <div className="metric-sub">Evento externo</div>
          </div>
        </div>
      )}

      {!todayCheckIn && (
        <div
          style={{
            padding: '16px 12px',
            textAlign: 'center',
            background: 'var(--bg-input)',
            borderRadius: 10,
            border: '1px dashed var(--border-subtle)',
            color: 'var(--text-secondary)',
          }}
        >
          <Heart size={20} style={{ marginBottom: 8 }} />
          <div className="text-sm text-slate-300">Registre seu check-in diário na aba Início</div>
          <div className="text-xs text-slate-500 mt-2">Acompanhe sono, energia e recuperação</div>
        </div>
      )}

      <div
        style={{
          display: 'flex',
          gap: 8,
          marginTop: 8,
        }}
      >
        <button
          onClick={handleCompleteCheckIn}
          disabled={!todayCheckIn || todayLedger?.status === 'LOGGED_ACTIVE' || todayLedger?.status === 'REST_CONFIRMED'}
          className="btn btn-primary flex-1"
          style={{ opacity: todayCheckIn && !todayLedger ? 1 : 0.5 }}
        >
          {todayLedger?.status === 'LOGGED_ACTIVE' || todayLedger?.status === 'REST_CONFIRMED'
            ? 'Dia Registrado ✓'
            : 'Registrar Check-in'}
        </button>
        {todayCheckIn && todayLedger?.status !== 'REST_CONFIRMED' && (
          <button
            onClick={() => {
              const next: VaultState = {
                ...vault,
                ledger: {
                  ...vault.ledger,
                  [bioDayId]: {
                    bioDayId,
                    status: 'REST_CONFIRMED',
                    internalLoadAu: 0,
                    usedMinimumFloor: true,
                  },
                },
              };
              triggerHaptic('success');
              onUpdateVault(next);
            }}
            className="btn btn-ghost flex-1"
          >
            <Moon size={16} /> Descanso
          </button>
        )}
      </div>
    </div>
  );
};

export default DailySummary;