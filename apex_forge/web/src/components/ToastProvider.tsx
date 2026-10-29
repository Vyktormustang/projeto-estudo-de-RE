import React, { createContext, useContext, useCallback, useRef, useState } from 'react';
import ToastContainer from './ToastNotification';
import type { Toast } from './ToastNotification';

interface ToastContextType {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, 'id'>) => string;
  dismissToast: (id: string) => void;
  clearAllToasts: () => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  let nextId = useRef(1);

  const showToast = useCallback(
    (payload: Omit<Toast, 'id'>): string => {
      const id = `toast_${nextId.current++}`;
      const newToast: Toast = { ...payload, id };
      setToasts((prev) => [...prev, newToast]);
      return id;
    },
    [],
  );

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, showToast, dismissToast, clearAllToasts }}>
      {children}
      <ToastContainer
        toasts={toasts}
        onDismiss={(id) => dismissToast(id)}
      />
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast deve ser usado dentro de ToastProvider');
  }
  return ctx;
};
