# AI Kubernetes Troubleshooting Agent

Intelligent troubleshooting for Kubernetes clusters. Click investigate, get instant root cause analysis with AI-powered diagnosis and fix recommendations.

## ✨ Features

- **🔍 Intelligent Investigation**: Automatically analyzes pods, logs, events, deployments, and network
- **🤖 AI-Powered Diagnosis**: Uses OpenAI-compatible LLMs via OpenRouter for root cause analysis
- **💡 Fix Recommendations**: Provides actionable fix recommendations with kubectl commands
- **📊 Confidence Scoring**: Shows confidence level with reasoning breakdown
- **📈 Investigation History**: Stores all investigations with InsForge database
- **🔐 Authentication**: Secure login via InsForge
- **⚡ Real-time Progress**: Watch investigation progress live
- **🎨 Clean UI**: Minimal, professional dashboard designed for clarity

## 🚀 Quick Start

### Option 1: Automated Setup

```bash
chmod +x quickstart.sh
./quickstart.sh
```

Then follow the prompts.

### Option 2: Manual Setup

**Prerequisites:**
- Node.js 18+
- Python 3.8+
- Kubernetes cluster access
- InsForge account
- OpenRouter API key

**Step 1: Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate
pip install -r requirements.txt

# Create .env with:
# OPENROUTER_API_KEY=sk_live_xxxxx
```

**Step 2: Frontend Setup**
```bash
cd frontend
npm install

# Create .env with:
# VITE_INSFORGE_URL=https://your-app.region.insforge.app
# VITE_INSFORGE_ANON_KEY=your-anon-key-here
# VITE_BACKEND_URL=http://localhost:8000
```

**Step 3: Create InsForge Database Tables**

See [INTEGRATION.md](./INTEGRATION.md) for SQL schema.

**Step 4: Run Services**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

**Step 5: Open Browser**
```
http://localhost:3000
```

### Option 3: Docker Compose

```bash
# Update .env files for backend and frontend
docker compose up --build
```

Access at `http://localhost:3000`

## 📖 Documentation

- **[Frontend Setup](./frontend/SETUP.md)** - Frontend configuration and features
- **[Frontend README](./frontend/README.md)** - Frontend development guide
- **[Integration Guide](./INTEGRATION.md)** - Complete system architecture and setup
- **[Architecture Design](./AGENTS.md)** - System design and requirements

## 🏗️ Architecture

```
User Browser
    ↓ (React + TypeScript)
Frontend Dashboard (Port 3000)
    ↓ (HTTP + InsForge WebSocket)
InsForge Backend Services
    ↓ (Auth, Database, Realtime)
FastAPI Backend (Port 8000)
    ↓ (kubectl + Python SDK)
Kubernetes Cluster
    ↓ (Pod info, logs, events)
OpenAI/OpenRouter
    ↓ (LLM reasoning)
Root Cause + Fix Recommendations
```

## 📁 Project Structure

```
.
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/               # REST API endpoints
│   │   ├── ai/                # AI reasoning & LLM integration
│   │   ├── kubernetes/        # K8s investigation logic
│   │   ├── models/            # Data models
│   │   ├── services/          # Business logic
│   │   └── core/              # Configuration
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                   # React + TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── context/           # Context providers
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API & InsForge client
│   │   ├── types/             # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
├── docs/                       # Documentation
├── prompts/                    # AI system prompts
├── docker-compose.yml          # Local development setup
├── INTEGRATION.md              # Full integration guide
├── quickstart.sh               # Setup automation script
└── README.md                   # This file
```

## 🔧 Tech Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **Tailwind CSS 3.4** - Styling
- **Lucide React** - Icons
- **@insforge/sdk** - Backend integration
- **Axios** - HTTP client

### Backend
- **FastAPI** - Web framework
- **Python 3.8+** - Runtime
- **Pydantic** - Data validation
- **Loguru** - Logging
- **httpx** - Async HTTP client

### Infrastructure
- **InsForge** - BaaS (Auth, Database, Realtime)
- **OpenRouter** - LLM API (OpenAI-compatible)
- **Docker** - Containerization
- **Kubernetes** - Container orchestration

## 🎯 How It Works

### Investigation Flow

1. **User clicks "Investigate Cluster"**
   - Frontend triggers `POST /investigate`
   - Progress tracker starts showing live status

2. **Backend collects evidence**
   - Inspects all pods and their status
   - Collects logs from problematic pods
   - Analyzes Kubernetes events
   - Inspects deployment configurations
   - Checks network policies and connectivity

3. **AI analyzes evidence**
   - Sends all evidence to LLM (via OpenRouter)
   - LLM identifies root cause
   - LLM generates fix recommendations

4. **Results displayed**
   - Root cause highlighted
   - Explanation of why it occurred
   - Step-by-step fix instructions
   - Ready-to-copy kubectl commands
   - Confidence score with breakdown
   - Prevention recommendations

5. **Investigation saved**
   - Stored in InsForge database
   - Available in history table
   - Tied to authenticated user

## 🔐 Authentication

Users sign up with email/password via InsForge:
- Secure password hashing
- JWT session tokens
- Automatic session restoration
- Logout clears session

Only authenticated users can:
- Trigger investigations
- View investigation history
- Save investigation results

## 💾 Database Schema

### investigations Table
```sql
- id: UUID (primary key)
- user_id: UUID (foreign key to auth users)
- timestamp: timestamp with timezone
- root_cause: text
- explanation: text
- fix: text
- kubectl_command: text
- confidence: integer (0-100)
- namespace: text
- status: text ('success', 'failed')
```

### Indexes
- `idx_investigations_user_id` - Query by user
- `idx_investigations_timestamp` - Sort by date

### RLS Policies
- Users can only view their own investigations
- Users can only insert their own investigations

## 🧪 Testing

### Verify Backend
```bash
curl http://localhost:8000/health
```

### Verify Frontend
```bash
open http://localhost:3000
```

### Test Investigation
1. Sign up with test email
2. Click "Investigate Cluster"
3. Watch progress tracker
4. View diagnosis results
5. Check investigation history

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to connect to Kubernetes" | Ensure `kubectl get pods` works |
| "Investigation failed" | Check backend logs and VITE_BACKEND_URL |
| "Login failed" | Verify InsForge credentials in .env |
| "History not showing" | Ensure `investigations` table exists in InsForge |
| "Cannot find module" | Run `npm install` in frontend directory |

See [INTEGRATION.md](./INTEGRATION.md#troubleshooting) for detailed troubleshooting.

## 📚 API Reference

### Backend Endpoint: `POST /investigate`

**Response:**
```json
{
  "status": "success",
  "investigation": {...},
  "diagnosis": {
    "root_cause": "Pod in CrashLoopBackOff",
    "explanation": "...",
    "fix": "...",
    "kubectl_commands": ["kubectl edit deployment ...", "kubectl rollout restart ..."],
    "confidence": 92,
    "confidence_reasons": ["Pod logs show error X", "..."],
    "prevention_recommendation": "..."
  }
}
```

## 🚀 Deployment

### Frontend
```bash
npm run build
# Deploy dist/ to any static host (Vercel, Netlify, GitHub Pages, S3)
```

### Backend
```bash
# Use Gunicorn + Uvicorn for production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app
```

## 📝 License

[Your License Here]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues or questions:
1. Check [INTEGRATION.md](./INTEGRATION.md)
2. Review backend/frontend logs
3. Check browser console in DevTools
4. Verify .env configuration

---

**Ready to get started?** Run `./quickstart.sh` or see [Quick Start](#-quick-start) above!
