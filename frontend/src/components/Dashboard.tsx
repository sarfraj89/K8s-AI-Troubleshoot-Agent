import { useCallback, useState } from 'react';
import { AlertCircle, Loader2, LogOut, CheckCircle2, Terminal } from 'lucide-react';
import { ProgressTracker } from './ProgressTracker';
import { DiagnosisCard } from './DiagnosisCard';
import { InvestigationHistory } from './InvestigationHistory';
import { ClusterSelector } from './ClusterSelector';
import { DiagnosisResult, InvestigationResponse } from '../types';
import { investigationApi } from '../services/api';
import { CHANNELS, insforgeClient, TABLES } from '../services/insforge';
import { useAuth } from '../hooks/useAuth';
import { useInvestigationProgress } from '../hooks/useInvestigationProgress';

export function Dashboard() {
  const { user, logout } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [historyVersion, setHistoryVersion] = useState(0);
  const [selectedContext, setSelectedContext] = useState<string | null>(null);
  const [selectedContextReady, setSelectedContextReady] = useState(false);
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const {
    progress,
    resetProgress,
    startFallbackProgress,
    completeProgress,
    failProgress,
  } = useInvestigationProgress(user?.id);

  const handleContextReadyChange = useCallback((ready: boolean) => {
    setSelectedContextReady(ready);
  }, []);

  const handleInvestigate = async () => {
    if (!user?.id) {
      setError('User not authenticated');
      return;
    }

    setIsLoading(true);
    setError(null);
    setDiagnosis(null);
    setIsHealthy(null);
    resetProgress();
    const stopFallbackProgress = startFallbackProgress();

    try {
      const result: InvestigationResponse = await investigationApi.investigate({
        user_id: user.id,
        progress_channel: CHANNELS.USER_PROGRESS(user.id),
        namespace: 'default',
        context: selectedContext ?? undefined,
      });

      // Check if cluster was healthy (no issues found)
      const pods = result.investigation?.pods as Record<string, unknown> | undefined;
      const healthy = Boolean(pods?.healthy) && !result.diagnosis.error;
      setIsHealthy(healthy);

      // Save to InsForge database
      const investigationRecord = {
        user_id: user.id,
        timestamp: new Date().toISOString(),
        root_cause: result.diagnosis.root_cause,
        confidence: result.diagnosis.confidence,
        namespace: result.namespace || 'default',
        status: 'success',
        explanation: result.diagnosis.explanation,
        fix: result.diagnosis.fix,
        kubectl_command:
          result.diagnosis.kubectl_command || result.diagnosis.kubectl_commands?.[0] || '',
      };

      const { error: saveError } = await insforgeClient
        .database.from(TABLES.INVESTIGATIONS)
        .insert([investigationRecord]);

      if (saveError) {
        console.warn('Failed to save investigation to history:', saveError);
      } else {
        setHistoryVersion((v) => v + 1);
      }

      completeProgress();
      setDiagnosis(result.diagnosis);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Investigation failed';
      setError(errorMessage);
      failProgress();
      console.error('Investigation error:', err);
    } finally {
      stopFallbackProgress();
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-950/40 backdrop-blur-xl border-b border-slate-900">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative p-2 bg-slate-900/80 border border-slate-800 rounded-lg shadow-inner">
              <div className="absolute -inset-px rounded-lg bg-gradient-to-tr from-indigo-500/20 to-cyan-500/20 opacity-60 blur-sm pointer-events-none" />
              <Terminal className="relative w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 to-slate-300">K8s AI Troubleshooter</h1>
              <p className="text-xs text-slate-400 font-mono">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-slate-300 hover:text-slate-100 bg-slate-900/60 hover:bg-slate-900 border border-slate-850 hover:border-slate-700 rounded-lg transition-all duration-200 active:scale-[0.97] shadow-sm"
          >
            <LogOut className="w-3.5 h-3.5" />
            Logout
          </button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6 animate-fade-in">
        {/* Investigation Card */}
        <div className="card-lift relative overflow-hidden bg-slate-900/20 backdrop-blur-md border border-slate-800/80 hover:border-slate-700/80 rounded-2xl p-6 shadow-xl hover:shadow-glow">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/10 to-cyan-500/10 rounded-2xl opacity-10 blur-sm pointer-events-none"></div>
          <h2 className="text-lg font-bold text-slate-100 mb-1 tracking-tight">Investigate Cluster</h2>
          <p className="text-sm text-slate-400 mb-6 max-w-2xl leading-relaxed">
            Select a cluster context from your config to begin diagnostic scanning. The agent checks pods, logs, events,
            deployments, and network configurations to identify root causes and fixes automatically.
          </p>

          {/* Cluster Selector */}
          <div className="mb-6">
            <ClusterSelector
              selectedContext={selectedContext}
              onSelect={setSelectedContext}
              onReadyChange={handleContextReadyChange}
            />
          </div>

          <button
            onClick={handleInvestigate}
            disabled={isLoading || !selectedContext || !selectedContextReady}
            className="px-6 py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 disabled:from-slate-800 disabled:to-slate-800/80 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-500/10 hover:shadow-indigo-500/30 transition-all duration-200 active:scale-[0.98] flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-white" />
            ) : (
              <Terminal className="w-4 h-4 text-white" />
            )}
            {isLoading ? 'Investigating...' : selectedContextReady ? 'Start Investigation' : 'Select Ready Cluster'}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-red-300">Investigation Failed</p>
              <pre className="text-xs text-red-400 mt-1 whitespace-pre-wrap font-mono leading-relaxed">{error}</pre>
            </div>
          </div>
        )}

        {/* Progress */}
        {(isLoading || progress.some((s) => s.status !== 'pending')) && (
          <div className="bg-slate-900/20 backdrop-blur-md border border-slate-800/80 hover:border-slate-700/70 rounded-2xl p-6 shadow-xl transition-colors duration-300">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
              {isLoading ? 'Investigation in Progress' : 'Investigation Finished'}
            </h2>
            <ProgressTracker progress={progress} isLoading={isLoading} />
          </div>
        )}

        {/* Healthy cluster message */}
        {!isLoading && isHealthy && diagnosis && (
          <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-emerald-300">No issues found</p>
              <p className="text-xs text-emerald-400/80 mt-0.5">
                Cluster context appears healthy. AI analysis details provided below.
              </p>
            </div>
          </div>
        )}

        {/* Diagnosis */}
        {diagnosis && !isLoading && (
          <div className="space-y-3">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Diagnosis Result</h2>
            <DiagnosisCard diagnosis={diagnosis} />
          </div>
        )}

        {/* History */}
        <div className="bg-slate-900/20 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 shadow-xl">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Investigation History</h2>
          <InvestigationHistory refreshKey={historyVersion} />
        </div>
      </div>
    </div>
  );
}
