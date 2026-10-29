import React, { useCallback, useRef, useState } from 'react';
import {
  Activity,
  Award,
  Database,
  Download,
  Edit3,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Trash2,
  Upload,
} from 'lucide-react';
import { AchievementsPanel } from './AchievementsPanel';
import { WeeklyReport } from './WeeklyReport';
import { ExportCsvPanel } from './ExportCsvPanel';
import { WeeklyInsights } from './WeeklyInsights';
import { StreakTracker } from './StreakTracker';
import { WeeklyComparison } from './WeeklyComparison';
import { MonthlyReview } from './MonthlyReview';
import { DailyJournal } from './DailyJournal';
import { EnergyChart } from './EnergyChart';
import { SleepChart } from './SleepChart';
import { HabitTracker } from './HabitTracker';
import { WeeklyGoals } from './WeeklyGoals';
import { computePolymathRadar } from '../engine/polymathRadarEngine';
import { addDaysToBioDay, evaluateEvolutionPhase } from '../engine/stateEngine';
import { EvolutionPhase, VaultState } from '../engine/types';
import {
  importBackupEnvelope,
  isRunningInsideApk,
  shareOrDownloadBackup,
  triggerHaptic,
} from '../services/vaultStorage';

interface Props {
  bioDayId: string;
  vault: VaultState;
  onUpdateVault: (next: VaultState) => void;
  onEditProfile: () => void;
  onLoadDemo: () => void;
  onLoadZeroYouth?: () => void;
  onResetVault: () => void;
}

const PHASE_SUBTITLES: Record<EvolutionPhase, string> = {
  1: 'Horário fixo de acordar, postura limpa nos exercícios, respiração calmante e hábito diário.',
  2: 'Aumento gradual das séries rumo aos 66 dias em que o hábito fica automático.',
  3: 'Ganho sólido de força e fôlego nos dias em que seu corpo acorda no Sinal Verde.',
  4: 'Controle emocional sob pressão, desafios rápidos de disciplina e estudo profundo.',
  5: 'Domínio completo: saúde física e clareza mental sustentáveis pelo resto da vida.',
};

export const TelemetryVaultTab: React.FC<Props> = ({
  bioDayId,
  vault,
  onUpdateVault,
  onEditProfile,
  onLoadDemo,
  onLoadZeroYouth,
  onResetVault,
}) => {
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (!file) return;
      const text = await file.text();
      const res = await importBackupEnvelope(text);
      if (res.ok && res.vault) {
        triggerHaptic('success');
        onUpdateVault(res.vault);
        setStatusMsg('Backup arrastado e restaurado com sucesso!');
      } else {
        setStatusMsg(res.error ?? 'Falha ao importar backup arrastado.');
      }
    },
    [onUpdateVault],
  );

  const phaseEval = evaluateEvolutionPhase(vault);

  const days14 = Array.from({ length: 14 }, (_, idx) => {
    const d = addDaysToBioDay(bioDayId, idx - 13);
    const au = vault.ledger[d]?.internalLoadAu ?? 0;
    const ci = vault.checkIns[d];
    const readinessProxy = ci
      ? Math.round(
          ((ci.sleepQuality + ci.energyLevel + ci.mentalCalm + ci.muscularRecovery) / 28) * 100,
        )
      : null;
    return { day: d.slice(5), au, readinessProxy };
  });

  const maxAu = Math.max(350, ...days14.map((x) => x.au));

  const handleApplyPhaseEval = () => {
    triggerHaptic('success');
    if (phaseEval.phase !== vault.currentPhase) {
      onUpdateVault({
        ...vault,
        currentPhase: phaseEval.phase,
      });
      setStatusMsg(`Parabéns! Você avançou para ${phaseEval.phaseName}!`);
    } else {
      setStatusMsg(phaseEval.nextUnlockRequirement);
    }
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const res = await importBackupEnvelope(text);
    if (res.ok && res.vault) {
      triggerHaptic('success');
      onUpdateVault(res.vault);
      setStatusMsg('Backup verificado e restaurado com sucesso!');
    } else {
      setStatusMsg(res.error ?? 'Falha ao importar backup.');
    }
    e.target.value = '';
  };

  const cogLogs = vault.cognitiveLogs ?? [];
  const cogCount = cogLogs.length;
  const bestCog = cogCount ? Math.max(...cogLogs.map((c) => c.score)) : 0;
  const lessonsCount = Object.keys(vault.teachingProgress ?? {}).length;
  const radar = computePolymathRadar(vault);

  const cx = 160;
  const cy = 148;
  const maxR = 96;
  const radarVertices = radar.axes.map((ax, i) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / radar.axes.length;
    const r = (Math.max(8, ax.score100) / 100) * maxR;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    const lx = cx + Math.cos(angle) * (maxR + 28);
    const ly = cy + Math.sin(angle) * (maxR + 20);
    const gx = cx + Math.cos(angle) * maxR;
    const gy = cy + Math.sin(angle) * maxR;
    return { ...ax, x, y, lx, ly, gx, gy };
  });
  const polygonPoints = radarVertices.map((v) => `${v.x.toFixed(1)},${v.y.toFixed(1)}`).join(' ');

  return (
    <>
      <div className="card card-amber">
        <div className="section-header">
          <div>
            <div className="section-kicker">Sua Jornada em 5 Fases</div>
            <h2 className="section-title">{phaseEval.phaseName}</h2>
          </div>
          <Award size={22} color="var(--amber)" />
        </div>

        <p className="muted" style={{ marginTop: 0 }}>
          {PHASE_SUBTITLES[vault.currentPhase]}
        </p>

        <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
          <span className="muted" style={{ fontSize: 12.5 }}>
            Consistência nos últimos 14 dias ({phaseEval.activeDaysCount} dias ativos)
          </span>
          <span className="mono" style={{ fontSize: 12.5, color: 'var(--amber)', fontWeight: 800 }}>
            {phaseEval.consistencyPctLast14d}%
          </span>
        </div>
        <div className="progress-track" style={{ marginBottom: 12 }}>
          <div
            className="progress-fill"
            style={{ width: `${phaseEval.consistencyPctLast14d}%` }}
          />
        </div>

        <div className="muted" style={{ fontSize: 12.8, marginBottom: 12 }}>
          <strong>Próxima conquista:</strong> {phaseEval.nextUnlockRequirement}
        </div>

        <button className="btn btn-primary btn-block" onClick={handleApplyPhaseEval}>
          <RefreshCw size={16} /> Verificar se Subi de Fase
        </button>
      </div>

      {/* DECAGONO POLIMATA 10D & DETECTOR DE ELO MAIS FRACO (GOLDRATT) */}
      <div className="card card-cyan">
        <div className="section-header">
          <div>
            <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
              Visão 360° da Base Absoluta • 10 Pilares Universais
            </div>
            <h2 className="section-title">Radar Polímata &amp; Equilíbrio</h2>
          </div>
          <span className="badge badge-cyan">Harmonia {radar.harmonyIndex100}/100</span>
        </div>

        <svg
          viewBox="0 0 320 296"
          style={{
            width: '100%',
            height: 'auto',
            background: 'var(--bg-input)',
            borderRadius: 12,
            border: '1px solid var(--border-subtle)',
            marginBottom: 12,
          }}
        >
          {[0.25, 0.5, 0.75, 1].map((ring) => (
            <circle
              key={ring}
              cx={cx}
              cy={cy}
              r={maxR * ring}
              fill="none"
              stroke="rgba(148,163,184,0.16)"
              strokeDasharray={ring < 1 ? '3 3' : undefined}
            />
          ))}
          {radarVertices.map((v) => (
            <g key={v.trackId}>
              <line
                x1={cx}
                y1={cy}
                x2={v.gx}
                y2={v.gy}
                stroke="rgba(148,163,184,0.18)"
                strokeWidth="1"
              />
              <text
                x={v.lx}
                y={v.ly}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#cbd5e1"
                fontSize="8.3"
                fontWeight="700"
              >
                {v.shortLabel.slice(0, 14)} ({v.score100})
              </text>
            </g>
          ))}
          <polygon
            points={polygonPoints}
            fill="rgba(6, 182, 212, 0.26)"
            stroke="#fbbf24"
            strokeWidth="2.2"
          />
          {radarVertices.map((v) => (
            <circle key={`${v.trackId}_pt`} cx={v.x} cy={v.y} r={3.5} fill="#fbbf24" />
          ))}
        </svg>

        <div className="grid-2" style={{ fontSize: 12.4 }}>
          <div className="metric-box" style={{ borderLeft: '3px solid var(--emerald)' }}>
            <div className="metric-label">Pilar Mais Forte</div>
            <strong style={{ color: '#34d399' }}>
              {radar.strongestAxis.shortLabel} ({radar.strongestAxis.score100}%)
            </strong>
            <div className="muted" style={{ fontSize: 11.4, marginTop: 2 }}>
              {radar.strongestAxis.studiedLessons}/{radar.strongestAxis.totalLessons} lições estudadas
            </div>
          </div>
          <div className="metric-box" style={{ borderLeft: '3px solid var(--amber)' }}>
            <div className="metric-label">Gargalo Atual a Reforçar</div>
            <strong style={{ color: 'var(--amber)' }}>
              {radar.weakestAxis.shortLabel} ({radar.weakestAxis.score100}%)
            </strong>
            <div className="muted" style={{ fontSize: 11.4, marginTop: 2 }}>
              {radar.weakestAxis.studiedLessons}/{radar.weakestAxis.totalLessons} lições • Priorize na Árvore!
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="section-header">
          <div>
            <div className="section-kicker">Histórico dos Últimos 14 Dias</div>
            <h2 className="section-title">Seu Esforço &amp; Sua Disposição</h2>
          </div>
          <Activity size={20} color="var(--cyan)" />
        </div>

        <div
          style={{
            display: 'flex',
            gap: 14,
            fontSize: 11.5,
            color: 'var(--text-secondary)',
            marginBottom: 8,
          }}
        >
          <span>🟧 Barras = Esforço do Treino</span>
          <span>🟢 Pontos = Sua Disposição no Dia</span>
        </div>

        <svg
          viewBox="0 0 360 155"
          style={{
            width: '100%',
            height: 'auto',
            background: 'var(--bg-input)',
            borderRadius: 12,
            padding: 8,
            border: '1px solid var(--border-subtle)',
          }}
        >
          {days14.map((item, idx) => {
            const x = 14 + idx * 24;
            const barH = Math.round((item.au / maxAu) * 95);
            const barY = 120 - barH;
            return (
              <g key={item.day}>
                <rect
                  x={x}
                  y={barY}
                  width={14}
                  height={Math.max(2, barH)}
                  rx={3}
                  fill={item.au > 0 ? 'rgba(245, 158, 11, 0.78)' : 'rgba(255,255,255,0.08)'}
                />
                {item.readinessProxy !== null && (
                  <circle
                    cx={x + 7}
                    cy={120 - Math.round((item.readinessProxy / 100) * 95)}
                    r={3.5}
                    fill="#10b981"
                  />
                )}
                {idx % 2 === 0 && (
                  <text
                    x={x + 7}
                    y={138}
                    textAnchor="middle"
                    fill="#9ba5b7"
                    fontSize="8.5"
                    fontFamily="monospace"
                  >
                    {item.day}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        <div className="grid-4" style={{ marginTop: 12 }}>
          <div className="metric-box">
            <div className="metric-label">Treinos</div>
            <div className="metric-value">{vault.workouts.length}</div>
            <div className="metric-sub">Concluídos</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Desafios Mentais</div>
            <div className="metric-value">{cogCount}</div>
            <div className="metric-sub">{bestCog > 0 ? `Recorde ${bestCog}` : 'Arena'}</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Lições &amp; Estudo</div>
            <div className="metric-value">
              {lessonsCount + vault.deliberatePractice.length}
            </div>
            <div className="metric-sub">{lessonsCount}/200 na Base Absoluta</div>
          </div>
          <div className="metric-box">
            <div className="metric-label">Vitórias</div>
            <div className="metric-value">{vault.cookieJar.length}</div>
            <div className="metric-sub">No Pote</div>
          </div>
        </div>
      </div>

      <div className="card card-cyan">
        <div className="section-header">
          <div>
            <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
              100% Privado no Seu Celular • Sem Nuvem Externa
            </div>
            <h2 className="section-title">Backup &amp; Configurações</h2>
          </div>
          <Database size={20} color="var(--cyan)" />
        </div>

        <div style={{ marginBottom: 12 }}>
          <span className={`badge ${isRunningInsideApk() ? 'badge-green' : 'badge-cyan'}`}>
            <ShieldCheck size={12} />{' '}
            {isRunningInsideApk()
              ? 'Cofre Seguro no Android Ativo'
              : 'Modo Navegador Ativo'}
          </span>
        </div>

        {statusMsg && (
          <div
            style={{
              padding: '9px 12px',
              borderRadius: 10,
              background: 'var(--emerald-soft)',
              border: '1px solid rgba(16,185,129,0.35)',
              fontSize: 12.8,
              marginBottom: 12,
            }}
          >
            {statusMsg}
          </div>
        )}

        {/* ZONA DE DRAG & DROP PARA BACKUP */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            padding: '14px 16px',
            borderRadius: 10,
            border: dragOver
              ? '2px dashed var(--cyan)'
              : '2px dashed var(--border-subtle)',
            background: dragOver ? 'var(--cyan-soft)' : 'var(--bg-input)',
            textAlign: 'center',
            marginBottom: 12,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          <Upload size={18} style={{ marginBottom: 6 }} />
          <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--cyan)' }}>
            Arraste seu backup .json aqui
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
            ou clique para selecionar arquivo
          </div>
          <button
            className="btn btn-ghost"
            style={{ marginTop: 8, padding: '6px 14px', fontSize: 12 }}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={14} /> Restaurar Backup
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            style={{ display: 'none' }}
            onChange={handleImportFile}
          />
        </div>

        {/* WEEKLY REPORT */}
        <WeeklyReport bioDayId={bioDayId} vault={vault} />

        {/* ACHIEVEMENTS PANEL */}
        <AchievementsPanel vault={vault} />

        {/* EXPORT CSV */}
        <ExportCsvPanel vault={vault} />

        {/* WEEKLY GOALS */}
        <WeeklyGoals bioDayId={bioDayId} vault={vault} onUpdateVault={onUpdateVault} />

        {/* WEEKLY INSIGHTS */}
        <WeeklyInsights bioDayId={bioDayId} vault={vault} />

        {/* STREAK TRACKER */}
        <StreakTracker bioDayId={bioDayId} vault={vault} />

        {/* WEEKLY COMPARISON */}
        <WeeklyComparison bioDayId={bioDayId} vault={vault} />

        {/* MONTHLY REVIEW */}
        <MonthlyReview bioDayId={bioDayId} vault={vault} />

        {/* DAILY JOURNAL */}
        <DailyJournal bioDayId={bioDayId} vault={vault} onUpdateVault={onUpdateVault} />

        {/* ENERGY CHART */}
        <EnergyChart bioDayId={bioDayId} vault={vault} />

        {/* SLEEP CHART */}
        <SleepChart bioDayId={bioDayId} vault={vault} />

        {/* HABIT TRACKER */}
        <HabitTracker bioDayId={bioDayId} vault={vault} onUpdateVault={onUpdateVault} />

        <div className="grid-2" style={{ marginBottom: 10 }}>
          <button
            className="btn btn-primary"
            onClick={() => {
              triggerHaptic('light');
              void shareOrDownloadBackup(vault);
            }}
          >
            <Download size={16} /> Salvar Backup
          </button>
        </div>

        <div className="grid-2" style={{ marginBottom: 10 }}>
          <button className="btn btn-ghost" onClick={onEditProfile}>
            <Edit3 size={16} /> Editar Meu Perfil
          </button>
          <button className="btn btn-ghost" onClick={onLoadDemo}>
            <PlayCircle size={16} /> Ver Exemplo (18d)
          </button>
        </div>

        {onLoadZeroYouth && (
          <button
            className="btn btn-emerald btn-block"
            style={{ marginBottom: 10 }}
            onClick={onLoadZeroYouth}
          >
            <Award size={16} /> Carregar Perfil &ldquo;Jovem no Marco Zero&rdquo; (Dia 1)
          </button>
        )}

        {!confirmReset ? (
          <button className="btn btn-danger btn-block" onClick={() => setConfirmReset(true)}>
            <Trash2 size={16} /> Apagar Tudo e Recomeçar do Zero
          </button>
        ) : (
          <div className="grid-2">
            <button className="btn btn-ghost" onClick={() => setConfirmReset(false)}>
              Cancelar
            </button>
            <button
              className="btn btn-danger"
              onClick={() => {
                setConfirmReset(false);
                onResetVault();
              }}
            >
              Confirmar Exclusão
            </button>
          </div>
        )}
      </div>
    </>
  );
};
