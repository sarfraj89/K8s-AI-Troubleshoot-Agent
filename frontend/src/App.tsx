import { Loader2, Terminal } from 'lucide-react';
import { useAuth } from './hooks/useAuth';
import { LoginForm } from './components/LoginForm';
import { Dashboard } from './components/Dashboard';

export function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-mesh-gradient bg-grid-overlay flex items-center justify-center text-slate-100">
        <div className="relative flex flex-col items-center gap-6 p-8 bg-slate-900/60 backdrop-blur-xl border border-slate-800/80 rounded-2xl shadow-2xl max-w-sm w-full mx-4 animate-fade-in">
          {/* Decorative glowing gradient ring */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-2xl opacity-20 blur-lg animate-pulse-slow"></div>
          
          <div className="relative flex flex-col items-center gap-4">
            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl shadow-inner relative overflow-hidden">
              <Terminal className="w-8 h-8 text-cyan-400" />
            </div>
            <div className="flex flex-col items-center gap-1.5 text-center">
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                <span className="font-semibold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-slate-100 to-slate-300">Initializing Agent</span>
              </div>
              <p className="text-xs text-slate-400 font-medium">Checking cluster configuration...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-mesh-gradient bg-grid-overlay text-slate-100 font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {user ? (
        <Dashboard />
      ) : (
        <div className="min-h-screen flex items-center justify-center p-4">
          <LoginForm onSuccess={() => {}} />
        </div>
      )}
    </div>
  );
}

export default App;
