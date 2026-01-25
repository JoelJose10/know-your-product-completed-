import { Sparkles } from 'lucide-react';

export default function Header() {
  return (
    <header className="w-full py-6 px-8 bg-white/80 backdrop-blur-sm border-b border-slate-200/60 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-slate-800 tracking-tight">
              Know Your Product
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              AI-Powered Documentation Analysis
            </p>
          </div>
        </div>
        
      </div>
    </header>
  );
}
