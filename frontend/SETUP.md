# Frontend Setup Guide

## Prerequisites

1. **Node.js** (v18 or higher)
2. **InsForge Account** with a project created
3. **Backend API** running at `http://localhost:8000`

## Installation

### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

### Step 2: Configure Environment

Copy the example environment file and update with your InsForge credentials:

```bash
cp .env.example .env
```

Edit `.env` with your InsForge project details:

```env
# Get from InsForge Project Settings
VITE_INSFORGE_URL=https://your-app.region.insforge.app
VITE_INSFORGE_ANON_KEY=your-anon-key-here

# Backend API
VITE_BACKEND_URL=http://localhost:8000
```

### Step 3: Set Up InsForge Database Tables

You need to create the following tables in InsForge:

#### Table 1: `investigations`

Columns:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to auth users)
- `timestamp` (Timestamp with timezone)
- `root_cause` (Text)
- `explanation` (Text)
- `fix` (Text)
- `kubectl_command` (Text)
- `confidence` (Integer)
- `namespace` (Text, optional)
- `status` (Text: 'success', 'failed')

#### Table 2: `progress_updates` (Optional, for future realtime enhancements)

Columns:
- `id` (UUID, Primary Key)
- `investigation_id` (UUID, Foreign Key)
- `step` (Text: 'pods', 'logs', 'events', 'deployments', 'network', 'ai', 'complete')
- `status` (Text: 'pending', 'in-progress', 'completed', 'error')
- `message` (Text, optional)
- `created_at` (Timestamp)

### Step 4: Start the Frontend Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Features

### Authentication
- Email/password login and signup
- Session management via InsForge
- Automatic user detection

### Investigation Dashboard
- **Investigate Button**: Triggers cluster investigation
- **Progress Tracker**: Real-time status of investigation steps
  - Checking Pods
  - Reading Logs
  - Analyzing Events
  - Inspecting Deployments
  - Checking Networking
  - AI Reasoning
  - Complete

### Diagnosis Display
Shows comprehensive analysis:
- **Root Cause**: Main issue identified
- **Explanation**: Why this issue occurred
- **Suggested Fix**: How to resolve it
- **Kubectl Commands**: Ready-to-use commands
- **Confidence Score**: How confident the AI is
- **Prevention Tips**: How to avoid this in the future

### Investigation History
- View past investigations
- Filter by status
- See timestamps and confidence scores
- Stores all data in InsForge database

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── App.tsx              # Main app component with routing
│   │   ├── Dashboard.tsx        # Main investigation dashboard
│   │   ├── LoginForm.tsx        # Authentication UI
│   │   ├── ProgressTracker.tsx  # Investigation progress display
│   │   ├── DiagnosisCard.tsx    # Diagnosis result display
│   │   └── InvestigationHistory.tsx  # Past investigations table
│   ├── context/
│   │   └── AuthContext.tsx      # Authentication state management
│   ├── hooks/
│   │   ├── useAuth.ts           # Auth hook
│   │   └── useInvestigationProgress.ts  # Realtime progress hook
│   ├── services/
│   │   ├── insforge.ts          # InsForge client setup
│   │   └── api.ts               # Backend API calls
│   ├── types/
│   │   └── index.ts             # TypeScript types
│   ├── App.tsx                  # App entry point
│   ├── main.tsx                 # React DOM render
│   └── index.css                # Global styles
├── index.html                   # HTML entry
├── vite.config.ts               # Vite configuration
├── tailwind.config.js           # Tailwind CSS config
├── postcss.config.js            # PostCSS config
├── tsconfig.json                # TypeScript config
└── package.json
```

## Available Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## API Integration

The frontend communicates with the FastAPI backend at `POST /investigate`:

**Request:**
```http
POST /investigate
```

**Response:**
```json
{
  "status": "success",
  "investigation": {
    "pods": { ... },
    "logs": { ... },
    "events": { ... },
    "deployments": { ... },
    "network": { ... }
  },
  "diagnosis": {
    "root_cause": "Pod in CrashLoopBackOff",
    "explanation": "...",
    "fix": "...",
    "kubectl_command": "kubectl edit deployment ...",
    "kubectl_commands": [...],
    "confidence": 92,
    "confidence_reasons": [...],
    "prevention_recommendation": "..."
  }
}
```

## Troubleshooting

### Issue: "InsForge configuration missing"
**Solution:** Check that `.env` file exists and has valid credentials.

### Issue: "Failed to load history"
**Solution:** Ensure the `investigations` table exists in InsForge with proper schema.

### Issue: "Investigation failed"
**Solution:** Ensure backend is running at the configured `VITE_BACKEND_URL`.

### Issue: Login not working
**Solution:** 
1. Check InsForge credentials in `.env`
2. Verify InsForge project has Auth enabled
3. Check browser console for detailed errors

## Next Steps

### For Development
1. Add error boundary for graceful error handling
2. Implement investigation filtering/search
3. Add export functionality for investigations
4. Implement real-time progress via WebSockets

### For Production
1. Replace `allow_origins=["*"]` in backend with specific domains
2. Add CORS configuration
3. Set up proper error logging
4. Implement rate limiting
5. Add input validation
6. Use environment-specific configurations

## Contributing

When modifying the frontend:
1. Keep UI components simple and reusable
2. Follow existing naming conventions
3. Update types in `src/types/index.ts`
4. Test with both authenticated and unauthenticated states
5. Ensure responsive design on mobile

## License

Same as main project.
