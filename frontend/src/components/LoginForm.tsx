import React, { useState } from 'react';
import { AlertCircle, Loader2, Terminal, Sparkles } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [verificationEmail, setVerificationEmail] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [localNotice, setLocalNotice] = useState<string | null>(null);
  const { login, signup, verifyEmail, resendVerificationEmail, loading, error } = useAuth();

  const getErrorMessage = (err: unknown) => {
    if (err instanceof Error) {
      return err.message;
    }

    if (typeof err === 'string') {
      return err;
    }

    if (err && typeof err === 'object') {
      const responseData = (err as { response?: { data?: unknown } }).response?.data;
      if (typeof responseData === 'string') {
        return responseData;
      }

      if (responseData && typeof responseData === 'object') {
        const detail = (responseData as { detail?: unknown }).detail;
        if (typeof detail === 'string') {
          return detail;
        }
      }

      const message = (err as { message?: unknown }).message;
      if (typeof message === 'string') {
        return message;
      }
    }

    return '';
  };

  const isVerificationRequiredError = (err: unknown) =>
    /forbidden|verification required|verify your email|email verification required|email.*not.*verified|otp/i.test(
      getErrorMessage(err),
    );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setLocalNotice(null);

    if (!email || !password) {
      setLocalError('Email and password are required');
      return;
    }

    try {
      if (isSignup) {
        const result = await signup(email, password);
        if (result.requiresVerification) {
          setNeedsVerification(true);
          setVerificationEmail(result.email);
          setVerificationCode('');
          setLocalNotice('Account created. Enter the 6-digit code sent to your email.');
          return;
        }
      } else {
        const result = await login(email, password);
        if (result?.requiresVerification) {
          setNeedsVerification(true);
          setVerificationEmail(result.email);
          setVerificationCode('');
          setLocalNotice('Enter the OTP sent to your email to finish signing in.');
          return;
        }
      }
      onSuccess?.();
    } catch (err) {
      if (isVerificationRequiredError(err)) {
        setNeedsVerification(true);
        setVerificationEmail(email);
        setVerificationCode('');
        setLocalError(null);
        setLocalNotice('Enter the OTP sent to your email to continue.');
        return;
      }

      setLocalError(err instanceof Error ? err.message : 'Authentication failed');
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setLocalNotice(null);

    if (!verificationEmail || !verificationCode) {
      setLocalError('Enter the 6-digit code from your email');
      return;
    }

    try {
      await verifyEmail(verificationEmail, verificationCode);
      setNeedsVerification(false);
      setVerificationCode('');
      setLocalNotice('Email verified successfully.');
      onSuccess?.();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Verification failed');
    }
  };

  const handleResend = async () => {
    setLocalError(null);
    setLocalNotice(null);

    try {
      await resendVerificationEmail(verificationEmail || email);
      setLocalNotice('Verification code sent again.');
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Unable to resend code');
    }
  };

  const displayError = localError || error;
  const displayNotice = localNotice;

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Decorative background glow */}
      <div className="absolute -top-40 -left-40 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="relative overflow-hidden bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-auto animate-fade-in">
        {/* Glow border ring */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-cyan-500/20 rounded-2xl opacity-40 blur-sm pointer-events-none"></div>

        {/* Card header */}
        <div className="relative flex flex-col items-center gap-4 mb-8">
          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl shadow-inner relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/10 to-cyan-500/10 opacity-30"></div>
            <Terminal className="w-8 h-8 text-cyan-400 relative z-10" />
          </div>
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 to-slate-300">
              {needsVerification ? 'Security Verification' : isSignup ? 'Create Account' : 'AI Troubleshooting Agent'}
            </h2>
            <p className="text-sm text-slate-400 mt-1.5 font-medium">
              {needsVerification 
                ? `Enter verification code sent to ${verificationEmail}` 
                : 'Diagnostics and automated cluster resolution.'}
            </p>
          </div>
        </div>

        {/* Feedback Messages */}
        {displayNotice && (
          <div className="mb-6 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
            <span className="font-medium">{displayNotice}</span>
          </div>
        )}

        {displayError && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <span className="font-medium">{displayError}</span>
          </div>
        )}

        {needsVerification ? (
          /* Verification Form */
          <form onSubmit={handleVerify} className="space-y-5 relative z-10">
            <div>
              <label htmlFor="otp" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Verification Code
              </label>
              <div className="relative">
                <input
                  id="otp"
                  type="text"
                  placeholder="000000"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  className="w-full pl-4 pr-4 py-3 bg-slate-950/40 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 transition font-mono tracking-widest text-center text-lg"
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !verificationCode}
              className="w-full py-3 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all duration-200 active:scale-[0.98] flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  Verifying Code...
                </>
              ) : (
                'Verify Account'
              )}
            </button>

            <div className="flex flex-col gap-3 pt-2 text-center text-xs">
              <button
                type="button"
                onClick={handleResend}
                disabled={loading}
                className="text-cyan-400 hover:text-cyan-300 font-medium transition cursor-pointer disabled:opacity-50"
              >
                Resend Code
              </button>
              <button
                type="button"
                onClick={() => {
                  setNeedsVerification(false);
                  setLocalError(null);
                  setLocalNotice(null);
                }}
                className="text-slate-400 hover:text-slate-300 transition"
              >
                Back to Authentication
              </button>
            </div>
          </form>
        ) : (
          /* Login/Signup Form */
          <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <input
                  id="email"
                  type="email"
                  placeholder="name@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-4 pr-4 py-3 bg-slate-950/40 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 transition font-sans text-sm"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-4 pr-4 py-3 bg-slate-950/40 border border-slate-800 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/50 transition font-sans text-sm"
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password}
              className="w-full py-3 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100 text-white text-sm font-semibold rounded-xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all duration-200 active:scale-[0.98] flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  {isSignup ? 'Creating Account...' : 'Signing In...'}
                </>
              ) : (
                isSignup ? 'Create Account' : 'Sign In'
              )}
            </button>

            <div className="pt-2 text-center text-xs">
              <button
                type="button"
                onClick={() => {
                  setIsSignup(!isSignup);
                  setLocalError(null);
                  setLocalNotice(null);
                }}
                disabled={loading}
                className="text-cyan-400 hover:text-cyan-300 font-medium transition cursor-pointer disabled:opacity-50"
              >
                {isSignup ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
