import { describe, expect, it } from 'vitest';
import {
  generateCorsiSequence,
  generateLociDeck,
  generateLogicQuestion,
  generateNumeracyQuestion,
  generateStroopTrial,
  generateWisdomDiscernmentQuestion,
  getWordsPool,
  STROOP_COLORS,
} from './cognitiveGenerator';
import {
  EXERCISE_CATALOG,
  getExerciseById,
  getExerciseProgressionLadder,
} from './exerciseCatalog';
import { AnimationArchetype } from './types';

const VALID_ARCHETYPES: AnimationArchetype[] = [
  'PUSH_UP',
  'BENCH_PRESS',
  'OVERHEAD_PRESS',
  'ROW_HORIZONTAL',
  'VERTICAL_PULL',
  'SQUAT',
  'SPLIT_SQUAT',
  'HIP_HINGE',
  'GLUTE_BRIDGE',
  'DEADBUG_CORE',
  'SIDE_PLANK',
  'MOBILITY_WALL',
  'CARDIO_STRIDE',
];

describe('FORJA v4.0 — Auditoria de Demonstrações Visuais & Arena Cognitiva', () => {
  it('1. Todos os 24+ exercícios possuem arquétipo animado válido, dica externa de Wulf, 3 passos e 2 erros', () => {
    expect(EXERCISE_CATALOG.length).toBeGreaterThanOrEqual(24);
    for (const ex of EXERCISE_CATALOG) {
      expect(VALID_ARCHETYPES).toContain(ex.animationArchetype);
      expect(ex.externalFocusCue.trim().length).toBeGreaterThan(15);
      expect(ex.musclesWorked.length).toBeGreaterThanOrEqual(1);
      expect(ex.stepByStep).toHaveLength(3);
      expect(ex.commonMistakes).toHaveLength(2);
      for (const s of ex.stepByStep) expect(s.trim().length).toBeGreaterThan(8);
      for (const m of ex.commonMistakes) expect(m.trim().length).toBeGreaterThan(8);
      if (ex.painSafeFallbackId) {
        expect(getExerciseById(ex.painSafeFallbackId)).toBeDefined();
      }
    }
  });

  it('2. Stroop Inibitório (3.000 rodadas fuzz): índices de gabarito sempre exatos e 4 opções sem duplicatas', () => {
    for (const tier of [1, 2, 3] as const) {
      for (let seed = 1; seed <= 1000; seed++) {
        const trial = generateStroopTrial(seed * 977 + tier, tier);
        expect(trial.options).toHaveLength(4);
        expect(new Set(trial.options).size).toBe(4);
        expect(trial.correctIndex).toBeGreaterThanOrEqual(0);
        expect(trial.correctIndex).toBeLessThan(4);
        const inkSpec = STROOP_COLORS.find((c) => c.hex === trial.inkHex);
        expect(inkSpec).toBeDefined();
        const expectedLabel =
          trial.rule === 'COR_DA_TINTA' ? inkSpec!.label : trial.wordText;
        expect(trial.options[trial.correctIndex]).toBe(expectedLabel);
      }
    }
  });

  it('3. Raciocínio Lógico & Matrizes 3x3 Raven (3.000 questões fuzz): alternativa correta única sem colisão', () => {
    for (const tier of [1, 2, 3] as const) {
      for (let seed = 1; seed <= 1000; seed++) {
        const item = generateLogicQuestion(seed * 1337 + tier, tier);
        expect(item.correctIndex).toBeGreaterThanOrEqual(0);
        expect(item.correctIndex).toBeLessThan(4);
        expect(item.explanation.length).toBeGreaterThan(10);

        if (item.kind === 'RAVEN_MATRIX') {
          expect(item.matrixGrid).toHaveLength(9);
          expect(item.matrixGrid![8]).toBeNull();
          expect(item.matrixOptions).toHaveLength(4);
          const sigs = item.matrixOptions!.map(
            (c) => `${c.shape}_${c.count}_${c.fill}`,
          );
          expect(new Set(sigs).size).toBe(4);
        } else {
          expect(item.textOptions).toHaveLength(4);
          expect(new Set(item.textOptions).size).toBe(4);
        }
      }
    }
  });

  it('4. Memória Visuoespacial Corsi: zero repetição de bloco e limites estritos de grade 3x3 e 4x4', () => {
    for (const gridDim of [3, 4] as const) {
      const totalCells = gridDim * gridDim;
      for (let span = 3; span <= 8; span++) {
        for (let seed = 1; seed <= 100; seed++) {
          const seq = generateCorsiSequence(span, gridDim, seed * 31 + span);
          expect(seq).toHaveLength(span);
          expect(new Set(seq).size).toBe(span);
          for (const cell of seq) {
            expect(cell).toBeGreaterThanOrEqual(0);
            expect(cell).toBeLessThan(totalCells);
          }
        }
      }
    }
  });

  it('5. Palácio da Memória (Method of Loci — 600 baterias): zero duplicata + filtro aritmético válido', () => {
    const pool = getWordsPool();
    for (const tier of [1, 2, 3] as const) {
      for (let seed = 1; seed <= 200; seed++) {
        const deck = generateLociDeck(tier, seed * 509 + tier);
        const expectedCount = tier === 1 ? 5 : tier === 2 ? 7 : 9;
        expect(deck.pairs).toHaveLength(expectedCount);
        const targetWords = deck.pairs.map((p) => p.targetWord);
        expect(new Set(targetWords).size).toBe(expectedCount);
        for (const t of targetWords) {
          expect(pool).toContain(t);
        }
        expect(deck.interferenceOptions).toHaveLength(4);
        expect(new Set(deck.interferenceOptions).size).toBe(4);
        expect(deck.interferenceCorrectIndex).toBeGreaterThanOrEqual(0);
        expect(deck.interferenceCorrectIndex).toBeLessThan(4);
      }
    }
  });

  it('6. Numeracia, Regra dos 72, Bayes & Fermi (3.000 questões fuzz) + Escada Biomecânica do Zero ao Mestre', () => {
    for (const ex of EXERCISE_CATALOG) {
      const ladder = getExerciseProgressionLadder(ex);
      expect(ladder.zeroStep.length).toBeGreaterThan(25);
      expect(ladder.masterStep.length).toBeGreaterThan(25);
    }

    for (const tier of [1, 2, 3] as const) {
      for (let seed = 1; seed <= 1000; seed++) {
        const q = generateNumeracyQuestion(seed * 733 + tier, tier);
        expect(q.options).toHaveLength(4);
        expect(new Set(q.options).size).toBe(4);
        expect(q.correctIndex).toBeGreaterThanOrEqual(0);
        expect(q.correctIndex).toBeLessThan(4);
        expect(q.mentalShortcut.length).toBeGreaterThan(10);
      }
    }
  });

  it('7. Discernimento, Antivieses & Sabedoria Prática (3.000 casos fuzz): 4 opções únicas e âncora científica/bíblica válida', () => {
    for (const tier of [1, 2, 3] as const) {
      for (let seed = 1; seed <= 1000; seed++) {
        const w = generateWisdomDiscernmentQuestion(seed * 919 + tier, tier);
        expect(w.options).toHaveLength(4);
        expect(new Set(w.options).size).toBe(4);
        expect(w.correctIndex).toBeGreaterThanOrEqual(0);
        expect(w.correctIndex).toBeLessThan(4);
        expect(w.principleAnchor.length).toBeGreaterThan(15);
      }
    }
  });
});
