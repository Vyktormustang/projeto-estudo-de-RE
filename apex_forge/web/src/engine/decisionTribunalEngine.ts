import { clamp } from './stateEngine';
import { RealDecisionRecord } from './types';

export interface DecisionTribunalInput {
  decisionTitle: string;
  towerCostEstimate: string;
  solomonThirdPerson: string;
  preMortemGuardrail: string;
  preservesCharacter: boolean;
  zeroRuinRisk: boolean;
  futureSelf101010: boolean;
  confidencePct: 55 | 70 | 85;
}

export interface DecisionTribunalAudit {
  maturityScore100: number;
  verdict: RealDecisionRecord['verdict'];
  verdictLabel: string;
  counselSummary: string;
  warnings: string[];
}

/**
 * Avalia uma decisao real combinando:
 * 1) Calcular o Custo da Torre (Lucas 14:28-30)
 * 2) Autodistanciamento em 3a Pessoa — Paradoxo de Salomao (Grossmann & Kross, Psychol Sci 2014)
 * 3) Pre-Mortem Prospectivo (Klein, HBR 2007; Mitchell et al., 1989)
 * 4) Veto Inegociavel de Carater (Mateus 16:26) e Zero Ruina Nao-Ergodica (Kelly 1956; Peters 2019)
 * 5) Continuidade com o Eu Futuro 10-10-10 (Hershfield et al., 2011)
 */
export function evaluateRealDecision(input: DecisionTribunalInput): DecisionTribunalAudit {
  const warnings: string[] = [];

  if (!input.preservesCharacter) {
    warnings.push(
      'VETO DE ROCHA (Mateus 16:26 • Provérbios 11:1): nenhuma vantagem compensa corromper seu caráter ou perder a paz na consciência.',
    );
  }
  if (!input.zeroRuinRisk) {
    warnings.push(
      'VETO ANTI-RUÍNA (Kelly 1956 • Peters 2019): há risco de perda catastrófica irreversível. Reduza o tamanho da exposição ou crie margem antes de prosseguir.',
    );
  }
  if (!input.futureSelf101010) {
    warnings.push(
      'ALERTA 10-10-10 (Hershfield, 2011): seu Eu de 10 meses / 10 anos pagará caro por um alívio impulsivo de 10 minutos.',
    );
  }

  const costWords = input.towerCostEstimate.trim().split(/\s+/).filter(Boolean).length;
  const solomonWords = input.solomonThirdPerson.trim().split(/\s+/).filter(Boolean).length;
  const preMortemWords = input.preMortemGuardrail.trim().split(/\s+/).filter(Boolean).length;

  if (costWords < 4) {
    warnings.push('Especifique o custo real de tempo, dinheiro e energia (Lucas 14:28).');
  }
  if (solomonWords < 5) {
    warnings.push(
      'Aprofunde a visão em 3ª pessoa: o que você diria se fosse seu melhor amigo nesta escolha?',
    );
  }
  if (preMortemWords < 5) {
    warnings.push(
      'Defina pelo menos 1 falha possível no Pré-Mortem e sua trava preventiva concreta.',
    );
  }

  let raw = 0;
  raw += Math.min(20, costWords * 2.5);
  raw += Math.min(22, solomonWords * 2.5);
  raw += Math.min(23, preMortemWords * 2.5);
  if (input.preservesCharacter) raw += 15;
  if (input.zeroRuinRisk) raw += 12;
  if (input.futureSelf101010) raw += 8;

  // Se houver veto moral ou de ruina total, o teto cai drasticamente por seguranca
  if (!input.preservesCharacter || !input.zeroRuinRisk) {
    raw = Math.min(raw, 34);
  }

  const maturityScore100 = Math.round(clamp(raw, 0, 100));

  if (!input.preservesCharacter || !input.zeroRuinRisk) {
    return {
      maturityScore100,
      verdict: 'VETO_PRUDENCIAL',
      verdictLabel: 'Veto Prudencial — Pare ou Redesenhe',
      counselSummary:
        'O Tribunal detectou violação de integridade ou risco de ruína irreversível. Um mestre nunca multiplica sua vida por zero: descarte ou redesenhe com margem de segurança.',
      warnings,
    };
  }

  if (maturityScore100 >= 75 && input.futureSelf101010) {
    return {
      maturityScore100,
      verdict: 'AVANCAR_COM_TRAVAS',
      verdictLabel: 'Avançar com Travas Ativas',
      counselSummary:
        'Custo calculado, visão de Salomão limpa, risco de ruína zerado e trava Pré-Mortem instalada! Execute com coragem e registre no Diário para auditar sem Viés de Retrospectiva.',
      warnings,
    };
  }

  return {
    maturityScore100,
    verdict: 'REFORCAR_ANTES_DE_AGIR',
    verdictLabel: 'Reforçar Análise Antes de Agir',
    counselSummary:
      'A decisão não tem ruína fatal, mas ainda faltam dados claros sobre o custo real, o Pré-Mortem ou o alinhamento 10-10-10. Complete as lacunas abaixo antes de bater o martelo.',
    warnings,
  };
}

export interface RealLifeCalibrationSummary {
  resolvedCount: number;
  meanBrierScore: number;      // 0.000 (perfeito) .. 1.000; 0.250 = moeda aleatoria
  calibrationScore100: number; // 0..100 para leitura intuitiva
  statusLabel: string;
}

/**
 * Fecha o ciclo ex-ante -> ex-post de uma decisao real (Fischhoff 1975; Tetlock 2015; Di Stefano 2014).
 * Calcula o Erro Quadratico de Brier BS = (p - o)^2, onde p in {0.55, 0.70, 0.85} e o in {1, 0}.
 */
export function resolveRealDecisionOutcome(
  record: RealDecisionRecord,
  resolvedOutcome: 'SUCESSO' | 'FALHA',
  outcomeLessonLearned: string,
  resolvedBioDayId: string,
): RealDecisionRecord {
  const p = record.confidencePct / 100;
  const o = resolvedOutcome === 'SUCESSO' ? 1 : 0;
  const brierScore = Math.round((p - o) * (p - o) * 10000) / 10000;

  return {
    ...record,
    resolvedOutcome,
    outcomeLessonLearned:
      outcomeLessonLearned.trim() ||
      (resolvedOutcome === 'SUCESSO'
        ? 'Travas preventivas e cálculo de custo confirmados na prática.'
        : 'Desvio real identificado; regra preventiva atualizada para decisões futuras.'),
    resolvedBioDayId,
    brierScore,
  };
}

export function computeRealLifeCalibrationSummary(
  records: RealDecisionRecord[],
): RealLifeCalibrationSummary {
  const resolved = records.filter(
    (r) => Boolean(r.resolvedOutcome) && typeof r.brierScore === 'number',
  );
  if (resolved.length === 0) {
    return {
      resolvedCount: 0,
      meanBrierScore: 0.25,
      calibrationScore100: 50,
      statusLabel: 'Aguardando 1º desfecho real auditado',
    };
  }

  const meanBrier =
    resolved.reduce((acc, r) => acc + (r.brierScore ?? 0.25), 0) / resolved.length;
  const roundedBrier = Math.round(meanBrier * 1000) / 1000;
  // p in {0.55..0.85} -> melhor BS possivel = 0.0225, pior = 0.7225; mapeia [0.0225..0.7225] -> [100..0]
  const calibrationScore100 = Math.round(
    clamp(((0.7225 - meanBrier) / 0.7) * 100, 0, 100),
  );

  let statusLabel = 'Calibração em Construção';
  if (meanBrier <= 0.14) {
    statusLabel = 'Superprevisor Calibrado (Nível Tetlock)';
  } else if (meanBrier <= 0.25) {
    statusLabel = 'Prudência Bem Calibrada (Acima do Acaso)';
  } else {
    statusLabel = 'Alerta de Excesso de Confiança — Ajuste Margens';
  }

  return {
    resolvedCount: resolved.length,
    meanBrierScore: roundedBrier,
    calibrationScore100,
    statusLabel,
  };
}

