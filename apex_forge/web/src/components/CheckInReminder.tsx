import React, { useMemo, useState } from 'react';
import { Clock, AlertCircle, CheckCircle2, Moon } from 'lucide-react';
import { VaultState } from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface CheckInReminderProps {
  bioDayId: string;
  vault: VaultState;
  onUpdateVault: (next: VaultState) => void;
}

export const CheckInReminder: React.FC<CheckInReminderProps> = ({ bioDayId, vault, onUpdateVault }) => {
  const checkIn = vault.checkIns[bioDayId];
  const ledger = vault.ledger[bioDayId];
  const alreadyDone = ledger?.status === 'LOGGED_ACTIVE' || ledger?.status === 'REST_CONFIRMED';

  const [snoozed, setSnoozed] = useState(false);

  const hoursSinceWake = useMemo(() => {
    if (!vault.profile) return null;
    const now = new Date();
    const wakeParts = vault.profile.usualWakeTime.split(':');
    const wakeTime = new Date(now);
    wakeTime.setHours(parseInt(wakeParts[0], 10), parseInt(wakeParts[1], 10), 0, 0);
    const diffMs = now.getTime() - wakeTime.getTime();
    return Math.max(0, Math.round(diffMs / (1000 * 60 * 60)));
  }, [vault.profile]);

  const shouldRemind = useMemo(() => {
    if (alreadyDone || snoozed) return false;
    if (!checkIn) return hoursSinceWake !== null && hoursSinceWake >= 2;
    return false;
  }, [checkIn, alreadyDone, snoozed, hoursSinceWake]);

  const handleCompleteCheckIn = () => {
    triggerHaptic('success');
    const next: VaultState = {
      ...vault,
      ledger: {
        ...vault.ledger,
        [bioDayId]: {
          bioDayId,
          status: 'LOGGED_ACTIVE',
          internalLoadAu: checkIn ? 50 : 0,
          usedMinimumFloor: false,
        },
      },
    };
    setSnoozed(true);
    onUpdateVault(next);
  };

  const handleSnooze = () => {
    triggerHaptic('light');
    setSnoozed(true);
  };

  const handleMarkRest = () => {
    triggerHaptic('success');
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
    setSnoozed(true);
    onUpdateVault(next);
  };

  if (!shouldRemind) return null;

  return (
    <div
      className="card card-rose"
      style={{
        marginBottom: 12,
        border: '2px solid var(--rose)',
      }}
    >
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--rose)' }}>
            Lembrete de Check-in
          </div>
          <h2 className="section-title">Você ainda não registrou hoje</h2>
        </div>
        <AlertCircle size={20} color="var(--rose)" />
      </div>

      <p className="muted" style={{ marginTop: 0, marginBottom: 10 }}>
        Está passando das {hoursSinceWake}h desde que você acordou. Um check-in rápido leva 20 segundos e ajuda a manter sua consistência.
      </p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button
          onClick={handleCompleteCheckIn}
          className="btn btn-primary flex-1"
          style={{ minWidth: 140 }}
        >
          <CheckCircle2 size={14} /> Registrar Check-in
        </button>
        <button
          onClick={handleMarkRest}
          className="btn btn-ghost flex-1"
          style={{ minWidth: 140 }}
        >
          <Moon size={14} /> Dia de Descanso
        </button>
        <button
          onClick={handleSnooze}
          className="btn btn-ghost"
          style={{ minWidth: 100 }}
        >
          <Clock size={14} /> Adiar
        </button>
      </div>
    </div>
  );
};

export default CheckInReminder;
