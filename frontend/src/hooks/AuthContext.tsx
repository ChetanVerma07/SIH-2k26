import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  avatar?: string;
  provider: 'email' | 'google' | 'facebook' | 'phone';
  createdAt: string;
}

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<boolean>;
  signUp: (name: string, email: string, password: string) => Promise<boolean>;
  signInWithGoogle: () => Promise<boolean>;
  signInWithFacebook: () => Promise<boolean>;
  signInWithPhone: (phone: string, otp: string) => Promise<boolean>;
  signOut: () => void;
  updateProfile: (updates: Partial<Pick<User, 'name' | 'email' | 'phone'>>) => void;
}

const AUTH_KEY = 'thermalshelter.auth';

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const raw = localStorage.getItem(AUTH_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    try {
      if (user) {
        localStorage.setItem(AUTH_KEY, JSON.stringify(user));
      } else {
        localStorage.removeItem(AUTH_KEY);
      }
    } catch { /* ignore */ }
  }, [user]);

  const createUser = (overrides: Partial<User>): User => ({
    id: `user-${Date.now().toString(36)}`,
    name: 'SIH Team',
    email: 'team@thermalshelter.ai',
    provider: 'email',
    createdAt: new Date().toISOString(),
    ...overrides,
  });

  const signIn = async (email: string, _password: string): Promise<boolean> => {
    // Simulate network delay
    await new Promise((r) => setTimeout(r, 800));
    setUser(createUser({ email, name: email.split('@')[0] }));
    return true;
  };

  const signUp = async (name: string, email: string, _password: string): Promise<boolean> => {
    await new Promise((r) => setTimeout(r, 800));
    setUser(createUser({ name, email }));
    return true;
  };

  const signInWithGoogle = async (): Promise<boolean> => {
    await new Promise((r) => setTimeout(r, 1000));
    setUser(createUser({
      name: 'SIH Team (Google)',
      email: 'sihteam@gmail.com',
      provider: 'google',
      avatar: 'G',
    }));
    return true;
  };

  const signInWithFacebook = async (): Promise<boolean> => {
    await new Promise((r) => setTimeout(r, 1000));
    setUser(createUser({
      name: 'SIH Team (Facebook)',
      email: 'sihteam@facebook.com',
      provider: 'facebook',
      avatar: 'F',
    }));
    return true;
  };

  const signInWithPhone = async (phone: string, _otp: string): Promise<boolean> => {
    await new Promise((r) => setTimeout(r, 800));
    setUser(createUser({
      name: `User ${phone.slice(-4)}`,
      email: `${phone}@phone.auth`,
      phone,
      provider: 'phone',
    }));
    return true;
  };

  const signOut = () => setUser(null);

  const updateProfile = (updates: Partial<Pick<User, 'name' | 'email' | 'phone'>>) => {
    setUser((prev) => (prev ? { ...prev, ...updates } : prev));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        signIn,
        signUp,
        signInWithGoogle,
        signInWithFacebook,
        signInWithPhone,
        signOut,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
