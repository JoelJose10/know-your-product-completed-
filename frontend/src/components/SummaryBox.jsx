import { FileText, Tag, TrendingUp, RefreshCw } from 'lucide-react';

export default function SummaryBox({ summary, isLoading, jobId }) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-200/60 p-8 animate-slide-up">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center">
            <RefreshCw className="w-5 h-5 text-indigo-500 animate-spin" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Analyzing Document...</h2>
            <p className="text-sm text-slate-500">Extracting insights from your files</p>
          </div>
        </div>
        
        <div className="space-y-4">
          <div className="skeleton h-4 w-full"></div>
          <div className="skeleton h-4 w-11/12"></div>
          <div className="skeleton h-4 w-4/5"></div>
          <div className="skeleton h-4 w-9/12"></div>
          <div className="skeleton h-4 w-3/4"></div>
        </div>
        
        <div className="mt-6 pt-6 border-t border-slate-100">
          <div className="flex gap-3">
            <div className="skeleton h-6 w-20 rounded-full"></div>
            <div className="skeleton h-6 w-24 rounded-full"></div>
            <div className="skeleton h-6 w-16 rounded-full"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-200/60 p-8 animate-fade-in">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-100 to-slate-50 flex items-center justify-center">
            <FileText className="w-5 h-5 text-slate-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-800">Product Summary</h2>
        </div>
        
        <div className="bg-slate-50 rounded-xl p-6 border border-dashed border-slate-200">
          <p className="text-slate-500 text-center">
            Your product summary will appear here once you upload a document.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-200/60 p-8 animate-slide-up">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center">
            <FileText className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">
              {summary.title || 'Product Summary'}
            </h2>
            {jobId && (
              <p className="text-xs text-slate-400 font-mono">Job: {jobId.slice(0, 8)}...</p>
            )}
          </div>
        </div>
        
        {summary.confidence && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 rounded-full">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
            <span className="text-xs font-medium text-emerald-700">
              {Math.round(summary.confidence * 100)}% confidence
            </span>
          </div>
        )}
      </div>
      
      <div className="prose prose-slate prose-sm max-w-none">
        <p className="text-slate-600 leading-relaxed whitespace-pre-wrap">
          {summary.content}
        </p>
      </div>
      
      {summary.tags && summary.tags.length > 0 && (
        <div className="mt-6 pt-6 border-t border-slate-100">
          <div className="flex items-center gap-2 mb-3">
            <Tag className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Tags</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {summary.tags.map((tag, index) => (
              <span
                key={index}
                className="px-3 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 rounded-full hover:bg-indigo-100 transition-colors cursor-default"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
