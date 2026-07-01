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
