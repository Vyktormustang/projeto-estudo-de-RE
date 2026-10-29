import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, Scale, ShieldCheck, Target } from 'lucide-react';
import {
  computeRealLifeCalibrationSummary,
  evaluateRealDecision,
} from '../engine/decisionTribunalEngine';
import { RealDecisionRecord } from '../engine/types';
import { playTacticalChime } from '../services/audioBiofeedback';
import { triggerHaptic } from '../services/vaultStorage';

interface Props {
  bioDayId: string;
  records: RealDecisionRecord[];
  onSaveDecision: (record: RealDecisionRecord) => void;
  onResolveDecision?: (
    decisionId: string,
    outcome: 'SUCESSO' | 'FALHA',
    lessonLearned: string,
  ) => void;
}

export const DecisionTribunalView: React.FC<Props> = ({
  bioDayId,
  records,
  onSaveDecision,
  onResolveDecision,
}) => {
  const [decisionTitle, setDecisionTitle] = useState('');
  const [towerCostEstimate, setTowerCostEstimate] = useState('');
  const [solomonThirdPerson, setSolomonThirdPerson] = useState('');
  const [preMortemGuardrail, setPreMortemGuardrail] = useState('');
  const [preservesCharacter, setPreservesCharacter] = useState(true);
  const [zeroRuinRisk, setZeroRuinRisk] = useState(true);
  const [futureSelf101010, setFutureSelf101010] = useState(true);
  const [confidencePct, setConfidencePct] = useState<55 | 70 | 85>(70);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [lessonDraft, setLessonDraft] = useState('');

  const liveAudit = evaluateRealDecision({
    decisionTitle,
    towerCostEstimate,
    solomonThirdPerson,
    preMortemGuardrail,
    preservesCharacter,
    zeroRuinRisk,
    futureSelf101010,
    confidencePct,
  });

  const calibration = computeRealLifeCalibrationSummary(records);

  const handleCommit = () => {
    if (!decisionTitle.trim()) return;
    triggerHaptic(liveAudit.verdict === 'VETO_PRUDENCIAL' ? 'heavy' : 'success');
    if (liveAudit.verdict === 'AVANCAR_COM_TRAVAS') {
      playTacticalChime('VICTORY');
    }

    onSaveDecision({
      id: `dec_${Date.now()}`,
      bioDayId,
      timestampMs: Date.now(),
      decisionTitle: decisionTitle.trim(),
      towerCostEstimate:
        towerCostEstimate.trim() || 'Custo de tempo e energia avaliado com margem.',
      solomonThirdPerson:
        solomonThirdPerson.trim() || 'Conselho em 3ª pessoa alinhado à prudência.',
      preMortemGuardrail:
        preMortemGuardrail.trim() || 'Trava preventiva definida antes da execução.',
      preservesCharacter,
      zeroRuinRisk,
      futureSelf101010,
      confidencePct,
      maturityScore100: liveAudit.maturityScore100,
      verdict: liveAudit.verdict,
    });

    setDecisionTitle('');
    setTowerCostEstimate('');
    setSolomonThirdPerson('');
    setPreMortemGuardrail('');
  };

  return (
    <>
      <div className="card card-amber">
        <div className="section-header">
          <div>
            <div className="section-kicker">
              Lucas 14:28 • Paradoxo de Salomão (Grossmann, 2014) • Pré-Mortem (Klein, 2007)
            </div>
            <h2 className="section-title">Tribunal de Decisão Real &amp; Diário Ex-Ante</h2>
          </div>
          <Scale size={22} color="var(--amber)" />
        </div>

        <p className="muted" style={{ marginTop: 0, marginBottom: 12 }}>
          Passe qualquer escolha importante de carreira, estudo, dinheiro ou relacionamento por este
          protocolo antes de agir. Além de blindar contra impulsos, ele congela seu raciocínio{' '}
          <em>antes</em> do resultado e fecha o ciclo com o Erro de Brier quando o desfecho real
          chega (Fischhoff, 1975; Tetlock, 2015).
        </p>

        <div className="field">
          <label>1. Qual decisão concreta você está avaliando hoje?</label>
          <input
            className="input"
            placeholder="Ex.: Mudar de área, assumir projeto novo, fazer compra grande, sociedade..."
            value={decisionTitle}
            onChange={(e) => setDecisionTitle(e.target.value)}
          />
        </div>

        <div className="field">
          <label>2. Custo da Torre (Lucas 14:28): quanto custará em horas, energia e dinheiro?</label>
          <input
            className="input"
            placeholder="Ex.: Exigirá 8h por semana por 6 meses + R$ 600 da margem livre sem dívida"
            value={towerCostEstimate}
            onChange={(e) => setTowerCostEstimate(e.target.value)}
          />
        </div>

        <div className="field">
          <label>
            3. Visão de Salomão em 3ª Pessoa: o que você aconselharia ao seu melhor amigo aqui?
          </label>
          <input
            className="input"
            placeholder="Ex.: Eu diria para ele começar pequeno testando por 30 dias antes de largar tudo"
            value={solomonThirdPerson}
            onChange={(e) => setSolomonThirdPerson(e.target.value)}
          />
        </div>

        <div className="field">
          <label>4. Pré-Mortem de Klein: se der errado em 6 meses, qual foi a causa + sua trava?</label>
          <input
            className="input"
            placeholder="Ex.: Falharia por falta de constância à noite; trava: fazer às 06h30 antes do celular"
            value={preMortemGuardrail}
            onChange={(e) => setPreMortemGuardrail(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
          <label className="check-toggle">
            <input
              type="checkbox"
              checked={preservesCharacter}
              onChange={(e) => setPreservesCharacter(e.target.checked)}
            />
            <div>
              <strong>Integridade Inegociável (Mateus 16:26 • Provérbios 11:1)</strong>
              <div className="muted">Preserva 100% meu caráter, minha palavra e minha consciência limpa.</div>
            </div>
          </label>

          <label className="check-toggle">
            <input
              type="checkbox"
              checked={zeroRuinRisk}
              onChange={(e) => setZeroRuinRisk(e.target.checked)}
            />
            <div>
              <strong>Zero Risco de Ruína Irreversível (Kelly, 1956 • Peters, 2019)</strong>
              <div className="muted">
                Mesmo no pior cenário, não destrói minha reserva vital, saúde ou família.
              </div>
            </div>
          </label>

          <label className="check-toggle">
            <input
              type="checkbox"
              checked={futureSelf101010}
              onChange={(e) => setFutureSelf101010(e.target.checked)}
            />
            <div>
              <strong>Aprovado na Lente 10-10-10 (Hershfield, 2011)</strong>
              <div className="muted">
                Meu Eu de 10 meses e de 10 anos ficará orgulhoso desta escolha.
              </div>
            </div>
          </label>
        </div>

        <div className="field" style={{ marginBottom: 12 }}>
          <label>5. Grau Honesto de Certeza Ex-Ante</label>
          <div className="chip-row">
            {([55, 70, 85] as const).map((pct) => (
              <button
                key={pct}
                type="button"
                className={`chip ${confidencePct === pct ? 'chip-active' : ''}`}
                onClick={() => setConfidencePct(pct)}
              >
                {pct}% de Certeza
              </button>
            ))}
          </div>
        </div>

        <div
          style={{
            padding: 12,
            borderRadius: 12,
            marginBottom: 12,
            background:
              liveAudit.verdict === 'AVANCAR_COM_TRAVAS'
                ? 'var(--emerald-soft)'
                : liveAudit.verdict === 'VETO_PRUDENCIAL'
                  ? 'var(--crimson-soft)'
                  : 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: 13.5 }}>{liveAudit.verdictLabel}</strong>
            <span className="badge badge-cyan">Maturidade {liveAudit.maturityScore100}/100</span>
          </div>
          <div className="muted" style={{ marginTop: 4, fontSize: 12.6 }}>
            {liveAudit.counselSummary}
          </div>
          {liveAudit.warnings.length > 0 && (
            <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 12, color: '#fde68a' }}>
              {liveAudit.warnings.map((w) => (
                <li key={w} style={{ marginBottom: 3 }}>
                  {w}
                </li>
              ))}
            </ul>
          )}
        </div>

        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={handleCommit}
        >
          <ShieldCheck size={16} /> Selar Decisão no Diário Ex-Ante
        </button>
      </div>

      {records.length > 0 && (
        <div className="card">
          <div className="section-header" style={{ marginBottom: 8 }}>
            <div>
              <div className="section-kicker">
                Ciclo Fechado Ex-Ante → Pós-Resultado (Tetlock, 2015)
              </div>
              <h3 className="section-title">
                Decisões Auditadas ({records.length})
              </h3>
            </div>
            <Target size={19} color="var(--cyan)" />
          </div>

          <div
            style={{
              padding: '10px 12px',
              borderRadius: 12,
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              marginBottom: 12,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 8,
            }}
          >
            <div>
              <div style={{ fontSize: 12.5, fontWeight: 800, color: '#67e8f9' }}>
                {calibration.statusLabel}
              </div>
              <div className="muted" style={{ fontSize: 11.5 }}>
                {calibration.resolvedCount} desfecho(s) real(is) fechado(s) • Erro Brier médio:{' '}
                <span className="mono">{calibration.meanBrierScore.toFixed(3)}</span> (quanto menor,
                melhor; acaso = 0.250)
              </div>
            </div>
            <span className="badge badge-green">
              Calibração {calibration.calibrationScore100}/100
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
            {records
              .slice()
              .reverse()
              .slice(0, 10)
              .map((rec) => {
                const isOpen = !rec.resolvedOutcome;
                const isEditingThis = resolvingId === rec.id;
                return (
                  <div
                    key={rec.id}
                    style={{
                      padding: 11,
                      borderRadius: 11,
                      background: 'var(--bg-elevated)',
                      borderLeft:
                        rec.verdict === 'AVANCAR_COM_TRAVAS'
                          ? '3px solid var(--emerald)'
                          : rec.verdict === 'VETO_PRUDENCIAL'
                            ? '3px solid var(--crimson)'
                            : '3px solid var(--amber)',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: 13,
                        fontWeight: 800,
                        gap: 8,
                      }}
                    >
                      <span>
                        {rec.verdict === 'AVANCAR_COM_TRAVAS' ? (
                          <CheckCircle2
                            size={13}
                            color="var(--emerald)"
                            style={{ verticalAlign: 'middle' }}
                          />
                        ) : (
                          <AlertTriangle
                            size={13}
                            color="var(--amber)"
                            style={{ verticalAlign: 'middle' }}
                          />
                        )}{' '}
                        {rec.decisionTitle}
                      </span>
                      <span className="mono" style={{ fontSize: 11.5, color: 'var(--cyan)' }}>
                        {rec.maturityScore100}/100 • {rec.confidencePct}%
                      </span>
                    </div>

                    <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                      <strong>Salomão 3ªp:</strong> {rec.solomonThirdPerson} •{' '}
                      <strong>Trava Klein:</strong> {rec.preMortemGuardrail}
                    </div>

                    {rec.resolvedOutcome ? (
                      <div
                        style={{
                          marginTop: 7,
                          padding: '6px 9px',
                          borderRadius: 8,
                          fontSize: 11.8,
                          background:
                            rec.resolvedOutcome === 'SUCESSO'
                              ? 'var(--emerald-soft)'
                              : 'var(--amber-soft)',
                        }}
                      >
                        <strong>
                          Desfecho Real:{' '}
                          {rec.resolvedOutcome === 'SUCESSO'
                            ? '✓ Previsão Confirmada'
                            : '↺ Desviou / Ajustado'}{' '}
                          (Brier {rec.brierScore?.toFixed(3)})
                        </strong>
                        {rec.outcomeLessonLearned ? ` — ${rec.outcomeLessonLearned}` : ''}
                      </div>
                    ) : onResolveDecision ? (
                      <div style={{ marginTop: 8 }}>
                        {!isEditingThis ? (
                          <button
                            type="button"
                            className="chip"
                            style={{ fontSize: 11.5 }}
                            onClick={() => {
                              setResolvingId(rec.id);
                              setLessonDraft('');
                            }}
                          >
                            Registrar Desfecho Real (Fechar Ciclo Brier)
                          </button>
                        ) : (
                          <div
                            style={{
                              padding: 9,
                              borderRadius: 10,
                              background: 'rgba(15, 23, 42, 0.55)',
                              marginTop: 4,
                            }}
                          >
                            <input
                              className="input"
                              style={{ marginBottom: 8, fontSize: 12.5 }}
                              placeholder="Qual lição real ficou após o resultado?"
                              value={lessonDraft}
                              onChange={(e) => setLessonDraft(e.target.value)}
                            />
                            <div className="grid-2">
                              <button
                                type="button"
                                className="btn btn-emerald"
                                style={{ minHeight: 36, fontSize: 12 }}
                                onClick={() => {
                                  triggerHaptic('success');
                                  playTacticalChime('VICTORY');
                                  onResolveDecision(rec.id, 'SUCESSO', lessonDraft);
                                  setResolvingId(null);
                                }}
                              >
                                ✓ Funcionou como Previsto
                              </button>
                              <button
                                type="button"
                                className="btn btn-ghost"
                                style={{ minHeight: 36, fontSize: 12 }}
                                onClick={() => {
                                  triggerHaptic('medium');
                                  onResolveDecision(rec.id, 'FALHA', lessonDraft);
                                  setResolvingId(null);
                                }}
                              >
                                ↺ Saiu Diferente (Aprender)
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : isOpen ? null : null}
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </>
  );
};
