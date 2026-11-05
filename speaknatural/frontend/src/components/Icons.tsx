/** Ícones em SVG (sem dependências externas, ocupam pouco no APK). */

interface IconProps {
  size?: number;
  className?: string;
}

const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.9,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
});

export function MicIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <rect x="9" y="2.5" width="6" height="11" rx="3" />
      <path d="M5.5 11.5a6.5 6.5 0 0 0 13 0" />
      <path d="M12 18v3.5M8.5 21.5h7" />
    </svg>
  );
}

export function StopIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <rect x="6" y="6" width="12" height="12" rx="2.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function PlayIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M7 4.5 19.5 12 7 19.5V4.5Z" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function RefreshIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M20 11a8 8 0 1 0-2.3 5.7" />
      <path d="M20 4.5V11h-6.5" />
    </svg>
  );
}

export function NextIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M5 5.5 15 12 5 18.5v-13Z" fill="currentColor" stroke="none" />
      <path d="M18.5 5v14" />
    </svg>
  );
}

export function PracticeIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M12 3.5a4 4 0 0 0-4 4v4a4 4 0 0 0 8 0v-4a4 4 0 0 0-4-4Z" />
      <path d="M6 11.5a6 6 0 0 0 12 0" />
      <path d="M12 17.5V21" />
    </svg>
  );
}

export function HistoryIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M3.5 12a8.5 8.5 0 1 0 2.6-6.1" />
      <path d="M3.5 4.5V10H9" />
      <path d="M12 7.5V12l3 2" />
    </svg>
  );
}

export function SettingsIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <circle cx="12" cy="12" r="3.2" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
    </svg>
  );
}

export function CloseIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  );
}

export function CheckIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M4.5 12.5 9.5 17.5 19.5 6.5" />
    </svg>
  );
}

export function AlertIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M12 3.8 21 20H3L12 3.8Z" />
      <path d="M12 9.5v4.5M12 17.2v.1" />
    </svg>
  );
}

export function SunIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4" />
    </svg>
  );
}

export function MoonIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
    </svg>
  );
}

export function SpeakerIcon({ size = 24, className }: IconProps) {
  return (
    <svg {...base(size)} className={className}>
      <path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4v-5Z" />
      <path d="M15.5 9a4 4 0 0 1 0 6" />
      <path d="M18 6.5a7.5 7.5 0 0 1 0 11" />
    </svg>
  );
}
