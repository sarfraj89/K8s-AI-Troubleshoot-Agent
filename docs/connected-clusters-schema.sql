-- Phase 1 schema for production connected clusters.
-- Run this in the InsForge SQL Editor after the existing investigations table.

CREATE TABLE IF NOT EXISTS public.connected_clusters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'custom'
    CHECK (provider IN ('aws', 'azure', 'gcp', 'local', 'custom')),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'connected', 'disconnected', 'revoked')),
  agent_token_hash TEXT NOT NULL,
  agent_version TEXT,
  cluster_uid TEXT,
  kube_version TEXT,
  last_heartbeat_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_connected_clusters_user_id
  ON public.connected_clusters(user_id);

CREATE INDEX IF NOT EXISTS idx_connected_clusters_status
  ON public.connected_clusters(status);

CREATE INDEX IF NOT EXISTS idx_connected_clusters_last_heartbeat
  ON public.connected_clusters(last_heartbeat_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_connected_clusters_user_name
  ON public.connected_clusters(user_id, lower(name));

ALTER TABLE public.connected_clusters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own connected clusters"
  ON public.connected_clusters
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own connected clusters"
  ON public.connected_clusters
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own connected clusters"
  ON public.connected_clusters
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own connected clusters"
  ON public.connected_clusters
  FOR DELETE
  USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.cluster_agent_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id UUID NOT NULL REFERENCES public.connected_clusters(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  message TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cluster_agent_events_cluster_id
  ON public.cluster_agent_events(cluster_id);

CREATE INDEX IF NOT EXISTS idx_cluster_agent_events_created_at
  ON public.cluster_agent_events(created_at DESC);

ALTER TABLE public.cluster_agent_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view events for their own connected clusters"
  ON public.cluster_agent_events
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1
      FROM public.connected_clusters c
      WHERE c.id = cluster_agent_events.cluster_id
        AND c.user_id = auth.uid()
    )
  );

CREATE TABLE IF NOT EXISTS public.investigation_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cluster_id UUID NOT NULL REFERENCES public.connected_clusters(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT NOT NULL DEFAULT 'investigate',
  namespace TEXT NOT NULL DEFAULT 'default',
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'completed', 'failed')),
  requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  evidence JSONB,
  diagnosis JSONB,
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_investigation_jobs_cluster_id
  ON public.investigation_jobs(cluster_id);

CREATE INDEX IF NOT EXISTS idx_investigation_jobs_user_id
  ON public.investigation_jobs(user_id);

CREATE INDEX IF NOT EXISTS idx_investigation_jobs_status
  ON public.investigation_jobs(status);

ALTER TABLE public.investigation_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own investigation jobs"
  ON public.investigation_jobs
  FOR SELECT
  USING (auth.uid() = user_id);
