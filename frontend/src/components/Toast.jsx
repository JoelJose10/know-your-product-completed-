import { useEffect, useState } from 'react';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

const ICONS = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
};

const COLORS = {
  success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
};

const ICON_COLORS = {
  success: 'text-emerald-500',
  error: 'text-red-500',
  info: 'text-blue-500',
};

export default function Toast({ message, type = 'info', duration = 5000, onClose }) {
  const [isVisible, setIsVisible] = useState(true);
  const Icon = ICONS[type];

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300); // Wait for animation
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300);
  };

  return (
    <div
      className={`
        flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg
        transition-all duration-300
        ${COLORS[type]}
        ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}
      `}
    >
      <Icon className={`w-5 h-5 ${ICON_COLORS[type]}`} />
      <p className="text-sm font-medium">{message}</p>
      <button
        onClick={handleClose}
        className="p-1 rounded-lg hover:bg-black/5 transition-colors"
        aria-label="Close notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
