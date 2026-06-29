import { CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { ProgressUpdate, ProgressStep } from '../types';

interface ProgressTrackerProps {
  progress: ProgressUpdate[];
  isLoading: boolean;
}

const STEP_LABELS: Record<ProgressStep, string> = {
  pods: 'Checking Pods',
  logs: 'Reading Logs',
  events: 'Analyzing Events',
  deployments: 'Inspecting Deployments',
  network: 'Checking Networking',
  ai: 'AI Reasoning',
  complete: 'Complete',
};

export function ProgressTracker({ progress, isLoading }: ProgressTrackerProps) {
  const getStepStatusClasses = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />,
          bg: 'bg-emerald-500/5 border-emerald-500/10',
          text: 'text-slate-350',
        };
      case 'in-progress':
        return {
          icon: <Loader2 className="w-5 h-5 text-cyan-400 animate-spin flex-shrink-0" />,
          bg: 'bg-cyan-500/5 border-cyan-500/20 shadow-sm shadow-cyan-500/5 animate-pulse-slow',
          text: 'text-slate-100 font-semibold',
        };
      case 'error':
        return {
          icon: <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />,
          bg: 'bg-red-500/5 border-red-500/25',
          text: 'text-red-200',
        };
      default:
        return {
          icon: <Clock className="w-5 h-5 text-slate-700 flex-shrink-0" />,
          bg: 'bg-transparent border-transparent opacity-50',
          text: 'text-slate-500',
        };
    }
  };

  if (!isLoading && progress.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        {progress.map((step) => {
          const classes = getStepStatusClasses(step.status);
          return (
            <div
              key={step.step}
              className={`flex items-start gap-4 p-3 rounded-xl border transition-all duration-300 ${classes.bg}`}
            >
              <div className="mt-0.5">{classes.icon}</div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm tracking-tight ${classes.text}`}>
                  {STEP_LABELS[step.step]}
                </p>
                {step.message && (
                  <p className="text-xs font-mono text-slate-400/90 mt-1 truncate max-w-full leading-relaxed bg-slate-950/40 p-1.5 px-2 rounded-lg border border-slate-900/60">
                    {step.message}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
