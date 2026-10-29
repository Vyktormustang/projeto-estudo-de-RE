import React, { useState } from 'react';
import { Flame, ShieldCheck, Brain, Sparkles, ArrowRight, ArrowLeft, PlayCircle } from 'lucide-react';
import { computeAdjustedProteinMassKg } from '../engine/stateEngine';
import {
  BiologicalSex,
  ClimateProfile,
  CommandVoice,
  EnergyGoal,
  EquipmentEnv,
  ExecutiveProfile,
  OccupationalDemand,
  ScheduleRegime,
  TrainingLevel,
  UserProfile,
} from '../engine/types';
import { triggerHaptic } from '../services/vaultStorage';

interface Props {
  initialProfile?: UserProfile | null;
  onComplete: (
    profile: UserProfile,
    firstIfThen?: {
      triggerSituation: string;
      shieldedAction: string;
      machiavelliPreCommitment: string;
    },
  ) => void;
  onLoadDemo?: () => void;
  onLoadZeroYouth?: () => void;
  onCancelEdit?: () => void;
}

export const OnboardingWizard: React.FC<Props> = ({
  initialProfile,
  onComplete,
  onLoadDemo,
  onLoadZeroYouth,
  onCancelEdit,
}) => {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  const [codename, setCodename] = useState(initialProfile?.codename ?? '');
  const [age, setAge] = useState(String(initialProfile?.age ?? 28));
  const [sex, setSex] = useState<BiologicalSex>(initialProfile?.sex ?? 'MASCULINO');
  const [weightKg, setWeightKg] = useState(String(initialProfile?.weightKg ?? 76));
  const [heightCm, setHeightCm] = useState(String(initialProfile?.heightCm ?? 175));
  const [level, setLevel] = useState<TrainingLevel>(initialProfile?.level ?? 'INICIANTE');
  const [equipment, setEquipment] = useState<EquipmentEnv>(initialProfile?.equipment ?? 'CASA');
  const [energyGoal, setEnergyGoal] = useState<EnergyGoal>(
    initialProfile?.energyGoal ?? 'MANUTENCAO_PERFORMANCE',
  );

  const [occupationalDemand, setOccupationalDemand] = useState<OccupationalDemand>(
    initialProfile?.occupationalDemand ?? 'SEDENTARIO_INTELECTUAL',
  );
  const [climate, setClimate] = useState<ClimateProfile>(
    initialProfile?.climate ?? 'CALOR_TROPICAL_UMIDO',
  );
  const [scheduleRegime, setScheduleRegime] = useState<ScheduleRegime>(
    initialProfile?.scheduleRegime ?? 'DIURNO_FIXO',
  );
  const [executiveProfile, setExecutiveProfile] = useState<ExecutiveProfile>(
    initialProfile?.executiveProfile ?? 'EQUILIBRADO',
  );
  const [weekdayFreeMinutes, setWeekdayFreeMinutes] = useState(
    String(initialProfile?.weekdayFreeMinutes ?? 40),
  );
  const [weekendFreeMinutes, setWeekendFreeMinutes] = useState(
    String(initialProfile?.weekendFreeMinutes ?? 60),
  );
  const [targetSleepHours, setTargetSleepHours] = useState(
    String(initialProfile?.targetSleepHours ?? 7.5),
  );
  const [usualWakeTime, setUsualWakeTime] = useState(initialProfile?.usualWakeTime ?? '06:30');
  const [usualBedTime, setUsualBedTime] = useState(initialProfile?.usualBedTime ?? '22:45');

  const [betaBlocker, setBetaBlocker] = useState(initialProfile?.pharma.betaBlocker ?? false);
  const [glp1Agonist, setGlp1Agonist] = useState(initialProfile?.pharma.glp1Agonist ?? false);
  const [adhdStimulant, setAdhdStimulant] = useState(initialProfile?.pharma.adhdStimulant ?? false);
  const [statin, setStatin] = useState(initialProfile?.pharma.statin ?? false);
  const [fluoroquinolone, setFluoroquinolone] = useState(
    initialProfile?.pharma.fluoroquinolone ?? false,
  );
  const [parqWarning, setParqWarning] = useState(initialProfile?.clinical.parqWarning ?? false);
  const [interoceptiveSensitive, setInteroceptiveSensitive] = useState(
    initialProfile?.clinical.interoceptiveSensitive ?? false,
  );
  const [bodyNeutralMode, setBodyNeutralMode] = useState(
    initialProfile?.clinical.bodyNeutralMode ?? false,
  );

  const [primaryGoalDomain, setPrimaryGoalDomain] = useState(
    initialProfile?.primaryGoalDomain ?? 'Estudo Profundo, Carreira & Raciocínio Técnico',
  );
  const [mainSaboteur, setMainSaboteur] = useState(
    initialProfile?.mainSaboteur ?? 'Uso de telas tarde da noite ou adiamento por cansaço',
  );
  const [commandVoice, setCommandVoice] = useState<CommandVoice>(
    initialProfile?.commandVoice ?? 'ADAPTATIVO',
  );

  const parsedW = Math.max(35, Math.min(260, Number(weightKg) || 76));
  const parsedH = Math.max(130, Math.min(230, Number(heightCm) || 175));
  const bmi = parsedW / Math.pow(parsedH / 100, 2);
  const adjMass = computeAdjustedProteinMassKg(parsedW, parsedH);

  const handleFinish = () => {
    triggerHaptic('success');
    const profile: UserProfile = {
      codename: codename.trim() || 'Operador',
      age: Math.max(14, Math.min(95, Math.round(Number(age) || 28))),
      sex,
      weightKg: parsedW,
      heightCm: parsedH,
      level,
      equipment,
      energyGoal,
      occupationalDemand,
      climate,
      scheduleRegime,
      executiveProfile,
      commandVoice,
      weekdayFreeMinutes: Math.max(10, Math.min(180, Math.round(Number(weekdayFreeMinutes) || 40))),
      weekendFreeMinutes: Math.max(10, Math.min(240, Math.round(Number(weekendFreeMinutes) || 60))),
      targetSleepHours: Math.max(5.5, Math.min(10, Number(targetSleepHours) || 7.5)),
      usualWakeTime: usualWakeTime || '06:30',
      usualBedTime: usualBedTime || '22:45',
      primaryGoalDomain: primaryGoalDomain.trim() || 'Maestria Pessoal & Foco',
      mainSaboteur: mainSaboteur.trim() || 'Procrastinação sob cansaço',
      pharma: {
        betaBlocker,
        glp1Agonist,
        adhdStimulant,
        statin,
        fluoroquinolone,
      },
      clinical: {
        parqWarning,
        bodyNeutralMode,
        interoceptiveSensitive,
      },
      createdAtIso: initialProfile?.createdAtIso ?? new Date().toISOString(),
    };

    const firstContract = !initialProfile
      ? {
          triggerSituation: `SE surgir o sabotador "${profile.mainSaboteur}"`,
          shieldedAction:
            'ENTÃO aciono imediatamente o Piso Inegociável de 5 minutos (vmPFC) sem negociar com o impulso.',
          machiavelliPreCommitment:
            'Ambiente preparado com antecedência para iniciar em menos de 60 segundos.',
        }
      : undefined;

    onComplete(profile, firstContract);
  };

  return (
    <div className="app-shell" style={{ paddingBottom: 32 }}>
      <div className="top-bar">
        <div className="brand-mark">
          <div className="brand-icon">
            <Flame size={20} />
          </div>
          <div>
            <div className="brand-title">FORJA — Sistema do Ápice</div>
            <div className="brand-sub">Configuração Rápida v35.0.0 • Passo {step}/4</div>
          </div>
        </div>
        {onCancelEdit && (
          <button className="btn btn-ghost" onClick={onCancelEdit}>
            Cancelar
          </button>
        )}
      </div>

      <div className="page-content">
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${step * 25}%` }} />
        </div>

        {!initialProfile && step === 1 && (onLoadDemo || onLoadZeroYouth) && (
          <div className="card card-cyan">
            <div className="section-kicker" style={{ color: 'var(--cyan)' }}>
              Atalhos Instantâneos • Escolha Seu Ponto de Partida
            </div>
            <p className="muted" style={{ margin: '4px 0 10px' }}>
              Configure seus dados abaixo em 1 minuto, ou inicie em 1 toque como um{' '}
              <strong>Jovem no Marco Zero (sem nenhuma habilidade)</strong> rumo à Maestria
              Universal:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {onLoadZeroYouth && (
                <button className="btn btn-emerald btn-block" onClick={onLoadZeroYouth}>
                  <Sparkles size={16} /> Iniciar como Jovem no Marco Zero (Dia 1)
                </button>
              )}
              {onLoadDemo && (
                <button className="btn btn-ghost btn-block" onClick={onLoadDemo}>
                  <PlayCircle size={17} /> Ver Exemplo com 18 Dias de Histórico
                </button>
              )}
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="card card-amber">
            <div className="section-header">
              <div>
                <div className="section-kicker">Etapa 1 de 4 • Biometria &amp; Ambiente</div>
                <h2 className="section-title">Quem entra na Forja hoje?</h2>
              </div>
              <Flame size={22} color="var(--amber)" />
            </div>

            <div className="field">
              <label>Nome ou Codinome Operacional</label>
              <input
                className="input"
                placeholder="Ex: Viktor, Operador 01..."
                value={codename}
                onChange={(e) => setCodename(e.target.value)}
              />
            </div>

            <div className="grid-2">
              <div className="field">
                <label>Idade (anos)</label>
                <input
                  type="number"
                  className="input"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Sexo Biológico (Referência Fisiológica)</label>
                <select
                  className="select"
                  value={sex}
                  onChange={(e) => setSex(e.target.value as BiologicalSex)}
                >
                  <option value="MASCULINO">Masculino</option>
                  <option value="FEMININO">Feminino (Autorregulação individualizada ativa)</option>
                </select>
              </div>
            </div>

            <div className="grid-2">
              <div className="field">
                <label>Peso Atual (kg)</label>
                <input
                  type="number"
                  className="input"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Altura (cm)</label>
                <input
                  type="number"
                  className="input"
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                />
              </div>
            </div>

            {bmi > 27 && !bodyNeutralMode && (
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: 10,
                  background: 'var(--amber-soft)',
                  fontSize: 12.5,
                  marginBottom: 12,
                }}
              >
                <strong>Correção Metabólica Ativa (Morton et al.):</strong> IMC {bmi.toFixed(1)} —
                proteína calculada sobre massa de referência ajustada (
                <strong>{adjMass.toFixed(1)} kg</strong>) para evitar superestimação irreal.
              </div>
            )}

            <div className="field">
              <label>Nível Real de Treinamento Atual</label>
              <select
                className="select"
                value={level}
                onChange={(e) => setLevel(e.target.value as TrainingLevel)}
              >
                <option value="INICIANTE">Iniciante / Sedentário / Retomando após pausa</option>
                <option value="INTERMEDIARIO">Intermediário (6+ meses consistentes)</option>
                <option value="AVANCADO">Avançado (2+ anos estruturados com controle de RIR)</option>
              </select>
            </div>

            <div className="field">
              <label>Ambiente e Equipamento Disponível</label>
              <select
                className="select"
                value={equipment}
                onChange={(e) => setEquipment(e.target.value as EquipmentEnv)}
              >
                <option value="CALISTENIA">Calistenia / Peso do Corpo (Zero equipamento)</option>
                <option value="CASA">Casa (Halteres, Elásticos e/ou Barra de Porta)</option>
                <option value="ACADEMIA">Academia Completa (Barras, Cabos e Máquinas)</option>
              </select>
            </div>

            <div className="field">
              <label>Objetivo Energético Atual</label>
              <select
                className="select"
                value={energyGoal}
                onChange={(e) => setEnergyGoal(e.target.value as EnergyGoal)}
              >
                <option value="MANUTENCAO_PERFORMANCE">
                  Manutenção / Recomposição &amp; Performance Cognitiva
                </option>
                <option value="DEFICIT_MODERADO">
                  Déficit Calórico (Redução de Gordura — ajuste Murphy &amp; Koehler ativo)
                </option>
                <option value="SUPERAVIT_MAGRO">
                  Superávit Magro (Hipertrofia &amp; Força Máxima)
                </option>
              </select>
            </div>

            <button
              className="btn btn-primary btn-block"
              onClick={() => {
                triggerHaptic('light');
                setStep(2);
              }}
            >
              Próximo: Rotina, Clima &amp; Tempo <ArrowRight size={17} />
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="card card-amber">
            <div className="section-header">
              <div>
                <div className="section-kicker">Etapa 2 de 4 • Ecologia Real de Vida</div>
                <h2 className="section-title">Rotina, Clima &amp; Lei do Tempo</h2>
              </div>
              <Brain size={22} color="var(--amber)" />
            </div>

            <div className="field">
              <label>Demanda Física do Trabalho / Estudo (Paradoxo OPA — Holtermann)</label>
              <select
                className="select"
                value={occupationalDemand}
                onChange={(e) => setOccupationalDemand(e.target.value as OccupationalDemand)}
              >
                <option value="SEDENTARIO_INTELECTUAL">
                  Intelectual / Sentado maior parte do dia
                </option>
                <option value="MISTO_EM_PE">Misto / Deslocamentos constantes em pé</option>
                <option value="BRACAL_PESADO">
                  Trabalho Braçal / Carga Física Pesada (veta carga axial extra na coluna)
                </option>
              </select>
            </div>

            <div className="grid-2">
              <div className="field">
                <label>Clima Predominante</label>
                <select
                  className="select"
                  value={climate}
                  onChange={(e) => setClimate(e.target.value as ClimateProfile)}
                >
                  <option value="CALOR_TROPICAL_UMIDO">
                    Calor Tropical / Úmido (eletrólitos + hidratação extra)
                  </option>
                  <option value="AMENO_CLIMATIZADO">Ameno / Ambiente Climatizado</option>
                </select>
              </div>
              <div className="field">
                <label>Regime Circadiano</label>
                <select
                  className="select"
                  value={scheduleRegime}
                  onChange={(e) => setScheduleRegime(e.target.value as ScheduleRegime)}
                >
                  <option value="DIURNO_FIXO">Diurno Regular</option>
                  <option value="TURNOS_PLANTAO">Turnos / Plantão / Madrugada</option>
                </select>
              </div>
            </div>

            <div className="field">
              <label>Perfil de Função Executiva (Lê seu padrão comportamental)</label>
              <select
                className="select"
                value={executiveProfile}
                onChange={(e) => setExecutiveProfile(e.target.value as ExecutiveProfile)}
              >
                <option value="EQUILIBRADO">Equilibrado</option>
                <option value="IMPULSIVO_BUSCA_NOVIDADE">
                  Hiperfoco / Busca de Novidade (TDAH / Criativo Intenso)
                </option>
                <option value="PERFECCIONISTA_RIGIDO">
                  Perfeccionista Rígido (risco de "tudo-ou-nada" ao falhar 1 dia)
                </option>
                <option value="ANSIOSO_EVITATIVO">
                  Ansioso / Sobrecarga Mental Frequente
                </option>
              </select>
            </div>

            <div className="grid-2">
              <div className="field">
                <label>Minutos Livres (Dia Útil)</label>
                <input
                  type="number"
                  className="input"
                  value={weekdayFreeMinutes}
                  onChange={(e) => setWeekdayFreeMinutes(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Minutos Livres (Fim de Semana)</label>
                <input
                  type="number"
                  className="input"
                  value={weekendFreeMinutes}
                  onChange={(e) => setWeekendFreeMinutes(e.target.value)}
                />
              </div>
            </div>

            <div className="grid-3">
              <div className="field">
                <label>Acorda às</label>
                <input
                  type="time"
                  className="input"
                  value={usualWakeTime}
                  onChange={(e) => setUsualWakeTime(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Dorme às</label>
                <input
                  type="time"
                  className="input"
                  value={usualBedTime}
                  onChange={(e) => setUsualBedTime(e.target.value)}
                />
              </div>
              <div className="field">
                <label>Meta Sono (h)</label>
                <input
                  type="number"
                  step="0.5"
                  className="input"
                  value={targetSleepHours}
                  onChange={(e) => setTargetSleepHours(e.target.value)}
                />
              </div>
            </div>

            <div className="grid-2">
              <button className="btn btn-ghost" onClick={() => setStep(1)}>
                <ArrowLeft size={16} /> Voltar
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  triggerHaptic('light');
                  setStep(3);
                }}
              >
                Segurança Clínica <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="card card-amber">
            <div className="section-header">
              <div>
                <div className="section-kicker">Etapa 3 de 4 • Blindagem Médica &amp; Farmacológica</div>
                <h2 className="section-title">Travas de Segurança Científica</h2>
              </div>
              <ShieldCheck size={22} color="var(--emerald)" />
            </div>
            <p className="muted" style={{ marginTop: 0 }}>
              Marque apenas se aplicável. Tudo fica 100% offline no dispositivo e recalibra as
              equações fisiológicas automaticamente.
            </p>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={betaBlocker}
                onChange={(e) => setBetaBlocker(e.target.checked)}
              />
              <div>
                <strong>Uso de Betabloqueador / Anti-hipertensivo bradicardizante</strong>
                <div className="muted">
                  Desativa fórmulas de FC máx (220−idade) e calibra cardio por Talk Test e RPE.
                </div>
              </div>
            </label>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={glp1Agonist}
                onChange={(e) => setGlp1Agonist(e.target.checked)}
              />
              <div>
                <strong>Uso de Agonista GLP-1 (Semaglutida/Tirzepatida) ou Bariátrica</strong>
                <div className="muted">
                  Ativa blindagem anticatabólica obrigatória de massa magra + proteína mínima alta.
                </div>
              </div>
            </label>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={adhdStimulant}
                onChange={(e) => setAdhdStimulant(e.target.checked)}
              />
              <div>
                <strong>Uso de Psicoestimulante (Venvanse / Ritalina / Modafinila)</strong>
                <div className="muted">
                  Monitora mascaramento simpático de fadiga e corte estrito de cafeína.
                </div>
              </div>
            </label>

            <label className="check-toggle">
              <input type="checkbox" checked={statin} onChange={(e) => setStatin(e.target.checked)} />
              <div>
                <strong>Uso de Estatina</strong>
                <div className="muted">
                  Atenção diferenciada entre mialgia medicamentosa persistente e dor pós-treino.
                </div>
              </div>
            </label>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={fluoroquinolone}
                onChange={(e) => setFluoroquinolone(e.target.checked)}
              />
              <div>
                <strong>Uso recente (&lt; 90 dias) de Antibiótico Fluoroquinolona (Cipro/Levo)</strong>
                <div className="muted">
                  Bloqueia pliometria e carga excêntrica brusca para proteção do tendão de Aquiles.
                </div>
              </div>
            </label>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={parqWarning}
                onChange={(e) => setParqWarning(e.target.checked)}
              />
              <div>
                <strong>Alerta PAR-Q+ (dor torácica, tontura ou cardiopatia sem liberação)</strong>
                <div className="muted">
                  Veta sprints máximos/VO2 até avaliação médica, mantendo Zona 2 segura e controle.
                </div>
              </div>
            </label>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={interoceptiveSensitive}
                onChange={(e) => setInteroceptiveSensitive(e.target.checked)}
              />
              <div>
                <strong>Ansiedade/desconforto ao fechar os olhos e focar na respiração</strong>
                <div className="muted">
                  Substitui meditação interoceptiva por Aterramento Visual de Olhos Abertos (Farias
                  et al., 2020).
                </div>
              </div>
            </label>

            <label className="check-toggle">
              <input
                type="checkbox"
                checked={bodyNeutralMode}
                onChange={(e) => setBodyNeutralMode(e.target.checked)}
              />
              <div>
                <strong>Modo Neutro Corporal (foco 100% em força, saúde e cognição)</strong>
                <div className="muted">
                  Oculta peso/IMC para proteção psicológica total.
                </div>
              </div>
            </label>

            <div className="grid-2" style={{ marginTop: 12 }}>
              <button className="btn btn-ghost" onClick={() => setStep(2)}>
                <ArrowLeft size={16} /> Voltar
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  triggerHaptic('light');
                  setStep(4);
                }}
              >
                Alvo &amp; Panteão <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="card card-amber">
            <div className="section-header">
              <div>
                <div className="section-kicker">Etapa 4 de 4 • Córtex, Maestria &amp; Panteão</div>
                <h2 className="section-title">Domínio Real &amp; Voz de Comando</h2>
              </div>
              <Sparkles size={22} color="var(--amber)" />
            </div>

            <div className="field">
              <label>
                Qual habilidade ou domínio REAL você quer levar ao Ápice? (Sala &amp; Gobet 2023)
              </label>
              <input
                className="input"
                value={primaryGoalDomain}
                onChange={(e) => setPrimaryGoalDomain(e.target.value)}
                placeholder="Ex: Programação/RE, Medicina, Concurso, Xadrez, Artes Marciais..."
              />
            </div>

            <div className="field">
              <label>Seu Maior Sabotador Recorrente (gera seu 1º Dique Se-Então)</label>
              <input
                className="input"
                value={mainSaboteur}
                onChange={(e) => setMainSaboteur(e.target.value)}
                placeholder="Ex: Rolar feed à noite, pular treino quando cansado..."
              />
            </div>

            <div className="field">
              <label>Roteamento do Panteão Operacional</label>
              <select
                className="select"
                value={commandVoice}
                onChange={(e) => setCommandVoice(e.target.value as CommandVoice)}
              >
                <option value="ADAPTATIVO">
                  Adaptativo Completo (Jesus Cristo, Sabedoria Bíblica, Goggins, Senku, Stark...)
                </option>
                <option value="CRISTO_BIBLIA">
                  A Pedra Angular (Jesus Cristo + Sabedoria da Bíblia — Caráter, Fé &amp; Serviço)
                </option>
                <option value="GOGGINS_MUSASHI">
                  Fogo &amp; Aço (David Goggins + Miyamoto Musashi — subordinado à clínica!)
                </option>
                <option value="SENKU_FEYNMAN">
                  Cientista Puro (Senku Ishigami + Richard Feynman + Nikola Tesla)
                </option>
                <option value="STARK_MAQUIAVEL">
                  Engenheiro &amp; Estrategista (Tony Stark + Maquiavel + Marco Aurélio)
                </option>
              </select>
            </div>

            <div className="grid-2" style={{ marginTop: 14 }}>
              <button className="btn btn-ghost" onClick={() => setStep(3)}>
                <ArrowLeft size={16} /> Voltar
              </button>
              <button className="btn btn-emerald" onClick={handleFinish}>
                Ativar Sistema do Ápice
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
