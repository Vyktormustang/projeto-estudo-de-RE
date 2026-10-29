import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';

interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    const saved = localStorage.getItem('forja_theme') as 'light' | 'dark' | null;
    if (saved) {
      setTheme(saved);
    }
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('forja_theme', next);
      return next;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme deve ser usado dentro de ThemeProvider');
  }
  return ctx;
};

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const Icon = theme === 'dark' ? Sun : Moon;
  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-surface hover:bg-surface-hover transition-colors text-slate-400 hover:text-white"
      title={theme === 'dark' ? 'Alternar para tema claro' : 'Alternar para tema escuro'}
      aria-label="Alternar tema"
    >
      <Icon size={16} />
    </button>
  );
};

export default ThemeProvider;
