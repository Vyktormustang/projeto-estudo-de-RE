import React, { useCallback, useState } from 'react';
import { Edit3, Save, CheckCircle2, Clock } from 'lucide-react';
import { VaultState } from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface DailyJournalProps {
  bioDayId: string;
  vault: VaultState;
  onUpdateVault: (next: VaultState) => void;
}

export const DailyJournal: React.FC<DailyJournalProps> = ({ bioDayId, vault, onUpdateVault }) => {
  const [editing, setEditing] = useState(false);
  const [note, setNote] = useState('');

  const existingNote = vault.eveningReflections?.[bioDayId]?.lessonLearnedToday || '';
  const [showSaved, setShowSaved] = useState(false);

  useCallback(() => {
    setNote(existingNote);
  }, [existingNote]);

  const handleSave = () => {
    triggerHaptic('success');
    const entry = {
      bioDayId,
      timestampMs: Date.now(),
      gratitudeNote: vault.eveningReflections?.[bioDayId]?.gratitudeNote || '',
      lessonLearnedToday: note,
      tomorrowTopPriority: vault.eveningReflections?.[bioDayId]?.tomorrowTopPriority || '',
      releasedResentment: vault.eveningReflections?.[bioDayId]?.releasedResentment ?? true,
    };

    const next: VaultState = {
      ...vault,
      eveningReflections: {
        ...vault.eveningReflections,
        [bioDayId]: entry,
      },
    };
    onUpdateVault(next);
    setEditing(false);
    setShowSaved(true);
    setTimeout(() => setShowSaved(false), 2000);
  };

  const handleCancel = () => {
    setEditing(false);
    setNote(existingNote);
  };

  if (!editing && !note) {
    return (
      <div className="card card-cyan" style={{ marginBottom: 12 }}>
        <div className="section-header">
          <div>
            <div className="section-kicker" style={{ color: 'var(--cyan)' }}>Diário do Dia</div>
            <h2 className="section-title">Registre sua reflexão</h2>
          </div>
          <Clock size={20} color="var(--cyan)" />
        </div>
        <p className="muted" style={{ marginTop: 0, marginBottom: 10 }}>
          Escreva o que aprendeu hoje, o que funcionou e o que pode melhorar amanhã.
        </p>
        <button
          onClick={() => { setEditing(true); setNote(existingNote); }}
          className="btn btn-primary btn-block"
        >
          <Edit3 size={14} /> Escrever Diário
        </button>
      </div>
    );
  }

  return (
    <div className="card card-amber" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--amber)' }}>Diário do Dia</div>
          <h2 className="section-title">Reflexão de ${bioDayId}</h2>
        </div>
        <Edit3 size={20} color="var(--amber)" />
      </div>

      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={4}
        className="input"
        style={{ minHeight: 100, marginBottom: 10, fontSize: 13 }}
        placeholder="O que você aprendeu hoje? O que funcionou? O que pode melhorar amanhã?"
      />

      {showSaved && (
        <div
          style={{
            padding: '8px 12px',
            background: 'var(--emerald-soft)',
            borderRadius: 8,
            border: '1px solid rgba(16,185,129,0.35)',
            fontSize: 12.5,
            color: 'var(--emerald)',
            fontWeight: 600,
            marginBottom: 10,
            textAlign: 'center',
          }}
        >
          <CheckCircle2 size={14} style={{ marginRight: 6 }} /> Salvou!
        </div>
      )}

      <div style={{ display: 'flex', gap: 8 }}>
        <button
          onClick={handleSave}
          disabled={note.trim().length === 0}
          className="btn btn-primary flex-1"
          style={{ opacity: note.trim().length === 0 ? 0.6 : 1 }}
        >
          <Save size={14} /> Salvar
        </button>
        <button
          onClick={handleCancel}
          className="btn btn-ghost flex-1"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
};

export default DailyJournal;
