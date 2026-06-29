import { useEffect, useState } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Investigation } from '../types';
import { insforgeClient, TABLES } from '../services/insforge';
import { useAuth } from '../hooks/useAuth';

interface InvestigationHistoryProps {
  refreshKey?: number;
}

export function InvestigationHistory({ refreshKey = 0 }: InvestigationHistoryProps) {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchHistory = async () => {
      if (!user?.id) return;

      try {
        setLoading(true);
        setError(null);

        const { data, error: fetchError } = await insforgeClient
          .database.from(TABLES.INVESTIGATIONS)
          .select('*')
          .eq('user_id', user.id)
          .order('timestamp', { ascending: false })
          .limit(10);

        if (fetchError) throw fetchError;

        setInvestigations(data || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load history';
        setError(errorMessage);
        console.error('History fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [user?.id, refreshKey]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-slate-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
        <p className="text-sm text-slate-300">{error}</p>
      </div>
    );
  }

  if (investigations.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-950/20 rounded-2xl border border-dashed border-slate-800/80 p-6">
        <p className="text-slate-500 text-sm">No investigations recorded yet. Initiate a new probe to see history.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800/80 bg-slate-900/10 backdrop-blur-md shadow-lg shadow-black/5">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/40">
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Timestamp</th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Namespace</th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Root Cause</th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-400">Confidence</th>
              <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-400 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {investigations.map((inv) => (
              <tr key={inv.id} className="group hover:bg-slate-800/30 transition-colors duration-150">
                <td className="px-5 py-4 text-xs font-mono text-slate-400/90 whitespace-nowrap">
                  {inv.timestamp
                    ? new Date(inv.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) +
                      ' ' +
                      new Date(inv.timestamp).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
                    : '-'}
                </td>
                <td className="px-5 py-4 text-sm whitespace-nowrap">
                  <span className="font-mono text-xs bg-slate-950/60 text-slate-300 px-2.5 py-1 rounded-lg border border-slate-850">
                    {inv.namespace || 'default'}
                  </span>
                </td>
                <td className="px-5 py-4 text-sm font-medium text-slate-200">
                  <div className="truncate max-w-[280px]" title={inv.root_cause}>
                    {inv.root_cause}
                  </div>
                </td>
                <td className="px-5 py-4 text-sm whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-200 font-semibold w-8">{inv.confidence}%</span>
                    <div className="w-12 bg-slate-950 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full rounded-full"
                        style={{ width: `${inv.confidence}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-5 py-4 text-sm text-right whitespace-nowrap">
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                      inv.status === 'success'
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                        : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${inv.status === 'success' ? 'bg-emerald-450 animate-pulse' : 'bg-amber-450'}`} />
                    {inv.status || 'unknown'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
