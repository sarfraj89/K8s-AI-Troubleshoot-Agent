import React, { ReactNode, useEffect, useState } from 'react';
import { AuthState } from '../types';
import { insforgeClient } from '../services/insforge';

export interface AuthContextType extends AuthState {
  login: (
    email: string,
    password: string,
  ) => Promise<{ requiresVerification: boolean; email: string } | void>;
  signup: (
    email: string,
    password: string,
  ) => Promise<{ requiresVerification: boolean; email: string }>;
  verifyEmail: (email: string, otp: string) => Promise<void>;
  resendVerificationEmail: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = React.createContext<AuthContextType | undefined>(undefined);

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object') {
    const responseData = (error as { response?: { data?: unknown } }).response?.data;

    if (typeof responseData === 'string') {
      return responseData;
    }

    if (responseData && typeof responseData === 'object') {
      const detail = (responseData as { detail?: unknown }).detail;
      if (typeof detail === 'string') {
        return detail;
      }
    }

    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string') {
      return message;
    }
  }

  return '';
}

function getErrorStatusCode(error: unknown) {
  if (!error || typeof error !== 'object') {
    return undefined;
  }

  const statusCode = (error as { statusCode?: unknown }).statusCode;
  if (typeof statusCode === 'number') {
    return statusCode;
  }

  const responseStatus = (error as { response?: { status?: unknown } }).response?.status;
  if (typeof responseStatus === 'number') {
    return responseStatus;
  }

  const responseData = (error as { response?: { data?: unknown } }).response?.data;
  if (responseData && typeof responseData === 'object') {
    const dataStatusCode = (responseData as { statusCode?: unknown }).statusCode;
    if (typeof dataStatusCode === 'number') {
      return dataStatusCode;
    }
  }

  return undefined;
}

function isVerificationRequiredError(error: unknown) {
  const message = getErrorMessage(error);
  const statusCode = getErrorStatusCode(error);

  return (
    statusCode === 403 ||
    /forbidden|verification required|verify your email|email verification required|email.*not.*verified|otp/i.test(message)
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  const getAuthResponseData = (data: unknown) =>
    data && typeof data === 'object' ? (data as Record<string, unknown>) : {};

  const requiresVerificationFromResponse = (data: unknown) => {
    const response = getAuthResponseData(data);

    return Boolean(
      response.requireEmailVerification ||
        response.requiresVerification ||
        response.verificationRequired ||
        response.otpRequired ||
        (response.user &&
          typeof response.user === 'object' &&
          (response.user as { emailVerified?: unknown }).emailVerified === false) ||
        ((response.accessToken === undefined || response.accessToken === null || response.accessToken === '') &&
          (response.user || response.message || response.detail)),
    );
  };

  // Check session on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        const { data, error } = await insforgeClient.auth.getCurrentUser();

        if (error) {
          throw error;
        }

        const user = data.user;

        if (user) {
          setState({
            user: {
              id: user.id,
              email: user.email || '',
            },
            loading: false,
            error: null,
          });
        } else {
          setState({
            user: null,
            loading: false,
            error: null,
          });
        }
      } catch (error) {
        setState({
          user: null,
          loading: false,
          error: null, // Silent error on initial load
        });
      }
    };

    checkSession();
  }, []);

  const login = async (email: string, password: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const { data, error } = await insforgeClient.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        if (isVerificationRequiredError(error)) {
          setState({
            user: null,
            loading: false,
            error: null,
          });
          return { requiresVerification: true, email };
        }

        throw new Error(getErrorMessage(error) || 'Login failed');
      }

      if (!data?.user) {
        throw new Error('Login failed');
      }

      setState({
        user: {
          id: data.user.id,
          email: data.user.email || '',
        },
        loading: false,
        error: null,
      });

      return { requiresVerification: false, email };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setState({
        user: null,
        loading: false,
        error: errorMessage,
      });
      throw err;
    }
  };

  const signup = async (email: string, password: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const { data, error } = await insforgeClient.auth.signUp({
        email,
        password,
        redirectTo: window.location.origin,
      });

      if (error) {
        if (isVerificationRequiredError(error)) {
          setState({
            user: null,
            loading: false,
            error: null,
          });
          return { requiresVerification: true, email };
        }

        throw new Error(error?.message || 'Signup failed');
      }

      const requiresVerification = requiresVerificationFromResponse(data);

      if (!data?.user && !requiresVerification) {
        throw new Error('Signup failed');
      }

      // InsForge email/password signup sends a verification code before the user can sign in.
      setState({
        user: null,
        loading: false,
        error: null,
      });

      return { requiresVerification: true, email };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Signup failed';
      setState({
        user: null,
        loading: false,
        error: errorMessage,
      });
      throw err;
    }
  };

  const verifyEmail = async (email: string, otp: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const { data, error } = await insforgeClient.auth.verifyEmail({
        email,
        otp,
      });

      if (error || !data?.user) {
        throw new Error(error?.message || 'Email verification failed');
      }

      setState({
        user: {
          id: data.user.id,
          email: data.user.email || email,
        },
        loading: false,
        error: null,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Email verification failed';
      setState({
        user: null,
        loading: false,
        error: errorMessage,
      });
      throw err;
    }
  };

  const resendVerificationEmail = async (email: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const { error } = await insforgeClient.auth.resendVerificationEmail({
        email,
        redirectTo: window.location.origin,
      });

      if (error) {
        throw new Error(error.message || 'Failed to resend verification email');
      }

      setState((prev) => ({
        ...prev,
        loading: false,
        error: 'Verification code sent again.',
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to resend verification email';
      setState({
        user: null,
        loading: false,
        error: errorMessage,
      });
      throw err;
    }
  };

  const logout = async () => {
    setState((prev) => ({ ...prev, loading: true }));

    try {
      await insforgeClient.auth.signOut();
      setState({
        user: null,
        loading: false,
        error: null,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Logout failed';
      setState({
        user: null,
        loading: false,
        error: errorMessage,
      });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        signup,
        verifyEmail,
        resendVerificationEmail,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
