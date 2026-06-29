import { useState } from 'react';
import { Copy, CheckCircle2 } from 'lucide-react';
import { DiagnosisResult } from '../types';

interface DiagnosisCardProps {
  diagnosis: DiagnosisResult;
}

export function DiagnosisCard({ diagnosis }: DiagnosisCardProps) {
  const [copiedCommand, setCopiedCommand] = useState<string | null>(null);
  const commands = (
    diagnosis.kubectl_commands?.length
      ? diagnosis.kubectl_commands
      : [diagnosis.kubectl_command]
  ).filter((command): command is string => Boolean(command));

  const copyToClipboard = (text: string, command: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCommand(command);
    setTimeout(() => setCopiedCommand(null), 2000);
  };

  if (diagnosis.error) {
    return (
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-6 space-y-2">
        <h3 className="font-semibold text-amber-400">Diagnosis Unavailable</h3>
        <p className="text-sm text-slate-300">{diagnosis.error}</p>
        <p className="text-xs text-slate-400 mt-2">{diagnosis.explanation}</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 space-y-6 shadow-xl shadow-black/10">
      {/* Root Cause */}
      <div className="relative overflow-hidden rounded-xl border border-red-500/10 bg-gradient-to-r from-red-500/5 to-transparent p-5">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Root Cause</h3>
        </div>
        <p className="text-xl md:text-2xl font-bold text-white tracking-tight">{diagnosis.root_cause}</p>
      </div>

      {/* Explanation */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Explanation</h3>
        <p className="text-slate-350 text-sm leading-relaxed">{diagnosis.explanation}</p>
      </div>

      {/* Fix */}
      <div className="rounded-xl border border-emerald-500/10 bg-emerald-500/[0.02] p-5 space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Suggested Fix</h3>
        <p className="text-slate-300 text-sm leading-relaxed">{diagnosis.fix}</p>
      </div>

      {/* Kubectl Commands */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Kubectl Commands</h3>
        <div className="space-y-2.5">
          {commands.map((cmd, idx) => (
            <div
              key={idx}
              className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3 px-4 flex items-center justify-between group transition-all duration-200 hover:border-slate-700/80"
            >
              <code className="text-xs text-slate-200 font-mono break-all selection:bg-slate-800">{cmd}</code>
              <button
                onClick={() => copyToClipboard(cmd, `cmd-${idx}`)}
                className="ml-3 p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-all flex-shrink-0 opacity-0 group-hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-1 focus:ring-slate-700"
                title="Copy to clipboard"
              >
                {copiedCommand === `cmd-${idx}` ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 animate-in fade-in zoom-in-95 duration-150" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Prevention */}
      {diagnosis.prevention_recommendation && (
        <div className="space-y-2 border-t border-slate-800/50 pt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Prevention Recommendations</h3>
          <p className="text-slate-350 text-sm leading-relaxed">{diagnosis.prevention_recommendation}</p>
        </div>
      )}

      {/* Confidence */}
      <div className="border-t border-slate-800/50 pt-5 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Confidence Score</h3>
          <span className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">{diagnosis.confidence}%</span>
        </div>
        <div className="relative w-full bg-slate-950 border border-slate-850 rounded-full h-3 overflow-hidden p-0.5">
          <div
            className="relative bg-gradient-to-r from-cyan-500 to-indigo-500 h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_8px_rgba(34,211,238,0.3)] overflow-hidden"
            style={{ width: `${diagnosis.confidence}%` }}
          >
            <span className="absolute inset-0 shimmer-bar animate-shimmer rounded-full" />
          </div>
        </div>
        {diagnosis.confidence_reasons?.length > 0 && (
          <div className="bg-slate-950/40 border border-slate-900/60 rounded-xl p-3 space-y-1.5">
            <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Analysis Insights</p>
            <ul className="space-y-1">
              {diagnosis.confidence_reasons.map((reason, idx) => (
                <li key={idx} className="text-xs text-slate-400 flex items-start gap-2">
                  <span className="text-cyan-500 select-none mt-0.5">•</span>
                  <span className="leading-relaxed">{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
