import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BookOpen,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Coffee,
  Compass,
  Droplets,
  Dumbbell,
  Flame,
  GraduationCap,
  Moon,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { addDaysToBioDay } from '../engine/stateEngine';
import { selectDailyRecommendedTeaching } from '../engine/teachingsCatalog';
import {
  ChessVaultData,
  DailyCheckIn,
  EveningReflectionEntry,
  JointRegion,
  PainKind,
  PrescribedDayPlan,
  TeachingLesson,
  TeachingProgressEntry,
  UserProfile,
  VaultState,
} from '../engine/types';
import { playTacticalChime } from '../services/audioBiofeedback';
import { triggerHaptic } from '../services/vaultStorage';
import { TeachingLessonModal } from './TeachingLessonModal';
import { DailySummary } from './DailySummary';
import { CheckInReminder } from './CheckInReminder';

interface Props {
  bioDayId: string;
  profile: UserProfile;
  existingCheckIn?: DailyCheckIn;
  plan: PrescribedDayPlan | null;
  amccCompletedToday: boolean;
  restConfirmedToday: boolean;
  teachingProgress: Record<string, TeachingProgressEntry>;
  completedFieldMissions?: Record<string, string>;
  eveningReflections?: Record<string, EveningReflectionEntry>;
  onSaveCheckIn: (checkIn: DailyCheckIn) => void;
  onSaveEveningReflection?: (entry: EveningReflectionEntry) => void;
  onConfirmRestDay: () => void;
  onCompleteAmcc: (title: string, description: string) => void;
  onCompleteLessonQuiz: (lesson: TeachingLesson, wasCorrect: boolean) => void;
  onToggleFieldMission: (lessonId: string) => void;
  onGoToWorkout: () => void;
  onGoToCortex: () => void;
  onGoToAcademy: () => void;
  onGoToSimulator: () => void;
  chessState?: ChessVaultData;
  onGoToChess?: () => void;
  vault: VaultState;
  onUpdateVault: (next: VaultState) => void;
}

const JOINT_LABELS: { id: JointRegion; label: string }[] = [
  { id: 'OMBRO', label: 'Ombro' },
  { id: 'COTOVELO_PUNHO', label: 'Cotovelo / Punho' },
  { id: 'LOMBAR', label: 'Coluna Lombar' },
  { id: 'QUADRIL', label: 'Quadril' },
  { id: 'JOELHO', label: 'Joelho' },
  { id: 'TORNOZELO_AQUILES', label: 'Tornozelo' },
];

export const CommandTab: React.FC<Props> = ({
  bioDayId,
  profile,
  existingCheckIn,
  plan,
  amccCompletedToday,
  restConfirmedToday,
  teachingProgress,
  completedFieldMissions = {},
  eveningReflections = {},
  onSaveCheckIn,
  onSaveEveningReflection,
  onConfirmRestDay,
  onCompleteAmcc,
  onCompleteLessonQuiz,
  onToggleFieldMission,
  onGoToWorkout,
  onGoToCortex,
  onGoToAcademy,
  onGoToSimulator,
  chessState,
  onGoToChess,
  vault,
  onUpdateVault,
}) => {
  const [editingCheckIn, setEditingCheckIn] = useState(!existingCheckIn);
  const [showScienceXray, setShowScienceXray] = useState(false);
  const [openDailyLesson, setOpenDailyLesson] = useState(false);

  const yesterdayId = addDaysToBioDay(bioDayId, -1);
  const yesterdayReflection = eveningReflections[yesterdayId];
  const todayReflection = eveningReflections[bioDayId];

  const [gratitudeNote, setGratitudeNote] = useState(todayReflection?.gratitudeNote ?? '');
  const [lessonLearnedToday, setLessonLearnedToday] = useState(
    todayReflection?.lessonLearnedToday ?? '',
  );
  const [tomorrowTopPriority, setTomorrowTopPriority] = useState(
    todayReflection?.tomorrowTopPriority ?? '',
  );
  const [releasedResentment, setReleasedResentment] = useState(
    todayReflection?.releasedResentment ?? true,
  );
  const [eveningSavedToast, setEveningSavedToast] = useState(false);

  useEffect(() => {
    setGratitudeNote(todayReflection?.gratitudeNote ?? '');
    setLessonLearnedToday(todayReflection?.lessonLearnedToday ?? '');
    setTomorrowTopPriority(todayReflection?.tomorrowTopPriority ?? '');
    setReleasedResentment(todayReflection?.releasedResentment ?? true);
    setEveningSavedToast(false);
  }, [bioDayId, todayReflection?.timestampMs]);

  const recommendedTeaching = selectDailyRecommendedTeaching(
    teachingProgress,
    bioDayId,
    plan?.readiness.zone,
  );

  const [sleepHours, setSleepHours] = useState(
    String(existingCheckIn?.sleepHours ?? profile.targetSleepHours),
  );
  const [sleepQuality, setSleepQuality] = useState<number>(existingCheckIn?.sleepQuality ?? 5);
  const [energyLevel, setEnergyLevel] = useState<number>(existingCheckIn?.energyLevel ?? 5);
  const [mentalCalm, setMentalCalm] = useState<number>(existingCheckIn?.mentalCalm ?? 5);
  const [muscularRecovery, setMuscularRecovery] = useState<number>(
    existingCheckIn?.muscularRecovery ?? 5,
  );
  const [painKind, setPainKind] = useState<PainKind>(existingCheckIn?.painKind ?? 'NENHUMA');
  const [painJoints, setPainJoints] = useState<JointRegion[]>(existingCheckIn?.painJoints ?? []);
  const [viralOrFeverSymptoms, setViralOrFeverSymptoms] = useState(
    existingCheckIn?.viralOrFeverSymptoms ?? false,
  );
  const [externalLifeStressEvent, setExternalLifeStressEvent] = useState(
    existingCheckIn?.externalLifeStressEvent ?? false,
  );
  const [availableMinutesToday, setAvailableMinutesToday] = useState<string>(
    existingCheckIn?.availableMinutesToday ? String(existingCheckIn.availableMinutesToday) : '',
  );

  const toggleJoint = (j: JointRegion) => {
    triggerHaptic('light');
    setPainJoints((prev) => (prev.includes(j) ? prev.filter((x) => x !== j) : [...prev, j]));
  };

  const handleSubmit = () => {
    triggerHaptic('medium');
    const customMins = Number(availableMinutesToday);
    const ci: DailyCheckIn = {
      bioDayId,
      timestampMs: Date.now(),
      sleepHours: Math.max(0, Math.min(14, Number(sleepHours) || profile.targetSleepHours)),
      sleepQuality,
      energyLevel,
      mentalCalm,
      muscularRecovery,
      painKind,
      painJoints: painKind === 'ARTICULAR_TENDINEA_AGUDA' ? painJoints : [],
      viralOrFeverSymptoms,
      externalLifeStressEvent,
      availableMinutesToday:
        Number.isFinite(customMins) && customMins >= 5 ? Math.round(customMins) : undefined,
    };
    onSaveCheckIn(ci);
    setEditingCheckIn(false);
  };

  const renderScale = (
    label: string,
    lowHint: string,
    highHint: string,
    val: number,
    onChange: (n: number) => void,
  ) => (
    <div className="field" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label style={{ color: 'var(--text-primary)' }}>{label}</label>
        <span className="mono" style={{ fontSize: 12, color: '#fbbf24', fontWeight: 800 }}>
          Nota {val}/7
        </span>
      </div>
      <div className="scale-row">
        {[1, 2, 3, 4, 5, 6, 7].map((n) => (
          <button
            key={n}
            type="button"
            className={`scale-btn ${val === n ? 'scale-btn-active' : ''}`}
            onClick={() => {
              triggerHaptic('light');
              onChange(n);
            }}
          >
            {n}
          </button>
        ))}
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 11,
          color: 'var(--text-muted)',
        }}
      >
        <span>1 = {lowHint}</span>
        <span>7 = {highHint}</span>
      </div>
    </div>
  );

  const zoneColor =
    plan?.readiness.zone === 'VERDE'
      ? '#10b981'
      : plan?.readiness.zone === 'VERMELHO'
        ? '#ef4444'
        : '#f59e0b';

  const zoneCardClass =
    plan?.readiness.zone === 'VERDE'
      ? 'card card-emerald'
      : plan?.readiness.zone === 'VERMELHO'
        ? 'card card-crimson'
        : 'card card-amber';

  const friendlyHeadline =
    plan?.readiness.zone === 'VERDE'
      ? 'Pronto para Evoluir com Segurança'
      : plan?.readiness.zone === 'VERMELHO'
        ? 'Dia de Recuperação & Proteção'
        : 'Ritmo Moderado & Inteligente';

  const friendlySub =
    plan?.readiness.zone === 'VERDE'
      ? 'Sua recuperação está ótima. Hoje é dia de progredir mantendo técnica limpa.'
      : plan?.readiness.zone === 'VERMELHO'
        ? 'Seu corpo sinalizou alerta ou sobrecarga. Recuperar hoje acelera seus ganhos de amanhã.'
        : 'Ajustamos automaticamente a quantidade de séries para você render bem sem se desgastar.';

  const ringRadius = 34;
  const ringCircumference = 2 * Math.PI * ringRadius;
  const ringOffset = plan
    ? ringCircumference * (1 - Math.min(100, Math.max(5, plan.readiness.score)) / 100)
    : ringCircumference;

  return (
    <>
        <CheckInReminder bioDayId={bioDayId} vault={vault} onUpdateVault={onUpdateVault} />

      <DailySummary
        bioDayId={bioDayId}
        vault={vault}
        onUpdateVault={onUpdateVault}
      />

      {openDailyLesson && (
        <TeachingLessonModal
          lesson={recommendedTeaching.lesson}
          existingProgress={teachingProgress[recommendedTeaching.lesson.id]}
          fieldMissionDone={Boolean(completedFieldMissions[recommendedTeaching.lesson.id])}
          onCompleteQuiz={onCompleteLessonQuiz}
          onToggleFieldMission={onToggleFieldMission}
          onClose={() => setOpenDailyLesson(false)}
        />
      )}

      {/* ALAVANCA Nº 1 HERDADA DO DESCARREGAMENTO PRE-SONO DE ONTEM (SCULLIN, 2018) */}
      {yesterdayReflection?.tomorrowTopPriority && (
        <div
          className="card card-emerald"
          style={{ padding: '12px 14px', marginBottom: 12 }}
        >
          <div className="section-kicker" style={{ color: '#34d399' }}>
            Missão nº 1 Definida por Você Ontem à Noite
          </div>
          <div style={{ fontWeight: 800, fontSize: 14.2, marginTop: 3 }}>
            🎯 {yesterdayReflection.tomorrowTopPriority}
          </div>
        </div>
      )}

      {/* PASSO 1: CHECK-IN AMIGAVEL DE 20 SEGUNDOS */}
      <div className="card">
        <div className="section-header">
          <div>
            <div className="section-kicker">Seu Estado Hoje • {bioDayId}</div>
            <h2 className="section-title">
              {existingCheckIn && !editingCheckIn
                ? 'Resumo do Seu Dia'
                : 'Como você está hoje? (20s)'}
            </h2>
          </div>
          {existingCheckIn && !editingCheckIn && (
            <button className="btn btn-ghost" onClick={() => setEditingCheckIn(true)}>
              Atualizar
            </button>
          )}
        </div>

        {editingCheckIn ? (
          <div>
            <div className="grid-2">
              <div className="field">
                <label>
                  <Moon size={13} style={{ verticalAlign: 'middle' }} /> Quantas horas dormiu?
                </label>
                <input
                  type="number"
                  step="0.5"
                  className="input"
                  value={sleepHours}
                  onChange={(e) => setSleepHours(e.target.value)}
                />
              </div>
              <div className="field">
                <label>
                  <Clock size={13} style={{ verticalAlign: 'middle' }} /> Tempo disponível hoje
                </label>
                <input
                  type="number"
                  className="input"
                  placeholder={`Padrão (${profile.weekdayFreeMinutes} min)`}
                  value={availableMinutesToday}
                  onChange={(e) => setAvailableMinutesToday(e.target.value)}
                />
              </div>
            </div>

            <div className="chip-row" style={{ marginBottom: 14 }}>
              {[
                { label: 'Só tenho 10 min', val: '10' },
                { label: 'Dia corrido (15 min)', val: '15' },
                { label: '30 min', val: '30' },
                { label: 'Tempo normal', val: '' },
              ].map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  className={`chip ${availableMinutesToday === preset.val ? 'chip-active' : ''}`}
                  onClick={() => {
                    triggerHaptic('light');
                    setAvailableMinutesToday(preset.val);
                  }}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {renderScale(
              'Qualidade do Sono',
              'Acordei quebrado',
              'Sono profundo',
              sleepQuality,
              setSleepQuality,
            )}
            {renderScale(
              'Nível de Energia',
              'Sem bateria',
              'Disposição total',
              energyLevel,
              setEnergyLevel,
            )}
            {renderScale(
              'Calma & Foco Mental',
              'Mente agitada',
              'Calmo e focado',
              mentalCalm,
              setMentalCalm,
            )}
            {renderScale(
              'Recuperação do Corpo',
              'Muito dolorido',
              '100% novo',
              muscularRecovery,
              setMuscularRecovery,
            )}

            <div className="field" style={{ marginTop: 12 }}>
              <label>Está sentindo alguma dor hoje?</label>
              <div className="chip-row">
                <button
                  type="button"
                  className={`chip ${painKind === 'NENHUMA' ? 'chip-active' : ''}`}
                  onClick={() => setPainKind('NENHUMA')}
                >
                  Nenhuma dor
                </button>
                <button
                  type="button"
                  className={`chip ${painKind === 'DOMS_MUSCULAR' ? 'chip-active' : ''}`}
                  onClick={() => setPainKind('DOMS_MUSCULAR')}
                >
                  Dor muscular comum de treino
                </button>
                <button
                  type="button"
                  className={`chip ${
                    painKind === 'ARTICULAR_TENDINEA_AGUDA' ? 'chip-danger-active' : ''
                  }`}
                  onClick={() => setPainKind('ARTICULAR_TENDINEA_AGUDA')}
                >
                  Fisgada em articulação / tendão
                </button>
              </div>
            </div>

            {painKind === 'ARTICULAR_TENDINEA_AGUDA' && (
              <div
                style={{
                  padding: 13,
                  borderRadius: 14,
                  background: 'var(--crimson-soft)',
                  border: '1px solid rgba(239,68,68,0.35)',
                  marginBottom: 12,
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8 }}>
                  Onde está incomodando? (Vamos trocar esses exercícios automaticamente):
                </div>
                <div className="chip-row">
                  {JOINT_LABELS.map((j) => (
                    <button
                      key={j.id}
                      type="button"
                      className={`chip ${
                        painJoints.includes(j.id) ? 'chip-danger-active' : ''
                      }`}
                      onClick={() => toggleJoint(j.id)}
                    >
                      {j.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={viralOrFeverSymptoms}
                onChange={(e) => setViralOrFeverSymptoms(e.target.checked)}
              />
              <div>
                <strong>Estou com febre, gripe forte ou infecção hoje</strong>
                <div className="muted">Pausa automática de segurança para proteger o coração.</div>
              </div>
            </label>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={externalLifeStressEvent}
                onChange={(e) => setExternalLifeStressEvent(e.target.checked)}
              />
              <div>
                <strong>Dia de estresse muito pesado fora do treino (trabalho/família/prova)</strong>
                <div className="muted">Suaviza o treino para não esgotar sua energia mental.</div>
              </div>
            </label>

            <button className="btn btn-primary btn-block" onClick={handleSubmit}>
              <Activity size={17} /> Montar Meu Plano Ideal de Hoje
            </button>
          </div>
        ) : (
          <div className="grid-4">
            <div className="metric-box">
              <div className="metric-label">Sono</div>
              <div className="metric-value">{existingCheckIn?.sleepHours}h</div>
              <div className="metric-sub">Nota {existingCheckIn?.sleepQuality}/7</div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Energia</div>
              <div className="metric-value">{existingCheckIn?.energyLevel}/7</div>
              <div className="metric-sub">Calma {existingCheckIn?.mentalCalm}/7</div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Músculos</div>
              <div className="metric-value">{existingCheckIn?.muscularRecovery}/7</div>
              <div className="metric-sub">
                {existingCheckIn?.painKind === 'ARTICULAR_TENDINEA_AGUDA'
                  ? `Protegendo (${existingCheckIn.painJoints.length})`
                  : existingCheckIn?.painKind === 'DOMS_MUSCULAR'
                    ? 'Dor leve normal'
                    : 'Sem dor'}
              </div>
            </div>
            <div className="metric-box">
              <div className="metric-label">Hoje</div>
              <div className="metric-value" style={{ fontSize: 15 }}>
                {restConfirmedToday ? 'Descanso' : `Treino ${plan?.queueSlot ?? 'A'}`}
              </div>
              <div className="metric-sub">No seu ritmo</div>
            </div>
          </div>
        )}
      </div>

      {/* PASSO 2: MEDIDOR VISUAL DE PRONTIDAO + ACAO CLARA */}
      {plan && (
        <>
          <div className={zoneCardClass}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                marginBottom: 14,
              }}
            >
              {/* Anel SVG de Prontidao */}
              <div style={{ position: 'relative', width: 84, height: 84, flexShrink: 0 }}>
                <svg width="84" height="84" viewBox="0 0 84 84">
                  <circle
                    cx="42"
                    cy="42"
                    r={ringRadius}
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="7"
                  />
                  <circle
                    cx="42"
                    cy="42"
                    r={ringRadius}
                    fill="none"
                    stroke={zoneColor}
                    strokeWidth="7"
                    strokeLinecap="round"
                    strokeDasharray={ringCircumference}
                    strokeDashoffset={ringOffset}
                    transform="rotate(-90 42 42)"
                  />
                </svg>
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <span className="mono" style={{ fontSize: 20, fontWeight: 900 }}>
                    {plan.readiness.score}
                  </span>
                  <span style={{ fontSize: 9.5, color: 'var(--text-secondary)', fontWeight: 700 }}>
                    PRONTIDÃO
                  </span>
                </div>
              </div>

              <div>
                <span
                  className={`badge ${
                    plan.readiness.zone === 'VERDE'
                      ? 'badge-green'
                      : plan.readiness.zone === 'VERMELHO'
                        ? 'badge-red'
                        : 'badge-yellow'
                  }`}
                >
                  Sinal {plan.readiness.zone}
                </span>
                <h2 className="section-title" style={{ marginTop: 6 }}>
                  {friendlyHeadline}
                </h2>
                <p className="muted" style={{ margin: '4px 0 0', fontSize: 13.2 }}>
                  {friendlySub}
                </p>
              </div>
            </div>

            {plan.readiness.maskedFatigueDetected && (
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: 12,
                  background: 'var(--amber-soft)',
                  border: '1px solid var(--amber)',
                  fontSize: 12.8,
                  marginBottom: 12,
                  display: 'flex',
                  gap: 8,
                  alignItems: 'center',
                }}
              >
                <AlertTriangle size={17} color="var(--amber)" />
                <span>
                  <strong>Proteção Inteligente:</strong> notamos queda nas repetições dos últimos
                  treinos e aliviamos o volume hoje para seu corpo supercompensar.
                </span>
              </div>
            )}

            {plan.readiness.activeVetoes.length > 0 && (
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: 12,
                  background: 'var(--crimson-soft)',
                  border: '1px solid rgba(239,68,68,0.4)',
                  fontSize: 12.8,
                  marginBottom: 12,
                }}
              >
                <strong>Cuidados Ativos Hoje:</strong>
                <ul className="reason-list" style={{ marginTop: 4 }}>
                  {plan.readiness.activeVetoes.map((v, idx) => (
                    <li key={idx}>{v}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 3 METAS PRATICAS E SIMPLES DO DIA */}
            <div className="grid-3">
              <div className="metric-box">
                <div className="metric-label">Treino Hoje</div>
                <div className="metric-value" style={{ fontSize: 16 }}>
                  ~{plan.estimatedMinutes} min
                </div>
                <div className="metric-sub">
                  Pare faltando {plan.readiness.intensityRirFloor} reps
                </div>
              </div>
              <div className="metric-box">
                <div className="metric-label">Meta Proteína</div>
                <div className="metric-value" style={{ fontSize: 16 }}>
                  {plan.readiness.proteinTargetGrams[0]}–{plan.readiness.proteinTargetGrams[1]}g
                </div>
                <div className="metric-sub">Ao longo do dia</div>
              </div>
              <div className="metric-box">
                <div className="metric-label">
                  <Droplets size={11} /> Água &amp; <Coffee size={11} /> Café
                </div>
                <div className="metric-value" style={{ fontSize: 15 }}>
                  {plan.readiness.waterTargetLiters}L • {plan.readiness.caffeineCutoffTime}
                </div>
                <div className="metric-sub">Último café até {plan.readiness.caffeineCutoffTime}</div>
              </div>
            </div>

            {/* BOTAO DE PROGRESSIVE DISCLOSURE: RAIO-X CIENTIFICO */}
            <button
              type="button"
              className="btn btn-ghost btn-block"
              style={{ marginTop: 12, minHeight: 38, fontSize: 12.5 }}
              onClick={() => setShowScienceXray((s) => !s)}
            >
              {showScienceXray ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              {showScienceXray
                ? 'Ocultar Raio-X Científico'
                : 'Ver Raio-X Científico (Por que o app decidiu isso?)'}
            </button>

            {showScienceXray && (
              <div className="science-drawer">
                <div className="grid-3" style={{ marginBottom: 8 }}>
                  <div>
                    <div className="metric-label">Carga Aguda/Crônica</div>
                    <div className="mono" style={{ fontWeight: 800 }}>
                      {Math.round(plan.readiness.acuteEwma)} /{' '}
                      {Math.round(plan.readiness.uncoupledChronicEwma)} AU
                    </div>
                  </div>
                  <div>
                    <div className="metric-label">Monotonia Foster</div>
                    <div className="mono" style={{ fontWeight: 800 }}>
                      {plan.readiness.regularizedMonotony.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="metric-label">Dose de Volume</div>
                    <div className="mono" style={{ fontWeight: 800 }}>
                      {Math.round(plan.readiness.volumeMultiplier * 100)}%
                    </div>
                  </div>
                </div>
                <ul className="reason-list" style={{ marginTop: 4 }}>
                  {plan.readiness.glassBoxReasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="grid-2" style={{ marginTop: 14 }}>
              <button className="btn btn-primary" onClick={onGoToWorkout}>
                <Dumbbell size={17} /> Ir para o Treino ({plan.estimatedMinutes}m)
              </button>
              <button className="btn btn-ghost" onClick={onGoToCortex}>
                <Brain size={17} /> Desafios Mentais
              </button>
            </div>

            {!restConfirmedToday && (
              <button
                className="btn btn-ghost btn-block"
                style={{ marginTop: 8, fontSize: 12.5, minHeight: 40 }}
                onClick={() => {
                  triggerHaptic('light');
                  onConfirmRestDay();
                }}
              >
                Hoje é meu Dia de Descanso Planejado (Marcar descanso sem perder ritmo)
              </button>
            )}
          </div>

          {/* MENSAGEM DO MENTOR & PEQUENA VITORIA DO DIA */}
          <div className="card card-amber">
            <div className="section-header">
              <div>
                <div className="section-kicker">Mentor do Dia • {plan.pantheon.archetypeTitle}</div>
                <h2 className="section-title">{plan.pantheon.mentorName}</h2>
              </div>
              <Flame size={20} color="var(--amber)" />
            </div>

            <p style={{ margin: '0 0 14px', fontSize: 14.5, lineHeight: 1.58 }}>
              {plan.pantheon.tacticalDirective}
            </p>

            <div
              style={{
                padding: 14,
                borderRadius: 14,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-strong)',
              }}
            >
              <div
                style={{
                  fontSize: 11.5,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  color: '#fbbf24',
                  marginBottom: 4,
                }}
              >
                Desafio Rápido de Disciplina ({plan.pantheon.amccChallenge.durationMin} min) —{' '}
                {plan.pantheon.amccChallenge.title}
              </div>
              <div style={{ fontSize: 13.8, marginBottom: 12 }}>
                {plan.pantheon.amccChallenge.description}
              </div>

              {amccCompletedToday ? (
                <div className="badge badge-green">
                  <CheckCircle2 size={13} /> Vitória Registrada no Seu Cofre Hoje!
                </div>
              ) : (
                <button
                  className="btn btn-emerald btn-block"
                  onClick={() => {
                    triggerHaptic('success');
                    playTacticalChime('VICTORY');
                    onCompleteAmcc(
                      plan.pantheon.amccChallenge.title,
                      plan.pantheon.amccChallenge.description,
                    );
                  }}
                >
                  <ShieldAlert size={16} /> Concluí Este Desafio — Guardar Vitória
                </button>
              )}
            </div>

            {plan.pantheon.variableRewardUnlocked && (
              <div
                style={{
                  marginTop: 12,
                  padding: 12,
                  borderRadius: 12,
                  background: 'var(--violet-soft)',
                  border: '1px solid rgba(139,92,246,0.38)',
                }}
              >
                <div
                  style={{
                    fontSize: 11.5,
                    fontWeight: 800,
                    color: '#c4b5fd',
                    marginBottom: 4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <Sparkles size={14} /> {plan.pantheon.variableRewardUnlocked.title}
                </div>
                <div style={{ fontSize: 13.2, color: '#ede9fe' }}>
                  {plan.pantheon.variableRewardUnlocked.scientificInsight}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* ENSINAMENTO RECOMENDADO DO DIA (ARVORE 4C/ID + REPETICAO ESPACADA) */}
      <div className="card card-cyan">
        <div className="section-header">
          <div>
            <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
              {recommendedTeaching.reasonTag} • ~{recommendedTeaching.lesson.readTimeSec}s
            </div>
            <h2 className="section-title">{recommendedTeaching.lesson.title}</h2>
          </div>
          <GraduationCap size={22} color="var(--cyan)" />
        </div>

        <div className="muted" style={{ marginBottom: 12 }}>
          <strong>{recommendedTeaching.lesson.mentorName}:</strong>{' '}
          {recommendedTeaching.lesson.subtitle}.
        </div>

        <div className="grid-2" style={{ marginBottom: 10 }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              triggerHaptic('light');
              setOpenDailyLesson(true);
            }}
          >
            <BookOpen size={16} /> Abrir Lição do Dia
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              triggerHaptic('light');
              onGoToAcademy();
            }}
          >
            <GraduationCap size={16} /> Árvore (200 Lições)
          </button>
        </div>

        <button
          type="button"
          className="btn btn-emerald btn-block"
          onClick={() => {
            triggerHaptic('medium');
            onGoToSimulator();
          }}
        >
          <Compass size={16} /> Simulador Vivo: &ldquo;Jovem do Zero ao Mestre&rdquo;
        </button>

        {onGoToChess && (
          <div
            style={{
              marginTop: 10,
              padding: '10px 12px',
              borderRadius: 10,
              background: 'rgba(129, 182, 76, 0.12)',
              border: '1px solid rgba(129, 182, 76, 0.35)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 10,
              flexWrap: 'wrap',
            }}
          >
            <div style={{ fontSize: 12.5 }}>
              <div style={{ fontWeight: 900, color: '#d9f99d' }}>
                ♟️ Arena de Xadrez Chess.com 2.0 • Problema Diário &amp; Chess960
              </div>
              <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>
                Elo Jogo: <strong>{chessState?.playRating ?? 1000}</strong> • Tática:{' '}
                <strong>{chessState?.puzzleRating ?? 1000}</strong> • Visão 30s:{' '}
                <strong>{chessState?.visionBestScore ?? 0}</strong> • Finais:{' '}
                <strong>{(chessState?.completedEndgameIds ?? []).length}/8</strong>
              </div>
            </div>
            <button
              type="button"
              className="btn btn-primary"
              style={{ padding: '7px 12px', fontSize: 12 }}
              onClick={() => {
                triggerHaptic('light');
                onGoToChess();
              }}
            >
              ♟️ Abrir Xadrez
            </button>
          </div>
        )}
      </div>

      {/* FECHAMENTO DA NOITE: EXAME DE CONSCIENCIA, GRATIDAO & DESCARREGAMENTO PRE-SONO */}
      <div className="card card-amber">
        <div className="section-header">
          <div>
            <div className="section-kicker">
              Ritual Noturno de 90s • Salmo 4:8 • Efésios 4:26 • Polissonografia (Scullin, 2018)
            </div>
            <h2 className="section-title">Fechamento da Noite &amp; Paz no Leito</h2>
          </div>
          <Moon size={22} color="var(--amber)" />
        </div>

        <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
          Codificar a lição do dia acelera o aprendizado em <strong>+22,8%</strong> (Di Stefano et
          al., Harvard) e descarregar a prioridade de amanhã no papel reduz o tempo para pegar no
          sono em <strong>~9 minutos</strong> (Scullin et al., 2018)!
        </p>

        <div className="field">
          <label>1. Gratidão Real de Hoje (1 bênção concreta — 1 Ts 5:18)</label>
          <input
            className="input"
            placeholder="Ex.: Saúde para treinar hoje, apoio da família, clareza num problema..."
            value={gratitudeNote}
            onChange={(e) => setGratitudeNote(e.target.value)}
          />
        </div>

        <div className="field">
          <label>2. Exame Honesto: o que aprendi hoje ou ajustarei amanhã sem culpa?</label>
          <input
            className="input"
            placeholder="Ex.: Rendi muito mais estudando sem celular; amanhã corto café às 13h..."
            value={lessonLearnedToday}
            onChange={(e) => setLessonLearnedToday(e.target.value)}
          />
        </div>

        <div className="field">
          <label>3. Descarregamento Pré-Sono: qual é a Alavanca nº 1 de amanhã?</label>
          <input
            className="input"
            placeholder="Ex.: Resolver 5 exercícios de Matemática às 07h30 antes de abrir mensagens"
            value={tomorrowTopPriority}
            onChange={(e) => setTomorrowTopPriority(e.target.value)}
          />
        </div>

        <label className="check-toggle" style={{ marginBottom: 12 }}>
          <input
            type="checkbox"
            checked={releasedResentment}
            onChange={(e) => setReleasedResentment(e.target.checked)}
          />
          <div>
            <strong>“Não se ponha o sol sobre a vossa ira” (Efésios 4:26)</strong>
            <div className="muted">
              Decido soltar mágoas e irritações de hoje para dormir com a consciência limpa e em paz.
            </div>
          </div>
        </label>

        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={() => {
            if (
              !gratitudeNote.trim() &&
              !lessonLearnedToday.trim() &&
              !tomorrowTopPriority.trim()
            ) {
              return;
            }
            triggerHaptic('success');
            playTacticalChime('VICTORY');
            onSaveEveningReflection?.({
              bioDayId,
              timestampMs: Date.now(),
              gratitudeNote: gratitudeNote.trim() || 'Grato por mais um dia de vida e aprendizado.',
              lessonLearnedToday:
                lessonLearnedToday.trim() || 'Constância fiel no pouco constrói a rocha.',
              tomorrowTopPriority:
                tomorrowTopPriority.trim() || 'Cumprir minha primeira hora focada sem distração.',
              releasedResentment,
            });
            setEveningSavedToast(true);
          }}
        >
          <Moon size={16} />{' '}
          {todayReflection || eveningSavedToast
            ? '✓ Noite Selada em Paz (Atualizar)'
            : 'Selar Fechamento da Noite & Desligar Mente'}
        </button>
      </div>
    </>
  );
};
