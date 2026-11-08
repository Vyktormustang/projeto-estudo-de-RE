import type { ReactNode } from 'react';
import { AlertIcon, CheckIcon, CloseIcon } from './Icons';

interface BannerProps {
  tone: 'error' | 'warning' | 'success' | 'info';
  title?: string;
  children: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
}

/** Faixa de aviso/erro usada em todas as telas (mensagens sempre em português). */
export function Banner({ tone, title, children, onClose, action }: BannerProps) {
  return (
    <div className={`banner banner--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <span className="banner__icon">
        {tone === 'success' ? <CheckIcon size={20} /> : <AlertIcon size={20} />}
      </span>
      <div className="banner__body">
        {title ? <strong className="banner__title">{title}</strong> : null}
        <p className="banner__text">{children}</p>
        {action ? <div className="banner__action">{action}</div> : null}
      </div>
      {onClose ? (
        <button type="button" className="banner__close" onClick={onClose} aria-label="Fechar aviso">
          <CloseIcon size={18} />
        </button>
      ) : null}
    </div>
  );
}
