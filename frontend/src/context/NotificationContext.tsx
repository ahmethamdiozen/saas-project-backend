import React, { createContext, useContext, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, X, Info, HelpCircle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
}

interface PromptOptions {
  title: string;
  message: string;
  placeholder?: string;
  defaultValue?: string;
  onConfirm: (value: string) => void;
}

interface NotificationContextType {
  showToast: (message: string, type?: ToastType) => void;
  confirm: (options: ConfirmOptions) => void;
  prompt: (options: PromptOptions) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [confirmState, setConfirmState] = useState<ConfirmOptions | null>(null);
  const [promptState, setPromptState] = useState<(PromptOptions & { isOpen: boolean }) | null>(null);
  const [promptValue, setPromptValue] = useState('');

  const showToast = useCallback((message: string, type: ToastType = 'success') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const confirm = useCallback((options: ConfirmOptions) => {
    setConfirmState(options);
  }, []);

  const prompt = useCallback((options: PromptOptions) => {
    setPromptState({ ...options, isOpen: true });
    setPromptValue(options.defaultValue || '');
  }, []);

  return (
    <NotificationContext.Provider value={{ showToast, confirm, prompt }}>
      {children}

      {/* TOASTS CONTAINER */}
      <div className="fixed top-24 right-6 z-[200] flex flex-col gap-3 pointer-events-none">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ x: 100, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 100, opacity: 0 }}
              className={`pointer-events-auto min-w-[300px] p-4 rounded-2xl border backdrop-blur-xl shadow-2xl flex items-center justify-between gap-4 ${
                toast.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' :
                toast.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-400' :
                'bg-blue-500/10 border-blue-500/20 text-blue-400'
              }`}
            >
              <div className="flex items-center gap-3 font-bold text-sm">
                {toast.type === 'success' && <CheckCircle2 size={20} />}
                {toast.type === 'error' && <AlertCircle size={20} />}
                {toast.type === 'info' && <Info size={20} />}
                {toast.message}
              </div>
              <button onClick={() => setToasts((p) => p.filter((t) => t.id !== toast.id))} className="opacity-50 hover:opacity-100 transition-opacity">
                <X size={16} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* CONFIRM MODAL */}
      <AnimatePresence>
        {confirmState && (
          <div className="fixed inset-0 z-[210] flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm">
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="w-full max-w-sm bg-[#0b0e14] border border-white/10 rounded-[2.5rem] p-8 shadow-2xl space-y-6">
              <div className="w-14 h-14 bg-accent/10 text-accent rounded-2xl flex items-center justify-center mx-auto">
                <HelpCircle size={32} />
              </div>
              <div className="text-center space-y-2">
                <h3 className="text-xl font-black text-white">{confirmState.title}</h3>
                <p className="text-sm text-gray-400 font-medium">{confirmState.message}</p>
              </div>
              <div className="flex gap-3">
                <button onClick={() => setConfirmState(null)} className="flex-1 py-3 text-sm font-bold text-gray-500 hover:text-white transition-colors">
                  {confirmState.cancelText || 'Cancel'}
                </button>
                <button 
                  onClick={() => { confirmState.onConfirm(); setConfirmState(null); }} 
                  className="flex-1 py-3 bg-accent text-white rounded-xl font-black text-sm shadow-xl shadow-accent/20 hover:scale-105 active:scale-95 transition-all"
                >
                  {confirmState.confirmText || 'Confirm'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* PROMPT MODAL */}
      <AnimatePresence>
        {promptState?.isOpen && (
          <div className="fixed inset-0 z-[210] flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm">
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="w-full max-w-md bg-[#0b0e14] border border-white/10 rounded-[2.5rem] p-8 shadow-2xl space-y-6">
              <div className="text-center space-y-2">
                <h3 className="text-2xl font-black text-white">{promptState.title}</h3>
                <p className="text-sm text-gray-400 font-medium">{promptState.message}</p>
              </div>
              <div className="relative">
                <input
                  autoFocus
                  type="text"
                  placeholder={promptState.placeholder || "Enter value..."}
                  value={promptValue}
                  onChange={(e) => setPromptValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && promptValue.trim()) {
                      promptState.onConfirm(promptValue);
                      setPromptState(null);
                    }
                  }}
                  className="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white font-medium outline-none focus:border-primary transition-all"
                />
              </div>
              <div className="flex gap-3">
                <button onClick={() => setPromptState(null)} className="flex-1 py-3 text-sm font-bold text-gray-500 hover:text-white transition-colors text-white font-black">
                  Cancel
                </button>
                <button 
                  disabled={!promptValue.trim()}
                  onClick={() => { promptState.onConfirm(promptValue); setPromptState(null); }} 
                  className="flex-1 py-3 bg-primary text-white rounded-xl font-black text-sm shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 text-white font-black"
                >
                  Continue
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) throw new Error('useNotifications must be used within a NotificationProvider');
  return context;
};
