# AI Kubernetes Troubleshooting Agent - Complete Integration Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │        Frontend (React + TypeScript + Vite)          │   │
│  │                                                      │   │
│  │  • LoginForm (InsForge Auth)                        │   │
│  │  • Dashboard (Investigation UI)                     │   │
│  │  • ProgressTracker (Live Updates)                   │   │
│  │  • DiagnosisCard (Results)                          │   │
│  │  • InvestigationHistory (Database)                  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP (localhost:3000)
┌──────────────────▼──────────────────────────────────────────┐
│              InsForge Backend Services                       │
│  • Authentication (Email/Password)                           │
│  • Database (investigations table)                           │
│  • Realtime WebSockets (progress updates)                    │
│  • File Storage (optional: save reports)                     │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP (CORS enabled)
┌──────────────────▼──────────────────────────────────────────┐
│              FastAPI Backend (Python)                        │
│  • POST /investigate (Orchestration)                         │
│  • Kubernetes Evidence Collection                            │
│  • AI Reasoning via OpenRouter                              │
│  • Root Cause Analysis                                       │
│  • Fix Recommendations                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬─────────────┐
        │          │          │             │
        ▼          ▼          ▼             ▼
    ┌─────────────────────────────────────────┐
    │     Kubernetes Cluster (localhost)      │
    │                                        │
    │  • kubectl (via subprocess)            │
    │  • Pod inspection                      │
    │  • Log collection                      │
    │  • Event analysis                      │
    │  • Deployment inspection               │
    │  • Network inspection                  │
    └─────────────────────────────────────────┘
        │
        └──────────────┬───────────────┐
                       │               │
                       ▼               ▼
                   ┌──────────┐    ┌──────────┐
                   │ OpenAI  │    │ OpenAI  │
                   │ (via    │    │ (direct │
                   │OpenRouter)   │ API opt.)
                   └──────────┘    └──────────┘
```

## Setup Instructions

### Phase 1: Backend Setup

#### 1.1 Kubernetes Environment
Ensure you have:
- Local Kubernetes cluster (minikube, kind, Docker Desktop)
- kubectl configured and accessible
- Some failing/interesting pods in the cluster to investigate

#### 1.2 Backend Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
```

#### 1.3 Backend Environment
Create `backend/.env`:
```env
# OpenRouter API Key (get from InsForge or OpenRouter.ai)
OPENROUTER_API_KEY=sk_live_xxxxx

# Optional: LLM Model preference
LLM_MODEL=openai/gpt-4

# Logging
LOG_LEVEL=INFO
```

#### 1.4 Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Test it:
```bash
curl http://localhost:8000/health
```

### Phase 2: InsForge Setup

#### 2.1 Create InsForge Project
1. Go to https://insforge.io
2. Create a new project (or use existing)
3. Get your API credentials:
   - **Base URL**: `https://your-app.region.insforge.app`
   - **Anon Key**: From Settings → API Keys

#### 2.2 Enable Authentication
1. Go to InsForge Dashboard → Auth
2. Enable Email/Password authentication
3. No additional configuration needed

#### 2.3 Create Database Tables

Use InsForge Dashboard SQL Editor or use the REST API to create tables:

**Table: `public.investigations`**

```sql
CREATE TABLE public.investigations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  root_cause TEXT NOT NULL,
  explanation TEXT,
  fix TEXT,
  kubectl_command TEXT,
  confidence INTEGER DEFAULT 0,
  namespace TEXT DEFAULT 'default',
  status TEXT DEFAULT 'success' CHECK (status IN ('success', 'failed')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for faster queries
CREATE INDEX idx_investigations_user_id ON public.investigations(user_id);
CREATE INDEX idx_investigations_timestamp ON public.investigations(timestamp DESC);

-- Set RLS policies if using row-level security
ALTER TABLE public.investigations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own investigations"
  ON public.investigations
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own investigations"
  ON public.investigations
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

**Table: `public.progress_updates` (Optional, for real-time features)**

```sql
CREATE TABLE public.progress_updates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  step TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in-progress', 'completed', 'error')),
  message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_progress_updates_investigation_id ON public.progress_updates(investigation_id);
```

**Table: `public.connected_clusters` (Phase 1 for in-cluster agents)**

Run the full schema in [`docs/connected-clusters-schema.sql`](./docs/connected-clusters-schema.sql).

This table tracks clusters connected by a lightweight agent installed inside EKS,
AKS, GKE, local kind/minikube, or any Kubernetes cluster.

Key columns:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Cluster connection id |
| user_id | UUID | Owner in `auth.users` |
| name | TEXT | User-visible cluster name |
| provider | TEXT | `aws`, `azure`, `gcp`, `local`, or `custom` |
| status | TEXT | `pending`, `connected`, `disconnected`, or `revoked` |
| agent_token_hash | TEXT | Hashed token for the future in-cluster agent |
| agent_version | TEXT | Agent version reported by heartbeat |
| cluster_uid | TEXT | Kubernetes cluster UID when available |
| kube_version | TEXT | Kubernetes version reported by heartbeat |
| last_heartbeat_at | timestamptz | Last successful agent heartbeat |
| metadata | JSONB | Provider labels/region/account metadata |

The companion `public.cluster_agent_events` table stores future agent lifecycle
events such as install, heartbeat, disconnect, token rotation, and investigation
job transitions.

### Phase 4: In-Cluster Agent MVP

The cloud-cluster path uses a read-only polling agent:

1. User creates a connected cluster in the dashboard.
2. Backend returns a one-time visible agent token and Helm install command.
3. User installs `charts/k8s-ai-agent` into EKS, AKS, GKE, or another cluster.
4. Agent sends `POST /agent/heartbeat`.
5. User queues an investigation with `POST /connected-clusters/{id}/investigate`.
6. Agent polls `GET /agent/jobs/next`, collects evidence, and posts the result.
7. Backend runs the existing AI diagnosis on submitted evidence.

For local chart testing:

```bash
docker build -t k8s-ai-agent:0.1.0 ./agent

helm install k8s-ai-agent ./charts/k8s-ai-agent \
  --namespace k8s-ai-agent \
  --create-namespace \
  --set backendUrl=http://host.docker.internal:8000 \
  --set clusterId=<cluster-id> \
  --set agentToken=<agent-token>
```

### Phase 3: Frontend Setup

#### 3.1 Install Dependencies
```bash
cd frontend
npm install
```

#### 3.2 Configure Environment
Create `frontend/.env`:
```env
VITE_INSFORGE_URL=https://your-app.region.insforge.app
VITE_INSFORGE_ANON_KEY=your-anon-key-here
VITE_BACKEND_URL=http://localhost:8000
VITE_ENV=development
```

#### 3.3 Start Development Server
```bash
npm run dev
```

Access at http://localhost:3000

### Phase 4: End-to-End Testing

#### 4.1 Test Login Flow
1. Navigate to http://localhost:3000
2. Click "Don't have an account? Sign up"
3. Create new account with test email
4. Verify redirect to dashboard

#### 4.2 Test Investigation
1. Click "Investigate Cluster" button
2. Watch progress tracker update
3. See diagnosis appear with:
   - Root cause
   - Explanation
   - Suggested fix
   - kubectl commands
   - Confidence score

#### 4.3 Test History
1. Run investigation again
2. Scroll to "Investigation History"
3. See both investigations in table
4. Verify timestamps and confidence scores match

#### 4.4 Test Error Handling
- Stop backend, try investigation → should show error
- Invalid InsForge credentials → should show auth error
- Network failure → should show timeout message

## Backend API Specification

### Endpoint: `POST /investigate`

**Description:** Run full Kubernetes investigation and get AI diagnosis

**Request:**
```http
POST /investigate HTTP/1.1
Host: localhost:8000
Content-Type: application/json
```

**Response (Success):**
```json
{
  "status": "success",
  "investigation": {
    "pods": {
      "healthy": 10,
      "problematic_pods": [
        {
          "name": "payment-service-xyz",
          "namespace": "default",
          "status": "CrashLoopBackOff",
          "message": "Back-off restarting failed container"
        }
      ]
    },
    "logs": {
      "collected_for": 2,
      "entries": [
        {
          "pod": "payment-service-xyz",
          "logs": "Error: DATABASE_URL environment variable not set"
        }
      ]
    },
    "events": {
      "watched_reasons_found": 3,
      "events": [...]
    },
    "deployments": {
      "total_deployments": 5,
      "unhealthy_deployments": [...]
    },
    "network": {
      "issues": [...]
    }
  },
  "diagnosis": {
    "root_cause": "DATABASE_URL environment variable missing",
    "explanation": "The payment-service deployment is missing the required DATABASE_URL environment variable, causing the application to fail during startup and enter a CrashLoopBackOff state.",
    "fix": "Add the DATABASE_URL environment variable to the payment-service deployment with the correct database connection string.",
    "kubectl_command": "kubectl set env deployment/payment-service DATABASE_URL=postgresql://user:pass@db:5432/mydb -n default",
    "kubectl_commands": [
      "kubectl set env deployment/payment-service DATABASE_URL=postgresql://user:pass@db:5432/mydb -n default",
      "kubectl rollout restart deployment/payment-service -n default"
    ],
    "confidence": 92,
    "confidence_reasons": [
      "Pod logs clearly show DATABASE_URL is missing",
      "Error message matches common environment variable issues",
      "Timing of failures correlates with deployment",
      "Pattern matches previous similar incidents"
    ],
    "prevention_recommendation": "Use ConfigMaps or Secrets for environment variables, validate required variables before deployment, and use Init containers to verify configuration before starting main application."
  }
}
```

**Response (Error):**
```json
{
  "detail": "Investigation failed: Connection to Kubernetes cluster failed"
}
```

**Status Codes:**
- `200 OK` - Investigation successful
- `500 Internal Server Error` - Investigation or diagnosis failed

## Frontend API Integration

### API Client Location
`frontend/src/services/api.ts`

### Usage Example
```typescript
import { investigationApi } from '../services/api';

// In your component
const result = await investigationApi.investigate();
// result.diagnosis contains the diagnosis object
```

### Error Handling
All API calls return `{data, error}` from InsForge SDK, or throw errors:

```typescript
try {
  const result = await investigationApi.investigate();
  // Handle success
} catch (error) {
  // Handle error
  console.error(error.message);
}
```

## Database Schema

### investigations Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to auth.users |
| timestamp | timestamp with timezone | When investigation was run |
| root_cause | TEXT | Main issue identified |
| explanation | TEXT | Detailed explanation |
| fix | TEXT | Recommended fix |
| kubectl_command | TEXT | Command to apply fix |
| confidence | INTEGER | Confidence score 0-100 |
| namespace | TEXT | Kubernetes namespace |
| status | TEXT | 'success' or 'failed' |
| created_at | timestamp with timezone | Record creation time |
| updated_at | timestamp with timezone | Last update time |

### Indexes
- `idx_investigations_user_id` - For user-specific queries
- `idx_investigations_timestamp` - For sorting by date

### RLS Policies
- Users can only view their own investigations
- Users can only insert their own investigations

## Running the Full System

### Terminal 1: Kubernetes (if using local cluster)
```bash
# Ensure cluster is running
minikube start  # or equivalent for your setup
```

### Terminal 2: Backend
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

### Terminal 3: Frontend
```bash
cd frontend
npm run dev
```

### Terminal 4: Monitoring (Optional)
```bash
# Watch Kubernetes events
kubectl get events -A --watch

# Watch pods
kubectl get pods -A --watch
```

## Debugging

### Frontend Issues
1. Check browser console for errors
2. Check network tab for API calls
3. Verify InsForge credentials in `.env`
4. Check that backend is accessible

### Backend Issues
1. Check uvicorn console output
2. Verify Kubernetes cluster is accessible: `kubectl get pods`
3. Check OpenRouter API key in `.env`
4. Review logs in `backend/` directory

### InsForge Issues
1. Verify API credentials are correct
2. Check that auth is enabled in InsForge dashboard
3. Verify database tables exist with correct schema
4. Check RLS policies are not blocking queries

## Common Issues

### "Failed to connect to Kubernetes"
- Ensure kubectl is configured: `kubectl get pods`
- Check cluster is running

### "Investigation failed: ..."
- Check backend logs
- Verify investigation endpoint is working: `curl http://localhost:8000/health`

### "Authentication failed"
- Check InsForge credentials
- Ensure user is created in InsForge auth
- Check browser console for detailed error

### "Failed to save investigation"
- Verify `investigations` table exists
- Check RLS policies allow inserts
- Check user_id is correct

## Production Deployment

### Frontend
```bash
npm run build
# Deploy dist/ folder to static hosting
```

### Backend
1. Use production ASGI server (Gunicorn + Uvicorn)
2. Configure proper logging
3. Set up monitoring
4. Use environment-specific configs

### InsForge
- No deployment needed (fully managed)

## Support & Resources

- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Backend**: FastAPI, Python, Kubernetes
- **Database**: InsForge (PostgreSQL compatible)
- **Authentication**: InsForge Auth
- **AI**: OpenRouter API (via OpenAI-compatible interface)
