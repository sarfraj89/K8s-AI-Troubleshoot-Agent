# AI Kubernetes Agent - Frontend

A minimal, professional React frontend for investigating Kubernetes clusters with AI-powered root cause analysis.

## Quick Start

### Prerequisites
- Node.js 18+
- InsForge account with API credentials
- Running backend API (`http://localhost:8000`)

### Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your InsForge credentials:
   ```env
   VITE_INSFORGE_URL=https://your-app.region.insforge.app
   VITE_INSFORGE_ANON_KEY=your-anon-key-here
   VITE_BACKEND_URL=http://localhost:8000
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Open browser**
   ```
   http://localhost:3000
   ```

## Features

### 🔐 Authentication
- Email/password signup and login
- Session management via InsForge
- Protected dashboard access

### 🔍 Investigation Dashboard
- One-click cluster investigation
- Real-time progress tracking
- Live status updates for each investigation step:
  - Checking Pods
  - Reading Logs
  - Analyzing Events
  - Inspecting Deployments
  - Checking Networking
  - AI Reasoning
  - Complete

### 📊 Diagnosis Results
- **Root Cause**: Main issue identified by AI
- **Explanation**: Why the issue occurred
- **Suggested Fix**: How to resolve it
- **Kubectl Commands**: Ready-to-copy commands
- **Confidence Score**: AI's confidence level with breakdown
- **Prevention Tips**: How to avoid this issue

### 📈 Investigation History
- View all past investigations
- Sorted by timestamp (newest first)
- See confidence scores and status
- Browse by root cause
- Up to 10 most recent investigations

## Project Structure

```
src/
├── components/
│   ├── App.tsx                  # Main app router
│   ├── Dashboard.tsx            # Investigation UI
│   ├── LoginForm.tsx            # Auth UI
│   ├── ProgressTracker.tsx      # Progress display
│   ├── DiagnosisCard.tsx        # Results display
│   └── InvestigationHistory.tsx # History table
├── context/
│   └── AuthContext.tsx          # Auth state & providers
├── hooks/
│   ├── useAuth.ts               # Auth hook
│   └── useInvestigationProgress.ts  # Progress subscription
├── services/
│   ├── insforge.ts              # InsForge SDK config
│   └── api.ts                   # Backend API client
├── types/
│   └── index.ts                 # TypeScript types
├── App.tsx                      # App component
├── main.tsx                     # React DOM entry
└── index.css                    # Global styles
```

## Development

### Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Adding Features

1. **New API Endpoint**
   - Add to `src/services/api.ts`
   - Type in `src/types/index.ts`
   - Use in component via `import { investigationApi }`

2. **New Component**
   - Create in `src/components/`
   - Export from component file
   - Use in other components

3. **New Service**
   - Create in `src/services/`
   - Instantiate InsForge client or API client
   - Export functions

4. **New Context/Hook**
   - Create in `src/context/` or `src/hooks/`
   - Use in components with appropriate hooks

## Database Integration

The frontend uses InsForge for:

### Authentication
- User signup/login
- Session management
- User identity

### Investigation History
Stores investigations with these fields:
- `user_id`: Links to authenticated user
- `timestamp`: When investigation ran
- `root_cause`: Main issue (indexed)
- `confidence`: Score 0-100
- `namespace`: Kubernetes namespace
- `status`: 'success' or 'failed'

### Real-time Updates (Optional)
Subscribe to progress updates via WebSocket:
```typescript
const { progress } = useInvestigationProgress(user?.id);
```

## API Integration

### Backend Endpoint
The frontend calls `POST /investigate` on the backend:

**Request:**
```typescript
const result = await investigationApi.investigate();
```

**Response:**
```typescript
{
  status: 'success',
  investigation: {...},  // Raw K8s data
  diagnosis: {
    root_cause: string,
    explanation: string,
    fix: string,
    kubectl_command: string,
    kubectl_commands: string[],
    confidence: number,
    confidence_reasons: string[]
  }
}
```

## Styling

Using **Tailwind CSS 3.4** with:
- Utility-first CSS
- Responsive design
- Dark/light modes ready
- Minimal custom CSS

### Color Scheme
- Primary: Blue (`bg-blue-600`)
- Success: Green (`bg-green-600`)
- Warning: Yellow (`bg-yellow-600`)
- Error: Red (`bg-red-600`)
- Neutral: Gray (`bg-gray-50` to `bg-gray-900`)

### Component Classes
```tsx
// Buttons
className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"

// Cards
className="bg-white rounded-lg shadow-md p-6"

// Inputs
className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
```

## Error Handling

All async operations wrapped with try-catch:

```typescript
try {
  const result = await investigationApi.investigate();
  setDiagnosis(result.diagnosis);
} catch (error) {
  setError(error.message);
}
```

Common error messages:
- "User not authenticated" - Login required
- "Investigation failed" - Backend error
- "Failed to load history" - Database issue
- "Diagnosis unavailable" - LLM error (show original issue)

## Performance

- **Code splitting**: Built-in with Vite
- **Lazy loading**: Components load on demand
- **Caching**: HTTP requests cached by browser
- **Optimized builds**: Minified + tree-shaken
- **Fast refresh**: HMR during development

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Deployment

### Build
```bash
npm run build
```

Outputs to `dist/` directory.

### Deploy
```bash
# Option 1: Static hosting (Vercel, Netlify, GitHub Pages)
# Upload dist/ folder

# Option 2: Docker
# See docker-compose.yml

# Option 3: Heroku
# Buildpack: heroku/nodejs
# Configure environment variables
```

### Environment Variables
Set in hosting platform:
```env
VITE_INSFORGE_URL=https://your-app.region.insforge.app
VITE_INSFORGE_ANON_KEY=your-anon-key-here
VITE_BACKEND_URL=https://api.yourdomain.com
VITE_ENV=production
```

## Troubleshooting

### Login not working
- ✅ Check InsForge credentials in `.env`
- ✅ Verify InsForge project has Auth enabled
- ✅ Check browser console for error details

### Investigation fails
- ✅ Ensure backend is running: `curl http://localhost:8000/health`
- ✅ Check VITE_BACKEND_URL in `.env`
- ✅ Verify network tab in DevTools for error details

### History not showing
- ✅ Verify `investigations` table exists in InsForge
- ✅ Check table has correct columns
- ✅ Verify RLS policies aren't blocking reads
- ✅ Check user_id matches current user

### Progress not updating
- ✅ This uses client-side simulation (no WebSocket needed yet)
- ✅ To add real WebSocket updates, configure InsForge realtime

## Future Enhancements

- [ ] Real-time WebSocket progress updates
- [ ] Investigation filtering/search
- [ ] Export investigations to PDF/CSV
- [ ] Investigation comparison (what changed)
- [ ] Automated scheduled investigations
- [ ] Slack/webhook notifications
- [ ] Multiple Kubernetes clusters
- [ ] Custom investigation templates

## Contributing

1. Follow existing code style
2. Keep components small and reusable
3. Update types for new data
4. Test in Chrome, Firefox, Safari
5. Check mobile responsiveness

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **Tailwind CSS 3.4** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client
- **@insforge/sdk** - Backend integration
- **React Query** - Data fetching (optional)

## License

Same as main project.

---

Need help? Check [SETUP.md](./SETUP.md) for detailed installation or [INTEGRATION.md](../INTEGRATION.md) for full system setup.
