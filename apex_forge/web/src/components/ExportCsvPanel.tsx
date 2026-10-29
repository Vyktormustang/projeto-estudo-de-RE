import React, { useCallback } from 'react';
import { Download, FileText, Share2 } from 'lucide-react';
import { VaultState } from '../engine/types';

interface ExportCsvProps {
  vault: VaultState;
  onExportComplete?: () => void;
}

export const ExportCsvPanel: React.FC<ExportCsvProps> = ({ vault, onExportComplete }) => {
  const exportWorkoutsCsv = useCallback(() => {
    const headers = ['data', 'slot', 'duracao_min', 'rpe', 'carga_interna_au', 'num_series'];
    const rows = vault.workouts.map((w) => [
      w.bioDayId,
      w.queueSlot,
      w.durationMinutes,
      w.sessionRpe,
      w.internalLoadAu,
      w.sets.length,
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    downloadCsv(csv, 'forja_treinos.csv');
  }, [vault.workouts]);

  const exportCheckInsCsv = useCallback(() => {
    const headers = ['data', 'sono_h', 'sono_qual', 'energia', 'calma_mental', 'recuperacao_muscular', 'dor', 'viral_febre', 'estresse_externo'];
    const rows = Object.entries(vault.checkIns).map(([bioDayId, ci]) => [
      bioDayId,
      ci.sleepHours,
      ci.sleepQuality,
      ci.energyLevel,
      ci.mentalCalm,
      ci.muscularRecovery,
      ci.painKind,
      ci.viralOrFeverSymptoms ? '1' : '0',
      ci.externalLifeStressEvent ? '1' : '0',
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    downloadCsv(csv, 'forja_checkins.csv');
  }, [vault.checkIns]);

  const exportDecisionsCsv = useCallback(() => {
    const headers = ['data', 'decisao', 'custo_torre', 'veredito', 'maturidade_100', 'resolvido'];
    const rows = (vault.decisionJournal ?? []).map((d) => [
      d.bioDayId,
      d.decisionTitle,
      d.towerCostEstimate,
      d.verdict,
      d.maturityScore100,
      d.resolvedOutcome ?? 'pendente',
    ]);
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    downloadCsv(csv, 'forja_decisoes.csv');
  }, [vault.decisionJournal]);

  const downloadCsv = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    onExportComplete?.();
  };

  return (
    <div className="card card-emerald" style={{ marginBottom: 12 }}>
      <div className="section-header">
        <div>
          <div className="section-kicker" style={{ color: 'var(--emerald)' }}>
            Exportação de Dados
          </div>
          <h2 className="section-title">Backup em CSV</h2>
        </div>
        <FileText size={20} color="var(--emerald)" />
      </div>

      <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
        Exporte seus dados para planilha (Excel, Google Sheets, etc.). Tudo fica offline no seu dispositivo.
      </p>

      <div className="grid-3" style={{ gap: 8 }}>
        <button
          className="btn btn-primary btn-block"
          onClick={exportWorkoutsCsv}
          disabled={vault.workouts.length === 0}
          style={{ opacity: vault.workouts.length === 0 ? 0.6 : 1 }}
        >
          <Download size={14} /> Treinos
        </button>
        <button
          className="btn btn-primary btn-block"
          onClick={exportCheckInsCsv}
          disabled={Object.keys(vault.checkIns).length === 0}
          style={{ opacity: Object.keys(vault.checkIns).length === 0 ? 0.6 : 1 }}
        >
          <Download size={14} /> Check-ins
        </button>
        <button
          className="btn btn-primary btn-block"
          onClick={exportDecisionsCsv}
          disabled={(vault.decisionJournal?.length ?? 0) === 0}
          style={{ opacity: (vault.decisionJournal?.length ?? 0) === 0 ? 0.6 : 1 }}
        >
          <Share2 size={14} /> Decisões
        </button>
      </div>

      <div className="grid-3" style={{ gap: 8, marginTop: 8 }}>
        <button
          className="btn btn-ghost btn-block"
          onClick={() => {
            exportWorkoutsCsv();
            exportCheckInsCsv();
            exportDecisionsCsv();
          }}
          disabled={
            vault.workouts.length === 0 &&
            Object.keys(vault.checkIns).length === 0 &&
            (vault.decisionJournal?.length ?? 0) === 0
          }
        >
          <Download size={14} /> Exportar Tudo
        </button>
      </div>
    </div>
  );
};

export default ExportCsvPanel;
