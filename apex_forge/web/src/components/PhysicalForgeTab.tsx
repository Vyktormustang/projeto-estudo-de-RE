import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Check,
  CheckCircle2,
  Clock,
  Eye,
  Play,
  PlayCircle,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Zap,
} from 'lucide-react';
import { EXERCISE_CATALOG, getExerciseById } from '../engine/exerciseCatalog';
import {
  ENGINE_VERSION,
  EquipmentEnv,
  ExerciseVariant,
  LoggedSet,
  PrescribedDayPlan,
  PrescribedExercise,
  WorkoutSessionLog,
} from '../engine/types';
import { playTacticalChime } from '../services/audioBiofeedback';
import { setWakeLock, triggerHaptic } from '../services/vaultStorage';
import { ExerciseDemoModal } from './ExerciseDemoModal';

interface Props {
  bioDayId: string;
  plan: PrescribedDayPlan | null;
  pastWorkouts: WorkoutSessionLog[];
  completedWorkoutToday?: WorkoutSessionLog;
  onCompleteWorkout: (
    log: WorkoutSessionLog,
    advanceSlot: boolean,
    usedMinimumFloor: boolean,
  ) => void;
  onGoToCheckIn: () => void;
}

interface DraftSetRow {
  loadKg: string;
  reps: string;
  rir: string;
  done: boolean;
}

type ExecutionMode = 'PADRAO' | 'PIVOT_15M' | 'PISO_5M';

export const PhysicalForgeTab: React.FC<Props> = ({
  bioDayId,
  plan,
  pastWorkouts,
  completedWorkoutToday,
  onCompleteWorkout,
  onGoToCheckIn,
}) => {
  const [execMode, setExecMode] = useState<ExecutionMode>('PADRAO');
  const [keepAwake, setKeepAwake] = useState(false);
  const [restSeconds, setRestSeconds] = useState(0);
  const [prepSeconds, setPrepSeconds] = useState(0);
  const [prepCompleted, setPrepCompleted] = useState(false);
  const [sessionMinutes, setSessionMinutes] = useState('40');
  const [sessionRpe, setSessionRpe] = useState<number>(7);
  const [draftSets, setDraftSets] = useState<Record<string, DraftSetRow[]>>({});

  // Modal de demonstracao animada + Biblioteca Visual
  const [demoExercise, setDemoExercise] = useState<ExerciseVariant | null>(null);
  const [showCatalogBrowser, setShowCatalogBrowser] = useState(false);
  const [catalogFilter, setCatalogFilter] = useState<'TODOS' | EquipmentEnv>('TODOS');

  useEffect(() => {
    setWakeLock(keepAwake);
    return () => setWakeLock(false);
  }, [keepAwake]);

  const activeExercises: PrescribedExercise[] = !plan
    ? []
    : execMode === 'PIVOT_15M'
      ? plan.doctorWho15MinPivot.exercises
      : execMode === 'PISO_5M'
        ? []
        : plan.exercises;

  useEffect(() => {
    if (!plan) return;
    if (execMode === 'PISO_5M') {
      setSessionMinutes('5');
      setSessionRpe(4);
      return;
    }
    if (execMode === 'PIVOT_15M') {
      setSessionMinutes('15');
      setSessionRpe(6);
    } else {
      setSessionMinutes(String(plan.estimatedMinutes));
      setSessionRpe(plan.readiness.zone === 'VERMELHO' ? 3 : 7);
    }

    const nextDraft: Record<string, DraftSetRow[]> = {};
    for (const ex of activeExercises) {
      let lastLoad = ex.suggestedLoadKg ?? 0;
      let lastReps = parseInt(ex.targetReps, 10) || 10;
      for (let i = pastWorkouts.length - 1; i >= 0; i--) {
        const hit = pastWorkouts[i].sets.find((s) => s.exerciseId === ex.exerciseId);
        if (hit) {
          lastLoad = hit.loadKg;
          lastReps = hit.reps;
          break;
        }
      }
      const parsedRir = parseInt(ex.targetRir, 10);
      const rirDefault = Number.isFinite(parsedRir) ? parsedRir : plan.readiness.intensityRirFloor;
      nextDraft[ex.exerciseId] = Array.from({ length: ex.sets }, () => ({
        loadKg: String(lastLoad),
        reps: String(lastReps),
        rir: String(rirDefault),
        done: false,
      }));
    }
    setDraftSets(nextDraft);
  }, [plan?.bioDayId, plan?.queueSlot, plan?.readiness.zone, execMode]);

  useEffect(() => {
    if (restSeconds <= 0) return;
    const id = window.setInterval(() => {
      setRestSeconds((prev) => {
        if (prev <= 1) {
          triggerHaptic('success');
          playTacticalChime('REST_DONE');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [restSeconds]);

  useEffect(() => {
    if (prepSeconds <= 0) return;
    const id = window.setInterval(() => {
      setPrepSeconds((prev) => {
        if (prev <= 1) {
          setPrepCompleted(true);
          triggerHaptic('success');
          playTacticalChime('VICTORY');
          return 0;
        }
        if (prev === 41 || prev === 31 || prev === 21) {
          triggerHaptic('light');
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(id);
  }, [prepSeconds]);

  const updateRow = (
    exId: string,
    idx: number,
    patch: Partial<DraftSetRow>,
    autoRestSec?: number,
  ) => {
    setDraftSets((prev) => {
      const list = [...(prev[exId] ?? [])];
      list[idx] = { ...list[idx], ...patch };
      return { ...prev, [exId]: list };
    });
    if (patch.done && autoRestSec) {
      triggerHaptic('medium');
      setRestSeconds(autoRestSec);
    }
  };

  const handleFinishSession = () => {
    if (!plan) return;
    triggerHaptic('success');
    playTacticalChime('VICTORY');

    const collectedSets: LoggedSet[] = [];
    for (const ex of activeExercises) {
      const rows = draftSets[ex.exerciseId] ?? [];
      for (const r of rows) {
        if (r.done || rows.length === 1) {
          collectedSets.push({
            exerciseId: ex.exerciseId,
            loadKg: Math.max(0, Number(r.loadKg) || 0),
            reps: Math.max(1, Math.round(Number(r.reps) || 8)),
            rir: Math.max(0, Math.min(6, Number(r.rir) || plan.readiness.intensityRirFloor)),
          });
        }
      }
    }

    const dur = Math.max(
      5,
      Math.min(240, Math.round(Number(sessionMinutes) || plan.estimatedMinutes)),
    );
    const au = Math.round(dur * sessionRpe);

    const slotLabel: WorkoutSessionLog['queueSlot'] =
      execMode === 'PISO_5M'
        ? 'PISO_MINIMO_5M'
        : execMode === 'PIVOT_15M'
          ? 'PIVOT_15M'
          : plan.queueSlot;

    const log: WorkoutSessionLog = {
      id: `wk_${Date.now()}`,
      bioDayId,
      timestampMs: Date.now(),
      queueSlot: slotLabel,
      durationMinutes: dur,
      sessionRpe,
      internalLoadAu: au,
      sets: collectedSets,
      completedAmccChallenge: false,
      engineVersion: ENGINE_VERSION,
    };

    const usedMinimumFloor = execMode !== 'PADRAO';
    const advanceSlot =
      execMode === 'PADRAO' && plan.queueSlot !== 'RECUPERACAO_ATIVA' && activeExercises.length > 0;

    onCompleteWorkout(log, advanceSlot, usedMinimumFloor);
  };

  const filteredCatalog =
    catalogFilter === 'TODOS'
      ? EXERCISE_CATALOG
      : EXERCISE_CATALOG.filter((e) => e.environments.includes(catalogFilter));

  return (
    <>
      {demoExercise && (
        <ExerciseDemoModal exercise={demoExercise} onClose={() => setDemoExercise(null)} />
      )}

      {!plan ? (
        <div className="card card-amber">
          <div className="section-kicker">1º Passo Rápido</div>
          <h2 className="section-title">Responda o resumo de 20s na aba Início</h2>
          <p className="muted">
            Assim ajustamos o peso, as repetições e trocamos qualquer exercício caso você esteja com
            dor ou cansaço hoje. Você também já pode explorar todas as demonstrações animadas abaixo!
          </p>
          <button className="btn btn-primary btn-block" onClick={onGoToCheckIn}>
            Fazer Leitura de 20s no Início
          </button>
        </div>
      ) : (
        <>
          <div className="card card-amber">
            <div className="section-header">
              <div>
                <div className="section-kicker">
                  Treino {plan.queueSlot} • Nunca pune dias pulados
                </div>
                <h2 className="section-title">
                  {execMode === 'PISO_5M'
                    ? plan.minimumFloor5Min.title
                    : execMode === 'PIVOT_15M'
                      ? plan.doctorWho15MinPivot.title
                      : plan.sessionTitle}
                </h2>
              </div>
              <button
                className={`chip ${keepAwake ? 'chip-active' : ''}`}
                onClick={() => {
                  triggerHaptic('light');
                  setKeepAwake((v) => !v);
                }}
              >
                <Eye size={13} style={{ verticalAlign: 'middle' }} />{' '}
                {keepAwake ? 'Tela Acesa' : 'Manter Tela'}
              </button>
            </div>

            <div className="chip-row" style={{ marginBottom: 12 }}>
              <button
                type="button"
                className={`chip ${execMode === 'PADRAO' ? 'chip-active' : ''}`}
                onClick={() => setExecMode('PADRAO')}
              >
                Treino Ideal ({plan.estimatedMinutes} min)
              </button>
              <button
                type="button"
                className={`chip ${execMode === 'PIVOT_15M' ? 'chip-active' : ''}`}
                onClick={() => setExecMode('PIVOT_15M')}
              >
                <Zap size={12} /> Modo Rápido (15 min)
              </button>
              <button
                type="button"
                className={`chip ${execMode === 'PISO_5M' ? 'chip-active' : ''}`}
                onClick={() => setExecMode('PISO_5M')}
              >
                Emergência (5 min)
              </button>
            </div>

            {/* RITUAL PRE-SERIE DE 60s: MOBILIDADE DINAMICA + FLAMINGO 10s + OXIDO NITRICO NASAL */}
            <div
              style={{
                padding: '10px 12px',
                borderRadius: 14,
                background: prepCompleted ? 'var(--emerald-soft)' : 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                marginBottom: 10,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 8,
                }}
              >
                <div>
                  <div style={{ fontSize: 13, fontWeight: 800 }}>
                    {prepCompleted
                      ? '✓ Ritual Pré-Série Concluído (Corpo & SNC Prontos!)'
                      : prepSeconds > 40
                        ? `Fase 1/3 (${prepSeconds}s): Mobilidade Articular Dinâmica (Simic, 2012)`
                        : prepSeconds > 30
                          ? `Fase 2A/3 (${prepSeconds}s): Flamingo 10s — Perna Direita (Araujo, BJSM 2022)`
                          : prepSeconds > 20
                            ? `Fase 2B/3 (${prepSeconds}s): Flamingo 10s — Perna Esquerda (Araujo, BJSM 2022)`
                            : prepSeconds > 0
                              ? `Fase 3/3 (${prepSeconds}s): Respiração Nasal Profunda NO (Lundberg, 1995)`
                              : 'Ritual Pré-Série de 60s (Mobilidade + Equilíbrio 10s + Nasal)'}
                  </div>
                  <div className="muted" style={{ fontSize: 11.5 }}>
                    {prepSeconds > 0
                      ? 'Siga a fase ao vivo sem estirar frio — lubrifica cápsulas e ativa propriocepção.'
                      : 'Prepara articulações, testa estabilidade unipodal (10s/lado) e oxigena via nasal.'}
                  </div>
                </div>
                <button
                  type="button"
                  className={`chip ${prepSeconds > 0 ? 'chip-active' : ''}`}
                  onClick={() => {
                    triggerHaptic('medium');
                    if (prepSeconds > 0) {
                      setPrepSeconds(0);
                    } else {
                      setPrepCompleted(false);
                      setPrepSeconds(60);
                    }
                  }}
                >
                  {prepSeconds > 0 ? 'Parar' : prepCompleted ? 'Refazer 60s' : 'Iniciar 60s'}
                </button>
              </div>
            </div>

            {/* CRONOMETRO DE DESCANSO ENTRE SERIES */}
            <div
              style={{
                padding: '10px 12px',
                borderRadius: 14,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 8,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Clock size={16} color="var(--cyan)" />
                <span className="mono" style={{ fontSize: 15.5, fontWeight: 800 }}>
                  {restSeconds > 0
                    ? `Descanso: ${Math.floor(restSeconds / 60)}:${String(
                        restSeconds % 60,
                      ).padStart(2, '0')}`
                    : 'Timer de Descanso'}
                </span>
              </div>
              <div className="chip-row">
                {[60, 90, 120, 180].map((sec) => (
                  <button
                    key={sec}
                    type="button"
                    className="chip"
                    style={{ padding: '6px 10px' }}
                    onClick={() => {
                      triggerHaptic('light');
                      setRestSeconds(sec);
                    }}
                  >
                    <Play size={11} /> {sec}s
                  </button>
                ))}
                {restSeconds > 0 && (
                  <button
                    type="button"
                    className="chip chip-danger-active"
                    onClick={() => setRestSeconds(0)}
                  >
                    <RotateCcw size={11} /> Zerar
                  </button>
                )}
              </div>
            </div>
          </div>

          {completedWorkoutToday && (
            <div className="card card-emerald">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <CheckCircle2 size={22} color="var(--emerald)" />
                <div>
                  <strong>Treino Concluído Hoje!</strong>
                  <div className="muted">
                    {completedWorkoutToday.durationMinutes} min • Esforço{' '}
                    {completedWorkoutToday.sessionRpe}/10
                  </div>
                </div>
              </div>
            </div>
          )}

          {execMode === 'PISO_5M' ? (
            <div className="card card-cyan">
              <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
                5 Minutos que Salvam o Hábito
              </div>
              <h3 className="section-title">{plan.minimumFloor5Min.title}</h3>
              <ol className="reason-list" style={{ color: 'var(--text-primary)' }}>
                {plan.minimumFloor5Min.steps.map((st, idx) => (
                  <li key={idx} style={{ marginBottom: 7 }}>
                    {st}
                  </li>
                ))}
              </ol>
            </div>
          ) : activeExercises.length === 0 ? (
            <div className="card card-cyan">
              <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
                Recuperação Ativa &amp; Alívio
              </div>
              <h3 className="section-title">{plan.mentalProtocol.title}</h3>
              <ul className="reason-list" style={{ color: 'var(--text-primary)' }}>
                {plan.mentalProtocol.instructions.map((ins, i) => (
                  <li key={i}>{ins}</li>
                ))}
              </ul>
            </div>
          ) : (
            activeExercises.map((ex, idx) => {
              const rows = draftSets[ex.exerciseId] ?? [];
              const fullDef = getExerciseById(ex.exerciseId);
              return (
                <div className="card" key={`${ex.exerciseId}_${idx}`}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: 10,
                      marginBottom: 8,
                    }}
                  >
                    <div>
                      <div className="section-kicker">
                        Exercício {idx + 1} • {ex.sets} séries de {ex.targetReps}
                      </div>
                      <h3 className="section-title" style={{ fontSize: 16.5 }}>
                        {ex.name}
                      </h3>
                    </div>

                    {fullDef && (
                      <button
                        type="button"
                        className="btn btn-ghost"
                        style={{
                          minHeight: 38,
                          padding: '6px 12px',
                          fontSize: 12.5,
                          borderColor: 'rgba(245,158,11,0.45)',
                          color: '#fbbf24',
                          flexShrink: 0,
                        }}
                        onClick={() => {
                          triggerHaptic('light');
                          setDemoExercise(fullDef);
                        }}
                      >
                        <PlayCircle size={15} /> Ver Demonstração
                      </button>
                    )}
                  </div>

                  {ex.substitutedReason && (
                    <div
                      style={{
                        padding: '8px 11px',
                        borderRadius: 10,
                        background: 'var(--cyan-soft)',
                        border: '1px solid rgba(6,182,212,0.35)',
                        fontSize: 12.3,
                        color: '#67e8f9',
                        marginBottom: 10,
                        display: 'flex',
                        gap: 7,
                        alignItems: 'center',
                      }}
                    >
                      <ShieldAlert size={15} />
                      <span>{ex.substitutedReason}</span>
                    </div>
                  )}

                  {fullDef && (
                    <div
                      style={{
                        padding: '9px 11px',
                        borderRadius: 10,
                        background: 'var(--bg-elevated)',
                        fontSize: 12.8,
                        marginBottom: 10,
                      }}
                    >
                      <strong style={{ color: '#fbbf24' }}>
                        <Sparkles size={12} style={{ verticalAlign: 'middle' }} /> Dica Simples:
                      </strong>{' '}
                      {fullDef.externalFocusCue}
                    </div>
                  )}

                  <div
                    className="set-row"
                    style={{
                      fontSize: 11.2,
                      color: 'var(--text-muted)',
                      fontWeight: 700,
                      marginTop: 6,
                    }}
                  >
                    <div>Série</div>
                    <div style={{ textAlign: 'center' }}>Peso (kg)</div>
                    <div style={{ textAlign: 'center' }}>Repetições</div>
                    <div style={{ textAlign: 'center' }}>Reserva</div>
                    <div style={{ textAlign: 'center' }}>Feito</div>
                  </div>

                  {rows.map((r, sIdx) => (
                    <div className="set-row" key={sIdx}>
                      <div className="mono muted" style={{ fontWeight: 800 }}>
                        #{sIdx + 1}
                      </div>
                      <input
                        type="number"
                        className="set-input"
                        value={r.loadKg}
                        onChange={(e) => updateRow(ex.exerciseId, sIdx, { loadKg: e.target.value })}
                      />
                      <input
                        type="number"
                        className="set-input"
                        value={r.reps}
                        onChange={(e) => updateRow(ex.exerciseId, sIdx, { reps: e.target.value })}
                      />
                      <input
                        type="number"
                        className="set-input"
                        value={r.rir}
                        onChange={(e) => updateRow(ex.exerciseId, sIdx, { rir: e.target.value })}
                      />
                      <button
                        type="button"
                        className={`btn ${r.done ? 'btn-emerald' : 'btn-ghost'}`}
                        style={{ minHeight: 38, padding: 0 }}
                        onClick={() =>
                          updateRow(
                            ex.exerciseId,
                            sIdx,
                            { done: !r.done },
                            !r.done ? 90 : undefined,
                          )
                        }
                      >
                        <Check size={16} />
                      </button>
                    </div>
                  ))}
                  <div className="muted" style={{ fontSize: 11.5, marginTop: 6 }}>
                    💡 <em>Reserva:</em> quantas repetições você ainda aguentaria fazer com postura
                    limpa (meta hoje: {ex.targetRir}).
                  </div>
                </div>
              );
            })
          )}

          {/* FINALIZAR SESSAO DE TREINO */}
          <div className="card card-emerald">
            <div className="section-kicker" style={{ color: '#34d399' }}>
              Finalizar Treino do Dia
            </div>
            <h3 className="section-title">Salvar Progresso</h3>

            <div className="grid-2" style={{ marginTop: 10 }}>
              <div className="field">
                <label>Quantos minutos durou?</label>
                <input
                  type="number"
                  className="input"
                  value={sessionMinutes}
                  onChange={(e) => setSessionMinutes(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Quão pesado foi no geral? (Nota {sessionRpe}/10)</label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={sessionRpe}
                  onChange={(e) => setSessionRpe(Number(e.target.value))}
                  style={{ accentColor: 'var(--emerald)', marginTop: 10 }}
                />
              </div>
            </div>

            <button className="btn btn-emerald btn-block" onClick={handleFinishSession}>
              <CheckCircle2 size={18} /> Concluir e Salvar Treino
            </button>
          </div>
        </>
      )}

      {/* BIBLIOTECA VISUAL COMPLETA DE EXERCICIOS ANIMADOS */}
      <div className="card">
        <div className="section-header" style={{ marginBottom: 8 }}>
          <div>
            <div className="section-kicker">Biblioteca Visual Interativa</div>
            <h3 className="section-title" style={{ fontSize: 16 }}>
              Explorar Todos os {EXERCISE_CATALOG.length} Exercícios Animados
            </h3>
          </div>
          <button
            type="button"
            className="btn btn-ghost"
            style={{ minHeight: 38, fontSize: 12.5 }}
            onClick={() => setShowCatalogBrowser((v) => !v)}
          >
            <BookOpen size={15} /> {showCatalogBrowser ? 'Recolher' : 'Abrir Biblioteca'}
          </button>
        </div>

        {showCatalogBrowser && (
          <div>
            <div className="chip-row" style={{ marginBottom: 12 }}>
              {(
                [
                  { id: 'TODOS', label: 'Todos' },
                  { id: 'CALISTENIA', label: 'Peso do Corpo' },
                  { id: 'CASA', label: 'Em Casa' },
                  { id: 'ACADEMIA', label: 'Academia' },
                ] as const
              ).map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={`chip ${catalogFilter === f.id ? 'chip-active' : ''}`}
                  onClick={() => setCatalogFilter(f.id)}
                >
                  {f.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filteredCatalog.map((item) => (
                <div
                  key={item.id}
                  className="metric-box"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 13.8 }}>{item.name}</div>
                    <div className="muted" style={{ fontSize: 12 }}>
                      {item.musclesWorked.join(' • ')}
                    </div>
                  </div>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    style={{
                      minHeight: 36,
                      padding: '6px 11px',
                      fontSize: 12,
                      color: '#fbbf24',
                      flexShrink: 0,
                    }}
                    onClick={() => {
                      triggerHaptic('light');
                      setDemoExercise(item);
                    }}
                  >
                    <PlayCircle size={14} /> Ver
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
};
