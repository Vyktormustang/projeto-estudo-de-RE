import { toPercent } from '../lib/format';
import type { WordColor } from '../lib/types';

interface ScoreRingProps {
  score: number;
  color: WordColor;
  label?: string;
  size?: number;
}

/**
 * Anel de progresso com a nota geral.
 * Feito com SVG puro (funciona offline no APK).
 */
export function ScoreRing({ score, color, label = 'Nota geral', size = 132 }: ScoreRingProps) {
  const percent = toPercent(score);
  const stroke = 11;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (percent / 100) * circumference;

  return (
    <div className={`score-ring score-ring--${color}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${label}: ${percent} por cento`}>
        <circle
          className="score-ring__track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
        />
        <circle
          className="score-ring__value"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference - dash}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="score-ring__text">
        <strong>{percent}%</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}
