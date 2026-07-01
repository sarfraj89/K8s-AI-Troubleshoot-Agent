import { useEffect, useState } from 'react';
import { CheckCircle2, Cloud, Copy, Loader2, Plus, RefreshCw, RadioTower, Terminal } from 'lucide-react';
import { ClusterProvider, ConnectedCluster } from '../types';
import { connectedClusterApi } from '../services/api';

const PROVIDERS: { value: ClusterProvider; label: string }[] = [
  { value: 'aws', label: 'AWS EKS' },
  { value: 'azure', label: 'Azure AKS' },
  { value: 'gcp', label: 'GCP GKE' },
  { value: 'custom', label: 'Custom' },
  { value: 'local', label: 'Local' },
];

interface ConnectedClustersProps {
  userId: string;
}

export function ConnectedClusters({ userId }: ConnectedClustersProps) {
  const [clusters, setClusters] = useState<ConnectedCluster[]>([]);
  const [name, setName] = useState('');
  const [provider, setProvider] = useState<ClusterProvider>('aws');
  const [installCommand, setInstallCommand] = useState('');
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchClusters = async () => {
    setLoading(true);
    setError(null);
    try {
      const { clusters: fetched } = await connectedClusterApi.list(userId);
      setClusters(fetched);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load connected clusters');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClusters();
  }, [userId]);

  const createCluster = async () => {
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    setMessage(null);
    try {
      const result = await connectedClusterApi.create({
        user_id: userId,
        name: name.trim(),
        provider,
      });
      setInstallCommand(result.helm_command);
      setName('');
      setClusters((prev) => [result.cluster, ...prev]);
      setMessage('Cluster connection created. Install the agent with the command below.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create cluster connection');
    } finally {
      setCreating(false);
    }
  };

  const queueInvestigation = async (cluster: ConnectedCluster) => {
    setMessage(null);
    setError(null);
    try {
      const { job } = await connectedClusterApi.investigate({
        clusterId: cluster.id,
        userId,
      });
      setMessage(`Investigation job queued: ${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to queue investigation');
    }
  };

  const copyCommand = async () => {
    await navigator.clipboard.writeText(installCommand);
    setMessage('Install command copied.');
  };

  return (
    <div className="bg-slate-900/20 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 shadow-xl">
      <div className="flex items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Connected Cloud Clusters</h2>
          <p className="text-sm text-slate-400 mt-1">
            Install a read-only agent inside EKS, AKS, GKE, or any Kubernetes cluster.
          </p>
        </div>
        <button
          onClick={fetchClusters}
          className="p-2 rounded-lg border border-slate-800 bg-slate-950/50 text-slate-300 hover:text-slate-100 hover:border-slate-700 transition"
          title="Refresh clusters"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid md:grid-cols-[1fr_180px_auto] gap-3 mb-4">
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="production-eks-us-east-1"
          className="px-3 py-2.5 bg-slate-950/40 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
        />
        <select
          value={provider}
          onChange={(event) => setProvider(event.target.value as ClusterProvider)}
          className="px-3 py-2.5 bg-slate-950/40 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
        >
          {PROVIDERS.map((item) => (
            <option key={item.value} value={item.value} className="bg-slate-900">
              {item.label}
            </option>
          ))}
        </select>
        <button
          onClick={createCluster}
          disabled={creating || !name.trim()}
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-800 disabled:opacity-50 text-sm font-semibold text-white flex items-center justify-center gap-2 transition"
        >
          {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          Connect
        </button>
      </div>

      {installCommand && (
        <div className="mb-4 rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-4">
          <div className="flex items-center justify-between gap-2 mb-2">
            <p className="text-sm font-semibold text-cyan-300 flex items-center gap-2">
              <Terminal className="w-4 h-4" />
              Agent install command
            </p>
            <button onClick={copyCommand} className="text-cyan-300 hover:text-cyan-200" title="Copy command">
              <Copy className="w-4 h-4" />
            </button>
          </div>
          <pre className="text-xs text-cyan-100 whitespace-pre-wrap break-all font-mono leading-relaxed">
            {installCommand}
          </pre>
        </div>
      )}

      {message && (
        <div className="mb-4 flex items-center gap-2 text-sm text-emerald-300">
          <CheckCircle2 className="w-4 h-4" />
          {message}
        </div>
      )}
      {error && <div className="mb-4 text-sm text-red-300">{error}</div>}

      <div className="space-y-2">
        {clusters.length === 0 ? (
          <div className="border border-dashed border-slate-800 rounded-xl p-6 text-center text-sm text-slate-500">
            No cloud clusters connected yet.
          </div>
        ) : (
          clusters.map((cluster) => (
            <div
              key={cluster.id}
              className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 rounded-xl border border-slate-800 bg-slate-950/30 p-4"
            >
              <div className="min-w-0 flex items-start gap-3">
                <Cloud className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-100 truncate">{cluster.name}</p>
                  <p className="text-xs text-slate-400 font-mono">
                    {cluster.provider} · {cluster.status}
                    {cluster.last_heartbeat_at ? ` · heartbeat ${new Date(cluster.last_heartbeat_at).toLocaleString()}` : ''}
                  </p>
                </div>
              </div>
              <button
                onClick={() => queueInvestigation(cluster)}
                disabled={cluster.status !== 'connected'}
                className="px-3 py-2 rounded-lg border border-slate-800 bg-slate-900/60 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-semibold text-slate-200 hover:border-slate-700 flex items-center justify-center gap-2 transition"
              >
                <RadioTower className="w-3.5 h-3.5" />
                Queue Investigation
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
