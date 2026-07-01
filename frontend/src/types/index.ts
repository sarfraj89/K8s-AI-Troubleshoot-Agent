// Investigation Types
export interface Investigation {
  id?: string;
  timestamp?: string;
  user_id?: string;
  root_cause: string;
  confidence: number;
  namespace?: string;
  context?: string;
  status?: string;
  explanation?: string;
  fix?: string;
  kubectl_command?: string;
}

export interface DiagnosisResult {
  root_cause: string;
  explanation: string;
  fix: string;
  kubectl_command: string;
  kubectl_commands: string[];
  confidence: number;
  confidence_reasons: string[];
  prevention_recommendation?: string;
  error?: string;
}

export interface InvestigationResponse {
  status: string;
  namespace?: string;
  context?: string;
  investigation: {
    pods: Record<string, unknown>;
    logs: Record<string, unknown>;
    events: Record<string, unknown>;
    deployments: Record<string, unknown>;
    network: Record<string, unknown>;
    context?: string;
  };
  diagnosis: DiagnosisResult;
}

// Cluster context types
export interface KubeContext {
  name: string;
  is_current: boolean;
  cluster?: string;
  namespace?: string;
  user?: string;
  reachable?: boolean;
  status?: 'ready' | 'unreachable';
  error?: string;
}

export interface ClusterListResponse {
  contexts: KubeContext[];
  count: number;
  mode?: 'local' | 'demo';
  demo_mode?: boolean;
  setup_error?: string;
}

// Connected cloud/in-cluster agent types
export type ClusterProvider = 'aws' | 'azure' | 'gcp' | 'local' | 'custom';

export type ConnectedClusterStatus = 'pending' | 'connected' | 'disconnected' | 'revoked';

export interface ConnectedCluster {
  id: string;
  user_id: string;
  name: string;
  provider: ClusterProvider;
  status: ConnectedClusterStatus;
  agent_version?: string | null;
  cluster_uid?: string | null;
  kube_version?: string | null;
  last_heartbeat_at?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ClusterAgentEvent {
  id: string;
  cluster_id: string;
  event_type: string;
  message?: string | null;
  payload?: Record<string, unknown>;
  created_at: string;
}

export interface ConnectClusterResponse {
  cluster: ConnectedCluster;
  agent_token: string;
  helm_command: string;
}

export interface InvestigationJob {
  id: string;
  cluster_id: string;
  user_id: string;
  type: 'investigate';
  namespace: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  requested_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  evidence?: Record<string, unknown> | null;
  diagnosis?: DiagnosisResult | null;
  error?: string | null;
}

// Investigation Progress Types
export type ProgressStep = 'pods' | 'logs' | 'events' | 'deployments' | 'network' | 'ai' | 'complete';

export interface ProgressUpdate {
  step: ProgressStep;
  status: 'pending' | 'in-progress' | 'completed' | 'error';
  message?: string;
  meta?: {
    messageId?: string;
    timestamp?: string;
  };
}

// User Auth Types
export interface User {
  id: string;
  email: string;
  created_at?: string;
  last_investigation?: string;
}

export interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}
