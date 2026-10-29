import React, { useCallback, useRef, useState } from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

const ICONS: Record<ToastType, React.ElementType> = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info,
  warning: AlertTriangle,
};

const COLORS: Record<ToastType, string> = {
  success: 'var(--emerald)',
  error: 'var(--rose)',
  info: 'var(--cyan)',
  warning: 'var(--amber)',
};

export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onDismiss,
}) => {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-6 right-6 z-50 flex flex-col gap-3 pointer-events-none"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
};

interface ToastItemProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

export const ToastItem: React.FC<ToastItemProps> = ({ toast, onDismiss }) => {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const Icon = ICONS[toast.type];
  const color = COLORS[toast.type];

  const dismiss = useCallback(() => {
    onDismiss(toast.id);
  }, [toast.id, onDismiss]);

  // Auto-dismiss
  React.useEffect(() => {
    const ms = toast.duration ?? 4000;
    timerRef.current = setTimeout(dismiss, ms);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [dismiss, toast.duration]);

  return (
    <div
      className="pointer-events-auto flex items-center gap-3 w-full max-w-xs px-4 py-3 rounded-xl shadow-xl border animate-in slide-in-from-right-200 duration-200 ease-out"
      style={{
        background: 'var(--bg-card)',
        borderColor: `${color}40`,
        boxShadow: `0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.15)`,
      }}
    >
      <Icon size={18} style={{ color }} />
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-sm text-white">
          {toast.title}
        </div>
        {toast.message && (
          <div className="text-xs text-slate-300 mt-1">{toast.message}</div>
        )}
      </div>
      <button
        onClick={dismiss}
        className="ml-2 p-1 text-slate-400 hover:text-white transition-colors"
        aria-label="Fechar notificação"
      >
        <X size={14} />
      </button>
    </div>
  );
};

export type ToastManager = {
  showToast: (toast: Omit<Toast, 'id'>) => string;
  dismissToast: (id: string) => void;
  clearAll: () => void;
};

export function createToastManager(): ToastManager & {
  toasts: Toast[];
  setToasts: React.Dispatch<React.SetStateAction<Toast[]>>;
} {
  let toasts: Toast[] = [];
  let listeners: (() => void)[] = [];
  let nextId = 1;

  const notify = () => {
    listeners.forEach((fn) => fn());
  };

  const showToast = (payload: Omit<Toast, 'id'>): string => {
    const id = `toast_${nextId++}`;
    const newToast: Toast = { ...payload, id };
    toasts = [...toasts, newToast];
    notify();
    return id;
  };

  const dismissToast = (id: string) => {
    toasts = toasts.filter((t) => t.id !== id);
    notify();
  };

  const clearAll = () => {
    toasts = [];
    notify();
  };

  return {
    toasts,
    setToasts: (cb) => {
      if (typeof cb === 'function') {
        toasts = cb(toasts);
      } else {
        toasts = cb;
      }
      notify();
    },
    showToast,
    dismissToast,
    clearAll,
  };
}

export default ToastContainer;