import { useEffect, useState } from 'react';
import { Server, RefreshCw, AlertCircle, ChevronDown, CheckCircle2, WifiOff } from 'lucide-react';
import { KubeContext } from '../types';
import { investigationApi } from '../services/api';

interface ClusterSelectorProps {
  selectedContext: string | null;
  onSelect: (context: string) => void;
  onReadyChange?: (ready: boolean) => void;
}

export function ClusterSelector({ selectedContext, onSelect, onReadyChange }: ClusterSelectorProps) {
  const [contexts, setContexts] = useState<KubeContext[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchClusters = async () => {
    setLoading(true);
    setError(null);
    try {
      const { contexts: fetched } = await investigationApi.getClusters();
      setContexts(fetched);

      // Auto-select current context if nothing selected yet
      if (!selectedContext) {
        const current = fetched.find((c) => c.is_current && c.reachable);
        const firstReady = fetched.find((c) => c.reachable);
        if (current) onSelect(current.name);
        else if (firstReady) onSelect(firstReady.name);
        else if (fetched.length > 0) onSelect(fetched[0].name);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clusters');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClusters();
  }, []);

  const selectedCluster = contexts.find((ctx) => ctx.name === selectedContext) ?? null;
  const isSelectedReady = Boolean(selectedCluster?.reachable);

  useEffect(() => {
    onReadyChange?.(isSelectedReady);
  }, [isSelectedReady, onReadyChange]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-400 animate-pulse">
        <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
        Scanning local config for clusters...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl">
          <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-300">Cannot connect to Kubernetes</p>
            <pre className="text-xs text-red-400 mt-1.5 whitespace-pre-wrap font-mono leading-relaxed">{error}</pre>
          </div>
        </div>
        <button
          onClick={fetchClusters}
          className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Scan
        </button>
      </div>
    );
  }

  if (contexts.length === 0) {
    return (
      <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl">
        <AlertCircle className="w-5 h-5 text-amber-450 mt-0.5 flex-shrink-0" />
        <p className="text-sm text-amber-300 leading-relaxed">
          No Kubernetes clusters found. Make sure your kubeconfig is configured with at least one context.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Target Cluster Context</label>
      <div className="relative max-w-xl">
        <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none">
          <Server className="w-4 h-4 text-indigo-400" />
        </div>
        <select
          value={selectedContext || ''}
          onChange={(e) => onSelect(e.target.value)}
          className="w-full pl-10 pr-10 py-3 bg-slate-950/40 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 transition font-sans text-sm appearance-none cursor-pointer"
        >
          {contexts.map((ctx) => (
            <option key={ctx.name} value={ctx.name} className="bg-slate-900 text-slate-200">
              {ctx.name}{ctx.is_current ? ' (current)' : ''}{ctx.reachable ? '' : ' - unreachable'}
            </option>
          ))}
        </select>
        <div className="absolute inset-y-0 right-3.5 flex items-center pointer-events-none">
          <ChevronDown className="w-4 h-4 text-slate-500" />
        </div>
      </div>

      {selectedCluster && (
        <div
          className={`max-w-xl rounded-xl border p-4 ${
            isSelectedReady
              ? 'bg-emerald-500/10 border-emerald-500/20'
              : 'bg-red-500/10 border-red-500/20'
          }`}
        >
          <div className="flex items-start gap-3">
            {isSelectedReady ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
            )}
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className={`text-sm font-semibold ${isSelectedReady ? 'text-emerald-300' : 'text-red-300'}`}>
                  {isSelectedReady ? 'Cluster ready' : 'Cluster unreachable'}
                </p>
                {selectedCluster.namespace && (
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate-950/50 text-slate-300 border border-slate-800">
                    ns/{selectedCluster.namespace}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1 truncate">
                {selectedCluster.cluster || selectedCluster.name}
              </p>
              {selectedCluster.error && !isSelectedReady && (
                <pre className="text-xs text-red-400 mt-2 whitespace-pre-wrap font-mono leading-relaxed">
                  {selectedCluster.error}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
