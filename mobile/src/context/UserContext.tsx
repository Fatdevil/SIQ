import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { BillingStatus, fetchStatus } from "../lib/UserAccessEngine";

const API_BASE = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const DEV_USER_ID = process.env.EXPO_PUBLIC_DEV_USER_ID ?? "dev-user";

type UserContextValue = {
  userId: string;
  status: BillingStatus | null;
  loading: boolean;
  refresh: () => Promise<BillingStatus | null>;
};

const UserContext = createContext<UserContextValue | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const userId = DEV_USER_ID;

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const next = await fetchStatus(API_BASE, userId);
      setStatus(next);
      return next;
    } catch (error) {
      console.error("Failed to fetch billing status", error);
      return null;
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo<UserContextValue>(() => ({ userId, status, loading, refresh }), [loading, refresh, status, userId]);

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export function useUserContext(): UserContextValue {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUserContext must be used within a UserProvider");
  }
  return context;
}
