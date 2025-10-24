import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { BillingStatus, fetchStatus } from '@/lib/UserAccessEngine';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const DEV_USER_ID = import.meta.env.VITE_DEV_USER_ID ?? 'dev-user';

export type UserContextValue = {
  userId: string;
  status: BillingStatus | null;
  loading: boolean;
  refresh: () => Promise<BillingStatus | null>;
};

const UserContext = createContext<UserContextValue | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const userId = DEV_USER_ID;

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const nextStatus = await fetchStatus(API_BASE, userId);
      setStatus(nextStatus);
      return nextStatus;
    } catch (error) {
      console.error('Failed to fetch billing status', error);
      return null;
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo<UserContextValue>(() => ({ userId, status, loading, refresh }), [userId, status, loading, refresh]);

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUserContext(): UserContextValue {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUserContext must be used within UserProvider');
  }
  return context;
}
